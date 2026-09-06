"""Gameplay settings: Shuffle, Roles & Bans, Maps, and Players tabs."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListView,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.core.models import ShuffleMode
from .common import create_card_box


def build_shuffle_tab(dialog, layout: QVBoxLayout):
    box_algo = create_card_box("Algoritmo de Emparejamiento")
    form_algo = QFormLayout(box_algo)
    form_algo.setSpacing(12)
    dialog.cb_shuffle_mode = QComboBox()
    dialog.cb_shuffle_mode.setView(QListView())
    for mode in ShuffleMode:
        dialog.cb_shuffle_mode.addItem(mode.display_name, mode)
    form_algo.addRow("Modo de emparejamiento:", dialog.cb_shuffle_mode)
    layout.addWidget(box_algo)

    box_div = create_card_box("Optimización de Diversidad")
    form_div = QFormLayout(box_div)
    form_div.setSpacing(12)
    dialog.spin_candidates = QSpinBox()
    dialog.spin_candidates.setRange(10, 500)
    dialog.spin_candidates.setSingleStep(10)
    form_div.addRow("Candidatos evaluados por mezcla:", dialog.spin_candidates)
    layout.addWidget(box_div)

    box_hist = create_card_box("Historial de Mezclas")
    form_hist = QFormLayout(box_hist)
    form_hist.setSpacing(12)
    dialog.spin_history_size = QSpinBox()
    dialog.spin_history_size.setRange(5, 100)
    form_hist.addRow("Tamaño máximo del historial:", dialog.spin_history_size)

    btn_clear = QPushButton("🗑️ Limpiar Historial de Mezclas")
    btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_clear.setStyleSheet("""
        QPushButton {
            background-color: #2A171B; border: 1px solid #5A2028; border-radius: 6px;
            color: #FFAAAA; font-weight: 700; padding: 6px 12px; font-size: 11px;
        }
        QPushButton:hover { background-color: #4A1E24; border-color: #FF4444; color: #FFFFFF; }
    """)
    btn_clear.clicked.connect(dialog._clear_shuffle_history)
    form_hist.addRow("", btn_clear)
    layout.addWidget(box_hist)

    # Configuración de Rotación de Zona de Espera
    box_rot = create_card_box("Política de Rotación de Zona de Espera")
    form_rot = QFormLayout(box_rot)
    form_rot.setSpacing(12)

    dialog.cb_rotation_policy = QComboBox()
    dialog.cb_rotation_policy.setView(QListView())
    dialog.cb_rotation_policy.addItem("Continua / Cinta (Recomendado)", "continuous")
    dialog.cb_rotation_policy.addItem("En Bloque (Todos a la vez)", "full_batch")
    dialog.cb_rotation_policy.addItem("El Ganador se Queda (Arcade / Retas)", "winner_stays")
    form_rot.addRow("Modo de rotación:", dialog.cb_rotation_policy)

    dialog.spin_rotation_batch = QSpinBox()
    dialog.spin_rotation_batch.setRange(1, 5)
    dialog.spin_rotation_batch.setValue(2)
    form_rot.addRow("Jugadores a rotar por partida:", dialog.spin_rotation_batch)

    dialog.spin_min_shield = QSpinBox()
    dialog.spin_min_shield.setRange(1, 4)
    dialog.spin_min_shield.setValue(2)
    form_rot.addRow("Permanencia mínima garantizada (Bo2):", dialog.spin_min_shield)

    dialog.spin_streamer_rest = QSpinBox()
    dialog.spin_streamer_rest.setRange(0, 10)
    dialog.spin_streamer_rest.setValue(0)
    form_rot.addRow("Descanso de Streamers 👑 (0 = Siempre juegan):", dialog.spin_streamer_rest)

    layout.addWidget(box_rot)


def build_roles_bans_tab(dialog, layout: QVBoxLayout):
    box_policy = create_card_box("Políticas de Roles")
    vbox_policy = QVBoxLayout(box_policy)
    dialog.chk_auto_roles = QCheckBox("Asignar y randomizar roles automáticamente al mezclar")
    dialog.chk_auto_roles.setStyleSheet("color: #FFFFFF; font-weight: 700; font-size: 12px;")
    vbox_policy.addWidget(dialog.chk_auto_roles)
    layout.addWidget(box_policy)

    box_5v5 = create_card_box("Composición 5v5 (Por Equipo)")
    form_5v5 = QFormLayout(box_5v5)
    form_5v5.setSpacing(10)
    dialog.spin_5v5_tank = QSpinBox()
    dialog.spin_5v5_tank.setRange(0, 5)
    form_5v5.addRow("🛡️ Tanques:", dialog.spin_5v5_tank)
    dialog.spin_5v5_damage = QSpinBox()
    dialog.spin_5v5_damage.setRange(0, 5)
    form_5v5.addRow("⚔️ Daño:", dialog.spin_5v5_damage)
    dialog.spin_5v5_support = QSpinBox()
    dialog.spin_5v5_support.setRange(0, 5)
    form_5v5.addRow("💖 Apoyo:", dialog.spin_5v5_support)
    layout.addWidget(box_5v5)

    box_6v6 = create_card_box("Composición 6v6 (Por Equipo)")
    form_6v6 = QFormLayout(box_6v6)
    form_6v6.setSpacing(10)
    dialog.spin_6v6_tank = QSpinBox()
    dialog.spin_6v6_tank.setRange(0, 6)
    form_6v6.addRow("🛡️ Tanques:", dialog.spin_6v6_tank)
    dialog.spin_6v6_damage = QSpinBox()
    dialog.spin_6v6_damage.setRange(0, 6)
    form_6v6.addRow("⚔️ Daño:", dialog.spin_6v6_damage)
    dialog.spin_6v6_support = QSpinBox()
    dialog.spin_6v6_support.setRange(0, 6)
    form_6v6.addRow("💖 Apoyo:", dialog.spin_6v6_support)
    layout.addWidget(box_6v6)

    box_bans = create_card_box("Baneos de Héroes")
    form_bans = QFormLayout(box_bans)
    form_bans.setSpacing(10)
    dialog.chk_auto_bans = QCheckBox("Sortear héroes baneados automáticamente")
    dialog.chk_auto_bans.setStyleSheet("color: #FFFFFF; font-weight: 700; font-size: 12px;")
    form_bans.addRow("", dialog.chk_auto_bans)

    dialog.spin_max_bans = QSpinBox()
    dialog.spin_max_bans.setRange(0, 20)
    form_bans.addRow("Máximo total de baneos:", dialog.spin_max_bans)

    dialog.spin_max_bans_per_role = QSpinBox()
    dialog.spin_max_bans_per_role.setRange(0, 10)
    form_bans.addRow("Máximo de baneos por rol:", dialog.spin_max_bans_per_role)

    dialog.spin_portrait_size = QSpinBox()
    dialog.spin_portrait_size.setRange(20, 64)
    dialog.spin_portrait_size.setSingleStep(4)
    form_bans.addRow("Tamaño de retratos baneados (px):", dialog.spin_portrait_size)

    dialog.spin_bans_rows = QSpinBox()
    dialog.spin_bans_rows.setRange(1, 5)
    dialog.spin_bans_rows.setValue(2)
    form_bans.addRow("Filas visibles de baneos:", dialog.spin_bans_rows)
    layout.addWidget(box_bans)


def build_maps_tab(dialog, layout: QVBoxLayout):
    box_pool = create_card_box("Sorteo y Selección de Mapas")
    form_pool = QFormLayout(box_pool)
    form_pool.setSpacing(12)
    dialog.chk_auto_map = QCheckBox("Sortear mapa automáticamente al mezclar la partida")
    dialog.chk_auto_map.setStyleSheet("color: #FFFFFF; font-weight: 700; font-size: 12px;")
    form_pool.addRow("", dialog.chk_auto_map)
    dialog.spin_avoid_maps = QSpinBox()
    dialog.spin_avoid_maps.setRange(0, 20)
    form_pool.addRow("Evitar mapas jugados recientemente:", dialog.spin_avoid_maps)
    layout.addWidget(box_pool)

    box_ui = create_card_box("Visualización de Tarjetas en Pestaña Mapas")
    form_ui = QFormLayout(box_ui)
    form_ui.setSpacing(12)
    dialog.cb_map_size = QComboBox()
    dialog.cb_map_size.setView(QListView())
    dialog.cb_map_size.addItem("Pequeño (Compacto)", "small")
    dialog.cb_map_size.addItem("Mediano (Normal)", "medium")
    dialog.cb_map_size.addItem("Grande", "large")
    form_ui.addRow("Tamaño de tarjetas:", dialog.cb_map_size)

    dialog.cb_map_aspect = QComboBox()
    dialog.cb_map_aspect.setView(QListView())
    dialog.cb_map_aspect.addItem("Dinámico (Adaptable)", "auto")
    dialog.cb_map_aspect.addItem("16:9 (Cinemático Fijo)", "16:9")
    form_ui.addRow("Formato de aspecto:", dialog.cb_map_aspect)
    layout.addWidget(box_ui)


def build_players_tab(dialog, layout: QVBoxLayout):
    box_clean = create_card_box("Mantenimiento y Limpieza de Jugadores Guardados")
    vbox_clean = QVBoxLayout(box_clean)
    vbox_clean.setSpacing(10)

    lbl_p_info = QLabel("Herramientas para purgar líneas pegadas por error o vaciar la lista de guardados.")
    lbl_p_info.setStyleSheet("color: #9A9EAB; font-size: 11px;")
    vbox_clean.addWidget(lbl_p_info)

    row_p_tools = QHBoxLayout()
    row_p_tools.setSpacing(10)

    btn_purge = QPushButton("🧹 Purgar Inválidos")
    btn_purge.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_purge.setFixedHeight(34)
    btn_purge.setStyleSheet("""
        QPushButton {
            font-size: 11px; font-weight: 800; color: #FFAA00;
            background-color: #261E14; border: 1px solid #6E4D1A; border-radius: 6px; padding: 4px 12px;
        }
        QPushButton:hover { background-color: #382C1B; border-color: #FFAA00; color: #FFFFFF; }
    """)
    btn_purge.clicked.connect(dialog._purge_invalid_saved_players)
    row_p_tools.addWidget(btn_purge)

    btn_clear_saved = QPushButton("🗑️ Vaciar Guardados")
    btn_clear_saved.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_clear_saved.setFixedHeight(34)
    btn_clear_saved.setStyleSheet("""
        QPushButton {
            font-size: 11px; font-weight: 800; color: #FF7788;
            background-color: #2A171B; border: 1px solid #6E222B; border-radius: 6px; padding: 4px 12px;
        }
        QPushButton:hover { background-color: #401F25; border-color: #FF4444; color: #FFFFFF; }
    """)
    btn_clear_saved.clicked.connect(dialog._clear_all_saved_players)
    row_p_tools.addWidget(btn_clear_saved)

    btn_reset_mmr = QPushButton("⚡ Reset MMR (5)")
    btn_reset_mmr.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_reset_mmr.setFixedHeight(34)
    btn_reset_mmr.setStyleSheet("""
        QPushButton {
            font-size: 11px; font-weight: 800; color: #FFAA00;
            background-color: #272015; border: 1px solid #784E12; border-radius: 6px; padding: 4px 12px;
        }
        QPushButton:hover { background-color: #3D2F1C; border-color: #FFAA00; color: #FFFFFF; }
    """)
    btn_reset_mmr.clicked.connect(dialog._reset_all_players_mmr)
    row_p_tools.addWidget(btn_reset_mmr)

    vbox_clean.addLayout(row_p_tools)
    layout.addWidget(box_clean)

    box_behavior = create_card_box("Comportamiento y Nombres de Jugadores")
    vbox_beh = QVBoxLayout(box_behavior)
    vbox_beh.setSpacing(10)

    dialog.chk_dnd_swap = QCheckBox("Intercambiar al soltar sobre una celda ocupada del otro equipo")
    dialog.chk_dnd_swap.setStyleSheet("color: #FFFFFF; font-weight: 700; font-size: 12px;")
    vbox_beh.addWidget(dialog.chk_dnd_swap)

    dialog.chk_auto_caps = QCheckBox("Auto-capitalizar y formatear nombres de jugadores al escribir")
    dialog.chk_auto_caps.setStyleSheet("color: #FFFFFF; font-weight: 700; font-size: 12px;")
    vbox_beh.addWidget(dialog.chk_auto_caps)
    layout.addWidget(box_behavior)
