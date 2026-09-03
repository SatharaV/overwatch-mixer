"""Esports Audio FX engine for ultra-rare hero ban voice line easter eggs."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QUrl
from owervach_tmixer.ui.widgets.hero_widget import resolve_canonical_name
from owervach_tmixer.utils import get_resource_path

try:
    from PySide6.QtMultimedia import QSoundEffect
    _MULTIMEDIA_AVAILABLE = True
except ImportError:
    _MULTIMEDIA_AVAILABLE = False

_active_sound: Optional[QSoundEffect] = None

HERO_AUDIO_DIRS = {
    "cassidy": "cassidy",
    "cole cassidy": "cassidy",
    "mcree": "cassidy",
    "mccree": "cassidy",
    "genji": "genji",
    "juno": "juno",
    "mercy": "mercy",
    "mersi": "mercy",
}


def play_hero_ban_sound(hero_name: str) -> bool:
    """Plays a randomized .wav voice line for the given hero if available."""
    global _active_sound
    if not _MULTIMEDIA_AVAILABLE:
        return False

    canonical = resolve_canonical_name(hero_name).strip().casefold()
    sub_dir = HERO_AUDIO_DIRS.get(canonical) or HERO_AUDIO_DIRS.get(hero_name.strip().casefold())
    if not sub_dir:
        return False

    audio_folder = get_resource_path(f"assets/Audios/{sub_dir}")
    if not audio_folder.exists():
        return False

    wav_files = [f for f in audio_folder.glob("*.wav") if f.is_file()]
    if not wav_files:
        return False

    chosen_wav = random.choice(wav_files)

    try:
        if _active_sound is not None:
            _active_sound.stop()
            _active_sound.deleteLater()

        sound = QSoundEffect()
        sound.setSource(QUrl.fromLocalFile(str(chosen_wav)))
        sound.setVolume(0.50)
        sound.play()
        _active_sound = sound
        return True
    except Exception:
        return False


def play_ban_sound_for_pool(banned_names: list[str] | set[str], window: object | None = None, trigger_chance: float = 0.05) -> bool:
    from owervach_tmixer.ui.easter_eggs import is_sathara_in_match
    # Si Sathara no está en un equipo activo ni en Zona de Espera, silencio total
    if not is_sathara_in_match(window):
        return False
    """Triggered from main screen: 5% rare chance, strictly picks 1 single hero if multiple qualify."""
    # 1. Filtro estricto de rareza (5% de probabilidad)
    if random.random() > trigger_chance:
        return False

    # 2. Filtrar todos los héroes baneados que cuentan con audio
    eligible_heroes: list[str] = []
    for name in banned_names:
        canonical = resolve_canonical_name(name).strip().casefold()
        raw_folded = name.strip().casefold()
        if canonical in HERO_AUDIO_DIRS or raw_folded in HERO_AUDIO_DIRS:
            eligible_heroes.append(name)

    if not eligible_heroes:
        return False

    # 3. Si cayeron 2 o más con audio, seleccionar exactamente a 1 solo por azar
    chosen_hero = random.choice(eligible_heroes)
    return play_hero_ban_sound(chosen_hero)
