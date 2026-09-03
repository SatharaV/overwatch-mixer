"""Match history management with deduplication and in-memory persistence."""

from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from .models import Match, MatchSettings
from .storage import Storage


class HistoryManager:
    """Manages match history with persistence and smart in-place updates."""

    def __init__(self, storage: Storage, max_size: int = 50):
        self.storage = storage
        self.max_size = max_size
        self._history: List[Match] = []
        self._load()

    def _load(self):
        self._history = self.storage.load_history()

    def add(self, match: Match):
        """Add or update a match in history without generating duplicates."""
        if self._history and (
            self._history[0] is match
            or self._history[0].timestamp == match.timestamp
        ):
            self._history[0] = match
        else:
            self._history.insert(0, match)

        if len(self._history) > self.max_size:
            self._history = self._history[:self.max_size]

        self.storage.save_history(self._history)

    def get_all(self) -> List[Match]:
        return self._history.copy()

    def get_recent_maps(self, count: int = 10) -> List[str]:
        """Get recent map names from history."""
        maps = []
        for match in self._history:
            if match.map and match.map.name not in maps:
                maps.append(match.map.name)
            if len(maps) >= count:
                break
        return maps

    def clear(self):
        self._history.clear()
        self.storage.clear_history()

    def get_stats(self) -> dict:
        """Get statistics about history."""
        if not self._history:
            return {"total": 0, "maps": {}, "modes": {}}

        map_counts = {}
        mode_counts = {}
        for match in self._history:
            if match.map:
                map_counts[match.map.name] = map_counts.get(match.map.name, 0) + 1
                mode_counts[match.map.mode] = mode_counts.get(match.map.mode, 0) + 1

        return {
            "total": len(self._history),
            "maps": map_counts,
            "modes": mode_counts,
        }
