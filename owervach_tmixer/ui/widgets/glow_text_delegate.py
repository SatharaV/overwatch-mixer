"""Item delegate that paints a soft diffuse halo behind special-player text.

QListWidget rows cannot use QGraphicsEffect directly, so the glow is painted
in `paint()`: the text is drawn onto a transparent pixmap, blurred with
QGraphicsBlurEffect via a throwaway QGraphicsScene, and composited behind a
crisp bright text pass. Purely cosmetic; non-special rows fall through to the
default rendering.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import (
    QGraphicsBlurEffect,
    QGraphicsScene,
    QStyledItemDelegate,
)

from owervach_tmixer.core.special_player import SPECIAL_GLOW

SPECIAL_ROLE = int(Qt.ItemDataRole.UserRole) + 20


class GlowTextDelegate(QStyledItemDelegate):
    """Paints a few-pixel diffuse glow behind rows flagged with SPECIAL_ROLE."""

    def __init__(self, parent=None, blur: float = 3.0):
        super().__init__(parent)
        self._glow_color = QColor(SPECIAL_GLOW)
        self._text_color = QColor(SPECIAL_GLOW).lighter(185)
        self._blur = blur
        self._cache: dict[tuple, QPixmap] = {}

    def paint(self, painter: QPainter, option, index):
        if not index.data(SPECIAL_ROLE):
            super().paint(painter, option, index)
            return

        text = index.data(Qt.ItemDataRole.DisplayRole)
        if not text:
            super().paint(painter, option, index)
            return

        font = index.data(Qt.ItemDataRole.FontRole)
        if not isinstance(font, QFont):
            font = option.font
        align = index.data(Qt.ItemDataRole.TextAlignmentRole) or (
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = option.rect.adjusted(8, 0, -8, 0)
        painter.drawPixmap(rect.topLeft(), self._halo(text, font, rect.size(), align))

        painter.setFont(font)
        painter.setPen(self._text_color)
        painter.drawText(rect, int(align.value), text)
        painter.restore()

    # ------------------------------------------------------------------ #
    def _halo(self, text: str, font: QFont, size, align) -> QPixmap:
        key = (text, font.toString(), size.width(), size.height(), self._blur)
        pixmap = self._cache.get(key)
        if pixmap is not None:
            return pixmap

        base = QPixmap(size)
        base.fill(Qt.GlobalColor.transparent)
        p = QPainter(base)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(font)
        p.setPen(self._glow_color)
        p.drawText(base.rect(), int(align.value), text)
        p.end()

        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(self._blur)
        scene = QGraphicsScene()
        item = scene.addPixmap(base)
        item.setGraphicsEffect(blur)

        out = QPixmap(size)
        out.fill(Qt.GlobalColor.transparent)
        op = QPainter(out)
        scene.render(op, QRectF(0, 0, size.width(), size.height()),
                     scene.itemsBoundingRect())
        op.end()

        if len(self._cache) > 64:
            self._cache.clear()
        self._cache[key] = out
        return out
