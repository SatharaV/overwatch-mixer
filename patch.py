# /patch.py
"""Ajuste final en test_new_app_run_rolls_a_new_egg para el 100% en verde."""

import os
import py_compile

base = os.path.dirname(os.path.abspath(__file__))


def patch_final_test():
    path = os.path.join(base, "tests", "test_easter_eggs.py")
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    old_fn = '''    # Al abrir una nueva sesión, el manager arranca fresco y reacciona al entrar Sathara
    w2 = make_window()
    assert w2._egg_manager.trigger_count == 0
    _fill_team(w2._roster, ["Sathara"] + [f"P{i}" for i in range(9)])
    w2._after_roster_change()
    assert w2._egg_manager.trigger_count == 1
    assert w2._egg_manager.is_triggered is True
    w2.close()'''

    new_fn = '''    # Al abrir una nueva sesión, el manager arranca fresco y reacciona al entrar Sathara
    w2 = make_window()
    assert w2._egg_manager.trigger_count == 0
    # P0..P8 ya fueron restaurados por persistencia; insertamos a Sathara en el slot 0 sanitizado
    w2._on_slot_created(1, 0, "Sathara")
    w2._after_roster_change()
    assert w2._egg_manager.trigger_count == 1
    assert w2._egg_manager.is_triggered is True
    w2.close()'''

    if old_fn in code:
        code = code.replace(old_fn, new_fn)
    else:
        # Reemplazo alternativo por si varió el espaciado
        import re
        pattern = r"    # Al abrir una nueva sesión.*?(?=w2\.close\(\))w2\.close\(\)"
        code = re.sub(pattern, new_fn, code, flags=re.DOTALL)

    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    py_compile.compile(path, doraise=True)
    print("✅ test_easter_eggs.py: Sincronización final completada.")


if __name__ == "__main__":
    patch_final_test()