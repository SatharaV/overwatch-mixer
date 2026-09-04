"""Universal Single-Source-of-Truth Smooth Kinetic Scrolling for PySide6 (True 144 FPS / PreciseTimer)."""

from __future__ import annotations
import time
from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtWidgets import QApplication, QScrollBar, QScrollArea, QWidget


class _KineticScrollDriver(QObject):
    """Driver cinético de alta resolución que sobrepasa el límite de 60Hz de Qt."""

    def __init__(self, scroll_bar: QScrollBar, parent: QWidget | None = None):
        super().__init__(parent)
        self._bar = scroll_bar
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._on_tick)

        self._start_val = 0.0
        self._target_val = 0.0
        self._start_time = 0.0
        self._duration_ms = 135.0
        self._is_running = False

    def scroll_by(self, delta: int, duration_ms: float = 135.0):
        now = time.perf_counter() * 1000.0
        current = self._bar.value()

        if self._is_running:
            target = max(self._bar.minimum(), min(self._bar.maximum(), int(round(self._target_val + delta))))
        else:
            target = max(self._bar.minimum(), min(self._bar.maximum(), current + delta))

        self._start_val = float(current)
        self._target_val = float(target)
        self._duration_ms = duration_ms
        self._start_time = now
        self._is_running = True

        screen = QApplication.primaryScreen()
        hz = screen.refreshRate() if screen and screen.refreshRate() > 30 else 144.0
        interval_ms = max(1, int(round(1000.0 / hz)))  # ~7ms a 144Hz
        self._timer.start(interval_ms)

    def _on_tick(self):
        now = time.perf_counter() * 1000.0
        elapsed = now - self._start_time
        t = min(1.0, max(0.0, elapsed / self._duration_ms))

        # Easing OutCubic: 1 - (1 - t)^3
        progress = 1.0 - (1.0 - t) ** 3
        new_val = int(round(self._start_val + (self._target_val - self._start_val) * progress))
        self._bar.setValue(new_val)

        if t >= 1.0 or new_val == int(self._target_val):
            self._bar.setValue(int(self._target_val))
            self._timer.stop()
            self._is_running = False


class SmoothScrollArea(QScrollArea):
    """Kinetic smooth-scrolling area driving scrollbars at the display's native refresh rate (144Hz+)."""

    def __init__(self, parent: QWidget | None = None, orientation: Qt.Orientation = Qt.Orientation.Vertical):
        super().__init__(parent)
        self._orientation = orientation
        self._v_driver = _KineticScrollDriver(self.verticalScrollBar(), self)
        self._h_driver = _KineticScrollDriver(self.horizontalScrollBar(), self)

    def wheelEvent(self, event):
        v_delta = event.angleDelta().y()
        h_delta = event.angleDelta().x()

        # Si el usuario gira la rueda vertical sobre un área horizontal (o con Shift),
        # convertir el giro en desplazamiento horizontal cinético fluido a 144 Hz
        is_horizontal_area = (
            self._orientation == Qt.Orientation.Horizontal
            or not self.verticalScrollBar().isVisible()
            or self.verticalScrollBar().maximum() <= self.verticalScrollBar().minimum()
        )

        if (event.modifiers() & Qt.KeyboardModifier.ShiftModifier or is_horizontal_area) and v_delta != 0 and h_delta == 0:
            h_delta = v_delta
            v_delta = 0

        handled = False

        if v_delta != 0 and self.verticalScrollBar().isVisible() and self.verticalScrollBar().maximum() > self.verticalScrollBar().minimum():
            step = int(-v_delta / 120.0 * 52.0)
            self._v_driver.scroll_by(step)
            handled = True

        if h_delta != 0 and self.horizontalScrollBar().isVisible() and self.horizontalScrollBar().maximum() > self.horizontalScrollBar().minimum():
            step = int(-h_delta / 120.0 * 52.0)
            self._h_driver.scroll_by(step)
            handled = True

        if handled:
            event.accept()
        else:
            super().wheelEvent(event)
