"""Tests for the main-page UI rework (saved-chip pool, map badge, bans panel)."""

from PySide6.QtCore import Qt

from owervach_tmixer.core.models import Role
from owervach_tmixer.main import QWIDGETSIZE_MAX
from owervach_tmixer.ui.styles import theme
from owervach_tmixer.ui.widgets.hero_widget import Hero


def _fill_teams(w, count=10):
    for i in range(count):
        w._roster.add_pending_to_team(f"P{i}")


def test_saved_pool_renders_chips_and_stays_visible(make_window):
    w = make_window()
    assert w.saved_panel.content.isHidden() is False

    w._roster.save_name("Fede")
    w._roster.save_name("Sathara")
    w._after_roster_change()

    chips = w.saved_panel.chips
    assert len(chips) == 2
    fede = next(c for c in chips if "Fede" in c.name)
    assert fede.special is False
    assert "Fede" in fede.label.text()
    sathara = next(c for c in chips if "Sathara" in c.name)
    assert sathara.special is True
    w.close()


def test_saved_double_click_fills_team_when_space(make_window):
    w = make_window()
    w._roster.save_name("Fede")
    w._after_roster_change()

    w.saved_panel.chip_activated.emit("Fede")

    assert w._roster.player_at(1, 0).name == "Fede"
    assert w._roster.find_saved("Fede") is not None
    w.close()


def test_saved_double_click_goes_to_bench_when_full(make_window):
    w = make_window()
    _fill_teams(w)
    w._roster.save_name("Solo")
    w._after_roster_change()

    w._on_saved_chip_activated("Solo")

    assert w._roster.find_bench("Solo") is not None
    assert w._roster.find_saved("Solo") is not None
    w.close()


def test_saved_drop_on_team_fills_first_free_slot(make_window):
    w = make_window()
    w._roster.save_name("Ana")
    w._after_roster_change()

    w._on_player_drop({"kind": "saved", "name": "Ana"}, 2, None)

    assert w._roster.player_at(2, 0).name == "Ana"
    w.close()


def test_saved_drop_on_full_team_warns(make_window, dialogs):
    w = make_window()
    _fill_teams(w)
    w._roster.save_name("Extra")
    w._after_roster_change()

    w._on_player_drop({"kind": "saved", "name": "Extra"}, 2, None)

    assert any(kind == "warning" for kind, _, _ in dialogs)
    assert w._roster.find_bench("Extra") is None
    assert not any(p.name == "Extra" for p in w._roster.active_players())
    w.close()


def test_saved_drop_on_bench(make_window):
    w = make_window()
    w._roster.save_name("Ana")
    w._after_roster_change()

    w._on_drop_to_bench({"kind": "saved", "name": "Ana"})

    assert w._roster.find_bench("Ana") is not None
    w.close()


def _portrait_tips(w):
    return {lab.toolTip() for lab in _live_portraits(w)}


def _live_portraits(w):
    labels = []
    layout = w.bans_panel.portraits_layout
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item is not None and item.widget() is not None:
            labels.append(item.widget())
    return labels


def test_bans_panel_reflects_current_bans(make_window):
    w = make_window()
    assert w.bans_panel.portrait_count() == 0
    assert w.bans_panel.scroll.isHidden() is False

    w._on_bans_changed({"Ana", "Bap"})

    assert w.bans_panel.portrait_count() == 2
    assert "HÉROES BANEADOS (2)" in w.bans_panel.title_label.text()
    assert {"Ana", "Bap"} <= _portrait_tips(w)
    w.close()


def test_bans_panel_clears_when_no_bans(make_window):
    w = make_window()
    w._on_bans_changed({"Ana"})
    assert w.bans_panel.portrait_count() == 1

    w._on_bans_changed(set())

    assert w.bans_panel.portrait_count() == 0
    assert "HÉROES BANEADOS (0)" in w.bans_panel.title_label.text()
    w.close()


def test_bans_panel_follows_hero_widget_ban_toggle(make_window):
    w = make_window()
    w.hero_widget.set_heroes(
        [
            Hero("Ana", Role.SUPPORT),
            Hero("Bap", Role.SUPPORT),
        ]
    )
    w.hero_widget.set_banned({"Ana", "Bap"})

    assert w.bans_panel.portrait_count() == 2
    assert {"Ana", "Bap"} <= _portrait_tips(w)
    w.close()


def test_bans_panel_always_visible_when_empty(make_window):
    w = make_window()
    assert w.bans_panel.isHidden() is False
    assert w.bans_panel.scroll.isHidden() is False
    w.close()


def test_bans_panel_collapses_and_expands(make_window):
    w = make_window()
    w._on_bans_changed({"Ana", "Bap"})

    w.bans_panel.toggle_btn.click()
    assert w.bans_panel.scroll.isHidden()
    assert w.bans_panel.minimumHeight() == 44

    w.bans_panel.toggle_btn.click()
    assert w.bans_panel.scroll.isHidden() is False
    w.close()


def test_bans_panel_wraps_many_heroes(make_window):
    w = make_window()
    names = [f"H{i}" for i in range(15)]
    w.bans_panel.set_banned(names)

    assert w.bans_panel.portrait_count() == 15
    w.close()


def test_bans_panel_portrait_size_resizes(make_window):
    w = make_window()
    w._on_bans_changed({"Ana", "Bap"})

    w.bans_panel.set_portrait_size(16)
    assert w.bans_panel.portrait_size() == 16

    w.bans_panel.set_portrait_size(32)
    assert w.bans_panel.portrait_size() == 32
    w.close()


def test_settings_dialog_saves_portrait_size(make_window):
    from owervach_tmixer.main import SettingsDialog

    w = make_window()
    dlg = SettingsDialog(w, w.settings_manager, w.shuffle_history)
    dlg.spin_portrait_size.setValue(48)
    dlg.accept()

    assert w.settings_manager.settings.ban_portrait_size == 48
    assert w.bans_panel.portrait_size() == 48
    w.close()


def test_bans_panel_shows_all_bans_without_manual_collapse(make_window, qapp):
    w = make_window()
    w.show()
    qapp.processEvents()

    w._on_bans_changed({f"H{i}" for i in range(30)})
    qapp.processEvents()

    assert w.bans_panel.portrait_count() == 30

    w._on_bans_changed(set())
    qapp.processEvents()
    assert w.bans_panel.portrait_count() == 0
    w.close()


def test_bans_panel_syncs_when_returning_to_main_tab(make_window, qapp):
    w = make_window()
    w.show()
    qapp.processEvents()
    picker_index = w.tabs.indexOf(w.hero_widget)

    w.tabs.setCurrentIndex(picker_index)
    qapp.processEvents()
    w._on_bans_changed(set())
    w._on_bans_changed({f"H{i}" for i in range(25)})
    qapp.processEvents()

    w.tabs.setCurrentIndex(0)
    qapp.processEvents()

    assert w.bans_panel.portrait_count() == 25
    w.close()


def test_splitter_handles_are_visible_in_global_stylesheet():
    qss = theme.build_stylesheet()
    assert "QSplitter::handle" in qss


def test_no_opaque_boxes_behind_words(make_window):
    w = make_window()
    bench_qss = w.bench_panel.styleSheet()
    assert "background-color: transparent" in bench_qss
    assert "background-color: #2F2F2F" not in bench_qss
    w.close()


def _slot_fill(w, count=10, per_team=5):
    for i, name in enumerate([f"P{j}" for j in range(count)]):
        w._on_slot_created((i // per_team) + 1, i % per_team, name)


def test_map_selected_in_tab_without_match_is_safe(make_window):
    w = make_window()
    assert w.map_widget.list_widget.count() > 0

    w.map_widget.list_widget.setCurrentRow(0)

    assert w._current_match is None
    w.close()


def test_generate_match_syncs_map_tab(make_window):
    w = make_window()
    _slot_fill(w)
    w._generate_match()

    m = w._current_match.map
    if m:
        assert w.map_widget.current_map_name.text() == m.name
    w.close()


def test_map_selected_in_tab_updates_live_match(make_window):
    w = make_window()
    _slot_fill(w)
    w._generate_match()

    row = (w.map_widget.list_widget.currentRow() + 1) % w.map_widget.list_widget.count()
    expected = w.map_widget.list_widget.item(row).data(Qt.UserRole)

    w.map_widget.list_widget.setCurrentRow(row)

    assert w._current_match.map.name == expected
    assert w.map_widget.current_map_name.text() == expected
    w.close()
