"""Complete match generation integrating all systems."""

from __future__ import annotations
from typing import Optional, List, Dict
from dataclasses import dataclass

from .models import (
    Player, Team, Map, Match, MatchSettings, GameMode,
    TeamComposition, ShuffleMode, Role,
)
from .shuffler import TeamShuffler
from .maps import MapPool
from .heroes import HeroManager
from .shuffle_history import ShuffleHistoryEntry


@dataclass
class MatchResult:
    """Result of a match generation."""
    team1: Team
    team2: Team
    map: Optional[Map] = None
    bans: List[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.bans is None:
            self.bans = []


class MatchGenerator:
    """Generates complete matches using all subsystems."""

    def __init__(
        self,
        shuffler: TeamShuffler,
        map_pool: MapPool,
        hero_manager: HeroManager,
    ):
        self.shuffler = shuffler
        self.map_pool = map_pool
        self.hero_manager = hero_manager

    def generate(
        self,
        players: List[Player],
        settings: MatchSettings,
        history: List[Match | ShuffleHistoryEntry],
        fixed_roles: Optional[Dict[str, Role]] = None,
        allow_partial: bool = False,
    ) -> MatchResult:
        from .models import validate_players
        errors = validate_players(players, settings.game_mode, allow_partial=allow_partial)
        if errors:
            return MatchResult(
                team1=Team(name=settings.team1_name, players=[]),
                team2=Team(name=settings.team2_name, players=[]),
                error="; ".join(errors)
            )

        fixed = {p.name: p.fixed_team for p in players if p.fixed_team is not None}
        composition = settings.composition_for_mode()

        # Execute Pro Mathematical Shuffle
        team1, team2 = self.shuffler.shuffle_pro(
            players=players,
            mode=settings.game_mode,
            composition=composition,
            fixed=fixed,
            history=history,
            shuffle_mode=settings.shuffle_mode,
            auto_roles=settings.auto_roles,
            balance_by_mmr=getattr(settings, "balance_by_mmr", False),
            fixed_roles=fixed_roles if settings.auto_roles else None,
            allow_partial=allow_partial,
        )

        team1.name = settings.team1_name
        team2.name = settings.team2_name

        selected_map = None
        if settings.auto_map and self.map_pool.maps:
            selected_map = self.map_pool.pick_random()

        bans = []
        if settings.auto_bans:
            bans = self.hero_manager.randomize_bans()
        else:
            bans = self.hero_manager.get_banned()

        return MatchResult(
            team1=team1,
            team2=team2,
            map=selected_map,
            bans=bans,
        )

    def reshuffle_teams(
        self,
        players: List[Player],
        settings: MatchSettings,
        history: List[Match | ShuffleHistoryEntry],
        current_team1: Team,
        current_team2: Team,
        allow_partial: bool = False,
    ) -> MatchResult:
        fixed = {p.name: p.fixed_team for p in players if p.fixed_team is not None}
        composition = settings.composition_for_mode()

        team1, team2 = self.shuffler.shuffle_pro(
            players=players,
            mode=settings.game_mode,
            composition=composition,
            fixed=fixed,
            history=history,
            shuffle_mode=settings.shuffle_mode,
            auto_roles=settings.auto_roles,
            balance_by_mmr=getattr(settings, "balance_by_mmr", False),
            allow_partial=allow_partial,
        )

        team1.name = settings.team1_name
        team2.name = settings.team2_name

        return MatchResult(
            team1=team1,
            team2=team2,
            map=current_team1.players[0].__dict__.get('_current_map') if hasattr(current_team1, '_current_map') else None,
            bans=[],
        )

    def reroll_map(self) -> Optional[Map]:
        if not self.map_pool.maps:
            return None
        return self.map_pool.pick_random()

    def reroll_bans(self, auto: bool) -> List[str]:
        if auto:
            return self.hero_manager.randomize_bans()
        return self.hero_manager.get_banned()
