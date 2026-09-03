"""Appearance settings: Theme accent, slot typography, Tier Maker sizes, and team names."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from owervach_tmixer.ui.styles import theme
from .common import create_card_box


def build_appearance_tab(dialog, layout: QVBoxLayout):
    box_accent = create_card_box("Color de Acento Principal (Sathara)")
    vbox_accent = QVBoxLayout(box_accent)
    vbox_accent.setSpacing(10)

    row = QHBoxLayout()
    row.setSpacing(8)

    dialog.btn_accent_swatch = QPushButton()
    dialog.btn_accent_swatch.setFixedSize(48, 28)
    dialog.btn_accent_swatch.setCursor(Qt.CursorShape.PointingHandCursor)
    dialog.btn_accent_swatch.clicked.connect(dialog._pick_accent_color)
    dialog.btn_accent_swatch.setToolTip("Abrir selector de color…")
    row.addWidget(dialog.btn_accent_swatch)

    hex_label = QLabel("HEX:")
    hex_label.setStyleSheet("color: #AAAAAA; font-weight: 700;")
    row.addWidget(hex_label)
    dialog.edit_hex = QLineEdit()
    dialog.edit_hex.setPlaceholderText("#RRGGBB")
    dialog.edit_hex.setMaximumWidth(110)
    dialog.edit_hex.textChanged.connect(dialog._on_hex_edited)
    row.addWidget(dialog.edit_hex)

    rgb_label = QLabel("RGB:")
    rgb_label.setStyleSheet("color: #AAAAAA; font-weight: 700;")
    row.addWidget(rgb_label)
    dialog.edit_rgb = QLineEdit()
    dialog.edit_rgb.setPlaceholderText("R, G, B")
    dialog.edit_rgb.setMaximumWidth(120)
    dialog.edit_rgb.textChanged.connect(dialog._on_rgb_edited)
    row.addWidget(dialog.edit_rgb)
    row.addStretch()
    vbox_accent.addLayout(row)

    dialog._accent_preset_group = QButtonGroup(dialog)
    dialog._accent_preset_group.setExclusive(True)
    dialog._accent_preset_hexes = {}
    presets = QHBoxLayout()
    presets.setSpacing(8)
    for name, hex_color in theme.PRESETS.items():
        btn = QPushButton(name)
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {hex_color}; color: #FFFFFF;
                font-weight: 700; padding: 6px 12px; border-radius: 6px;
            }}
        """)
        btn.toggled.connect(lambda on, h=hex_color: on and dialog._set_accent_hex(h))
        dialog._accent_preset_group.addButton(btn)
        dialog._accent_preset_hexes[btn] = hex_color
        presets.addWidget(btn)
    vbox_accent.addLayout(presets)

    dialog.btn_reset_accent = QPushButton("Restablecer Color Original (Verde Sathara)")
    dialog.btn_reset_accent.setCursor(Qt.CursorShape.PointingHandCursor)
    dialog.btn_reset_accent.setStyleSheet("padding: 6px 12px; font-weight: 700; font-size: 11px;")
    dialog.btn_reset_accent.clicked.connect(lambda: dialog._set_accent_hex(theme.DEFAULT_ACCENT))
    vbox_accent.addWidget(dialog.btn_reset_accent)
    layout.addWidget(box_accent)

    box_font = create_card_box("Tipografía y Anatomía de Jugadores en Equipos")
    form_font = QFormLayout(box_font)
    form_font.setSpacing(10)

    dialog.cb_dynamic_font = QComboBox()
    dialog.cb_dynamic_font.setView(QListView())
    dialog.cb_dynamic_font.addItem("Dinámico (Auto-escalable según espacio) — Recomendado", True)
    dialog.cb_dynamic_font.addItem("Fijo (Tamaño manual en px)", False)
    form_font.addRow("Escalado del nombre:", dialog.cb_dynamic_font)

    dialog.spin_slot_font_size = QSpinBox()
    dialog.spin_slot_font_size.setRange(10, 20)
    dialog.spin_slot_font_size.setValue(13)
    form_font.addRow("Tamaño base / fijo (px):", dialog.spin_slot_font_size)

    dialog.cb_slot_align = QComboBox()
    dialog.cb_slot_align.setView(QListView())
    dialog.cb_slot_align.addItem("Centrado (Predeterminado)", "center")
    dialog.cb_slot_align.addItem("Izquierda", "left")
    form_font.addRow("Alineación del nombre:", dialog.cb_slot_align)

    dialog.cb_slot_font_weight = QComboBox()
    dialog.cb_slot_font_weight.setView(QListView())
    dialog.cb_slot_font_weight.addItem("Negrita (Bold - 800)", "bold")
    dialog.cb_slot_font_weight.addItem("Mediana (Medium - 600)", "medium")
    dialog.cb_slot_font_weight.addItem("Normal (500)", "normal")
    form_font.addRow("Grosor del texto:", dialog.cb_slot_font_weight)

    dialog.cb_role_badge_style = QComboBox()
    dialog.cb_role_badge_style.setView(QListView())
    dialog.cb_role_badge_style.addItem("Solo Emoji (🛡️ / ⚔️ / 💉) — Máximo espacio", "emoji")
    dialog.cb_role_badge_style.addItem("Emoji + Inicial (🛡️ T / ⚔️ D / 💉 S)", "initial")
    dialog.cb_role_badge_style.addItem("Texto Completo (🛡️ TANK / ...)", "full")
    form_font.addRow("Estilo de rol:", dialog.cb_role_badge_style)

    dialog.cb_badge_outlines = QComboBox()
    dialog.cb_badge_outlines.setView(QListView())
    dialog.cb_badge_outlines.addItem("Sin bordes (Limpio y simétrico) — Predeterminado", False)
    dialog.cb_badge_outlines.addItem("Con bordes (Outlines de Rol + Habilidad en naranja)", True)
    form_font.addRow("Bordes en insignias:", dialog.cb_badge_outlines)
    layout.addWidget(box_font)

    box_tier = create_card_box("Dimensiones en Tier Maker")
    form_tier = QFormLayout(box_tier)
    form_tier.setSpacing(10)

    dialog.cb_tier_export_ratio = QComboBox()
    dialog.cb_tier_export_ratio.setView(QListView())
    dialog.cb_tier_export_ratio.addItem("16:9 (Panorámico / Redes Sociales) — Recomendado", "16:9")
    dialog.cb_tier_export_ratio.addItem("Automático (Ajuste libre al contenido)", "auto")
    form_tier.addRow("Formato al exportar imagen:", dialog.cb_tier_export_ratio)

    dialog.spin_tier_hero_size = QSpinBox()
    dialog.spin_tier_hero_size.setRange(50, 120)
    dialog.spin_tier_hero_size.setValue(76)
    form_tier.addRow("Tamaño de retratos de héroe (px):", dialog.spin_tier_hero_size)

    dialog.spin_tier_map_w = QSpinBox()
    dialog.spin_tier_map_w.setRange(80, 220)
    dialog.spin_tier_map_w.setValue(125)
    form_tier.addRow("Ancho de tarjetas de mapas (px):", dialog.spin_tier_map_w)

    dialog.spin_tier_map_h = QSpinBox()
    dialog.spin_tier_map_h.setRange(45, 120)
    dialog.spin_tier_map_h.setValue(75)
    form_tier.addRow("Alto de tarjetas de mapas (px):", dialog.spin_tier_map_h)

    dialog.spin_tier_map_font = QSpinBox()
    dialog.spin_tier_map_font.setRange(10, 24)
    dialog.spin_tier_map_font.setValue(14)
    form_tier.addRow("Tamaño de texto en mapas (px):", dialog.spin_tier_map_font)

    dialog.spin_tier_player_w = QSpinBox()
    dialog.spin_tier_player_w.setRange(80, 220)
    dialog.spin_tier_player_w.setValue(125)
    form_tier.addRow("Ancho de tarjetas de jugadores (px):", dialog.spin_tier_player_w)

    dialog.spin_tier_player_h = QSpinBox()
    dialog.spin_tier_player_h.setRange(45, 120)
    dialog.spin_tier_player_h.setValue(75)
    form_tier.addRow("Alto de tarjetas de jugadores (px):", dialog.spin_tier_player_h)
    layout.addWidget(box_tier)

    box_teams = create_card_box("Nombres de Equipo Predeterminados")
    form_teams = QFormLayout(box_teams)
    form_teams.setSpacing(10)
    dialog.edit_team1 = QLineEdit()
    form_teams.addRow("Equipo 1:", dialog.edit_team1)
    dialog.edit_team2 = QLineEdit()
    form_teams.addRow("Equipo 2:", dialog.edit_team2)
    layout.addWidget(box_teams)
