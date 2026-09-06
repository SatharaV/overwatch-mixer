"""Universal Vector Icon Button (SSOT) — Rendered procedurally via QPainter."""

from __future__ import annotations

from typing import Optional, Tuple
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygon, QTransform
from PySide6.QtWidgets import QPushButton, QWidget

from owervach_tmixer.ui.styles import theme


class VectorIconButton(QPushButton):
    """High-DPI procedural vector button with dynamic theme adaptation."""

    def __init__(
        self,
        icon_type: str,
        tooltip: str = "",
        size: Tuple[int, int] = (32, 26),
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.icon_type = icon_type
        self.setFixedSize(size[0], size[1])
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            self.setToolTip(tooltip)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        is_hovered = self.underMouse()
        is_pressed = self.isDown()
        accent_col = theme.accent_color()

        if self.icon_type in ("up", "down"):
            bg_col = QColor("#2D3342") if is_hovered else QColor("#1C1E26")
            border_col = accent_col if is_hovered else QColor("#383E50")
            icon_col = QColor("#FFFFFF") if is_hovered else accent_col
        elif self.icon_type == "clear":
            bg_col = QColor("#3D301C") if is_hovered else QColor("#241D14")
            border_col = QColor("#FFAA00") if is_hovered else QColor("#5A4018")
            icon_col = QColor("#FFFFFF") if is_hovered else QColor("#FFAA00")
        elif self.icon_type in ("del", "close"):
            bg_col = QColor("#461922") if is_hovered else QColor("#281318")
            border_col = QColor("#FF4444") if is_hovered else QColor("#62202A")
            icon_col = QColor("#FFFFFF") if is_hovered else QColor("#FF5566")
        elif self.icon_type == "gear":
            bg_col = QColor("#2A2D36") if is_hovered else QColor("#1E2026")
            border_col = accent_col if is_hovered else QColor("#33363F")
            icon_col = accent_col if is_hovered else QColor("#A0A5B5")
        else:
            bg_col = QColor("#22252E") if is_hovered else QColor("#181A20")
            border_col = accent_col if is_hovered else QColor("#2E323D")
            icon_col = QColor("#FFFFFF") if is_hovered else accent_col

        if is_pressed:
            bg_col = bg_col.darker(130)

        # Marco y fondo redondeado
        painter.setPen(QPen(border_col, 1))
        painter.setBrush(QBrush(bg_col))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 5, 5)

        cx = self.width() / 2.0
        cy = self.height() / 2.0

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(icon_col))

        if self.icon_type == "up":
            poly = QPolygon([
                QPoint(int(cx), int(cy - 4)),
                QPoint(int(cx - 4), int(cy + 3)),
                QPoint(int(cx + 4), int(cy + 3)),
            ])
            painter.drawPolygon(poly)

        elif self.icon_type == "down":
            poly = QPolygon([
                QPoint(int(cx), int(cy + 4)),
                QPoint(int(cx - 4), int(cy - 3)),
                QPoint(int(cx + 4), int(cy - 3)),
            ])
            painter.drawPolygon(poly)

        elif self.icon_type == "clear":
            painter.setPen(QPen(icon_col, 1.6, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            painter.drawArc(int(cx - 5), int(cy - 5), 10, 10, 45 * 16, 270 * 16)
            painter.setBrush(QBrush(icon_col))
            painter.setPen(Qt.NoPen)
            arrow = QPolygon([
                QPoint(int(cx + 3), int(cy - 5)),
                QPoint(int(cx + 3), int(cy)),
                QPoint(int(cx + 7), int(cy - 2)),
            ])
            painter.drawPolygon(arrow)

        elif self.icon_type in ("del", "close"):
            painter.setPen(QPen(icon_col, 2.0, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(int(cx - 4), int(cy - 4), int(cx + 4), int(cy + 4))
            painter.drawLine(int(cx + 4), int(cy - 4), int(cx - 4), int(cy + 4))

        elif self.icon_type == "gear":
            num_teeth = 6
            outer_r = 7.5
            inner_r = 5.2
            hole_r = 2.4

            gear_path = QPainterPath()
            gear_path.addEllipse(QPointF(cx, cy), inner_r, inner_r)

            tooth_w = 3.2
            tooth_h = outer_r - inner_r + 1.2
            for i in range(num_teeth):
                angle = i * (360.0 / num_teeth)
                tooth = QPainterPath()
                tooth.addRoundedRect(
                    QRectF(cx - tooth_w / 2.0, cy - outer_r, tooth_w, tooth_h),
                    0.8,
                    0.8,
                )
                transform = QTransform().translate(cx, cy).rotate(angle).translate(-cx, -cy)
                gear_path = gear_path.united(transform.map(tooth))

            hole = QPainterPath()
            hole.addEllipse(QPointF(cx, cy), hole_r, hole_r)
            gear_final = gear_path.subtracted(hole)

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(icon_col))
            painter.drawPath(gear_final)

        painter.end()
