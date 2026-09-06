"""Data models for the Overwatch Organizer with configurable player name alignment, robust bans, and Bayesian Auto-MMR."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class GameMode(Enum):
    """Game mode determining team size."""

    FIVE_V_FIVE = "5v5"
    SIX_V_SIX = "6v6"

    @property
    def players_per_team(self) -> int:
        return 5 if self == GameMode.FIVE_V_FIVE else 6

    @property
    def total_players(self) -> int:
        return self.players_per_team * 2


class Role(Enum):
    """Hero roles in Overwatch."""

    TANK = "tank"
    DAMAGE = "damage"
    SUPPORT = "support"

    @property
    def color(self) -> str:
        colors = {
            Role.TANK: "#00B4FF",
            Role.DAMAGE: "#FF4444",
            Role.SUPPORT: "#FFD700",
        }
        return colors[self]

    @property
    def icon_name(self) -> str:
        return self.value


class ShuffleMode(Enum):
    """Team shuffling algorithm modes."""

    RANDOM = "random"
    MAX_VARIETY = "max_variety"
    AVOID_LAST = "avoid_last"

    @property
    def display_name(self) -> str:
        names = {
            ShuffleMode.RANDOM: "Aleatorio",
            ShuffleMode.MAX_VARIETY: "Máxima variedad",
            ShuffleMode.AVOID_LAST: "Evitar última mezcla",
        }
        return names[self]


class MapMode(Enum):
    """Map game modes."""

    CONTROL = "Control"
    ESCORT = "Escort"
    HYBRID = "Hybrid"
    PUSH = "Push"
    FLASHPOINT = "Flashpoint"


@dataclass
class Player:
    """A player with multi-role MMR, empirical auto-calibration, and custom styling."""

    name: str
    role: Role | None = None
    fixed_team: int | None = None
    fixed_role: bool = False
    mmr: int = 5
    mmr_tank: int | None = None
    mmr_damage: int | None = None
    mmr_support: int | None = None
    custom_title: str = ""
    custom_color: str | None = None
    auto_mmr_enabled: bool = True
    calculated_mmr: float | None = None
    calculated_mmr_tank: float | None = None
    calculated_mmr_damage: float | None = None
    calculated_mmr_support: float | None = None
    wins: int = 0
    losses: int = 0
    draws: int = 0
    is_vip: bool = False
    streak_played: int = 0
    streak_benched: int = 0

    _DECOR_TOKENS = ("⭐", "🔒", "🛡️", "⚔️", "❤️")
    _ROLE_WORDS = {"tank", "damage", "support"}

    def __post_init__(self):
        self.name = self._clean_name(self.name)

    @classmethod
    def _clean_name(cls, name: str) -> str:
        from owervach_tmixer.core.special_player import format_player_name
        parts = name.strip().split()
        if not parts:
            return ""
        has_decor = any(any(tok in p for tok in cls._DECOR_TOKENS) for p in parts)
        cleaned = [
            p
            for p in parts
            if not any(tok in p for tok in cls._DECOR_TOKENS)
            and not (has_decor and p.casefold() in cls._ROLE_WORDS)
        ]
        raw_str = " ".join(cleaned)
        return format_player_name(raw_str, True)

    def reset_mmr(self, default_val: int = 5):
        """Resetea el MMR manual al valor base y limpia calibraciones IA y estadísticas."""
        self.mmr = default_val
        self.mmr_tank = None
        self.mmr_damage = None
        self.mmr_support = None
        self.calculated_mmr = None
        self.calculated_mmr_tank = None
        self.calculated_mmr_damage = None
        self.calculated_mmr_support = None
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.streak_played = 0
        self.streak_benched = 0

    def get_mmr_for_role(self, role: Role | str | None = None) -> float | int:
        """Returns the effective rating (Calibrated by IA if enabled, or Manual Prior)."""
        # 1. Si la autocalibración está activa y existe dato empírico
        if self.auto_mmr_enabled and self.calculated_mmr is not None:
            if role is not None:
                role_str = role.value if isinstance(role, Role) else str(role).lower()
                if ("tank" in role_str or "tanque" in role_str) and self.calculated_mmr_tank is not None:
                    return round(self.calculated_mmr_tank, 1)
                elif ("damage" in role_str or "dps" in role_str or "daño" in role_str) and self.calculated_mmr_damage is not None:
                    return round(self.calculated_mmr_damage, 1)
                elif ("support" in role_str or "apoyo" in role_str or "sanador" in role_str) and self.calculated_mmr_support is not None:
                    return round(self.calculated_mmr_support, 1)
            return round(self.calculated_mmr, 1)

        # 2. Fallback Manual Fijo
        if role is None:
            return getattr(self, "mmr", 5)

        role_str = role.value if isinstance(role, Role) else str(role).lower()
        if "tank" in role_str or "tanque" in role_str:
            return self.mmr_tank if self.mmr_tank is not None else getattr(self, "mmr", 5)
        elif "damage" in role_str or "dps" in role_str or "daño" in role_str:
            return self.mmr_damage if self.mmr_damage is not None else getattr(self, "mmr", 5)
        elif "support" in role_str or "apoyo" in role_str or "sanador" in role_str:
            return self.mmr_support if self.mmr_support is not None else getattr(self, "mmr", 5)

        return getattr(self, "mmr", 5)

    @property
    def is_fixed(self) -> bool:
        return self.fixed_team is not None

    @property
    def total_matches(self) -> int:
        return self.wins + self.losses + self.draws

    @property
    def winrate(self) -> float:
        if self.total_matches == 0:
            return 0.0
        return (self.wins / self.total_matches) * 100.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "role": self.role.value if self.role else None,
            "fixed_team": self.fixed_team,
            "fixed_role": self.fixed_role,
            "mmr": getattr(self, "mmr", 5),
            "mmr_tank": getattr(self, "mmr_tank", None),
            "mmr_damage": getattr(self, "mmr_damage", None),
            "mmr_support": getattr(self, "mmr_support", None),
            "custom_title": getattr(self, "custom_title", ""),
            "custom_color": getattr(self, "custom_color", None),
            "auto_mmr_enabled": getattr(self, "auto_mmr_enabled", True),
            "calculated_mmr": getattr(self, "calculated_mmr", None),
            "calculated_mmr_tank": getattr(self, "calculated_mmr_tank", None),
            "calculated_mmr_damage": getattr(self, "calculated_mmr_damage", None),
            "calculated_mmr_support": getattr(self, "calculated_mmr_support", None),
            "wins": getattr(self, "wins", 0),
            "losses": getattr(self, "losses", 0),
            "draws": getattr(self, "draws", 0),
            "is_vip": getattr(self, "is_vip", False),
            "streak_played": getattr(self, "streak_played", 0),
            "streak_benched": getattr(self, "streak_benched", 0),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Player:
        role = Role(data["role"]) if data.get("role") else None
        return cls(
            name=data["name"],
            role=role,
            fixed_team=data.get("fixed_team"),
            fixed_role=data.get("fixed_role", False),
            mmr=data.get("mmr", 5),
            mmr_tank=data.get("mmr_tank"),
            mmr_damage=data.get("mmr_damage"),
            mmr_support=data.get("mmr_support"),
            custom_title=data.get("custom_title", ""),
            custom_color=data.get("custom_color"),
            auto_mmr_enabled=data.get("auto_mmr_enabled", True),
            calculated_mmr=data.get("calculated_mmr"),
            calculated_mmr_tank=data.get("calculated_mmr_tank"),
            calculated_mmr_damage=data.get("calculated_mmr_damage"),
            calculated_mmr_support=data.get("calculated_mmr_support"),
            wins=data.get("wins", 0),
            losses=data.get("losses", 0),
            draws=data.get("draws", 0),
            is_vip=data.get("is_vip", False),
            streak_played=data.get("streak_played", 0),
            streak_benched=data.get("streak_benched", 0),
        )


@dataclass
class TeamComposition:
    """Role composition for a team."""

    tank: int = 1
    damage: int = 2
    support: int = 2

    @property
    def total(self) -> int:
        return self.tank + self.damage + self.support

    def to_dict(self) -> dict:
        return {"tank": self.tank, "damage": self.damage, "support": self.support}

    @classmethod
    def from_dict(cls, data: dict) -> TeamComposition:
        return cls(
            tank=data.get("tank", 1),
            damage=data.get("damage", 2),
            support=data.get("support", 2),
        )

    @classmethod
    def default_for_mode(cls, mode: GameMode) -> TeamComposition:
        if mode == GameMode.FIVE_V_FIVE:
            return cls(tank=1, damage=2, support=2)
        return cls(tank=2, damage=2, support=2)


@dataclass
class Team:
    """A team with players."""

    name: str
    players: list[Player] = field(default_factory=list)

    def __post_init__(self):
        if not self.name:
            self.name = "Equipo"

    @property
    def size(self) -> int:
        return len(self.players)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "players": [p.to_dict() for p in self.players],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Team:
        return cls(
            name=data["name"],
            players=[Player.from_dict(p) for p in data.get("players", [])],
        )


@dataclass
class Map:
    """A map with its game mode."""

    name: str
    mode: str
    enabled: bool = True

    def __post_init__(self):
        self.name = self.name.strip()
        self.mode = self.mode.strip()

    def to_dict(self) -> dict:
        return {"name": self.name, "mode": self.mode, "enabled": self.enabled}

    @classmethod
    def from_dict(cls, data: dict) -> Map:
        return cls(
            name=data["name"],
            mode=data["mode"],
            enabled=data.get("enabled", True),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Map):
            return False
        return self.name == other.name and self.mode == other.mode

    def __hash__(self) -> int:
        return hash((self.name, self.mode))


@dataclass
class MatchSettings:
    """Settings for generating a match with robust ban defaults and Auto-MMR."""

    game_mode: GameMode = GameMode.FIVE_V_FIVE
    team1_name: str = "Gatitos"
    team2_name: str = "Perritas"
    team1_color: str = "#00B4FF"
    team2_color: str = "#FF4444"
    vsync: bool = True
    slot_font_size: int = 15
    window_geometry: dict = field(default_factory=dict)
    window_geometries: dict[str, dict] = field(default_factory=dict)
    shuffle_mode: ShuffleMode = ShuffleMode.MAX_VARIETY
    diversity_candidates: int = 50
    history_size: int = 10
    avoid_recent_maps: int = 3
    composition_5v5: TeamComposition = field(
        default_factory=lambda: TeamComposition(tank=1, damage=2, support=2)
    )
    composition_6v6: TeamComposition = field(
        default_factory=lambda: TeamComposition(tank=2, damage=2, support=2)
    )
    auto_roles: bool = False
    show_roles: bool = True
    balance_by_mmr: bool = False
    auto_calibrate_mmr: bool = True
    randomize_team_names: bool = False
    team_name_theme: str = "overwatch"
    auto_map: bool = True
    auto_bans: bool = True
    max_bans: int = 5
    max_bans_per_role: int = 2
    ban_portrait_size: int = 44
    bans_visible_rows: int = 3
    dnd_cross_team_swap: bool = True
    accent_color: str = "#61ab02"
    theme_name: str = "obsidian"
    map_card_size: str = "medium"
    map_card_aspect: str = "auto"
    saved_panel_expanded: bool = True
    bans_panel_expanded: bool = True
    slot_font_size: int = 13
    slot_dynamic_font: bool = True
    role_badge_style: str = 'emoji'
    slot_badge_outlines: bool = False
    slot_font_weight: str = "bold"
    slot_text_align: str = "center"
    auto_capitalize_names: bool = True
    tier_hero_size: int = 76
    tier_map_width: int = 125
    tier_map_height: int = 75
    tier_map_font_size: int = 14
    tier_player_width: int = 125
    tier_player_height: int = 75
    tier_export_ratio: str = '16:9'
    tier_show_watermark_export: bool = True
    tier_show_watermark_ui: bool = True
    last_selected_map: dict | None = None
    category_value_orders: dict[str, list[str]] = field(default_factory=dict)
    settings_tab_order: list[str] = field(default_factory=lambda: [
        "appearance", "content", "shuffle", "roles_bans", "maps", "players", "backup", "about", "about"
    ])
    bench_rotation_enabled: bool = False
    streamer_rest_interval: int = 0
    rotation_policy: str = "continuous"
    rotation_batch_size: int = 2
    min_matches_shield: int = 2

    def composition_for_mode(self) -> TeamComposition:
        if self.game_mode == GameMode.FIVE_V_FIVE:
            return self.composition_5v5
        return self.composition_6v6

    def role_order(self) -> list[Role]:
        comp = self.composition_for_mode()
        return [Role.TANK] * comp.tank + [Role.DAMAGE] * comp.damage + [Role.SUPPORT] * comp.support

    def to_dict(self) -> dict:
        return {
            "game_mode": self.game_mode.value,
            "team1_name": self.team1_name,
            "team2_name": self.team2_name,
            "shuffle_mode": self.shuffle_mode.value,
            "diversity_candidates": self.diversity_candidates,
            "history_size": self.history_size,
            "avoid_recent_maps": self.avoid_recent_maps,
            "composition_5v5": self.composition_5v5.to_dict(),
            "composition_6v6": self.composition_6v6.to_dict(),
            "auto_roles": self.auto_roles,
            "show_roles": self.show_roles,
            "balance_by_mmr": self.balance_by_mmr,
            "auto_calibrate_mmr": self.auto_calibrate_mmr,
            "randomize_team_names": self.randomize_team_names,
            "team_name_theme": self.team_name_theme,
            "auto_map": self.auto_map,
            "auto_bans": self.auto_bans,
            "max_bans": self.max_bans,
            "max_bans_per_role": self.max_bans_per_role,
            "ban_portrait_size": self.ban_portrait_size,
            "bans_visible_rows": getattr(self, "bans_visible_rows", 2),
            "dnd_cross_team_swap": self.dnd_cross_team_swap,
            "accent_color": self.accent_color,
            "theme_name": getattr(self, "theme_name", "obsidian"),
            "saved_panel_expanded": self.saved_panel_expanded,
            "bans_panel_expanded": self.bans_panel_expanded,
            "slot_font_size": self.slot_font_size,
            "slot_dynamic_font": getattr(self, "slot_dynamic_font", True),
            "role_badge_style": getattr(self, "role_badge_style", "emoji"),
            "slot_badge_outlines": getattr(self, "slot_badge_outlines", False),
            "slot_font_weight": self.slot_font_weight,
            "slot_text_align": self.slot_text_align,
            "tier_hero_size": self.tier_hero_size,
            "tier_map_width": self.tier_map_width,
            "tier_map_height": self.tier_map_height,
            "tier_map_font_size": self.tier_map_font_size,
            "tier_player_width": self.tier_player_width,
            "tier_player_height": self.tier_player_height,
            "tier_export_ratio": getattr(self, "tier_export_ratio", "16:9"),
            "tier_show_watermark_export": getattr(self, "tier_show_watermark_export", True),
            "tier_show_watermark_ui": getattr(self, "tier_show_watermark_ui", True),
            "last_selected_map": self.last_selected_map,
            "category_value_orders": self.category_value_orders,
            "settings_tab_order": self.settings_tab_order,
            "window_geometry": getattr(self, "window_geometry", {}),
            "window_geometries": getattr(self, "window_geometries", {}),
            "team1_color": getattr(self, "team1_color", "#00B4FF"),
            "team2_color": getattr(self, "team2_color", "#FF4444"),
            "vsync": getattr(self, "vsync", True),
            "bench_rotation_enabled": getattr(self, "bench_rotation_enabled", False),
            "streamer_rest_interval": getattr(self, "streamer_rest_interval", 0),
            "rotation_policy": getattr(self, "rotation_policy", "continuous"),
            "rotation_batch_size": getattr(self, "rotation_batch_size", 2),
            "min_matches_shield": getattr(self, "min_matches_shield", 2),
        }

    @classmethod
    def from_dict(cls, data: dict) -> MatchSettings:
        raw_max_bans = data.get("max_bans", 5)
        raw_per_role = data.get("max_bans_per_role", 2)
        return cls(
            game_mode=GameMode(data.get("game_mode", "5v5")),
            team1_name=data.get("team1_name", "Gatitos"),
            team2_name=data.get("team2_name", "Perritas"),
            shuffle_mode=ShuffleMode(data.get("shuffle_mode", "max_variety")),
            diversity_candidates=data.get("diversity_candidates", 50),
            history_size=data.get("history_size", 10),
            avoid_recent_maps=data.get("avoid_recent_maps", 3),
            composition_5v5=TeamComposition.from_dict(
                data.get("composition_5v5", {"tank": 1, "damage": 2, "support": 2})
            ),
            composition_6v6=TeamComposition.from_dict(
                data.get("composition_6v6", {"tank": 2, "damage": 2, "support": 2})
            ),
            auto_roles=data.get("auto_roles", False),
            show_roles=data.get("show_roles", True),
            balance_by_mmr=data.get("balance_by_mmr", False),
            auto_calibrate_mmr=data.get("auto_calibrate_mmr", True),
            randomize_team_names=data.get("randomize_team_names", False),
            team_name_theme=data.get("team_name_theme", "overwatch"),
            auto_map=data.get("auto_map", True),
            auto_bans=data.get("auto_bans", True),
            max_bans=raw_max_bans if (raw_max_bans is not None and raw_max_bans > 0) else 5,
            max_bans_per_role=raw_per_role if (raw_per_role is not None and raw_per_role > 0) else 2,
            ban_portrait_size=data.get("ban_portrait_size", 44),
            bans_visible_rows=data.get("bans_visible_rows", 3),
            dnd_cross_team_swap=data.get("dnd_cross_team_swap", True),
            accent_color=data.get("accent_color", "#61ab02"),
            theme_name=data.get("theme_name", "obsidian"),
            map_card_size=data.get("map_card_size", "medium"),
            map_card_aspect=data.get("map_card_aspect", "auto"),
            saved_panel_expanded=data.get("saved_panel_expanded", True),
            bans_panel_expanded=data.get("bans_panel_expanded", True),
            slot_font_size=data.get("slot_font_size", 13),
            slot_dynamic_font=data.get("slot_dynamic_font", True),
            role_badge_style=data.get("role_badge_style", "emoji"),
            slot_badge_outlines=data.get("slot_badge_outlines", False),
            slot_font_weight=data.get("slot_font_weight", "bold"),
            slot_text_align=data.get("slot_text_align", "center"),
            tier_hero_size=data.get("tier_hero_size", 76),
            tier_map_width=data.get("tier_map_width", 125),
            tier_map_height=data.get("tier_map_height", 75),
            tier_map_font_size=data.get("tier_map_font_size", 14),
            tier_player_width=data.get("tier_player_width", 125),
            tier_player_height=data.get("tier_player_height", 75),
            tier_export_ratio=data.get("tier_export_ratio", "16:9"),
            tier_show_watermark_export=data.get("tier_show_watermark_export", True),
            tier_show_watermark_ui=data.get("tier_show_watermark_ui", True),
            last_selected_map=data.get("last_selected_map"),
            category_value_orders=data.get("category_value_orders", {}),
            settings_tab_order=data.get("settings_tab_order", ["appearance", "content", "shuffle", "roles_bans", "maps", "players", "backup", "about", "about"]),
            window_geometry=data.get("window_geometry", {}),
            window_geometries=data.get("window_geometries", {}),
            team1_color=data.get("team1_color", "#00B4FF"),
            team2_color=data.get("team2_color", "#FF4444"),
            vsync=data.get("vsync", True),
            bench_rotation_enabled=data.get("bench_rotation_enabled", False),
            streamer_rest_interval=data.get("streamer_rest_interval", 0),
            rotation_policy=data.get("rotation_policy", "continuous"),
            rotation_batch_size=data.get("rotation_batch_size", 2),
            min_matches_shield=data.get("min_matches_shield", 2),
        )


@dataclass
class Match:
    """A complete generated match."""

    team1: Team
    team2: Team
    map: Map | None = None
    bans: list[str] = field(default_factory=list)
    winner: int | None = None  # 1 for Team 1, 2 for Team 2, 0 for Draw, None for unplayed
    timestamp: datetime = field(default_factory=datetime.now)
    settings_snapshot: MatchSettings | None = None

    def to_dict(self) -> dict:
        return {
            "team1": self.team1.to_dict(),
            "team2": self.team2.to_dict(),
            "map": self.map.to_dict() if self.map else None,
            "bans": self.bans,
            "winner": self.winner,
            "timestamp": self.timestamp.isoformat(),
            "settings_snapshot": self.settings_snapshot.to_dict()
            if self.settings_snapshot
            else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Match:
        settings = (
            MatchSettings.from_dict(data["settings_snapshot"])
            if data.get("settings_snapshot")
            else None
        )
        return cls(
            team1=Team.from_dict(data["team1"]),
            team2=Team.from_dict(data["team2"]),
            map=Map.from_dict(data["map"]) if data.get("map") else None,
            bans=data.get("bans", []),
            winner=data.get("winner"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            settings_snapshot=settings,
        )


@dataclass
class Hero:
    """A hero with role, custom tags, and robust origin tracking."""

    name: str
    role: Role
    tags: dict[str, str] = field(default_factory=dict)
    original_name: str | None = None
    is_custom: bool = False
    custom_portrait: str | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "role": self.role.value,
            "tags": self.tags,
            "original_name": self.original_name,
            "is_custom": self.is_custom,
            "custom_portrait": self.custom_portrait,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Hero:
        return cls(
            name=data["name"],
            role=Role(data["role"]),
            tags=data.get("tags", {}),
            original_name=data.get("original_name"),
            is_custom=data.get("is_custom", False),
            custom_portrait=data.get("custom_portrait"),
        )


@dataclass
class BanManager:
    """Manages hero bans with resilient limits."""

    heroes: list[Hero] = field(default_factory=list)
    max_bans: int = 5
    max_bans_per_role: int = 2
    banned: set[str] = field(default_factory=set)

    def __post_init__(self):
        if self.max_bans <= 0:
            self.max_bans = 5
        if self.max_bans_per_role <= 0:
            self.max_bans_per_role = 2

    def toggle_ban(self, hero_name: str) -> bool:
        if hero_name in self.banned:
            self.banned.remove(hero_name)
            return False
        if not self.can_ban(hero_name):
            return False
        self.banned.add(hero_name)
        return True

    def hero_by_name(self, hero_name: str) -> Hero | None:
        folded = hero_name.casefold()
        return next((hero for hero in self.heroes if hero.name.casefold() == folded), None)

    def banned_in_role(self, role: Role) -> int:
        return sum(
            self.hero_by_name(name) is not None and self.hero_by_name(name).role == role
            for name in self.banned
        )

    def can_ban(self, hero_name: str) -> bool:
        hero = self.hero_by_name(hero_name)
        if hero is None or hero.name in self.banned:
            return False
        effective_max = self.max_bans if self.max_bans > 0 else 5
        effective_per_role = self.max_bans_per_role if self.max_bans_per_role > 0 else 2
        if len(self.banned) >= effective_max:
            return False
        return self.banned_in_role(hero.role) < effective_per_role

    def ban_error(self, hero_name: str) -> str:
        hero = self.hero_by_name(hero_name)
        if hero is None:
            return "Héroe no encontrado."
        effective_max = self.max_bans if self.max_bans > 0 else 5
        effective_per_role = self.max_bans_per_role if self.max_bans_per_role > 0 else 2
        if len(self.banned) >= effective_max:
            return f"Máximo {effective_max} baneos alcanzado."
        if self.banned_in_role(hero.role) >= effective_per_role:
            return f"Máximo {effective_per_role} baneos de {hero.role.value}."
        return ""

    def is_banned(self, hero_name: str) -> bool:
        return hero_name in self.banned

    def randomize_bans(self) -> set[str]:
        import random

        all_names = [h.name for h in self.heroes]
        random.shuffle(all_names)
        self.banned.clear()
        effective_max = self.max_bans if self.max_bans > 0 else 5
        for name in all_names:
            if len(self.banned) >= effective_max:
                break
            if self.can_ban(name):
                self.banned.add(name)
        return self.banned.copy()

    def clear_bans(self):
        self.banned.clear()

    def to_dict(self) -> dict:
        return {
            "max_bans": self.max_bans,
            "max_bans_per_role": self.max_bans_per_role,
            "banned": list(self.banned),
        }

    @classmethod
    def from_dict(cls, data: dict, heroes: list[Hero]) -> BanManager:
        raw_max = data.get("max_bans", 5)
        raw_role = data.get("max_bans_per_role", 2)
        return cls(
            heroes=heroes,
            max_bans=raw_max if (raw_max is not None and raw_max > 0) else 5,
            max_bans_per_role=raw_role if (raw_role is not None and raw_role > 0) else 2,
            banned=set(data.get("banned", [])),
        )


def validate_players(players: list[Player], mode: GameMode, allow_partial: bool = False) -> list[str]:
    errors = []
    required = mode.total_players

    if not players:
        errors.append("No hay jugadores en la lista.")
        return errors

    if not allow_partial and len(players) != required:
        errors.append(
            f"Se necesitan exactamente {required} jugadores para {mode.value} (hay {len(players)})."
        )

    empty_names = [i for i, p in enumerate(players) if not p.name]
    if empty_names:
        errors.append(f"Nombres vacíos en posiciones: {[i + 1 for i in empty_names]}")

    seen = set()
    duplicates = []
    for i, p in enumerate(players):
        if p.name in seen:
            duplicates.append(p.name)
        seen.add(p.name)
    if duplicates:
        errors.append(f"Nombres duplicados: {', '.join(duplicates)}")

    fixed_team1 = sum(1 for p in players if p.fixed_team == 1)
    fixed_team2 = sum(1 for p in players if p.fixed_team == 2)
    team_size = mode.players_per_team

    if fixed_team1 > team_size:
        errors.append(f"Demasiados jugadores fijados en Equipo 1 ({fixed_team1}/{team_size}).")
    if fixed_team2 > team_size:
        errors.append(f"Demasiados jugadores fijados en Equipo 2 ({fixed_team2}/{team_size}).")

    return errors


def validate_map_import(lines: list[str]) -> tuple[list[Map], list[tuple[int, str]]]:
    valid = []
    errors = []
    seen = set()

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue

        if "|" not in line:
            errors.append((i, f"Falta separador '|': {line}"))
            continue

        name, mode = line.split("|", 1)
        name = name.strip()
        mode = mode.strip()

        if not name or not mode:
            errors.append((i, f"Nombre o modo vacío: {line}"))
            continue

        mode_map = {
            "control": "Control",
            "escort": "Escort",
            "hybrid": "Hybrid",
            "push": "Push",
            "flashpoint": "Flashpoint",
        }
        normalized_mode = mode_map.get(mode.lower(), mode)

        if (name, normalized_mode) in seen:
            errors.append((i, f"Duplicado: {name} | {normalized_mode}"))
            continue

        seen.add((name, normalized_mode))
        valid.append(Map(name=name, mode=normalized_mode))

    return valid, errors
