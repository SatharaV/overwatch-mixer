"""Unit tests for the Roster model (no Qt needed)."""

import pytest

from owervach_tmixer.core.models import GameMode, Player, Role
from owervach_tmixer.core.roster import Roster, RosterError


def fill_roster(roster, n, suffix=""):
    t = 1
    for i in range(n):
        if t == 1 and i >= len(roster.team1_slots):
            t = 2
        slot = i if t == 1 else i - len(roster.team1_slots)
        roster.create_in_slot(t, slot, f"P{i}{suffix}")


def test_empty_5v5():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    assert len(r.team1_slots) == 5 and len(r.team2_slots) == 5
    assert r.active_players() == []
    assert r.bench == [] and r.saved == []


def test_create_and_duplicate():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    r.create_in_slot(1, 0, "Ana")
    assert r.player_at(1, 0).name == "Ana"
    with pytest.raises(RosterError):  # case-insensitive duplicate
        r.create_in_slot(1, 1, "aNA")
    assert len(r.active_players()) == 1


def test_bench_roundtrip():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    r.create_in_slot(1, 0, "Ana")
    p = r.send_to_bench(1, 0)
    assert p is not None and r.team1_slots[0] is None
    assert [x.name for x in r.bench] == ["Ana"]
    r.add_from_bench_to_team(p, 1)
    assert r.team1_slots[0] is p and r.bench == []
    with pytest.raises(RosterError):
        r.add_pending_to_team("Ana", team_num=1)  # already playing (via slot)


def test_saved_does_not_block_playing_same_name():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    r.create_in_slot(1, 0, "Ana")
    r.save_player(r.player_at(1, 0))
    assert r.name_taken("Ana") is True  # active -> correctly blocked
    assert "Ana" in {p.name for p in r.saved}
    # a player only present in saved is NOT "playing" -> can be added
    r.save_name("Bob")
    assert not r.name_taken("Bob")
    assert "Bob" in [x.name for x in r.saved]


def test_add_saved_player_to_match():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    r.save_name("Fede")
    r.add_pending_to_team("Fede", team_num=2)
    assert r.team2_slots[0].name == "Fede"
    assert "Fede" in [x.name for x in r.saved]  # copy stays saved


def test_mode_change_5v6_normalizes_and_fills():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    fill_roster(r, 10)          # 10 active
    r.add_to_bench("P10")
    assert len(r.active_players()) == 10 and len(r.bench) == 1

    r.on_game_mode_change(GameMode.SIX_V_SIX)  # capacity 12: bench absorbed
    assert len(r.team1_slots) == 6 and len(r.team2_slots) == 6
    assert len(r.active_players()) == 11
    assert r.bench == []
    assert any(p.name == "P10" for p in r.active_players())

    r.on_game_mode_change(GameMode.FIVE_V_FIVE)  # capacity 10: overflow to bench
    assert len(r.team1_slots) == 5 and len(r.team2_slots) == 5
    assert len(r.active_players()) == 10
    assert len(r.bench) == 1


def test_clear_keeps_saved():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    r.create_in_slot(1, 0, "Ana")
    r.send_to_bench(1, 0)
    r.save_name("Kept")
    r.clear_teams_and_bench()
    assert r.active_players() == [] and r.bench == []
    assert [x.name for x in r.saved] == ["Kept"]


def test_roles_and_fixed_roundtrip_via_serialization():
    r = Roster.empty(GameMode.FIVE_V_FIVE)
    r.create_in_slot(1, 0, "Ana")
    p = r.player_at(1, 0)
    p.role = Role.TANK
    p.fixed_team = 1
    data = r.to_dict()
    assert data["version"] == Roster.VERSION
    r2 = Roster.from_dict(data, GameMode.FIVE_V_FIVE)
    p2 = r2.player_at(1, 0)
    assert p2.role == Role.TANK and p2.fixed_team == 1


def test_from_legacy_snapshots_to_saved():
    r = Roster.from_legacy(
        [Player(name="A"), Player(name="A"), Player(name="B")], GameMode.FIVE_V_FIVE
    )
    assert sorted(p.name for p in r.active_players()) == ["A", "B"]
    assert sorted(p.name for p in r.saved) == ["A", "B"]  # dedup + snapshots
