"""Map management and randomization."""

from __future__ import annotations
import random
from typing import List, Optional, Tuple
from collections import deque

from .models import Map


class MapPool:
    """Manages a pool of maps with history tracking."""

    def __init__(self, maps: List[Map], avoid_recent: int = 3):
        self.maps = maps
        self._avoid_recent = 0
        self._recent: deque[str] = deque(maxlen=0)
        self.avoid_recent = avoid_recent

    @property
    def avoid_recent(self) -> int:
        return self._avoid_recent

    @avoid_recent.setter
    def avoid_recent(self, count: int):
        """Update the history window while retaining the newest map names."""
        self._avoid_recent = max(0, count)
        recent = list(getattr(self, "_recent", ()))[:self._avoid_recent]
        self._recent = deque(recent, maxlen=self._avoid_recent)

    def load_history(self, recent_maps: List[str]):
        """Load recent map history."""
        self._recent = deque(recent_maps[:self.avoid_recent], maxlen=self.avoid_recent)

    def get_recent(self) -> List[str]:
        """Get list of recent maps (most recent first)."""
        return list(self._recent)

    def pick_random(self, rng: Optional[random.Random] = None) -> Map:
        """Pick a random map, avoiding recent ones if possible."""
        if rng is None:
            rng = random.Random()

        if not self.maps:
            raise ValueError("No maps available")

        available = [m for m in self.maps if m.name not in self._recent]

        if not available:
            # All maps are in recent history, pick from all
            available = self.maps

        selected = rng.choice(available)
        self._recent.appendleft(selected.name)
        return selected

    def pick_specific(self, name: str) -> Optional[Map]:
        """Pick a specific map by name."""
        for m in self.maps:
            if m.name == name:
                self._recent.appendleft(m.name)
                return m
        return None

    def add_map(self, map_obj: Map):
        """Add a map to the pool."""
        if map_obj not in self.maps:
            self.maps.append(map_obj)

    def remove_map(self, name: str) -> bool:
        """Remove a map by name."""
        for i, m in enumerate(self.maps):
            if m.name == name:
                self.maps.pop(i)
                return True
        return False

    def get_by_mode(self, mode: str) -> List[Map]:
        """Get maps filtered by mode."""
        return [m for m in self.maps if m.mode.lower() == mode.lower()]

    def get_modes(self) -> List[str]:
        """Get list of unique modes."""
        modes = set(m.mode for m in self.maps)
        return sorted(modes)

    def to_dict(self) -> dict:
        return {
            "maps": [m.to_dict() for m in self.maps],
            "avoid_recent": self.avoid_recent,
            "recent": list(self._recent),
        }

    @classmethod
    def from_dict(cls, data: dict) -> MapPool:
        pool = cls(
            maps=[Map.from_dict(m) for m in data.get("maps", [])],
            avoid_recent=data.get("avoid_recent", 3)
        )
        pool.load_history(data.get("recent", []))
        return pool
