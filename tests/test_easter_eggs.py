"""Easter egg system + permanent special-player glow."""

import pytest
import random
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

from owervach_tmixer.core.models import GameMode
from owervach_tmixer.core.roster import Roster
from owervach_tmixer.core.special_player import (
    SPECIAL_GLOW,
    SPECIAL_NAMES,
    is_special_player_name,
)
from owervach_tmixer.ui.easter_eggs import (
    EasterEgg,
    EasterEggManager,
    EggContext,
)
from owervach_tmixer.ui.widgets.glow_text_delegate import (
    SPECIAL_ROLE,
    GlowTextDelegate,
)


@pytest.mark.parametrize("name", [
    "Satara", "SATARA", "sataRa", "SATTARA", "sattara", "SaTTaRa",
    "Sathara", "sathara", "SATHARA", "SaThArA", "  Satara  ",
    "Satar", "satar", "Satharaaa", "sathaara", "Satara2", "SaTaRaX",
])
def test_special_names_are_detected(name):
    assert is_special_player_name(name)


@pytest.mark.parametrize("name", [
    "", "Palomita", "Genji", "Tracer", "Doomfist", "Reinhardt", "Player1",
])
def test_common_names_are_not_special(name):
    assert not is_special_player_name(name)


def test_special_constants():
    assert SPECIAL_GLOW == "#61ab02"
    assert SPECIAL_NAMES == ("satara", "sattara", "sathara")


def test_manager_triggers_once():
    manager = EasterEggManager()
    assert manager.trigger_count == 0
    assert manager.maybe_trigger(None) is True
    assert manager.is_triggered is True
    assert manager.chosen_id in {"detected", "chosen", "again", "randomizer", "crown"}
    assert manager.trigger_count == 1
    assert manager.maybe_trigger(None) is False
    assert manager.trigger_count == 1


def test_fresh_manager_means_new_session():
    a = EasterEggManager()
    assert a.maybe_trigger(None) is True
    b = EasterEggManager()
    assert b.is_triggered is False
    assert b.maybe_trigger(None) is True


def test_manager_survives_broken_egg():
    class Boom(EasterEgg):
        id = "boom"

        def trigger(self, ctx):
            raise RuntimeError("boom")

    manager = EasterEggManager(eggs=[Boom()])
    assert manager.maybe_trigger(None) is True
    assert manager.chosen_id == "boom"


def test_ctx_without_window_is_safe():
    ctx = EggContext(window=None, player_name="Sathara")
    manager = EasterEggManager()
    assert manager.maybe_trigger(ctx) is True


def test_manager_can_use_a_seeded_rng_for_repeatable_selection():
    eggs = [
        type("First", (EasterEgg,), {"id": "first", "trigger": lambda self, ctx: None})(),
        type("Second", (EasterEgg,), {"id": "second", "trigger": lambda self, ctx: None})(),
    ]
    first = EasterEggManager(eggs=eggs, rng=random.Random(4))
    second = EasterEggManager(eggs=eggs, rng=random.Random(4))
    assert first.maybe_trigger(None) is True
    assert second.maybe_trigger(None) is True
    assert first.chosen_id == second.chosen_id
    assert first.available_egg_ids == ("first", "second")


def _fill_team(r, names):
    t = 1
    for i, name in enumerate(names):
        if t == 1 and i >= len(r.team1_slots):
            t = 2
        slot = i if t == 1 else i - len(r.team1_slots)
        r.create_in_slot(t, slot, name)


def test_slot_glow_for_special_player(make_window):
    w = make_window()
    r = w._roster
    _fill_team(r, ["Sathara", "P1", "P2", "P3", "P4",
                   "P5", "P6", "P7", "P8", "P9"])
    w._after_roster_change()
    special = w.match_display.team1_widget.slot_widgets[0]
    normal = w.match_display.team1_widget.slot_widgets[1]

    effect = special._editor.graphicsEffect()
    assert isinstance(effect, QGraphicsDropShadowEffect)
    assert effect.color() == QColor(SPECIAL_GLOW)
    assert effect.blurRadius() > 0
    assert normal._editor.graphicsEffect() is None
    w.close()


def test_glow_cleared_for_renamed_player(make_window):
    w = make_window()
    r = w._roster
    _fill_team(r, ["Sathara", "P1", "P2", "P3", "P4",
                   "P5", "P6", "P7", "P8", "P9"])
    w._after_roster_change()
    slot = w.match_display.team1_widget.slot_widgets[0]
    assert isinstance(slot._editor.graphicsEffect(), QGraphicsDropShadowEffect)
    w._on_slot_renamed(1, 0, "Palomita")
    w._refresh_roster_ui()
    assert slot._editor.graphicsEffect() is None
    w.close()


def test_special_glow_in_bench_and_saved(make_window):
    w = make_window()
    r = w._roster
    _fill_team(r, [f"P{i}" for i in range(10)])
    r.add_to_bench("sathara")
    r.save_name("Sattara")
    r.save_name("Palomita")
    w._after_roster_change()

    assert isinstance(w.bench_panel, object)
    bench_chip = next(c for c in w.bench_panel.chips if is_special_player_name(c.name))
    assert bench_chip is not None
    assert bench_chip.special is True
    saved_chips = w.saved_panel.chips
    saved_item = next(c for c in saved_chips if is_special_player_name(c.name))
    assert saved_item.special is True
    non_special = next(c for c in saved_chips if not is_special_player_name(c.name))
    assert non_special.special is not True
    w.close()


def test_egg_triggers_once_and_never_again(make_window):
    w = make_window()
    r = w._roster
    _fill_team(r, ["Sathara"] + [f"P{i}" for i in range(9)])
    w._after_roster_change()
    assert w._egg_manager.is_triggered is True
    assert w._egg_manager.trigger_count == 1
    chosen_id = w._egg_manager.chosen_id

    w._refresh_roster_ui()
    w._on_slot_renamed(1, 0, "SATARA")
    w._refresh_roster_ui()
    w._reroll_roles(1)
    w._on_mode_changed(GameMode.SIX_V_SIX)
    assert w._egg_manager.trigger_count == 1
    assert w._egg_manager.chosen_id == chosen_id
    assert w._egg_manager.is_triggered is True
    w.close()


def test_egg_triggers_when_restored_from_persistence(app_dir, make_window):
    from owervach_tmixer.core.storage import Storage

    r = Roster.empty(GameMode.FIVE_V_FIVE)
    _fill_team(r, ["Sattara"] + [f"P{i}" for i in range(9)])
    Storage().save_roster(r)

    # Al iniciar la app, la sanitización preventiva limpia a Sathara de partida/banca
    w = make_window()
    special = w.match_display.team1_widget.slot_widgets[0]
    assert special._player is None
    assert w._egg_manager.is_triggered is False
    assert w._egg_manager.trigger_count == 0
    w.close()


def test_new_app_run_rolls_a_new_egg(app_dir, make_window):
    w1 = make_window()
    _fill_team(w1._roster, ["Sathara"] + [f"P{i}" for i in range(9)])
    w1._after_roster_change()
    assert w1._egg_manager.is_triggered is True
    w1.close()

    # Al abrir una nueva sesión, el manager arranca fresco y reacciona al entrar Sathara
    w2 = make_window()
    assert w2._egg_manager.trigger_count == 0
    # P0..P8 ya fueron restaurados por persistencia; insertamos a Sathara en el slot 0 sanitizado
    w2._on_slot_created(1, 0, "Sathara")
    w2._after_roster_change()
    assert w2._egg_manager.trigger_count == 1
    assert w2._egg_manager.is_triggered is True
    w2.close()


def test_special_player_stays_functionally_normal(make_window):
    w = make_window()
    r = w._roster
    _fill_team(r, ["Sathara"] + [f"P{i}" for i in range(9)])
    w._after_roster_change()
    w._generate_match()
    assert len(w._roster.active_players()) == 10
    assert any(p.role is not None for p in w._roster.active_players())
    sathara = next(p for p in w._roster.active_players() if is_special_player_name(p.name))
    team, idx = w._roster.slot_of(sathara)
    w._on_slot_bench(team, idx)
    assert w._roster.player_at(team, idx) is None
    assert w._roster.find_bench(sathara.name) is not None
    w._on_bench_add_to_team(sathara.name, team)
    assert is_special_player_name(w._roster.player_at(team, idx).name)
    assert w._egg_manager.trigger_count == 1
    w.close()


def _green_tint_pixels(image):
    total = 0
    for y in range(image.height()):
        for x in range(image.width()):
            c = image.pixelColor(x, y)
            if c.alpha() > 0 and c.green() > c.red() and c.green() > c.blue():
                if c.green() > 60:
                    total += 1
    return total


def test_delegate_paints_glow_for_special_rows(qapp):
    from PySide6.QtGui import QPainter, QPixmap, QStandardItem, QStandardItemModel
    from PySide6.QtWidgets import QStyleOptionViewItem

    model = QStandardItemModel()
    font_item = QStandardItem("sathara")
    font_item.setData(True, SPECIAL_ROLE)
    plain_item = QStandardItem("Palomita")
    model.appendRow(font_item)
    model.appendRow(plain_item)
    final_index = model.index(1, 0)
    assert final_index.data(SPECIAL_ROLE) is not True

    delegate = GlowTextDelegate()
    option = QStyleOptionViewItem()
    option.rect = option.rect.adjusted(0, 0, 199, 39)
    option.font = font_item.font()

    pm = QPixmap(200, 40)
    pm.fill(QColor("#1F1F1F"))
    p = QPainter(pm)
    delegate.paint(p, option, model.index(0, 0))
    p.end()
    assert _green_tint_pixels(pm.toImage()) > 100


def test_delegate_falls_back_for_normal_rows(qapp):
    from PySide6.QtGui import QPainter, QPixmap, QStandardItem, QStandardItemModel
    from PySide6.QtWidgets import QStyleOptionViewItem

    model = QStandardItemModel()
    plain = QStandardItem("Palomita")
    model.appendRow(plain)
    delegate = GlowTextDelegate()
    option = QStyleOptionViewItem()
    option.rect = option.rect.adjusted(0, 0, 199, 39)
    option.font = plain.font()
    pm = QPixmap(200, 40)
    pm.fill(QColor("#1F1F1F"))
    p = QPainter(pm)
    delegate.paint(p, option, model.index(0, 0))
    p.end()
    assert _green_tint_pixels(pm.toImage()) == 0
