"""Overwatch Header Bar featuring full-height Blizzard tabs with continuous cyan baseline."""

from __future__ import annotations

from typing import TYPE_CHECKING
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from owervach_tmixer.core.models import GameMode
from owervach_tmixer.ui.styles import theme
from owervach_tmixer.ui.widgets.mode_toggle import ModeSwitch
from owervach_tmixer.ui.widgets.vector_button import VectorIconButton


class HeaderBar(QWidget):
    """Top navigation bar replicating Blizzard's full-height flush tabs and status area."""

    nav_tab_clicked = Signal(int)
    mode_changed = Signal(object)
    show_roles_toggled = Signal(bool)
    randomize_roles_toggled = Signal(bool)
    tryhard_toggled = Signal(bool)
    rotation_toggled = Signal(bool)
    settings_clicked = Signal()

    def __init__(self, initial_mode: GameMode, show_roles: bool, auto_roles: bool, balance_by_mmr: bool, bench_rotation_enabled: bool = False, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setObjectName("headerBar")

        self._setup_ui(initial_mode, show_roles, auto_roles, balance_by_mmr, bench_rotation_enabled)
        self.apply_theme(0)

    def _setup_ui(self, initial_mode: GameMode, show_roles: bool, auto_roles: bool, balance_by_mmr: bool, bench_rotation_enabled: bool = False):
        hlayout = QHBoxLayout(self)
        # Margen 0 vertical para que las pestañas toquen el techo y el piso de la barra
        hlayout.setContentsMargins(0, 0, 10, 0)
        hlayout.setSpacing(0)

        # 1. Pestañas de Navegación Full-Height
        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_buttons: list[QPushButton] = []

        tabs_data = [
            ("PARTIDA", 0),
            ("MAPAS", 1),
            ("BANEOS", 2),
            ("TIER MAKER", 3),
            ("HISTORIAL", 4),
        ]

        for text, idx in tabs_data:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("tab_idx", idx)
            btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
            btn.clicked.connect(lambda _, i=idx: self.nav_tab_clicked.emit(i))
            self._nav_group.addButton(btn)
            self._nav_buttons.append(btn)
            hlayout.addWidget(btn)
            if idx == 0:
                btn.setChecked(True)

        hlayout.addStretch(1)

        # Controles utilitarios a la derecha con spacing limpio
        tools_widget = QWidget(self)
        t_layout = QHBoxLayout(tools_widget)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(6)

        self.mode_switch = ModeSwitch(initial_mode)
        self.mode_switch.mode_changed.connect(self.mode_changed.emit)
        t_layout.addWidget(self.mode_switch, 0)

        self.roles_toggle = QPushButton("ROLES")
        self.roles_toggle.setCheckable(True)
        self.roles_toggle.setToolTip("Mostrar/ocultar roles en ranuras")
        self.roles_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.roles_toggle.setChecked(show_roles)
        self.roles_toggle.toggled.connect(self.show_roles_toggled.emit)
        t_layout.addWidget(self.roles_toggle, 0)

        self.randomize_roles_toggle = QPushButton("AUTO")
        self.randomize_roles_toggle.setCheckable(True)
        self.randomize_roles_toggle.setToolTip("Randomizar roles automáticamente al mezclar")
        self.randomize_roles_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.randomize_roles_toggle.setChecked(auto_roles)
        self.randomize_roles_toggle.toggled.connect(self.randomize_roles_toggled.emit)
        t_layout.addWidget(self.randomize_roles_toggle, 0)

        self.tryhard_toggle = QPushButton("TRYHARD")
        self.tryhard_toggle.setCheckable(True)
        self.tryhard_toggle.setToolTip("Balanceo estricto por nivel/MMR")
        self.tryhard_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tryhard_toggle.setChecked(balance_by_mmr)
        self.tryhard_toggle.toggled.connect(self.tryhard_toggled.emit)
        t_layout.addWidget(self.tryhard_toggle, 0)

        self.rotation_toggle = QPushButton("ROTAR")
        self.rotation_toggle.setCheckable(True)
        self.rotation_toggle.setToolTip("Rotación continua de jugadores")
        self.rotation_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rotation_toggle.setChecked(bench_rotation_enabled)
        self.rotation_toggle.toggled.connect(self.rotation_toggled.emit)
        t_layout.addWidget(self.rotation_toggle, 0)

        self.btn_settings = VectorIconButton(
            icon_type="gear",
            tooltip="Configuración del Sistema",
            size=(28, 28),
            parent=self,
        )
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        t_layout.addWidget(self.btn_settings, 0)

        hlayout.addWidget(tools_widget, 0, Qt.AlignVCenter)

    def apply_theme(self, current_tab_idx: int = 0):
        t = theme.tokens()
        accent = t.accent
        is_ow = (t.header_tab_style == "flush_baseline")

        tab_labels_ow = ["PARTIDA", "MAPAS", "BANEOS", "TIER MAKER", "HISTORIAL"]
        tab_labels_std = ["🎮 Partida", "🗺️ Mapas", "⛔ Baneos", "📊 Tier Maker", "📜 Historial"]

        bg_header = "#060B14" if is_ow else t.bg_surface
        border_b = "border-bottom: 2px solid rgba(0, 240, 255, 0.45);" if is_ow else f"border-bottom: 1px solid {t.border_subtle};"

        self.setStyleSheet(f"""
            QWidget#headerBar {{
                background-color: {bg_header};
                {border_b}
            }}
        """)

        for btn in self._nav_buttons:
            idx = btn.property("tab_idx")
            is_active = (idx == current_tab_idx)
            btn.blockSignals(True)
            btn.setText(tab_labels_ow[idx] if is_ow else tab_labels_std[idx])
            btn.setChecked(is_active)
            btn.blockSignals(False)

            if is_ow:
                f_disp = t.font_family_display
                if is_active:
                    # Pestaña activa ocupando el 100% de la altura vertical con línea cian neón abajo
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            font-family: {f_disp};
                            font-size: 17px;
                            font-weight: 900;
                            font-style: italic;
                            color: #FFFFFF;
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0060E6, stop:1 #0044B8);
                            border: none;
                            border-bottom: 3.5px solid #00F0FF;
                            padding: 0px 22px;
                            letter-spacing: 1px;
                        }}
                    """)
                else:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            font-family: {f_disp};
                            font-size: 17px;
                            font-weight: 900;
                            font-style: italic;
                            color: #A4B6CC;
                            background-color: transparent;
                            border: none;
                            border-bottom: 3.5px solid transparent;
                            padding: 0px 18px;
                            letter-spacing: 1px;
                        }}
                        QPushButton:hover {{
                            color: #FFFFFF;
                            background-color: rgba(255, 255, 255, 0.08);
                            border-bottom: 3.5px solid rgba(0, 240, 255, 0.40);
                        }}
                    """)
            else:
                if is_active:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            font-size: 11.5px; font-weight: 800; color: {accent};
                            background-color: {theme.accent_rgba(0.14)};
                            border: 1px solid {accent}; border-radius: 6px; padding: 4px 10px; margin: 6px 2px;
                        }}
                    """)
                else:
                    btn.setStyleSheet("""
                        QPushButton {
                            font-size: 11.5px; font-weight: 700; color: #9A9FA8;
                            background-color: transparent; border: 1px solid transparent;
                            border-radius: 6px; padding: 4px 10px; margin: 6px 2px;
                        }
                        QPushButton:hover { color: #FFFFFF; background-color: #22252C; }
                    """)

        if is_ow:
            self.roles_toggle.setText("ROLES")
            self.randomize_roles_toggle.setText("AUTO")
            self.tryhard_toggle.setText("TRYHARD")
            self.rotation_toggle.setText("ROTAR")
        else:
            self.roles_toggle.setText("🛡️ Roles")
            self.randomize_roles_toggle.setText("🎲 Auto")
            self.tryhard_toggle.setText("⚖️ Tryhard")
            self.rotation_toggle.setText("🔄 Rotar")

        self.mode_switch.apply_theme()
        self.update_pill_style(self.roles_toggle, "#00B4FF")
        self.update_pill_style(self.randomize_roles_toggle, accent)
        self.update_pill_style(self.tryhard_toggle, "#9D5CFF")
        self.update_pill_style(self.rotation_toggle, "#FFAA00")

    def update_pill_style(self, btn: QPushButton, active_color: str):
        is_ow = (theme.tokens().header_tab_style == "flush_baseline")
        is_on = btn.isChecked() and btn.isEnabled()

        if is_ow:
            f_family = '"Futura", "Segoe UI", sans-serif'
            if is_on:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        font-family: {f_family};
                        font-size: 11px;
                        font-weight: 900;
                        color: #FFFFFF;
                        background-color: {active_color};
                        border: none;
                        border-radius: 2px;
                        padding: 5px 9px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        font-family: {f_family};
                        font-size: 11px;
                        font-weight: 700;
                        color: #8C9EB5;
                        background-color: rgba(14, 24, 40, 0.75);
                        border: none;
                        border-radius: 2px;
                        padding: 5px 9px;
                    }}
                    QPushButton:hover {{
                        color: #FFFFFF;
                        background-color: rgba(28, 44, 70, 0.90);
                    }}
                """)
        else:
            if is_on:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        font-size: 10.5px; font-weight: 800; color: {active_color};
                        background-color: rgba(255, 255, 255, 0.08);
                        border: 1px solid {active_color}; border-radius: 5px; padding: 4px 7px;
                    }}
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        font-size: 10.5px; font-weight: 700; color: #727680;
                        background-color: #1F2127; border: 1px solid #2F323A;
                        border-radius: 5px; padding: 4px 7px;
                    }
                    QPushButton:hover { color: #CCCCCC; background-color: #282B33; }
                """)
