"""Slot operations mixin: Creation, renaming, roles, MMR, and color customization."""

from __future__ import annotations

from typing import TYPE_CHECKING
from PySide6.QtWidgets import QMessageBox

from owervach_tmixer.core.models import Role
from owervach_tmixer.core.roster import RosterError
from owervach_tmixer.core.special_player import format_player_name, is_special_player_name, get_delete_confirm_prompt

if TYPE_CHECKING:
    from owervach_tmixer.ui.controllers.roster_controller import RosterController


class SlotOperationsMixin:
    """Handles cell mutations, renaming, role assignment, and MMR."""

    def create_in_slot(self: RosterController, team_num: int, slot_idx: int, name: str):
        auto_caps = getattr(self.win.settings_manager.settings, "auto_capitalize_names", True)
        clean_name = format_player_name(name, auto_caps)
        try:
            self.roster.create_in_slot(team_num, slot_idx, clean_name)
        except RosterError as exc:
            self.win.show_toast(str(exc), "warning")
            return
        self.after_roster_change()
        if is_special_player_name(clean_name):
            self.win._egg_manager.on_player_joined_team(clean_name, team_num, self.win)

    def rename_slot(self: RosterController, team_num: int, slot_idx: int, new_name: str):
        player = self.roster.player_at(team_num, slot_idx)
        if player is None:
            return
        self.rename_global(player.name, new_name)

    def rename_global(self: RosterController, old_name: str, new_name: str):
        auto_caps = getattr(self.win.settings_manager.settings, "auto_capitalize_names", True)
        clean_name = format_player_name(new_name, auto_caps)
        if not clean_name or clean_name == old_name:
            return

        old_folded = old_name.casefold()
        new_folded = clean_name.casefold()

        # Blindaje: Evitar colisión con jugadores existentes al renombrar
        if new_folded != old_folded:
            for p in self.roster.active_players() + self.roster.bench:
                if p.name.casefold() == new_folded and p.name.casefold() != old_folded:
                    self.win.show_toast(f"⚠️ El jugador '{clean_name}' ya existe.", "warning")
                    return

        for p in self.roster.active_players():
            if p.name.casefold() == old_folded:
                p.name = clean_name

        for p in self.roster.bench:
            if p.name.casefold() == old_folded:
                p.name = clean_name

        for p in self.roster.saved:
            if p.name.casefold() == old_folded:
                p.name = clean_name

        if old_name in self.win._fixed_roles:
            self.win._fixed_roles[clean_name] = self.win._fixed_roles.pop(old_name)

        self.after_roster_change()
        self.win.show_toast(f"✏️ Jugador renombrado a '{clean_name}'", "info")

    def set_slot_vip(self: RosterController, team_num: int, slot_idx: int, is_vip: bool):
        player = self.roster.player_at(team_num, slot_idx)
        if player is None:
            return
        self.set_global_player_vip(player.name, is_vip)

    def set_global_player_vip(self: RosterController, name: str, is_vip: bool):
        """Sincroniza el privilegio Streamer en partida, espera y guardados (Regla de Armonía)."""
        target_folded = name.casefold()
        for p in self.roster.active_players() + self.roster.bench + self.roster.saved:
            if p.name.casefold() == target_folded:
                p.is_vip = is_vip
        self.after_roster_change()
        status = "otorgada" if is_vip else "retirada"
        self.win.show_toast(f"👑 Prioridad Streamer {status} para '{name}'", "info")

    def clear_all_vips(self: RosterController):
        """Cierre de sesión Sudo: Quita todas las coronas del sistema con un solo clic."""
        count = 0
        for p in self.roster.active_players() + self.roster.bench + self.roster.saved:
            if getattr(p, "is_vip", False):
                p.is_vip = False
                count += 1
        self.after_roster_change()
        self.win.show_toast(f"👑 Se retiraron {count} coronas de Streamer (Sesión sudo cerrada)", "info")

    def set_slot_fixed_team(self: RosterController, team_num: int, slot_idx: int, new_fixed_team: int | None):
        player = self.roster.player_at(team_num, slot_idx)
        if player is None:
            return
        if new_fixed_team is not None:
            team_size = self.roster.game_mode.players_per_team
            fixed_count = sum(
                1
                for p in self.roster.active_players()
                if p.fixed_team == new_fixed_team and p is not player
            )
            if fixed_count >= team_size:
                self.win.show_toast(
                    f"El Equipo {new_fixed_team} ya tiene {team_size} jugadores fijados.",
                    "warning",
                )
                return
        player.fixed_team = new_fixed_team
        self.after_roster_change()
        if new_fixed_team:
            self.win.status_bar.showMessage(
                f"{player.name} fijado en Equipo {new_fixed_team}", 3000
            )
        else:
            self.win.status_bar.showMessage(f"{player.name} desfijado", 3000)

    def set_slot_role(self: RosterController, team_num: int, slot_idx: int, role: Role | None):
        player = self.roster.player_at(team_num, slot_idx)
        if player is None:
            return
        player.role = role
        player.fixed_role = role is not None
        self.after_roster_change()
        if role:
            self.win.status_bar.showMessage(
                f"Rol fijado: {player.name} → {role.value.capitalize()}", 3000
            )
        else:
            self.win.status_bar.showMessage(f"Rol quitado: {player.name}", 3000)

    def set_slot_mmr(self: RosterController, team_num: int, slot_idx: int, role: Role | None, mmr: int):
        player = self.roster.player_at(team_num, slot_idx)
        if player is None:
            return
        if role is None:
            player.mmr = mmr
        elif role == Role.TANK:
            player.mmr_tank = mmr
        elif role == Role.DAMAGE:
            player.mmr_damage = mmr
        elif role == Role.SUPPORT:
            player.mmr_support = mmr

        p_saved = self.find_in(self.roster.saved, player.name)
        if p_saved:
            if role is None:
                p_saved.mmr = mmr
            elif role == Role.TANK:
                p_saved.mmr_tank = mmr
            elif role == Role.DAMAGE:
                p_saved.mmr_damage = mmr
            elif role == Role.SUPPORT:
                p_saved.mmr_support = mmr

        self.after_roster_change(refresh_saved=False)
        if is_special_player_name(player.name):
            self.win._egg_manager.on_player_mmr_changed(player.name, mmr, self.win)
        else:
            role_label = f" ({role.value.capitalize()})" if role else " (General)"
            self.win.show_toast(f"⚖️ Nivel de {player.name}{role_label} actualizado a ★ {mmr}/10", "info")

    def set_global_player_mmr(self: RosterController, name: str, role: Role | None, mmr: int):
        p_saved = self.find_in(self.roster.saved, name)
        if p_saved:
            if role is None:
                p_saved.mmr = mmr
            elif role == Role.TANK:
                p_saved.mmr_tank = mmr
            elif role == Role.DAMAGE:
                p_saved.mmr_damage = mmr
            elif role == Role.SUPPORT:
                p_saved.mmr_support = mmr

        p_bench = self.find_in(self.roster.bench, name)
        if p_bench:
            if role is None:
                p_bench.mmr = mmr
            elif role == Role.TANK:
                p_bench.mmr_tank = mmr
            elif role == Role.DAMAGE:
                p_bench.mmr_damage = mmr
            elif role == Role.SUPPORT:
                p_bench.mmr_support = mmr

        for p in self.roster.active_players():
            if p.name.casefold() == name.casefold():
                if role is None:
                    p.mmr = mmr
                elif role == Role.TANK:
                    p.mmr_tank = mmr
                elif role == Role.DAMAGE:
                    p.mmr_damage = mmr
                elif role == Role.SUPPORT:
                    p.mmr_support = mmr

        self.after_roster_change(refresh_saved=False)
        if is_special_player_name(name):
            self.win._egg_manager.on_player_mmr_changed(name, mmr, self.win)
        else:
            role_label = f" ({role.value.capitalize()})" if role else " (General)"
            self.win.show_toast(f"⚖️ Nivel de {name}{role_label} actualizado a ★ {mmr}/10", "info")

    def set_global_player_color(self: RosterController, name: str, color_hex: str | None):
        target_folded = name.casefold()

        for p in self.roster.active_players():
            if p.name.casefold() == target_folded:
                p.custom_color = color_hex

        for p in self.roster.bench:
            if p.name.casefold() == target_folded:
                p.custom_color = color_hex

        for p in self.roster.saved:
            if p.name.casefold() == target_folded:
                p.custom_color = color_hex

        self.after_roster_change()

    def send_to_bench(self: RosterController, team_num: int, slot_idx: int):
        player = self.roster.send_to_bench(team_num, slot_idx)
        if player is None:
            return
        self.after_roster_change()
        self.win.status_bar.showMessage(f"{player.name} enviado a Zona de Espera", 3000)
        if is_special_player_name(player.name):
            self.win._egg_manager.on_player_benched(player.name, self.win)

    def save_player(self: RosterController, team_num: int, slot_idx: int):
        player = self.roster.player_at(team_num, slot_idx)
        if player is None or self.roster.is_saved(player):
            return
        self.roster.save_player(player)
        self.after_roster_change()
        if is_special_player_name(player.name):
            self.win._egg_manager.on_player_saved(player.name, self.win)

    def unsave_player(self: RosterController, team_num: int, slot_idx: int):
        player = self.roster.player_at(team_num, slot_idx)
        if player is None:
            return
        self.roster.remove_saved(player)
        self.after_roster_change()
        if is_special_player_name(player.name):
            self.win._egg_manager.on_player_permanently_removed(player.name, self.win)

    def remove_player(self: RosterController, team_num: int, slot_idx: int):
        player = self.roster.clear_slot(team_num, slot_idx)
        if player is None:
            return
        self.after_roster_change()
        self.win.status_bar.showMessage(f"{player.name} quitado de la partida", 3000)
        if is_special_player_name(player.name):
            self.win._egg_manager.on_player_removed(player.name, self.win)

    def remove_permanent(self: RosterController, team_num: int, slot_idx: int):
        player = self.roster.player_at(team_num, slot_idx)
        if player is None:
            return
        title, prompt_msg = get_delete_confirm_prompt(player.name, context_type="permanent")
        reply = QMessageBox.question(
            self.win,
            title,
            prompt_msg,
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.roster.clear_slot(team_num, slot_idx)
        self.roster.remove_saved(player)
        self.after_roster_change()
        if is_special_player_name(player.name):
            self.win._egg_manager.on_player_permanently_removed(player.name, self.win)
