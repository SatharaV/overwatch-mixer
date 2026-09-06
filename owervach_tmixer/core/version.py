"""Single Source of Truth (SSOT) for application version and release metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VersionInfo:
    version: str = "1.2.0"
    release_type: str = "RELEASE"
    status: str = "Producción Estable"
    channel: str = "Stable"
    codename: str = "Overlord"
    build_date: str = "2026-09-06"

    @property
    def badge(self) -> str:
        return f"v{self.version} {self.release_type}".strip()

    @property
    def full_title(self) -> str:
        return f"Owervach TMixer v{self.version}"


_CACHED_VERSION: VersionInfo | None = None


def get_version_info() -> VersionInfo:
    """Loads version metadata from data/version.json with immutable caching and safe fallback."""
    global _CACHED_VERSION
    if _CACHED_VERSION is not None:
        return _CACHED_VERSION

    candidates = [
        Path(__file__).resolve().parent.parent / "data" / "version.json",
        Path(__file__).resolve().parent / "data" / "version.json",
        Path("owervach_tmixer/data/version.json"),
        Path("data/version.json"),
    ]

    for candidate in candidates:
        if candidate.exists():
            try:
                raw = json.loads(candidate.read_text(encoding="utf-8"))
                _CACHED_VERSION = VersionInfo(
                    version=str(raw.get("version", "1.2.0")),
                    release_type=str(raw.get("release_type", "RELEASE")),
                    status=str(raw.get("status", "Producción Estable")),
                    channel=str(raw.get("channel", "Stable")),
                    codename=str(raw.get("codename", "Overlord")),
                    build_date=str(raw.get("build_date", "2026-09-06")),
                )
                return _CACHED_VERSION
            except Exception:
                pass

    _CACHED_VERSION = VersionInfo()
    return _CACHED_VERSION
