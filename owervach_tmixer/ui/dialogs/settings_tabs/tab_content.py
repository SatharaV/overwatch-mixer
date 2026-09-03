"""Content creation settings: Add custom heroes/maps, tags editor, ZIP packs, and custom item manager."""

from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import platformdirs
from owervach_tmixer import APP_NAME
from owervach_tmixer.core.models import Hero, Map
from owervach_tmixer.ui.styles import theme
from owervach_tmixer.ui.widgets.hero_widget import hero_portrait_path
from owervach_tmixer.utils import get_resource_path
from .common import create_card_box

MODE_COLORS: dict[str, str] = {
    "Assault": "#E03131",
    "Clash": "#FF6B6B",
    "Control": "#00B4FF",
    "Escort": "#FFAA00",
    "Flashpoint": "#20C997",
    "Hybrid": "#9D5CFF",
    "Push": "#51CF66",
}


def _find_hero_portrait(hero_name: str) -> Path | None:
    return hero_portrait_path(hero_name)


def _find_map_image(map_name: str, mode: str) -> Path | None:
    user_dir = Path(platformdirs.user_data_dir(APP_NAME)) / "Maps" / mode
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = user_dir / f"{map_name}{ext}"
        if p.exists():
            return p
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = get_resource_path(f"assets/Maps/{mode}/{map_name}{ext}")
        if p.exists():
            return p
    return None


def build_content_tab(dialog, layout: QVBoxLayout):
    box_create = create_card_box("Crear Héroes y Mapas Nuevos")
    vbox_create = QVBoxLayout(box_create)
    vbox_create.setSpacing(10)

    row_btns = QHBoxLayout()
    row_btns.setSpacing(10)

    add_hero = QPushButton("🎭 + Añadir Héroe Nuevo")
    add_hero.setProperty("primary", True)
    add_hero.setCursor(Qt.CursorShape.PointingHandCursor)
    add_hero.setFixedHeight(36)
    add_hero.clicked.connect(dialog._on_add_hero_clicked)
    row_btns.addWidget(add_hero)

    add_map = QPushButton("🗺️ + Añadir Mapa Nuevo")
    add_map.setProperty("primary", True)
    add_map.setCursor(Qt.CursorShape.PointingHandCursor)
    add_map.setFixedHeight(36)
    add_map.clicked.connect(dialog._on_add_map_clicked)
    row_btns.addWidget(add_map)
    vbox_create.addLayout(row_btns)
    layout.addWidget(box_create)

    box_tags = create_card_box("Clasificación y Editor de Etiquetas")
    vbox_tags = QVBoxLayout(box_tags)
    vbox_tags.setSpacing(8)

    lbl_tags_info = QLabel("Personaliza y etiqueta a cada héroe para ordenarlos y filtrarlos.")
    lbl_tags_info.setStyleSheet("color: #9A9EAB; font-size: 11px;")
    vbox_tags.addWidget(lbl_tags_info)

    btn_open_tags = QPushButton("🏷️ Abrir Editor de Etiquetas de Héroes")
    btn_open_tags.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_open_tags.setFixedHeight(36)
    btn_open_tags.setStyleSheet(f"""
        QPushButton {{
            font-size: 12px; font-weight: 800; color: #FFFFFF;
            background-color: #1E222A; border: 1px solid {theme.accent()}; border-radius: 6px;
        }}
        QPushButton:hover {{ background-color: {theme.accent_rgba(0.14)}; }}
    """)
    btn_open_tags.clicked.connect(dialog._open_hero_tags_editor)
    vbox_tags.addWidget(btn_open_tags)
    layout.addWidget(box_tags)

    box_zip = create_card_box("Paquete Completo (.ZIP con Fotos)")
    vbox_zip = QVBoxLayout(box_zip)
    vbox_zip.setSpacing(8)

    lbl_zip_info = QLabel("Exporta o importa todos tus mapas, héroes y fotos en un solo archivo comprimido.")
    lbl_zip_info.setStyleSheet("color: #9A9EAB; font-size: 11px;")
    vbox_zip.addWidget(lbl_zip_info)

    row_zip = QHBoxLayout()
    row_zip.setSpacing(10)

    btn_exp_zip = QPushButton("📦 Exportar Pack Completo (.zip)")
    btn_exp_zip.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_exp_zip.setFixedHeight(34)
    btn_exp_zip.clicked.connect(dialog._export_full_zip_pack)
    row_zip.addWidget(btn_exp_zip)

    btn_imp_zip = QPushButton("📥 Importar Pack Completo (.zip)")
    btn_imp_zip.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_imp_zip.setFixedHeight(34)
    btn_imp_zip.clicked.connect(dialog._import_full_zip_pack)
    row_zip.addWidget(btn_imp_zip)
    vbox_zip.addLayout(row_zip)
    layout.addWidget(box_zip)

    box_custom = create_card_box("Gestor de Héroes y Mapas Creados")
    dialog._custom_layout = QVBoxLayout(box_custom)
    dialog._custom_layout.setSpacing(8)
    dialog._refresh_custom_content_lists()
    layout.addWidget(box_custom)


def create_custom_hero_row(dialog, hero: Hero) -> QWidget:
    row = QFrame()
    row.setStyleSheet("background-color: #1E2027; border: 1px solid #2F334E; border-radius: 6px;")
    hlayout = QHBoxLayout(row)
    hlayout.setContentsMargins(8, 4, 8, 4)
    hlayout.setSpacing(8)

    thumb = QLabel()
    thumb.setFixedSize(28, 28)
    img_path = _find_hero_portrait(hero.original_name or hero.name)
    if img_path:
        pix = QPixmap(str(img_path))
        if not pix.isNull():
            thumb.setPixmap(pix.scaled(28, 28, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
    thumb.setStyleSheet("border-radius: 4px; background-color: #121316;")
    hlayout.addWidget(thumb)

    lbl_name = QLabel(hero.name)
    lbl_name.setStyleSheet("font-size: 13px; font-weight: 700; color: #FFFFFF;")
    hlayout.addWidget(lbl_name, 1)

    role_label = QLabel(hero.role.value.capitalize())
    role_color = hero.role.color
    role_label.setStyleSheet(f"""
        QLabel {{
            font-size: 10px; font-weight: 800; color: {role_color};
            background-color: rgba(255, 255, 255, 0.08); border: 1px solid {role_color};
            border-radius: 4px; padding: 2px 6px;
        }}
    """)
    hlayout.addWidget(role_label)

    btn_del = QPushButton("🗑️")
    btn_del.setToolTip(f"Eliminar '{hero.name}'")
    btn_del.setFixedSize(28, 28)
    btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_del.setStyleSheet("""
        QPushButton { font-size: 13px; background-color: #261B1E; border: 1px solid #5A2228; border-radius: 4px; }
        QPushButton:hover { background-color: #5A1E24; border-color: #FF4444; }
    """)
    btn_del.clicked.connect(lambda _, h=hero: dialog._delete_custom_hero(h))
    hlayout.addWidget(btn_del)
    return row


def create_custom_map_row(dialog, map_obj: Map) -> QWidget:
    row = QFrame()
    row.setStyleSheet("background-color: #1E2027; border: 1px solid #2F333E; border-radius: 6px;")
    hlayout = QHBoxLayout(row)
    hlayout.setContentsMargins(8, 4, 8, 4)
    hlayout.setSpacing(8)

    thumb = QLabel()
    thumb.setFixedSize(42, 28)
    img_path = _find_map_image(map_obj.name, map_obj.mode)
    if img_path:
        pix = QPixmap(str(img_path))
        if not pix.isNull():
            thumb.setPixmap(pix.scaled(42, 28, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
    thumb.setStyleSheet("border-radius: 4px; background-color: #121316;")
    hlayout.addWidget(thumb)

    lbl_name = QLabel(map_obj.name)
    lbl_name.setStyleSheet("font-size: 13px; font-weight: 700; color: #FFFFFF;")
    hlayout.addWidget(lbl_name, 1)

    mode_color = MODE_COLORS.get(map_obj.mode, "#888888")
    mode_label = QLabel(map_obj.mode.upper())
    mode_label.setStyleSheet(f"""
        QLabel {{
            font-size: 10px; font-weight: 800; color: #FFFFFF;
            background-color: {mode_color}; border-radius: 4px; padding: 2px 6px;
        }}
    """)
    hlayout.addWidget(mode_label)

    btn_del = QPushButton("🗑️")
    btn_del.setToolTip(f"Eliminar '{map_obj.name}'")
    btn_del.setFixedSize(28, 28)
    btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_del.setStyleSheet("""
        QPushButton { font-size: 13px; background-color: #261B1E; border: 1px solid #5A2228; border-radius: 4px; }
        QPushButton:hover { background-color: #5A1E24; border-color: #FF4444; }
    """)
    btn_del.clicked.connect(lambda _, m=map_obj: dialog._delete_custom_map(m))
    hlayout.addWidget(btn_del)
    return row
