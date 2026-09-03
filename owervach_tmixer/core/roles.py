"""Role assignment logic preserving full player metadata, custom colors, and MMR."""

from __future__ import annotations

import random
from .models import Player, Role, Team, TeamComposition


def _clone_player_with_role(player: Player, new_role: Role | None, fixed_role: bool) -> Player:
    """Create a copy of a player preserving their color, multi-role MMR, title and identity."""
    return Player(
        name=player.name,
        role=new_role,
        fixed_team=player.fixed_team,
        fixed_role=fixed_role,
        mmr=getattr(player, "mmr", 5),
        mmr_tank=getattr(player, "mmr_tank", None),
        mmr_damage=getattr(player, "mmr_damage", None),
        mmr_support=getattr(player, "mmr_support", None),
        custom_title=getattr(player, "custom_title", ""),
        custom_color=getattr(player, "custom_color", None),
    )


def assign_roles(
    players: list[Player],
    composition: TeamComposition,
    fixed_roles: dict[str, Role] | None = None,
    rng: random.Random | None = None
) -> list[Player]:
    """
    Assign roles to players according to team composition.
    Respects fixed_roles and preserves all metadata (color, MMR, titles).
    """
    if rng is None:
        rng = random.Random()

    if fixed_roles is None:
        fixed_roles = {}

    fixed_players = [p for p in players if p.name in fixed_roles]
    free_players = [p for p in players if p.name not in fixed_roles]

    role_counts = {
        Role.TANK: composition.tank,
        Role.DAMAGE: composition.damage,
        Role.SUPPORT: composition.support,
    }

    for p in fixed_players:
        role = fixed_roles[p.name]
        role_counts[role] -= 1

    if any(count < 0 for count in role_counts.values()):
        raise ValueError("Fixed roles exceed composition limits")

    role_pool: list[Role] = []
    for role, count in role_counts.items():
        role_pool.extend([role] * count)

    if len(role_pool) != len(free_players):
        raise ValueError("Role pool size mismatch")

    rng.shuffle(role_pool)

    result = []
    for player in players:
        if player.name in fixed_roles:
            result.append(_clone_player_with_role(player, fixed_roles[player.name], True))
        else:
            assigned_role = role_pool.pop()
            result.append(_clone_player_with_role(player, assigned_role, False))

    return result


def assign_roles_to_teams(
    team1: Team,
    team2: Team,
    composition: TeamComposition,
    fixed_roles: dict[str, Role] | None = None,
    rng: random.Random | None = None
) -> tuple[Team, Team]:
    """Assign roles to both teams independently."""
    t1_players = assign_roles(team1.players, composition, fixed_roles, rng)
    t2_players = assign_roles(team2.players, composition, fixed_roles, rng)

    return Team(name=team1.name, players=t1_players), Team(name=team2.name, players=t2_players)


def clear_roles(players: list[Player]) -> list[Player]:
    """Remove role assignments while strictly preserving player color, MMR and identity."""
    return [
        _clone_player_with_role(p, None, False)
        for p in players
    ]
