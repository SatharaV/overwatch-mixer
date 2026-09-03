"""Esports Header Bar containing branding, tab navigation, mode switch, and quick control pills."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from owervach_tmixer.core.models import GameMode
from owervach_tmixer.ui.styles import theme
from owervach_tmixer.ui.widgets.mode_toggle import ModeSwitch
from owervach_tmixer.utils import get_resource_path

ASSETS_DIR = get_resource_path("assets")


class HeaderBar(QWidget):
    """Top navigation and command header for Overwatch Team Mixer."""

    nav_tab_clicked = Signal(int)
    mode_changed = Signal(object)
    show_roles_toggled = Signal(bool)
    randomize_roles_toggled = Signal(bool)
    tryhard_toggled = Signal(bool)
    settings_clicked = Signal()

    def __init__(self, initial_mode: GameMode, show_roles: bool, auto_roles: bool, balance_by_mmr: bool, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(54)
        self.setStyleSheet("""
            QWidget#headerBar {
                background-color: #16171B;
                border-bottom: 1px solid #282A30;
            }
        """)
        self.setObjectName("headerBar")

        self._setup_ui(initial_mode, show_roles, auto_roles, balance_by_mmr)
        self.apply_theme(0)

    def _setup_ui(self, initial_mode: GameMode, show_roles: bool, auto_roles: bool, balance_by_mmr: bool):
        hlayout = QHBoxLayout(self)
        hlayout.setContentsMargins(8, 0, 8, 0)
        hlayout.setSpacing(5)

        # 1. Branding
        brand_label = QLabel("⚔️ OW MIXER")
        brand_label.setStyleSheet("font-size: 13px; font-weight: 900; color: #FFFFFF; background: transparent; border: none;")
        hlayout.addWidget(brand_label, 0)

        sep = QFrame(self)
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedHeight(24)
        sep.setStyleSheet("background-color: #2D3038; max-width: 1px; border: none;")
        hlayout.addWidget(sep, 0)

        # 2. Navigation Tabs
        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_buttons: list[QPushButton] = []

        tabs_data = [
            ("🎮 Partida", 0),
            ("🗺️ Mapas", 1),
            ("⛔ Baneos", 2),
            ("📊 Tier Maker", 3),
            ("📜 Historial", 4),
        ]

        for text, idx in tabs_data:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("tab_idx", idx)
            btn.clicked.connect(lambda _, i=idx: self.nav_tab_clicked.emit(i))
            self._nav_group.addButton(btn)
            self._nav_buttons.append(btn)
            hlayout.addWidget(btn)
            if idx == 0:
                btn.setChecked(True)

        hlayout.addStretch(1)

        # 3. Mode Switch (5v5 / 6v6)
        self.mode_switch = ModeSwitch(initial_mode)
        self.mode_switch.mode_changed.connect(self.mode_changed.emit)
        hlayout.addWidget(self.mode_switch, 0)

        # 4. Quick Pills
        self.roles_toggle = QPushButton("🛡️ Roles")
        self.roles_toggle.setCheckable(True)
        self.roles_toggle.setToolTip("Mostrar/ocultar los roles en las tarjetas de jugadores")
        self.roles_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.roles_toggle.setChecked(show_roles)
        self.roles_toggle.toggled.connect(self.show_roles_toggled.emit)
        hlayout.addWidget(self.roles_toggle, 0)

        self.randomize_roles_toggle = QPushButton("🎲 Auto")
        self.randomize_roles_toggle.setCheckable(True)
        self.randomize_roles_toggle.setToolTip("Randomizar los roles automáticamente al mezclar")
        self.randomize_roles_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.randomize_roles_toggle.setChecked(auto_roles)
        self.randomize_roles_toggle.toggled.connect(self.randomize_roles_toggled.emit)
        hlayout.addWidget(self.randomize_roles_toggle, 0)

        self.tryhard_toggle = QPushButton("⚖️ Tryhard")
        self.tryhard_toggle.setCheckable(True)
        self.tryhard_toggle.setToolTip("Modo Tryhard: Balanceo estricto por nivel/MMR entre ambos equipos")
        self.tryhard_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tryhard_toggle.setChecked(balance_by_mmr)
        self.tryhard_toggle.toggled.connect(self.tryhard_toggled.emit)
        hlayout.addWidget(self.tryhard_toggle, 0)

        # 5. Settings Button
        self.btn_settings = QPushButton()
        self.btn_settings.setToolTip("Configuración de la aplicación")
        self.btn_settings.setFixedSize(34, 34)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setIcon(QIcon(str(ASSETS_DIR / "settings.svg")))
        self.btn_settings.setIconSize(QSize(18, 18))
        self.btn_settings.setStyleSheet("""
            QPushButton {
                border: 1px solid #33363F;
                border-radius: 6px;
                background-color: #1E2026;
            }
            QPushButton:hover {
                background-color: #2A2D36;
                border-color: #555A68;
            }
            QPushButton:pressed { background-color: #141518; }
        """)
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        hlayout.addWidget(self.btn_settings, 0)

    def apply_theme(self, current_tab_idx: int = 0):
        accent = theme.accent()
        bg_active = theme.accent_rgba(0.12)
        border_active = theme.accent_rgba(0.40)

        for btn in self._nav_buttons:
            is_active = (btn.property("tab_idx") == current_tab_idx)
            btn.blockSignals(True)
            btn.setChecked(is_active)
            btn.blockSignals(False)
            if is_active:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        font-size: 12px;
                        font-weight: 800;
                        color: {accent};
                        background-color: {bg_active};
                        border: 1px solid {border_active};
                        border-radius: 6px;
                        padding: 4px 7px;
                        font-size: 11.5px;
                    }}
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        font-size: 12px;
                        font-weight: 700;
                        color: #9A9FA8;
                        background-color: transparent;
                        border: 1px solid transparent;
                        border-radius: 6px;
                        padding: 4px 7px;
                        font-size: 11.5px;
                    }
                    QPushButton:hover {
                        color: #FFFFFF;
                        background-color: #22252C;
                    }
                """)

        self.mode_switch.apply_theme()
        self.update_pill_style(self.roles_toggle, "#00B4FF")
        self.update_pill_style(self.randomize_roles_toggle, accent)
        self.update_pill_style(self.tryhard_toggle, "#9D5CFF")

    def update_pill_style(self, btn: QPushButton, active_color: str):
        is_enabled = btn.isEnabled()
        is_on = btn.isChecked() and is_enabled

        if not is_enabled:
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 11px;
                    font-weight: 700;
                    color: #484B54;
                    background-color: #16171B;
                    border: 1px solid #23252C;
                    border-radius: 5px;
                    padding: 4px 7px;
                    font-size: 10.5px;
                }
            """)
        elif is_on:
            btn.setStyleSheet(f"""
                QPushButton {{
                    font-size: 11px;
                    font-weight: 800;
                    color: {active_color};
                    background-color: rgba(255, 255, 255, 0.08);
                    border: 1px solid {active_color};
                    border-radius: 5px;
                    padding: 4px 7px;
                    font-size: 10.5px;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.14);
                }}
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 11px;
                    font-weight: 700;
                    color: #727680;
                    background-color: #1F2127;
                    border: 1px solid #2F323A;
                    border-radius: 5px;
                    padding: 4px 7px;
                    font-size: 10.5px;
                }
                QPushButton:hover {
                    color: #CCCCCC;
                    background-color: #282B33;
                    border-color: #404450;
                }
            """)
