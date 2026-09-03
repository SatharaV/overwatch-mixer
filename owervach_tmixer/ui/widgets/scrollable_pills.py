"""Horizontal scrollable pill container with instant-reacting vector arrows and wheel support."""

from __future__ import annotations
from .smooth_scroll import SmoothScrollArea

from typing import Optional

from PySide6.QtCore import QEasingCurve, QEvent, QObject, QPoint, QPropertyAnimation, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPolygon, QWheelEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QWidget,
)

from owervach_tmixer.ui.styles import theme


class ScrollArrowBtn(QPushButton):
    """Vector-drawn navigation arrow button for scrollable toolbars."""

    def __init__(self, direction: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.direction = direction
        self.setFixedSize(24, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_hovered = self.underMouse()
        is_pressed = self.isDown()
        accent_col = theme.accent_color()

        bg_col = QColor("#222634") if is_hovered else QColor("#181B24")
        border_col = accent_col if is_hovered else QColor("#2E3344")
        icon_col = QColor("#FFFFFF") if is_hovered else accent_col

        if is_pressed:
            bg_col = bg_col.darker(130)

        painter.setPen(QPen(border_col, 1))
        painter.setBrush(QBrush(bg_col))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 4, 4)

        cx = self.width() // 2
        cy = self.height() // 2

        painter.setPen(QPen(icon_col, 1))
        painter.setBrush(QBrush(icon_col))

        if self.direction == "left":
            poly = QPolygon([QPoint(cx - 3, cy), QPoint(cx + 3, cy - 4), QPoint(cx + 3, cy + 4)])
            painter.drawPolygon(poly)
        else:
            poly = QPolygon([QPoint(cx + 3, cy), QPoint(cx - 3, cy - 4), QPoint(cx - 3, cy + 4)])
            painter.drawPolygon(poly)

        painter.end()


class ScrollablePillsWidget(QWidget):
    """Universal horizontal container with smooth animation and auto-hiding vector arrows."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._scroll_anim: Optional[QPropertyAnimation] = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        self.btn_left = ScrollArrowBtn("left", self)
        self.btn_left.setToolTip("Desplazar a la izquierda")
        self.btn_left.clicked.connect(lambda: self._scroll_by(-160))
        self.btn_left.hide()
        main_layout.addWidget(self.btn_left)

        self.scroll = SmoothScrollArea(self, Qt.Orientation.Horizontal)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        self.scroll.viewport().setStyleSheet("background-color: transparent; border: none;")

        self.container = QWidget(self.scroll)
        self.container.setStyleSheet("background-color: transparent;")
        self.pills_layout = QHBoxLayout(self.container)
        self.pills_layout.setContentsMargins(0, 0, 0, 0)
        self.pills_layout.setSpacing(6)

        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll, 1)

        self.btn_right = ScrollArrowBtn("right", self)
        self.btn_right.setToolTip("Desplazar a la derecha")
        self.btn_right.clicked.connect(lambda: self._scroll_by(160))
        self.btn_right.hide()
        main_layout.addWidget(self.btn_right)

        self.scroll.horizontalScrollBar().valueChanged.connect(self._check_overflow)

        self.installEventFilter(self)
        self.scroll.installEventFilter(self)
        self.scroll.viewport().installEventFilter(self)
        self.container.installEventFilter(self)

    def add_widget(self, widget: QWidget):
        widget.installEventFilter(self)
        self.pills_layout.addWidget(widget)

    def update_pills_geometry(self):
        total_w = 0
        spacing = self.pills_layout.spacing()
        count = self.pills_layout.count()
        for i in range(count):
            item = self.pills_layout.itemAt(i)
            if item and item.widget():
                total_w += item.widget().sizeHint().width()
        if count > 1:
            total_w += (count - 1) * spacing

        self.container.setFixedWidth(total_w)
        self._check_overflow()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._check_overflow()

    def showEvent(self, event):
        super().showEvent(event)
        self.update_pills_geometry()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Wheel and isinstance(event, QWheelEvent):
            delta = event.angleDelta().y() or event.angleDelta().x()
            if delta != 0:
                h_bar = self.scroll.horizontalScrollBar()
                self._scroll_by(-delta)
                return True
        elif event.type() == QEvent.Type.Resize:
            self._check_overflow()
        return super().eventFilter(watched, event)

    def _scroll_by(self, delta: int):
        h_bar = self.scroll.horizontalScrollBar()
        target = max(0, min(h_bar.maximum(), h_bar.value() + delta))
        anim = QPropertyAnimation(h_bar, b"value", self)
        anim.setDuration(160)
        anim.setStartValue(h_bar.value())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._scroll_anim = anim

    def _check_overflow(self):
        vp_w = self.scroll.viewport().width() if self.scroll.viewport() else self.scroll.width()
        content_w = self.container.width()
        h_bar = self.scroll.horizontalScrollBar()

        can_scroll = (content_w > vp_w) or (h_bar.maximum() > 0)
        if not can_scroll:
            self.btn_left.hide()
            self.btn_right.hide()
            return

        val = h_bar.value()
        max_val = h_bar.maximum()

        self.btn_left.setVisible(val > 0)
        self.btn_right.setVisible(val < max_val)

    def apply_theme(self):
        self.btn_left.update()
        self.btn_right.update()
