"""JSON file storage for persistence with intelligent self-healing entity merges."""

from __future__ import annotations

import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

import platformdirs

from .. import APP_NAME
from .models import (
    BanManager,
    GameMode,
    Hero,
    Map,
    Match,
    MatchSettings,
    Player,
)
from .roster import Roster
from ..utils import get_resource_path


class Storage:
    """Handles loading/saving all data to JSON files."""

    LEGACY_APP_NAME = "overwatch-organizer"

    def __init__(self, app_name: str = APP_NAME):
        self.app_dir = Path(platformdirs.user_data_dir(app_name))
        self.app_dir.mkdir(parents=True, exist_ok=True)

        self.config_dir = Path(platformdirs.user_config_dir(app_name))
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # File paths
        self.players_file = self.app_dir / "players.json"
        self.maps_file = self.app_dir / "maps.json"
        self.heroes_file = self.app_dir / "heroes.json"
        self.settings_file = self.config_dir / "settings.json"
        self.history_file = self.app_dir / "history.json"
        self.bans_file = self.app_dir / "bans.json"

        self._migrate_legacy_data(app_name)

    def _migrate_legacy_data(self, app_name: str):
        if app_name == self.LEGACY_APP_NAME:
            return
        legacy_pairs = (
            (Path(platformdirs.user_data_dir(self.LEGACY_APP_NAME)), self.app_dir),
            (Path(platformdirs.user_config_dir(self.LEGACY_APP_NAME)), self.config_dir),
        )
        for legacy, target in legacy_pairs:
            if not legacy.exists():
                continue
            for src in legacy.iterdir():
                if src.is_file() and src.suffix == ".json":
                    dst = target / src.name
                    if not dst.exists():
                        shutil.copy2(src, dst)

    def _backup_corrupted(self, path: Path) -> Path | None:
        backup = path.with_name(f"{path.name}.corrupted.bak")
        n = 1
        while backup.exists():
            backup = path.with_name(f"{path.name}.corrupted.bak.{n}")
            n += 1
        try:
            os.replace(path, backup)
        except OSError:
            return None
        print(f"[owervach-tmixer] Advertencia: {path.name} corrupto/incompleto; "
              f"respaldo en {backup.name}. Se usan valores por defecto.",
              file=sys.stderr)
        return backup

    def _read_json(self, path: Path | str) -> object | None:
        path = Path(path)
        if not path.exists():
            return None
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            self._backup_corrupted(path)
            return None

    def _write_json_atomic(self, path: Path | str, data):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f"{path.name}.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)

    # --- Players ---
    def load_players(self) -> list[Player]:
        data = self._read_json(self.players_file)
        if data is None:
            return []
        try:
            return [Player.from_dict(p) for p in data]
        except Exception:
            self._backup_corrupted(self.players_file)
            return []

    def save_players(self, players: list[Player]):
        self._write_json_atomic(self.players_file, [p.to_dict() for p in players])

    # --- Roster ---
    def load_roster(self, mode: GameMode) -> Roster:
        data = self._read_json(self.players_file)
        if data is None:
            return Roster.empty(mode)

        if isinstance(data, dict) and data.get("version") == Roster.VERSION:
            try:
                roster = Roster.from_dict(data, mode)
                if roster.game_mode != mode:
                    roster.on_game_mode_change(mode)
                return roster
            except Exception:
                self._backup_corrupted(self.players_file)
                return Roster.empty(mode)
        if isinstance(data, list):
            players = []
            try:
                for item in data:
                    if isinstance(item, str):
                        players.append(Player(name=item))
                    elif isinstance(item, dict):
                        players.append(Player.from_dict(item))
                return Roster.from_legacy(players, mode)
            except Exception:
                self._backup_corrupted(self.players_file)
                return Roster.empty(mode)
        self._backup_corrupted(self.players_file)
        return Roster.empty(mode)

    def save_roster(self, roster: Roster):
        self._write_json_atomic(self.players_file, roster.to_dict())

    # --- Maps ---
    def load_maps(self) -> list[Map]:
        return self._merge_base_content(self.maps_file, self._load_default_maps(), Map.from_dict)

    def _load_default_maps(self) -> list[Map]:
        try:
            default_file = get_resource_path("data/default_maps.json")
            if default_file.exists():
                with open(default_file, encoding="utf-8") as f:
                    data = json.load(f)
                return [Map.from_dict(m) for m in data]
        except Exception:
            print("[owervach-tmixer] Advertencia: datos por defecto de mapas "
                  "ilegibles; se usa la lista vacía.", file=sys.stderr)
        return []

    def restore_default_maps(self) -> list[Map]:
        defaults = self._load_default_maps()
        self.save_maps(defaults)
        return defaults

    def save_maps(self, maps: list[Map]):
        self._write_json_atomic(self.maps_file, [m.to_dict() for m in maps])

    def _merge_base_content(self, path: Path, base: list, from_dict):
        stored = []
        for item in self._read_json_list(path):
            try:
                stored.append(from_dict(item))
            except (KeyError, TypeError, ValueError):
                continue
        base_names = {m.name for m in base}
        if stored and not {m.name for m in stored} & base_names:
            stored = []
        merged = list(base)
        seen = set(base_names)
        for item in stored:
            if item.name in seen:
                for i, existing in enumerate(merged):
                    if existing.name == item.name:
                        merged[i] = item
                        break
            else:
                merged.append(item)
                seen.add(item.name)
        self._write_list(path, merged)
        return merged

    def _read_json_list(self, path: Path) -> list:
        data = self._read_json(path)
        if data is None:
            return []
        if not isinstance(data, list):
            self._backup_corrupted(path)
            return []
        return data

    def _write_list(self, path: Path, items: list):
        self._write_json_atomic(path, [i.to_dict() for i in items])

    # --- Heroes ---
    def load_heroes(self) -> list[Hero]:
        return self._merge_base_heroes(self.heroes_file, self._load_default_heroes())

    def _merge_base_heroes(self, path: Path, base: list[Hero]) -> list[Hero]:
        import unicodedata

        KNOWN_ALIASES = {
            "burrisa": "Orisa", "coomfist": "Doomfist", "diva": "D.Va",
            "esfera": "Wrecking Ball", "winton": "Winston", "saria": "Zarya",
            "mmmei": "Mei", "riper": "Reaper", "sonbra": "Sombra",
            "soyurn": "Sojourn", "treiser": "Tracer", "bapluis": "Baptiste",
            "keriko": "Kiriko", "mersi": "Mercy", "cierra": "Sierra",
            "momina": "Domina", "ernesto": "Emre", "la luuuupaaa": "Illari",
            "poya": "Pharah", "soldier: 67": "Soldier: 76",
        }

        def _norm_k(t: str) -> str:
            if not t:
                return ""
            n = unicodedata.normalize("NFKD", t)
            return "".join(c for c in n if not unicodedata.combining(c)).casefold().replace(" ", "").replace(".", "").replace(":", "")

        stored_raw = self._read_json_list(path)
        stored: list[Hero] = []
        for item in stored_raw:
            try:
                stored.append(Hero.from_dict(item))
            except (KeyError, TypeError, ValueError):
                continue

        base_tokens = {_norm_k(h.name): h for h in base}
        alias_tokens = {_norm_k(k): _norm_k(v) for k, v in KNOWN_ALIASES.items()}

        # Si el archivo contiene datos pero NINGUNO coincide con base ni alias, descartar basura (Junk file reset)
        if stored:
            matched = any(
                _norm_k(h.name) in base_tokens or (h.original_name and _norm_k(h.original_name) in base_tokens)
                for h in stored
            )
            if not matched:
                stored = []

        stored_base_map: dict[str, Hero] = {}
        custom_heroes: list[Hero] = []
        represented_base_tokens: set[str] = set()

        for s_hero in stored:
            orig_tok = _norm_k(s_hero.original_name or "")
            name_tok = _norm_k(s_hero.name)
            alias_target = alias_tokens.get(name_tok)

            if orig_tok and orig_tok in base_tokens:
                s_hero.is_custom = False
                stored_base_map[orig_tok] = s_hero
                represented_base_tokens.add(orig_tok)
            elif name_tok in base_tokens:
                s_hero.is_custom = False
                stored_base_map[name_tok] = s_hero
                represented_base_tokens.add(name_tok)
            elif alias_target and alias_target in base_tokens:
                s_hero.is_custom = False
                if not s_hero.original_name:
                    s_hero.original_name = base_tokens[alias_target].name
                stored_base_map[alias_target] = s_hero
                represented_base_tokens.add(alias_target)
            else:
                s_hero.is_custom = True
                custom_heroes.append(s_hero)

        merged: list[Hero] = []
        for b_hero in base:
            b_tok = _norm_k(b_hero.name)
            if b_tok in stored_base_map:
                merged.append(stored_base_map[b_tok])
            elif b_tok not in represented_base_tokens:
                b_hero.is_custom = False
                merged.append(b_hero)

        seen_names = {_norm_k(h.name) for h in merged}
        for ch in custom_heroes:
            ch_tok = _norm_k(ch.name)
            if ch_tok not in seen_names:
                merged.append(ch)
                seen_names.add(ch_tok)

        self._write_list(path, merged)
        return merged


    def _load_default_heroes(self) -> list[Hero]:
        try:
            default_file = get_resource_path("data/default_heroes.json")
            if default_file.exists():
                with open(default_file, encoding="utf-8") as f:
                    data = json.load(f)
                return [Hero.from_dict(h) for h in data]
        except Exception:
            print("[owervach-tmixer] Advertencia: datos por defecto de héroes "
                  "ilegibles; se usa la lista vacía.", file=sys.stderr)
        return []

    def restore_default_heroes(self) -> list[Hero]:
        defaults = self._load_default_heroes()
        self.save_heroes(defaults)
        return defaults

    def save_heroes(self, heroes: list[Hero]):
        self._write_json_atomic(self.heroes_file, [h.to_dict() for h in heroes])

    # --- Settings ---
    def load_settings(self) -> MatchSettings:
        data = self._read_json(self.settings_file)
        if data is None:
            return self._load_default_settings()
        try:
            return MatchSettings.from_dict(data)
        except Exception:
            self._backup_corrupted(self.settings_file)
            return self._load_default_settings()

    def _load_default_settings(self) -> MatchSettings:
        try:
            default_file = get_resource_path("data/default_settings.json")
            if default_file.exists():
                with open(default_file, encoding="utf-8") as f:
                    data = json.load(f)
                return MatchSettings.from_dict(data)
        except Exception:
            print("[owervach-tmixer] Advertencia: ajustes por defecto ilegibles; "
                  "se usan valores de fábrica.", file=sys.stderr)
        return MatchSettings()

    def save_settings(self, settings: MatchSettings):
        self._write_json_atomic(self.settings_file, settings.to_dict())

    # --- History ---
    def load_history(self) -> list[Match]:
        data = self._read_json(self.history_file)
        if data is None:
            return []
        try:
            return [Match.from_dict(m) for m in data]
        except Exception:
            self._backup_corrupted(self.history_file)
            return []

    def save_history(self, history: list[Match]):
        self._write_json_atomic(self.history_file, [m.to_dict() for m in history])

    def add_to_history(self, match: Match, max_size: int = 50):
        history = self.load_history()
        history.insert(0, match)
        if len(history) > max_size:
            history = history[:max_size]
        self.save_history(history)

    def clear_history(self):
        if self.history_file.exists():
            self.history_file.unlink()

    # --- Bans ---
    def load_bans(self, heroes: list[Hero]) -> BanManager:
        data = self._read_json(self.bans_file)
        if data is None:
            return BanManager(heroes=heroes)
        try:
            return BanManager.from_dict(data, heroes)
        except Exception:
            self._backup_corrupted(self.bans_file)
            return BanManager(heroes=heroes)

    def save_bans(self, ban_manager: BanManager):
        self._write_json_atomic(self.bans_file, ban_manager.to_dict())

    # --- Import/Export ---
    def export_players(self, players: list[Player], path: Path | str):
        self._write_json_atomic(Path(path), [p.to_dict() for p in players])

    def import_players(self, path: Path | str) -> list[Player]:
        with open(Path(path), "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Player.from_dict(p) for p in data]

    def export_maps(self, maps: list[Map], path: Path | str):
        self._write_json_atomic(Path(path), [m.to_dict() for m in maps])

    def import_maps(self, path: Path | str) -> list[Map]:
        with open(Path(path), "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Map.from_dict(m) for m in data]

    def export_settings(self, settings: MatchSettings, path: Path | str):
        self._write_json_atomic(Path(path), settings.to_dict())

    def import_settings(self, path: Path | str) -> MatchSettings:
        with open(Path(path), "r", encoding="utf-8") as f:
            data = json.load(f)
        return MatchSettings.from_dict(data)

    def export_heroes(self, heroes: list[Hero], path: Path | str):
        self._write_json_atomic(Path(path), [h.to_dict() for h in heroes])

    def import_heroes(self, path: Path | str) -> list[Hero]:
        with open(Path(path), "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Hero.from_dict(h) for h in data]

    # --- Full ZIP Packs (Data + Custom Images) ---
    def export_full_pack_zip(self, path: Path | str):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_name in ("maps.json", "heroes.json", "players.json", "history.json", "bans.json"):
                fpath = self.app_dir / file_name
                if fpath.exists():
                    zipf.write(fpath, arcname=f"data/{file_name}")

            if self.settings_file.exists():
                zipf.write(self.settings_file, arcname="data/settings.json")

            portraits_dir = self.app_dir / "hero_portraits"
            if portraits_dir.exists():
                for img in portraits_dir.glob("*"):
                    if img.is_file():
                        zipf.write(img, arcname=f"hero_portraits/{img.name}")

            maps_dir = self.app_dir / "Maps"
            if maps_dir.exists():
                for img in maps_dir.rglob("*"):
                    if img.is_file():
                        rel = img.relative_to(maps_dir)
                        zipf.write(img, arcname=f"Maps/{rel}")

    def import_full_pack_zip(self, path: Path | str) -> bool:
        path = Path(path)
        if not path.exists():
            return False
        with zipfile.ZipFile(path, "r") as zipf:
            for member in zipf.infolist():
                norm_name = Path(member.filename).as_posix()
                if ".." in norm_name or norm_name.startswith("/"):
                    continue

                if norm_name.startswith("hero_portraits/") or norm_name.startswith("Maps/"):
                    zipf.extract(member, self.app_dir)
                elif norm_name.startswith("data/"):
                    fname = Path(norm_name).name
                    if not fname.endswith(".json"):
                        continue
                    target = self.config_dir / fname if fname == "settings.json" else self.app_dir / fname
                    target.parent.mkdir(parents=True, exist_ok=True)
                    data = zipf.read(member.filename)
                    with open(target, "wb") as f:
                        f.write(data)
        return True

    def factory_reset(self) -> tuple[MatchSettings, list[Map], list[Hero], Roster]:
        # 1. Limpiar carpetas actuales
        for d in (self.app_dir, self.config_dir):
            if d.exists():
                for item in d.iterdir():
                    try:
                        if item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                        else:
                            item.unlink(missing_ok=True)
                    except OSError:
                        pass

        # 2. Purgar también carpetas legacy para que nunca resuciten datos viejos
        for legacy_name in (self.LEGACY_APP_NAME,):
            for pdir in (platformdirs.user_data_dir(legacy_name), platformdirs.user_config_dir(legacy_name)):
                p = Path(pdir)
                if p.exists():
                    shutil.rmtree(p, ignore_errors=True)

        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        settings = self._load_default_settings()
        self.save_settings(settings)

        maps = self._load_default_maps()
        self.save_maps(maps)

        heroes = self._load_default_heroes()
        self.save_heroes(heroes)

        roster = Roster.empty(settings.game_mode)
        self.save_roster(roster)

        if self.history_file.exists():
            self.history_file.unlink(missing_ok=True)
        if self.bans_file.exists():
            self.bans_file.unlink(missing_ok=True)

        return settings, maps, heroes, roster
