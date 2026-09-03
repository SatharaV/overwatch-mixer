"""Universal Single-Source-of-Truth Smooth Kinetic Scrolling for PySide6 (144 FPS)."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import QScrollArea, QWidget


class SmoothScrollArea(QScrollArea):
    """Kinetic smooth-scrolling area driven by OutCubic property animation.
    
    Supports both vertical and horizontal smooth scrolling automatically.
    """

    def __init__(self, parent: QWidget | None = None, orientation: Qt.Orientation = Qt.Orientation.Vertical):
        super().__init__(parent)
        self._orientation = orientation

        self._v_anim = QPropertyAnimation(self.verticalScrollBar(), b"value", self)
        self._v_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._v_anim.setDuration(220)

        self._h_anim = QPropertyAnimation(self.horizontalScrollBar(), b"value", self)
        self._h_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._h_anim.setDuration(220)

    def wheelEvent(self, event):
        v_delta = event.angleDelta().y()
        h_delta = event.angleDelta().x()

        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier and v_delta != 0 and h_delta == 0:
            h_delta = v_delta
            v_delta = 0

        handled = False

        if v_delta != 0 and self.verticalScrollBar().isVisible() and self.verticalScrollBar().maximum() > self.verticalScrollBar().minimum():
            vbar = self.verticalScrollBar()
            step = int(-v_delta / 120 * 48)
            current = self._v_anim.endValue() if self._v_anim.state() == QPropertyAnimation.State.Running else vbar.value()
            if current is None:
                current = vbar.value()
            target = max(vbar.minimum(), min(vbar.maximum(), current + step))
            self._v_anim.stop()
            self._v_anim.setStartValue(vbar.value())
            self._v_anim.setEndValue(target)
            self._v_anim.start()
            handled = True

        if h_delta != 0 and self.horizontalScrollBar().isVisible() and self.horizontalScrollBar().maximum() > self.horizontalScrollBar().minimum():
            hbar = self.horizontalScrollBar()
            step = int(-h_delta / 120 * 48)
            current = self._h_anim.endValue() if self._h_anim.state() == QPropertyAnimation.State.Running else hbar.value()
            if current is None:
                current = hbar.value()
            target = max(hbar.minimum(), min(hbar.maximum(), current + step))
            self._h_anim.stop()
            self._h_anim.setStartValue(hbar.value())
            self._h_anim.setEndValue(target)
            self._h_anim.start()
            handled = True

        if handled:
            event.accept()
        else:
            super().wheelEvent(event)
