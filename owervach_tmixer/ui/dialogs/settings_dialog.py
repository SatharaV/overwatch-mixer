"""Settings dialog with modular categories, persistent geometry, theme switcher, and reactive Apply."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

import platformdirs
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer import APP_NAME
from owervach_tmixer.core.models import Hero, Map, TeamComposition
from owervach_tmixer.core.settings import SettingsManager
from owervach_tmixer.core.shuffle_history import ShuffleHistoryManager
from owervach_tmixer.ui.styles import theme
from owervach_tmixer.ui.widgets.map_widget import ScrollablePillsWidget
from owervach_tmixer.ui.widgets.smooth_scroll import SmoothScrollArea
from owervach_tmixer.ui.dialogs.common_geometry import PersistentGeometryMixin

from .settings_tabs.common import NoWheelEventFilter
from .settings_tabs.tab_appearance import build_appearance_tab
from .settings_tabs.tab_backup import build_backup_tab
from .settings_tabs.tab_about import build_about_tab
from .settings_tabs.tab_content import (
    build_content_tab,
    create_custom_hero_row,
    create_custom_map_row,
)
from .settings_tabs.tab_gameplay import (
    build_maps_tab,
    build_players_tab,
    build_roles_bans_tab,
    build_shuffle_tab,
)

if TYPE_CHECKING:
    from owervach_tmixer.ui.main_window import MainWindow

DEFAULT_TAB_ORDER = [
    "appearance", "content", "shuffle", "roles_bans", "maps", "players", "backup", "about"
]

TAB_REGISTRY: dict[str, tuple[str, Callable]] = {
    "appearance": ("🎨 Personalizar", build_appearance_tab),
    "content": ("➕ Creador & Packs", build_content_tab),
    "shuffle": ("🔀 Mezcla", build_shuffle_tab),
    "roles_bans": ("🎭 Roles & Bans", build_roles_bans_tab),
    "maps": ("🗺️ Mapas", build_maps_tab),
    "players": ("👥 Jugadores", build_players_tab),
    "backup": ("💾 Respaldos", build_backup_tab),
    "about": ("ℹ️ Acerca de", build_about_tab),
}


class _SettingsPageWidget(QWidget):
    """Contenedor de pestaña que neutraliza su minimumSizeHint horizontal para evitar que fuerce scrollbar."""
    def minimumSizeHint(self):
        s = super().minimumSizeHint()
        from PySide6.QtCore import QSize
        return QSize(0, s.height())


class _SettingsScrollArea(SmoothScrollArea):
    """ScrollArea que acopla rígidamente el ancho de su contenido al ancho visible del viewport."""
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.widget():
            vw = self.viewport().width()
            if self.widget().width() != vw:
                self.widget().setFixedWidth(vw)


class SettingsDialog(QDialog, PersistentGeometryMixin):
    """Modern esports settings dialog with 8 decoupled categories, persistent geometry, and live theme engine."""

    def __init__(
        self,
        parent: MainWindow,
        settings_manager: SettingsManager,
        shuffle_history: ShuffleHistoryManager,
    ):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.shuffle_history = shuffle_history
        self.setWindowTitle("Configuración del Sistema")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)
        self.setStyleSheet(theme.build_stylesheet())

        raw_order = getattr(self.settings_manager.settings, "settings_tab_order", DEFAULT_TAB_ORDER)
        valid_raw = [k for k in raw_order if k in TAB_REGISTRY]
        self._tab_order = list(dict.fromkeys(valid_raw + [k for k in DEFAULT_TAB_ORDER if k in TAB_REGISTRY]))

        self._pages_by_key: dict[str, QWidget] = {}
        self._buttons_by_key: dict[str, QPushButton] = {}
        self._is_loading = True
        self._has_pending_changes = False

        # Guardar estado original para reversión armónica en caso de cancelar
        self._original_theme_name = getattr(self.settings_manager.settings, "theme_name", "obsidian")
        self._original_accent = self.settings_manager.settings.accent_color

        self._setup_ui()
        self._load_settings()
        self._connect_dirty_listeners()
        self._is_loading = False
        self._update_apply_button_state()

        self.setup_persistent_geometry(
            settings_manager=self.settings_manager,
            window_id="settings_dialog",
            default_size=(720, 620),
            min_size=(580, 480),
        )

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Header Bar
        top_bar = QWidget()
        top_bar.setStyleSheet("background-color: #16171E; border-bottom: 1px solid #262936;")
        top_bar.setFixedHeight(48)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 0, 16, 0)

        self.title_label = QLabel("⚙️  CONFIGURACIÓN DEL SISTEMA")
        self.title_label.setStyleSheet(
            f"font-size: 13px; font-weight: 900; color: {theme.accent()}; letter-spacing: 0.8px;"
        )
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()

        btn_tip = QLabel("💡 Clic derecho para reordenar")
        btn_tip.setStyleSheet("font-size: 11px; color: #6E7484; font-weight: 600; background: transparent; border: none;")
        top_layout.addWidget(btn_tip)
        layout.addWidget(top_bar)

        self._no_wheel_filter = NoWheelEventFilter(self)
        self.installEventFilter(self._no_wheel_filter)

        # 2. Master Navigation Bar
        self.nav_wrapper = QWidget()
        self.nav_wrapper.setStyleSheet("background-color: #14151C; border-bottom: 1px solid #262936;")
        self.nav_wrapper.setFixedHeight(46)
        self.nw_layout = QHBoxLayout(self.nav_wrapper)
        self.nw_layout.setContentsMargins(8, 3, 8, 3)

        self.pills_bar = ScrollablePillsWidget(self.nav_wrapper)
        self._tab_group = QButtonGroup(self)
        self._tab_group.setExclusive(True)
        self._tab_buttons: list[QPushButton] = []
        self._settings_stack = QStackedWidget()

        for key, (label, creator_fn) in TAB_REGISTRY.items():
            # Fix global arquitectónico: Contención estricta al ancho del viewport en todas las pestañas
            scroll = _SettingsScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.horizontalScrollBar().setEnabled(False)
            scroll.setStyleSheet("""
                QScrollArea { background-color: transparent; border: none; }
                QScrollBar:vertical {
                    background: #14151B;
                    width: 8px;
                    border: none;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #2D303D;
                    min-height: 24px;
                    border-radius: 4px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #61ab02;
                }
                QScrollBar:horizontal {
                    height: 0px;
                    border: none;
                    background: transparent;
                }
            """)

            page = _SettingsPageWidget()
            page.setStyleSheet("background-color: transparent;")
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(14, 10, 14, 10)
            page_layout.setSpacing(12)
            creator_fn(self, page_layout)
            page_layout.addStretch()

            scroll.setWidget(page)
            self._pages_by_key[key] = scroll
            self._settings_stack.addWidget(scroll)

        self._rebuild_pills_bar(active_key=self._tab_order[0])

        self.nw_layout.addWidget(self.pills_bar)
        layout.addWidget(self.nav_wrapper)
        layout.addWidget(self._settings_stack, 1)

        # 3. Footer Bar: Tríada [ Aceptar ] [ Cancelar ] [ Aplicar ]
        footer_bar = QWidget()
        footer_bar.setStyleSheet("background-color: #14151B; border-top: 1px solid #242734;")
        footer_bar.setFixedHeight(50)
        footer_layout = QHBoxLayout(footer_bar)
        footer_layout.setContentsMargins(14, 0, 14, 0)
        footer_layout.setSpacing(8)

        btn_reset_defaults = QPushButton("↺ Predeterminados")
        btn_reset_defaults.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset_defaults.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                font-weight: 700;
                color: #A0A5B5;
                background-color: #1C1E26;
                border: 1px solid #2C2F3C;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                color: #FFAA00;
                border-color: #784E12;
                background-color: #272015;
            }
        """)
        btn_reset_defaults.clicked.connect(self._confirm_reset_defaults)
        footer_layout.addWidget(btn_reset_defaults)

        footer_layout.addStretch()

        self.btn_accept = QPushButton("Aceptar")
        self.btn_accept.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_accept.setProperty("primary", True)
        self.btn_accept.setStyleSheet(f"""
            QPushButton {{
                font-size: 12px;
                font-weight: 700;
                color: #FFFFFF;
                background-color: {theme.accent()};
                border: 1px solid {theme.accent_light()};
                border-radius: 6px;
                padding: 6px 18px;
            }}
            QPushButton:hover {{
                background-color: {theme.accent_lighter()};
                border-color: #FFFFFF;
            }}
        """)
        self.btn_accept.clicked.connect(self.accept)
        footer_layout.addWidget(self.btn_accept)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                font-weight: 700;
                color: #C6CAD6;
                background-color: #1E212B;
                border: 1px solid #2F3342;
                border-radius: 6px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #282C3A;
                border-color: #3F4558;
                color: #FFFFFF;
            }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        footer_layout.addWidget(self.btn_cancel)

        self.btn_apply = QPushButton("Aplicar")
        self.btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply.clicked.connect(self._on_apply_clicked)
        footer_layout.addWidget(self.btn_apply)

        layout.addWidget(footer_bar)

    def _on_theme_skin_selected(self, index: int):
        """Maneja la selección de tema: requiere confirmación explícita (Aplicar o Aceptar)."""
        tid = self.cb_theme_skin.currentData()
        themes_reg = theme.get_theme_manager().get_registered_themes()
        if tid in themes_reg:
            _, desc = themes_reg[tid]
            self.lbl_theme_desc.setText(desc)

        if not self._is_loading:
            # No se aplica inmediatamente; se requiere presionar Aplicar o Aceptar
            self._mark_dirty()

    def _apply_dialog_theme(self):
        """Re-renderiza estilos dinámicos dentro de la ventana de configuración."""
        accent = theme.accent()
        self.title_label.setStyleSheet(
            f"font-size: 13px; font-weight: 900; color: {accent}; letter-spacing: 0.8px;"
        )
        self.btn_accept.setStyleSheet(f"""
            QPushButton {{
                font-size: 12px;
                font-weight: 700;
                color: #FFFFFF;
                background-color: {accent};
                border: 1px solid {theme.accent_light()};
                border-radius: 6px;
                padding: 6px 18px;
            }}
            QPushButton:hover {{
                background-color: {theme.accent_lighter()};
                border-color: #FFFFFF;
            }}
        """)
        for btn in self._tab_buttons:
            self._apply_pill_style(btn)
        self._update_apply_button_state()

    def _mark_dirty(self):
        """Notifica que se produjo un cambio pendiente y activa el botón Aplicar."""
        if self._is_loading:
            return
        self._has_pending_changes = True
        self._update_apply_button_state()

    def _update_apply_button_state(self):
        accent = theme.accent()
        if self._has_pending_changes:
            self.btn_apply.setEnabled(True)
            self.btn_apply.setStyleSheet(f"""
                QPushButton {{
                    font-size: 12px;
                    font-weight: 700;
                    color: #FFFFFF;
                    background-color: #222838;
                    border: 1px solid {accent};
                    border-radius: 6px;
                    padding: 6px 16px;
                }}
                QPushButton:hover {{
                    background-color: {theme.accent_rgba(0.25)};
                    color: #FFFFFF;
                }}
            """)
        else:
            self.btn_apply.setEnabled(False)
            self.btn_apply.setStyleSheet("""
                QPushButton {
                    font-size: 12px;
                    font-weight: 600;
                    color: #555A6B;
                    background-color: #16171E;
                    border: 1px solid #242734;
                    border-radius: 6px;
                    padding: 6px 16px;
                }
            """)

    def _connect_dirty_listeners(self):
        """Conecta eventos de cambio en todos los controles a _mark_dirty."""
        for child in self.findChildren(QSpinBox):
            child.valueChanged.connect(self._mark_dirty)
        for child in self.findChildren(QComboBox):
            if child is not self.cb_theme_skin:
                child.currentIndexChanged.connect(self._mark_dirty)
        for child in self.findChildren(QCheckBox):
            child.toggled.connect(self._mark_dirty)
        for child in self.findChildren(QLineEdit):
            child.textChanged.connect(self._mark_dirty)

    def _on_apply_clicked(self):
        """Aplica los cambios sin cerrar y consolida el nuevo tema en disco."""
        self._save_settings()
        self._original_theme_name = getattr(self.settings_manager.settings, "theme_name", "obsidian")
        self._original_accent = self.settings_manager.settings.accent_color
        self._has_pending_changes = False
        self._update_apply_button_state()
        parent = self.parent()
        if parent and hasattr(parent, "show_toast"):
            parent.show_toast("Ajustes aplicados correctamente", "success")

    def _rebuild_pills_bar(self, active_key: str | None = None):
        if hasattr(self, "pills_bar"):
            while self.pills_bar.pills_layout.count():
                item = self.pills_bar.pills_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        for btn in list(self._tab_buttons):
            self._tab_group.removeButton(btn)
        self._tab_buttons.clear()
        self._buttons_by_key.clear()

        for key in self._tab_order:
            label, _ = TAB_REGISTRY[key]
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip("Clic derecho para mover esta pestaña")
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, k=key, b=btn: self._show_tab_context_menu(b.mapToGlobal(pos), k)
            )

            self._apply_pill_style(btn)
            self._tab_group.addButton(btn)
            self._tab_buttons.append(btn)
            self._buttons_by_key[key] = btn
            self.pills_bar.add_widget(btn)

            page_widget = self._pages_by_key[key]
            stack_idx = self._settings_stack.indexOf(page_widget)
            btn.toggled.connect(
                lambda on, i=stack_idx: on and self._settings_stack.setCurrentIndex(i)
            )

        target_key = active_key if (active_key and active_key in self._buttons_by_key) else self._tab_order[0]
        self._buttons_by_key[target_key].setChecked(True)

    def _apply_pill_style(self, button: QPushButton):
        accent = theme.accent()
        accent_bg = theme.accent_rgba(0.18)
        button.setStyleSheet(f"""
            QPushButton {{
                font-size: 11px;
                font-weight: 700;
                color: #9297A5;
                background-color: #1A1C23;
                border: 1px solid #282C38;
                border-radius: 6px;
                padding: 5px 12px;
            }}
            QPushButton:hover {{
                color: #FFFFFF;
                background-color: #222530;
                border-color: #3B4052;
            }}
            QPushButton:checked {{
                color: #FFFFFF;
                background-color: {accent_bg};
                border: 1px solid {accent};
            }}
            QPushButton:checked:hover {{
                color: #FFFFFF;
                background-color: {accent_bg};
                border: 1px solid {accent};
            }}
        """)

    def _show_tab_context_menu(self, global_pos: QPoint, key: str):
        menu = QMenu(self)
        idx = self._tab_order.index(key)

        act_left = QAction("⬅️ Mover a la izquierda", self)
        act_left.setEnabled(idx > 0)
        act_left.triggered.connect(lambda: self._move_tab(key, -1))
        menu.addAction(act_left)

        act_right = QAction("➡️ Mover a la derecha", self)
        act_right.setEnabled(idx < len(self._tab_order) - 1)
        act_right.triggered.connect(lambda: self._move_tab(key, 1))
        menu.addAction(act_right)

        menu.addSeparator()

        act_reset = QAction("↺ Restablecer orden predeterminado", self)
        act_reset.triggered.connect(self._reset_tab_order)
        menu.addAction(act_reset)

        menu.exec(global_pos)

    def _move_tab(self, key: str, delta: int):
        idx = self._tab_order.index(key)
        new_idx = idx + delta
        if 0 <= new_idx < len(self._tab_order):
            self._tab_order.insert(new_idx, self._tab_order.pop(idx))
            self.settings_manager.settings.settings_tab_order = list(self._tab_order)
            self.settings_manager.save()
            self._rebuild_pills_bar(active_key=key)

    def _reset_tab_order(self):
        self._tab_order = list(DEFAULT_TAB_ORDER)
        self.settings_manager.settings.settings_tab_order = list(self._tab_order)
        self.settings_manager.save()
        self._rebuild_pills_bar(active_key=self._tab_order[0])

    def _set_accent_hex(self, hex_color: str):
        color = QColor(hex_color)
        old_hex = getattr(self, "_accent_hex", "")
        self._accent_hex = color.name().lower() if color.isValid() else theme.accent()
        self.btn_accent_swatch.setStyleSheet(
            f"background-color: {self._accent_hex}; border: 1px solid #666666; border-radius: 4px;"
        )
        for btn, h_color in self._accent_preset_hexes.items():
            btn.blockSignals(True)
            btn.setChecked(QColor(h_color).name().lower() == self._accent_hex)
            btn.blockSignals(False)
        self._update_hex_field()
        self._update_rgb_field()

        # Actualizar visualmente la ventana con el nuevo acento
        self._apply_dialog_theme()

        if old_hex and old_hex.lower() != self._accent_hex.lower():
            self._mark_dirty()

    def _update_hex_field(self):
        self.edit_hex.blockSignals(True)
        self.edit_hex.setText(self._accent_hex.upper())
        self.edit_hex.blockSignals(False)

    def _update_rgb_field(self):
        color = QColor(self._accent_hex)
        rgb = f"{color.red()}, {color.green()}, {color.blue()}"
        self.edit_rgb.blockSignals(True)
        self.edit_rgb.setText(rgb)
        self.edit_rgb.blockSignals(False)

    def _on_hex_edited(self, text: str):
        raw = text.strip()
        if not raw.startswith("#"):
            raw = "#" + raw
        if len(raw) != 7:
            return
        color = QColor(raw)
        if color.isValid():
            self._set_accent_hex(raw)

    def _on_rgb_edited(self, text: str):
        parts = [p.strip() for p in text.split(",")]
        if len(parts) != 3:
            return
        try:
            r, g, b = (int(p) for p in parts)
        except ValueError:
            return
        if not all(0 <= c <= 255 for c in (r, g, b)):
            return
        self._set_accent_hex(f"#{r:02X}{g:02X}{b:02X}")

    def _pick_accent_color(self):
        color = QColorDialog.getColor(QColor(self._accent_hex), self, "Color principal")
        if color.isValid():
            self._set_accent_hex(color.name().lower())

    def _load_settings(self):
        s = self.settings_manager.settings

        # Cargar tema activo en el combo
        current_theme_id = getattr(s, "theme_name", "obsidian")
        for i in range(self.cb_theme_skin.count()):
            if self.cb_theme_skin.itemData(i) == current_theme_id:
                self.cb_theme_skin.setCurrentIndex(i)
                break
        themes_reg = theme.get_theme_manager().get_registered_themes()
        if current_theme_id in themes_reg:
            self.lbl_theme_desc.setText(themes_reg[current_theme_id][1])

        for i in range(self.cb_shuffle_mode.count()):
            if self.cb_shuffle_mode.itemData(i) == s.shuffle_mode:
                self.cb_shuffle_mode.setCurrentIndex(i)
                break

        self.spin_candidates.setValue(s.diversity_candidates)
        self.spin_history_size.setValue(s.history_size)
        self.spin_avoid_maps.setValue(s.avoid_recent_maps)

        curr_policy = getattr(s, "rotation_policy", "continuous")
        if hasattr(self, "cb_rotation_policy"):
            for i in range(self.cb_rotation_policy.count()):
                if self.cb_rotation_policy.itemData(i) == curr_policy:
                    self.cb_rotation_policy.setCurrentIndex(i)
                    break
        if hasattr(self, "spin_rotation_batch"):
            self.spin_rotation_batch.setValue(getattr(s, "rotation_batch_size", 2))
        if hasattr(self, "spin_min_shield"):
            self.spin_min_shield.setValue(getattr(s, "min_matches_shield", 2))
        if hasattr(self, "spin_streamer_rest"):
            self.spin_streamer_rest.setValue(getattr(s, "streamer_rest_interval", 0))
        if hasattr(self, "chk_auto_map"):
            self.chk_auto_map.setChecked(getattr(s, "auto_map", True))

        card_size = getattr(s, "map_card_size", "medium")
        for i in range(self.cb_map_size.count()):
            if self.cb_map_size.itemData(i) == card_size:
                self.cb_map_size.setCurrentIndex(i)
                break

        card_aspect = getattr(s, "map_card_aspect", "auto")
        for i in range(self.cb_map_aspect.count()):
            if self.cb_map_aspect.itemData(i) == card_aspect:
                self.cb_map_aspect.setCurrentIndex(i)
                break

        self.chk_auto_roles.setChecked(s.auto_roles)
        self.chk_auto_roles.setEnabled(s.show_roles)
        if not s.show_roles:
            self.chk_auto_roles.setChecked(False)

        self.spin_5v5_tank.setValue(s.composition_5v5.tank)
        self.spin_5v5_damage.setValue(s.composition_5v5.damage)
        self.spin_5v5_support.setValue(s.composition_5v5.support)
        self.spin_6v6_tank.setValue(s.composition_6v6.tank)
        self.spin_6v6_damage.setValue(s.composition_6v6.damage)
        self.spin_6v6_support.setValue(s.composition_6v6.support)

        self.chk_auto_bans.setChecked(s.auto_bans)
        self.spin_max_bans.setValue(s.max_bans)
        self.spin_max_bans_per_role.setValue(s.max_bans_per_role)
        self.spin_portrait_size.setValue(getattr(s, "ban_portrait_size", 48))
        if hasattr(self, "spin_bans_rows"):
            self.spin_bans_rows.setValue(getattr(s, "bans_visible_rows", 2))

        self.edit_team1.setText(s.team1_name)
        self.edit_team2.setText(s.team2_name)
        self.chk_dnd_swap.setChecked(s.dnd_cross_team_swap)
        self.chk_auto_caps.setChecked(getattr(s, "auto_capitalize_names", True))
        if hasattr(self, "chk_vsync"):
            self.chk_vsync.setChecked(getattr(s, "vsync", True))
        self._set_accent_hex(s.accent_color)

        self.spin_slot_font_size.setValue(getattr(s, "slot_font_size", 13))
        curr_weight = getattr(s, "slot_font_weight", "bold")
        for i in range(self.cb_slot_font_weight.count()):
            if self.cb_slot_font_weight.itemData(i) == curr_weight:
                self.cb_slot_font_weight.setCurrentIndex(i)
                break

        is_dyn = getattr(s, "slot_dynamic_font", True)
        if hasattr(self, "cb_dynamic_font"):
            for i in range(self.cb_dynamic_font.count()):
                if self.cb_dynamic_font.itemData(i) == is_dyn:
                    self.cb_dynamic_font.setCurrentIndex(i)
                    break

        role_style = getattr(s, "role_badge_style", "emoji")
        if hasattr(self, "cb_role_badge_style"):
            for i in range(self.cb_role_badge_style.count()):
                if self.cb_role_badge_style.itemData(i) == role_style:
                    self.cb_role_badge_style.setCurrentIndex(i)
                    break

        b_outlines = getattr(s, "slot_badge_outlines", False)
        if hasattr(self, "cb_badge_outlines"):
            for i in range(self.cb_badge_outlines.count()):
                if self.cb_badge_outlines.itemData(i) == b_outlines:
                    self.cb_badge_outlines.setCurrentIndex(i)
                    break

        curr_align = getattr(s, "slot_text_align", "center")
        for i in range(self.cb_slot_align.count()):
            if self.cb_slot_align.itemData(i) == curr_align:
                self.cb_slot_align.setCurrentIndex(i)
                break

        curr_tier_ratio = getattr(s, "tier_export_ratio", "16:9")
        if hasattr(self, "cb_tier_export_ratio"):
            for i in range(self.cb_tier_export_ratio.count()):
                if self.cb_tier_export_ratio.itemData(i) == curr_tier_ratio:
                    self.cb_tier_export_ratio.setCurrentIndex(i)
                    break
        self.spin_tier_hero_size.setValue(getattr(s, "tier_hero_size", 76))
        self.spin_tier_map_w.setValue(getattr(s, "tier_map_width", 125))
        self.spin_tier_map_h.setValue(getattr(s, "tier_map_height", 75))
        self.spin_tier_map_font.setValue(getattr(s, "tier_map_font_size", 14))
        self.spin_tier_player_w.setValue(getattr(s, "tier_player_width", 125))
        self.spin_tier_player_h.setValue(getattr(s, "tier_player_height", 75))
        if hasattr(self, "chk_tier_watermark_export"):
            self.chk_tier_watermark_export.setChecked(getattr(s, "tier_show_watermark_export", True))
        if hasattr(self, "chk_tier_watermark_ui"):
            self.chk_tier_watermark_ui.setChecked(getattr(s, "tier_show_watermark_ui", True))

    def _clear_shuffle_history(self):
        reply = QMessageBox.question(
            self, "Limpiar historial",
            "¿Eliminar todo el historial de mezclas? Esto afectará la diversidad de futuras mezclas.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.shuffle_history.clear()
            parent_window = self.parent()
            if parent_window is not None and hasattr(parent_window, "status_bar"):
                parent_window.status_bar.showMessage("Historial de mezclas limpiado", 3000)

    def _purge_invalid_saved_players(self):
        parent: MainWindow = self.parent()
        if not parent or not hasattr(parent, "_roster"):
            return

        from owervach_tmixer.ui.widgets.saved_panel import sanitize_player_name
        before = len(parent._roster.saved)
        clean_list = []
        for p in parent._roster.saved:
            if sanitize_player_name(p.name):
                clean_list.append(p)

        removed = before - len(clean_list)
        parent._roster.saved = clean_list
        parent._after_roster_change()
        parent.show_toast(f"🧹 Se purgaron {removed} entradas de código/inválidas. Quedan {len(clean_list)} jugadores.", "success")

    def _reset_all_players_mmr(self):
        reply = QMessageBox.question(
            self,
            "⚡ Restablecer MMR Globalmente",
            "¿Deseas restablecer el MMR de TODOS los jugadores al valor base (5)?\n\n"
            "• Afectará a jugadores Guardados, en Zona de Espera y en Equipos.\n"
            "• Se reiniciarán el MMR manual, calibraciones de IA y estadísticas de partidas.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        parent = self.parent()
        if not parent or not hasattr(parent, "_roster"):
            return

        roster = parent._roster
        count = 0
        all_players = list(roster.saved) + list(roster.bench) + [p for p in roster.team1_slots if p] + [p for p in roster.team2_slots if p]
        seen = set()
        for p in all_players:
            if p and p.name not in seen:
                seen.add(p.name)
                p.reset_mmr(5)
                count += 1

        parent.storage.save_roster(roster)
        parent._after_roster_change()
        if hasattr(parent, "tier_maker"):
            parent.tier_maker.reload_bank()
        parent.show_toast(f"⚡ MMR de {count} jugadores restablecido a 5 correctamente", "success")

    def _clear_all_saved_players(self):
        reply = QMessageBox.question(
            self, "Vaciar jugadores guardados",
            "¿Deseas eliminar a todos los jugadores de tu lista de Guardados? (No afectará a los equipos actuales).",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            parent: MainWindow = self.parent()
            if parent and hasattr(parent, "_roster"):
                count = len(parent._roster.saved)
                parent._roster.saved.clear()
                parent._after_roster_change()
                parent.show_toast(f"🗑️ Se vaciaron {count} jugadores guardados.", "info")

    def _open_hero_tags_editor(self):
        try:
            from owervach_tmixer.ui.dialogs.hero_tags_dialog import HeroTagsDialog
            diag = HeroTagsDialog(self.parent())
            diag.exec()
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"Editor de etiquetas no disponible: {exc}")

    def _export_full_zip_pack(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Paquete Completo", "OverwatchMixer_CustomPack.zip", "ZIP Packages (*.zip)"
        )
        if not path:
            return
        try:
            parent: MainWindow = self.parent()
            parent.storage.export_full_pack_zip(path)
            parent.show_toast(f"📦 Paquete guardado en '{Path(path).name}'", "success")
        except Exception as exc:
            QMessageBox.critical(self, "Error al exportar", f"No se pudo crear el paquete ZIP: {exc}")

    def _import_full_zip_pack(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar Paquete Completo", "", "ZIP Packages (*.zip)"
        )
        if not path:
            return
        try:
            parent: MainWindow = self.parent()
            success = parent.storage.import_full_pack_zip(path)
            if success:
                parent._load_data()
                self._load_settings()
                self._refresh_custom_content_lists()
                parent.show_toast("✅ Paquete completo importado y sincronizado", "success")
            else:
                QMessageBox.warning(self, "Error", "No se pudo leer el archivo ZIP.")
        except Exception as exc:
            QMessageBox.critical(self, "Error al importar", f"Error al procesar el archivo ZIP: {exc}")

    def _on_add_hero_clicked(self):
        self.parent()._add_custom_hero()
        self._refresh_custom_content_lists()

    def _on_add_map_clicked(self):
        self.parent()._add_custom_map()
        self._refresh_custom_content_lists()

    def _refresh_custom_content_lists(self):
        if not hasattr(self, "_custom_layout"):
            return
        while self._custom_layout.count():
            item = self._custom_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        parent: MainWindow = self.parent()
        if not parent:
            return

        try:
            defaults_maps = {m.name.casefold() for m in parent.storage._load_default_maps()}
            defaults_heroes = {h.name.casefold() for h in parent.storage._load_default_heroes()}
            custom_maps = [m for m in parent.map_widget.get_maps() if m.name.casefold() not in defaults_maps]
            custom_heroes = [
                h for h in parent.hero_widget.get_heroes()
                if (getattr(h, "original_name", None) or h.name).casefold() not in defaults_heroes
            ]
        except Exception:
            return

        if not custom_maps and not custom_heroes:
            empty = QLabel("ℹ️ No has añadido héroes ni mapas personalizados aún.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #727684; font-size: 12px; font-weight: 600; padding: 12px 0;")
            self._custom_layout.addWidget(empty)
            return

        if custom_heroes:
            lbl_h = QLabel(f"🎭 HÉROES PERSONALIZADOS ({len(custom_heroes)})")
            lbl_h.setStyleSheet("font-size: 11px; font-weight: 800; color: #B0B5C2; margin-top: 2px;")
            self._custom_layout.addWidget(lbl_h)
            for hero in custom_heroes:
                self._custom_layout.addWidget(create_custom_hero_row(self, hero))

        if custom_maps:
            lbl_m = QLabel(f"🗺️ MAPAS PERSONALIZADOS ({len(custom_maps)})")
            lbl_m.setStyleSheet("font-size: 11px; font-weight: 800; color: #B0B5C2; margin-top: 6px;")
            self._custom_layout.addWidget(lbl_m)
            for map_obj in custom_maps:
                self._custom_layout.addWidget(create_custom_map_row(self, map_obj))

    def _delete_custom_hero(self, hero: Hero):
        reply = QMessageBox.question(
            self, "Eliminar héroe personalizado",
            f"¿Deseas eliminar al héroe '{hero.name}' y su foto del sistema?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            parent: MainWindow = self.parent()
            portraits_dir = Path(platformdirs.user_data_dir(APP_NAME)) / "hero_portraits"
            safe_name = "".join(char for char in (hero.original_name or hero.name) if char.isalnum() or char in " -_").strip()
            for ext in (".png", ".jpg", ".jpeg", ".webp"):
                img = portraits_dir / f"{safe_name}{ext}"
                if img.exists():
                    try:
                        img.unlink(missing_ok=True)
                    except Exception:
                        pass

            heroes = [h for h in parent.hero_widget.get_heroes() if h.name.casefold() != hero.name.casefold()]
            parent.hero_widget.set_heroes(heroes)
            parent._on_heroes_changed(heroes)
            parent.show_toast(f"🗑️ Héroe '{hero.name}' eliminado", "info")
            self._refresh_custom_content_lists()

    def _delete_custom_map(self, map_obj: Map):
        reply = QMessageBox.question(
            self, "Eliminar mapa personalizado",
            f"¿Deseas eliminar el mapa '{map_obj.name}' y su foto del sistema?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            parent: MainWindow = self.parent()
            maps_dir = Path(platformdirs.user_data_dir(APP_NAME)) / "Maps" / map_obj.mode
            for ext in (".png", ".jpg", ".jpeg", ".webp"):
                img = maps_dir / f"{map_obj.name}{ext}"
                if img.exists():
                    try:
                        img.unlink(missing_ok=True)
                    except Exception:
                        pass

            maps = [m for m in parent.map_widget.get_maps() if m.name.casefold() != map_obj.name.casefold()]
            parent.map_widget.set_maps(maps)
            parent._on_maps_changed(maps)

            if parent._current_match and parent._current_match.map and parent._current_match.map.name == map_obj.name:
                parent._clear_map()

            parent.show_toast(f"🗑️ Mapa '{map_obj.name}' eliminado", "info")
            self._refresh_custom_content_lists()

    def _restore_default_maps(self):
        reply = QMessageBox.question(
            self, "Restablecer mapas",
            "¿Deseas restaurar la lista oficial completa de mapas de Overwatch?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            parent: MainWindow = self.parent()
            maps = parent.storage.restore_default_maps()
            parent.map_widget.set_maps(maps)
            parent._on_maps_changed(maps)
            parent.show_toast("✅ Mapas oficiales restaurados", "success")
            self._refresh_custom_content_lists()

    def _restore_default_heroes(self):
        reply = QMessageBox.question(
            self, "Restablecer héroes",
            "¿Deseas restaurar la lista oficial completa de héroes de Overwatch?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            parent: MainWindow = self.parent()
            heroes = parent.storage.restore_default_heroes()
            parent.hero_widget.set_heroes(heroes)
            parent._on_heroes_changed(heroes)
            parent.show_toast("✅ Héroes oficiales restaurados", "success")
            self._refresh_custom_content_lists()

    def _on_factory_reset_clicked(self):
        reply1 = QMessageBox.warning(
            self,
            "⚠️ ¿Restablecer a Estado de Fábrica?",
            "Esta acción borrará absolutamente todos tus datos:\n"
            "• Jugadores guardados y en espera\n"
            "• Mapas y Héroes personalizados con sus fotos\n"
            "• Historial de partidas y configuraciones\n\n"
            "¿Deseas continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply1 != QMessageBox.Yes:
            return

        reply2 = QMessageBox.critical(
            self,
            "☢️ Confirmación Definitiva",
            "¿Estás 100% seguro? Esta operación no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply2 != QMessageBox.Yes:
            return

        parent: MainWindow = self.parent()
        if parent:
            parent._factory_reset()
            self._load_settings()
            self._refresh_custom_content_lists()
            self.accept()

    def _confirm_reset_defaults(self):
        reply = QMessageBox.question(
            self,
            "Restablecer Ajustes",
            "¿Deseas restablecer todos los parámetros de configuración a sus valores predeterminados de fábrica?\n\n"
            "(Tus jugadores, héroes y mapas guardados se mantendrán intactos).",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.settings_manager.reset_to_defaults()
            self._load_settings()
            self._mark_dirty()
            parent = self.parent()
            if parent and hasattr(parent, "show_toast"):
                parent.show_toast("Ajustes del sistema restablecidos a valores por defecto", "info")

    def _save_settings(self):
        s = self.settings_manager.settings

        # Persistir tema seleccionado (fijado a obsidian para release estable)
        new_theme_id = "obsidian"
        s.theme_name = "obsidian" 
        accent_changed = s.accent_color.lower() != self._accent_hex.lower()
        s.accent_color = self._accent_hex

        theme.set_theme(new_theme_id, s.accent_color)

        s.shuffle_mode = self.cb_shuffle_mode.currentData()
        s.diversity_candidates = self.spin_candidates.value()
        s.history_size = self.spin_history_size.value()
        s.avoid_recent_maps = self.spin_avoid_maps.value()

        if hasattr(self, "cb_rotation_policy"):
            s.rotation_policy = self.cb_rotation_policy.currentData()
        if hasattr(self, "spin_rotation_batch"):
            s.rotation_batch_size = self.spin_rotation_batch.value()
        if hasattr(self, "spin_min_shield"):
            s.min_matches_shield = self.spin_min_shield.value()
        if hasattr(self, "spin_streamer_rest"):
            s.streamer_rest_interval = self.spin_streamer_rest.value()
        if hasattr(self, "chk_auto_map"):
            s.auto_map = self.chk_auto_map.isChecked()

        s.map_card_size = self.cb_map_size.currentData()
        s.map_card_aspect = self.cb_map_aspect.currentData()

        s.auto_roles = self.chk_auto_roles.isChecked()
        s.composition_5v5 = TeamComposition(
            tank=self.spin_5v5_tank.value(),
            damage=self.spin_5v5_damage.value(),
            support=self.spin_5v5_support.value(),
        )
        s.composition_6v6 = TeamComposition(
            tank=self.spin_6v6_tank.value(),
            damage=self.spin_6v6_damage.value(),
            support=self.spin_6v6_support.value(),
        )

        s.auto_bans = self.chk_auto_bans.isChecked()
        s.max_bans = self.spin_max_bans.value()
        s.max_bans_per_role = self.spin_max_bans_per_role.value()
        s.ban_portrait_size = self.spin_portrait_size.value()
        if hasattr(self, "spin_bans_rows"):
            s.bans_visible_rows = self.spin_bans_rows.value()

        s.team1_name = self.edit_team1.text()
        s.team2_name = self.edit_team2.text()
        s.dnd_cross_team_swap = self.chk_dnd_swap.isChecked()
        s.auto_capitalize_names = self.chk_auto_caps.isChecked()
        if hasattr(self, "chk_vsync"):
            s.vsync = self.chk_vsync.isChecked()

        if hasattr(self, "cb_dynamic_font"):
            s.slot_dynamic_font = self.cb_dynamic_font.currentData()
        if hasattr(self, "cb_role_badge_style"):
            s.role_badge_style = self.cb_role_badge_style.currentData()
        if hasattr(self, "cb_badge_outlines"):
            s.slot_badge_outlines = self.cb_badge_outlines.currentData()
        s.slot_text_align = self.cb_slot_align.currentData()
        s.slot_font_size = self.spin_slot_font_size.value()
        s.slot_font_weight = self.cb_slot_font_weight.currentData()

        if hasattr(self, "cb_tier_export_ratio"):
            s.tier_export_ratio = self.cb_tier_export_ratio.currentData()
        s.tier_hero_size = self.spin_tier_hero_size.value()
        s.tier_map_width = self.spin_tier_map_w.value()
        s.tier_map_height = self.spin_tier_map_h.value()
        s.tier_map_font_size = self.spin_tier_map_font.value()
        s.tier_player_width = self.spin_tier_player_w.value()
        s.tier_player_height = self.spin_tier_player_h.value()
        if hasattr(self, "chk_tier_watermark_export"):
            s.tier_show_watermark_export = self.chk_tier_watermark_export.isChecked()
        if hasattr(self, "chk_tier_watermark_ui"):
            s.tier_show_watermark_ui = self.chk_tier_watermark_ui.isChecked()

        self.settings_manager.save()
        self.shuffle_history.set_max_size(s.history_size)

        parent_window = self.parent()
        if parent_window is not None:
            parent_window.mode_switch.set_mode(s.game_mode)
            parent_window.roles_toggle.setChecked(s.show_roles)
            parent_window._apply_role_policy()
            parent_window._adapt_pinned_roles_to_mode()

            parent_window.match_display.team1_widget.name_input.setText(s.team1_name)
            parent_window.match_display.team2_widget.name_input.setText(s.team2_name)
            parent_window._apply_settings_to_widgets()
            parent_window._after_roster_change()
            if hasattr(parent_window, "tier_maker"):
                parent_window.tier_maker.apply_theme()
                parent_window.tier_maker.reload_bank()
            parent_window._apply_theme()

    def closeEvent(self, event):
        self.save_persistent_geometry()
        # Si se cierra con la X y había cambios no guardados en tema, revertir armónicamente
        if self._has_pending_changes:
            theme.set_theme(self._original_theme_name, self._original_accent)
            parent = self.parent()
            if parent and hasattr(parent, "_apply_theme"):
                parent._apply_theme()
        super().closeEvent(event)

    def accept(self):
        self.save_persistent_geometry()
        self._save_settings()
        super().accept()

    def reject(self):
        self.save_persistent_geometry()
        # Revertir armónicamente al tema guardado original si se cancela
        theme.set_theme(self._original_theme_name, self._original_accent)
        parent = self.parent()
        if parent and hasattr(parent, "_apply_theme"):
            parent._apply_theme()
        super().reject()
