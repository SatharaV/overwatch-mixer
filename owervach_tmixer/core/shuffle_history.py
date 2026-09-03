"""Shuffle history management for diversity-aware team generation."""

from __future__ import annotations
import json
from typing import List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import platformdirs

from .. import APP_NAME
from .models import Team, Player, GameMode, MatchSettings


class ShuffleHistoryEntry:
    """A single entry in the shuffle history."""

    def __init__(
        self,
        team1: Team,
        team2: Team,
        game_mode: GameMode,
        settings_snapshot: Optional[MatchSettings] = None
    ):
        self.team1 = team1
        self.team2 = team2
        self.game_mode = game_mode
        self.settings_snapshot = settings_snapshot
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        return {
            "team1": self.team1.to_dict(),
            "team2": self.team2.to_dict(),
            "game_mode": self.game_mode.value,
            "settings_snapshot": self.settings_snapshot.to_dict() if self.settings_snapshot else None,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> ShuffleHistoryEntry:
        settings = None
        if data.get("settings_snapshot"):
            settings = MatchSettings.from_dict(data["settings_snapshot"])
        return cls(
            team1=Team.from_dict(data["team1"]),
            team2=Team.from_dict(data["team2"]),
            game_mode=GameMode(data["game_mode"]),
            settings_snapshot=settings,
        )

    def get_similarity_pairs(self) -> set:
        """Get all player pairs in this shuffle for similarity calculation."""
        from itertools import combinations
        pairs = set()
        for p1, p2 in combinations(self.team1.players, 2):
            pairs.add(tuple(sorted([p1.name, p2.name])))
        for p1, p2 in combinations(self.team2.players, 2):
            pairs.add(tuple(sorted([p1.name, p2.name])))
        return pairs


class ShuffleHistoryManager:
    """Manages shuffle history with persistence."""

    def __init__(self, max_size: int = 10, app_name: str = APP_NAME):
        self.max_size = max_size
        self._history: List[ShuffleHistoryEntry] = []
        self._app_dir = Path(platformdirs.user_data_dir(app_name))
        self._app_dir.mkdir(parents=True, exist_ok=True)
        self._file = self._app_dir / "shuffle_history.json"
        self._load()

    def _load(self):
        if not self._file.exists():
            return
        try:
            with open(self._file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._history = [ShuffleHistoryEntry.from_dict(e) for e in data]
            # Trim if exceeded
            if len(self._history) > self.max_size:
                self._history = self._history[:self.max_size]
        except (json.JSONDecodeError, KeyError):
            self._history = []

    def _save(self):
        data = [entry.to_dict() for entry in self._history]
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, team1: Team, team2: Team, game_mode: GameMode, settings: Optional[MatchSettings] = None):
        """Add a new shuffle to history."""
        entry = ShuffleHistoryEntry(team1, team2, game_mode, settings)
        self._history.insert(0, entry)
        if len(self._history) > self.max_size:
            self._history = self._history[:self.max_size]
        self._save()

    def get_all(self) -> List[ShuffleHistoryEntry]:
        return self._history.copy()

    def get_last(self) -> Optional[ShuffleHistoryEntry]:
        return self._history[0] if self._history else None

    def get_at(self, index: int) -> Optional[ShuffleHistoryEntry]:
        if 0 <= index < len(self._history):
            return self._history[index]
        return None

    def remove_at(self, index: int) -> bool:
        if 0 <= index < len(self._history):
            self._history.pop(index)
            self._save()
            return True
        return False

    def clear(self):
        self._history.clear()
        self._save()

    def set_max_size(self, size: int):
        self.max_size = max(1, size)
        if len(self._history) > self.max_size:
            self._history = self._history[:self.max_size]
            self._save()