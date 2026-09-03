"""Roster Controller — Core coordinator for team slots, bench, saved players, and DnD."""

from __future__ import annotations

from typing import TYPE_CHECKING

from owervach_tmixer.core.models import Player
from owervach_tmixer.core.roster import Roster
from owervach_tmixer.core.special_player import is_special_player_name
from owervach_tmixer.ui.easter_eggs import EggContext

# Mixins desacoplados
from .roster.slot_operations import SlotOperationsMixin
from .roster.bench_saved_operations import BenchSavedOperationsMixin
from .roster.dnd_operations import DndOperationsMixin

if TYPE_CHECKING:
    from owervach_tmixer.ui.main_window import MainWindow


class RosterController(SlotOperationsMixin, BenchSavedOperationsMixin, DndOperationsMixin):
    """Controls all player roster operations, slot modifications, and DnD routing."""

    def __init__(self, main_window: MainWindow, roster: Roster):
        self.win = main_window
        self.roster: Roster = roster

    @staticmethod
    def find_in(collection: list[Player], name: str) -> Player | None:
        folded = name.strip().casefold()
        return next((p for p in collection if p.name.casefold() == folded), None)

    # ------------------------------------------------------------------
    # Lifecycle & UI Sync
    # ------------------------------------------------------------------
    def rebuild_fixed_roles(self):
        self.win._fixed_roles = {
            p.name: p.role
            for p in self.roster.active_players()
            if p.fixed_role and p.role is not None
        }

    def apply_default_roles_if_needed(self):
        s = self.win.settings_manager.settings
        if s.show_roles and not s.auto_roles:
            self.roster.apply_default_roles(s.role_order())

    def after_roster_change(self, refresh_saved: bool = True):
        self.apply_default_roles_if_needed()
        self.win.storage.save_roster(self.roster)
        self.rebuild_fixed_roles()
        if hasattr(self.win, "_sync_match_teams"):
            self.win._sync_match_teams()
        self.refresh_roster_ui()

    def recalculate_auto_ratings(self):
        """Recalculates empirical Win/Loss stats and Bayesian ratings for all players."""
        try:
            from owervach_tmixer.core.auto_mmr import calibrate_all_players_from_history
            history = self.win.history_manager.get_all()
            all_known = list(self.roster.saved) + list(self.roster.bench) + list(self.roster.active_players())
            stats_map = calibrate_all_players_from_history(history, all_known)

            for p in all_known:
                folded = p.name.casefold()
                if folded in stats_map:
                    st = stats_map[folded]
                    p.calculated_mmr = st.calculated_mmr
                    p.calculated_mmr_tank = st.calculated_mmr_tank
                    p.calculated_mmr_damage = st.calculated_mmr_damage
                    p.calculated_mmr_support = st.calculated_mmr_support
                    p.wins = st.wins
                    p.losses = st.losses
                    p.draws = st.draws
        except Exception:
            pass

    def refresh_roster_ui(self):
        self.recalculate_auto_ratings()
        s = self.win.settings_manager.settings
        self.apply_default_roles_if_needed()
        saved_names = self.roster.saved_names()
        show_mmr = getattr(s, "balance_by_mmr", False)

        self.win.match_display.team1_widget.set_slots(
            self.roster.team1_slots, saved_names, s.show_roles, show_mmr
        )
        self.win.match_display.team2_widget.set_slots(
            self.roster.team2_slots, saved_names, s.show_roles, show_mmr
        )
        self.win.bench_panel.set_bench(self.roster.bench, saved_names, show_mmr=show_mmr)

        active_names = {p.name for p in self.roster.active_players()}
        bench_names = {p.name for p in self.roster.bench}
        self.win.saved_panel.set_saved(self.roster.saved, active_names, bench_names, show_mmr=show_mmr)
        self.win.dock.update_counts(len(self.roster.saved), len(self.roster.bench))

        active = len(self.roster.active_players())
        needed = s.game_mode.total_players
        msg = (
            f"Jugadores: {active} activos · {len(self.roster.bench)} en espera "
            f"· {len(self.roster.saved)} guardados"
        )
        if active < needed:
            msg += f" · faltan {needed - active} para {s.game_mode.value}"
        self.win.status_bar.showMessage(msg, 5000)

        self.check_special_player()

    def check_special_player(self):
        names = (
            [p.name for p in self.roster.active_players() if is_special_player_name(p.name)]
            or [p.name for p in self.roster.bench_players() if is_special_player_name(p.name)]
        )
        if names:
            self.win._egg_manager.maybe_trigger(
                EggContext(window=self.win, player_name=names[0])
            )
