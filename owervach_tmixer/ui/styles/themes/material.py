"""Material Design Theme: Google MD3 dark surface elevations."""

from __future__ import annotations
from owervach_tmixer.ui.styles.tokens import ThemeTokens
from .base import BaseTheme


class MaterialTheme(BaseTheme):
    @property
    def default_tokens(self) -> ThemeTokens:
        return ThemeTokens(
            id="material",
            display_name="Material Design 3",
            description="Curvas suaves, elevaciones tonales MD3 y estética moderna tipo Android.",
            bg_app="#141218",
            bg_surface="#1D1B20",
            bg_elevated="#2B2930",
            bg_subtle="#211F26",
            bg_active_pill="rgba(208, 188, 255, 0.18)",
            text_primary="#E6E0E9",
            text_secondary="#CAC4D0",
            text_muted="#79747E",
            border_subtle="#49454F",
            border_medium="#635E6B",
            border_radius=12,
            font_family='"Roboto", "Product Sans", "Segoe UI", sans-serif',
            font_family_display='"Roboto", "Product Sans", "Segoe UI", sans-serif',
            accent="#D0BCFF",
        )
