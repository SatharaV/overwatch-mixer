"""Tests for BLOQUE 2: drag & drop relocation rules + integration."""

from collections import Counter

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from owervach_tmixer.core.models import (
    GameMode,
    MatchSettings,
    Role,
    TeamComposition,
)
from owervach_tmixer.core.roster import Roster, RosterError
from owervach_tmixer.ui.styles import theme


def fill(r, n):
    t = 1
    for i in range(n):
        if t == 1 and i >= len(r.team1_slots):
            t = 2
        slot = i if t == 1 else i - len(r.team1_slots)
        r.create_in_slot(t, slot, f"P{i}")
    return [p for p in r.active_players()]


def slot_payload(r, name):
    for team in (1, 2):
        slots = r.team1_slots if team == 1 else r.team2_slots
        for i, p in enumerate(slots):
            if p and p.name == name:
                return {"kind": "slot", "team": team, "idx": i, "name": name}
    raise AssertionError(f"not found: {name}")


def who(r, team):
    return [p.name if p else None for p in (r.team1_slots if team == 1 else r.team2_slots)]


def slot_at(w, team, idx):
    widget = w.match_display.team1_widget if team == 1 else w.match_display.team2_widget
    return widget.slot_widgets[idx]


def test_same_team_drop_swaps_cells():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    fill(r, 10)
    msg = r.relocate(slot_payload(r, "P0"), 1, 1)
    assert who(r, 1) == ["P1", "P0", "P2", "P3", "P4"]
    assert "intercambiados" in msg
    assert who(r, 2) == ["P5", "P6", "P7", "P8", "P9"]


def test_same_team_to_free_cell():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    fill(r, 10)
    r.clear_slot(1, 3)
    r.relocate(slot_payload(r, "P1"), 1, 3)
    assert who(r, 1) == ["P0", None, "P2", "P1", "P4"]


def test_same_slot_is_noop():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    fill(r, 10)
    msg = r.relocate(slot_payload(r, "P0"), 1, 0)
    assert msg == "Sin cambios"
    assert who(r, 1) == ["P0", "P1", "P2", "P3", "P4"]


def test_cross_team_to_free_slot():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    fill(r, 10)
    r.clear_slot(2, 4)
    msg = r.relocate(slot_payload(r, "P0"), 2, 4)
    assert who(r, 1) == [None, "P1", "P2", "P3", "P4"]
    assert who(r, 2) == ["P5", "P6", "P7", "P8", "P0"]
    assert "movido" in msg


def test_out_of_range_target_rejected():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    fill(r, 10)
    with pytest.raises(RosterError, match="inválida"):
        r.relocate(slot_payload(r, "P0"), 2, 5)


def test_cross_team_occupied_rejected_by_default():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    fill(r, 10)
    with pytest.raises(RosterError, match="no está permitido"):
        r.relocate(slot_payload(r, "P0"), 2, 0)


def test_cross_team_occupied_swaps_when_enabled():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    fill(r, 10)
    msg = r.relocate(slot_payload(r, "P0"), 2, 0, cross_team_swap=True)
    assert who(r, 1) == ["P5", "P1", "P2", "P3", "P4"]
    assert who(r, 2) == ["P0", "P6", "P7", "P8", "P9"]
    assert "intercambiados entre equipos" in msg


def test_cross_team_swap_blocked_if_occupant_fixed():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    fill(r, 10)
    r.team2_slots[0].fixed_team = 2
    with pytest.raises(RosterError, match="fijado a Equipo 2"):
        r.relocate(slot_payload(r, "P0"), 2, 0, cross_team_swap=True)


def test_fixed_player_never_crosses_teams():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    fill(r, 10)
    r.team1_slots[0].fixed_team = 1
    with pytest.raises(RosterError, match="fijado a Equipo 1"):
        r.relocate(slot_payload(r, "P0"), 2, 5, cross_team_swap=True)
    r.relocate(slot_payload(r, "P0"), 1, 2)
    assert who(r, 1) == ["P2", "P1", "P0", "P3", "P4"]


def test_full_team_rejects_panel_drop():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    fill(r, 10)
    with pytest.raises(RosterError, match="lleno"):
        r.relocate(slot_payload(r, "P0"), 2, None)


def test_team_to_bench_clears_state():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    fill(r, 10)
    r.team1_slots[0].role = Role.TANK
    r.team1_slots[0].fixed_role = True
    r.team1_slots[0].fixed_team = 1
    p = r.send_to_bench(1, 0)
    assert p is not None and p in r.bench
    assert p.role is None and p.fixed_team is None and p.fixed_role is False
    assert r.team1_slots[0] is None


def test_bench_to_free_slot():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    fill(r, 10)
    r.add_to_bench("Extra")
    msg = r.relocate({"kind": "bench", "name": "Extra"}, 1, 3)
    assert r.team1_slots[3].name == "Extra"
    assert r.find_bench("Extra") is None
    assert "entra" in msg


def test_bench_to_occupied_slot_moves_occupant_to_bench():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    fill(r, 10)
    r.add_to_bench("Extra")
    r.relocate({"kind": "bench", "name": "Extra"}, 1, 0)
    assert r.team1_slots[0].name == "Extra"
    assert [p.name for p in r.bench] == ["P0"]


def test_bench_holds_only_a_name():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    fill(r, 10)
    r.team1_slots[0].role = Role.TANK
    r.team1_slots[0].fixed_role = True
    r.team1_slots[0].fixed_team = 1

    r.send_to_bench(1, 0)
    assert r.bench[0].role is None and r.bench[0].fixed_team is None

    r.add_to_bench("Extra")
    r.relocate({"kind": "bench", "name": "Extra"}, 1, 1)
    assert [p.name for p in r.bench] == ["P0", "P1"]
    assert (p := r.find_bench("P1")) is not None
    assert p.role is None and p.fixed_team is None


def create_all(w, names):
    per_team = w._roster.team_size
    for i, name in enumerate(names):
        team = (i // per_team) + 1
        slot = i % per_team
        w._on_slot_created(team, slot, name)


def payload_for(w, name):
    for team in (1, 2):
        slots = w._roster.team1_slots if team == 1 else w._roster.team2_slots
        for i, p in enumerate(slots):
            if p and p.name == name:
                return {"kind": "slot", "team": team, "idx": i, "name": name}
    raise AssertionError(f"not found: {name}")


def bench_names(w):
    return {p.name for p in w._roster.bench}


def test_drop_cross_team_to_free_cell_and_persists(make_window, app_dir):
    w = make_window()
    create_all(w, [f"P{i}" for i in range(10)])
    w._roster.clear_slot(2, 4)
    w._after_roster_change()

    w._on_player_drop(payload_for(w, "P0"), 2, 4)
    assert w._roster.team2_slots[4].name == "P0"
    assert w._roster.team1_slots[0] is None

    w.close()
    w2 = make_window()
    assert w2._roster.team2_slots[4].name == "P0"
    w2.close()


def test_drop_onto_itself_is_noop(make_window, dialogs):
    w = make_window()
    w._on_slot_created(1, 0, "Ana")
    before = [p.name for p in w._roster.active_players()]
    w._on_player_drop(payload_for(w, "Ana"), 1, 0)
    assert [p.name for p in w._roster.active_players()] == before
    assert not any(kind == "warning" for kind, _, _ in dialogs)


def test_drop_occupied_cross_team_default_rejects(make_window, dialogs):
    w = make_window()
    w.settings_manager.update_dnd_cross_team_swap(False)
    create_all(w, [f"P{i}" for i in range(10)])
    before = [p.name for p in w._roster.active_players()]
    w._on_player_drop(payload_for(w, "P0"), 2, 0)
    assert [p.name for p in w._roster.active_players()] == before
    assert any("no está permitido" in t for _, _, t in dialogs)
    w.close()


def test_drop_occupied_cross_team_swap_when_setting_on(make_window, dialogs):
    w = make_window()
    create_all(w, [f"P{i}" for i in range(10)])
    w.settings_manager.update_dnd_cross_team_swap(True)
    w._on_player_drop(payload_for(w, "P0"), 2, 0)
    assert w._roster.team1_slots[0].name == "P5"
    assert w._roster.team2_slots[0].name == "P0"
    assert not any(kind == "warning" for kind, _, _ in dialogs)
    w.close()


def test_drop_bench_onto_occupied_moves_occupant_to_bench(make_window):
    w = make_window()
    create_all(w, [f"P{i}" for i in range(10)])
    w._roster.add_to_bench("Extra")
    w._after_roster_change()
    w._on_player_drop({"kind": "bench", "name": "Extra"}, 1, 0)
    assert w._roster.team1_slots[0].name == "Extra"
    assert bench_names(w) == {"P0"}
    assert w._roster.find_bench("P0").role is None
    w.close()


def test_bench_persists_only_the_name(make_window, app_dir):
    w = make_window()
    w._on_slot_created(1, 0, "Ana")
    w._on_slot_role_changed(1, 0, Role.TANK)
    w._on_slot_fixed_changed(1, 0, 1)
    w._on_drop_to_bench(payload_for(w, "Ana"))
    w._after_roster_change()

    chip = w.bench_panel.find_chip("Ana")
    assert chip is not None
    assert chip.name == "Ana"

    saved = (app_dir / "players.json").read_text()
    assert '"role": null' in saved or '"role": None' in saved
    w.close()


def test_drop_to_bench_handler(make_window):
    w = make_window()
    w._on_slot_created(1, 0, "Ana")
    w._on_drop_to_bench(payload_for(w, "Ana"))
    assert w._roster.team1_slots[0] is None
    assert bench_names(w) == {"Ana"}
    w.close()


def test_ui_drop_signal_path(make_window):
    w = make_window()
    create_all(w, [f"P{i}" for i in range(10)])
    slot = w.match_display.team1_widget.slot_widgets[0]
    slot.drop_requested.emit(payload_for(w, "P0"), 1)
    assert [p.name for p in w._roster.team1_slots] == ["P1", "P0", "P2", "P3", "P4"]
    w.close()


def test_randomizer_uses_only_active_players(make_window):
    w = make_window()
    create_all(w, [f"P{i}" for i in range(10)])
    w._roster.add_to_bench("Bench1")
    w._roster.add_to_bench("Bench2")
    w._after_roster_change()
    w._generate_match()
    assert w._current_match is not None
    generated = {p.name for p in w._current_match.team1.players + w._current_match.team2.players}
    assert generated == {f"P{i}" for i in range(10)}
    assert bench_names(w) == {"Bench1", "Bench2"}
    w.close()


def test_generate_warns_when_not_enough_active(make_window, dialogs):
    w = make_window()
    # Con lobby completamente vacío debe advertir
    w._roster.clear_teams_and_bench()
    w._generate_match()
    assert w._current_match is None
    assert any(kind == "warning" for kind, _, _ in dialogs)
    w.close()


def test_mode_6v6_5v5_keeps_fixed_and_moves_overflow(make_window):
    w = make_window()
    create_all(w, [f"P{i}" for i in range(10)])
    r = w._roster
    r.team1_slots[0].fixed_team = 1
    r.add_to_bench("E1")
    r.add_to_bench("E2")
    w._after_roster_change()

    w._on_mode_changed(GameMode.SIX_V_SIX)
    assert len(r.active_players()) == 12 and r.bench == []

    w._on_mode_changed(GameMode.FIVE_V_FIVE)
    assert len(r.active_players()) == 10
    assert sorted(p.name for p in r.bench) == ["E1", "E2"]
    assert r.team1_slots[0].name == "P0" and r.team1_slots[0].fixed_team == 1
    w.close()


def test_swap_setting_roundtrip(make_window, app_dir):
    w = make_window()
    w.settings_manager.update_dnd_cross_team_swap(True)
    w.close()
    w2 = make_window()
    assert w2.settings_manager.settings.dnd_cross_team_swap is True
    w2.close()


def test_roles_toggles_exist(make_window):
    w = make_window()
    assert "Roles" in w.roles_toggle.text()
    assert "Auto" in w.randomize_roles_toggle.text() or "Randomizar" in w.randomize_roles_toggle.text()
    assert w.roles_toggle.isChecked() is True
    assert w.randomize_roles_toggle.isChecked() is True
    w.close()


def test_randomize_roles_toggle_controls_reroll_button(make_window):
    w = make_window()
    assert w.match_display.team1_widget.btn_mix_roles.isEnabled() is True
    w.randomize_roles_toggle.setChecked(False)
    assert w.settings_manager.settings.auto_roles is False
    assert w.match_display.team1_widget.btn_mix_roles.isEnabled() is False
    w.randomize_roles_toggle.setChecked(True)
    assert w.match_display.team1_widget.btn_mix_roles.isEnabled() is True
    w.close()


def test_show_roles_off_forces_randomize_off_and_disables(make_window):
    w = make_window()
    w._on_slot_created(1, 0, "Ana")
    w._on_slot_role_changed(1, 0, Role.TANK)
    w.randomize_roles_toggle.setChecked(True)
    w.roles_toggle.setChecked(False)
    assert w.settings_manager.settings.show_roles is False
    assert w.settings_manager.settings.auto_roles is False
    assert w.randomize_roles_toggle.isChecked() is False
    assert w.randomize_roles_toggle.isEnabled() is False
    assert w.match_display.team1_widget.btn_mix_roles.isEnabled() is False
    decor = slot_at(w, 1, 0)._decor.text()
    assert "TANK" not in decor
    assert w._roster.team1_slots[0].fixed_role is True
    w.roles_toggle.setChecked(True)
    assert w.settings_manager.settings.show_roles is True
    assert w.randomize_roles_toggle.isEnabled() is True
    assert "TANK" in slot_at(w, 1, 0)._decor.text()
    w.close()


def test_role_settings_roundtrip(make_window, app_dir):
    w = make_window()
    w.settings_manager.update_auto_roles(False)
    w.settings_manager.update_show_roles(False)
    w.close()
    w2 = make_window()
    s = w2.settings_manager.settings
    assert s.auto_roles is False
    assert s.show_roles is False
    assert w2.randomize_roles_toggle.isChecked() is False
    assert w2.match_display.team1_widget.btn_mix_roles.isEnabled() is False
    w2.close()


def test_mode_toggle_switch(make_window):
    w = make_window()
    sw = w.mode_switch
    assert "5" in sw.label_5.text()
    assert "6" in sw.label_6.text()
    assert sw.mode() == GameMode.FIVE_V_FIVE
    QTest.mouseClick(sw._knob, Qt.LeftButton)
    assert sw.mode() == GameMode.SIX_V_SIX
    assert len(w._roster.team1_slots) == 6
    sw.set_mode(GameMode.FIVE_V_FIVE)
    assert sw.mode() == GameMode.FIVE_V_FIVE
    assert len(w._roster.team1_slots) == 5
    w.close()


def test_role_order_matches_composition():
    s = MatchSettings()
    assert s.role_order() == [Role.TANK, Role.DAMAGE, Role.DAMAGE,
                              Role.SUPPORT, Role.SUPPORT]
    s.game_mode = GameMode.SIX_V_SIX
    assert s.role_order() == [Role.TANK, Role.TANK, Role.DAMAGE, Role.DAMAGE,
                              Role.SUPPORT, Role.SUPPORT]
    s.game_mode = GameMode.FIVE_V_FIVE
    s.composition_5v5 = TeamComposition(tank=2, damage=1, support=2)
    assert s.role_order() == [Role.TANK, Role.TANK, Role.DAMAGE,
                              Role.SUPPORT, Role.SUPPORT]


def test_no_randomize_fixed_role_order_5v5(make_window):
    w = make_window()
    w.settings_manager.update_auto_roles(False)
    create_all(w, [f"P{i}" for i in range(10)])
    expected = ["TANK", "DAMAGE", "DAMAGE", "SUPPORT", "SUPPORT"]
    for team_id in (1, 2):
        widget = w.match_display.team1_widget if team_id == 1 else w.match_display.team2_widget
        for idx, role_word in enumerate(expected):
            assert role_word in widget.slot_widgets[idx]._decor.text()
    assert w._roster.team1_slots[0].role == Role.TANK
    assert w._roster.team1_slots[2].role == Role.DAMAGE
    w.close()


def test_no_randomize_fixed_role_order_6v6(make_window):
    w = make_window()
    w.settings_manager.update_auto_roles(False)
    w._on_mode_changed(GameMode.SIX_V_SIX)
    create_all(w, [f"P{i}" for i in range(12)])
    expected = ["TANK", "TANK", "DAMAGE", "DAMAGE", "SUPPORT", "SUPPORT"]
    widget = w.match_display.team1_widget
    for idx, role_word in enumerate(expected):
        assert role_word in widget.slot_widgets[idx]._decor.text()
    w.close()


def test_pinned_role_survives_fixed_default(make_window):
    w = make_window()
    w.settings_manager.update_auto_roles(False)
    w._on_slot_created(1, 0, "Ana")
    w._on_slot_role_changed(1, 0, Role.SUPPORT)
    w._refresh_roster_ui()
    assert "SUPPORT" in slot_at(w, 1, 0)._decor.text()
    w.close()


def test_toggling_randomize_off_freezes_order(make_window):
    w = make_window()
    create_all(w, [f"P{i}" for i in range(10)])
    w.randomize_roles_toggle.setChecked(False)
    assert [p.role for p in w._roster.team1_slots] == [
        Role.TANK, Role.DAMAGE, Role.DAMAGE, Role.SUPPORT, Role.SUPPORT]
    w.randomize_roles_toggle.setChecked(True)
    w._refresh_roster_ui()
    assert [p.role for p in w._roster.team1_slots] == [
        Role.TANK, Role.DAMAGE, Role.DAMAGE, Role.SUPPORT, Role.SUPPORT]
    w.close()


def test_fixed_default_roles_persist(make_window, app_dir):
    w = make_window()
    w.settings_manager.update_auto_roles(False)
    w._on_slot_created(1, 0, "Ana")
    w.close()
    w2 = make_window()
    assert w2._roster.team1_slots[0].role == Role.TANK
    w2.close()


def test_reroll_roles_works_without_generated_match(make_window):
    w = make_window()
    w.settings_manager.update_auto_roles(True)
    assert w._current_match is None
    create_all(w, [f"P{i}" for i in range(10)])
    w._reroll_roles(1)
    roles = [p.role for p in w._roster.team1_slots]
    assert all(role is not None for role in roles)
    assert Counter(roles) == Counter([Role.TANK, Role.DAMAGE, Role.DAMAGE,
                                      Role.SUPPORT, Role.SUPPORT])
    assert len({r for r in roles}) > 1
    w.close()


def test_reroll_roles_randomizes_slots_0_1(make_window):
    w = make_window()
    w.settings_manager.update_auto_roles(True)
    create_all(w, [f"P{i}" for i in range(10)])
    w._reroll_roles(1)
    first = [p.role for p in w._roster.team1_slots][:2]
    seen = {tuple(first)}
    for _ in range(6):
        w._reroll_roles(1)
        current = [p.role for p in w._roster.team1_slots][:2]
        seen.add(tuple(current))
    assert len(seen) > 1
    w.close()


def test_reroll_roles_is_a_noop_when_randomize_off(make_window):
    w = make_window()
    w.settings_manager.update_auto_roles(False)
    create_all(w, [f"P{i}" for i in range(10)])
    w._reroll_roles(1)
    assert [p.role for p in w._roster.team1_slots] == [
        Role.TANK, Role.DAMAGE, Role.DAMAGE, Role.SUPPORT, Role.SUPPORT]
    w.close()


def test_reroll_roles_respects_pinned_players(make_window):
    w = make_window()
    w.settings_manager.update_auto_roles(True)
    create_all(w, [f"P{i}" for i in range(10)])
    w._on_slot_role_changed(1, 0, Role.SUPPORT)
    pinned = w._roster.team1_slots[0]
    for _ in range(4):
        w._reroll_roles(1)
        slots = w._roster.team1_slots + w._roster.team2_slots
        assert next(p for p in slots if p is not None and p.name == pinned.name).role == Role.SUPPORT
    w.close()


def test_startup_normalizes_show_off_auto_on(make_window, app_dir):
    w = make_window()
    s = w.settings_manager.settings
    s.auto_roles = True
    s.show_roles = False
    w.settings_manager.save()
    w.close()
    w2 = make_window()
    assert w2.settings_manager.settings.auto_roles is False
    assert w2.randomize_roles_toggle.isChecked() is False
    assert w2.randomize_roles_toggle.isEnabled() is False
    assert w2.match_display.team1_widget.btn_mix_roles.isEnabled() is False
    w2.close()


def test_estado_b_6v6_after_randomized(make_window):
    w = make_window()
    w._on_mode_changed(GameMode.SIX_V_SIX)
    w.settings_manager.update_auto_roles(True)
    create_all(w, [f"P{i}" for i in range(12)])
    w._reroll_roles(1)
    assert [p.role for p in w._roster.team1_slots] != [
        Role.TANK, Role.TANK, Role.DAMAGE, Role.DAMAGE, Role.SUPPORT, Role.SUPPORT]
    w.randomize_roles_toggle.setChecked(False)
    assert [p.role for p in w._roster.team1_slots] == [
        Role.TANK, Role.TANK, Role.DAMAGE, Role.DAMAGE, Role.SUPPORT, Role.SUPPORT]
    w.close()


def test_mode_switch_6v6_to_5v5_reroll_no_error(make_window, monkeypatch):
    warnings = []
    monkeypatch.setattr(
        "PySide6.QtWidgets.QMessageBox.warning",
        staticmethod(lambda *a, **k: warnings.append(a[2] if len(a) > 2 else a)))
    w = make_window()
    w._on_mode_changed(GameMode.SIX_V_SIX)
    w.settings_manager.update_auto_roles(True)
    create_all(w, [f"P{i}" for i in range(12)])
    w._reroll_roles(1)
    w._reroll_roles(2)
    w._on_mode_changed(GameMode.FIVE_V_FIVE)
    w._reroll_roles(1)
    w._reroll_roles(2)
    assert warnings == []
    for team in (w._roster.team1_slots, w._roster.team2_slots):
        roles = [p.role for p in team if p is not None]
        assert Counter(roles) == Counter([Role.TANK, Role.DAMAGE, Role.DAMAGE,
                                          Role.SUPPORT, Role.SUPPORT])
    w.close()


def test_mode_switch_releases_excess_pins_only(make_window, app_dir, monkeypatch):
    warnings = []
    monkeypatch.setattr(
        "PySide6.QtWidgets.QMessageBox.warning",
        staticmethod(lambda *a, **k: warnings.append(a[2] if len(a) > 2 else a)))
    w = make_window()
    w._on_mode_changed(GameMode.SIX_V_SIX)
    w.settings_manager.update_auto_roles(True)
    create_all(w, [f"P{i}" for i in range(12)])
    _on_slot_role_changed = w._on_slot_role_changed
    _on_slot_role_changed(1, 0, Role.TANK)
    _on_slot_role_changed(1, 1, Role.TANK)
    _on_slot_role_changed(1, 2, Role.DAMAGE)
    _on_slot_role_changed(1, 3, Role.DAMAGE)
    pinned = {p.name for p in w._roster.team1_slots if p.fixed_role}
    assert len(pinned) == 4
    w._on_mode_changed(GameMode.FIVE_V_FIVE)
    keepers = {p.name for p in w._roster.team1_slots
               if p is not None and p.fixed_role and p.role == Role.TANK}
    free_tanks = [p.name for p in w._roster.team1_slots
                  if p is not None and not p.fixed_role and p.role == Role.TANK]
    assert len(keepers) == 1
    assert len(free_tanks) == 1
    assert len({p.name for p in w._roster.team1_slots
                if p.fixed_role and p.role == Role.DAMAGE}) == 2
    w._reroll_roles(1)
    assert warnings == []
    w.close()
    w2 = make_window()
    assert any(p is not None and p.fixed_role and p.role == Role.TANK
               for p in w2._roster.team1_slots)
    w2.close()


def test_mode_switch_5v5_to_6v6_updates_composition(make_window, monkeypatch):
    warnings = []
    monkeypatch.setattr(
        "PySide6.QtWidgets.QMessageBox.warning",
        staticmethod(lambda *a, **k: warnings.append(a[2] if len(a) > 2 else a)))
    w = make_window()
    w.settings_manager.update_auto_roles(True)
    create_all(w, [f"P{i}" for i in range(10)])
    w._reroll_roles(1)
    w._on_mode_changed(GameMode.SIX_V_SIX)
    assert len(w._roster.team1_slots) == 6
    w._on_slot_created(1, 5, "Pa")
    w._on_slot_created(2, 5, "Pb")
    w._reroll_roles(1)
    w._reroll_roles(2)
    assert warnings == []
    for team in (w._roster.team1_slots, w._roster.team2_slots):
        roles = [p.role for p in team if p is not None]
        assert Counter(roles) == Counter([Role.TANK, Role.TANK, Role.DAMAGE,
                                          Role.DAMAGE, Role.SUPPORT, Role.SUPPORT])
    w.close()


def test_mix_roles_button_in_team_header_exists(make_window):
    w = make_window()
    for widget in (w.match_display.team1_widget, w.match_display.team2_widget):
        assert "Roles" in widget.btn_mix_roles.text() or "Mezclar" in widget.btn_mix_roles.text()
        assert widget.btn_mix_roles.isEnabled() is True
    w.close()


def test_mix_roles_per_team_independence(make_window):
    w = make_window()
    create_all(w, [f"P{i}" for i in range(10)])
    w._reroll_roles(1)
    w._reroll_roles(2)
    team2_before = [p.role for p in w._roster.team2_slots]
    for _ in range(6):
        w._reroll_roles(1)
        assert [p.role for p in w._roster.team2_slots] == team2_before
    team1_before = [p.role for p in w._roster.team1_slots]
    for _ in range(6):
        w._reroll_roles(2)
        assert [p.role for p in w._roster.team1_slots] == team1_before
    w.close()


def test_settings_dialog_uses_wrapping_tabs(make_window):
    from owervach_tmixer.main import SettingsDialog

    w = make_window()
    dlg = SettingsDialog(w, w.settings_manager, w.shuffle_history)
    assert dlg._settings_stack.count() == 8
    assert len(dlg._tab_group.buttons()) == 8
    assert dlg._settings_stack.currentIndex() == 0
    assert hasattr(dlg, "chk_auto_roles")
    dlg.close()
    w.close()


def test_accent_default_is_green():
    assert MatchSettings().accent_color == "#61ab02"


def test_accent_roundtrip():
    s = MatchSettings()
    s.accent_color = "#00B4FF"
    assert MatchSettings.from_dict(s.to_dict()).accent_color == "#00B4FF"
    assert MatchSettings.from_dict({}).accent_color == "#61ab02"


def test_accent_flows_into_stylesheet_and_mode_switch(make_window):
    w = make_window()
    theme.set_accent("#00B4FF")
    try:
        assert "#00b4ff" in theme.build_stylesheet()
        w._apply_theme()
        assert "#00b4ff" in w.styleSheet()
        w.mode_switch.set_mode(GameMode.FIVE_V_FIVE)
        w.mode_switch.apply_theme()
        assert "#00b4ff" in w.mode_switch.label_5.styleSheet()
    finally:
        theme.set_accent("#61ab02")
    w.close()


def test_appearance_section_saves_and_rethenes(make_window):
    from owervach_tmixer.main import SettingsDialog

    w = make_window()
    dlg = SettingsDialog(w, w.settings_manager, w.shuffle_history)
    assert hasattr(dlg, "btn_accent_swatch")
    assert dlg.edit_hex.text() == "#61AB02"
    assert dlg.edit_rgb.text() == "97, 171, 2"
    for btn, hex_color in dlg._accent_preset_hexes.items():
        if hex_color == "#00B4FF":
            btn.setChecked(True)
            break
    else:
        raise AssertionError("preset azul no encontrado")
    assert dlg._accent_hex == "#00b4ff"
    dlg._save_settings()
    assert w.settings_manager.settings.accent_color == "#00b4ff"
    assert theme.accent() == "#00b4ff"
    assert "#00b4ff" in w.styleSheet()
    w.mode_switch.apply_theme()
    assert "#00b4ff" in w.mode_switch.label_5.styleSheet()
    dlg.close()
    theme.set_accent("#61ab02")
    w.close()
