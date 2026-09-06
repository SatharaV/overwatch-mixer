"""Tests for canonical player uniqueness and roster sanitization."""

import pytest
from owervach_tmixer.core.models import GameMode, Player
from owervach_tmixer.core.roster import Roster, RosterError


def test_roster_sanitize_removes_cross_duplicates():
    r = Roster(
        game_mode=GameMode.FIVE_V_FIVE,
        team1_slots=[Player("Dylan"), Player("Damian"), None, None, None],
        team2_slots=[Player("Dylan"), Player("Caro"), None, None, None],
        bench=[Player("Damian"), Player("Rocker"), Player("Rocker")],
        saved=[Player("Dylan"), Player("Dylan"), Player("Sathara")],
    )
    assert len(r.active_players()) == 3
    assert [p.name for p in r.team1_slots if p] == ["Dylan", "Damian"]
    assert [p.name for p in r.team2_slots if p] == ["Caro"]
    assert [p.name for p in r.bench] == ["Rocker"]
    assert [p.name for p in r.saved] == ["Dylan", "Sathara"]


def test_send_to_bench_deduplicates():
    r = Roster(
        game_mode=GameMode.FIVE_V_FIVE,
        team1_slots=[Player("Nanita"), None, None, None, None],
        team2_slots=[None] * 5,
        bench=[Player("Nanita")],
    )
    r.send_to_bench(1, 0)
    assert len(r.bench) == 1
    assert r.bench[0].name == "Nanita"
    assert r.team1_slots[0] is None


def test_fill_from_bench_does_not_wipe_bench():
    r = Roster(
        game_mode=GameMode.FIVE_V_FIVE,
        team1_slots=[None] * 5,
        team2_slots=[None] * 5,
        bench=[Player("P1"), Player("P2"), Player("P3")],
    )
    r.fill_from_bench()
    assert len(r.active_players()) == 3
    assert len(r.bench) == 0


def test_rotate_bench_and_teams_no_duplicate_explosion():
    r = Roster(
        game_mode=GameMode.FIVE_V_FIVE,
        team1_slots=[Player("P1"), Player("P2"), Player("P3"), Player("P4"), Player("P5")],
        team2_slots=[Player("P6"), Player("P7"), Player("P8"), Player("P9"), Player("P10")],
        bench=[Player("B1"), Player("B2"), Player("B3")],
    )
    for p in r.active_players():
        p.streak_played = 3

    p_in, p_out = r.rotate_bench_and_teams(batch_size=2, min_shield=2)
    assert p_in == 2
    assert p_out == 2
    
    active_names = [p.name for p in r.active_players()]
    bench_names = [p.name for p in r.bench]

    assert len(active_names) == 10
    assert len(set(active_names)) == 10
    assert len(bench_names) == 3
    assert len(set(bench_names)) == 3
    assert set(active_names).isdisjoint(set(bench_names))
