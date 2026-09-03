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
    export_ratio: str = "16:9",
) -> QPixmap:
    """Renders tier list in 16:9 panoramic or Auto adaptive bounding box with RATAMMAKER logo."""
    from PySide6.QtWidgets import QApplication

    header_h = 56

    for r in rows:
        r.controls_bar.hide()
    canvas_widget.hide_watermark = True

    if current_mode == "hero":
        card_w, card_h = 76, 76
    else:
        card_w, card_h = 125, 75
    card_pitch_x = card_w + 6
    card_pitch_y = card_h + 6
    label_w = 88

    # A. MODO 16:9 (Panorámico optimizado)
    if export_ratio == "16:9":
        best_w = 1280
        min_slack = 999999

        for cand_w in range(1040, 2080, 20):
            avail_w = cand_w - label_w - 12
            cards_per_line = max(1, avail_w // card_pitch_x)

            total_rows_h = 0
            for r in rows:
                n_cards = len(r.cards)
                lines = max(1, (n_cards + cards_per_line - 1) // cards_per_line) if n_cards > 0 else 1
                row_h = max(96, 12 + lines * card_pitch_y)
                total_rows_h += row_h

            content_h = total_rows_h + header_h
            target_16_9_h = int(round(cand_w * 9 / 16))

            if target_16_9_h >= content_h:
                slack = target_16_9_h - content_h
                if slack < min_slack:
                    min_slack = slack
                    best_w = cand_w

        if best_w % 2 != 0:
            best_w += 1

        orig_min_w = canvas_widget.minimumWidth()
        orig_max_w = canvas_widget.maximumWidth()

        canvas_widget.setFixedWidth(best_w)
        for r in rows:
            r.resize(best_w, r.height())
            r.drop_zone.resize(best_w - label_w, r.drop_zone.height())
            r.drop_zone.flow_layout.setGeometry(r.drop_zone.rect())
            r.adjustSize()
        canvas_widget.adjustSize()

        rows_pixmap = canvas_widget.grab()

        canvas_widget.setMinimumWidth(orig_min_w)
        canvas_widget.setMaximumWidth(orig_max_w)
        for r in rows:
            r.controls_bar.show()
        canvas_widget.hide_watermark = False
        canvas_widget.adjustSize()

        rw = rows_pixmap.width()
        rh = rows_pixmap.height()
        final_w = rw
        final_h = int(round(final_w * 9 / 16))

        if final_h < rh + header_h:
            final_h = rh + header_h
            final_w = int(round(final_h * 16 / 9))

    # B. MODO AUTOMÁTICO (Ajuste libre al contenido sin recorte)
    else:
        canvas_widget.adjustSize()
        rows_pixmap = canvas_widget.grab()
        for r in rows:
            r.controls_bar.show()
        canvas_widget.hide_watermark = False

        rw = rows_pixmap.width()
        rh = rows_pixmap.height()
        final_w = rw
        final_h = rh + header_h

    if final_w % 2 != 0:
        final_w += 1
    if final_h % 2 != 0:
        final_h += 1

    final_pixmap = QPixmap(final_w, final_h)
    final_pixmap.fill(QColor("#0B0C10"))

    painter = QPainter(final_pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    header_rect = QRect(0, 0, final_w, header_h)
    painter.fillRect(header_rect, QColor("#14151B"))

    painter.setPen(QPen(QColor("#282B36"), 1))
    painter.drawLine(0, header_h - 1, final_w, header_h - 1)

    watermark = get_watermark_pixmap(target_height=36)
    if watermark:
        painter.setOpacity(1.0)
        logo_x = final_w - watermark.width() - 24
        logo_y = (header_h - watermark.height()) // 2
        painter.drawPixmap(logo_x, logo_y, watermark)

    painter.setOpacity(1.0)
    painter.drawPixmap(0, header_h, rows_pixmap)
    painter.end()

    return final_pixmap
