"""NASA-Grade Team shuffling and Matchmaking algorithms with Role-MMR Mirror Balancing."""

from __future__ import annotations

import copy
import random
from itertools import combinations
from typing import Dict, List, Optional, Set, Tuple

from .models import GameMode, Match, Player, Role, ShuffleMode, Team, TeamComposition
from .shuffle_history import ShuffleHistoryEntry


def pair_key(p1: Player, p2: Player) -> Tuple[str, str]:
    return tuple(sorted([p1.name, p2.name]))


def get_team_pairs(team: Team) -> Set[Tuple[str, str]]:
    pairs = set()
    for p1, p2 in combinations(team.players, 2):
        pairs.add(pair_key(p1, p2))
    return pairs


def calculate_pair_similarity(
    team1: Team,
    team2: Team,
    history: List[Match | ShuffleHistoryEntry]
) -> float:
    if not history:
        return 0.0

    current_pairs = get_team_pairs(team1) | get_team_pairs(team2)
    if not current_pairs:
        return 0.0

    max_similarity = 0.0
    for entry in history:
        if hasattr(entry, 'get_similarity_pairs'):
            hist_pairs = entry.get_similarity_pairs()
        else:
            hist_pairs = get_team_pairs(entry.team1) | get_team_pairs(entry.team2)
        if not hist_pairs:
            continue
        intersection = current_pairs & hist_pairs
        similarity = len(intersection) / len(current_pairs)
        max_similarity = max(max_similarity, similarity)

    return max_similarity


def evaluate_matchup_loss(
    t1_players: List[Player],
    t2_players: List[Player],
    history: List[Match | ShuffleHistoryEntry]
) -> float:
    """
    NASA Multi-Objective Matchmaking Loss Function.
    Evaluates:
    1. Overall team MMR delta
    2. Role-by-role Mirror Gap (Tank delta, DPS delta, Support delta)
    3. Similarity penalty against recent matches
    """
    # 1. Total Team MMR (adjusted by assigned role)
    score_t1 = sum(p.get_mmr_for_role(p.role) for p in t1_players)
    score_t2 = sum(p.get_mmr_for_role(p.role) for p in t2_players)
    total_delta = abs(score_t1 - score_t2)

    # 2. Mirror Role Gaps
    t1_tanks = [p.get_mmr_for_role(Role.TANK) for p in t1_players if p.role == Role.TANK]
    t2_tanks = [p.get_mmr_for_role(Role.TANK) for p in t2_players if p.role == Role.TANK]
    tank_gap = abs((sum(t1_tanks) / len(t1_tanks)) - (sum(t2_tanks) / len(t2_tanks))) if (t1_tanks and t2_tanks) else 0.0

    t1_dps = [p.get_mmr_for_role(Role.DAMAGE) for p in t1_players if p.role == Role.DAMAGE]
    t2_dps = [p.get_mmr_for_role(Role.DAMAGE) for p in t2_players if p.role == Role.DAMAGE]
    dps_gap = abs((sum(t1_dps) / len(t1_dps)) - (sum(t2_dps) / len(t2_dps))) if (t1_dps and t2_dps) else 0.0

    t1_sup = [p.get_mmr_for_role(Role.SUPPORT) for p in t1_players if p.role == Role.SUPPORT]
    t2_sup = [p.get_mmr_for_role(Role.SUPPORT) for p in t2_players if p.role == Role.SUPPORT]
    sup_gap = abs((sum(t1_sup) / len(t1_sup)) - (sum(t2_sup) / len(t2_sup))) if (t1_sup and t2_sup) else 0.0

    # 3. History similarity
    similarity = calculate_pair_similarity(Team(name="", players=t1_players), Team(name="", players=t2_players), history)

    # Weighted Quadratic Loss
    loss = (
        (total_delta ** 2) * 2.0 +
        (tank_gap ** 2) * 3.5 +   # Tank matchup has highest impact
        (dps_gap ** 2) * 2.0 +
        (sup_gap ** 2) * 2.0 +
        (similarity * 15.0)
    )
    return loss


def generate_candidate_with_roles(
    players: List[Player],
    mode: GameMode,
    composition: TeamComposition,
    fixed: Dict[str, int],
    fixed_roles: Optional[Dict[str, Role]],
    rng: random.Random,
    allow_partial: bool = False,
) -> Tuple[List[Player], List[Player]]:
    """Generates a valid assignment of players to teams and roles respecting all locks."""
    team_size = mode.players_per_team
    
    # 1. Distribute players to Team 1 and Team 2
    fixed_t1 = [copy.copy(p) for p in players if fixed.get(p.name) == 1]
    fixed_t2 = [copy.copy(p) for p in players if fixed.get(p.name) == 2]
    free_p = [copy.copy(p) for p in players if p.name not in fixed]
    rng.shuffle(free_p)

    if allow_partial and len(players) < mode.total_players:
        half = len(players) // 2
        extra = rng.randint(0, 1) if (len(players) % 2) else 0
        target_t1 = half + extra
        target_t2 = len(players) - target_t1
        if len(fixed_t1) > target_t1:
            target_t1 = len(fixed_t1)
        elif len(fixed_t2) > target_t2:
            target_t1 = len(players) - len(fixed_t2)
        needed_t1 = max(0, min(len(free_p), target_t1 - len(fixed_t1)))
    else:
        needed_t1 = team_size - len(fixed_t1)

    t1_players = fixed_t1 + free_p[:needed_t1]
    t2_players = fixed_t2 + free_p[needed_t1:]

    # 2. Assign roles to each team
    role_slots = [Role.TANK] * composition.tank + [Role.DAMAGE] * composition.damage + [Role.SUPPORT] * composition.support

    def _assign_team_roles(team_list: List[Player]):
        available_roles = list(role_slots)
        # Apply fixed roles first
        if fixed_roles:
            for p in team_list:
                if p.name in fixed_roles and fixed_roles[p.name] in available_roles:
                    p.role = fixed_roles[p.name]
                    available_roles.remove(fixed_roles[p.name])
                else:
                    p.role = None
        else:
            for p in team_list:
                p.role = None

        rng.shuffle(available_roles)
        for p in team_list:
            if p.role is None and available_roles:
                p.role = available_roles.pop()

    _assign_team_roles(t1_players)
    _assign_team_roles(t2_players)

    return t1_players, t2_players


def simple_shuffle(
    players: List[Player],
    mode: GameMode,
    fixed: Dict[str, int],
    rng: Optional[random.Random] = None,
    allow_partial: bool = False,
) -> Tuple[List[Player], List[Player]]:
    """Simple random distribution of players respecting fixed teams."""
    if rng is None:
        rng = random.Random()
    if not allow_partial and len(players) != mode.total_players:
        raise ValueError(f"Expected {mode.total_players} players for {mode.value}, got {len(players)}")
    if len(players) < 2:
        raise ValueError("At least 2 players are required to shuffle")

    team_size = mode.players_per_team
    fixed_t1 = [copy.copy(p) for p in players if fixed.get(p.name) == 1]
    fixed_t2 = [copy.copy(p) for p in players if fixed.get(p.name) == 2]
    free_p = [copy.copy(p) for p in players if p.name not in fixed]
    rng.shuffle(free_p)

    if allow_partial and len(players) < mode.total_players:
        half = len(players) // 2
        extra = rng.randint(0, 1) if (len(players) % 2) else 0
        target_t1 = half + extra
        target_t2 = len(players) - target_t1
        if len(fixed_t1) > target_t1:
            target_t1 = len(fixed_t1)
        elif len(fixed_t2) > target_t2:
            target_t1 = len(players) - len(fixed_t2)
        needed_t1 = max(0, min(len(free_p), target_t1 - len(fixed_t1)))
    else:
        needed_t1 = team_size - len(fixed_t1)

    t1 = fixed_t1 + free_p[:needed_t1]
    t2 = fixed_t2 + free_p[needed_t1:]
    return t1, t2


class TeamShuffler:
    """Manages team shuffling and role-mirror mathematical matchmaking."""

    def __init__(self, diversity_candidates: int = 50):
        self.diversity_candidates = diversity_candidates
        self._rng = random.Random()

    def shuffle_pro(
        self,
        players: List[Player],
        mode: GameMode,
        composition: TeamComposition,
        fixed: Dict[str, int],
        history: List[Match | ShuffleHistoryEntry],
        shuffle_mode: ShuffleMode,
        auto_roles: bool = True,
        balance_by_mmr: bool = False,
        fixed_roles: Optional[Dict[str, Role]] = None,
        allow_partial: bool = False,
    ) -> Tuple[Team, Team]:
        """
        Executes the matchmaking optimization:
        - If balance_by_mmr is True: Runs multi-candidate search minimizing the NASA Loss Function.
        - If False: Standard casual shuffle.
        """
        team_size = mode.players_per_team
        if not allow_partial and len(players) != mode.total_players:
            raise ValueError(f"Expected {mode.total_players} players for {mode.value}, got {len(players)}")
        if len(players) < 2:
            raise ValueError("At least 2 players are required to shuffle")

        num_candidates = self.diversity_candidates if (balance_by_mmr or shuffle_mode == ShuffleMode.MAX_VARIETY) else 15
        if balance_by_mmr:
            num_candidates = max(num_candidates, 80)

        best_t1: Optional[List[Player]] = None
        best_t2: Optional[List[Player]] = None
        best_loss = float('inf')

        for _ in range(num_candidates):
            if auto_roles:
                t1, t2 = generate_candidate_with_roles(players, mode, composition, fixed, fixed_roles, self._rng, allow_partial=allow_partial)
            else:
                fixed_t1 = [copy.copy(p) for p in players if fixed.get(p.name) == 1]
                fixed_t2 = [copy.copy(p) for p in players if fixed.get(p.name) == 2]
                free_p = [copy.copy(p) for p in players if p.name not in fixed]
                self._rng.shuffle(free_p)
                t1 = fixed_t1 + free_p[:team_size - len(fixed_t1)]
                t2 = fixed_t2 + free_p[team_size - len(fixed_t1):]

            if balance_by_mmr:
                loss = evaluate_matchup_loss(t1, t2, history)
            else:
                loss = calculate_pair_similarity(Team(name="", players=t1), Team(name="", players=t2), history)

            if loss < best_loss:
                best_loss = loss
                best_t1 = t1
                best_t2 = t2
                if loss == 0.0:
                    break

        if best_t1 is None or best_t2 is None:
            best_t1, best_t2 = generate_candidate_with_roles(players, mode, composition, fixed, fixed_roles, self._rng)

        return Team(name="", players=best_t1), Team(name="", players=best_t2)

    def set_seed(self, seed: Optional[int]):
        if seed is not None:
            self._rng.seed(seed)
        else:
            self._rng.seed()
