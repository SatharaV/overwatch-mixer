"""Standalone executable & AppImage compiler for Overwatch Team Mixer (Cross-Platform)."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENTRY = ROOT / "owervach_tmixer" / "main.py"
APP_NAME = "Overwatch-Mixer"
IS_WINDOWS = platform.system() == "Windows"
SPEC_FILE = ROOT / f"{APP_NAME}.spec"


def get_icon_path(assets_dir: Path) -> Path:
    if IS_WINDOWS:
        ico = assets_dir / "overwatch-logo-white.ico"
        return ico if ico.exists() else assets_dir / "icon.svg"
    png = assets_dir / "overwatch-logo-white.png"
    if png.exists():
        return png
    svg = assets_dir / "overwatch-logo-white.svg"
    return svg if svg.exists() else assets_dir / "icon.svg"


def create_surgical_spec():
    assets_dir = ROOT / "owervach_tmixer" / "assets"
    icon_path = get_icon_path(assets_dir)
    icon_entry = f"icon=r'{icon_path}'," if icon_path.exists() else "icon=None,"

    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import platform
from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(r'{ROOT}')
ENTRY = ROOT / 'owervach_tmixer' / 'main.py'
IS_WINDOWS = platform.system() == 'Windows'

UNWANTED_LIBS = (
    'webengine', 'quick', 'qml', '3d', 'virtualkeyboard', 'pdf',
    'location', 'positioning', 'bluetooth', 'nfc', 'sensors', 'sql',
    'test', 'designer', 'uitools', 'remoteobjects', 'scxml', 'serialport',
    'webchannel', 'websockets',
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
        'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
        'PySide6.QtSvg', 'PySide6.QtMultimedia', 'platformdirs', 'owervach_tmixer',
    ] + collect_submodules('owervach_tmixer'),
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'pydoc'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

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


def get_or_download_appimagetool() -> Path | None:
    system_tool = shutil.which("appimagetool")
    if system_tool:
        return Path(system_tool)

    cache_dir = Path.home() / ".cache" / "appimage"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached_tool = cache_dir / "appimagetool-x86_64.AppImage"

    if not cached_tool.exists() or cached_tool.stat().st_size < 1000000:
        official_urls = [
            "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage",
            "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage",
        ]
        print("⬇️ Descargando appimagetool oficial de GitHub (sin AUR)...")
        success = False

        if shutil.which("curl"):
            for url in official_urls:
                try:
                    subprocess.run(["curl", "-L", "-s", "-o", str(cached_tool), url], check=True)
                    if cached_tool.exists() and cached_tool.stat().st_size > 1000000:
                        success = True
                        break
                except Exception:
                    continue

        if not success:
            import urllib.request
            for url in official_urls:
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req) as resp, open(cached_tool, "wb") as out:
                        out.write(resp.read())
                    if cached_tool.exists() and cached_tool.stat().st_size > 1000000:
                        success = True
                        break
                except Exception:
                    continue

        if success:
            cached_tool.chmod(0o755)
            print("✅ appimagetool oficial verificado y listo en ~/.cache/appimage/.")
        else:
            print("⚠️ No se pudo descargar automáticamente.")
            return None

    return cached_tool


def build_appdir_and_appimage(target_bin: Path):
    appdir = ROOT / "dist" / "AppDir"
    if appdir.exists():
        shutil.rmtree(appdir)

    usr_bin = appdir / "usr" / "bin"
    usr_bin.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target_bin, usr_bin / APP_NAME)

    assets_dir = ROOT / "owervach_tmixer" / "assets"
    png_icon = assets_dir / "overwatch-logo-white.png"
    icon_dest = appdir / "owervach-tmixer.png"
    if png_icon.exists():
        shutil.copy2(png_icon, icon_dest)
        icons_dir = appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps"
        icons_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(png_icon, icons_dir / "owervach-tmixer.png")

    from owervach_tmixer import __version__
    desktop_content = f"""[Desktop Entry]
Type=Application
Name=Overwatch Team Mixer
GenericName=Team Organizer & MMR Mixer
Comment=El orquestador definitivo de partidas personalizadas para Overwatch
Exec=Overwatch-Mixer
Icon=owervach-tmixer
Categories=Game;Utility;
Terminal=false
StartupWMClass=owervach-tmixer
X-AppImage-Version={__version__}
"""
    (appdir / "owervach-tmixer.desktop").write_text(desktop_content, encoding="utf-8")

    apprun_content = """#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/Overwatch-Mixer" "$@"
"""
    apprun = appdir / "AppRun"
    apprun.write_text(apprun_content, encoding="utf-8")
    apprun.chmod(0o755)

    print(f"📦 Estructura AppDir lista en: {appdir}")

    tool_path = get_or_download_appimagetool()
    if tool_path and tool_path.exists():
        out_appimage = ROOT / "dist" / f"{APP_NAME}-x86_64.AppImage"
        print("🚀 Empaquetando AppImage oficial...")
        env = os.environ.copy()
        env["ARCH"] = "x86_64"
        env["APPIMAGE_EXTRACT_AND_RUN"] = "1"
        subprocess.run([str(tool_path), str(appdir), str(out_appimage)], check=True, env=env)
        print("\n=======================================================")
        print("✨ ¡APPIMAGE GENERADO CON ÉXITO PARA GEARLEVER!")
        print(f"📦 Archivo: {out_appimage}")
        print("=======================================================\n")


def main() -> int:
    system_name = platform.system()
    print("\n=======================================================")
    print("🎮 OVERWATCH TEAM MIXER — COMPILADOR STANDALONE")
    print("=======================================================")
    print(f"🖥️  Sistema: {system_name} ({platform.machine()})")

    if not ENTRY.exists():
        print(f"❌ Error: No se encontró {ENTRY}")
        return 1

    create_surgical_spec()

    cmd = [sys.executable, "-m", "PyInstaller", "--clean", str(SPEC_FILE)]
    try:
        subprocess.run(cmd, check=True, cwd=ROOT)
    except Exception as exc:
        print(f"\n❌ Falló la compilación: {exc}")
        return 1

    out_ext = ".exe" if IS_WINDOWS else ""
    target_bin = ROOT / "dist" / f"{APP_NAME}{out_ext}"

    if target_bin.exists():
        size_mb = target_bin.stat().st_size / (1024 * 1024)
        print(f"\n✨ Binario compilado: {target_bin} ({size_mb:.2f} MB)")
        if not IS_WINDOWS:
            build_appdir_and_appimage(target_bin)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
