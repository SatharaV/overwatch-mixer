"""Context menu and interactive actions for PlayerSlotWidget."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import QColorDialog, QDialog, QInputDialog, QMenu

from owervach_tmixer.core.models import Role
from owervach_tmixer.core.special_player import format_player_name, is_special_player_name
from owervach_tmixer.ui.dialogs.player_properties_dialog import PlayerPropertiesDialog

if TYPE_CHECKING:
    from .player_slot import PlayerSlotWidget


def show_slot_context_menu(slot: PlayerSlotWidget, global_pos):
    """Builds and executes the esports context menu for a player slot."""
    if slot._player is None:
        return

    menu = QMenu(slot)
    player = slot._player
    is_sp = is_special_player_name(player.name)

    if not is_sp:
        act_rename = QAction("✏️ Renombrar jugador...", slot)
        act_rename.triggered.connect(lambda: prompt_rename_player(slot))
        menu.addAction(act_rename)

    act_props = QAction("⚙️ Ajustar Habilidad / MMR...", slot)
    act_props.triggered.connect(lambda: open_properties_modal(slot))
    menu.addAction(act_props)

    if not is_sp:
        act_color = QAction("🎨 Asignar Color Personalizado...", slot)
        act_color.triggered.connect(lambda: prompt_pick_color(slot))
        menu.addAction(act_color)

        if getattr(player, "custom_color", None):
            act_reset_color = QAction("↺ Restablecer Color", slot)
            act_reset_color.triggered.connect(lambda: reset_custom_color(slot))
            menu.addAction(act_reset_color)

    menu.addSeparator()

    if player.is_fixed:
        act = QAction(f"Desfijar de Equipo {player.fixed_team}", slot)
        act.triggered.connect(lambda: slot.slot_fixed_changed.emit(None))
    else:
        act = QAction(f"Fijar en Equipo {slot.team_num}", slot)
        act.triggered.connect(lambda: slot.slot_fixed_changed.emit(slot.team_num))
    menu.addAction(act)

    menu.addSeparator()

    if slot._show_roles:
        for role in Role:
            act = QAction(f"Rol: {role.value.capitalize()}", slot)
            act.setCheckable(True)
            act.setChecked(player.role == role)
            act.triggered.connect(lambda checked, r=role: slot.slot_role_changed.emit(r))
            menu.addAction(act)
        act_clear = QAction("Quitar rol", slot)
        act_clear.triggered.connect(lambda: slot.slot_role_changed.emit(None))
        menu.addAction(act_clear)
        menu.addSeparator()

    act_bench = QAction("Enviar a Zona de Espera", slot)
    act_bench.triggered.connect(slot.slot_bench.emit)
    menu.addAction(act_bench)

    if not slot._saved:
        act_save = QAction("💾 Guardar jugador", slot)
        act_save.triggered.connect(slot.slot_save.emit)
        menu.addAction(act_save)

    menu.addSeparator()

    act_remove = QAction("Quitar de la partida", slot)
    act_remove.triggered.connect(slot.slot_remove.emit)
    menu.addAction(act_remove)

    menu.exec(global_pos)


def open_properties_modal(slot: PlayerSlotWidget):
    if slot._player is None:
        return
    dialog = PlayerPropertiesDialog(slot._player, slot.window())
    if dialog.exec() == QDialog.DialogCode.Accepted:
        data = dialog.get_data()
        if len(data) == 5:
            gen, tank, dps, sup, auto_on = data
            slot._player.auto_mmr_enabled = auto_on
        else:
            gen, tank, dps, sup = data[:4]
        slot._player.mmr = gen
        slot._player.mmr_tank = tank
        slot._player.mmr_damage = dps
        slot._player.mmr_support = sup
        slot.set_player(slot._player, slot._saved, slot._show_roles, slot._show_mmr)
        slot.slot_mmr_changed.emit(None, gen)


def prompt_rename_player(slot: PlayerSlotWidget):
    if slot._player is None or is_special_player_name(slot._player.name):
        return
    current_name = slot._player.name.replace(" 👑", "").strip()
    new_name, ok = QInputDialog.getText(
        slot.window(),
        "Renombrar jugador",
        "Nuevo nombre para el jugador:",
        text=current_name,
    )
    if ok and new_name.strip():
        formatted = format_player_name(new_name.strip(), True)
        slot.slot_renamed.emit(formatted)


def prompt_pick_color(slot: PlayerSlotWidget):
    if slot._player is None:
        return
    initial = QColor(slot._player.custom_color) if getattr(slot._player, "custom_color", None) else QColor("#61ab02")
    color = QColorDialog.getColor(initial, slot.window(), f"Color para {slot._player.name}")
    if color.isValid():
        slot._player.custom_color = color.name()
        slot._apply_style()
        slot.slot_color_changed.emit(slot._player.name, color.name())


def reset_custom_color(slot: PlayerSlotWidget):
    if slot._player is not None:
        slot._player.custom_color = None
        slot._apply_style()
        slot.slot_color_changed.emit(slot._player.name, None)
