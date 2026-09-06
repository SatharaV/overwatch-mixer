"""Design System Semantic Tokens for Overwatch Team Mixer."""

from __future__ import annotations
from dataclasses import dataclass
from PySide6.QtGui import QColor


@dataclass(frozen=True)
class ThemeTokens:
    """Immutable semantic design tokens consumed by all themes and widgets."""

    id: str
    display_name: str
    description: str

    bg_app: str
    bg_surface: str
    bg_elevated: str
    bg_subtle: str
    bg_active_pill: str

    text_primary: str
    text_secondary: str
    text_muted: str

    border_subtle: str
    border_medium: str
    border_radius: int

    font_family: str          # Fuente base de interfaz (ej. Futura)
    font_family_display: str  # Fuente de titulares/impacto (ej. Big Noodle Titling)

    accent: str

    success: str = "#20C997"
    warning: str = "#FFAA00"
    danger: str = "#FF4444"
    info: str = "#00F0FF"

    layout_type: str = "classic"
    slot_empty_text: str = "➕"
    slot_side_stripe: bool = False
    button_secondary_style: str = "outline"
    vs_style: str = "badge"
    winner_format_style: str = "emoji"
    header_tab_style: str = "pill"
    map_show_room_label: bool = False
    btn_generate_gradient: bool = False

    def __post_init__(self):
        object.__setattr__(self, "accent", self.accent.lower())

    def accent_qcolor(self) -> QColor:
        return QColor(self.accent)

    def accent_rgba(self, alpha: float = 0.18) -> str:
        c = self.accent_qcolor()
        return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alpha:.2f})"

    def accent_dark(self, factor: int = 125) -> str:
        return self.accent_qcolor().darker(factor).name().lower()

    def accent_light(self, factor: int = 120) -> str:
        return self.accent_qcolor().lighter(factor).name().lower()

    def accent_lighter(self, factor: int = 135) -> str:
        return self.accent_qcolor().lighter(factor).name().lower()
