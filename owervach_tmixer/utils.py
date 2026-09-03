"""Runtime resource-path helpers (PyInstaller-safe)."""

from __future__ import annotations

import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent


def get_resource_path(relative_path: str | Path) -> Path:
    """Resolve a shipped resource path for dev and PyInstaller bundles.

    The logical root is the ``owervach_tmixer`` package in both modes: inside
    a PyInstaller bundle resources live at ``sys._MEIPASS/owervach_tmixer/...``
    (where ``--add-data`` places them), and in development they live inside the
    package itself. ``relative_path`` is always relative to the package root,
    e.g. ``"assets/settings.svg"`` or ``"data/default_maps.json"``.
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "owervach_tmixer" / relative_path
    return _PACKAGE_ROOT / relative_path
