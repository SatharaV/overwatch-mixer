"""Integration tests for BLOQUE 1 (roster-based match tab)."""

import json

from owervach_tmixer.core.models import GameMode, Match, Player, Role, Team


def slot_at(w, team_num, idx):
    widget = w.match_display.team1_widget if team_num == 1 else w.match_display.team2_widget
    return widget.slot_widgets[idx]


def create_all(w, names, per_team=5):
    for i, name in enumerate(names):
        team = (i // per_team) + 1
        slot = i % per_team
        w._on_slot_created(team, slot, name)


def test_no_jugadores_tab(make_window):
    w = make_window()
    tabs = [w.tabs.tabText(i) for i in range(w.tabs.count())]
    assert "Jugadores" not in tabs
    assert [t for t in tabs if t != "Tier Maker"] == ["Partida", "Mapas", "Héroes / Baneos", "Historial"]
    assert len(w._roster.team1_slots) == 5


def test_inline_create_rename_cancel(make_window):
    w = make_window()
    slot = slot_at(w, 1, 0)
    slot.setText("Ana")
    slot.editingFinished.emit()
    assert [p.name for p in w._roster.active_players()] == ["Ana"]
    assert slot._player.name == "Ana"

    # rename via double-click edit flow
    slot._begin_edit()
    slot.setText("Ana X")
    slot.editingFinished.emit()
    assert w._roster.player_at(1, 0).name == "Ana X"

    # Esc cancels and restores display
    slot._begin_edit()
    slot.setText("Nombre Raro")
    slot._cancel_edit()
    assert slot._player.name == "Ana X"
    assert "Ana X" in slot.text()


def test_duplicate_create_blocked(make_window, dialogs):
    w = make_window()
    w._on_slot_created(1, 0, "Ana")
    w._on_slot_created(1, 1, "aNa")
    assert len(w._roster.active_players()) == 1
    assert any(kind == "warning" for kind, _, _ in dialogs)


def test_fixed_role_bench_saved_flow(make_window):
    w = make_window()
    r = w._roster
    w._on_slot_created(1, 0, "Ana")
    w._on_slot_fixed_changed(1, 0, 1)
    assert r.team1_slots[0].is_fixed
    w._on_slot_role_changed(1, 0, Role.TANK)
    assert r.team1_slots[0].role == Role.TANK

    w._on_slot_save(1, 0)
    assert "Ana" in {p.name for p in r.saved}

    w._on_slot_bench(1, 0)
    assert r.team1_slots[0] is None
    assert "Ana" in {p.name for p in r.bench}

    w._on_bench_add_to_team("Ana", 1)
    player = r.team1_slots[0]
    assert player is not None and player.name == "Ana"

    w._on_bench_add_to_team("Ana", 2)
    assert len(r.active_players()) == 1

    w._on_slot_unsave(1, 0)
    assert "Ana" not in {p.name for p in r.saved}


def test_save_player_drops_provisional_role(make_window):
    w = make_window()
    r = w._roster
    w._on_slot_created(1, 0, "Dovah")
    player = r.player_at(1, 0)
    w._on_slot_save(1, 0)

    saved = next(p for p in r.saved if p.name == "Dovah")
    assert saved.role is None
    assert saved.fixed_role is False

    player.role = Role.SUPPORT
    player.fixed_role = False
    w._on_slot_save(1, 0)
    saved = next(p for p in r.saved if p.name == "Dovah")
    assert saved.role is None

    w._on_slot_created(1, 4, "Ana")
    w._on_slot_role_changed(1, 4, Role.TANK)
    w._on_slot_save(1, 4)
    assert w._roster.player_at(1, 4).fixed_role is True
    pinned = next(p for p in r.saved if p.name == "Ana")
    assert pinned.role == Role.TANK
    w.close()


def test_persistence_across_restart(make_window, app_dir):
    w1 = make_window()
    for t in (1, 2):
        for i in range(5):
            w1._on_slot_created(t, i, f"P{i if t == 1 else i + 5}")
    w1._on_slot_bench(1, 4)
    w1.saved_panel.bulk_saved.emit(["P5", "Extra"])
    w1.close()

    w2 = make_window()
    r = w2._roster
    active = {p.name for p in r.active_players()}
    assert active == {f"P{i}" for i in range(10)} - {"P4"}
    assert {p.name for p in r.bench} == {"P4"}
    assert {p.name for p in r.saved} == {"P5", "Extra"}

    with open(app_dir / "players.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["version"] == 2
    w2.close()


def test_generate_match_fills_slots_and_persists(make_window):
    w = make_window()
    create_all(w, [f"P{i}" for i in range(10)])
    w._generate_match()
    assert w._current_match is not None
    m = w._current_match
    assert len(m.team1.players) == 5 and len(m.team2.players) == 5

    r = w._roster
    assert len(r.active_players()) == 10
    t1_names = {p.name for p in r.team1_slots if p}
    t2_names = {p.name for p in r.team2_slots if p}
    assert t1_names == {p.name for p in m.team1.players}
    assert t2_names == {p.name for p in m.team2.players}
    w.close()


def test_mode_switch_5v6(make_window):
    w = make_window()
    create_all(w, [f"P{i}" for i in range(10)])
    r = w._roster
    r.add_to_bench("Extra")
    w._after_roster_change()

    w._on_mode_changed(GameMode.SIX_V_SIX)
    assert len(r.team1_slots) == 6 and len(r.team2_slots) == 6
    assert len(r.active_players()) == 11
    assert r.bench == []

    w._on_mode_changed(GameMode.FIVE_V_FIVE)
    assert len(r.team1_slots) == 5 and len(r.team2_slots) == 5
    assert len(r.active_players()) == 10
    assert len(r.bench) == 1
    w.close()


def test_new_match_clears_teams_keeps_saved(make_window, dialogs):
    w = make_window()
    w._on_slot_created(1, 0, "Ana")
    w.saved_panel.bulk_saved.emit(["Ana", "Keep"])
    w._new_match()
    r = w._roster
    assert r.active_players() == [] and r.bench == []
    assert {p.name for p in r.saved} == {"Ana", "Keep"}
    assert w._current_match is None
    w.close()


def test_load_match_from_history_adopts_teams(make_window):
    w = make_window()
    match = Match(
        team1=Team(name="Alpha", players=[Player(name="A1"), Player(name="A2"), Player(name="A3"),
                                          Player(name="A4"), Player(name="A5")]),
        team2=Team(name="Beta", players=[Player(name="B1"), Player(name="B2"), Player(name="B3"),
                                         Player(name="B4"), Player(name="B5")]),
    )
    w._load_match_from_history(match)
    r = w._roster
    active = {p.name for p in r.active_players()}
    assert active == {f"{t}{i}" for t in ("A", "B") for i in range(1, 6)}
    assert w._current_match is match
    w.close()


def test_legacy_migration_to_saved(make_window, app_dir):
    (app_dir / "players.json").write_text(
        json.dumps([
            {"name": "Alpha", "role": None, "fixed_team": None},
            {"name": "Beta", "role": "damage", "fixed_team": 1},
            "Gamma",
        ]),
        encoding="utf-8",
    )
    w = make_window()
    r = w._roster
    assert sorted(p.name for p in r.active_players()) == ["Alpha", "Beta", "Gamma"]
    assert sorted(p.name for p in r.saved) == ["Alpha", "Beta", "Gamma"]
    w.close()


def test_repeated_reshuffle_never_exceeds_composition(make_window, dialogs):
    w = make_window()
    create_all(w, [f"P{i}" for i in range(10)])
    w._generate_match()
    assert w._fixed_roles == {}

    for _ in range(8):
        w._reshuffle_teams()

    assert w._current_match is not None
    assert not any(kind == "warning" for kind, _, _ in dialogs)
    for team in (w._current_match.team1, w._current_match.team2):
        roles = [p.role for p in team.players]
        assert roles.count(Role.TANK) == 1
        assert roles.count(Role.DAMAGE) == 2
        assert roles.count(Role.SUPPORT) == 2
    w.close()


def test_user_pinned_role_survives_reshuffle(make_window, dialogs):
    w = make_window()
    create_all(w, [f"P{i}" for i in range(10)])
    w._generate_match()
    target = w._roster.team1_slots[0]
    w._on_slot_role_changed(1, 0, Role.TANK)
    assert target.fixed_role is True
    assert w._fixed_roles == {target.name: Role.TANK}

    for _ in range(5):
        w._reshuffle_teams()

    assert not any(kind == "warning" for kind, _, _ in dialogs)
    pinned = next(p for p in w._roster.active_players() if p.name == target.name)
    assert pinned.role == Role.TANK
    assert pinned.fixed_role is True
    w.close()


def test_slot_indicators_are_decorative(make_window):
    w = make_window()
    w._on_slot_created(1, 0, "Ana")
    slot = slot_at(w, 1, 0)
    w._on_slot_save(1, 0)
    w._on_slot_fixed_changed(1, 0, 1)
    w._on_slot_role_changed(1, 0, Role.TANK)
    w._refresh_roster_ui()

    assert slot.text() == "Ana"
    decor = slot._decor.text()
    assert "⭐" in decor and "🔒" in decor and "TANK" in decor

    slot._begin_edit()
    assert slot.text() == "Ana"
    assert slot._decor.text() == decor
    slot._cancel_edit()
    assert slot.text() == "Ana"
    w.close()


def test_polluted_names_are_sanitized(make_window, app_dir):
    (app_dir / "players.json").write_text(
        json.dumps({
            "version": 2,
            "mode": "5v5",
            "team1": [
                {"name": "Palomita ⭐ 🔒 🔒 🛡️TANK",
                 "role": "tank", "fixed_team": 1, "fixed_role": True},
                {"name": "Gandy ⭐ ⚔️DAMAGE ⚔️DAMAGE ❤️SUPPORT ❤️SUPPORT",
                 "role": "damage", "fixed_team": None, "fixed_role": False},
            ] + [None] * 3,
            "team2": [None] * 5,
            "bench": [],
            "saved": [],
        }),
        encoding="utf-8",
    )
    w = make_window()
    names = [p.name for p in w._roster.active_players() if p]
    assert "Palomita" in names
    assert "Gandy" in names
    assert Player("Tank Girl").name == "Tank Girl"
    w.close()
