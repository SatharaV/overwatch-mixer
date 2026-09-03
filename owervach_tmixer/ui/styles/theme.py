"""Universal Theme Provider & Dynamic Color Engine for Overwatch Team Mixer."""

from __future__ import annotations

from PySide6.QtGui import QColor
from owervach_tmixer.ui.styles.stylesheet import STYLESHEET_TEMPLATE

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

_accent = QColor(DEFAULT_ACCENT)


def set_accent(hex_color: str) -> str:
    """Set the runtime primary accent color."""
    global _accent
    _accent = QColor(hex_color)
    if not _accent.isValid():
        _accent = QColor(DEFAULT_ACCENT)
    return accent()


def accent() -> str:
    """Returns normalized lowercase hex (#rrggbb)."""
    return _accent.name().lower()


def accent_color() -> QColor:
    """Returns the current accent as a QColor instance."""
    return QColor(_accent)


def accent_dark() -> str:
    """Darker shade for hover/pressed states."""
    return _accent.darker(122).name().lower()


def accent_light() -> str:
    """Lighter highlight shade."""
    return _accent.lighter(116).name().lower()


def accent_lighter() -> str:
    """Extra bright highlight shade."""
    return _accent.lighter(132).name().lower()


def accent_rgba(alpha: float = 0.15) -> str:
    """Generates an rgba(...) string using the current accent."""
    return f"rgba({_accent.red()}, {_accent.green()}, {_accent.blue()}, {alpha:.2f})"


def generate_primary_gradient() -> str:
    """Generates a dynamic linear gradient CSS using current theme accent shades."""
    top = accent_light()
    bottom = accent_dark()
    border = accent_lighter()
    return f"""
        QPushButton[primary="true"], QPushButton#btnGenerate {{
            font-size: 14px;
            font-weight: 900;
            color: #050505;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {top}, stop:1 {bottom});
            border: 1px solid {border};
            border-radius: 8px;
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
    """Render the global stylesheet dynamically with the active accent."""
    if hex_color is not None:
        set_accent(hex_color)

    acc = accent()
    acc_dark = accent_dark()
    acc_light = accent_light()

    css = STYLESHEET_TEMPLATE
    css = css.replace("@ACCENT@", acc)
    css = css.replace("@ACCENT_DARK@", acc_dark)
    css = css.replace("@ACCENT_LIGHT@", acc_light)
    css = css.replace("@ACCENT_LIGHTER@", accent_lighter())
    css = css.replace("@ACCENT_RGBA_12@", accent_rgba(0.12))
    css = css.replace("@ACCENT_RGBA_14@", accent_rgba(0.14))
    css = css.replace("@ACCENT_RGBA_18@", accent_rgba(0.18))
    css = css.replace("@ACCENT_RGBA_22@", accent_rgba(0.22))
    css = css.replace("@ACCENT_RGBA_40@", accent_rgba(0.40))
    return css
