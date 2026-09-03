"""Comprehensive hero tag management suite (Modular Orchestrator)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.core.models import Hero, Role
from owervach_tmixer.ui.styles import theme

# Submódulos desacoplados y re-exportaciones de compatibilidad universal
from .tags.tag_prompt_dialog import AddTagPromptDialog, QInputDialog_getItem
from .tags.hero_tag_row import HeroTagRow, TagVectorBtn, ROLE_BADGE_COLOR

if TYPE_CHECKING:
    from owervach_tmixer.ui.main_window import MainWindow


class HeroTagsDialog(QDialog):
    """Main suite for hero tag assignment, bulk actions, and global category ranking."""

    def __init__(self, parent: MainWindow):
        super().__init__(parent)
        self.main_window: MainWindow = parent
        self._heroes = self.main_window.hero_widget.get_heroes()
        self._rows: list[HeroTagRow] = []

        self.setWindowTitle("Gestor y Clasificación de Etiquetas de Héroes")
        self.resize(780, 750)
        self.setMinimumWidth(680)
        self.setStyleSheet("background-color: #121316;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        top_bar = QHBoxLayout()
        title = QLabel("🏷️  CLASIFICACIÓN Y GESTOR DE ETIQUETAS")
        title.setStyleSheet(f"font-size: 14px; font-weight: 900; color: {theme.accent()};")
        top_bar.addWidget(title)
        top_bar.addStretch()

        btn_close = QPushButton("✕ Cerrar")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #1F222A; border: 1px solid #363B48; border-radius: 6px;
                padding: 6px 14px; color: #FFFFFF; font-weight: 700; font-size: 12px;
            }
            QPushButton:hover { background-color: #2D323E; border-color: #61ab02; }
        """)
        btn_close.clicked.connect(self.accept)
        top_bar.addWidget(btn_close)
        layout.addLayout(top_bar)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #282A33; border-radius: 8px; background-color: #16171B; }
            QTabBar::tab {
                background: #1C1E24; color: #9A9FA8; font-weight: 700; padding: 8px 16px; border: 1px solid #282A33; border-radius: 6px; margin-right: 4px;
            }
            QTabBar::tab:selected { background: rgba(97, 171, 2, 0.15); color: #61ab02; border-color: #61ab02; }
        """)

        tab_heroes = QWidget()
        th_layout = QVBoxLayout(tab_heroes)
        th_layout.setContentsMargins(12, 12, 12, 12)
        th_layout.setSpacing(10)
        self._setup_heroes_tab(th_layout)
        self.tabs.addTab(tab_heroes, "👥 Héroes y Asignación Masiva")

        tab_categories = QWidget()
        tc_layout = QVBoxLayout(tab_categories)
        tc_layout.setContentsMargins(14, 14, 14, 14)
        tc_layout.setSpacing(12)
        self._setup_categories_tab(tc_layout)
        self.tabs.addTab(tab_categories, "⚙️ Categorías Globales")

        layout.addWidget(self.tabs, 1)

    def _setup_heroes_tab(self, layout: QVBoxLayout):
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar héroe en la lista...")
        self.search_input.setStyleSheet("background-color: #17181D; border: 1px solid #282A33; border-radius: 6px; padding: 6px 12px; color: #FFF; font-size: 12px; font-weight: 600;")
        self.search_input.textChanged.connect(self._filter_rows)
        search_row.addWidget(self.search_input, 1)

        btn_select_all = QPushButton("☑️ Todos")
        btn_select_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_select_all.setStyleSheet("padding: 6px 10px; font-size: 11px; font-weight: 700; background-color: #1F222A; border: 1px solid #333845; border-radius: 5px; color: #FFF;")
        btn_select_all.clicked.connect(lambda: self._set_all_selected(True))
        search_row.addWidget(btn_select_all)

        btn_select_none = QPushButton("⬜ Ninguno")
        btn_select_none.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_select_none.setStyleSheet("padding: 6px 10px; font-size: 11px; font-weight: 700; background-color: #1F222A; border: 1px solid #333845; border-radius: 5px; color: #FFF;")
        btn_select_none.clicked.connect(lambda: self._set_all_selected(False))
        search_row.addWidget(btn_select_none)

        layout.addLayout(search_row)

        self.bulk_bar = QFrame()
        self.bulk_bar.setStyleSheet("background-color: #1E222B; border: 1px solid #353B4A; border-radius: 6px; padding: 2px;")
        b_layout = QHBoxLayout(self.bulk_bar)
        b_layout.setContentsMargins(8, 4, 8, 4)
        b_layout.setSpacing(8)

        self.lbl_selected = QLabel("0 seleccionados")
        self.lbl_selected.setStyleSheet("font-size: 12px; font-weight: 800; color: #61ab02;")
        b_layout.addWidget(self.lbl_selected)
        b_layout.addStretch()

        self.btn_bulk_add = QPushButton("⚡ Asignar Etiqueta a Selección")
        self.btn_bulk_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_bulk_add.setStyleSheet("background-color: #29303D; border: 1px solid #61ab02; color: #FFFFFF; font-weight: 800; font-size: 11px; padding: 5px 12px; border-radius: 5px;")
        self.btn_bulk_add.clicked.connect(self._bulk_assign_tag)
        b_layout.addWidget(self.btn_bulk_add)

        self.btn_bulk_remove = QPushButton("🗑️ Quitar Etiqueta de Selección")
        self.btn_bulk_remove.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_bulk_remove.setStyleSheet("background-color: #301E22; border: 1px solid #FF5555; color: #FFAAAA; font-weight: 700; font-size: 11px; padding: 5px 12px; border-radius: 5px;")
        self.btn_bulk_remove.clicked.connect(self._bulk_remove_tag)
        b_layout.addWidget(self.btn_bulk_remove)

        self.bulk_bar.hide()
        layout.addWidget(self.bulk_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        self.list_layout = QVBoxLayout(container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)

        self._rows.clear()
        for hero in self._heroes:
            row = HeroTagRow(hero, self)
            self._rows.append(row)
            self.list_layout.addWidget(row)

        self.list_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

    def _setup_categories_tab(self, layout: QVBoxLayout):
        desc = QLabel("Administra las categorías de etiquetas globales. Usa las flechas ◀ ▶ para definir el orden jerárquico de mayor a menor.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #9A9FA8; font-size: 12px; line-height: 1.4;")
        layout.addWidget(desc)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        self.cat_container = QWidget()
        self.cat_container.setStyleSheet("background-color: transparent;")
        self.cat_layout = QVBoxLayout(self.cat_container)
        self.cat_layout.setContentsMargins(0, 0, 0, 0)
        self.cat_layout.setSpacing(10)

        scroll.setWidget(self.cat_container)
        layout.addWidget(scroll, 1)

        btn_reset_all = QPushButton("⚠️ Borrar Todas las Etiquetas de Todos los Héroes")
        btn_reset_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset_all.setStyleSheet("background-color: #38181D; border: 1px solid #FF4444; color: #FFAAAA; font-weight: 800; font-size: 12px; padding: 10px; border-radius: 6px;")
        btn_reset_all.clicked.connect(self._reset_all_tags)
        layout.addWidget(btn_reset_all)

        self._refresh_categories_tab()

    def _refresh_categories_tab(self):
        while self.cat_layout.count():
            item = self.cat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        all_keys = self.get_all_category_keys()
        if not all_keys:
            empty = QLabel("No has creado ninguna categoría de etiquetas aún.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #626673; font-size: 12px; font-weight: 600; padding: 20px 0;")
            self.cat_layout.addWidget(empty)
            return

        settings = self.main_window.settings_manager.settings
        custom_orders = getattr(settings, "category_value_orders", {})

        for key in all_keys:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #17181D;
                    border: 1px solid #282A33;
                    border-radius: 8px;
                }
            """)
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(14, 12, 14, 12)
            c_layout.setSpacing(10)

            top_row = QHBoxLayout()
            lbl = QLabel(f"🏷️  <b>{key}</b>")
            lbl.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {theme.accent()}; background: transparent; border: none;")
            top_row.addWidget(lbl)

            count = sum(1 for h in self._heroes if key in h.tags)
            lbl_count = QLabel(f"({count} héroes)")
            lbl_count.setStyleSheet("font-size: 12px; font-weight: 600; color: #888E9E; background: transparent; border: none;")
            top_row.addWidget(lbl_count)
            top_row.addStretch()

            btn_del = QPushButton("🗑️ Eliminar")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setStyleSheet("""
                QPushButton {
                    background-color: #2D1A1E; border: 1px solid #5A2228; color: #FF9999;
                    font-weight: 700; font-size: 11px; padding: 5px 10px; border-radius: 5px;
                }
                QPushButton:hover { background-color: #4A1E24; border-color: #FF4444; color: #FFFFFF; }
            """)
            btn_del.clicked.connect(lambda _, k=key: self._delete_global_category(k))
            top_row.addWidget(btn_del)
            c_layout.addLayout(top_row)

            distinct_values = []
            for h in self._heroes:
                v = h.tags.get(key)
                if v and v != "✓" and v not in distinct_values:
                    distinct_values.append(v)

            if distinct_values:
                saved_order = custom_orders.get(key, [])
                ordered_vals = [v for v in saved_order if v in distinct_values] + [v for v in distinct_values if v not in saved_order]

                custom_orders[key] = ordered_vals
                self.main_window.settings_manager.settings.category_value_orders = custom_orders
                self.main_window.settings_manager.save()

                lbl_hier = QLabel("Jerarquía de ordenamiento (Mayor a Menor prioridad):")
                lbl_hier.setStyleSheet("font-size: 12px; font-weight: 800; color: #B0B5C2; background: transparent; border: none;")
                c_layout.addWidget(lbl_hier)

                chips_row = QHBoxLayout()
                chips_row.setSpacing(8)

                if len(ordered_vals) == 1:
                    badge = QFrame()
                    badge.setStyleSheet("background-color: #1F222A; border: 1px solid #363B48; border-radius: 6px;")
                    b_layout = QHBoxLayout(badge)
                    b_layout.setContentsMargins(12, 6, 12, 6)
                    lbl_val = QLabel(f"🥇 <b>{ordered_vals[0]}</b>")
                    lbl_val.setStyleSheet("font-size: 13px; font-weight: 800; color: #FFFFFF; background: transparent; border: none;")
                    b_layout.addWidget(lbl_val)
                    chips_row.addWidget(badge)

                    hint_lbl = QLabel("<i>(Asigna otros valores para poder intercambiar sus posiciones con ◀ ▶)</i>")
                    hint_lbl.setStyleSheet("font-size: 11px; color: #6C7280; background: transparent; border: none;")
                    chips_row.addWidget(hint_lbl)
                else:
                    medals = ["🥇", "🥈", "🥉"]
                    for idx, val in enumerate(ordered_vals):
                        badge = QFrame()
                        badge.setStyleSheet("""
                            QFrame {
                                background-color: #1E2129;
                                border: 1px solid #363C4D;
                                border-radius: 6px;
                            }
                        """)
                        b_layout = QHBoxLayout(badge)
                        b_layout.setContentsMargins(8, 4, 8, 4)
                        b_layout.setSpacing(6)

                        prefix = medals[idx] if idx < 3 else f"#{idx+1}"
                        lbl_val = QLabel(f"{prefix} <b>{val}</b>")
                        lbl_val.setStyleSheet("font-size: 13px; font-weight: 800; color: #FFFFFF; background: transparent; border: none;")
                        b_layout.addWidget(lbl_val)

                        if idx > 0:
                            btn_left = TagVectorBtn("left", tooltip="Mover a mayor rango (más a la izquierda)", size=(30, 28), parent=badge)
                            btn_left.clicked.connect(lambda _, k=key, i=idx: self._move_value_rank(k, i, -1))
                            b_layout.addWidget(btn_left)

                        if idx < len(ordered_vals) - 1:
                            btn_right = TagVectorBtn("right", tooltip="Mover a menor rango (más a la derecha)", size=(30, 28), parent=badge)
                            btn_right.clicked.connect(lambda _, k=key, i=idx: self._move_value_rank(k, i, 1))
                            b_layout.addWidget(btn_right)

                        chips_row.addWidget(badge)

                chips_row.addStretch()
                c_layout.addLayout(chips_row)

            self.cat_layout.addWidget(card)

        self.cat_layout.addStretch()

    def get_all_category_keys(self) -> list[str]:
        keys = set()
        for h in self._heroes:
            keys.update(h.tags.keys())
        return sorted(keys)

    def _on_selection_changed(self):
        selected_count = sum(1 for r in self._rows if r.is_selected() and r.isVisible())
        if selected_count > 0:
            self.lbl_selected.setText(f"{selected_count} héroe(s) seleccionados")
            self.bulk_bar.show()
        else:
            self.bulk_bar.hide()

    def _set_all_selected(self, selected: bool):
        for r in self._rows:
            if r.isVisible():
                r.set_selected(selected)
        self._on_selection_changed()

    def _bulk_assign_tag(self):
        selected_rows = [r for r in self._rows if r.is_selected() and r.isVisible()]
        if not selected_rows:
            return

        diag = AddTagPromptDialog(f"{len(selected_rows)} héroes", existing_categories=self.get_all_category_keys(), parent=self)
        if diag.exec() == QDialog.DialogCode.Accepted:
            k, v = diag.get_data()
            if k:
                for r in selected_rows:
                    r.hero.tags[k] = v
                    r.rebuild_chips()
                self._persist_changes()
                self._set_all_selected(False)
                self.main_window.show_toast(f"⚡ Etiqueta '{k}' asignada a {len(selected_rows)} héroes", "success")

    def _bulk_remove_tag(self):
        selected_rows = [r for r in self._rows if r.is_selected() and r.isVisible()]
        if not selected_rows:
            return

        all_keys = sorted({k for r in selected_rows for k in r.hero.tags.keys()})
        if not all_keys:
            QMessageBox.information(self, "Sin etiquetas", "Los héroes seleccionados no tienen etiquetas.")
            return

        item, ok = QInputDialog_getItem(self, "Quitar Etiqueta", "Selecciona la etiqueta a quitar de la selección:", all_keys)
        if ok and item:
            for r in selected_rows:
                if item in r.hero.tags:
                    del r.hero.tags[item]
                    r.rebuild_chips()
            self._persist_changes()
            self._set_all_selected(False)
            self.main_window.show_toast(f"🗑️ Etiqueta '{item}' quitada de {len(selected_rows)} héroes", "info")

    def _move_value_rank(self, key: str, idx: int, delta: int):
        settings = self.main_window.settings_manager.settings
        orders = getattr(settings, "category_value_orders", {})
        vals = orders.get(key, [])
        new_idx = idx + delta
        if 0 <= new_idx < len(vals):
            vals[idx], vals[new_idx] = vals[new_idx], vals[idx]
            orders[key] = vals
            settings.category_value_orders = orders
            self.main_window.settings_manager.save()
            self._persist_changes()
            self._refresh_categories_tab()

    def _delete_global_category(self, key: str):
        reply = QMessageBox.question(
            self, "Eliminar categoría",
            f"¿Eliminar la categoría '{key}' de TODOS los héroes?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            for h in self._heroes:
                if key in h.tags:
                    del h.tags[key]
            for r in self._rows:
                r.rebuild_chips()
            self._persist_changes()
            self._refresh_categories_tab()
            self.main_window.show_toast(f"🗑️ Categoría '{key}' eliminada de todos los héroes", "info")

    def _reset_all_tags(self):
        reply = QMessageBox.question(
            self, "Resetear todas las etiquetas",
            "¿Estás seguro de que deseas borrar TODAS las etiquetas personalizadas de TODOS los héroes?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            for h in self._heroes:
                h.tags.clear()
            for r in self._rows:
                r.rebuild_chips()
            self._persist_changes()
            self._refresh_categories_tab()
            self.main_window.show_toast("🧹 Todas las etiquetas han sido eliminadas", "info")

    def _filter_rows(self, text: str):
        q = text.strip().casefold()
        for row in self._rows:
            visible = not q or q in row.hero.name.casefold() or any(q in k.casefold() or q in v.casefold() for k, v in row.hero.tags.items())
            row.setVisible(visible)
        self._on_selection_changed()

    def _persist_changes(self):
        self.main_window.hero_widget.set_heroes(self._heroes)
        self.main_window._on_heroes_changed(self._heroes)
        self._refresh_categories_tab()
