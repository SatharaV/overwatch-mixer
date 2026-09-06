"""Settings management."""

from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field

from .models import MatchSettings, GameMode, TeamComposition, ShuffleMode
from .storage import Storage


@dataclass
class WindowGeometry:
    """Window position and size."""
    x: int = 100
    y: int = 100
    width: int = 1280
    height: int = 720
    maximized: bool = False

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "maximized": self.maximized,
        }

    @classmethod
    def from_dict(cls, data: dict) -> WindowGeometry:
        return cls(
            x=data.get("x", 100),
            y=data.get("y", 100),
            width=data.get("width", 1200),
            height=data.get("height", 800),
            maximized=data.get("maximized", False),
        )


class SettingsManager:
    """Manages application settings with persistence."""

    def __init__(self, storage: Storage):
        self.storage = storage
        self._settings: MatchSettings = storage.load_settings()
        raw_geom = getattr(self._settings, "window_geometry", None)
        if isinstance(raw_geom, dict) and raw_geom.get("width", 0) > 0:
            self._geometry = WindowGeometry.from_dict(raw_geom)
        else:
            self._geometry = WindowGeometry()

    @property
    def settings(self) -> MatchSettings:
        return self._settings

    @property
    def geometry(self) -> WindowGeometry:
        return self._geometry

    def update_theme_name(self, theme_name: str):
        self._settings.theme_name = theme_name
        self.save()

    def update_game_mode(self, mode: GameMode):
        self._settings.game_mode = mode
        self.save()

    def update_team_names(self, team1: str, team2: str):
        self._settings.team1_name = team1
        self._settings.team2_name = team2
        self.save()

    def update_shuffle_mode(self, mode: ShuffleMode):
        self._settings.shuffle_mode = mode
        self.save()

    def update_diversity_candidates(self, count: int):
        self._settings.diversity_candidates = max(1, count)
        self.save()

    def update_history_size(self, size: int):
        self._settings.history_size = max(1, size)
        self.save()

    def update_avoid_recent_maps(self, count: int):
        self._settings.avoid_recent_maps = max(0, count)
        self.save()

    def update_composition(self, mode: GameMode, composition: TeamComposition):
        if mode == GameMode.FIVE_V_FIVE:
            self._settings.composition_5v5 = composition
        else:
            self._settings.composition_6v6 = composition
        self.save()

    def update_auto_roles(self, enabled: bool):
        self._settings.auto_roles = enabled
        self.save()

    def update_show_roles(self, enabled: bool):
        self._settings.show_roles = enabled
        self.save()

    def update_auto_map(self, enabled: bool):
        self._settings.auto_map = enabled
        self.save()

    def update_auto_bans(self, enabled: bool):
        self._settings.auto_bans = enabled
        self.save()

    def update_max_bans(self, count: int):
        self._settings.max_bans = max(0, count)
        self.save()

    def update_max_bans_per_role(self, count: int):
        self._settings.max_bans_per_role = max(0, count)
        self.save()

    def update_dnd_cross_team_swap(self, enabled: bool):
        self._settings.dnd_cross_team_swap = enabled
        self.save()

    def update_geometry(self, geometry: WindowGeometry):
        self._geometry = geometry
        if hasattr(self._settings, "window_geometry"):
            self._settings.window_geometry = geometry.to_dict()
        self.save()

    def save(self):
        self.storage.save_settings(self._settings)

    def get_window_geometry(self, window_id: str = "main", default_size: tuple[int, int] = (1280, 720)) -> WindowGeometry:
        raw_map = getattr(self._settings, "window_geometries", {})
        raw = raw_map.get(window_id) if isinstance(raw_map, dict) else None
        if not raw and window_id == "main":
            raw = getattr(self._settings, "window_geometry", None)
        if isinstance(raw, dict) and raw.get("width", 0) > 0:
            return WindowGeometry.from_dict(raw)
        return WindowGeometry(width=default_size[0], height=default_size[1])

    def update_window_geometry(self, window_id: str, geometry: WindowGeometry):
        if not hasattr(self._settings, "window_geometries") or not isinstance(self._settings.window_geometries, dict):
            self._settings.window_geometries = {}
        self._settings.window_geometries[window_id] = geometry.to_dict()
        if window_id == "main":
            self._geometry = geometry
            self._settings.window_geometry = geometry.to_dict()
        self.save()

    def reset_to_defaults(self):
        self._settings = MatchSettings()
        self.save()
