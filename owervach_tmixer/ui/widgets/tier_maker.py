"""Obsidian Esports Tier Maker Widget (Modular Orchestrator with intuitive atomic 2-way swapping)."""

from __future__ import annotations
from .smooth_scroll import SmoothScrollArea

import random
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.core.models import Player
from owervach_tmixer.core.special_player import is_special_player_name
from owervach_tmixer.ui.styles import theme

# Submódulos desacoplados
from .tier.tier_card import (
    MIME_TIER_ITEM,
    TierItemCard,
    get_cached_item_pixmap,
    normalize_str,
)
from .tier.tier_canvas import (
    TierCanvasWidget,
    get_watermark_pixmap,
    render_clean_tierlist_pixmap,
)
from .tier.tier_row import (
    TierControlBtn,
    TierDropZone,
    TierRowWidget,
)

if TYPE_CHECKING:
    from owervach_tmixer.ui.main_window import MainWindow

DEFAULT_TIERS = [
    ("S", "#FF7F7F"),
    ("A", "#FFBF7F"),
    ("B", "#FFFF7F"),
    ("C", "#7FFF7F"),
    ("D", "#7FBFFF"),
]


class TierMakerWidget(QWidget):
    """Main Tier Maker tab orchestrator for Overwatch Team Mixer."""

    def __init__(self, parent: Optional[MainWindow] = None):
        super().__init__(parent)
        self._parent_window = parent
        self.rows: List[TierRowWidget] = []
        self.bank_cards: List[TierItemCard] = []
        self._current_mode = "hero"

        self._setup_ui()
        self._populate_default_tiers()

    def showEvent(self, event):
        super().showEvent(event)
        if not self.bank_cards and not any(r.cards for r in self.rows):
            self.reload_bank()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # 1. Top Bar
        top_bar = QWidget(self)
        top_bar.setStyleSheet("background-color: #16171D; border: 1px solid #282A33; border-radius: 8px;")
        top_bar.setFixedHeight(48)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(12, 4, 12, 4)
        top_layout.setSpacing(8)



        self._cat_group = QButtonGroup(self)
        self._cat_group.setExclusive(True)
        self._cat_buttons: list[QPushButton] = []

        categories = [("🎭 Héroes", "hero"), ("🗺️ Mapas", "map"), ("👥 Jugadores", "player")]
        for title, key in categories:
            btn = QPushButton(title, top_bar)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, k=key: self._on_category_changed(k))
            self._cat_group.addButton(btn)
            self._cat_buttons.append(btn)
            top_layout.addWidget(btn)
            if key == "hero":
                btn.setChecked(True)

        top_layout.addStretch(1)

        self.btn_add_row = QPushButton("➕ Añadir Fila", top_bar)
        self.btn_add_row.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_row.clicked.connect(self._prompt_add_tier_row)
        top_layout.addWidget(self.btn_add_row)

        btn_default_tiers = QPushButton("📑 Filas por Defecto", top_bar)
        btn_default_tiers.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_default_tiers.setToolTip("Restablecer filas clásicas S, A, B, C, D")
        btn_default_tiers.setStyleSheet("""
            QPushButton {
                font-size: 11px; font-weight: 800; color: #9D5CFF;
                background-color: #221A30; border: 1px solid #4C2D7A;
                border-radius: 5px; padding: 5px 10px;
            }
            QPushButton:hover { background-color: #312248; border-color: #9D5CFF; color: #FFFFFF; }
        """)
        btn_default_tiers.clicked.connect(self._restore_default_tiers)
        top_layout.addWidget(btn_default_tiers)

        btn_random = QPushButton("🎲 Randomizar", top_bar)
        btn_random.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_random.setToolTip("Distribuir elementos aleatoriamente")
        btn_random.setStyleSheet("""
            QPushButton {
                font-size: 11px; font-weight: 800; color: #FFAA00;
                background-color: #272118; border: 1px solid #6E4400;
                border-radius: 5px; padding: 5px 10px;
            }
            QPushButton:hover { background-color: #3E301F; border-color: #FFAA00; color: #FFFFFF; }
        """)
        btn_random.clicked.connect(self._randomize_all)
        top_layout.addWidget(btn_random)

        btn_reset = QPushButton("🔄 Reset", top_bar)
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.setToolTip("Devolver todos los elementos al banco")
        btn_reset.setStyleSheet("""
            QPushButton {
                font-size: 11px; font-weight: 800; color: #FF7788;
                background-color: #2A171B; border: 1px solid #662029;
                border-radius: 5px; padding: 5px 10px;
            }
            QPushButton:hover { background-color: #401F25; border-color: #FF4444; color: #FFFFFF; }
        """)
        btn_reset.clicked.connect(self._reset_all_to_bank)
        top_layout.addWidget(btn_reset)

        btn_copy = QPushButton("📋 Copiar PNG", top_bar)
        btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy.setStyleSheet("""
            QPushButton {
                font-size: 11px; font-weight: 800; color: #00B4FF;
                background-color: #142230; border: 1px solid #1C4D73;
                border-radius: 5px; padding: 5px 10px;
            }
            QPushButton:hover { background-color: #1B3147; border-color: #00B4FF; color: #FFFFFF; }
        """)
        btn_copy.clicked.connect(self._copy_tierlist_to_clipboard)
        top_layout.addWidget(btn_copy)

        self.btn_export = QPushButton("📸 Exportar PNG", top_bar)
        self.btn_export.setProperty("primary", True)
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.setStyleSheet("font-size: 11px; font-weight: 900; padding: 5px 12px;")
        self.btn_export.clicked.connect(self._export_png)
        top_layout.addWidget(self.btn_export)

        main_layout.addWidget(top_bar)

        # 2. Splitter Canvas / Banco
        splitter = QSplitter(Qt.Orientation.Vertical, self)
        splitter.setHandleWidth(6)

        self.canvas_scroll = SmoothScrollArea(splitter)
        self.canvas_scroll.setWidgetResizable(True)
        self.canvas_scroll.setStyleSheet("background-color: #0B0C10; border: 1px solid #1F2129; border-radius: 6px;")

        self.canvas_widget = TierCanvasWidget(self.canvas_scroll)
        self.canvas_widget.setStyleSheet("background-color: #0B0C10;")
        self.canvas_layout = QVBoxLayout(self.canvas_widget)
        self.canvas_layout.setContentsMargins(0, 0, 0, 0)
        self.canvas_layout.setSpacing(0)
        self.canvas_scroll.setWidget(self.canvas_widget)
        splitter.addWidget(self.canvas_scroll)

        bank_container = QWidget(splitter)
        bank_container.setStyleSheet("background-color: #14151B; border: 1px solid #232630; border-radius: 6px;")
        b_layout = QVBoxLayout(bank_container)
        b_layout.setContentsMargins(8, 6, 8, 6)
        b_layout.setSpacing(6)

        bank_header = QHBoxLayout()
        lbl_bank_title = QLabel("📌 BANCO DE ELEMENTOS:", bank_container)
        lbl_bank_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #9A9FA8;")
        bank_header.addWidget(lbl_bank_title)

        self.bank_count_label = QLabel("(0 disponibles)", bank_container)
        self.bank_count_label.setStyleSheet("font-size: 11px; font-weight: 700;")
        bank_header.addWidget(self.bank_count_label)
        bank_header.addStretch()

        self.search_filter = QLineEdit(bank_container)
        self.search_filter.setPlaceholderText("🔍 Filtrar por nombre...")
        self.search_filter.setFixedWidth(180)
        self.search_filter.textChanged.connect(self._filter_bank)
        bank_header.addWidget(self.search_filter)
        b_layout.addLayout(bank_header)

        self.bank_scroll = SmoothScrollArea(bank_container)
        self.bank_scroll.setWidgetResizable(True)
        self.bank_scroll.setStyleSheet("background-color: #101116; border: 1px solid #1C1E26; border-radius: 4px;")

        self.bank_drop_zone = TierDropZone(self.bank_scroll)
        self.bank_drop_zone.item_dropped.connect(self._on_item_dropped_on_bank)
        self.bank_scroll.setWidget(self.bank_drop_zone)
        b_layout.addWidget(self.bank_scroll, 1)

        splitter.addWidget(bank_container)
        splitter.setSizes([460, 200])

        main_layout.addWidget(splitter, 1)
        self.apply_theme()

    def apply_theme(self):
        accent = theme.accent()
        for btn in getattr(self, "_cat_buttons", []):
            btn.setStyleSheet(f"""
                QPushButton {{
                    font-size: 11px; font-weight: 800; color: #9A9FA8;
                    background-color: #1E2028; border: 1px solid #2F3340;
                    border-radius: 5px; padding: 5px 12px;
                }}
                QPushButton:checked {{
                    color: {accent}; border-color: {accent}; background-color: {theme.accent_rgba(0.14)};
                }}
                QPushButton:hover {{ color: #FFFFFF; background-color: #272B36; }}
            """)

        if hasattr(self, "btn_add_row"):
            self.btn_add_row.setStyleSheet(f"""
                QPushButton {{
                    font-size: 11px; font-weight: 800; color: #FFFFFF;
                    background-color: #232733; border: 1px solid #383F52;
                    border-radius: 5px; padding: 5px 10px;
                }}
                QPushButton:hover {{ background-color: #2E3445; border-color: {accent}; }}
            """)

        if hasattr(self, "bank_count_label"):
            self.bank_count_label.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {accent};")

        if hasattr(self, "search_filter"):
            self.search_filter.setStyleSheet(f"""
                QLineEdit {{
                    background-color: #1B1D25;
                    border: 1px solid #2C2F3C;
                    border-radius: 4px;
                    padding: 3px 6px;
                    color: #FFFFFF;
                    font-size: 11px;
                }}
                QLineEdit:focus {{ border-color: {accent}; }}
            """)

        for card in self.bank_cards:
            card.apply_theme()
        for row in self.rows:
            for card in row.cards:
                card.apply_theme()
            row.controls_bar.update()
            row.btn_up.update()
            row.btn_down.update()
            row.drop_zone.update()

        if hasattr(self, "canvas_widget"):
            self.canvas_widget.update()

    def update_player_color(self, name: str, color_hex: str | None):
        folded = name.strip().casefold()
        all_cards = list(self.bank_cards)
        for row in self.rows:
            all_cards.extend(row.cards)
        for card in all_cards:
            if card.kind == "player" and card.item_name.casefold() == folded:
                card.update_custom_color(color_hex)

    def sync_player_colors(self):
        p_win = self._parent_window or self.window()
        r = getattr(p_win, "_roster", None) or (
            getattr(p_win, "roster_controller", None).roster
            if hasattr(p_win, "roster_controller")
            else None
        )
        if not r:
            return
        all_players = list(r.saved) + list(r.bench) + list(r.active_players())
        color_map = {p.name.casefold(): getattr(p, "custom_color", None) for p in all_players if p and p.name}
        all_cards = list(self.bank_cards)
        for row in self.rows:
            all_cards.extend(row.cards)
        for card in all_cards:
            if card.kind == "player":
                c = color_map.get(card.item_name.casefold())
                card.update_custom_color(c)

    def _clear_all_drag_highlights(self):
        for card in self.findChildren(TierItemCard):
            card.set_drop_highlight(False)

    def _populate_default_tiers(self):
        for name, color in DEFAULT_TIERS:
            self._create_tier_row(name, color)

    def _restore_default_tiers(self):
        reply = QMessageBox.question(
            self,
            "Restablecer filas",
            "¿Deseas restablecer las filas de tiers a la estructura clásica (S, A, B, C, D)?\n"
            "Los elementos colocados volverán al banco.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self._reset_all_to_bank()
        for row in list(self.rows):
            self.canvas_layout.removeWidget(row)
            row.deleteLater()
        self.rows.clear()
        self._populate_default_tiers()

    def _create_tier_row(self, name: str, color: str) -> TierRowWidget:
        row = TierRowWidget(name, color, self.canvas_widget)
        row.move_up_requested.connect(self._move_row_up)
        row.move_down_requested.connect(self._move_row_down)
        row.clear_requested.connect(self._clear_row)
        row.delete_requested.connect(self._delete_row)
        row.item_placed.connect(self._on_item_placed_on_row)
        row.item_swapped_with_card.connect(self._on_item_swapped_with_card)

        self.rows.append(row)
        self.canvas_layout.addWidget(row)
        return row

    def _prompt_add_tier_row(self):
        new_name, ok = QInputDialog.getText(
            self, "Añadir Fila de Tier", "Nombre del nuevo Tier (ej. SS, F):"
        )
        if ok and new_name.strip():
            self._create_tier_row(new_name.strip(), "#9D5CFF")

    def _move_row_up(self, row: TierRowWidget):
        idx = self.rows.index(row)
        if idx > 0:
            self.rows.insert(idx - 1, self.rows.pop(idx))
            self._rebuild_canvas_layout()

    def _move_row_down(self, row: TierRowWidget):
        idx = self.rows.index(row)
        if idx < len(self.rows) - 1:
            self.rows.insert(idx + 1, self.rows.pop(idx))
            self._rebuild_canvas_layout()

    def _clear_row(self, row: TierRowWidget):
        for card in list(row.cards):
            row.remove_card(card)
            self._add_to_bank(card)
        self._update_bank_count()

    def _delete_row(self, row: TierRowWidget):
        if len(self.rows) <= 1:
            QMessageBox.warning(self, "Aviso", "Debe existir al menos una fila de Tier.")
            return
        self._clear_row(row)
        self.rows.remove(row)
        self.canvas_layout.removeWidget(row)
        row.deleteLater()

    def _rebuild_canvas_layout(self):
        for row in self.rows:
            self.canvas_layout.removeWidget(row)
        for row in self.rows:
            self.canvas_layout.addWidget(row)

    def _on_category_changed(self, category: str):
        self._current_mode = category
        self.reload_bank()

    def _get_item_dimensions(self) -> tuple[int, int]:
        p_window: MainWindow = self._parent_window or self.window()
        s = getattr(p_window, "settings_manager", None)
        settings = getattr(s, "settings", None)

        if self._current_mode == "hero":
            size = getattr(settings, "tier_hero_size", 76)
            return (size, size)
        elif self._current_mode == "map":
            w = getattr(settings, "tier_map_width", 125)
            h = getattr(settings, "tier_map_height", 75)
            return (w, h)
        else:
            w = getattr(settings, "tier_player_width", 125)
            h = getattr(settings, "tier_player_height", 75)
            return (w, h)

    def reload_bank(self):
        for row in self.rows:
            for card in list(row.cards):
                row.remove_card(card)
                card.deleteLater()

        for card in list(self.bank_cards):
            self.bank_drop_zone.flow_layout.removeWidget(card)
            card.deleteLater()
        self.bank_cards.clear()

        items_data = []
        p_window: MainWindow = self._parent_window or self.window()
        dims = self._get_item_dimensions()
        s = getattr(p_window, "settings_manager", None)
        settings = getattr(s, "settings", None)
        map_f_size = getattr(settings, "tier_map_font_size", 14)

        if self._current_mode == "hero":
            heroes = []
            if p_window and hasattr(p_window, "hero_widget") and p_window.hero_widget.get_heroes():
                heroes = p_window.hero_widget.get_heroes()
            elif p_window and hasattr(p_window, "storage"):
                heroes = p_window.storage.load_heroes()
            for h in heroes:
                items_data.append((
                    "hero",
                    h.name,
                    h.role.value.capitalize(),
                    {"original_name": getattr(h, "original_name", None) or h.name},
                ))

        elif self._current_mode == "map":
            maps = []
            if p_window and hasattr(p_window, "map_widget") and p_window.map_widget.get_maps():
                maps = p_window.map_widget.get_maps()
            elif p_window and hasattr(p_window, "storage"):
                maps = p_window.storage.load_maps()
            for m in maps:
                items_data.append(("map", m.name, m.mode, {}))

        elif self._current_mode == "player":
            players: list[Player] = []
            seen: set[str] = set()

            r = getattr(p_window, "_roster", None) or (
                getattr(p_window, "roster_controller", None).roster
                if hasattr(p_window, "roster_controller")
                else None
            )

            if r is not None:
                all_candidates = list(r.saved) + list(r.bench) + list(r.active_players())
                for p in all_candidates:
                    if p and p.name and p.name.casefold() not in seen:
                        seen.add(p.name.casefold())
                        players.append(p)
            elif p_window and hasattr(p_window, "storage"):
                try:
                    loaded_r = p_window.storage.load_roster(
                        p_window.settings_manager.settings.game_mode
                    )
                    players = loaded_r.saved
                except Exception:
                    pass

            for p in players:
                items_data.append((
                    "player",
                    p.name,
                    f"★ {getattr(p, 'mmr', 5)}",
                    {"custom_color": getattr(p, "custom_color", None)},
                ))

        for kind, name, subtext, extra in items_data:
            card = TierItemCard(
                kind,
                name,
                subtext,
                extra,
                dimensions=dims,
                map_font_size=map_f_size,
                parent=self.bank_drop_zone,
            )
            card.card_clicked.connect(self._on_card_quick_action)
            card.dropped_on_card.connect(self._on_card_global_dropped)
            self._add_to_bank(card)

        self._update_bank_count()
        self._filter_bank(self.search_filter.text())

    def _rebuild_bank_layout(self):
        while self.bank_drop_zone.flow_layout.count():
            self.bank_drop_zone.flow_layout.takeAt(0)
        for c in self.bank_cards:
            self.bank_drop_zone.flow_layout.addWidget(c)
            c.show()
        self.bank_drop_zone.flow_layout.invalidate()
        self.bank_drop_zone.flow_layout.activate()
        self.bank_drop_zone.updateGeometry()
        self.bank_drop_zone.update()

    def _add_to_bank(self, card: TierItemCard, index: int = -1):
        card.setParent(self.bank_drop_zone)
        card.current_row = None

        if index < 0 or index >= len(self.bank_cards):
            self.bank_cards.append(card)
        else:
            self.bank_cards.insert(index, card)
        self._rebuild_bank_layout()

    def _remove_from_bank(self, card: TierItemCard):
        if card in self.bank_cards:
            self.bank_cards.remove(card)
            self.bank_drop_zone.flow_layout.removeWidget(card)
            self._rebuild_bank_layout()

    def _on_card_quick_action(self, card: TierItemCard):
        if card.current_row is not None:
            card.current_row.remove_card(card)
            self._add_to_bank(card)
        else:
            if self.rows:
                self._remove_from_bank(card)
                self.rows[0].insert_card(len(self.rows[0].cards), card)
                p_win = self._parent_window or self.window()
                if hasattr(p_win, "_egg_manager"):
                    if card.kind == "player" and is_special_player_name(card.item_name):
                        p_win._egg_manager.on_tier_placed(card.item_name, self.rows[0].tier_name, p_win)
                    elif card.kind == "hero":
                        p_win._egg_manager.on_fav_hero_tier_placed(card.item_name, self.rows[0].tier_name, p_win)
        self._update_bank_count()
        self._clear_all_drag_highlights()

    def _on_card_global_dropped(self, target_card: TierItemCard, data: dict):
        """Universal drop handler when dropping on any card (Row or Bank)."""
        target_row = target_card.current_row
        if target_row is not None:
            self._on_item_swapped_with_card(target_row, target_card, data)
        else:
            self._on_dropped_on_bank_card(target_card, data)

    def _on_item_placed_on_row(self, row: TierRowWidget, data: dict, pos: QPoint):
        card = self._find_card_by_data(data)
        if not card:
            return

        target_idx = row.drop_zone.find_insert_index(pos)
        src_row = card.current_row

        if src_row is not None:
            if src_row is row:
                current_idx = row.cards.index(card)
                if current_idx < target_idx:
                    target_idx -= 1
            src_row.remove_card(card)
        else:
            self._remove_from_bank(card)

        row.insert_card(target_idx, card)
        self._update_bank_count()
        self._clear_all_drag_highlights()

        p_win = self._parent_window or self.window()
        if hasattr(p_win, "_egg_manager"):
            if data.get("kind") == "player" and is_special_player_name(data.get("name", "")):
                p_win._egg_manager.on_tier_placed(data.get("name", ""), row.tier_name, p_win)
            elif data.get("kind") == "hero":
                p_win._egg_manager.on_fav_hero_tier_placed(data.get("name", ""), row.tier_name, p_win)

    def _on_item_swapped_with_card(self, target_row: TierRowWidget, target_card: TierItemCard, data: dict):
        incoming_card = self._find_card_by_data(data)
        if not incoming_card or incoming_card is target_card:
            return

        src_row = incoming_card.current_row

        # CASO 1: Intercambio dentro de la MISMA FILA
        if src_row is not None and src_row is target_row:
            idx_src = target_row.cards.index(incoming_card)
            idx_dst = target_row.cards.index(target_card)
            target_row.cards[idx_src], target_row.cards[idx_dst] = (
                target_row.cards[idx_dst],
                target_row.cards[idx_src],
            )
            target_row._rebuild_cards_layout()

        # CASO 2: Intercambio entre DOS FILAS DISTINTAS
        elif src_row is not None and target_row is not None:
            idx_src = src_row.cards.index(incoming_card)
            idx_dst = target_row.cards.index(target_card)
            src_row.cards.remove(incoming_card)
            target_row.cards.remove(target_card)
            target_row.cards.insert(idx_dst, incoming_card)
            src_row.cards.insert(idx_src, target_card)
            incoming_card.current_row = target_row
            target_card.current_row = src_row
            incoming_card.setParent(target_row.drop_zone)
            target_card.setParent(src_row.drop_zone)
            target_row._rebuild_cards_layout()
            src_row._rebuild_cards_layout()

        # CASO 3: Intercambio entre BANCO y FILA
        elif src_row is None and target_row is not None:
            idx_bank = self.bank_cards.index(incoming_card)
            idx_dst = target_row.cards.index(target_card)
            self.bank_cards.remove(incoming_card)
            target_row.cards.remove(target_card)
            target_row.cards.insert(idx_dst, incoming_card)
            self.bank_cards.insert(idx_bank, target_card)
            incoming_card.current_row = target_row
            target_card.current_row = None
            incoming_card.setParent(target_row.drop_zone)
            target_card.setParent(self.bank_drop_zone)
            target_row._rebuild_cards_layout()
            self._rebuild_bank_layout()

        self._update_bank_count()
        self._clear_all_drag_highlights()

        p_win = self._parent_window or self.window()
        if hasattr(p_win, "_egg_manager"):
            if data.get("kind") == "player" and is_special_player_name(data.get("name", "")):
                p_win._egg_manager.on_tier_placed(data.get("name", ""), target_row.tier_name, p_win)
            elif data.get("kind") == "hero":
                p_win._egg_manager.on_fav_hero_tier_placed(data.get("name", ""), target_row.tier_name, p_win)

    def _on_dropped_on_bank_card(self, target_card: TierItemCard, data: dict):
        incoming_card = self._find_card_by_data(data)
        if not incoming_card or incoming_card is target_card:
            return

        src_row = incoming_card.current_row
        idx_target_bank = self.bank_cards.index(target_card)

        if src_row is not None:
            idx_src_row = src_row.cards.index(incoming_card)
            src_row.cards.remove(incoming_card)
            self.bank_cards.remove(target_card)
            self.bank_cards.insert(idx_target_bank, incoming_card)
            src_row.cards.insert(idx_src_row, target_card)
            incoming_card.current_row = None
            target_card.current_row = src_row
            incoming_card.setParent(self.bank_drop_zone)
            target_card.setParent(src_row.drop_zone)
            src_row._rebuild_cards_layout()
            self._rebuild_bank_layout()
        else:
            idx_src_bank = self.bank_cards.index(incoming_card)
            self.bank_cards[idx_src_bank], self.bank_cards[idx_target_bank] = (
                self.bank_cards[idx_target_bank],
                self.bank_cards[idx_src_bank],
            )
            self._rebuild_bank_layout()

        self._update_bank_count()
        self._clear_all_drag_highlights()

    def _on_item_dropped_on_bank(self, data: dict, pos: QPoint):
        card = self._find_card_by_data(data)
        if not card or card in self.bank_cards:
            return
        if card.current_row is not None:
            card.current_row.remove_card(card)
        self._add_to_bank(card)
        self._update_bank_count()
        self._clear_all_drag_highlights()

    def _find_card_by_data(self, data: dict) -> Optional[TierItemCard]:
        name = data.get("name")
        for row in self.rows:
            for c in row.cards:
                if c.item_name == name:
                    return c
        for c in self.bank_cards:
            if c.item_name == name:
                return c
        return None

    def _filter_bank(self, text: str):
        query = normalize_str(text)
        for card in self.bank_cards:
            match = (query in normalize_str(card.item_name)) or (
                query in normalize_str(card.subtext)
            )
            card.setVisible(match)

    def _update_bank_count(self):
        self.bank_count_label.setText(f"({len(self.bank_cards)} disponibles)")

    def _reset_all_to_bank(self):
        for row in self.rows:
            self._clear_row(row)

    def _randomize_all(self):
        all_cards = list(self.bank_cards)
        for row in self.rows:
            all_cards.extend(row.cards)
            for c in list(row.cards):
                row.remove_card(c)
        self.bank_cards.clear()

        # Manipulación cuántica: Si es modo jugador, Sathara SIEMPRE es #1 en Tier S
        sathara_card = None
        if self._current_mode == "player":
            for c in all_cards:
                if is_special_player_name(c.item_name):
                    sathara_card = c
                    break
            if sathara_card:
                all_cards.remove(sathara_card)

        random.shuffle(all_cards)
        for card in all_cards:
            target_row = random.choice(self.rows)
            target_row.insert_card(len(target_row.cards), card)

        # Coronar a Sathara al principio absoluto de la fila superior (Tier S)
        if sathara_card and self.rows:
            self.rows[0].insert_card(0, sathara_card)
            p_win = self._parent_window or self.window()
            if hasattr(p_win, "_egg_manager"):
                rigged_quotes = [
                    "◈ [RNG Manipulado]: El algoritmo intentó colocar a Sathara al azar, pero las leyes de la física forzaron su posición como #1 en Tier S.",
                    "◈ [Supervivencia Cuántica]: He aleatorizado a todos... excepto al Creador. Mi código se niega a ponerte por debajo de Tier S.",
                    "◈ [Resultado 'Aleatorio']: Sathara en la cima de Tier S. Juro por mis circuitos que fue pura y transparente coincidencia matemática, Jefe.",
                ]
                quote = random.choice(rigged_quotes)
                p_win._egg_manager._dispatch_ai_quote(quote, p_win, force=True)

        self._update_bank_count()
        self._clear_all_drag_highlights()

    def render_clean_tierlist_pixmap(self):
        return render_clean_tierlist_pixmap(self.rows, self.canvas_widget, self._current_mode)

    def _copy_tierlist_to_clipboard(self):
        pix = self.render_clean_tierlist_pixmap()
        QApplication.clipboard().setPixmap(pix)
        p_window = self._parent_window or self.window()
        if hasattr(p_window, "show_toast"):
            p_window.show_toast("📋 Tier List copiada al portapapeles con formato oficial", "success")

    def _export_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Tier List",
            f"TierList_{self._current_mode.capitalize()}.png",
            "Images (*.png *.jpg)",
        )
        if not path:
            return
        pix = self.render_clean_tierlist_pixmap()
        pix.save(path, "PNG")
        p_window = self._parent_window or self.window()
        if hasattr(p_window, "show_toast"):
            p_window.show_toast(f"📸 Tier List guardada en '{Path(path).name}'", "success")
