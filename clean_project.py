#!/usr/bin/env python3
"""Project Sanitation Script: Purges all __pycache__, .pytest_cache, temporary files,
and build artifacts to prepare a pristine ZIP for Windows and clean Git commits.
"""

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

DIRS_TO_REMOVE = [
    "__pycache__",
    ".pytest_cache",
    "build",
    "dist/AppDir",
    ".mypy_cache",
    ".ruff_cache",
]

PATTERNS_TO_REMOVE = [
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.tmp",
    "*.corrupted.bak*",
    ".DS_Store",
    "Thumbs.db",
]


def clean_project():
    print("\n=======================================================")
    print("🧹 LIMPIEZA QUIRÚRGICA DEL PROYECTO (PRE-ZIP & GIT)")
    print("=======================================================")

    deleted_files = 0
    deleted_dirs = 0

    # 1. Eliminar directorios de caché recursivamente
    for dir_name in DIRS_TO_REMOVE:
        for found_dir in ROOT.rglob(dir_name):
            if found_dir.is_dir():
                try:
                    shutil.rmtree(found_dir, ignore_errors=True)
                    print(f"  🗑️ Directorio purgado: {found_dir.relative_to(ROOT)}")
                    deleted_dirs += 1
                except Exception as e:
                    print(f"  ⚠️ No se pudo eliminar {found_dir}: {e}")

    # 2. Eliminar archivos temporales por patrón
    for pattern in PATTERNS_TO_REMOVE:
        for found_file in ROOT.rglob(pattern):
            if found_file.is_file():
                try:
                    found_file.unlink(missing_ok=True)
                    deleted_files += 1
                except Exception as e:
                    print(f"  ⚠️ No se pudo eliminar {found_file}: {e}")

    # 3. Eliminar patch.py residual para no arrastrarlo a Windows
    patch_file = ROOT / "patch.py"
    if patch_file.exists():
        patch_file.unlink(missing_ok=True)
        print("  🗑️ patch.py temporal eliminado.")
        deleted_files += 1

    print("\n-------------------------------------------------------")
    print(f"✨ ¡Proyecto 100% limpio! ({deleted_dirs} carpetas y {deleted_files} archivos purgados)")
    print("📦 Ya puedes comprimir tu carpeta a .ZIP con total seguridad.")
    print("=======================================================\n")


if __name__ == "__main__":
    clean_project()
