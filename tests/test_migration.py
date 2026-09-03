"""Test the one-time data migration from the legacy "overwatch-organizer" dirs."""

import json
import os

import pytest

from owervach_tmixer.core.storage import Storage


@pytest.fixture
def isolated_xdg(tmp_path, monkeypatch):
    import platformdirs
    data = tmp_path / "xdg-data"
    config = tmp_path / "xdg-config"
    data.mkdir(parents=True, exist_ok=True)
    config.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(platformdirs, "user_data_dir", lambda appname=None, *a, **k: str(data / (appname or "owervach-tmixer")))
    monkeypatch.setattr(platformdirs, "user_config_dir", lambda appname=None, *a, **k: str(config / (appname or "owervach-tmixer")))
    monkeypatch.setenv("XDG_DATA_HOME", str(data))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config))
    return data, config
def _write(base: "os.PathLike[str]", name: str, payload: dict):
    path = base / name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    return path


def test_migrates_legacy_data_and_keeps_originals(isolated_xdg):
    data, config = isolated_xdg
    legacy_data = data / "overwatch-organizer"
    legacy_config = config / "overwatch-organizer"
    legacy_data.mkdir()
    legacy_config.mkdir()

    players = [{"name": "Snapshot", "role": "tank", "fixed_team": None}]
    legacy_players = _write(legacy_data, "players.json", players)
    _write(legacy_config, "settings.json", {"game_mode": "6v6"})

    Storage()

    new_data = data / "owervach-tmixer"
    copied = (new_data / "players.json").read_text(encoding="utf-8")
    assert copied == legacy_players.read_text(encoding="utf-8")
    assert (config / "owervach-tmixer" / "settings.json").exists()
    assert legacy_players.exists(), "legacy source files must be preserved as backup"


def test_migration_is_idempotent_copies_only_missing(isolated_xdg):
    data, _ = isolated_xdg
    legacy_data = data / "overwatch-organizer"
    legacy_data.mkdir()
    _write(legacy_data, "players.json", [{"name": "A"}])

    first = Storage()
    first.save_players([])

    Storage()

    new_players = data / "owervach-tmixer" / "players.json"
    assert (new_players).exists()
    with open(new_players, encoding="utf-8") as f:
        assert json.load(f) == [], "existing (empty) data must not be overwritten by legacy copy"


def test_no_legacy_dirs_does_nothing(isolated_xdg):
    data, _ = isolated_xdg
    Storage()
    new_data = data / "owervach-tmixer"
    assert new_data.exists()
    assert not (new_data / "players.json").exists()


def test_legacy_app_name_skips_migration(isolated_xdg):
    data, _ = isolated_xdg
    Storage(app_name="overwatch-organizer")
    assert not (data / "owervach-tmixer").exists()
