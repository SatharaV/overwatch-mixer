"""Drag & Drop routing operations mixin with seamless Bench -> Team transfers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from owervach_tmixer.core.roster import RosterError
from owervach_tmixer.core.special_player import is_special_player_name

if TYPE_CHECKING:
    from owervach_tmixer.ui.controllers.roster_controller import RosterController


class DndOperationsMixin:
    """Handles player drag & drop relocation and persistence with zero-friction transitions."""

    def handle_player_drop(self: RosterController, payload: dict[str, Any], target_team: int, target_idx: int | None):
        kind = payload.get("kind")
        name = payload.get("name", "")

        # 1. Reparto múltiple desde Zona de Espera
        if kind == "bench_multi":
            names = payload.get("names", [name])
            moved = 0
            curr_slot = target_idx
            for p_name in names:
                if curr_slot is not None and self.roster.player_at(target_team, curr_slot) is None:
                    dest_slot = curr_slot
                    curr_slot = None
                else:
                    dest_slot = self.roster.first_free_slot(target_team)

                if dest_slot is None:
                    break

                try:
                    self.roster.relocate(
                        {"kind": "bench", "name": p_name},
                        target_team,
                        dest_slot,
                        cross_team_swap=False,
                    )
                    moved += 1
                except Exception:
                    break

            self.after_roster_change()
            self.win.bench_panel.selected_names.clear()
            self.win.bench_panel._refresh_selection_visuals()
            if moved > 0:
                self.win.show_toast(f"🎮 {moved} jugadores añadidos al Equipo {target_team}", "success")
            else:
                self.win.show_toast(f"⚠️ El Equipo {target_team} ya está lleno", "warning")
            return

        # 2. Reparto múltiple desde Guardados
        if kind == "saved_multi":
            names = payload.get("names", [name])
            moved = 0
            curr_slot = target_idx
            for p_name in names:
                if curr_slot is not None and self.roster.player_at(target_team, curr_slot) is None:
                    dest_slot = curr_slot
                    curr_slot = None
                else:
                    dest_slot = self.roster.first_free_slot(target_team)

                if dest_slot is None:
                    break

                try:
                    self.handle_saved_dropped_on_team(p_name, target_team, dest_slot)
                    moved += 1
                except Exception:
                    break

            self.after_roster_change()
            self.win.saved_panel.selected_names.clear()
            self.win.saved_panel._refresh_selection_visuals()
            if moved > 0:
                self.win.show_toast(f"🎮 {moved} jugadores guardados añadidos al Equipo {target_team}", "success")
            else:
                self.win.show_toast(f"⚠️ El Equipo {target_team} ya está lleno", "warning")
            return

        if kind == "saved":
            self.handle_saved_dropped_on_team(name, target_team, target_idx)
            return

        if kind == "slot":
            src = (payload.get("team"), payload.get("idx"))
            if src == (target_team, target_idx):
                return

        try:
            msg = self.roster.relocate(
                payload,
                target_team if target_team in (1, 2) else 0,
                target_idx if isinstance(target_idx, int) and target_idx >= 0 else None,
                cross_team_swap=self.win.settings_manager.settings.dnd_cross_team_swap,
            )
        except RosterError as exc:
            self.win.show_toast(str(exc), "warning")
            return
        self.after_roster_change()
        if msg and msg != "Sin cambios":
            self.win.status_bar.showMessage(msg, 3000)
            if is_special_player_name(name):
                self.win._egg_manager.on_player_joined_team(name, target_team, self.win)

    def handle_saved_dropped_on_team(self: RosterController, name: str, target_team: int, target_idx: int | None = None):
        saved = self.find_in(self.roster.saved, name)
        bench_p = self.find_in(self.roster.bench, name)
        if saved is None and bench_p is None:
            return

        role = saved.role if saved else (bench_p.role if bench_p else None)
        fixed_team = saved.fixed_team if saved else (bench_p.fixed_team if bench_p else None)
        fixed_role = saved.fixed_role if saved else (bench_p.fixed_role if bench_p else False)
        custom_color = (saved.custom_color if saved else None) or (bench_p.custom_color if bench_p else None)

        team_num = target_team if target_team in (1, 2) else 0

        was_in_bench = bench_p is not None
        if was_in_bench:
            self.roster.remove_from_bench(name)

        try:
            self.roster.add_pending_to_team(
                name,
                role=role,
                fixed_team=fixed_team,
                team_num=team_num,
                slot_idx=target_idx,
                fixed_role=fixed_role,
                custom_color=custom_color,
            )
        except RosterError as exc:
            if was_in_bench:
                self.roster.add_to_bench(name)
            self.win.show_toast(str(exc), "warning")
            return

        self.after_roster_change()
        self.win.status_bar.showMessage(f"{name} añadido a la partida", 3000)
        if is_special_player_name(name):
            self.win._egg_manager.on_player_joined_team(name, team_num, self.win)

    def handle_drop_to_bench(self: RosterController, payload: dict[str, Any]):
        kind = payload.get("kind")
        if kind == "slot":
            self.send_to_bench(payload.get("team"), payload.get("idx"))
        elif kind == "saved":
            self.saved_add_to_bench(payload.get("name", ""))
        elif kind == "saved_multi":
            self.bulk_saved_add_to_bench(payload.get("names", []))
            self.win.saved_panel.selected_names.clear()
            self.win.saved_panel._refresh_selection_visuals()

    def handle_player_dropped_to_saved(self: RosterController, payload: dict[str, Any]):
        kind = payload.get("kind")
        if kind == "bench_multi":
            self.bulk_bench_save(payload.get("names", []))
            self.win.bench_panel.selected_names.clear()
            self.win.bench_panel._refresh_selection_visuals()
            return
        player = None
        if kind == "slot":
            team_num = payload.get("team")
            slot_idx = payload.get("idx")
            if team_num in (1, 2) and slot_idx is not None:
                player = self.roster.player_at(team_num, slot_idx)
        elif kind == "bench":
            name = payload.get("name")
            if name:
                player = self.find_in(self.roster.bench, name)

        if player is None:
            return

        if self.roster.is_saved(player):
            self.win.show_toast(f"ℹ️ '{player.name}' ya está en tu lista de guardados", "info")
            return

        self.roster.save_player(player)
        self.after_roster_change()
        if is_special_player_name(player.name):
            self.win._egg_manager.on_player_saved(player.name, self.win)
        else:
            self.win.show_toast(f"⭐ '{player.name}' añadido a guardados", "success")
