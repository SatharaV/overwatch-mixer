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
    assert w.bans_panel.minimumHeight() == 74

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


def _draft_live_portraits(panel, team: int):
    layout = panel.draft_t1_layout if team == 1 else panel.draft_t2_layout
    labels = []
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item is not None and item.widget() is not None:
            labels.append(item.widget())
    return labels


def test_bans_panel_switches_to_draft_mode(make_window):
    w = make_window()
    assert w.bans_panel.current_mode() == "bans"
    assert w.bans_panel.stack.currentIndex() == 0

    w.bans_panel.btn_mode_draft.click()

    assert w.bans_panel.current_mode() == "draft"
    assert w.bans_panel.stack.currentIndex() == 1
    assert "DRAFT DE HÉROES" in w.bans_panel.title_label.text()
    assert not w.bans_panel.draft_empty_label.isHidden()
    assert w.settings_manager.settings.hero_restriction_mode == "draft"
    w.close()


def test_bans_panel_draft_mode_switch_back_to_bans(make_window):
    w = make_window()
    w.bans_panel.set_mode("draft", emit=False)
    w.bans_panel.btn_mode_bans.click()

    assert w.bans_panel.current_mode() == "bans"
    assert w.bans_panel.stack.currentIndex() == 0
    assert w.settings_manager.settings.hero_restriction_mode == "bans"
    w.close()


def test_draft_persists_when_switching_modes(make_window):
    w = make_window()
    for i in range(10):
        w._on_slot_created((i // 5) + 1, i % 5, f"P{i}")
    w.settings_manager.settings.hero_restriction_mode = "draft"
    w._generate_match()
    t1 = list(w._current_match.team1_draft)
    t2 = list(w._current_match.team2_draft)
    assert len(t1) == 5 and len(t2) == 5

    # BANS -> DRAFT -> BANS -> DRAFT: nada se borra en el Match ni el panel
    w.bans_panel.btn_mode_bans.click()
    w.bans_panel.btn_mode_draft.click()

    assert w._current_match.team1_draft == t1
    assert w._current_match.team2_draft == t2
    assert w.bans_panel._draft_t1 == t1
    assert w.bans_panel._draft_t2 == t2
    assert len(_draft_live_portraits(w.bans_panel, 1)) == 5
    assert len(_draft_live_portraits(w.bans_panel, 2)) == 5
    w.close()


def test_mode_switch_does_not_clear_match_bans(make_window):
    w = make_window()
    for i in range(10):
        w._on_slot_created((i // 5) + 1, i % 5, f"P{i}")
    w.settings_manager.settings.hero_restriction_mode = "bans"
    w._generate_match()
    saved = list(w._current_match.bans)

    w.bans_panel.btn_mode_draft.click()
    w.bans_panel.btn_mode_bans.click()

    assert w._current_match.bans == saved
    w.close()


def test_draft_mode_auto_generates_when_match_has_players(make_window):
    w = make_window()
    for i in range(10):
        w._on_slot_created((i // 5) + 1, i % 5, f"P{i}")
    w.settings_manager.settings.hero_restriction_mode = "bans"
    w._generate_match()
    assert w._current_match.team1_draft == []

    # Cambiar a Draft con partida activa: genera el draft inicial automáticamente
    w.bans_panel.btn_mode_draft.click()

    assert len(w._current_match.team1_draft) == 5
    assert len(w._current_match.team2_draft) == 5
    assert w.bans_panel.draft_empty_label.isHidden()
    w.close()


def test_draft_mode_without_players_shows_empty_label(make_window):
    w = make_window()
    w.bans_panel.btn_mode_draft.click()

    assert w._current_match is None
    assert not w.bans_panel.draft_empty_label.isHidden()
    w.close()


def test_draft_panel_height_is_275_without_scrollbar(make_window, qapp):
    from PySide6.QtCore import Qt

    w = make_window()
    for i in range(10):
        w._on_slot_created((i // 5) + 1, i % 5, f"P{i}")
    w.settings_manager.settings.hero_restriction_mode = "draft"
    w._generate_match()

    assert w.bans_panel.minimumHeight() == 275
    assert w.bans_panel.maximumHeight() == 275
    assert w.bans_panel.draft_scroll.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    w.close()


def test_generate_match_in_draft_mode_populates_teams(make_window):
    w = make_window()
    for i in range(10):
        w._on_slot_created((i // 5) + 1, i % 5, f"P{i}")
    w.settings_manager.settings.hero_restriction_mode = "draft"

    w._generate_match()

    m = w._current_match
    assert m is not None
    assert len(m.team1_draft) == 5
    assert len(m.team2_draft) == 5
    assert m.bans == []
    assert w.bans_panel.current_mode() == "draft"
    assert len(_draft_live_portraits(w.bans_panel, 1)) == 5
    assert len(_draft_live_portraits(w.bans_panel, 2)) == 5
    assert "GATITOS" in w.bans_panel.label_t1.text()
    assert "PERRITAS" in w.bans_panel.label_t2.text()
    w.close()


def test_generate_match_in_bans_mode_clears_draft(make_window):
    w = make_window()
    for i in range(10):
        w._on_slot_created((i // 5) + 1, i % 5, f"P{i}")
    w.settings_manager.settings.hero_restriction_mode = "bans"

    w._generate_match()

    m = w._current_match
    assert m.team1_draft == [] and m.team2_draft == []
    w.close()


def test_bans_panel_randomize_button_rerolls_draft(make_window):
    w = make_window()
    for i in range(10):
        w._on_slot_created((i // 5) + 1, i % 5, f"P{i}")
    w.settings_manager.settings.hero_restriction_mode = "draft"
    w._generate_match()
    first_t1 = list(w._current_match.team1_draft)

    w.bans_panel.btn_randomize.click()

    assert len(w._current_match.team1_draft) == 5
    assert w._current_match.team1_draft != first_t1 or w._current_match.team2_draft != first_t1
    assert len(_draft_live_portraits(w.bans_panel, 1)) == 5
    w.close()


def test_bans_panel_pill_tabs_are_checkable_and_exclusive(make_window):
    w = make_window()
    # Píldoras estilo dock: checkable, mutuamente excluyentes
    assert w.bans_panel.btn_mode_bans.isCheckable()
    assert w.bans_panel.btn_mode_draft.isCheckable()
    assert w.bans_panel.btn_mode_bans.height() <= 30
    assert w.bans_panel.current_mode() == "bans"
    assert w.bans_panel.btn_mode_bans.isChecked()

    w.bans_panel.btn_mode_draft.click()
    assert w.bans_panel.btn_mode_draft.isChecked()
    assert not w.bans_panel.btn_mode_bans.isChecked()

    w.bans_panel.btn_mode_bans.click()
    assert w.bans_panel.btn_mode_bans.isChecked()
    assert not w.bans_panel.btn_mode_draft.isChecked()
    w.close()


def test_game_mode_switch_updates_draft_caps_on_the_fly(make_window):
    from owervach_tmixer.core.models import GameMode

    w = make_window()
    s = w.settings_manager.settings
    s.draft_heroes_per_team = 5
    s.draft_max_tank = 1

    w._on_mode_changed(GameMode.SIX_V_SIX)

    assert s.draft_heroes_per_team == 6
    assert s.draft_max_tank == 2
    assert s.draft_max_damage == 2
    assert s.draft_max_support == 2

    w._on_mode_changed(GameMode.FIVE_V_FIVE)

    assert s.draft_heroes_per_team == 5
    assert s.draft_max_tank == 1
    assert s.draft_max_damage == 2
    assert s.draft_max_support == 2
    w.close()


def test_game_mode_switch_rerolls_existing_draft(make_window):
    from owervach_tmixer.core.models import GameMode

    w = make_window()
    for i in range(10):
        w._on_slot_created((i // 5) + 1, i % 5, f"P{i}")
    w.settings_manager.settings.hero_restriction_mode = "draft"
    w._generate_match()
    assert len(w._current_match.team1_draft) == 5

    w._on_mode_changed(GameMode.SIX_V_SIX)

    assert len(w._current_match.team1_draft) == 6
    assert len(w._current_match.team2_draft) == 6
    assert len(_draft_live_portraits(w.bans_panel, 1)) == 6
    w.close()


def test_copy_to_discord_shows_draft_block(make_window, monkeypatch):
    from PySide6.QtWidgets import QApplication

    w = make_window()
    for i in range(10):
        w._on_slot_created((i // 5) + 1, i % 5, f"P{i}")
    w.settings_manager.settings.hero_restriction_mode = "draft"
    w._generate_match()

    captured = {}
    monkeypatch.setattr(
        QApplication, "clipboard",
        lambda: type("C", (), {"setText": staticmethod(lambda t: captured.setdefault("text", t))})(),
    )
    w.match_display._copy_for_discord()

    text = captured["text"]
    assert "DRAFT OBLIGATORIO DE HÉROES" in text
    assert "🔹 **Gatitos:**" in text
    assert "🔸 **Perritas:**" in text
    assert "Baneos:" not in text
    joined = ", ".join(w._current_match.team1_draft)
    assert joined and joined in text
    w.close()


def test_copy_to_discord_keeps_bans_format(make_window, monkeypatch):
    from PySide6.QtWidgets import QApplication

    w = make_window()
    for i in range(10):
        w._on_slot_created((i // 5) + 1, i % 5, f"P{i}")
    w.settings_manager.settings.hero_restriction_mode = "bans"
    w._generate_match()

    captured = {}
    monkeypatch.setattr(
        QApplication, "clipboard",
        lambda: type("C", (), {"setText": staticmethod(lambda t: captured.setdefault("text", t))})(),
    )
    w.match_display._copy_for_discord()

    text = captured["text"]
    assert "DRAFT OBLIGATORIO" not in text
    m = w._current_match
    if m.bans:
        assert "⛔ **Baneos:**" in text
    w.close()


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
