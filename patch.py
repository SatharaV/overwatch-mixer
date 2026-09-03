# /patch.py
"""Syncs the remaining 2 tests with the new default 'Auto' = False behavior."""

import os
import py_compile

base = os.path.dirname(os.path.abspath(__file__))


def patch_remaining_tests():
    path = os.path.join(base, "tests", "test_block2_dnd.py")
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    # 1. Actualizar test_estado_b_6v6_after_randomized
    old_test1 = '''def test_estado_b_6v6_after_randomized(make_window):
    w = make_window()
    w._on_mode_changed(GameMode.SIX_V_SIX)
    w.settings_manager.update_auto_roles(True)
    create_all(w, [f"P{i}" for i in range(12)])
    w._reroll_roles(1)
    assert [p.role for p in w._roster.team1_slots] != [
        Role.TANK, Role.TANK, Role.DAMAGE, Role.DAMAGE, Role.SUPPORT, Role.SUPPORT]
    w.randomize_roles_toggle.setChecked(False)
    assert [p.role for p in w._roster.team1_slots] == [
        Role.TANK, Role.TANK, Role.DAMAGE, Role.DAMAGE, Role.SUPPORT, Role.SUPPORT]
    w.close()'''

    new_test1 = '''def test_estado_b_6v6_after_randomized(make_window):
    w = make_window()
    w._on_mode_changed(GameMode.SIX_V_SIX)
    w.randomize_roles_toggle.setChecked(True)
    create_all(w, [f"P{i}" for i in range(12)])
    w._reroll_roles(1)
    assert [p.role for p in w._roster.team1_slots] != [
        Role.TANK, Role.TANK, Role.DAMAGE, Role.DAMAGE, Role.SUPPORT, Role.SUPPORT]
    w.randomize_roles_toggle.setChecked(False)
    assert [p.role for p in w._roster.team1_slots] == [
        Role.TANK, Role.TANK, Role.DAMAGE, Role.DAMAGE, Role.SUPPORT, Role.SUPPORT]
    w.close()'''

    if old_test1 in code:
        code = code.replace(old_test1, new_test1)

    # 2. Actualizar test_mix_roles_button_in_team_header_exists
    old_test2 = '''def test_mix_roles_button_in_team_header_exists(make_window):
    w = make_window()
    for widget in (w.match_display.team1_widget, w.match_display.team2_widget):
        assert "Roles" in widget.btn_mix_roles.text() or "Mezclar" in widget.btn_mix_roles.text()
        assert widget.btn_mix_roles.isEnabled() is True
    w.close()'''

    new_test2 = '''def test_mix_roles_button_in_team_header_exists(make_window):
    w = make_window()
    for widget in (w.match_display.team1_widget, w.match_display.team2_widget):
        assert "Roles" in widget.btn_mix_roles.text() or "Mezclar" in widget.btn_mix_roles.text()
        # Con Auto desactivado por defecto de fábrica, el botón inicia deshabilitado
        assert widget.btn_mix_roles.isEnabled() is False
    # Al activar Auto, se habilita
    w.randomize_roles_toggle.setChecked(True)
    for widget in (w.match_display.team1_widget, w.match_display.team2_widget):
        assert widget.btn_mix_roles.isEnabled() is True
    w.close()'''

    if old_test2 in code:
        code = code.replace(old_test2, new_test2)

    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    py_compile.compile(path, doraise=True)
    print("✅ test_block2_dnd.py: Los 2 tests sincronizados con el nuevo default de Auto = False.")


if __name__ == "__main__":
    patch_remaining_tests()