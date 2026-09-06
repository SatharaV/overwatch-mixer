"""Central Theme Lifecycle Manager with safe lazy typography loading."""

from __future__ import annotations
from typing import Callable
from PySide6.QtGui import QFontDatabase, QGuiApplication
from owervach_tmixer.utils import get_resource_path
from owervach_tmixer.ui.styles.themes import (
    BaseTheme,
    ObsidianTheme,
    OverwatchUITheme,
    MaterialTheme,
)
from owervach_tmixer.ui.styles.tokens import ThemeTokens


class ThemeManager:
    """Singleton orchestrator managing registered themes, active skin, and dynamic QSS."""

    _instance: ThemeManager | None = None

    def __init__(self):
        self._fonts_loaded = False
        self._themes: dict[str, type[BaseTheme]] = {
            "obsidian": ObsidianTheme,
            "overwatch": OverwatchUITheme,
            "material": MaterialTheme,
        }
        self._current_theme_id = "obsidian"
        self._current_theme: BaseTheme = ObsidianTheme()
        self._accent_override: str | None = None
        self._listeners: list[Callable[[], None]] = []

    @classmethod
    def instance(cls) -> ThemeManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def ensure_fonts_loaded(self):
        """Loads Blizzard Big Noodle Titling and Futura fonts ONLY when QApplication is active.

        Guards against SIGSEGV caused by calling QFontDatabase before QApplication initialization.
        """
        if self._fonts_loaded:
            return
        if QGuiApplication.instance() is None:
            return

        self._fonts_loaded = True
        fonts_dir = get_resource_path("assets/Fonts")
        if fonts_dir.exists():
            for font_file in fonts_dir.glob("*.ttf"):
                try:
                    QFontDatabase.addApplicationFont(str(font_file))
                except Exception:
                    pass

    @property
    def current_theme(self) -> BaseTheme:
        return self._current_theme

    @property
    def current_theme_id(self) -> str:
        return self._current_theme_id

    @property
    def tokens(self) -> ThemeTokens:
        return self._current_theme.tokens

    def get_registered_themes(self) -> dict[str, tuple[str, str]]:
        """Returns dict of {theme_id: (display_name, description)}."""
        result = {}
        for tid, cls_theme in self._themes.items():
            inst = cls_theme()
            result[tid] = (inst.default_tokens.display_name, inst.default_tokens.description)
        return result

    def set_theme(self, theme_id: str, accent_override: str | None = None):
        """Switches the active theme strategy and reapplies styling."""
        self.ensure_fonts_loaded()
        if theme_id not in self._themes:
            theme_id = "obsidian"

        self._current_theme_id = theme_id
        if accent_override is not None:
            self._accent_override = accent_override.lower()

        cls_theme = self._themes[theme_id]
        self._current_theme = cls_theme(accent_override=self._accent_override)
        self._notify_listeners()

    def set_accent(self, hex_color: str):
        """Sets an accent color override on the active theme (always lowercase)."""
        clean_hex = hex_color.lower() if hex_color else None
        self._accent_override = clean_hex
        self._current_theme.set_accent_override(clean_hex)
        self._notify_listeners()

    def reset_accent(self):
        """Restores the theme's native default accent."""
        self._accent_override = None
        self._current_theme.set_accent_override(None)
        self._notify_listeners()

    def build_stylesheet(self) -> str:
        """Renders QSS from the currently active theme strategy."""
        self.ensure_fonts_loaded()
        return self._current_theme.build_stylesheet()

    def add_theme_listener(self, callback: Callable[[], None]):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_theme_listener(self, callback: Callable[[], None]):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self):
        for cb in list(self._listeners):
            try:
                cb()
            except Exception:
                pass
