"""Hero and ban management."""

from __future__ import annotations
import random
from typing import List, Set, Optional

from .models import Hero, Role, BanManager


class HeroManager:
    """Manages hero list and ban operations."""

    def __init__(self, heroes: List[Hero], max_bans: int = 5, max_bans_per_role: int = 2):
        self.heroes = heroes
        self.ban_manager = BanManager(
            heroes=heroes, max_bans=max_bans, max_bans_per_role=max_bans_per_role)

    def set_max_bans(self, max_bans: int):
        self.ban_manager.max_bans = max(max_bans, 0)
        # Trim current bans if needed
        if len(self.ban_manager.banned) > self.ban_manager.max_bans:
            excess = len(self.ban_manager.banned) - self.ban_manager.max_bans
            for hero in list(self.ban_manager.banned)[:excess]:
                self.ban_manager.banned.remove(hero)

    def set_max_bans_per_role(self, max_bans_per_role: int):
        self.ban_manager.max_bans_per_role = max(max_bans_per_role, 0)
        for role in Role:
            while self.ban_manager.banned_in_role(role) > self.ban_manager.max_bans_per_role:
                name = next(
                    name for name in self.ban_manager.banned
                    if self.ban_manager.hero_by_name(name).role == role
                )
                self.ban_manager.banned.remove(name)

    def toggle_ban(self, hero_name: str) -> bool:
        """Toggle ban status. Returns True if now banned."""
        return self.ban_manager.toggle_ban(hero_name)

    def is_banned(self, hero_name: str) -> bool:
        return self.ban_manager.is_banned(hero_name)

    def get_banned(self) -> List[str]:
        return sorted(self.ban_manager.banned)

    def clear_bans(self):
        self.ban_manager.clear_bans()

    def randomize_bans(self) -> List[str]:
        self.ban_manager.randomize_bans()
        return self.get_banned()

    def get_heroes_by_role(self, role: Optional[Role] = None) -> List[Hero]:
        if role is None:
            return self.heroes
        return [h for h in self.heroes if h.role == role]

    def get_roles(self) -> List[Role]:
        roles = set(h.role for h in self.heroes)
        return sorted(roles, key=lambda r: r.value)

    def add_hero(self, hero: Hero):
        if hero not in self.heroes:
            self.heroes.append(hero)
            self.ban_manager.heroes.append(hero)

    def remove_hero(self, name: str) -> bool:
        for i, h in enumerate(self.heroes):
            if h.name == name:
                self.heroes.pop(i)
                # Also remove from ban manager
                self.ban_manager.heroes = [h for h in self.ban_manager.heroes if h.name != name]
                self.ban_manager.banned.discard(name)
                return True
        return False

    def to_dict(self) -> dict:
        return {
            "heroes": [h.to_dict() for h in self.heroes],
            "max_bans": self.ban_manager.max_bans,
            "max_bans_per_role": self.ban_manager.max_bans_per_role,
            "banned": list(self.ban_manager.banned),
        }

    @classmethod
    def from_dict(cls, data: dict) -> HeroManager:
        heroes = [Hero.from_dict(h) for h in data.get("heroes", [])]
        mgr = cls(
            heroes=heroes,
            max_bans=data.get("max_bans", 5),
            max_bans_per_role=data.get("max_bans_per_role", 2),
        )
        mgr.ban_manager.banned = set(data.get("banned", []))
        return mgr
