"""Standalone executable compiler for Overwatch Team Mixer — Preserves Handcrafted IcoFX Icon."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENTRY = ROOT / "owervach_tmixer" / "main.py"
APP_NAME = "Overwatch-Mixer"
IS_WINDOWS = platform.system() == "Windows"
SPEC_FILE = ROOT / f"{APP_NAME}.spec"


def get_white_icon_path(assets_dir: Path) -> Path:
    """Prioritizes user's handcrafted IcoFX overwatch-logo-white.ico (NEVER overwrites it)."""
    ico_white = assets_dir / "overwatch-logo-white.ico"
    png_white = assets_dir / "overwatch-logo-white.png"
    svg_white = assets_dir / "overwatch-logo-white.svg"

    # 1. Si el usuario ya creó su .ico en IcoFX, usarlo intocable
    if ico_white.exists():
        print(f"💎 Usando icono maestro artesanal IcoFX: {ico_white.name}")
        return ico_white

    # 2. Si no existiera, fallback de emergencia
    if IS_WINDOWS:
        fallback = assets_dir / "overwatch-logo.ico"
    else:
        fallback = png_white if png_white.exists() else assets_dir / "overwatch-logo.png"

    return fallback if fallback.exists() else assets_dir / "icon.svg"


def create_surgical_spec():
    assets_dir = ROOT / "owervach_tmixer" / "assets"
    icon_path = get_white_icon_path(assets_dir)

    icon_entry = f"icon=r'{icon_path}'," if icon_path.exists() else "icon=None,"

    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import platform
from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(r'{ROOT}')
ENTRY = ROOT / 'owervach_tmixer' / 'main.py'
IS_WINDOWS = platform.system() == 'Windows'

UNWANTED_LIBS = (
    'webengine',
    'quick',
    'qml',
    '3d',
    'virtualkeyboard',
    'pdf',
    'location',
    'positioning',
    'bluetooth',
    'nfc',
    'sensors',
    'sql',
    'test',
    'designer',
    'uitools',
    'remoteobjects',
    'scxml',
    'serialport',
    'webchannel',
    'websockets',
)

def is_unwanted(path_str):
    if not path_str:
        return False
    low = str(path_str).lower()
    return any(kw in low for kw in UNWANTED_LIBS)

a = Analysis(
    [str(ENTRY)],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'owervach_tmixer' / 'assets'), 'owervach_tmixer/assets'),
        (str(ROOT / 'owervach_tmixer' / 'data'), 'owervach_tmixer/data'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtSvg',
        'PySide6.QtMultimedia',
        'platformdirs',
        'owervach_tmixer',
    ] + collect_submodules('owervach_tmixer'),
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'pydoc'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

# ✂️ CIRUGÍA BINARIA: Extracción de librerías Qt no utilizadas
a.binaries = [b for b in a.binaries if not is_unwanted(b[0]) and not is_unwanted(b[1])]
a.datas = [d for d in a.datas if not is_unwanted(d[0]) and not is_unwanted(d[1])]

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=not IS_WINDOWS,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {icon_entry}
)
"""
    SPEC_FILE.write_text(spec_content, encoding="utf-8")


def main() -> int:
    system_name = platform.system()
    print(f"\n=======================================================")
    print(f"🎮 OVERWATCH TEAM MIXER — STANDALONE ULTRA-LIGHT")
    print(f"=======================================================")
    print(f"🖥️  Sistema: {system_name} ({platform.machine()})")
    print(f"✂️  Filtro: Binary-level TOC pruning activado")
    print(f"🔊 Audio FX: PySide6.QtMultimedia habilitado")
    print(f"💎 Logo: overwatch-logo-white.ico (IcoFX protegido)")
    print(f"-------------------------------------------------------")

    if not ENTRY.exists():
        print(f"❌ Error: No se encontró el archivo de entrada: {ENTRY}")
        return 1

    print("📄 Generando receta .spec quirúrgica...")
    create_surgical_spec()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        str(SPEC_FILE),
    ]

    print("🚀 Compilando binario con icono IcoFX...")
    try:
        subprocess.run(cmd, check=True, cwd=ROOT)
    except Exception as exc:
        print(f"\n❌ Falló la compilación: {exc}")
        return 1

    out_ext = ".exe" if IS_WINDOWS else ""
    target_bin = ROOT / "dist" / f"{APP_NAME}{out_ext}"

    if target_bin.exists():
        size_mb = target_bin.stat().st_size / (1024 * 1024)
        print(f"\n=======================================================")
        print(f"✨ ¡COMPILACIÓN ULTRA-LIGERA FINALIZADA!")
        print(f"📦 Binario Generado: {target_bin}")
        print(f"📊 Peso Final:       {size_mb:.2f} MB")
        print(f"=======================================================\n")
        return 0
    else:
        print(f"\n⚠️ No se encontró el binario en dist/")
        return 1


if __name__ == "__main__":
    sys.exit(main())
