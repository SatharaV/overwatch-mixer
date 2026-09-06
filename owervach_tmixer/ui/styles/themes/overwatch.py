"""Overwatch UI Theme: Authentic Blizzard dark space navy aesthetic."""

from __future__ import annotations
from owervach_tmixer.ui.styles.tokens import ThemeTokens
from .base import BaseTheme


class OverwatchUITheme(BaseTheme):
    """Deep space navy, full-height electric blue tabs with cyan neon baseline, Futura UI, and Big Noodle Display."""

    @property
    def default_tokens(self) -> ThemeTokens:
        return ThemeTokens(
            id="overwatch",
            display_name="Overwatch UI",
            description="Interfaz oficial de Overwatch: azul marino espacial, pestañas full-height y cian neón.",
            # Fondo azul marino espacial oficial de Overwatch
            bg_app="qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0E182A, stop:0.35 #0A1220, stop:0.75 #070D17, stop:1 #04080F)",
            bg_surface="rgba(13, 22, 36, 0.94)",
            bg_elevated="rgba(20, 32, 52, 0.95)",
            bg_subtle="#060B12",
            bg_active_pill="rgba(249, 158, 26, 0.22)",
            text_primary="#FFFFFF",
            text_secondary="#B8C8D8",
            text_muted="#5D708A",
            border_subtle="transparent",
            border_medium="#00F0FF",
            border_radius=3,
            font_family='"Futura", "Segoe UI", Arial, sans-serif',
            font_family_display='"Big Noodle Titling", "Futura", sans-serif',
            accent="#F99E1A",
            info="#00F0FF",
            warning="#FFAA00",
            danger="#FF4444",
            success="#20C997",
            layout_type="tactical_overwatch",
            slot_empty_text="VACÍO",
            slot_side_stripe=True,
            button_secondary_style="ice_white",
            vs_style="monumental",
            winner_format_style="display_caps",
            header_tab_style="flush_baseline",
            map_show_room_label=True,
            btn_generate_gradient=True,
        )
