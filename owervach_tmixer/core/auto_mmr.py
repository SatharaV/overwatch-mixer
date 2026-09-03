"""Bayesian Auto-MMR calibration engine and individual player performance tracker."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from .models import Match, Player, Role

K_BASE_FACTOR = 0.60  # Sensibilidad de aprendizaje por partida
MIN_MMR = 1.0
MAX_MMR = 10.0


@dataclass
class PlayerPerformanceStats:
    """Detailed empirical match record for an individual player."""

    name: str
    matches_played: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    calculated_mmr: float = 5.0
    calculated_mmr_tank: Optional[float] = None
    calculated_mmr_damage: Optional[float] = None
    calculated_mmr_support: Optional[float] = None
    role_records: Dict[str, Dict[str, int]] = field(
        default_factory=lambda: {
            "tank": {"wins": 0, "losses": 0, "draws": 0},
            "damage": {"wins": 0, "losses": 0, "draws": 0},
            "support": {"wins": 0, "losses": 0, "draws": 0},
        }
    )

    @property
    def winrate(self) -> float:
        if self.matches_played == 0:
            return 0.0
        return (self.wins / self.matches_played) * 100.0

    def get_role_winrate(self, role_str: str) -> float:
        rec = self.role_records.get(role_str.lower(), {})
        total = rec.get("wins", 0) + rec.get("losses", 0) + rec.get("draws", 0)
        if total == 0:
            return 0.0
        return (rec.get("wins", 0) / total) * 100.0


def calculate_match_expected_win(avg_mmr_a: float, avg_mmr_b: float) -> float:
    """Calculates expected victory probability of Team A against Team B using logistic curve."""
    diff = (avg_mmr_b - avg_mmr_a) / 4.0
    return 1.0 / (1.0 + (10.0 ** diff))


def calibrate_all_players_from_history(
    history: List[Match],
    players_pool: List[Player],
) -> Dict[str, PlayerPerformanceStats]:
    """Processes historical matches chronologically and computes true calibrated MMR for all players."""
    stats_map: Dict[str, PlayerPerformanceStats] = {}

    def get_or_create(name: str) -> PlayerPerformanceStats:
        folded = name.strip().casefold()
        if folded not in stats_map:
            # Buscar si el jugador tiene un MMR manual de partida como punto de partida (Prior)
            base_prior = 5.0
            for p in players_pool:
                if p.name.casefold() == folded:
                    base_prior = float(getattr(p, "mmr", 5))
                    break
            stats_map[folded] = PlayerPerformanceStats(name=name, calculated_mmr=base_prior)
        return stats_map[folded]

    # Procesar de la partida más antigua a la más reciente
    chronological_matches = sorted(history, key=lambda m: m.timestamp)

    for match in chronological_matches:
        winner = getattr(match, "winner", None)
        if winner not in (1, 2, 0):
            continue

        t1_players = [p for p in match.team1.players if p]
        t2_players = [p for p in match.team2.players if p]

        if not t1_players or not t2_players:
            continue

        # Promedios de MMR del enfrentamiento
        avg1 = sum(get_or_create(p.name).calculated_mmr for p in t1_players) / len(t1_players)
        avg2 = sum(get_or_create(p.name).calculated_mmr for p in t2_players) / len(t2_players)

        prob_win1 = calculate_match_expected_win(avg1, avg2)
        prob_win2 = 1.0 - prob_win1

        actual1 = 1.0 if winner == 1 else (0.5 if winner == 0 else 0.0)
        actual2 = 1.0 if winner == 2 else (0.5 if winner == 0 else 0.0)

        delta1 = K_BASE_FACTOR * (actual1 - prob_win1)
        delta2 = K_BASE_FACTOR * (actual2 - prob_win2)

        # 1. Actualizar jugadores Equipo 1
        for p in t1_players:
            st = get_or_create(p.name)
            st.matches_played += 1
            if winner == 1:
                st.wins += 1
            elif winner == 2:
                st.losses += 1
            else:
                st.draws += 1

            st.calculated_mmr = max(MIN_MMR, min(MAX_MMR, st.calculated_mmr + delta1))

            # Calibración específica por rol
            if p.role:
                r_key = p.role.value.lower()
                if r_key in st.role_records:
                    if winner == 1:
                        st.role_records[r_key]["wins"] += 1
                    elif winner == 2:
                        st.role_records[r_key]["losses"] += 1
                    else:
                        st.role_records[r_key]["draws"] += 1

                curr_role_mmr = getattr(st, f"calculated_mmr_{r_key}", None)
                if curr_role_mmr is None:
                    curr_role_mmr = st.calculated_mmr
                setattr(st, f"calculated_mmr_{r_key}", max(MIN_MMR, min(MAX_MMR, curr_role_mmr + delta1)))

        # 2. Actualizar jugadores Equipo 2
        for p in t2_players:
            st = get_or_create(p.name)
            st.matches_played += 1
            if winner == 2:
                st.wins += 1
            elif winner == 1:
                st.losses += 1
            else:
                st.draws += 1

            st.calculated_mmr = max(MIN_MMR, min(MAX_MMR, st.calculated_mmr + delta2))

            if p.role:
                r_key = p.role.value.lower()
                if r_key in st.role_records:
                    if winner == 2:
                        st.role_records[r_key]["wins"] += 1
                    elif winner == 1:
                        st.role_records[r_key]["losses"] += 1
                    else:
                        st.role_records[r_key]["draws"] += 1

                curr_role_mmr = getattr(st, f"calculated_mmr_{r_key}", None)
                if curr_role_mmr is None:
                    curr_role_mmr = st.calculated_mmr
                setattr(st, f"calculated_mmr_{r_key}", max(MIN_MMR, min(MAX_MMR, curr_role_mmr + delta2)))

    return stats_map
