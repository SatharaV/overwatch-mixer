"""Fast, non-UI checks for the match randomizers."""

import random

import pytest

from owervach_tmixer.core.maps import MapPool
from owervach_tmixer.core.models import BanManager, GameMode, Hero, Map, Player, Role
from owervach_tmixer.core.shuffler import simple_shuffle


def _players(count: int) -> list[Player]:
    return [Player(f"Player {number}") for number in range(count)]


def test_shuffle_preserves_fixed_teams():
    players = _players(GameMode.FIVE_V_FIVE.total_players)
    team1, team2 = simple_shuffle(
        players,
        GameMode.FIVE_V_FIVE,
        {"Player 0": 1, "Player 9": 2},
        random.Random(7),
    )
    assert "Player 0" in {player.name for player in team1}
    assert "Player 9" in {player.name for player in team2}
    assert len(team1) == len(team2) == 5


def test_shuffle_rejects_an_incomplete_lobby():
    with pytest.raises(ValueError, match="Expected 10 players"):
        simple_shuffle(_players(9), GameMode.FIVE_V_FIVE, {}, random.Random(1))


def test_map_history_resizes_when_avoid_recent_changes():
    maps = [Map("A", "Control"), Map("B", "Control"), Map("C", "Control")]
    pool = MapPool(maps, avoid_recent=2)
    pool.pick_specific("A")
    pool.pick_specific("B")
    assert pool.get_recent() == ["B", "A"]

    pool.avoid_recent = 1
    assert pool.get_recent() == ["B"]
    pool.avoid_recent = 0
    assert pool.get_recent() == []


def test_bans_respect_global_and_role_limits():
    heroes = [
        Hero("Tank 1", Role.TANK), Hero("Tank 2", Role.TANK), Hero("Tank 3", Role.TANK),
        Hero("Damage 1", Role.DAMAGE), Hero("Damage 2", Role.DAMAGE),
        Hero("Support 1", Role.SUPPORT), Hero("Support 2", Role.SUPPORT),
    ]
    bans = BanManager(heroes=heroes, max_bans=5, max_bans_per_role=2)
    assert bans.toggle_ban("Tank 1") is True
    assert bans.toggle_ban("Tank 2") is True
    assert bans.toggle_ban("Tank 3") is False
    assert "Máximo 2 baneos de tank." == bans.ban_error("Tank 3")
    bans.randomize_bans()
    assert len(bans.banned) == 5
    assert all(bans.banned_in_role(role) <= 2 for role in Role)
