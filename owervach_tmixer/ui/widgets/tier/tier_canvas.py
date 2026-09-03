"""Canvas rendering, Ratam Maker watermark, and HD PNG export for Tier Maker."""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from owervach_tmixer.utils import get_resource_path
from .tier_row import TierRowWidget


def get_watermark_pixmap(target_height: int = 40) -> QPixmap | None:
    path = get_resource_path("assets/ratammaker-logo-hehe.png")
    if not path.exists():
        path = get_resource_path("assets/tiermaker-logo.png")
    if not path.exists():
        return None
    pix = QPixmap(str(path))
    if pix.isNull():
        return None
    return pix.scaledToHeight(target_height, Qt.TransformationMode.SmoothTransformation)


class TierCanvasWidget(QWidget):
    """Drawing area for tier rows with dynamic background watermark."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.hide_watermark = False

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.hide_watermark:
            return

        watermark = get_watermark_pixmap(target_height=52)
        if not watermark:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setOpacity(0.95)

        margin_right = 88
        margin_top = 22
        x = self.width() - watermark.width() - margin_right
        y = margin_top

        if x > 120:
            painter.drawPixmap(x, y, watermark)
        painter.end()


def render_clean_tierlist_pixmap(
    rows: List[TierRowWidget],
    canvas_widget: TierCanvasWidget,
    current_mode: str = "hero",
) -> QPixmap:
    """Renders the tier list into an esports PNG with official Obsidian tournament header."""
    for r in rows:
        r.controls_bar.hide()

    canvas_widget.hide_watermark = True
    canvas_widget.adjustSize()
    rows_pixmap = canvas_widget.grab()
    canvas_widget.hide_watermark = False

    for r in rows:
        r.controls_bar.show()

    header_h = 56
    total_w = rows_pixmap.width()
    total_h = rows_pixmap.height() + header_h

    final_pixmap = QPixmap(total_w, total_h)
    final_pixmap.fill(QColor("#0B0C10"))

    painter = QPainter(final_pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    header_rect = QRect(0, 0, total_w, header_h)
    painter.fillRect(header_rect, QColor("#14151B"))

    painter.setPen(QPen(QColor("#282B36"), 1))
    painter.drawLine(0, header_h - 1, total_w, header_h - 1)

    mode_titles = {
        "hero": "🎭 TIER LIST DE HÉROES — OW MIXER",
        "map": "🗺️ TIER LIST DE MAPAS — OW MIXER",
        "player": "👥 TIER LIST DE JUGADORES — OW MIXER",
    }
    title_text = mode_titles.get(current_mode, "⚔️ OVERWATCH TEAM MIXER — TIER LIST")
    painter.setPen(QPen(QColor("#FFFFFF")))
    painter.setFont(QFont("Segoe UI", 13, QFont.Weight.Black))
    painter.drawText(
        QRect(20, 0, total_w // 2, header_h),
        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
        title_text,
    )

    watermark = get_watermark_pixmap(target_height=36)
    if watermark:
        painter.setOpacity(1.0)
        logo_x = total_w - watermark.width() - 20
        logo_y = (header_h - watermark.height()) // 2
        painter.drawPixmap(logo_x, logo_y, watermark)

    painter.setOpacity(1.0)
    painter.drawPixmap(0, header_h, rows_pixmap)
    painter.end()

    return final_pixmap
