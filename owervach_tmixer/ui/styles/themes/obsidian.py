"""Obsidian Theme: Esports dark aesthetic."""

from __future__ import annotations
from owervach_tmixer.ui.styles.tokens import ThemeTokens
from .base import BaseTheme


class ObsidianTheme(BaseTheme):
    @property
    def default_tokens(self) -> ThemeTokens:
        return ThemeTokens(
            id="obsidian",
            display_name="Obsidian Esports",
            description="Fondo obsidiana puro con jerarquía profunda y acento Sathara neón.",
            bg_app="#121316",
            bg_surface="#16171E",
            bg_elevated="#1A1C24",
            bg_subtle="#14151B",
            bg_active_pill="rgba(97, 171, 2, 0.18)",
            text_primary="#FFFFFF",
            text_secondary="#9AA0B2",
            text_muted="#5D6273",
            border_subtle="#262936",
            border_medium="#323647",
            border_radius=6,
            font_family='"Segoe UI", "Helvetica Neue", Arial, sans-serif',
            font_family_display='"Segoe UI", "Helvetica Neue", Arial, sans-serif',
            accent="#61ab02",
            layout_type="classic",
            slot_empty_text="➕",
            slot_side_stripe=False,
            button_secondary_style="outline",
            vs_style="badge",
            winner_format_style="emoji",
            header_tab_style="pill",
            map_show_room_label=False,
            btn_generate_gradient=False,
        )
