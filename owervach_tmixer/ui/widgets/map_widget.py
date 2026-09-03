"""Modern Overwatch map pool explorer (Modular Orchestrator with smooth instant layout)."""

from __future__ import annotations
from .smooth_scroll import SmoothScrollArea

import random
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.core.models import Map, validate_map_import
from owervach_tmixer.core.storage import Storage
from owervach_tmixer.ui.styles import theme

# Submódulos desacoplados
from .scrollable_pills import ScrollArrowBtn, ScrollablePillsWidget
from .map_drawer import MapSelectedDrawer
from .map_card import MapCardWidget, MODE_COLORS, map_image_path

MODES_FILTER = ["Todos", "Control", "Hybrid", "Escort", "Push", "Flashpoint", "Clash", "Assault"]

MODE_ORDER = {
    "Control": 0,
    "Hybrid": 1,
    "Escort": 2,
    "Push": 3,
    "Flashpoint": 4,
    "Clash": 5,
    "Assault": 6,
}


class _MapListCompatibilityAdapter:
    def __init__(self, map_widget: MapWidget):
        self._widget = map_widget

    def count(self) -> int:
        return len(self._widget._maps)

    def currentRow(self) -> int:
        if not self._widget._current_selected:
            return -1
        for i, m in enumerate(self._widget._maps):
            if m.name == self._widget._current_selected.name:
                return i
        return -1

    def setCurrentRow(self, row: int):
        if 0 <= row < len(self._widget._maps):
            m = self._widget._maps[row]
            self._widget.select_map(m)
            self._widget.map_selected.emit(m)

    def item(self, row: int):
        if 0 <= row < len(self._widget._maps):
            m = self._widget._maps[row]
            class _Item:
                def data(self, role):
                    return m.name
            return _Item()
        return None


class MapWidget(QWidget):
    """Modern visual map pool explorer with responsive grid, smart randomizer, and live drawer."""

    maps_changed = Signal(list)
    map_selected = Signal(object)
    avoid_recent_changed = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._maps: List[Map] = []
        self._disabled_names: set[str] = set()
        self._current_selected: Optional[Map] = None
        self._avoid_recent = 3
        self._recent_maps: list[str] = []
        self._current_filter_mode = "Todos"
        self._search_text = ""
        self._card_widgets: list[MapCardWidget] = []

        self._card_size = "medium"
        self._aspect_ratio = "auto"

        self._setup_ui()

    @property
    def list_widget(self):
        return _MapListCompatibilityAdapter(self)

    @property
    def current_map_mode(self):
        if not hasattr(self, "_lbl_current_map_mode"):
            self._lbl_current_map_mode = QLabel(self)
            self._lbl_current_map_mode.setStyleSheet("background-color: transparent;")
        if self._current_selected:
            self._lbl_current_map_mode.setText(self._current_selected.mode)
        return self._lbl_current_map_mode

    @property
    def current_map_name(self):
        if not hasattr(self, "_lbl_current_map_name"):
            self._lbl_current_map_name = QLabel(self)
        if self._current_selected:
            self._lbl_current_map_name.setText(self._current_selected.name)
        return self._lbl_current_map_name

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # 1. Top Controls Bar (Estandarizada a 48px)
        top_frame = QWidget(self)
        top_frame.setFixedHeight(48)
        top_frame.setStyleSheet("background-color: #16171D; border: 1px solid #282A33; border-radius: 8px;")
        top_bar = QHBoxLayout(top_frame)
        top_bar.setContentsMargins(10, 4, 10, 4)
        top_bar.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar mapa...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedWidth(155)
        self.search_input.textChanged.connect(self._on_search_changed)
        top_bar.addWidget(self.search_input)

        self.cb_sort = QComboBox()
        self.cb_sort.setView(QListView())
        self.cb_sort.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cb_sort.setFixedWidth(150)
        self.cb_sort.addItem("🌐 Modo + A-Z", "mode_name_asc")
        self.cb_sort.addItem("🔤 Nombre (A - Z)", "name_asc")
        self.cb_sort.addItem("🔤 Nombre (Z - A)", "name_desc")
        self.cb_sort.addItem("🗺️ Solo por Modo", "mode_only")
        self.cb_sort.addItem("✅ Activos primero", "active_first")
        self.cb_sort.currentIndexChanged.connect(self._on_sort_changed)
        top_bar.addWidget(self.cb_sort)

        # Scrollable Mode Pills
        self.pills_bar = ScrollablePillsWidget(self)
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self._mode_buttons: list[QPushButton] = []

        for mode in MODES_FILTER:
            btn = QPushButton(mode)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if mode == "Todos":
                btn.setChecked(True)
            btn.toggled.connect(lambda on, m=mode: on and self._on_mode_filter_changed(m))
            self.mode_group.addButton(btn)
            self._mode_buttons.append(btn)
            self.pills_bar.add_widget(btn)

        top_bar.addWidget(self.pills_bar, 1)

        self.lbl_stats = QLabel("🎯 0 / 0 Activos")
        self.lbl_stats.setObjectName("lblMapStats")
        self.lbl_stats.setAlignment(Qt.AlignCenter)
        self.lbl_stats.setFixedHeight(30)
        top_bar.addWidget(self.lbl_stats)

        self.btn_enable_all = QPushButton("✅ Activar")
        self.btn_enable_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_enable_all.setStyleSheet("padding: 5px 8px; font-size: 11px; font-weight: 700;")
        self.btn_enable_all.clicked.connect(self._enable_filtered_maps)
        top_bar.addWidget(self.btn_enable_all)

        self.btn_disable_all = QPushButton("❌ Desactivar")
        self.btn_disable_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_disable_all.setStyleSheet("padding: 5px 8px; font-size: 11px; font-weight: 700;")
        self.btn_disable_all.clicked.connect(self._disable_filtered_maps)
        top_bar.addWidget(self.btn_disable_all)

        layout.addWidget(top_frame)

        # 2. Grid de Mapas
        self.scroll = SmoothScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background-color: transparent;")

        self.outer_grid_layout = QVBoxLayout(self.grid_container)
        self.outer_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.outer_grid_layout.setSpacing(0)

        self.grid_layout = QGridLayout()
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setHorizontalSpacing(12)
        self.grid_layout.setVerticalSpacing(12)

        self.outer_grid_layout.addLayout(self.grid_layout)
        self.outer_grid_layout.addStretch(1)

        self.scroll.setWidget(self.grid_container)
        layout.addWidget(self.scroll, 1)

        # 3. Cajón Inferior Desacoplado
        self.drawer = MapSelectedDrawer(self)
        self.drawer.clear_requested.connect(self._clear_selected_map)
        self.drawer.avoid_recent_changed.connect(self._on_avoid_changed)
        layout.addWidget(self.drawer)

        # 4. Botón Central Protagónico Inferior de 46px (Idéntico a Mezclar Partida)
        bottom_actions = QHBoxLayout()
        bottom_actions.setContentsMargins(0, 2, 0, 0)
        self.btn_randomize = QPushButton("🎲  SORTEAR MAPA")
        self.btn_randomize.setObjectName("btnRandomizeMap")
        self.btn_randomize.setMinimumHeight(46)
        self.btn_randomize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_randomize.setToolTip("Sortear aleatoriamente un mapa del pool activo")
        self.btn_randomize.clicked.connect(self._randomize_map)
        bottom_actions.addWidget(self.btn_randomize, 1)
        layout.addLayout(bottom_actions)

        # Aliases de compatibilidad directa
        self.drawer_frame = self.drawer
        self.drawer_thumb = self.drawer.drawer_thumb
        self.lbl_drawer_name = self.drawer.lbl_drawer_name
        self.lbl_drawer_mode = self.drawer.lbl_drawer_mode
        self.btn_drawer_clear = self.drawer.btn_drawer_clear
        self.spin_avoid = self.drawer.spin_avoid

        self.apply_theme()

    def apply_theme(self):
        accent = theme.accent()

        if hasattr(self, "search_input"):
            self.search_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: #181A22;
                    border: 1px solid #2B2E38;
                    border-radius: 6px;
                    padding: 5px 8px;
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: 600;
                }}
                QLineEdit:focus {{ border-color: {accent}; }}
            """)

        if hasattr(self, "cb_sort"):
            self.cb_sort.setStyleSheet(f"""
                QComboBox {{
                    background-color: #181A22;
                    border: 1px solid #2B2E38;
                    border-radius: 6px;
                    padding: 5px 8px;
                    color: #E2E6F0;
                    font-size: 11px;
                    font-weight: 700;
                }}
                QComboBox:hover {{ border-color: #3E4352; }}
                QComboBox:focus {{ border-color: {accent}; }}
                QComboBox::drop-down {{ border: none; width: 20px; }}
            """)

        for btn in getattr(self, "_mode_buttons", []):
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #181A22;
                    border: 1px solid #2B2E38;
                    border-radius: 5px;
                    padding: 6px 12px;
                    color: #A0A5B2;
                    font-weight: 700;
                    font-size: 12px;
                }}
                QPushButton:checked {{
                    background-color: {theme.accent_rgba(0.14)};
                    border-color: {accent};
                    color: #FFFFFF;
                }}
                QPushButton:hover {{ background-color: #22252F; color: #FFFFFF; }}
            """)

        if hasattr(self, "lbl_stats"):
            self.lbl_stats.setStyleSheet(f"""
                QLabel#lblMapStats {{
                    font-size: 11px;
                    font-weight: 700;
                    color: #DDE2EE;
                    background-color: #171922;
                    border: 1px solid #2B2F3D;
                    border-radius: 6px;
                    padding: 2px 10px;
                }}
            """)

        if hasattr(self, "pills_bar"):
            self.pills_bar.apply_theme()

        if hasattr(self, "drawer"):
            self.drawer.apply_theme()

        if hasattr(self, "btn_randomize"):
            self.btn_randomize.setStyleSheet(f"""
                QPushButton#btnRandomizeMap {{
                    font-size: 14px;
                    font-weight: 900;
                    color: {accent};
                    background-color: rgba(20, 22, 30, 0.88);
                    border: 1px solid {accent};
                    border-radius: 8px;
                    letter-spacing: 0.5px;
                    padding: 6px 20px;
                }}
                QPushButton#btnRandomizeMap:hover {{
                    background-color: {theme.accent_rgba(0.16)};
                    border-color: {theme.accent_light()};
                    color: #FFFFFF;
                }}
                QPushButton#btnRandomizeMap:pressed {{
                    background-color: {theme.accent_rgba(0.28)};
                }}
            """)

        for card in self._card_widgets:
            card._apply_style()

    def set_card_preferences(self, size: str, aspect: str):
        self._card_size = size
        self._aspect_ratio = aspect
        for card in self._card_widgets:
            card.set_preferences(size, aspect)
        self._relayout_grid_columns(force=True)

    def set_maps(self, maps: List[Map]):
        self._maps = list(maps)
        self._disabled_names = {
            m.name for m in self._maps
            if hasattr(m, "enabled") and not m.enabled
        }
        self._maps = self._sort_maps(self._maps)
        self._rebuild_grid()

    def get_maps(self) -> List[Map]:
        return self._maps.copy()

    def set_avoid_recent(self, count: int):
        self._avoid_recent = count
        self.drawer.set_avoid_recent(count)

    def select_map(self, map_obj: Map | None):
        self._current_selected = map_obj
        if hasattr(self, "_lbl_current_map_name") and map_obj:
            self._lbl_current_map_name.setText(map_obj.name)
        if hasattr(self, "_lbl_current_map_mode") and map_obj:
            self._lbl_current_map_mode.setText(map_obj.mode)
        for card in self._card_widgets:
            card.set_selected(map_obj is not None and card.map_obj.name == map_obj.name)
        self.drawer.set_map(map_obj)

    def _clear_selected_map(self):
        self.select_map(None)
        parent_win = self.window()
        if hasattr(parent_win, "_clear_map"):
            parent_win._clear_map()

    def showEvent(self, event):
        super().showEvent(event)
        # Sincronización instantánea directa (cero delay, cero parpadeo)
        self._relayout_grid_columns(force=True)
        if hasattr(self, "pills_bar"):
            self.pills_bar.update_pills_geometry()
            self.pills_bar._check_overflow()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout_grid_columns(force=True)
        if hasattr(self, "pills_bar"):
            self.pills_bar._check_overflow()

    def _calculate_columns(self) -> int:
        w = self.scroll.viewport().width() if self.scroll.viewport() else 0
        if w <= 100:
            w = self.scroll.width()
        if w <= 100:
            w = self.width()
        if w <= 100 and self.window():
            w = max(1000, self.window().width() - 400)
        if w <= 100:
            w = 1100

        card_w = 190 if self._card_size == "small" else (300 if self._card_size == "large" else 235)
        cols = max(2, min(8, w // card_w))
        return cols

    def _sort_maps(self, maps: list[Map]) -> list[Map]:
        sort_mode = self.cb_sort.currentData() if hasattr(self, "cb_sort") else "mode_name_asc"

        if sort_mode == "name_asc":
            return sorted(maps, key=lambda m: m.name.casefold())
        elif sort_mode == "name_desc":
            return sorted(maps, key=lambda m: m.name.casefold(), reverse=True)
        elif sort_mode == "mode_only":
            return sorted(maps, key=lambda m: MODE_ORDER.get(m.mode, 99))
        elif sort_mode == "active_first":
            return sorted(maps, key=lambda m: (m.name in self._disabled_names, MODE_ORDER.get(m.mode, 99), m.name.casefold()))
        else:  # mode_name_asc
            return sorted(maps, key=lambda m: (MODE_ORDER.get(m.mode, 99), m.name.casefold()))

    def _on_sort_changed(self):
        self._maps = self._sort_maps(self._maps)
        self._rebuild_grid()

    def _rebuild_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._card_widgets.clear()

        for m in self._maps:
            is_active = m.name not in self._disabled_names
            card = MapCardWidget(
                m,
                is_active=is_active,
                card_size=self._card_size,
                aspect_ratio=self._aspect_ratio,
                parent=getattr(self, "grid_container", self),
            )
            card.clicked.connect(self._on_card_clicked)
            card.double_clicked.connect(self._on_card_double_clicked)
            card.status_toggled.connect(self._on_card_status_toggled)
            card.delete_requested.connect(self._on_card_delete_requested)

            if self._current_selected and self._current_selected.name == m.name:
                card.set_selected(True)

            self._card_widgets.append(card)

        self._filter_cards()
        self.drawer.set_map(self._current_selected)

    def _relayout_grid_columns(self, force: bool = False):
        cols = self._calculate_columns()
        visible_cards = [c for c in self._card_widgets if c.isVisible()]

        # Solo omitir si no se fuerza, las columnas no cambiaron Y la cantidad visible coincide exactamente
        if (
            not force
            and getattr(self, "_last_laid_cols", None) == cols
            and getattr(self, "_last_visible_count", None) == len(visible_cards)
            and self.grid_layout.count() == len(visible_cards)
        ):
            return

        self._last_laid_cols = cols
        self._last_visible_count = len(visible_cards)

        # 1. Despejar completamente el grid
        while self.grid_layout.count():
            self.grid_layout.takeAt(0)

        # 2. Resetear pesos de columnas
        for c in range(12):
            self.grid_layout.setColumnStretch(c, 0)

        # 3. Colocar tarjetas visibles de forma continua y limpia desde (0, 0)
        for i, card in enumerate(visible_cards):
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(card, row, col)

        # 4. Asignar expansión proporcional a las columnas ocupadas
        for c in range(cols):
            self.grid_layout.setColumnStretch(c, 1)
    def _filter_cards(self):
        active_count = 0
        visible_count = 0
        visible_active = 0

        for card in self._card_widgets:
            m = card.map_obj
            matches_search = not self._search_text or self._search_text in m.name.casefold()
            matches_mode = (
                self._current_filter_mode == "Todos"
                or m.mode.casefold() == self._current_filter_mode.casefold()
            )

            visible = matches_search and matches_mode
            card.setVisible(visible)

            if card.is_active():
                active_count += 1
            if visible:
                visible_count += 1
                if card.is_active():
                    visible_active += 1

        self._relayout_grid_columns(force=True)

        accent = theme.accent()
        if self._current_filter_mode == "Todos" and not self._search_text:
            self.lbl_stats.setText(f"🎯 <span style='color:{accent}; font-weight:900;'>{active_count}</span> / {len(self._maps)} Activos")
            self.btn_enable_all.setText("✅ Activar todos")
            self.btn_disable_all.setText("❌ Desactivar todos")
            self.btn_randomize.setText("🎲  SORTEAR MAPA")
        else:
            mode_label = self._current_filter_mode
            mode_color = MODE_COLORS.get(mode_label, accent)
            self.lbl_stats.setText(f"🎯 <span style='color:{mode_color}; font-weight:900;'>{visible_active}</span> / {visible_count} {mode_label}")
            self.btn_enable_all.setText(f"✅ Activar {mode_label}")
            self.btn_disable_all.setText(f"❌ Desactivar {mode_label}")
            self.btn_randomize.setText(f"🎲  SORTEAR {mode_label.upper()}")

    def _on_search_changed(self, text: str):
        self._search_text = text.strip().casefold()
        self._filter_cards()

    def _on_mode_filter_changed(self, mode: str):
        self._current_filter_mode = mode
        self._filter_cards()

    def _on_card_clicked(self, map_obj: Map):
        is_active = map_obj.name not in self._disabled_names
        self._on_card_status_toggled(map_obj, not is_active)

    def _on_card_status_toggled(self, map_obj: Map, is_active: bool):
        if is_active:
            self._disabled_names.discard(map_obj.name)
        else:
            self._disabled_names.add(map_obj.name)

        for m in self._maps:
            if m.name == map_obj.name:
                m.enabled = is_active
                break

        for card in self._card_widgets:
            if card.map_obj.name == map_obj.name:
                card.set_active(is_active)
                break

        self._filter_cards()
        self.maps_changed.emit(self._maps)

    def _on_card_double_clicked(self, map_obj: Map):
        self.select_map(map_obj)
        self.map_selected.emit(map_obj)
        p_window = self.window()
        if hasattr(p_window, "show_toast"):
            p_window.show_toast(f"🗺️ Mapa '{map_obj.name}' seleccionado para la partida", "success")

    def _on_card_delete_requested(self, map_obj: Map):
        reply = QMessageBox.question(
            self, "Eliminar mapa",
            f"¿Eliminar '{map_obj.name}' de la lista de mapas?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._maps = [m for m in self._maps if m.name != map_obj.name]
            self._disabled_names.discard(map_obj.name)
            self._rebuild_grid()
            self.maps_changed.emit(self._maps)

    def _enable_filtered_maps(self):
        for card in self._card_widgets:
            if card.isVisible():
                self._disabled_names.discard(card.map_obj.name)
                card.set_active(True)
                for m in self._maps:
                    if m.name == card.map_obj.name:
                        m.enabled = True
                        break
        self._filter_cards()
        self.maps_changed.emit(self._maps)

    def _disable_filtered_maps(self):
        for card in self._card_widgets:
            if card.isVisible():
                self._disabled_names.add(card.map_obj.name)
                card.set_active(False)
                for m in self._maps:
                    if m.name == card.map_obj.name:
                        m.enabled = False
                        break
        self._filter_cards()
        self.maps_changed.emit(self._maps)

    def _randomize_map(self):
        if self._current_filter_mode != "Todos":
            active_pool = [
                m for m in self._maps
                if m.name not in self._disabled_names and m.mode.casefold() == self._current_filter_mode.casefold()
            ]
        else:
            active_pool = [m for m in self._maps if m.name not in self._disabled_names]

        if not active_pool:
            mode_desc = f"en el modo '{self._current_filter_mode}'" if self._current_filter_mode != "Todos" else "en el pool"
            p_window = self.window()
            if hasattr(p_window, "show_toast"):
                p_window.show_toast(f"⚠️ No hay mapas activos {mode_desc} para sortear.", "warning")
            else:
                QMessageBox.warning(self, "Sin mapas", f"No hay mapas activos {mode_desc} para sortear.")
            return

        available = [m for m in active_pool if m.name not in self._recent_maps]
        if not available:
            available = active_pool

        selected = random.choice(available)

        self._recent_maps.insert(0, selected.name)
        self._recent_maps = self._recent_maps[:self._avoid_recent]

        self.select_map(selected)
        self.map_selected.emit(selected)
        p_window = self.window()
        if hasattr(p_window, "show_toast"):
            p_window.show_toast(f"🎲 Mapa sorteado: {selected.name} ({selected.mode})", "info")

    def restore_defaults(self):
        storage = Storage()
        self._maps = sorted(storage.restore_default_maps(), key=lambda m: (MODE_ORDER.get(m.mode, 99), m.name))
        self._disabled_names.clear()
        self._rebuild_grid()
        self.maps_changed.emit(self._maps)

    def _on_avoid_changed(self, value: int):
        self._avoid_recent = value
        self.avoid_recent_changed.emit(value)

    def _import_maps(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar mapas", "", "JSON Files (*.json);;Text Files (*.txt)"
        )
        if not path:
            return
        try:
            storage = Storage()
            if path.endswith(".json"):
                maps = storage.import_maps(path)
            else:
                with open(path, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                maps, _ = validate_map_import(lines)

            existing = {(m.name, m.mode) for m in self._maps}
            for m in maps:
                if (m.name, m.mode) not in existing:
                    self._maps.append(m)

            self._maps.sort(key=lambda m: (MODE_ORDER.get(m.mode, 99), m.name))
            self._rebuild_grid()
            self.maps_changed.emit(self._maps)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo importar: {e}")

    def _export_maps(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar mapas", "maps.json", "JSON Files (*.json);;Text Files (*.txt)"
        )
        if not path:
            return
        try:
            storage = Storage()
            if path.endswith(".json"):
                storage.export_maps(self._maps, path)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    for m in self._maps:
                        f.write(f"{m.name} | {m.mode}\n")
            QMessageBox.information(self, "Éxito", "Mapas exportados correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar: {e}")
