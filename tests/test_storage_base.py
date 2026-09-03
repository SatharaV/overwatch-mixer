"""Base heroes/maps are part of the app: always present, self-healing merges."""

import json

import pytest

from owervach_tmixer.core.models import Hero, Role
from owervach_tmixer.core.storage import Storage
from owervach_tmixer.ui.widgets.hero_widget import hero_portrait_path


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
def _write_list(base, name, payload):
    path = base / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    return path


def _base_hero_count():
    return len(Storage()._load_default_heroes())


def _base_map_count():
    return len(Storage()._load_default_maps())


def test_junk_heroes_file_reseeded_to_base(isolated_xdg):
    data, _ = isolated_xdg
    _write_list(data, "owervach-tmixer/heroes.json", [{"name": "TestHero", "role": "tank"}])

    heroes = Storage().load_heroes()

    assert len(heroes) == _base_hero_count()
    assert "TestHero" not in {h.name for h in heroes}
    stored = json.load(open(data / "owervach-tmixer/heroes.json", encoding="utf-8"))
    assert {h["name"] for h in stored} == {h.name for h in heroes}


def test_junk_maps_file_reseeded_to_base(isolated_xdg):
    data, _ = isolated_xdg
    _write_list(data, "owervach-tmixer/maps.json", [{"name": "TestMap", "mode": "Control"}])

    maps = Storage().load_maps()

    assert len(maps) == _base_map_count()
    assert "TestMap" not in {m.name for m in maps}
    stored = json.load(open(data / "owervach-tmixer/maps.json", encoding="utf-8"))
    assert {m["name"] for m in stored} == {m.name for m in maps}


def test_missing_file_seeds_base(isolated_xdg):
    data, _ = isolated_xdg
    heroes = Storage().load_heroes()

    assert len(heroes) == _base_hero_count()
    assert (data / "owervach-tmixer/heroes.json").exists()
    assert len(Storage().load_maps()) == _base_map_count()


def test_union_keeps_base_and_custom_hero(isolated_xdg):
    data, _ = isolated_xdg
    _write_list(
        data,
        "owervach-tmixer/heroes.json",
        [{"name": "Ana", "role": "support"}, {"name": "MiHero", "role": "support"}],
    )

    heroes = Storage().load_heroes()

    names = [h.name for h in heroes]
    assert names[:-1] == _ordered_base_names()
    assert names[-1] == "MiHero"
    assert heroes[-1].role == Role.SUPPORT
    stored = json.load(open(data / "owervach-tmixer/heroes.json", encoding="utf-8"))
    assert any(h["name"] == "MiHero" for h in stored)


def _ordered_base_names():
    return [h.name for h in Storage()._load_default_heroes()]


def test_stored_attribute_wins_on_collision(isolated_xdg):
    data, _ = isolated_xdg
    _write_list(
        data,
        "owervach-tmixer/heroes.json",
        [{"name": "Ana", "role": "damage"}],
    )

    heroes = Storage().load_heroes()

    ana = next(h for h in heroes if h.name == "Ana")
    assert ana.role == Role.DAMAGE


def test_future_hero_propagates_into_stored_pool(isolated_xdg, monkeypatch):
    data, _ = isolated_xdg
    base = Storage()._load_default_heroes()
    _write_list(
        data,
        "owervach-tmixer/heroes.json",
        [{"name": "Ana", "role": "support"}, {"name": "LegacyExtra", "role": "support"}],
    )

    future = base + [Hero(name="FutureHero", role=Role.TANK)]
    monkeypatch.setattr(Storage, "_load_default_heroes", lambda self: list(future))

    heroes = Storage().load_heroes()

    names = {h.name for h in heroes}
    assert "FutureHero" in names
    assert "LegacyExtra" in names


def test_all_base_heroes_resolve_a_portrait():
    heroes = Storage()._load_default_heroes()

    missing = [h.name for h in heroes if hero_portrait_path(h.name) is None]

    assert missing == []


def test_union_keeps_custom_map(isolated_xdg):
    data, _ = isolated_xdg
    _write_list(
        data,
        "owervach-tmixer/maps.json",
        [{"name": "Busan", "mode": "Control"}, {"name": "MiMapa", "mode": "Push"}],
    )

    maps = Storage().load_maps()

    names = [m.name for m in maps]
    assert "Busan" in names
    assert "MiMapa" in names
    assert next(m for m in maps if m.name == "MiMapa").mode == "Push"
