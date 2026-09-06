"""Universal geometry persistence mixin for all dialogs and windows."""

from __future__ import annotations

from typing import TYPE_CHECKING
from PySide6.QtCore import QRect
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget

from owervach_tmixer.core.settings import WindowGeometry

if TYPE_CHECKING:
    from owervach_tmixer.core.settings import SettingsManager


class PersistentGeometryMixin:
    """Mixin that grants zero-friction window geometry persistence to any QWidget/QDialog/QMainWindow."""

    def setup_persistent_geometry(
        self: QWidget,
        settings_manager: SettingsManager,
        window_id: str,
        default_size: tuple[int, int] = (720, 620),
        min_size: tuple[int, int] = (580, 480),
    ):
        self._geo_settings_manager = settings_manager
        self._geo_window_id = window_id
        self.setMinimumSize(min_size[0], min_size[1])

        geom = settings_manager.get_window_geometry(window_id, default_size=default_size)
        if geom.width > 0 and geom.height > 0:
            self.resize(geom.width, geom.height)
            if self._is_position_visible(geom.x, geom.y, geom.width, geom.height):
                self.move(geom.x, geom.y)
            else:
                self._center_on_active_screen()

    def _is_position_visible(self, x: int, y: int, w: int, h: int) -> bool:
        """Verifies if the saved geometry rectangle intersects with any connected active screen."""
        target_rect = QRect(x, y, w, h)
        for screen in QGuiApplication.screens():
            if screen.availableGeometry().intersects(target_rect):
                return True
        return False

    def _center_on_active_screen(self: QWidget):
        """Centers the window on the active display."""
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            geo = self.frameGeometry()
            geo.moveCenter(screen_geo.center())
            self.move(geo.topLeft())

    def save_persistent_geometry(self: QWidget):
        """Captures and stores current geometry into persistent storage."""
        if not hasattr(self, "_geo_settings_manager") or not hasattr(self, "_geo_window_id"):
            return

        is_max = self.isMaximized()
        if is_max:
            norm = self.normalGeometry()
            gx, gy, gw, gh = norm.x(), norm.y(), norm.width(), norm.height()
        else:
            gx, gy, gw, gh = self.x(), self.y(), self.width(), self.height()

        geom = WindowGeometry(x=gx, y=gy, width=gw, height=gh, maximized=is_max)
        self._geo_settings_manager.update_window_geometry(self._geo_window_id, geom)
