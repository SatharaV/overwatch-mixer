"""Universal Theme Provider & Dynamic Color Engine (Facade over ThemeManager)."""

from __future__ import annotations
from PySide6.QtGui import QColor
from owervach_tmixer.ui.styles.theme_manager import ThemeManager
from owervach_tmixer.ui.styles.tokens import ThemeTokens

DEFAULT_ACCENT = "#61ab02"
ORIGINAL_ACCENT = "#FF7B00"

PRESETS: dict[str, str] = {
    "Sathara": DEFAULT_ACCENT,
    "Naranja": "#FF7B00",
    "Azul": "#00B4FF",
    "Rojo": "#E63946",
    "Morado": "#7B2CBF",
    "Dorado": "#E0A300",
}

_mgr = ThemeManager.instance()


def get_theme_manager() -> ThemeManager:
    """Returns the central ThemeManager singleton."""
    return _mgr


def tokens() -> ThemeTokens:
    """Returns active theme tokens."""
    return _mgr.tokens


def set_theme(theme_name: str, accent_color: str | None = None):
    """Switches the global application skin."""
    _mgr.set_theme(theme_name, accent_color)


def set_accent(hex_color: str) -> str:
    """Set the runtime primary accent color."""
    _mgr.set_accent(hex_color)
    return accent()


def accent() -> str:
    """Returns normalized lowercase hex (#rrggbb) of active accent."""
    return _mgr.tokens.accent.lower()


def accent_color() -> QColor:
    """Returns the current accent as a QColor instance."""
    return _mgr.tokens.accent_qcolor()


def accent_dark(factor: int = 125) -> str:
    return _mgr.tokens.accent_dark(factor)


def accent_light(factor: int = 120) -> str:
    return _mgr.tokens.accent_light(factor)


def accent_lighter(factor: int = 135) -> str:
    return _mgr.tokens.accent_lighter(factor)


def accent_rgba(alpha: float = 0.18) -> str:
    return _mgr.tokens.accent_rgba(alpha)


def generate_primary_gradient() -> str:
    """Generates dynamic linear gradient CSS for primary buttons."""
    top = accent_light()
    bottom = accent_dark()
    border = accent_lighter()
    return f"""
        QPushButton[primary="true"], QPushButton#btnGenerate {{
            font-size: 14px;
            font-weight: 900;
            color: #FFFFFF;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {top}, stop:1 {bottom});
            border: 1px solid {border};
            border-radius: {_mgr.tokens.border_radius}px;
        }}
        QPushButton[primary="true"]:hover, QPushButton#btnGenerate:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {accent_lighter()}, stop:1 {accent()});
            border-color: #FFFFFF;
        }}
        QPushButton[primary="true"]:pressed, QPushButton#btnGenerate:pressed {{
            background: {accent_dark()};
            border-color: {accent()};
        }}
    """


def build_stylesheet(hex_color: str | None = None) -> str:
    """Render the global stylesheet dynamically with active theme and accent."""
    if hex_color is not None:
        set_accent(hex_color)
    return _mgr.build_stylesheet()
