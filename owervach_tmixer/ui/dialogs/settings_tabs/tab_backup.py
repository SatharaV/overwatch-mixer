"""Backup and system restore settings tab."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
)

from .common import create_card_box


def build_backup_tab(dialog, layout: QVBoxLayout):
    box_json = create_card_box("Respaldos en Texto (JSON)")
    vbox_json = QVBoxLayout(box_json)
    vbox_json.setSpacing(10)

    grid_json = QGridLayout()
    grid_json.setHorizontalSpacing(8)
    grid_json.setVerticalSpacing(8)

    maps_import = QPushButton("📥 Importar Mapas JSON")
    maps_import.clicked.connect(lambda: dialog.parent().map_widget._import_maps() if hasattr(dialog.parent(), "map_widget") else None)
    maps_export = QPushButton("📤 Exportar Mapas JSON")
    maps_export.clicked.connect(lambda: dialog.parent().map_widget._export_maps() if hasattr(dialog.parent(), "map_widget") else None)
    heroes_import = QPushButton("📥 Importar Héroes JSON")
    heroes_import.clicked.connect(lambda: dialog.parent().hero_widget._import_heroes() if hasattr(dialog.parent(), "hero_widget") else None)
    heroes_export = QPushButton("📤 Exportar Héroes JSON")
    heroes_export.clicked.connect(lambda: dialog.parent().hero_widget._export_heroes() if hasattr(dialog.parent(), "hero_widget") else None)

    for b in (maps_import, maps_export, heroes_import, heroes_export):
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet("padding: 6px 10px; font-size: 11px; font-weight: 600;")

    grid_json.addWidget(maps_import, 0, 0)
    grid_json.addWidget(maps_export, 0, 1)
    grid_json.addWidget(heroes_import, 1, 0)
    grid_json.addWidget(heroes_export, 1, 1)
    vbox_json.addLayout(grid_json)
    layout.addWidget(box_json)

    box_restore = create_card_box("Restablecimiento del Sistema")
    vbox_res = QVBoxLayout(box_restore)
    vbox_res.setSpacing(10)

    row_resets = QHBoxLayout()
    row_resets.setSpacing(8)
    btn_reset_maps = QPushButton("🔄 Restablecer Mapas Oficiales")
    btn_reset_maps.setStyleSheet("background-color: #241D12; border: 1px solid #774400; color: #FFAA00; padding: 6px; font-weight: 700; font-size: 11px; border-radius: 6px;")
    btn_reset_maps.clicked.connect(dialog._restore_default_maps)
    row_resets.addWidget(btn_reset_maps)

    btn_reset_heroes = QPushButton("🔄 Restablecer Héroes Oficiales")
    btn_reset_heroes.setStyleSheet("background-color: #241D12; border: 1px solid #774400; color: #FFAA00; padding: 6px; font-weight: 700; font-size: 11px; border-radius: 6px;")
    btn_reset_heroes.clicked.connect(dialog._restore_default_heroes)
    row_resets.addWidget(btn_reset_heroes)
    vbox_res.addLayout(row_resets)

    btn_factory = QPushButton("☢️ Restablecer Todo a Estado de Fábrica")
    btn_factory.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_factory.setFixedHeight(34)
    btn_factory.setStyleSheet("""
        QPushButton {
            background-color: #2D1418; border: 1px solid #6E222B; color: #FF7788;
            font-weight: 800; font-size: 11px; border-radius: 6px; margin-top: 4px;
        }
        QPushButton:hover { background-color: #4A1920; border-color: #FF4444; color: #FFFFFF; }
    """)
    btn_factory.clicked.connect(dialog._on_factory_reset_clicked)
    vbox_res.addWidget(btn_factory)
    layout.addWidget(box_restore)
