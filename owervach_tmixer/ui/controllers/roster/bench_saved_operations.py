"""Bench & Saved players operations mixin."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from PySide6.QtWidgets import QMessageBox

from owervach_tmixer.core.roster import RosterError
from owervach_tmixer.core.special_player import is_special_player_name, get_delete_confirm_prompt

if TYPE_CHECKING:
    from owervach_tmixer.ui.controllers.roster_controller import RosterController


class BenchSavedOperationsMixin:
    """Handles bench pool, saved list management, and bulk operations."""

    def bench_add_to_team(self: RosterController, name: str, team_num: int | None):
        player = self.find_in(self.roster.bench, name)
        if player is None:
            return
        target = team_num
        if target not in (1, 2):
            free_fixed = self.roster.first_free_slot(player.fixed_team)
            if player.fixed_team in (1, 2) and free_fixed is not None:
                target = player.fixed_team
            else:
                free = self.roster.any_free_slot()
                if free is None:
                    self.win.show_toast(
                        "Ambos equipos están llenos. Mezcla o quita jugadores primero.",
                        "warning",
                    )
                    return
                target = free[0]
        try:
            self.roster.add_from_bench_to_team(player, target)
        except RosterError as exc:
            self.win.show_toast(str(exc), "warning")
            return
        self.after_roster_change()
        if is_special_player_name(name):
            self.win._egg_manager.on_player_joined_team(name, target, self.win)

    def bench_remove(self: RosterController, name: str):
        if self.find_in(self.roster.bench, name) is not None:
            self.roster.remove_from_bench(name)
            self.after_roster_change()
            if is_special_player_name(name):
                self.win._egg_manager.on_player_bench_removed(name, self.win)

    def bench_remove_permanent(self: RosterController, name: str):
        player = self.find_in(self.roster.bench, name)
        if player is None:
            return
        title, prompt_msg = get_delete_confirm_prompt(name, context_type="permanent")
        reply = QMessageBox.question(
            self.win,
            title,
            prompt_msg,
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.roster.remove_from_bench(name)
        self.roster.remove_saved(player)
        self.after_roster_change()
        if is_special_player_name(name):
            self.win._egg_manager.on_player_permanently_removed(name, self.win)

    def bench_save(self: RosterController, name: str):
        player = self.find_in(self.roster.bench, name)
        if player is None or self.roster.is_saved(player):
            return
        self.roster.save_player(player)
        self.after_roster_change()
        if is_special_player_name(name):
            self.win._egg_manager.on_player_saved(name, self.win)

    def bench_unsave(self: RosterController, name: str):
        if self.find_in(self.roster.bench, name) is not None:
            self.roster.remove_saved_name(name)
            self.after_roster_change()
            if is_special_player_name(name):
                self.win._egg_manager.on_player_permanently_removed(name, self.win)

    def fill_teams_from_bench(self: RosterController):
        if not self.roster.bench:
            self.win.show_toast("ℹ️ No hay jugadores en Zona de Espera", "info")
            return

        free_count = sum(1 for p in self.roster.team1_slots if p is None) + \
                     sum(1 for p in self.roster.team2_slots if p is None)
        if free_count == 0:
            self.win.show_toast("⚠️ Ambos equipos ya están llenos", "warning")
            return

        moved = 0
        while self.roster.bench and self.roster.any_free_slot() is not None:
            player = self.roster.bench[0]
            target_team = 1 if self.roster.first_free_slot(1) is not None else 2
            try:
                self.roster.add_from_bench_to_team(player, target_team)
                moved += 1
            except RosterError:
                break

        self.after_roster_change()
        if moved > 0:
            self.win.show_toast(f"✅ {moved} jugador(es) asignados a los equipos", "success")
            self.win.status_bar.showMessage(f"{moved} jugadores movidos a equipos", 3000)

    def fill_teams_from_saved(self: RosterController):
        if not self.roster.saved:
            self.win.show_toast("ℹ️ No hay jugadores en tu lista de Guardados", "info")
            return

        free_count = sum(1 for p in self.roster.team1_slots if p is None) + \
                     sum(1 for p in self.roster.team2_slots if p is None)
        if free_count == 0:
            self.win.show_toast("⚠️ Ambos equipos ya están llenos", "warning")
            return

        active_names = {p.name.casefold() for p in self.roster.active_players()}
        moved = 0
        for saved_p in self.roster.saved:
            if saved_p.name.casefold() in active_names:
                continue
            if self.roster.any_free_slot() is None:
                break
            target_team = 1 if self.roster.first_free_slot(1) is not None else 2
            try:
                self.roster.add_pending_to_team(
                    saved_p.name,
                    role=saved_p.role,
                    fixed_team=saved_p.fixed_team,
                    team_num=target_team,
                    fixed_role=saved_p.fixed_role,
                )
                active_names.add(saved_p.name.casefold())
                moved += 1
            except RosterError:
                continue

        self.after_roster_change()
        if moved > 0:
            self.win.show_toast(f"✅ {moved} jugador(es) guardados asignados a los equipos", "success")
        else:
            self.win.show_toast("ℹ️ Todos los jugadores guardados ya están en la partida", "info")

    def send_all_saved_to_bench(self: RosterController):
        if not self.roster.saved:
            self.win.show_toast("ℹ️ No hay jugadores en tu lista de Guardados", "info")
            return

        active_and_bench = {p.name.casefold() for p in self.roster.active_players()} | \
                           {p.name.casefold() for p in self.roster.bench}
        moved = 0
        for saved_p in self.roster.saved:
            if saved_p.name.casefold() not in active_and_bench:
                try:
                    self.roster.add_to_bench(saved_p.name)
                    active_and_bench.add(saved_p.name.casefold())
                    moved += 1
                except RosterError:
                    continue

        self.after_roster_change()
        if moved > 0:
            self.win.show_toast(f"🪑 {moved} jugador(es) guardados añadidos a Zona de Espera", "info")
        else:
            self.win.show_toast("ℹ️ Todos los jugadores guardados ya están en partida o en espera", "info")

    def bench_all_teams(self: RosterController):
        active = self.roster.active_players()
        if not active:
            self.win.show_toast("ℹ️ No hay jugadores en los equipos", "info")
            return

        moved = 0
        for idx, p in enumerate(list(self.roster.team1_slots)):
            if p is not None:
                self.roster.send_to_bench(1, idx)
                moved += 1

        for idx, p in enumerate(list(self.roster.team2_slots)):
            if p is not None:
                self.roster.send_to_bench(2, idx)
                moved += 1

        self.after_roster_change()
        self.win.show_toast(f"📤 {moved} jugador(es) enviados a Zona de Espera", "info")
        self.win.status_bar.showMessage("Todos los jugadores enviados a Zona de Espera", 3000)

    def saved_add_to_match(self: RosterController, name: str, team_num: int):
        self.handle_saved_dropped_on_team(name, team_num, None)

    def saved_add_to_bench(self: RosterController, name: str):
        saved = self.find_in(self.roster.saved, name)
        if saved is None:
            return
        try:
            self.roster.add_to_bench(name)
        except RosterError as exc:
            self.win.show_toast(str(exc), "warning")
            return
        self.after_roster_change()
        if is_special_player_name(name):
            self.win._egg_manager.on_player_benched(name, self.win)

    def saved_chip_activated(self: RosterController, name: str):
        saved = self.find_in(self.roster.saved, name)
        if saved is None:
            return
        if self.roster.any_free_slot() is not None:
            self.handle_saved_dropped_on_team(name, 0, None)
        else:
            self.saved_add_to_bench(name)
            self.win.status_bar.showMessage(
                f"Equipos llenos · {name} añadido a Zona de Espera", 3000
            )

    def saved_remove(self: RosterController, name: str):
        title, prompt_msg = get_delete_confirm_prompt(name, context_type="saved")
        reply = QMessageBox.question(
            self.win,
            title,
            prompt_msg,
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.roster.remove_saved_name(name)
        self.after_roster_change()
        if is_special_player_name(name):
            self.win._egg_manager.on_player_permanently_removed(name, self.win)

    def bulk_saved(self: RosterController, names: list[str]):
        added = self._add_names_to_saved(names)
        if added:
            self.after_roster_change()
            self.win.status_bar.showMessage(
                f"{added} jugador(es) añadido(s) a guardados", 3000
            )

    def _add_names_to_saved(self: RosterController, names: list[str]) -> int:
        added = 0
        for raw in names:
            name = str(raw).strip()
            if not name:
                continue
            if name.casefold() in self.roster.saved_names():
                continue
            self.roster.save_name(name)
            added += 1
        return added

    def import_saved(self: RosterController, path: str):
        try:
            names = []
            if path.endswith(".json"):
                with open(path, encoding="utf-8") as f:
                    for entry in json.load(f):
                        if isinstance(entry, str):
                            names.append(entry)
                        elif isinstance(entry, dict) and entry.get("name"):
                            names.append(entry["name"])
            else:
                with open(path, encoding="utf-8") as f:
                    names = [line.strip() for line in f if line.strip()]
            added = self._add_names_to_saved(names)
            self.after_roster_change()
            self.win.show_toast(f"{added} jugador(es) añadido(s) a guardados.", "success")
        except Exception as exc:
            self.win.show_toast(f"No se pudo importar: {exc}", "warning")

    def export_saved(self: RosterController, path: str):
        try:
            if path.endswith(".json"):
                self.win.storage.export_players(self.roster.saved, path)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("\n".join(p.name for p in self.roster.saved))
            self.win.show_toast("Guardados exportados correctamente.", "success")
        except Exception as exc:
            self.win.show_toast(f"No se pudo exportar: {exc}", "warning")


    def reorder_bench(self: RosterController, src_name: str, target_name: str):
        if src_name == target_name:
            return
        idx_src = next((i for i, p in enumerate(self.roster.bench) if p.name == src_name), -1)
        idx_tgt = next((i for i, p in enumerate(self.roster.bench) if p.name == target_name), -1)
        if idx_src != -1 and idx_tgt != -1:
            p = self.roster.bench.pop(idx_src)
            self.roster.bench.insert(idx_tgt, p)
            self.after_roster_change()

    def reorder_saved(self: RosterController, src_name: str, target_name: str):
        if src_name == target_name:
            return
        idx_src = next((i for i, p in enumerate(self.roster.saved) if p.name == src_name), -1)
        idx_tgt = next((i for i, p in enumerate(self.roster.saved) if p.name == target_name), -1)
        if idx_src != -1 and idx_tgt != -1:
            p = self.roster.saved.pop(idx_src)
            self.roster.saved.insert(idx_tgt, p)
            self.after_roster_change()

    def bulk_bench_save(self: RosterController, names: list[str]):
        count = 0
        for name in names:
            p = self.find_in(self.roster.bench, name)
            if p and not self.roster.is_saved(p):
                self.roster.save_player(p)
                count += 1
        if count > 0:
            self.after_roster_change()
            self.win.show_toast(f"⭐ {count} jugador(es) guardados", "success")

    def bulk_bench_remove(self: RosterController, names: list[str]):
        for name in names:
            self.roster.remove_from_bench(name)
        self.after_roster_change()
        self.win.show_toast(f"✕ {len(names)} jugador(es) retirados de espera", "info")

    def bulk_bench_add_to_team(self: RosterController, names: list[str], team_num: int):
        moved = 0
        for name in names:
            p = self.find_in(self.roster.bench, name)
            if p and self.roster.first_free_slot(team_num) is not None:
                try:
                    self.roster.add_from_bench_to_team(p, team_num)
                    moved += 1
                except Exception:
                    break
        self.after_roster_change()
        if moved > 0:
            self.win.show_toast(f"🎮 {moved} jugador(es) añadidos al Equipo {team_num}", "success")
        else:
            self.win.show_toast(f"⚠️ El Equipo {team_num} no tiene suficientes espacios", "warning")

    def bulk_saved_add_to_bench(self: RosterController, names: list[str]):
        moved = 0
        bench_names = {p.name.casefold() for p in self.roster.bench}
        for name in names:
            if name.casefold() not in bench_names:
                try:
                    self.roster.add_to_bench(name)
                    bench_names.add(name.casefold())
                    moved += 1
                except Exception:
                    continue
        self.after_roster_change()
        if moved > 0:
            self.win.show_toast(f"🪑 {moved} jugador(es) añadidos a Zona de Espera", "info")

    def bulk_saved_add_to_team(self: RosterController, names: list[str], team_num: int):
        moved = 0
        for name in names:
            if self.roster.first_free_slot(team_num) is None:
                break
            p = self.find_in(self.roster.saved, name)
            if p:
                try:
                    self.roster.add_pending_to_team(name, role=p.role, fixed_team=p.fixed_team, team_num=team_num)
                    moved += 1
                except Exception:
                    continue
        self.after_roster_change()
        if moved > 0:
            self.win.show_toast(f"🎮 {moved} jugador(es) añadidos al Equipo {team_num}", "success")
        else:
            self.win.show_toast(f"⚠️ El Equipo {team_num} ya está lleno", "warning")

    def bulk_saved_remove(self: RosterController, names: list[str]):
        reply = QMessageBox.question(
            self.win,
            "Eliminar jugadores guardados",
            f"¿Deseas eliminar permanentemente a los {len(names)} jugadores seleccionados de tu lista de guardados?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            for name in names:
                self.roster.remove_saved_name(name)
            self.after_roster_change()
            self.win.show_toast(f"🗑️ {len(names)} jugador(es) eliminados de guardados", "info")
