"""Match Controller — Business logic for matchmaking, unified rerolls, and map persistence."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from owervach_tmixer.core.heroes import HeroManager
from owervach_tmixer.core.maps import MapPool
from owervach_tmixer.core.models import (
    GameMode,
    Hero,
    Map,
    Match,
    Role,
    Team,
    validate_players,
)
from owervach_tmixer.core.roles import assign_roles
from owervach_tmixer.core.special_player import is_special_player_name
from owervach_tmixer.ui.audio_fx import play_ban_sound_for_pool
from owervach_tmixer.ui.styles import theme

if TYPE_CHECKING:
    from owervach_tmixer.ui.main_window import MainWindow


class MatchController:
    """Controls match generation, role balance, map selection, bans, and history synchronization."""

    def __init__(self, main_window: MainWindow):
        self.win = main_window
        self._last_shuffle_time: float = 0.0
        self._is_generating: bool = False

    # ------------------------------------------------------------------
    # Team Synchronization & Slot Mapping
    # ------------------------------------------------------------------
    def sync_match_teams(self):
        if self.win._current_match is None:
            return
        roster = self.win.roster_controller.roster
        self.win._current_match.team1 = Team(
            name=self.win.match_display.team1_widget.get_team_name(),
            players=[p for p in roster.team1_slots if p],
        )
        self.win._current_match.team2 = Team(
            name=self.win.match_display.team2_widget.get_team_name(),
            players=[p for p in roster.team2_slots if p],
        )

    def apply_teams_to_slots(self, team1: Team, team2: Team):
        roster = self.win.roster_controller.roster
        size = roster.game_mode.players_per_team
        t1 = list(team1.players) + [None] * (size - len(team1.players))
        t2 = list(team2.players) + [None] * (size - len(team2.players))
        roster.team1_slots[:] = t1[:size]
        roster.team2_slots[:] = t2[:size]

    # ------------------------------------------------------------------
    # Match Generation & Shuffling with Debounce
    # ------------------------------------------------------------------
    def generate_match(self):
        # 1. Candado anti-congelamiento: Si ya está calculando, descartar inmediatamente el clic
        if getattr(self, "_is_generating", False):
            return

        now = time.time()
        if (now - self._last_shuffle_time) < 0.12:
            return

        self._is_generating = True
        try:
            self._do_generate_match()
        finally:
            self._last_shuffle_time = time.time()
            self._is_generating = False

    def _persist_in_background(self, roster, match):
        """Guarda el roster y el historial en segundo plano para no congelar los 144 FPS de la interfaz."""
        try:
            self.win.storage.save_roster(roster)
            self.win.history_manager.add(match)
            self.win.history_panel._refresh()
        except Exception:
            pass

    def _do_generate_match(self):

        focus_widget = QApplication.focusWidget()
        if focus_widget and hasattr(focus_widget, "clearFocus"):
            focus_widget.clearFocus()

        settings = self.win.settings_manager.settings
        roster = self.win.roster_controller.roster
        needed = settings.game_mode.total_players

        # Smart Queue & VIP Streamer Continuous Rotation
        if getattr(settings, "bench_rotation_enabled", False) and roster.bench:
            winner_team = self.win._current_match.winner if self.win._current_match else None
            p_in, p_out = roster.rotate_bench_and_teams(
                streamer_rest_interval=getattr(settings, "streamer_rest_interval", 0),
                policy=getattr(settings, "rotation_policy", "continuous"),
                batch_size=getattr(settings, "rotation_batch_size", 2),
                min_shield=getattr(settings, "min_matches_shield", 2),
                winner_team=winner_team,
            )
            if p_in > 0:
                self.win.roster_controller.after_roster_change()
                self.win.show_toast(f"🔄 Rotación ({p_in} entran, {p_out} a espera)", "info")

        active = roster.active_players()
        if len(active) < needed and roster.bench:
            filled_count = 0
            while roster.bench and roster.any_free_slot() is not None:
                p = roster.bench[0]
                target = 1 if roster.first_free_slot(1) is not None else 2
                try:
                    roster.add_from_bench_to_team(p, target)
                    filled_count += 1
                except Exception:
                    break
            if filled_count > 0:
                self.win.roster_controller.after_roster_change()
                active = roster.active_players()

        if not active:
            self.win.show_toast("⚠️ Agrega jugadores a los equipos para comenzar", "warning")
            return

        if len(active) < 2:
            self.win.show_toast("⚠️ Se necesitan al menos 2 jugadores para mezclar", "warning")
            return

        errors = validate_players(active, settings.game_mode, allow_partial=True)
        if errors:
            self.win.show_toast("⚠️ " + " · ".join(errors), "warning")
            return

        if settings.auto_roles:
            comp = settings.composition_for_mode()
            if comp.total != settings.game_mode.players_per_team:
                self.win.show_toast(
                    f"La composición {comp.tank}-{comp.damage}-{comp.support} no suma "
                    f"{settings.game_mode.players_per_team} jugadores por equipo.",
                    "warning",
                )
                return

        try:
            result = self.win.match_generator.generate(
                players=active,
                settings=settings,
                history=self.win.shuffle_history.get_all(),
                fixed_roles=self.win._fixed_roles if settings.auto_roles else None,
                allow_partial=True,
            )
        except ValueError as exc:
            self.win.show_toast(f"No se puede asignar roles: {exc}", "warning")
            return

        if result.error:
            self.win.show_toast(result.error, "warning")
            return

        # Sorteo Maestro: Si auto_map está activo, sortear nuevo mapa
        if settings.auto_map and self.win.map_pool.maps:
            chosen_map = self.win.map_pool.pick_random()
        else:
            chosen_map = (
                self.win._current_match.map
                if (self.win._current_match and self.win._current_match.map)
                else self.win.match_display.map_banner.get_map()
            )

        # Si auto_bans está activo, sortear nuevos baneos y verificar Audio FX
        if settings.auto_bans:
            bans_list = self._get_random_bans_with_trinity_chance()
            self.win.hero_widget.set_banned(set(bans_list))
            self.win.bans_panel.set_banned(bans_list)
        else:
            bans_list = result.bans

        self.win._current_match = Match(
            team1=result.team1,
            team2=result.team2,
            map=chosen_map,
            bans=bans_list,
            settings_snapshot=settings,
        )

        if chosen_map:
            self.win.match_display.set_map(chosen_map)
            self.win.map_widget.select_map(chosen_map)
            settings.last_selected_map = chosen_map.to_dict()
            self.win.settings_manager.save()
            # Locución táctica de Athena sobre el mapa sorteado
            if hasattr(self.win, "_egg_manager"):
                self.win._egg_manager.on_map_rolled(chosen_map.name, self.win)

        # Renderizado atómico en un solo frame (bloquea micro-parpadeos de slots)
        self.win.match_display.setUpdatesEnabled(False)
        try:
            self.apply_teams_to_slots(result.team1, result.team2)
            self.win.roster_controller.rebuild_fixed_roles()
            self.win.match_display.set_match(self.win._current_match)
            self.win.roster_controller.refresh_roster_ui()
        finally:
            self.win.match_display.setUpdatesEnabled(True)

        self.win.shuffle_history.add(
            result.team1, result.team2, settings.game_mode, settings
        )

        # Escritura asíncrona a disco diferida: Cero congelamiento en el hilo principal
        current_m = self.win._current_match
        QTimer.singleShot(25, lambda: self._persist_in_background(roster, current_m))

        special_names = [p.name for p in active if is_special_player_name(p.name)]
        if special_names:
            self.win._egg_manager.on_match_shuffled(special_names, self.win)

        self.win.status_bar.showMessage("Partida generada con balanceo", 3000)
        self.win.tabs.setCurrentIndex(0)
        self.win._update_nav_buttons_style()

    def reshuffle_teams(self):
        if getattr(self, "_is_generating", False):
            return
        now = time.time()
        if (now - self._last_shuffle_time) < 0.12:
            return
        self._is_generating = True
        try:
            self._do_reshuffle_teams()
        finally:
            self._last_shuffle_time = time.time()
            self._is_generating = False

    def _do_reshuffle_teams(self):

        if not self.win._current_match:
            self.generate_match()
            return

        settings = self.win.settings_manager.settings
        roster = self.win.roster_controller.roster
        try:
            result = self.win.match_generator.generate(
                players=roster.active_players(),
                settings=settings,
                history=self.win.shuffle_history.get_all(),
                fixed_roles=self.win._fixed_roles if settings.auto_roles else None,
                allow_partial=True,
            )
        except ValueError as exc:
            self.win.show_toast(f"No se puede asignar roles: {exc}", "warning")
            return

        if result.error:
            self.win.show_toast(result.error, "warning")
            return

        result.map = self.win._current_match.map
        result.bans = self.win._current_match.bans

        self.win._current_match = Match(
            team1=result.team1,
            team2=result.team2,
            map=result.map,
            bans=result.bans,
            settings_snapshot=settings,
        )

        self.win.match_display.setUpdatesEnabled(False)
        try:
            self.apply_teams_to_slots(result.team1, result.team2)
            self.win.roster_controller.rebuild_fixed_roles()
            self.win.match_display.set_match(self.win._current_match)
            self.win.roster_controller.refresh_roster_ui()
        finally:
            self.win.match_display.setUpdatesEnabled(True)

        self.win.shuffle_history.add(
            result.team1, result.team2, settings.game_mode, settings
        )

        current_m = self.win._current_match
        QTimer.singleShot(25, lambda: self._persist_in_background(roster, current_m))
        self.win.status_bar.showMessage("Equipos re-mezclados", 3000)

    def reroll_roles(self, team_num: int):
        settings = self.win.settings_manager.settings
        if not settings.auto_roles:
            return

        composition = settings.composition_for_mode()
        roster = self.win.roster_controller.roster
        slots = roster.team1_slots if team_num == 1 else roster.team2_slots
        players = [p for p in slots if p is not None]
        try:
            assigned = assign_roles(players, composition, self.win._fixed_roles)
        except ValueError as exc:
            self.win.show_toast(f"No se puede asignar roles: {exc}", "warning")
            return

        it = iter(assigned)
        for i, player in enumerate(slots):
            if player is not None:
                slots[i] = next(it)

        self.win.roster_controller.after_roster_change()
        self.win.status_bar.showMessage(f"Roles re-randomizados · Equipo {team_num}", 3000)

    def set_match_winner(self, winner_code: int | None):
        if self.win._current_match is None:
            # Si no se había generado partida formal pero hay jugadores, sincronizar
            self.sync_match_teams()
            if not self.win.roster_controller.roster.active_players():
                self.win.show_toast("⚠️ No hay jugadores en la partida para registrar resultado", "warning")
                return

        if self.win._current_match is not None:
            self.win._current_match.winner = winner_code
            self.win.history_manager.add(self.win._current_match)
            self.win.history_panel._refresh()

        self.win.match_display.set_winner(winner_code)

        if winner_code == 1:
            t1 = self.win.match_display.team1_widget.get_team_name()
        elif winner_code == 2:
            t2 = self.win.match_display.team2_widget.get_team_name()
        elif winner_code == 0:
            self.win.show_toast("⚖️ Empate registrado para la partida", "info")
        else:
            self.win.show_toast("↺ Resultado de partida restablecido a pendiente", "info")

    # ------------------------------------------------------------------
    # Map Operations
    # ------------------------------------------------------------------
    def clear_map(self):
        if self.win._current_match is not None:
            self.win._current_match.map = None
            self.win.history_manager.add(self.win._current_match)
            self.win.history_panel._refresh()
        self.win.match_display.set_map(None)
        self.win.map_widget.select_map(None)
        self.win.settings_manager.settings.last_selected_map = None
        self.win.settings_manager.save()
        self.win.status_bar.showMessage("Sin mapa seleccionado", 3000)

    def reroll_map(self, silent: bool = True):
        if not self.win.map_pool.maps:
            self.win.show_toast("⚠️ No hay mapas en el pool activo", "warning")
            return

        new_map = self.win.map_pool.pick_random()
        if self.win._current_match is not None:
            self.win._current_match.map = new_map
            self.win.history_manager.add(self.win._current_match)
            self.win.history_panel._refresh()

        self.win.match_display.set_map(new_map)
        self.win.map_widget.select_map(new_map)
        self.win.map_pool.load_history(
            self.win.history_manager.get_recent_maps(
                self.win.settings_manager.settings.avoid_recent_maps
            )
        )
        self.win.settings_manager.settings.last_selected_map = new_map.to_dict() if new_map else None
        self.win.settings_manager.save()

        # El banner ya se actualiza visualmente en grande, evitamos spam de toast
        if not silent:
            self.win.show_toast(f"🗺️ Mapa sorteado: {new_map.name} ({new_map.mode})", "info")
        self.win.status_bar.showMessage(f"Mapa sorteado: {new_map.name} ({new_map.mode})", 3000)

    def on_map_selected(self, map_obj: Map | None):
        if self.win._current_match:
            self.win._current_match.map = map_obj
            self.win.match_display.set_match(self.win._current_match)
        else:
            self.win.match_display.set_map(map_obj)

        self.win.settings_manager.settings.last_selected_map = map_obj.to_dict() if map_obj else None
        self.win.settings_manager.save()

    def on_maps_changed(self, maps: list[Map]):
        active_maps = [m for m in maps if getattr(m, "enabled", True)]
        self.win.map_pool = MapPool(active_maps, avoid_recent=self.win.map_pool.avoid_recent)
        self.win.map_pool.load_history(
            self.win.history_manager.get_recent_maps(self.win.map_pool.avoid_recent)
        )
        self.win.match_generator.map_pool = self.win.map_pool
        self.win.storage.save_maps(maps)

    def on_avoid_recent_changed(self, value: int):
        self.win.map_pool.avoid_recent = value
        self.win.settings_manager.update_avoid_recent_maps(value)

    # ------------------------------------------------------------------
    # Bans & Heroes Event Handlers
    # ------------------------------------------------------------------
    def _get_random_bans_with_trinity_chance(self) -> list[str]:
        from owervach_tmixer.ui.easter_eggs import is_sathara_in_match
        import random
        # 5% de probabilidad secreta si Sathara está en la partida
        if is_sathara_in_match(self.win) and random.random() < 0.05:
            mains = ["Wrecking Ball", "Pharah", "Brigitte"]
            all_other = [h.name for h in self.win.hero_manager.heroes if h.name not in mains]
            random.shuffle(all_other)
            max_b = self.win.hero_manager.ban_manager.max_bans
            needed = max(0, max_b - len(mains))
            return mains + all_other[:needed]

        self.win.hero_manager.randomize_bans()
        return list(self.win.hero_manager.get_banned())

    def randomize_bans_from_main(self):
        """Unified ban randomization shortcut from main interface with 5% Trinity chance."""
        new_bans = self._get_random_bans_with_trinity_chance()
        self.win.hero_widget.set_banned(set(new_bans))
        self.on_bans_changed(set(new_bans))
        play_ban_sound_for_pool(new_bans, window=self.win)


    def on_bans_changed(self, banned: set):
        self.win.hero_manager.ban_manager.banned = set(banned)
        self.win.storage.save_bans(self.win.hero_manager.ban_manager)
        if self.win._current_match:
            self.win._current_match.bans = list(banned)
            self.win.match_display.set_match(self.win._current_match)
        self.win.bans_panel.set_banned(sorted(set(banned)))
        if hasattr(self.win, "_egg_manager"):
            self.win._egg_manager.check_trinity_ban(banned, self.win)

    def on_max_bans_changed(self, value: int):
        self.win.hero_manager.set_max_bans(value)
        self.win.settings_manager.update_max_bans(value)
        self.win.storage.save_bans(self.win.hero_manager.ban_manager)

    def on_max_bans_per_role_changed(self, value: int):
        self.win.hero_manager.set_max_bans_per_role(value)
        self.win.settings_manager.update_max_bans_per_role(value)
        self.win.hero_widget.set_banned(self.win.hero_manager.ban_manager.banned)
        self.win.storage.save_bans(self.win.hero_manager.ban_manager)

    def on_heroes_changed(self, heroes: list[Hero]):
        self.win.hero_manager = HeroManager(
            heroes,
            max_bans=self.win.hero_manager.ban_manager.max_bans,
            max_bans_per_role=self.win.hero_manager.ban_manager.max_bans_per_role,
        )
        self.win.storage.save_heroes(heroes)

    # ------------------------------------------------------------------
    # Match History & Reset
    # ------------------------------------------------------------------
    def clear_all(self):
        """Clears both teams and the waiting bench in one atomic touch without blocking modals."""
        roster = self.win.roster_controller.roster
        if not roster.active_players() and not roster.bench:
            self.win.show_toast("ℹ️ Los equipos y la espera ya están vacíos", "info")
            return

        self.win._current_match = None
        self.win.match_display.set_match(None)
        roster.clear_teams_and_bench()
        self.win.roster_controller.after_roster_change()
        self.win.status_bar.showMessage("Equipos y Zona de Espera vaciados", 3000)
        self.win.show_toast("🧹 Equipos y Zona de Espera vaciados", "info")

    def new_match(self):
        reply = QMessageBox.question(
            self.win,
            "Nueva partida",
            "¿Crear una nueva partida? Se vaciarán los equipos y la lista de En Espera.\n"
            "Los jugadores guardados se conservan.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.win._current_match = None
            self.win.match_display.set_match(None)
            self.win.roster_controller.roster.clear_teams_and_bench()
            self.win.roster_controller.after_roster_change()
            self.win.status_bar.showMessage(
                "Equipos y En Espera vaciados · Guardados conservados", 3000
            )

    def load_match_from_history(self, match: Match):
        self.win._current_match = match
        self.apply_teams_to_slots(match.team1, match.team2)
        self.win.roster_controller.after_roster_change()
        self.win.match_display.set_match(match)
        if match.map:
            self.win.map_widget.select_map(match.map)
        self.win.tabs.setCurrentIndex(0)
        self.win._update_nav_buttons_style()
        self.win.status_bar.showMessage("Partida cargada del historial", 3000)

    # ------------------------------------------------------------------
    # Mode, Roles & Policy
    # ------------------------------------------------------------------
    def on_mode_changed(self, mode: GameMode):
        roster = self.win.roster_controller.roster
        before = roster.game_mode
        self.win.settings_manager.update_game_mode(mode)
        roster.on_game_mode_change(mode)
        self.adapt_pinned_roles_to_mode()
        if before != mode:
            self.win.roster_controller.after_roster_change(refresh_saved=False)
        else:
            self.win.roster_controller.refresh_roster_ui()
        self.win.status_bar.showMessage(f"Modo: {mode.value}", 3000)

    def adapt_pinned_roles_to_mode(self):
        s = self.win.settings_manager.settings
        comp = s.composition_for_mode()
        caps = {
            Role.TANK: comp.tank,
            Role.DAMAGE: comp.damage,
            Role.SUPPORT: comp.support,
        }
        counts = {Role.TANK: 0, Role.DAMAGE: 0, Role.SUPPORT: 0}
        for p in self.win.roster_controller.roster.active_players():
            if p.fixed_role and p.role is not None:
                if counts[p.role] >= caps[p.role]:
                    p.fixed_role = False
                else:
                    counts[p.role] += 1

    def apply_role_policy(self):
        s = self.win.settings_manager.settings
        if not s.show_roles and s.auto_roles:
            s.auto_roles = False
            self.win.settings_manager.save()

        self.win.roles_toggle.blockSignals(True)
        self.win.roles_toggle.setChecked(s.show_roles)
        self.win.roles_toggle.blockSignals(False)

        self.win.randomize_roles_toggle.blockSignals(True)
        self.win.randomize_roles_toggle.setChecked(s.auto_roles)
        self.win.randomize_roles_toggle.setEnabled(s.show_roles)
        self.win.randomize_roles_toggle.blockSignals(False)

        self.win._update_pill_style(self.win.roles_toggle, "#00B4FF")
        self.win._update_pill_style(self.win.randomize_roles_toggle, "#61ab02")

        self.win.match_display.team1_widget.btn_mix_roles.setEnabled(
            s.show_roles and s.auto_roles
        )
        self.win.match_display.team2_widget.btn_mix_roles.setEnabled(
            s.show_roles and s.auto_roles
        )

    def on_show_roles_toggled(self, checked: bool):
        self.win.settings_manager.update_show_roles(checked)
        self.apply_role_policy()
        self.win._update_pill_style(self.win.roles_toggle, "#00B4FF")
        self.win.match_display.set_show_roles(checked)
        if checked and not self.win.settings_manager.settings.auto_roles:
            self.win.roster_controller.after_roster_change()
        else:
            self.win.roster_controller.refresh_roster_ui()
        self.win.status_bar.showMessage(
            f"Mostrar roles: {'Activados' if checked else 'Ocultos'}", 3000
        )

    def on_randomize_roles_toggled(self, checked: bool):
        if not self.win.settings_manager.settings.show_roles:
            return
        self.win.settings_manager.update_auto_roles(checked)
        self.win._update_pill_style(self.win.randomize_roles_toggle, "#61ab02")
        self.win.match_display.team1_widget.btn_mix_roles.setEnabled(checked)
        self.win.match_display.team2_widget.btn_mix_roles.setEnabled(checked)
        if checked:
            self.win.roster_controller.refresh_roster_ui()
        else:
            self.win.roster_controller.after_roster_change()
        self.win.status_bar.showMessage(
            f"Randomizar roles: {'Activado' if checked else 'Desactivado'}", 3000
        )

    def on_tryhard_toggled(self, checked: bool):
        self.win.settings_manager.settings.balance_by_mmr = checked
        self.win.settings_manager.save()
        self.win._update_pill_style(self.win.tryhard_toggle, "#9D5CFF")
        self.win.match_display.set_show_mmr(checked)
        self.win.roster_controller.refresh_roster_ui()
        if checked:
            self.win.show_toast("⚖️ Modo Tryhard ACTIVADO: Balance por MMR y Rol", "info")
        else:
            self.win.show_toast("🎲 Modo Casual ACTIVADO: Mezcla libre", "info")

    def on_rotation_toggled(self, checked: bool):
        self.win.settings_manager.settings.bench_rotation_enabled = checked
        self.win.settings_manager.save()
        if hasattr(self.win, "rotation_toggle"):
            self.win._update_pill_style(self.win.rotation_toggle, "#FFAA00")
        # Sincronización visual instantánea de fichas en la Zona de Espera
        self.win.roster_controller.refresh_roster_ui()
        if checked:
            self.win.show_toast("🔄 Rotación de Banca ACTIVADA: Espera rotará al mezclar", "info")
        else:
            self.win.show_toast("🛑 Rotación de Banca DESACTIVADA: Partida aislada", "info")

    def on_team_name_changed(self, team_num: int, name: str):
        s = self.win.settings_manager.settings
        self.win.settings_manager.update_team_names(
            team1=name if team_num == 1 else s.team1_name,
            team2=name if team_num == 2 else s.team2_name,
        )
        self.sync_match_teams()

    # ------------------------------------------------------------------
    # Factory Reset
    # ------------------------------------------------------------------
    def factory_reset(self):
        settings, maps, heroes, roster = self.win.storage.factory_reset()
        self.win.settings_manager._settings = settings
        self.win.shuffle_history.clear()
        self.win.storage.clear_history()

        self.win._roster = roster
        self.win.roster_controller.roster = roster
        self.win._current_match = None
        self.win._fixed_roles.clear()

        self.win.map_pool = MapPool(
            [m for m in maps if getattr(m, "enabled", True)],
            avoid_recent=settings.avoid_recent_maps,
        )
        self.win.hero_manager = HeroManager(
            heroes,
            max_bans=settings.max_bans,
            max_bans_per_role=settings.max_bans_per_role,
        )
        self.win.match_generator.map_pool = self.win.map_pool
        self.win.match_generator.hero_manager = self.win.hero_manager

        self.win.map_widget.set_maps(maps)
        self.win.hero_widget.set_heroes(heroes)
        self.win.hero_widget.set_banned(set())
        self.win.bans_panel.set_banned([])
        self.win.match_display.set_match(None)
        self.win.match_display.set_map(None)
        self.win.history_panel._refresh()

        theme.set_accent(settings.accent_color)
        self.win._apply_settings_to_widgets()
        self.win._apply_theme()
        self.win.roster_controller.refresh_roster_ui()
        self.win.show_toast("☢️ Sistema restablecido con éxito a estado de fábrica", "special")
