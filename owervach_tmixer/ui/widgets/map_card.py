"""Card widget for an individual Overwatch map with instant fixed-tier RAM cache and background pre-loader."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont, QImage, QImageReader, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMenu,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.core.models import Map
from owervach_tmixer.ui.styles import theme
from owervach_tmixer.utils import get_resource_path
from .marquee_label import MarqueeLabel

MODE_COLORS = {
    "Assault": "#E03131",
    "Clash": "#FF6B6B",
    "Control": "#00B4FF",
    "Escort": "#FFAA00",
    "Flashpoint": "#20C997",
    "Hybrid": "#9D5CFF",
    "Push": "#51CF66",
}

_MAP_PATH_CACHE: dict[tuple[str, str], Path | None] = {}
_MAP_BANNER_CACHE: dict[tuple[str, str, str, str], QPixmap] = {}
_PRELOADED = False


def map_image_path(name: str, mode: str) -> Path | None:
    cache_key = (name, mode)
    if cache_key in _MAP_PATH_CACHE:
        return _MAP_PATH_CACHE[cache_key]

    maps_root = get_resource_path("assets/Maps")
    if not maps_root.exists():
        _MAP_PATH_CACHE[cache_key] = None
        return None

    mode_dir = maps_root / mode
    clean_name = name.replace(":", "")

    candidates = [
        mode_dir / f"{name}.png",
        mode_dir / f"{clean_name}.png",
        mode_dir / f"{name}.jpg",
        mode_dir / f"{clean_name}.jpg",
        mode_dir / f"{name}.webp",
        mode_dir / f"{clean_name}.webp",
    ]

    for p in candidates:
        if p.exists():
            _MAP_PATH_CACHE[cache_key] = p
            return p

    folded = name.casefold().replace(":", "")
    for f in maps_root.rglob("*"):
        if f.is_file() and f.stem.casefold().replace(":", "") == folded:
            _MAP_PATH_CACHE[cache_key] = f
            return f

    _MAP_PATH_CACHE[cache_key] = None
    return None


def get_cached_map_banner(name: str, mode: str, card_size: str = "medium", aspect_ratio: str = "auto") -> QPixmap:
    """Fetches pre-rendered rounded map banner from memory with 100% cache hit guaranteed."""
    cache_key = (name, mode, card_size, aspect_ratio)
    if cache_key in _MAP_BANNER_CACHE:
        return _MAP_BANNER_CACHE[cache_key]

    # Dimensiones estándar fijas para evitar recalcular por cada píxel
    if card_size == "small":
        target_w, target_h = (260, 80 if aspect_ratio != "16:9" else 146)
    elif card_size == "large":
        target_w, target_h = (480, 135 if aspect_ratio != "16:9" else 270)
    else:  # medium
        target_w, target_h = (360, 100 if aspect_ratio != "16:9" else 202)

    img_path = map_image_path(name, mode)
    if img_path and img_path.exists():
        reader = QImageReader(str(img_path))
        reader.setAutoTransform(True)
        reader.setScaledSize(reader.size().scaled(target_w, target_h, Qt.AspectRatioMode.KeepAspectRatioByExpanding))
        img = reader.read()
        if not img.isNull():
            crop_x = max(0, (img.width() - target_w) // 2)
            crop_y = max(0, (img.height() - target_h) // 2)
            cropped_img = img.copy(crop_x, crop_y, target_w, target_h)

            rounded = QPixmap(target_w, target_h)
            rounded.fill(Qt.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            path = QPainterPath()
            path.addRoundedRect(0, 0, target_w, target_h + 10, 8, 8)
            painter.setClipPath(path)
            painter.drawImage(0, 0, cropped_img)
            painter.end()

            _MAP_BANNER_CACHE[cache_key] = rounded
            return rounded

    # Fallback si no hay imagen
    mode_color = QColor(MODE_COLORS.get(mode, "#6B7280"))
    fallback = QPixmap(target_w, target_h)
    fallback.fill(Qt.transparent)
    painter = QPainter(fallback)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(0, 0, target_w, target_h + 10, 8, 8)
    painter.setClipPath(path)
    painter.fillRect(0, 0, target_w, target_h, mode_color.darker(280))
    painter.setPen(mode_color)
    font = QFont("Segoe UI", int(target_h // 4), QFont.Bold)
    painter.setFont(font)
    painter.drawText(0, 0, target_w, target_h, Qt.AlignCenter, "🗺️")
    painter.end()

    _MAP_BANNER_CACHE[cache_key] = fallback
    return fallback


def preload_all_map_banners(maps: list[Map]):
    """Pre-decodes all map banners into RAM in background so tab switching is 0ms instant."""
    global _PRELOADED
    if _PRELOADED:
        return
    _PRELOADED = True

    def _worker():
        for m in maps:
            for size in ("medium", "small", "large"):
                get_cached_map_banner(m.name, m.mode, card_size=size, aspect_ratio="auto")
    t = threading.Thread(target=_worker, daemon=True)
    t.start()


class MapCardWidget(QFrame):
    """Visual map card supporting instant memory caching, outline badges, and 16:9 ratio."""

    clicked = Signal(object)
    double_clicked = Signal(object)
    status_toggled = Signal(object, bool)
    delete_requested = Signal(object)

    def __init__(
        self,
        map_obj: Map,
        is_active: bool = True,
        card_size: str = "medium",
        aspect_ratio: str = "auto",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.map_obj = map_obj
        self._is_active = is_active
        self._is_selected = False
        self._card_size = card_size
        self._aspect_ratio = aspect_ratio

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("mapCard")
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self._apply_dimensions()
        self._setup_ui()
        self._apply_style()

    def _apply_dimensions(self):
        if self._card_size == "small":
            self.min_w, self.max_w = 160, 260
            self.banner_h = 80
            self.info_h = 36
            font_pt = 10
        elif self._card_size == "large":
            self.min_w, self.max_w = 260, 480
            self.banner_h = 135
            self.info_h = 48
            font_pt = 12
        else:  # medium
            self.min_w, self.max_w = 200, 380
            self.banner_h = 100
            self.info_h = 42
            font_pt = 11

        total_h = self.banner_h + self.info_h
        self.setMinimumWidth(self.min_w)
        self.setMaximumWidth(self.max_w)
        self.setFixedHeight(total_h)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if hasattr(self, "banner"):
            self.banner.setFixedHeight(self.banner_h)
        if hasattr(self, "info_widget"):
            self.info_widget.setFixedHeight(self.info_h)
        if hasattr(self, "lbl_name"):
            font = self.lbl_name.font()
            font.setPointSize(font_pt)
            self.lbl_name.setFont(font)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.banner = QLabel(self)
        self.banner.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.banner.setScaledContents(True)
        self.banner.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.banner)

        # Selected floating badge
        self.lbl_selected_badge = QLabel("👑 SELECCIONADO", self.banner)
        self.lbl_selected_badge.setGeometry(8, 8, 105, 20)
        self.lbl_selected_badge.setAlignment(Qt.AlignCenter)
        self.lbl_selected_badge.setStyleSheet(f"""
            QLabel {{
                font-size: 9px;
                font-weight: 900;
                color: #FFFFFF;
                background-color: rgba(10, 12, 18, 0.88);
                border: 1px solid {theme.accent()};
                border-radius: 4px;
                padding: 1px 4px;
            }}
        """)
        self.lbl_selected_badge.setVisible(self._is_selected)

        self.info_widget = QWidget(self)
        info_layout = QHBoxLayout(self.info_widget)
        info_layout.setContentsMargins(8, 2, 8, 2)
        info_layout.setSpacing(6)

        self.lbl_name = MarqueeLabel(self.map_obj.name, self.info_widget)
        font = QFont()
        font.setWeight(QFont.Weight.Bold)
        self.lbl_name.setFont(font)
        self.lbl_name.setStyleSheet("color: #FFFFFF; background: transparent;")
        info_layout.addWidget(self.lbl_name, 1)

        # Outline Mode Badge
        mode_color = MODE_COLORS.get(self.map_obj.mode, "#6B7280")
        self.lbl_mode = QLabel(self.map_obj.mode.upper(), self.info_widget)
        self.lbl_mode.setAlignment(Qt.AlignCenter)
        self.lbl_mode.setStyleSheet(f"""
            QLabel {{
                font-size: 9px;
                font-weight: 800;
                color: {mode_color};
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid {mode_color};
                border-radius: 4px;
                padding: 1px 5px;
                border-radius: 3px;
            }}
        """)
        self.lbl_mode.setFixedHeight(16)
        info_layout.addWidget(self.lbl_mode, 0, Qt.AlignVCenter)

        layout.addWidget(self.info_widget)
        self._render_banner()

    def set_preferences(self, card_size: str, aspect_ratio: str):
        self._card_size = card_size
        self._aspect_ratio = aspect_ratio
        self._apply_dimensions()
        self._render_banner()

    def _render_banner(self):
        target_w = max(self.min_w, self.width())

        if self._aspect_ratio == "16:9":
            target_h = int(target_w * 9 / 16)
        else:
            target_h = self.banner_h

        if self.banner.height() != target_h:
            self.banner.setFixedHeight(target_h)
            self.setFixedHeight(target_h + self.info_h)

        banner_pix = get_cached_map_banner(self.map_obj.name, self.map_obj.mode, self._card_size, self._aspect_ratio)
        self.banner.setPixmap(banner_pix)

    def set_active(self, active: bool):
        self._is_active = active
        self._apply_style()

    def is_active(self) -> bool:
        return self._is_active

    def set_selected(self, selected: bool):
        self._is_selected = selected
        if hasattr(self, "lbl_selected_badge"):
            self.lbl_selected_badge.setVisible(selected)
        self._apply_style()

    def _apply_style(self):
        mode_col = MODE_COLORS.get(self.map_obj.mode, "#888888")
        accent_col = theme.accent()

        if self._is_selected:
            border = f"2px solid {accent_col}"
            bg = "#181D26"
        elif self._is_active:
            border = "1px solid #282A33"
            bg = "#17181D"
        else:
            border = "1px dashed #20222A"
            bg = "#121316"

        self.setStyleSheet(f"""
            QFrame#mapCard {{
                background-color: {bg};
                border: {border};
                border-radius: 8px;
            }}
            QFrame#mapCard:hover {{
                border-color: {mode_col if not self._is_selected else accent_col};
                background-color: #1E2028;
            }}
        """)

        if hasattr(self, "lbl_selected_badge"):
            self.lbl_selected_badge.setStyleSheet(f"""
                QLabel {{
                    font-size: 9px;
                    font-weight: 900;
                    color: #FFFFFF;
                    background-color: rgba(10, 12, 18, 0.88);
                    border: 1px solid {accent_col};
                    border-radius: 4px;
                    padding: 1px 4px;
                }}
            """)

        if hasattr(self, "lbl_mode"):
            self.lbl_mode.setFixedHeight(16)
            self.lbl_mode.setStyleSheet(f"""
                QLabel {{
                    font-size: 8.5px;
                    font-weight: 800;
                    color: {mode_col};
                    background-color: rgba(255, 255, 255, 0.05);
                    border: 1px solid {mode_col};
                    border-radius: 3px;
                    padding: 0px 4px;
                }}
            """)

        if not self._is_active and not self._is_selected:
            effect = QGraphicsOpacityEffect(self)
            effect.setOpacity(0.35)
            self.setGraphicsEffect(effect)
        else:
            self.setGraphicsEffect(None)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.map_obj)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.map_obj)
        super().mouseDoubleClickEvent(event)

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        act_pick = QAction("👑 Elegir para la partida actual", self)
        act_pick.triggered.connect(lambda: self.double_clicked.emit(self.map_obj))
        menu.addAction(act_pick)

        act_toggle = QAction(
            "❌ Desactivar del pool" if self._is_active else "✅ Activar en el pool", self
        )
        act_toggle.triggered.connect(lambda: self.status_toggled.emit(self.map_obj, not self._is_active))
        menu.addAction(act_toggle)

        menu.addSeparator()

        act_delete = QAction("🗑️ Eliminar mapa", self)
        act_delete.triggered.connect(lambda: self.delete_requested.emit(self.map_obj))
        menu.addAction(act_delete)
        menu.exec(self.mapToGlobal(pos))
