"""MarqueeLabel — a QLabel that elides long text and scrolls it on hover.

If the text fits the available width it renders normally (left/center
aligned).  When it overflows, the resting state shows an ellipsis
("NombreMuyLa...") and, while the mouse hovers over the label, a ~30 fps
timer scrolls the full text back-and-forth so the whole name can be read.
Leaving the widget stops the timer and restores the ellipsis.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QLabel, QWidget


class MarqueeLabel(QLabel):
    """Single-line label that elides overflow and scrolls on hover."""

    def __init__(
        self,
        text: str = "",
        parent: QWidget | None = None,
        alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        fps: int = 30,
    ):
        super().__init__(text, parent)
        self._full = text if text is not None else ""
        self._alignment = alignment
        self._fps = fps
        self._offset = 0
        self._scrolling = False
        self._gap = 24
        self.setObjectName("marqueeLabel")
        self.setSizePolicy(
            self.sizePolicy().horizontalPolicy(),
            self.sizePolicy().verticalPolicy(),
        )
        self._timer = QTimer(self)
        self._timer.setInterval(max(20, 1000 // self._fps))
        self._timer.timeout.connect(self._tick)

    # ------------------------------------------------------------------ #
    # Public API (keeps QLabel.setText usable)
    # ------------------------------------------------------------------ #
    def setText(self, text: str):
        self._full = text if text is not None else ""
        self._stop_scroll()
        self._sync_resting()

    def full_text(self) -> str:
        """The complete (un-elided) text, as stored by the last setText()."""
        return self._full

    def is_scrolling(self) -> bool:
        return self._scrolling

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _fits(self) -> bool:
        if not self._full:
            return True
        return self.fontMetrics().horizontalAdvance(self._full) <= self.width()

    def _elided(self) -> str:
        return self.fontMetrics().elidedText(
            self._full, Qt.TextElideMode.ElideRight, self.width())

    def _sync_resting(self):
        """Normal (non-hover) appearance: full text or ellipsis."""
        if self._scrolling:
            return
        if not self._full:
            super().setText("")
        elif self._fits():
            super().setText(self._full)
        else:
            super().setText(self._elided())
        self.update()

    def _start_scroll(self):
        self._offset = 0
        self._scrolling = True
        super().setText(self._full)
        self._timer.start()

    def _stop_scroll(self):
        self._scrolling = False
        self._timer.stop()
        self._offset = 0
        self.update()

    def _tick(self):
        text_w = self.fontMetrics().horizontalAdvance(self._full)
        total = text_w + self.width() + self._gap
        self._offset += 1
        if self._offset > total:
            self._offset = 0
        self.update()

    # ------------------------------------------------------------------ #
    # Events
    # ------------------------------------------------------------------ #
    def enterEvent(self, event):
        super().enterEvent(event)
        if not self._fits() and self._full:
            self._start_scroll()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if self._scrolling:
            self._stop_scroll()
            self._sync_resting()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Recompute against the real visible width: if resting, refresh the
        # elided/full text; even while scrolling we repaint so the marquee
        # track matches the new width immediately.
        if not self._scrolling:
            self._sync_resting()
        self.update()

    def paintEvent(self, event):
        if self._scrolling and self._full:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            painter.setPen(self.palette().color(self.foregroundRole()))
            fm = self.fontMetrics().horizontalAdvance(self._full)
            x = self.width() - self._offset
            rect = QRect(x, 0, fm + self._gap, self.height())
            painter.drawText(
                rect,
                int(Qt.AlignmentFlag.AlignVCenter),
                self._full,
            )
            return
        super().paintEvent(event)
