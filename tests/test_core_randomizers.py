"""Fast, non-UI checks for the match randomizers."""

import random

import pytest

from owervach_tmixer.core.heroes import HeroManager
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


def _draft_pool() -> list[Hero]:
    return (
        [Hero(f"Tank {i}", Role.TANK) for i in range(4)]
        + [Hero(f"Damage {i}", Role.DAMAGE) for i in range(6)]
        + [Hero(f"Support {i}", Role.SUPPORT) for i in range(6)]
    )


def _role_of(manager: HeroManager, name: str) -> Role:
    return next(h.role for h in manager.heroes if h.name == name)


def test_generate_draft_respects_size_and_role_caps():
    mgr = HeroManager(_draft_pool())
    t1, t2 = mgr.generate_draft()
    for team in (t1, t2):
        assert len(team) == 5
        counts = {Role.TANK: 0, Role.DAMAGE: 0, Role.SUPPORT: 0}
        for name in team:
            counts[_role_of(mgr, name)] += 1
        assert counts[Role.TANK] <= 1
        assert counts[Role.DAMAGE] <= 2
        assert counts[Role.SUPPORT] <= 2


def test_generate_draft_exclusive_teams_without_mirror():
    mgr = HeroManager(_draft_pool())
    t1, t2 = mgr.generate_draft(allow_mirror=False)
    assert set(t1) & set(t2) == set()
    assert len(t1) == len(t2) == 5


def test_generate_draft_mirror_allows_overlap():
    # Con pool minúsculo y espejo, ambos equipos pueden repetir héroes
    tiny = HeroManager([Hero("T", Role.TANK), Hero("D", Role.DAMAGE), Hero("S", Role.SUPPORT)])
    a, b = tiny.generate_draft(heroes_per_team=3, max_tank=1, max_damage=1, max_support=1)
    assert len(a) == 3 and len(b) == 3
    assert set(a) == set(b)


def test_generate_draft_fills_less_when_pool_is_short():
    mgr = HeroManager([Hero("Solo Tank", Role.TANK)])
    t1, t2 = mgr.generate_draft()
    assert t1 == ["Solo Tank"] and t2 == ["Solo Tank"]


def test_generate_draft_custom_caps():
    mgr = HeroManager(_draft_pool())
    t1, _ = mgr.generate_draft(heroes_per_team=6, max_tank=2, max_damage=3, max_support=1)
    counts = {Role.TANK: 0, Role.DAMAGE: 0, Role.SUPPORT: 0}
    for name in t1:
        counts[_role_of(mgr, name)] += 1
    assert len(t1) == 6
    assert counts[Role.TANK] == 2 and counts[Role.DAMAGE] == 3 and counts[Role.SUPPORT] == 1
