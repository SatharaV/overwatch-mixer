"""Settings panel widget."""

from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QSpinBox, QCheckBox, QLineEdit, QComboBox,
    QGroupBox, QFormLayout, QMessageBox, QFileDialog,
    QTabWidget, QScrollArea
)
from PySide6.QtGui import QAction

from owervach_tmixer.core.models import GameMode, ShuffleMode, TeamComposition, MatchSettings
from owervach_tmixer.core.settings import SettingsManager


class SettingsPanel(QWidget):
    """Settings configuration panel."""

    settings_changed = Signal(object)  # MatchSettings
    reset_requested = Signal()

    def __init__(self, settings_manager: SettingsManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self._setup_ui()
        self._load_current_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Tabs
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget, 1)

        # Tab 1: Partida
        self.tab_match = self._create_match_tab()
        self.tab_widget.addTab(self.tab_match, "Partida")

        # Tab 2: Mezcla
        self.tab_shuffle = self._create_shuffle_tab()
        self.tab_widget.addTab(self.tab_shuffle, "Mezcla")

        # Tab 3: Roles
        self.tab_roles = self._create_roles_tab()
        self.tab_widget.addTab(self.tab_roles, "Roles")

        # Tab 4: Mapas
        self.tab_maps = self._create_maps_tab()
        self.tab_widget.addTab(self.tab_maps, "Mapas")

        # Tab 5: Baneos
        self.tab_bans = self._create_bans_tab()
        self.tab_widget.addTab(self.tab_bans, "Baneos")

        # Tab 6: Equipos
        self.tab_teams = self._create_teams_tab()
        self.tab_widget.addTab(self.tab_teams, "Equipos")

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_import = QPushButton("Importar ajustes")
        self.btn_import.clicked.connect(self._import_settings)
        btn_layout.addWidget(self.btn_import)

        self.btn_export = QPushButton("Exportar ajustes")
        self.btn_export.clicked.connect(self._export_settings)
        btn_layout.addWidget(self.btn_export)

        self.btn_reset = QPushButton("Restablecer")
        self.btn_reset.setProperty("danger", True)
        self.btn_reset.clicked.connect(self._reset_settings)
        btn_layout.addWidget(self.btn_reset)

        layout.addLayout(btn_layout)

    def _create_match_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Game mode
        mode_group = QGroupBox("Modo de partida")
        mode_layout = QHBoxLayout(mode_group)

        self.rb_5v5 = QRadioButton("5v5 (10 jugadores)")
        self.rb_5v5.setChecked(True)
        self.rb_5v5.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self.rb_5v5)

        self.rb_6v6 = QRadioButton("6v6 (12 jugadores)")
        self.rb_6v6.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self.rb_6v6)

        layout.addWidget(mode_group)

        layout.addStretch()
        return tab

    def _create_shuffle_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Shuffle mode
        shuffle_group = QGroupBox("Modo de mezcla")
        shuffle_layout = QVBoxLayout(shuffle_group)

        self.cb_shuffle_mode = QComboBox()
        for mode in ShuffleMode:
            self.cb_shuffle_mode.addItem(mode.display_name, mode)
        self.cb_shuffle_mode.currentIndexChanged.connect(self._on_shuffle_mode_changed)
        shuffle_layout.addWidget(QLabel("Algoritmo:"))
        shuffle_layout.addWidget(self.cb_shuffle_mode)

        # Description
        self.shuffle_desc = QLabel()
        self.shuffle_desc.setWordWrap(True)
        self.shuffle_desc.setStyleSheet("color: #999999; font-size: 12px; padding: 8px;")
        shuffle_layout.addWidget(self.shuffle_desc)

        layout.addWidget(shuffle_group)

        # Diversity candidates
        div_group = QGroupBox("Diversidad (para 'Máxima variedad')")
        div_layout = QFormLayout(div_group)

        self.spin_candidates = QSpinBox()
        self.spin_candidates.setRange(10, 500)
        self.spin_candidates.setValue(50)
        self.spin_candidates.setSingleStep(10)
        self.spin_candidates.valueChanged.connect(self._on_candidates_changed)
        div_layout.addRow("Candidatos a evaluar:", self.spin_candidates)

        layout.addWidget(div_group)

        # History size
        hist_group = QGroupBox("Historial")
        hist_layout = QFormLayout(hist_group)

        self.spin_history = QSpinBox()
        self.spin_history.setRange(5, 100)
        self.spin_history.setValue(10)
        self.spin_history.valueChanged.connect(self._on_history_changed)
        hist_layout.addRow("Tamaño del historial:", self.spin_history)

        layout.addWidget(hist_group)

        layout.addStretch()
        return tab

    def _create_roles_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Auto roles
        self.chk_auto_roles = QCheckBox("Randomizar roles automáticamente al generar partida")
        self.chk_auto_roles.setChecked(True)
        self.chk_auto_roles.toggled.connect(self._on_auto_roles_changed)
        layout.addWidget(self.chk_auto_roles)

        # 5v5 composition
        comp5_group = QGroupBox("Composición 5v5 (por equipo)")
        comp5_layout = QFormLayout(comp5_group)

        self.spin_5v5_tank = QSpinBox()
        self.spin_5v5_tank.setRange(0, 5)
        self.spin_5v5_tank.setValue(1)
        self.spin_5v5_tank.valueChanged.connect(self._on_comp5_changed)
        comp5_layout.addRow("Tanques:", self.spin_5v5_tank)

        self.spin_5v5_damage = QSpinBox()
        self.spin_5v5_damage.setRange(0, 5)
        self.spin_5v5_damage.setValue(2)
        self.spin_5v5_damage.valueChanged.connect(self._on_comp5_changed)
        comp5_layout.addRow("Daño:", self.spin_5v5_damage)

        self.spin_5v5_support = QSpinBox()
        self.spin_5v5_support.setRange(0, 5)
        self.spin_5v5_support.setValue(2)
        self.spin_5v5_support.valueChanged.connect(self._on_comp5_changed)
        comp5_layout.addRow("Apoyo:", self.spin_5v5_support)

        self.lbl_5v5_total = QLabel("Total: 5")
        self.lbl_5v5_total.setStyleSheet("font-weight: 600; color: #FF7B00;")
        comp5_layout.addRow(self.lbl_5v5_total)

        layout.addWidget(comp5_group)

        # 6v6 composition
        comp6_group = QGroupBox("Composición 6v6 (por equipo)")
        comp6_layout = QFormLayout(comp6_group)

        self.spin_6v6_tank = QSpinBox()
        self.spin_6v6_tank.setRange(0, 6)
        self.spin_6v6_tank.setValue(2)
        self.spin_6v6_tank.valueChanged.connect(self._on_comp6_changed)
        comp6_layout.addRow("Tanques:", self.spin_6v6_tank)

        self.spin_6v6_damage = QSpinBox()
        self.spin_6v6_damage.setRange(0, 6)
        self.spin_6v6_damage.setValue(2)
        self.spin_6v6_damage.valueChanged.connect(self._on_comp6_changed)
        comp6_layout.addRow("Daño:", self.spin_6v6_damage)

        self.spin_6v6_support = QSpinBox()
        self.spin_6v6_support.setRange(0, 6)
        self.spin_6v6_support.setValue(2)
        self.spin_6v6_support.valueChanged.connect(self._on_comp6_changed)
        comp6_layout.addRow("Apoyo:", self.spin_6v6_support)

        self.lbl_6v6_total = QLabel("Total: 6")
        self.lbl_6v6_total.setStyleSheet("font-weight: 600; color: #FF7B00;")
        comp6_layout.addRow(self.lbl_6v6_total)

        layout.addWidget(comp6_group)

        layout.addStretch()
        return tab

    def _create_maps_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        self.chk_auto_map = QCheckBox("Randomizar mapa automáticamente al generar partida")
        self.chk_auto_map.setChecked(True)
        self.chk_auto_map.toggled.connect(self._on_auto_map_changed)
        layout.addWidget(self.chk_auto_map)

        # Avoid recent
        avoid_group = QGroupBox("Evitar mapas recientes")
        avoid_layout = QFormLayout(avoid_group)

        self.spin_avoid_maps = QSpinBox()
        self.spin_avoid_maps.setRange(0, 20)
        self.spin_avoid_maps.setValue(3)
        self.spin_avoid_maps.valueChanged.connect(self._on_avoid_maps_changed)
        avoid_layout.addRow("Mapas a evitar:", self.spin_avoid_maps)

        layout.addWidget(avoid_group)

        layout.addStretch()
        return tab

    def _create_bans_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        self.chk_auto_bans = QCheckBox("Randomizar baneos automáticamente al generar partida")
        self.chk_auto_bans.setChecked(False)
        self.chk_auto_bans.toggled.connect(self._on_auto_bans_changed)
        layout.addWidget(self.chk_auto_bans)

        # Max bans
        bans_group = QGroupBox("Límite de baneos")
        bans_layout = QFormLayout(bans_group)

        self.spin_max_bans = QSpinBox()
        self.spin_max_bans.setRange(0, 20)
        self.spin_max_bans.setValue(4)
        self.spin_max_bans.valueChanged.connect(self._on_max_bans_changed)
        bans_layout.addRow("Máximo baneos:", self.spin_max_bans)

        layout.addWidget(bans_group)

        layout.addStretch()
        return tab

    def _create_teams_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        team_group = QGroupBox("Nombres de equipos por defecto")
        team_layout = QFormLayout(team_group)

        self.edit_team1 = QLineEdit()
        self.edit_team1.setText("Team Overwatch")
        self.edit_team1.textChanged.connect(self._on_team_names_changed)
        team_layout.addRow("Equipo 1:", self.edit_team1)

        self.edit_team2 = QLineEdit()
        self.edit_team2.setText("Los Perritos")
        self.edit_team2.textChanged.connect(self._on_team_names_changed)
        team_layout.addRow("Equipo 2:", self.edit_team2)

        layout.addWidget(team_group)

        layout.addStretch()
        return tab

    def _load_current_settings(self):
        s = self.settings_manager.settings

        # Game mode
        self.rb_5v5.setChecked(s.game_mode == GameMode.FIVE_V_FIVE)
        self.rb_6v6.setChecked(s.game_mode == GameMode.SIX_V_SIX)

        # Shuffle mode
        for i in range(self.cb_shuffle_mode.count()):
            if self.cb_shuffle_mode.itemData(i) == s.shuffle_mode:
                self.cb_shuffle_mode.setCurrentIndex(i)
                break

        self.spin_candidates.setValue(s.diversity_candidates)
        self.spin_history.setValue(s.history_size)

        # Roles
        self.chk_auto_roles.setChecked(s.auto_roles)
        self.spin_5v5_tank.setValue(s.composition_5v5.tank)
        self.spin_5v5_damage.setValue(s.composition_5v5.damage)
        self.spin_5v5_support.setValue(s.composition_5v5.support)
        self.spin_6v6_tank.setValue(s.composition_6v6.tank)
        self.spin_6v6_damage.setValue(s.composition_6v6.damage)
        self.spin_6v6_support.setValue(s.composition_6v6.support)
        self._update_comp_totals()

        # Maps
        self.chk_auto_map.setChecked(s.auto_map)
        self.spin_avoid_maps.setValue(s.avoid_recent_maps)

        # Bans
        self.chk_auto_bans.setChecked(s.auto_bans)
        self.spin_max_bans.setValue(s.max_bans)

        # Teams
        self.edit_team1.setText(s.team1_name)
        self.edit_team2.setText(s.team2_name)

        self._update_shuffle_desc()

    def _update_shuffle_desc(self):
        mode = self.cb_shuffle_mode.currentData()
        descriptions = {
            ShuffleMode.RANDOM: "Mezcla completamente aleatoria. Puede repetir combinaciones similares.",
            ShuffleMode.MAX_VARIETY: "Genera múltiples combinaciones y elige la más diferente al historial. Recomendado.",
            ShuffleMode.AVOID_LAST: "Solo evita que la siguiente mezcla sea muy parecida a la anterior.",
        }
        self.shuffle_desc.setText(descriptions.get(mode, ""))

    def _update_comp_totals(self):
        total5 = self.spin_5v5_tank.value() + self.spin_5v5_damage.value() + self.spin_5v5_support.value()
        total6 = self.spin_6v6_tank.value() + self.spin_6v6_damage.value() + self.spin_6v6_support.value()

        self.lbl_5v5_total.setText(f"Total: {total5}" + (" ✓" if total5 == 5 else " ⚠"))
        self.lbl_6v6_total.setText(f"Total: {total6}" + (" ✓" if total6 == 6 else " ⚠"))

        color = "#4CAF50" if total5 == 5 else "#FF4444"
        self.lbl_5v5_total.setStyleSheet(f"font-weight: 600; color: {color};")

        color = "#4CAF50" if total6 == 6 else "#FF4444"
        self.lbl_6v6_total.setStyleSheet(f"font-weight: 600; color: {color};")

    def _emit_settings_changed(self):
        self.settings_changed.emit(self.settings_manager.settings)

    # Event handlers
    def _on_mode_changed(self):
        mode = GameMode.FIVE_V_FIVE if self.rb_5v5.isChecked() else GameMode.SIX_V_SIX
        self.settings_manager.update_game_mode(mode)
        self._emit_settings_changed()

    def _on_shuffle_mode_changed(self):
        mode = self.cb_shuffle_mode.currentData()
        self.settings_manager.update_shuffle_mode(mode)
        self._update_shuffle_desc()
        self._emit_settings_changed()

    def _on_candidates_changed(self, value: int):
        self.settings_manager.update_diversity_candidates(value)
        self._emit_settings_changed()

    def _on_history_changed(self, value: int):
        self.settings_manager.update_history_size(value)
        self._emit_settings_changed()

    def _on_auto_roles_changed(self, checked: bool):
        self.settings_manager.update_auto_roles(checked)
        self._emit_settings_changed()

    def _on_comp5_changed(self):
        comp = TeamComposition(
            tank=self.spin_5v5_tank.value(),
            damage=self.spin_5v5_damage.value(),
            support=self.spin_5v5_support.value(),
        )
        self.settings_manager.update_composition(GameMode.FIVE_V_FIVE, comp)
        self._update_comp_totals()
        self._emit_settings_changed()

    def _on_comp6_changed(self):
        comp = TeamComposition(
            tank=self.spin_6v6_tank.value(),
            damage=self.spin_6v6_damage.value(),
            support=self.spin_6v6_support.value(),
        )
        self.settings_manager.update_composition(GameMode.SIX_V_SIX, comp)
        self._update_comp_totals()
        self._emit_settings_changed()

    def _on_auto_map_changed(self, checked: bool):
        self.settings_manager.update_auto_map(checked)
        self._emit_settings_changed()

    def _on_avoid_maps_changed(self, value: int):
        self.settings_manager.update_avoid_recent_maps(value)
        self._emit_settings_changed()

    def _on_auto_bans_changed(self, checked: bool):
        self.settings_manager.update_auto_bans(checked)
        self._emit_settings_changed()

    def _on_max_bans_changed(self, value: int):
        self.settings_manager.update_max_bans(value)
        self._emit_settings_changed()

    def _on_team_names_changed(self):
        self.settings_manager.update_team_names(
            self.edit_team1.text(), self.edit_team2.text()
        )
        self._emit_settings_changed()

    def _import_settings(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar ajustes", "", "JSON Files (*.json)"
        )
        if not path:
            return

        try:
            settings = self.settings_manager.storage.import_settings(path)
            self.settings_manager._settings = settings
            self.settings_manager.save()
            self._load_current_settings()
            self._emit_settings_changed()
            QMessageBox.information(self, "Éxito", "Ajustes importados correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo importar: {e}")

    def _export_settings(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar ajustes", "settings.json", "JSON Files (*.json)"
        )
        if not path:
            return

        try:
            self.settings_manager.storage.export_settings(self.settings_manager.settings, path)
            QMessageBox.information(self, "Éxito", "Ajustes exportados correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar: {e}")

    def _reset_settings(self):
        reply = QMessageBox.question(
            self, "Restablecer",
            "¿Restablecer todos los ajustes a valores por defecto?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.settings_manager.reset_to_defaults()
            self._load_current_settings()
            self._emit_settings_changed()
            self.reset_requested.emit()