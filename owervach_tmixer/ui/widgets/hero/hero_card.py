"""Hero Card widget and high-performance portrait memory cache."""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import platformdirs
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer import APP_NAME
from owervach_tmixer.core.models import Hero, Role
from owervach_tmixer.utils import get_resource_path

if TYPE_CHECKING:
    from owervach_tmixer.ui.widgets.hero_widget import HeroWidget

ASSETS_DIR = get_resource_path("assets/Heroes")
CUSTOM_ASSETS_DIR = Path(platformdirs.user_data_dir(APP_NAME)) / "hero_portraits"

ROLE_COLOR = {
    Role.TANK: "#00B4FF",
    Role.DAMAGE: "#FF4444",
    Role.SUPPORT: "#FFD700",
}
ROLE_LABEL = {Role.TANK: "Tanque", Role.DAMAGE: "Daño", Role.SUPPORT: "Apoyo"}

_NICKNAME_MAP_CACHE: dict[str, str] = {}
_PORTRAIT_PATH_CACHE: dict[str, Path | None] = {}

# Mapeo universal autosanador de apodos y variaciones populares
KNOWN_CANON_ALIASES: dict[str, str] = {
    "burrisa": "Orisa",
    "coomfist": "Doomfist",
    "diva": "D.Va",
    "esfera": "Wrecking Ball",
    "winton": "Winston",
    "saria": "Zarya",
    "mmmei": "Mei",
    "riper": "Reaper",
    "sonbra": "Sombra",
    "soyurn": "Sojourn",
    "treiser": "Tracer",
    "bapluis": "Baptiste",
    "keriko": "Kiriko",
    "mersi": "Mercy",
    "cierra": "Sierra",
    "momina": "Domina",
    "ernesto": "Emre",
    "la luuuupaaa": "Illari",
    "poya": "Pharah",
    "soldier: 67": "Soldier: 76",
}



def normalize_token(text: str) -> str:
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_str = "".join(c for c in nfkd if not unicodedata.combining(c))
    return "".join(c for c in ascii_str.lower() if c.isalnum())


def update_nickname_cache(heroes: list[Hero]):
    global _NICKNAME_MAP_CACHE, _PORTRAIT_PATH_CACHE
    _NICKNAME_MAP_CACHE.clear()
    _PORTRAIT_PATH_CACHE.clear()
    for h in heroes:
        if getattr(h, "original_name", None):
            _NICKNAME_MAP_CACHE[h.name.casefold()] = h.original_name


def resolve_canonical_name(name: str) -> str:
    if not name:
        return ""
    folded = name.strip().casefold()
    if folded in _NICKNAME_MAP_CACHE:
        return _NICKNAME_MAP_CACHE[folded]
    if folded in KNOWN_CANON_ALIASES:
        return KNOWN_CANON_ALIASES[folded]
    norm = normalize_token(name)
    for alias_raw, canon in KNOWN_CANON_ALIASES.items():
        if normalize_token(alias_raw) == norm:
            return canon
    return name


def hero_portrait_path(name_or_nickname: str) -> Path | None:
    if not name_or_nickname:
        return None

    target = resolve_canonical_name(name_or_nickname)
    tokens_to_try = [
        normalize_token(target),
        normalize_token(name_or_nickname),
        normalize_token(KNOWN_CANON_ALIASES.get(name_or_nickname.strip().casefold(), "")),
    ]
    tokens_to_try = [t for t in tokens_to_try if t]

    for tok in tokens_to_try:
        if tok in _PORTRAIT_PATH_CACHE:
            cached = _PORTRAIT_PATH_CACHE[tok]
            if cached is not None and cached.exists():
                return cached

    candidate_dirs = [CUSTOM_ASSETS_DIR, ASSETS_DIR]
    for folder in candidate_dirs:
        if not folder.exists():
            continue
        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                stem_norm = normalize_token(file_path.stem)
                for tok in tokens_to_try:
                    if stem_norm == tok:
                        for t in tokens_to_try:
                            _PORTRAIT_PATH_CACHE[t] = file_path
                        return file_path

    for tok in tokens_to_try:
        _PORTRAIT_PATH_CACHE[tok] = None
    return None


def get_rounded_pixmap(pix: QPixmap, size: int = 76, radius: float = 8.0) -> QPixmap:
    if pix.isNull():
        return pix
    scaled = pix.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    crop_x = max(0, (scaled.width() - size) // 2)
    crop_y = max(0, (scaled.height() - size) // 2)
    cropped = scaled.copy(crop_x, crop_y, size, size)

    out = QPixmap(size, size)
    out.fill(Qt.transparent)
    painter = QPainter(out)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    path = QPainterPath()
    path.addRoundedRect(0, 0, size, size, radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, cropped)
    painter.end()
    return out


class HeroCard(QFrame):
    toggled = Signal(bool)

    def __init__(self, hero: Hero, hero_widget: HeroWidget, parent: QWidget | None = None):
        super().__init__(parent or hero_widget)
        self.hero = hero
        self.hero_widget = hero_widget
        self._is_banned = False
        self.setFixedSize(110, 136)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("heroCard")

        self._setup_ui()
        self.refresh_style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        self.portrait_lbl = QLabel()
        self.portrait_lbl.setFixedSize(76, 76)
        self.portrait_lbl.setAlignment(Qt.AlignCenter)
        self.portrait_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        img_path = hero_portrait_path(self.hero.original_name or self.hero.name)
        if img_path:
            pix = QPixmap(str(img_path))
            if not pix.isNull():
                self.portrait_lbl.setPixmap(get_rounded_pixmap(pix, size=76, radius=8.0))
        self.portrait_lbl.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.portrait_lbl, 0, Qt.AlignHCenter)

        self.name_lbl = QLabel(self.hero.name)
        self.name_lbl.setAlignment(Qt.AlignCenter)
        self.name_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.name_lbl.setStyleSheet("font-size: 11px; font-weight: 800; color: #FFFFFF; background: transparent;")
        layout.addWidget(self.name_lbl, 0, Qt.AlignHCenter)

        self.badge_lbl = QLabel(ROLE_LABEL[self.hero.role].upper())
        self.badge_lbl.setAlignment(Qt.AlignCenter)
        self.badge_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.badge_lbl, 0, Qt.AlignHCenter)

    def set_banned(self, banned: bool):
        self._is_banned = banned
        self.refresh_style()

    def is_banned(self) -> bool:
        return self._is_banned

    def refresh_style(self):
        role_color = ROLE_COLOR[self.hero.role]
        self.name_lbl.setText(self.hero.name)

        display_tooltip = f"{self.hero.name}"
        if self.hero.original_name:
            display_tooltip += f" (Original: {self.hero.original_name})"
        display_tooltip += f" · {ROLE_LABEL[self.hero.role]}"

        if self._is_banned:
            self.setStyleSheet("""
                QFrame#heroCard {
                    background-color: #241417;
                    border: 1px solid #FF4444;
                    border-radius: 8px;
                }
                QFrame#heroCard:hover {
                    background-color: #30181D;
                }
            """)
            self.badge_lbl.setText("⛔ BANEADO")
            self.badge_lbl.setStyleSheet("""
                QLabel {
                    font-size: 9px;
                    font-weight: 900;
                    color: #FFFFFF;
                    background-color: #FF4444;
                    border-radius: 3px;
                    padding: 1px 5px;
                }
            """)
            self.setToolTip(f"⛔ {display_tooltip} · Clic izq: desbanear · Clic der: opciones")
        else:
            self.setStyleSheet(f"""
                QFrame#heroCard {{
                    background-color: #17181D;
                    border: 1px solid #282A33;
                    border-radius: 8px;
                }}
                QFrame#heroCard:hover {{
                    background-color: #20232C;
                    border-color: {role_color};
                }}
            """)
            self.badge_lbl.setText(ROLE_LABEL[self.hero.role].upper())
            self.badge_lbl.setStyleSheet(f"""
                QLabel {{
                    font-size: 9px;
                    font-weight: 800;
                    color: {role_color};
                    background-color: rgba(255, 255, 255, 0.06);
                    border: 1px solid {role_color};
                    border-radius: 3px;
                    padding: 1px 5px;
                }}
            """)
            self.setToolTip(f"{display_tooltip} · Clic izq: banear · Clic der: opciones")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggled.emit(not self._is_banned)
            event.accept()
            return
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        self._show_context_menu(event.globalPos())
        event.accept()

    def _show_context_menu(self, global_pos):
        menu = QMenu(self)

        if self._is_banned:
            act_ban = QAction(f"✅ Desbanear a {self.hero.name}", self)
            act_ban.triggered.connect(lambda: self.hero_widget._toggle(self.hero.name, False))
        else:
            act_ban = QAction(f"⛔ Banear a {self.hero.name}", self)
            act_ban.triggered.connect(lambda: self.hero_widget._toggle(self.hero.name, True))
        menu.addAction(act_ban)

        menu.addSeparator()

        act_rename = QAction("✏️ Cambiar nombre (Apodo)...", self)
        act_rename.triggered.connect(lambda: self.hero_widget._prompt_rename_hero(self.hero))
        menu.addAction(act_rename)

        if self.hero.original_name:
            act_restore = QAction(f"🔄 Restaurar nombre original ({self.hero.original_name})", self)
            act_restore.triggered.connect(lambda: self.hero_widget._restore_hero_name(self.hero))
            menu.addAction(act_restore)

        menu.addSeparator()

        act_add_tag = QAction("🏷️ Asignar Etiqueta Rápida...", self)
        act_add_tag.triggered.connect(lambda: self.hero_widget._prompt_add_tag_to_hero(self.hero))
        menu.addAction(act_add_tag)

        if self.hero.tags:
            tag_menu = menu.addMenu("✕ Quitar Etiqueta")
            for k, v in self.hero.tags.items():
                act_rm_tag = QAction(f"Quitar '{k}: {v}'", self)
                act_rm_tag.triggered.connect(lambda _, key=k: self.hero_widget._remove_tag_from_hero(self.hero, key))
                tag_menu.addAction(act_rm_tag)

        menu.addSeparator()

        act_copy = QAction("📋 Copiar nombre al portapapeles", self)
        act_copy.triggered.connect(lambda: QApplication.clipboard().setText(self.hero.name))
        menu.addAction(act_copy)

        menu.exec(global_pos)
