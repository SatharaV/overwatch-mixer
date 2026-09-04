"""Main application window with clean MVC architecture and live theme engine."""

from __future__ import annotations

import shutil
from pathlib import Path

import platformdirs
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QMainWindow,
    QSplashScreen,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer import APP_NAME, APP_TITLE
from owervach_tmixer.core.heroes import HeroManager
from owervach_tmixer.core.history import HistoryManager
from owervach_tmixer.core.maps import MapPool
from owervach_tmixer.core.match_generator import MatchGenerator
from owervach_tmixer.core.models import GameMode, Hero, Map, Match, Role
from owervach_tmixer.core.roster import Roster
from owervach_tmixer.core.settings import SettingsManager
from owervach_tmixer.core.shuffle_history import ShuffleHistoryManager
from owervach_tmixer.core.shuffler import TeamShuffler
from owervach_tmixer.core.storage import Storage
from owervach_tmixer.ui.controllers.match_controller import MatchController
from owervach_tmixer.ui.controllers.roster_controller import RosterController
from owervach_tmixer.ui.dialogs.add_custom_dialog import AddCustomItemDialog
from owervach_tmixer.ui.dialogs.settings_dialog import SettingsDialog
from owervach_tmixer.ui.easter_eggs import EasterEggManager
from owervach_tmixer.ui.audio_fx import play_ban_sound_for_pool
from owervach_tmixer.ui.styles import theme
from owervach_tmixer.ui.widgets.header_bar import HeaderBar
from owervach_tmixer.ui.widgets.hero_widget import HeroWidget
from owervach_tmixer.ui.widgets.history_panel import HistoryPanel
from owervach_tmixer.ui.widgets.map_widget import MapWidget
from owervach_tmixer.ui.widgets.map_card import preload_all_map_banners
from owervach_tmixer.ui.widgets.roster_dock import RosterDockWidget
from owervach_tmixer.ui.widgets.team_display import MatchDisplayWidget
from owervach_tmixer.ui.widgets.tier_maker import TierMakerWidget
from owervach_tmixer.ui.widgets.toast import ToastManager

QWIDGETSIZE_MAX = 16777215


def create_splash_screen() -> QSplashScreen:
    pixmap = QPixmap(1, 1)
    pixmap.fill(Qt.transparent)
    return QSplashScreen(pixmap)


class MainWindow(QMainWindow):
    """Main application window (Visual Orchestrator)."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1280, 720)
        self.setMinimumSize(1040, 600)

        self._start_maximized = False
        self.storage = Storage()
        self.settings_manager = SettingsManager(self.storage)
        self.shuffler = TeamShuffler()
        self.shuffle_history = ShuffleHistoryManager(
            max_size=self.settings_manager.settings.history_size
        )
        self.map_pool = MapPool([], avoid_recent=3)
        self.hero_manager = HeroManager([], max_bans=5, max_bans_per_role=2)
        self.history_manager = HistoryManager(self.storage)
        self.match_generator = MatchGenerator(
            shuffler=self.shuffler,
            map_pool=self.map_pool,
            hero_manager=self.hero_manager,
        )

        self._current_match: Match | None = None
        self._fixed_roles: dict[str, Role] = {}
        self._egg_manager = EasterEggManager()

        initial_roster = Roster.empty(GameMode.FIVE_V_FIVE)
        self.roster_controller = RosterController(self, initial_roster)
        self.match_controller = MatchController(self)

        self._setup_ui()
        self.toast = ToastManager(self)
        self._load_data()
        self._connect_signals()
        self._restore_geometry()

    @property
    def _roster(self) -> Roster:
        return self.roster_controller.roster

    @_roster.setter
    def _roster(self, val: Roster):
        self.roster_controller.roster = val

    @property
    def side_splitter(self):
        return getattr(self.dock, "vertical_splitter", None)

    @property
    def mode_switch(self):
        return self.header_bar.mode_switch

    @property
    def roles_toggle(self):
        return self.header_bar.roles_toggle

    @property
    def randomize_roles_toggle(self):
        return self.header_bar.randomize_roles_toggle

    @property
    def tryhard_toggle(self):
        return self.header_bar.tryhard_toggle

    @property
    def btn_settings(self):
        return self.header_bar.btn_settings

    @property
    def _nav_buttons(self):
        return self.header_bar._nav_buttons

    @property
    def _nav_group(self):
        return self.header_bar._nav_group

    @staticmethod
    def _find_in(collection, name: str):
        return RosterController.find_in(collection, name)

    def show_toast(self, message: str, kind: str = "info"):
        self.toast.show_toast(message, kind)

    def _setup_ui(self):
        theme.set_accent(self.settings_manager.settings.accent_color)

        central = QWidget(self)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setCentralWidget(central)

        # 1. Header Bar Desacoplada
        s = self.settings_manager.settings
        self.header_bar = HeaderBar(
            initial_mode=s.game_mode,
            show_roles=s.show_roles,
            auto_roles=s.auto_roles,
            balance_by_mmr=getattr(s, "balance_by_mmr", False),
            parent=central,
        )
        self.header_bar.nav_tab_clicked.connect(self._on_nav_tab_clicked)
        self.header_bar.mode_changed.connect(self._on_mode_changed)
        self.header_bar.show_roles_toggled.connect(self._on_show_roles_toggled)
        self.header_bar.randomize_roles_toggled.connect(self._on_randomize_roles_toggled)
        self.header_bar.tryhard_toggled.connect(self._on_tryhard_toggled)
        self.header_bar.settings_clicked.connect(self._show_settings)
        main_layout.addWidget(self.header_bar)

        # 2. Main Tab View con parent solido
        self.tabs = QTabWidget(central)
        self.tabs.tabBar().hide()
        self.tabs.setStyleSheet("QTabWidget::pane { border: none; background-color: #121316; }")
        main_layout.addWidget(self.tabs, 1)

        # Tab 1: Partida
        self.tab_match = QWidget(self.tabs)
        match_layout = QVBoxLayout(self.tab_match)
        match_layout.setContentsMargins(14, 12, 14, 12)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal, self.tab_match)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(8)
        self.main_splitter.setStyleSheet("""
            QSplitter::handle:horizontal {
                background-color: #181A22;
                border-left: 1px solid #262934;
                border-right: 1px solid #262934;
                border-radius: 2px;
                margin: 4px 1px;
            }
            QSplitter::handle:horizontal:hover {
                background-color: #61ab02;
            }
        """)

        self.match_display = MatchDisplayWidget(self.main_splitter)
        self.match_display.setMinimumWidth(560)
        self.main_splitter.addWidget(self.match_display)

        self.dock = RosterDockWidget(self.main_splitter)
        self.dock.setMinimumWidth(300)
        self.dock.setMaximumWidth(580)
        self.saved_panel = self.dock.saved_panel
        self.bench_panel = self.dock.bench_panel
        self.bans_panel = self.dock.bans_panel
        self.bans_panel.randomize_requested.connect(self._randomize_bans_from_main)
        self.bans_panel.set_portrait_size(
            getattr(self.settings_manager.settings, "ban_portrait_size", 44)
        )
        self.main_splitter.addWidget(self.dock)
        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 1)

        match_layout.addWidget(self.main_splitter, 1)
        self.tabs.addTab(self.tab_match, "Partida")

        # Tab 2: Mapas
        self.map_widget = MapWidget(self.tabs)
        self.tabs.addTab(self.map_widget, "Mapas")

        # Tab 3: Heroes / Baneos
        self.hero_widget = HeroWidget(self.tabs)
        self.tabs.addTab(self.hero_widget, "Héroes / Baneos")

        # Tab 4: Tier Maker
        self.tier_maker = TierMakerWidget(self)
        self.tabs.addTab(self.tier_maker, "Tier Maker")

        # Tab 5: Historial
        self.history_panel = HistoryPanel(self.history_manager, self.tabs)
        self.tabs.addTab(self.history_panel, "Historial")

        self.setStatusBar(None)
        self.status_bar = type(
            "SilentStatusBar",
            (),
            {"showMessage": lambda *a, **k: None, "clearMessage": lambda *a: None},
        )()

        self._apply_theme()

    def _on_nav_tab_clicked(self, idx: int):
        self.tabs.setCurrentIndex(idx)
        self.header_bar.apply_theme(idx)
        if idx == 3 and hasattr(self, "tier_maker"):
            if not self.tier_maker.bank_cards and not any(r.cards for r in self.tier_maker.rows):
                self.tier_maker.reload_bank()

    def _update_nav_buttons_style(self):
        curr_idx = self.tabs.currentIndex() if hasattr(self, "tabs") else 0
        self.header_bar.apply_theme(curr_idx)

    def _update_pill_style(self, btn, active_color: str):
        self.header_bar.update_pill_style(btn, active_color)

    def _apply_theme(self):
        self.setUpdatesEnabled(False)
        try:
            qss = theme.build_stylesheet()
            self.setStyleSheet(qss)

            if hasattr(self, "match_display") and self.match_display:
                self.match_display.apply_theme()
            if hasattr(self, "map_widget") and self.map_widget:
                self.map_widget.apply_theme()
            if hasattr(self, "hero_widget") and self.hero_widget:
                self.hero_widget.apply_theme()
            if hasattr(self, "dock") and self.dock:
                self.dock.apply_theme()
            if hasattr(self, "history_panel") and self.history_panel:
                self.history_panel.apply_theme()
            if hasattr(self, "header_bar") and self.header_bar:
                curr_idx = self.tabs.currentIndex() if hasattr(self, "tabs") else 0
                self.header_bar.apply_theme(curr_idx)
            if hasattr(self, "tier_maker") and self.tier_maker:
                self.tier_maker.apply_theme()
            if hasattr(self, "roster_controller") and self.roster_controller:
                self.roster_controller.refresh_roster_ui()
        finally:
            self.setUpdatesEnabled(True)
            self.update()
    def _show_settings(self):
        try:
            dialog = SettingsDialog(self, self.settings_manager, self.shuffle_history)
            dialog.exec()
        except Exception as exc:
            import traceback
            traceback.print_exc()
            self.show_toast(f"Error al abrir configuracion: {exc}", "danger")

    def _connect_signals(self):
        self.match_display.team1_widget.slot_created.connect(self._on_slot_created)
        self.match_display.team2_widget.slot_created.connect(self._on_slot_created)
        self.match_display.team1_widget.slot_renamed.connect(self._on_slot_renamed)
        self.match_display.team2_widget.slot_renamed.connect(self._on_slot_renamed)
        self.match_display.team1_widget.slot_fixed_changed.connect(self._on_slot_fixed_changed)
        self.match_display.team2_widget.slot_fixed_changed.connect(self._on_slot_fixed_changed)
        self.match_display.team1_widget.slot_role_changed.connect(self._on_slot_role_changed)
        self.match_display.team2_widget.slot_role_changed.connect(self._on_slot_role_changed)
        self.match_display.team1_widget.slot_mmr_changed.connect(self._on_slot_role_mmr_changed)
        self.match_display.team2_widget.slot_mmr_changed.connect(self._on_slot_role_mmr_changed)
        self.match_display.team1_widget.slot_color_changed.connect(self._on_global_player_color_changed)
        self.match_display.team2_widget.slot_color_changed.connect(self._on_global_player_color_changed)
        self.match_display.team1_widget.slot_bench.connect(self._on_slot_bench)
        self.match_display.team2_widget.slot_bench.connect(self._on_slot_bench)
        self.match_display.team1_widget.slot_save.connect(self._on_slot_save)
        self.match_display.team2_widget.slot_save.connect(self._on_slot_save)
        self.match_display.team1_widget.slot_unsave.connect(self._on_slot_unsave)
        self.match_display.team2_widget.slot_unsave.connect(self._on_slot_unsave)
        self.match_display.team1_widget.slot_remove.connect(self._on_slot_remove)
        self.match_display.team2_widget.slot_remove.connect(self._on_slot_remove)
        self.match_display.team1_widget.slot_remove_permanent.connect(self._on_slot_remove_permanent)
        self.match_display.team2_widget.slot_remove_permanent.connect(self._on_slot_remove_permanent)
        self.match_display.team1_widget.player_drop_requested.connect(self._on_player_drop)
        self.match_display.team2_widget.player_drop_requested.connect(self._on_player_drop)

        self.match_display.team1_widget.team_name_changed.connect(lambda name: self._on_team_name_changed(1, name))
        self.match_display.team2_widget.team_name_changed.connect(lambda name: self._on_team_name_changed(2, name))

        self.bench_panel.add_to_team.connect(self._on_bench_add_to_team)
        self.bench_panel.remove_from_bench.connect(self._on_bench_remove)
        self.bench_panel.remove_permanent.connect(self._on_bench_remove_permanent)
        self.bench_panel.save_player.connect(self._on_bench_save)
        self.bench_panel.unsave_player.connect(self._on_bench_unsave)
        self.bench_panel.bench_drop_entry.connect(self._on_drop_to_bench)
        self.bench_panel.fill_teams_requested.connect(self._on_fill_teams_from_bench)
        self.bench_panel.bench_all_requested.connect(self._on_bench_all_teams)
        self.bench_panel.player_role_mmr_changed.connect(self._on_global_player_role_mmr_changed)
        self.bench_panel.player_renamed.connect(self._on_global_player_renamed)
        self.bench_panel.player_color_changed.connect(self._on_global_player_color_changed)
        self.bench_panel.reorder_bench.connect(self.roster_controller.reorder_bench)
        self.bench_panel.bulk_save_requested.connect(self.roster_controller.bulk_bench_save)
        self.bench_panel.bulk_remove_requested.connect(self.roster_controller.bulk_bench_remove)
        self.bench_panel.bulk_add_to_team_requested.connect(self.roster_controller.bulk_bench_add_to_team)

        self.saved_panel.add_to_match.connect(self._on_saved_add_to_match)
        self.saved_panel.add_to_bench.connect(self._on_saved_add_to_bench)
        self.saved_panel.remove_saved.connect(self._on_saved_remove)
        self.saved_panel.bulk_saved.connect(self._on_bulk_saved)
        self.saved_panel.import_file.connect(self._on_saved_import)
        self.saved_panel.export_file.connect(self._on_saved_export)
        self.saved_panel.chip_activated.connect(self._on_saved_chip_activated)
        self.saved_panel.player_dropped.connect(self._on_player_dropped_to_saved)
        self.saved_panel.player_role_mmr_changed.connect(self._on_global_player_role_mmr_changed)
        self.saved_panel.player_renamed.connect(self._on_global_player_renamed)
        self.saved_panel.player_color_changed.connect(self._on_global_player_color_changed)
        self.saved_panel.fill_teams_from_saved_requested.connect(self._on_fill_teams_from_saved)
        self.saved_panel.send_all_saved_to_bench_requested.connect(self._on_send_all_saved_to_bench)
        self.saved_panel.reorder_saved.connect(self.roster_controller.reorder_saved)
        self.saved_panel.bulk_add_to_bench_requested.connect(self.roster_controller.bulk_saved_add_to_bench)
        self.saved_panel.bulk_add_to_team_requested.connect(self.roster_controller.bulk_saved_add_to_team)
        self.saved_panel.bulk_remove_requested.connect(self.roster_controller.bulk_saved_remove)

        self.map_widget.maps_changed.connect(self._on_maps_changed)
        self.map_widget.map_selected.connect(self._on_map_selected)
        self.map_widget.avoid_recent_changed.connect(self._on_avoid_recent_changed)

        self.hero_widget.bans_changed.connect(self._on_bans_changed)
        self.hero_widget.max_bans_changed.connect(self._on_max_bans_changed)
        self.hero_widget.max_bans_per_role_changed.connect(self._on_max_bans_per_role_changed)
        self.hero_widget.heroes_changed.connect(self._on_heroes_changed)

        self.match_display.team1_widget.reroll_roles.connect(lambda: self._reroll_roles(1))
        self.match_display.team2_widget.reroll_roles.connect(lambda: self._reroll_roles(2))
        self.match_display.generate_match.connect(self._generate_match)
        self.match_display.clear_all_requested.connect(self._clear_all)
        self.match_display.reroll_map.connect(self._reroll_map)
        self.match_display.clear_map.connect(self._clear_map)
        self.match_display.copy_to_discord_done.connect(
            lambda: self.show_toast("Alineacion y mapa copiados al portapapeles", "success")
        )
        self.match_display.winner_declared.connect(self.match_controller.set_match_winner)
        self.match_display.copy_to_discord_empty.connect(
            lambda: self.show_toast("No hay jugadores en los equipos para copiar", "warning")
        )

        self._shortcut_generate = QShortcut(Qt.Key.Key_Return | Qt.KeyboardModifier.ControlModifier, self)
        self._shortcut_generate.activated.connect(self._generate_match)

        self.history_panel.match_selected.connect(self._load_match_from_history)
        self.history_panel.clear_requested.connect(self._on_history_cleared)

        self.shuffler.diversity_candidates = self.settings_manager.settings.diversity_candidates

    def _sanitize_special_player_presence(self, roster):
        """Garantiza que Sathara jamás arranque en equipos ni en espera (solo en guardados)."""
        from owervach_tmixer.core.special_player import is_special_player_name
        for idx, p in enumerate(roster.team1_slots):
            if p and is_special_player_name(p.name):
                roster.team1_slots[idx] = None
        for idx, p in enumerate(roster.team2_slots):
            if p and is_special_player_name(p.name):
                roster.team2_slots[idx] = None
        roster.bench = [p for p in roster.bench if not (p and is_special_player_name(p.name))]

    def _load_data(self):
        loaded_roster = self.storage.load_roster(self.settings_manager.settings.game_mode)
        self._sanitize_special_player_presence(loaded_roster)
        self._roster = loaded_roster
        self.storage.save_roster(loaded_roster)
        self.roster_controller.refresh_roster_ui()
        self.roster_controller.rebuild_fixed_roles()

        maps = self.storage.load_maps()
        active_maps = [m for m in maps if getattr(m, "enabled", True)]
        self.map_pool = MapPool(active_maps, avoid_recent=self.settings_manager.settings.avoid_recent_maps)
        self.map_pool.load_history(
            self.history_manager.get_recent_maps(self.settings_manager.settings.avoid_recent_maps)
        )
        self.match_generator.map_pool = self.map_pool
        self.map_widget.set_maps(maps)
        preload_all_map_banners(maps)
        self.map_widget.set_avoid_recent(self.settings_manager.settings.avoid_recent_maps)

        last_map_data = getattr(self.settings_manager.settings, "last_selected_map", None)
        if last_map_data:
            try:
                restored_map = Map.from_dict(last_map_data)
                self.match_display.set_map(restored_map)
                self.map_widget.select_map(restored_map)
            except Exception:
                pass

        heroes = self.storage.load_heroes()
        settings = self.settings_manager.settings
        effective_max = settings.max_bans if (settings.max_bans and settings.max_bans > 0) else 5
        effective_role = settings.max_bans_per_role if (settings.max_bans_per_role and settings.max_bans_per_role > 0) else 2

        self.hero_manager = HeroManager(heroes, max_bans=effective_max, max_bans_per_role=effective_role)
        self.hero_widget.set_heroes(heroes)
        self.hero_widget.set_max_bans(effective_max)
        self.hero_widget.set_max_bans_per_role(effective_role)

        bans_data = self.storage.load_bans(heroes)
        self.hero_widget.set_banned(bans_data.banned)
        self.hero_manager.ban_manager.banned = self.hero_widget.get_banned()
        self.bans_panel.set_banned(sorted(bans_data.banned))

        self._apply_settings_to_widgets()
        if hasattr(self, "tier_maker"):
            self.tier_maker.reload_bank()

    def _apply_settings_to_widgets(self):
        s = self.settings_manager.settings
        self.match_display.set_game_mode(s.game_mode)
        self.mode_switch.set_mode(s.game_mode)
        self.match_display.team1_widget.set_team_name(s.team1_name)
        self.match_display.team2_widget.set_team_name(s.team2_name)
        self.shuffler.diversity_candidates = s.diversity_candidates
        self.match_display.set_show_roles(s.show_roles)
        self.roles_toggle.setChecked(s.show_roles)

        is_tryhard = getattr(s, "balance_by_mmr", False)
        if hasattr(self, "tryhard_toggle"):
            self.tryhard_toggle.setChecked(is_tryhard)
            self._update_pill_style(self.tryhard_toggle, "#9D5CFF")
        self.match_display.set_show_mmr(is_tryhard)

        self._apply_role_policy()
        self.shuffle_history.set_max_size(s.history_size)
        self.map_pool.avoid_recent = s.avoid_recent_maps
        self.map_widget.set_avoid_recent(s.avoid_recent_maps)

        if hasattr(s, "map_card_size") and hasattr(s, "map_card_aspect"):
            self.map_widget.set_card_preferences(s.map_card_size, s.map_card_aspect)

        effective_max = s.max_bans if (s.max_bans and s.max_bans > 0) else 5
        effective_role = s.max_bans_per_role if (s.max_bans_per_role and s.max_bans_per_role > 0) else 2

        self.hero_manager.set_max_bans(effective_max)
        self.hero_widget.set_max_bans(effective_max)
        self.hero_manager.set_max_bans_per_role(effective_role)
        self.hero_widget.set_max_bans_per_role(effective_role)
        self.bans_panel.set_portrait_size(getattr(s, "ban_portrait_size", 44))
        if hasattr(self.bans_panel, "set_visible_rows"):
            self.bans_panel.set_visible_rows(getattr(s, "bans_visible_rows", 3))

        self.match_display.set_font_preferences(
            getattr(s, "slot_font_size", 13),
            getattr(s, "slot_font_weight", "bold"),
            getattr(s, "slot_text_align", "center"),
            getattr(s, "slot_dynamic_font", True),
            getattr(s, "role_badge_style", "emoji"),
            getattr(s, "slot_badge_outlines", False),
        )

    def _after_roster_change(self, refresh_saved: bool = True):
        self.roster_controller.after_roster_change(refresh_saved)

    def _apply_default_roles_if_needed(self):
        self.roster_controller.apply_default_roles_if_needed()

    def _refresh_roster_ui(self):
        self.roster_controller.refresh_roster_ui()

    def _check_special_player(self):
        self.roster_controller.check_special_player()

    def _rebuild_fixed_roles(self):
        self.roster_controller.rebuild_fixed_roles()

    def _on_slot_created(self, team_num: int, slot_idx: int, name: str):
        self.roster_controller.create_in_slot(team_num, slot_idx, name)

    def _on_slot_renamed(self, team_num: int, slot_idx: int, new_name: str):
        self.roster_controller.rename_slot(team_num, slot_idx, new_name)

    def _on_global_player_renamed(self, old_name: str, new_name: str):
        self.roster_controller.rename_global(old_name, new_name)

    def _on_slot_fixed_changed(self, team_num: int, slot_idx: int, new_fixed_team):
        self.roster_controller.set_slot_fixed_team(team_num, slot_idx, new_fixed_team)

    def _on_slot_role_changed(self, team_num: int, slot_idx: int, role):
        self.roster_controller.set_slot_role(team_num, slot_idx, role)

    def _on_slot_role_mmr_changed(self, team_num: int, slot_idx: int, role, mmr: int):
        self.roster_controller.set_slot_mmr(team_num, slot_idx, role, mmr)

    def _on_global_player_role_mmr_changed(self, name: str, role, mmr: int):
        self.roster_controller.set_global_player_mmr(name, role, mmr)

    def _on_global_player_color_changed(self, name: str, color_hex: str | None):
        self.roster_controller.set_global_player_color(name, color_hex)
        if hasattr(self, "tier_maker"):
            self.tier_maker.update_player_color(name, color_hex)

    def _on_slot_bench(self, team_num: int, slot_idx: int):
        self.roster_controller.send_to_bench(team_num, slot_idx)

    def _on_slot_save(self, team_num: int, slot_idx: int):
        self.roster_controller.save_player(team_num, slot_idx)

    def _on_slot_unsave(self, team_num: int, slot_idx: int):
        self.roster_controller.unsave_player(team_num, slot_idx)

    def _on_slot_remove(self, team_num: int, slot_idx: int):
        self.roster_controller.remove_player(team_num, slot_idx)

    def _on_slot_remove_permanent(self, team_num: int, slot_idx: int):
        self.roster_controller.remove_permanent(team_num, slot_idx)

    def _on_player_drop(self, payload, target_team: int, target_idx):
        self.roster_controller.handle_player_drop(payload, target_team, target_idx)

    def _on_saved_dropped_on_team(self, name: str, target_team: int):
        self.roster_controller.handle_saved_dropped_on_team(name, target_team)

    def _on_drop_to_bench(self, payload):
        self.roster_controller.handle_drop_to_bench(payload)

    def _on_player_dropped_to_saved(self, payload: dict):
        self.roster_controller.handle_player_dropped_to_saved(payload)

    def _on_bench_add_to_team(self, name: str, team_num):
        self.roster_controller.bench_add_to_team(name, team_num)

    def _on_bench_remove(self, name: str):
        self.roster_controller.bench_remove(name)

    def _on_bench_remove_permanent(self, name: str):
        self.roster_controller.bench_remove_permanent(name)

    def _on_bench_save(self, name: str):
        self.roster_controller.bench_save(name)

    def _on_bench_unsave(self, name: str):
        self.roster_controller.bench_unsave(name)

    def _on_fill_teams_from_bench(self):
        self.roster_controller.fill_teams_from_bench()

    def _on_fill_teams_from_saved(self):
        self.roster_controller.fill_teams_from_saved()

    def _on_send_all_saved_to_bench(self):
        self.roster_controller.send_all_saved_to_bench()

    def _on_bench_all_teams(self):
        self.roster_controller.bench_all_teams()

    def _on_saved_add_to_match(self, name: str, team_num):
        self.roster_controller.saved_add_to_match(name, team_num)

    def _on_saved_add_to_bench(self, name: str):
        self.roster_controller.saved_add_to_bench(name)

    def _on_saved_chip_activated(self, name: str):
        self.roster_controller.saved_chip_activated(name)

    def _on_saved_remove(self, name: str):
        self.roster_controller.saved_remove(name)

    def _on_bulk_saved(self, names):
        self.roster_controller.bulk_saved(names)

    def _on_saved_import(self, path: str):
        self.roster_controller.import_saved(path)

    def _on_saved_export(self, path: str):
        self.roster_controller.export_saved(path)

    def _sync_match_teams(self):
        self.match_controller.sync_match_teams()

    def _apply_teams_to_slots(self, team1, team2):
        self.match_controller.apply_teams_to_slots(team1, team2)

    def _clear_all(self):
        self.match_controller.clear_all()

    def _generate_match(self):
        self.match_controller.generate_match()

    def _reshuffle_teams(self):
        self.match_controller.reshuffle_teams()

    def _reroll_roles(self, team_num: int):
        self.match_controller.reroll_roles(team_num)

    def _clear_map(self):
        self.match_controller.clear_map()

    def _reroll_map(self):
        self.match_controller.reroll_map()

    def _new_match(self):
        self.match_controller.new_match()

    def _load_match_from_history(self, match: Match):
        self.match_controller.load_match_from_history(match)

    def _on_mode_changed(self, mode):
        self.match_controller.on_mode_changed(mode)

    def _adapt_pinned_roles_to_mode(self):
        self.match_controller.adapt_pinned_roles_to_mode()

    def _apply_role_policy(self):
        self.match_controller.apply_role_policy()

    def _on_show_roles_toggled(self, checked: bool):
        self.match_controller.on_show_roles_toggled(checked)

    def _on_randomize_roles_toggled(self, checked: bool):
        self.match_controller.on_randomize_roles_toggled(checked)

    def _on_tryhard_toggled(self, checked: bool):
        self.match_controller.on_tryhard_toggled(checked)

    def _on_team_name_changed(self, team_num: int, name: str):
        self.match_controller.on_team_name_changed(team_num, name)

    def _on_maps_changed(self, maps: list[Map]):
        self.match_controller.on_maps_changed(maps)

    def _on_map_selected(self, map_obj: Map):
        self.match_controller.on_map_selected(map_obj)

    def _on_avoid_recent_changed(self, value: int):
        self.match_controller.on_avoid_recent_changed(value)

    def _randomize_bans_from_main(self):
        self.match_controller.randomize_bans_from_main()

    def _on_bans_changed(self, banned: set):
        self.match_controller.on_bans_changed(banned)

    def _on_max_bans_changed(self, value: int):
        self.match_controller.on_max_bans_changed(value)

    def _on_max_bans_per_role_changed(self, value: int):
        self.match_controller.on_max_bans_per_role_changed(value)

    def _on_heroes_changed(self, heroes: list[Hero]):
        self.match_controller.on_heroes_changed(heroes)

    def _factory_reset(self):
        self.match_controller.factory_reset()

    def _add_custom_map(self):
        dialog = AddCustomItemDialog(item_type="map", parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        name, mode, image_path = dialog.get_data()
        if any(item.name.casefold() == name.casefold() for item in self.map_widget.get_maps()):
            self.show_toast("Ese mapa ya esta en la lista.", "info")
            return

        if image_path:
            maps_dir = Path(platformdirs.user_data_dir(APP_NAME)) / "Maps" / mode
            maps_dir.mkdir(parents=True, exist_ok=True)
            extension = image_path.suffix.lower() or ".png"
            shutil.copy2(image_path, maps_dir / f"{name}{extension}")

        new_map = Map(name, mode)
        maps = self.map_widget.get_maps() + [new_map]
        self.map_widget.set_maps(maps)
        self._on_maps_changed(maps)
        self.show_toast(f"Mapa '{new_map.name}' añadido con exito", "success")

    def _add_custom_hero(self):
        dialog = AddCustomItemDialog(item_type="hero", parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        name, role_name, image_path = dialog.get_data()
        if any(hero.name.casefold() == name.casefold() for hero in self.hero_widget.get_heroes()):
            self.show_toast("Ese heroe ya esta en la lista.", "info")
            return

        role = {"Tanque": Role.TANK, "Daño": Role.DAMAGE, "Apoyo": Role.SUPPORT}[role_name]

        if image_path:
            portraits_dir = Path(platformdirs.user_data_dir(APP_NAME)) / "hero_portraits"
            portraits_dir.mkdir(parents=True, exist_ok=True)
            safe_name = "".join(char for char in name if char.isalnum() or char in " -_").strip()
            extension = image_path.suffix.lower() or ".png"
            shutil.copy2(image_path, portraits_dir / f"{safe_name}{extension}")

        heroes = self.hero_widget.get_heroes() + [Hero(name, role)]
        self.hero_widget.set_heroes(heroes)
        self._on_heroes_changed(heroes)
        self.show_toast(f"Heroe '{name}' añadido con exito", "success")

    def _on_history_cleared(self):
        self.map_pool.load_history([])

    def _restore_geometry(self):
        geom = self.settings_manager.geometry
        if geom.width > 0 and geom.height > 0:
            self.resize(geom.width, geom.height)
            self.move(geom.x, geom.y)
        # NUNCA llamar a showMaximized() aqui dentro
        self._start_maximized = bool(geom.maximized)

    def _save_geometry(self):
        self.settings_manager.update_geometry(self._get_window_geometry())

    def _get_window_geometry(self):
        from owervach_tmixer.core.settings import WindowGeometry

        is_max = self.isMaximized()
        if is_max:
            norm = self.normalGeometry()
            gx, gy = norm.x(), norm.y()
            gw, gh = norm.width(), norm.height()
        else:
            gx, gy = self.x(), self.y()
            gw, gh = self.width(), self.height()

        return WindowGeometry(
            x=gx,
            y=gy,
            width=gw,
            height=gh,
            maximized=is_max,
        )

    def showEvent(self, event):
        super().showEvent(event)
        self.dock.setMinimumWidth(300)
        self.dock.setMaximumWidth(580)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.dock.setMinimumWidth(300)
        self.dock.setMaximumWidth(580)

    def closeEvent(self, event):
        self._save_geometry()
        self._sanitize_special_player_presence(self._roster)
        self.storage.save_roster(self._roster)
        if self._current_match:
            self.history_manager.add(self._current_match)
        event.accept()
