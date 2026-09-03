"""Modern Overwatch hero draft & ban management widget (Modular Orchestrator)."""

from __future__ import annotations
from .smooth_scroll import SmoothScrollArea

from typing import Optional

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.core.models import BanManager, Hero, Role
from owervach_tmixer.ui.styles import theme
from owervach_tmixer.ui.widgets.flow_layout import FlowLayout

from .hero.hero_card import (
    HeroCard,
    ROLE_COLOR,
    ROLE_LABEL,
    get_rounded_pixmap,
    hero_portrait_path,
    normalize_token,
    resolve_canonical_name,
    update_nickname_cache,
)


class HeroWidget(QWidget):
    """Modern hero gallery with responsive grid, multi-tier tag sorting, and non-blocking ban drawer."""

    bans_changed = Signal(set)
    max_bans_changed = Signal(int)
    max_bans_per_role_changed = Signal(int)
    heroes_changed = Signal(list)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._heroes: list[Hero] = []
        self._ban_manager = BanManager(heroes=[], max_bans=5, max_bans_per_role=2)
        self._cards: list[HeroCard] = []
        self._search_text = ""
        self._current_role_filter: Role | None = None

        self.setStyleSheet("background-color: #121316;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # 1. Top Controls Bar Estandarizada a 48px
        top_frame = QWidget(self)
        top_frame.setFixedHeight(48)
        top_frame.setStyleSheet("background-color: #16171D; border: 1px solid #282A33; border-radius: 8px;")
        top_bar = QHBoxLayout(top_frame)
        top_bar.setContentsMargins(10, 4, 10, 4)
        top_bar.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar héroe...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedWidth(170)
        self.search_input.textChanged.connect(self._on_search_changed)
        top_bar.addWidget(self.search_input)

        self.cb_sort = QComboBox()
        self.cb_sort.setView(QListView())
        self.cb_sort.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cb_sort.setMinimumWidth(150)
        self.cb_sort.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.cb_sort.currentIndexChanged.connect(self._on_sort_changed)
        self._update_sort_options()
        top_bar.addWidget(self.cb_sort)

        self.role_group = QButtonGroup(self)
        self.role_group.setExclusive(True)
        self._role_buttons: list[QPushButton] = []

        filters = [
            ("Todos", None),
            ("🛡️ Tanques", Role.TANK),
            ("⚔️ Daño", Role.DAMAGE),
            ("💖 Apoyo", Role.SUPPORT),
        ]

        for label, role in filters:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if role is None:
                btn.setChecked(True)
            btn.toggled.connect(lambda on, r=role: on and self._on_role_filter_changed(r))
            self.role_group.addButton(btn)
            self._role_buttons.append(btn)
            top_bar.addWidget(btn)

        top_bar.addStretch()

        self.lbl_stats = QLabel("Baneos: 0 / 5")
        self.lbl_stats.setStyleSheet("""
            font-size: 12px;
            font-weight: 800;
            color: #FF5555;
            background-color: rgba(255, 85, 85, 0.12);
            border: 1px solid rgba(255, 85, 85, 0.35);
            border-radius: 4px;
            padding: 3px 8px;
        """)
        top_bar.addWidget(self.lbl_stats)

        self.btn_clear = QPushButton("🧹 Limpiar")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                font-weight: 700;
                background-color: #1F222A;
                border: 1px solid #333846;
                border-radius: 6px;
                padding: 6px 12px;
                color: #D0D4DE;
            }
            QPushButton:hover {
                background-color: #2E181C;
                border-color: #FF5555;
                color: #FFFFFF;
            }
        """)
        self.btn_clear.clicked.connect(self._clear_bans)
        top_bar.addWidget(self.btn_clear)

        layout.addWidget(top_frame)

        # 2. Main Responsive Grid Area
        self.scroll = SmoothScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        self.scroll.viewport().setAutoFillBackground(False)
        self.scroll.viewport().setStyleSheet("background-color: transparent; border: none;")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background-color: transparent;")

        self.outer_grid_layout = QVBoxLayout(self.grid_container)
        self.outer_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.outer_grid_layout.setSpacing(0)

        self.grid_layout = QGridLayout()
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setHorizontalSpacing(10)
        self.grid_layout.setVerticalSpacing(10)

        self.outer_grid_layout.addLayout(self.grid_layout)
        self.outer_grid_layout.addStretch(1)

        self.scroll.setWidget(self.grid_container)
        layout.addWidget(self.scroll, 1)

        # 3. Responsive Banned Summary Drawer
        self.summary_box = QFrame()
        self.summary_box.setStyleSheet("""
            QFrame {
                background-color: #17181D;
                border: 1px solid #282A33;
                border-top: 2.5px solid #FF4444;
                border-radius: 8px;
            }
        """)
        sum_layout = QVBoxLayout(self.summary_box)
        sum_layout.setContentsMargins(12, 8, 12, 8)
        sum_layout.setSpacing(6)

        self.summary_title = QLabel("⛔  HÉROES BANEADOS")
        self.summary_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #FF5555; background: transparent; border: none;")
        sum_layout.addWidget(self.summary_title)

        self.summary_scroll = SmoothScrollArea(self.summary_box)
        self.summary_scroll.setWidgetResizable(True)
        self.summary_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.summary_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.summary_scroll.setStyleSheet("background: transparent; border: none;")

        self.summary_container = QWidget(self.summary_scroll)
        self.summary_container.setStyleSheet("background: transparent;")
        self.summary_items = FlowLayout(self.summary_container, margin=2, h_spacing=6, v_spacing=6)

        self.summary_scroll.setWidget(self.summary_container)
        sum_layout.addWidget(self.summary_scroll)

        layout.addWidget(self.summary_box)

        # 4. Botón Central Protagónico Inferior de 46px (Rojo con Outline de 1px)
        bottom_actions = QHBoxLayout()
        bottom_actions.setContentsMargins(0, 2, 0, 0)
        self.btn_randomize = QPushButton("🎲  SORTEAR BANEOS")
        self.btn_randomize.setObjectName("btnRandomizeBans")
        self.btn_randomize.setMinimumHeight(46)
        self.btn_randomize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_randomize.setToolTip("Sortear aleatoriamente los héroes baneados")
        self.btn_randomize.clicked.connect(self._randomize_bans)
        bottom_actions.addWidget(self.btn_randomize, 1)
        layout.addLayout(bottom_actions)

        self.apply_theme()

    def apply_theme(self):
        accent = theme.accent()
        if hasattr(self, "search_input"):
            self.search_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: #181A22;
                    border: 1px solid #2B2E38;
                    border-radius: 6px;
                    padding: 6px 10px;
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: 600;
                }}
                QLineEdit:focus {{ border-color: {accent}; }}
            """)

        for btn in getattr(self, "_role_buttons", []):
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #181A22;
                    border: 1px solid #2B2E38;
                    border-radius: 6px;
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

        if hasattr(self, "btn_randomize"):
            self.btn_randomize.setStyleSheet("""
                QPushButton#btnRandomizeBans {
                    font-size: 14px;
                    font-weight: 900;
                    color: #FF5555;
                    background-color: rgba(30, 20, 24, 0.88);
                    border: 1px solid #FF4444;
                    border-radius: 8px;
                    letter-spacing: 0.5px;
                    padding: 6px 20px;
                }
                QPushButton#btnRandomizeBans:hover {
                    background-color: rgba(255, 68, 68, 0.16);
                    border-color: #FF7777;
                    color: #FFFFFF;
                }
                QPushButton#btnRandomizeBans:pressed {
                    background-color: rgba(255, 68, 68, 0.28);
                }
            """)

        self._update_view()

    def set_heroes(self, heroes: list[Hero]):
        self._heroes = list(heroes)
        update_nickname_cache(self._heroes)
        self._update_sort_options()
        self._heroes = self._sort_heroes(self._heroes)
        self._ban_manager.heroes = self._heroes
        self._ban_manager.banned.intersection_update({h.name for h in self._heroes})
        self._rebuild_cards()

    def set_max_bans(self, value: int):
        val = max(1, int(value)) if value is not None else 5
        self._ban_manager.max_bans = val
        self._trim_bans()

    def set_max_bans_per_role(self, value: int):
        val = max(1, int(value)) if value is not None else 2
        self._ban_manager.max_bans_per_role = val
        self._trim_bans()

    def set_banned(self, banned: set[str]):
        self._ban_manager.banned = set(banned)
        self._trim_bans()

    def get_banned(self) -> set[str]:
        return self._ban_manager.banned.copy()

    def get_heroes(self) -> list[Hero]:
        return self._heroes.copy()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._relayout_grid_columns)
        QTimer.singleShot(0, self._relayout_summary)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout_grid_columns()
        self._relayout_summary()

    def _relayout_summary(self):
        if not hasattr(self, "summary_scroll") or not hasattr(self, "summary_items"):
            return
        vw = self.summary_scroll.viewport().width() if self.summary_scroll.viewport() else 0
        if vw <= 0 and hasattr(self, "summary_box"):
            vw = self.summary_box.width() - 24
        if vw > 0:
            target_h = max(40, self.summary_box.height() - 32)
            self.summary_container.resize(vw, target_h)
            self.summary_items.setGeometry(self.summary_container.rect())
        self.summary_container.updateGeometry()
        self.summary_container.update()
    def _calculate_columns(self) -> int:
        w = self.scroll.viewport().width()
        if w <= 100:
            w = self.width()
        if w <= 100:
            w = 1200
        cols = max(3, min(14, w // 120))
        return cols

    def _update_sort_options(self):
        curr_data = self.cb_sort.currentData() if hasattr(self, "cb_sort") else "role_name_asc"
        self.cb_sort.blockSignals(True)
        self.cb_sort.clear()

        self.cb_sort.addItem("🎭 Rol + A-Z", "role_name_asc")
        self.cb_sort.addItem("🔤 Nombre (A - Z)", "name_asc")
        self.cb_sort.addItem("🔤 Nombre (Z - A)", "name_desc")
        self.cb_sort.addItem("🛡️ Solo por Rol", "role_only")

        all_tag_keys = sorted({k for h in self._heroes for k in getattr(h, "tags", {}).keys()})
        for tag_key in all_tag_keys:
            self.cb_sort.addItem(f"🏷️ {tag_key} (Mayor a Menor)", f"tag_{tag_key}")

        idx = self.cb_sort.findData(curr_data)
        self.cb_sort.setCurrentIndex(idx if idx >= 0 else 0)
        self.cb_sort.blockSignals(False)

    def _sort_heroes(self, heroes: list[Hero]) -> list[Hero]:
        role_order = {Role.TANK: 0, Role.DAMAGE: 1, Role.SUPPORT: 2}
        sort_mode = self.cb_sort.currentData() if hasattr(self, "cb_sort") else "role_name_asc"

        if str(sort_mode).startswith("tag_"):
            tag_key = str(sort_mode).replace("tag_", "", 1)

            main_win = self.window()
            custom_orders = {}
            if hasattr(main_win, "settings_manager"):
                custom_orders = getattr(main_win.settings_manager.settings, "category_value_orders", {})
            custom_order = custom_orders.get(tag_key, [])

            tier_dict = {
                "dios": 1000, "god": 1000, "dios del sexo": 1000, "prime": 1000,
                "op": 900, "broken": 900, "chetado": 900, "s+": 850, "s": 800,
                "a+": 750, "a": 700, "alto": 650, "mucho": 600, "muy": 600,
                "b+": 550, "b": 500, "medio": 450, "normal": 400, "si": 400, "sí": 400,
                "c": 350, "d": 300, "poco": 250, "un poco": 250, "bajo": 200,
                "no": 100, "f": 50, "manco": 10, "rivals": 0, "vete al rivals": 0
            }

            def tag_sort_key(h: Hero):
                val = str(getattr(h, "tags", {}).get(tag_key, "")).strip()
                if not val or val == "✓":
                    return (1, 0, h.name.casefold())

                if custom_order and val in custom_order:
                    return (0, custom_order.index(val), h.name.casefold())

                try:
                    return (0, -float(val), h.name.casefold())
                except ValueError:
                    pass

                val_lower = val.lower()
                for k, score in tier_dict.items():
                    if k in val_lower.split() or val_lower == k or val_lower.startswith(k):
                        return (0, -score, h.name.casefold())

                return (0, val.casefold(), h.name.casefold())

            return sorted(heroes, key=tag_sort_key)

        if sort_mode == "name_asc":
            return sorted(heroes, key=lambda h: h.name.casefold())
        elif sort_mode == "name_desc":
            return sorted(heroes, key=lambda h: h.name.casefold(), reverse=True)
        elif sort_mode == "role_only":
            return sorted(heroes, key=lambda h: role_order.get(h.role, 99))
        else:
            return sorted(heroes, key=lambda h: (role_order.get(h.role, 99), h.name.casefold()))

    def _on_sort_changed(self):
        self._heroes = self._sort_heroes(self._heroes)
        self._rebuild_cards()

    def _rebuild_cards(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        for hero in self._heroes:
            card = HeroCard(hero, self, parent=getattr(self, 'grid_container', self))
            card.toggled.connect(lambda checked, name=hero.name: self._toggle(name, checked))
            self._cards.append(card)

        self._filter_cards()
        self._update_view()

    def _relayout_grid_columns(self):
        cols = self._calculate_columns()

        while self.grid_layout.count():
            self.grid_layout.takeAt(0)

        for c in range(16):
            self.grid_layout.setColumnStretch(c, 0)

        visible_cards = [c for c in self._cards if c.isVisible()]

        for i, card in enumerate(visible_cards):
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(card, row, col)

        for c in range(cols):
            self.grid_layout.setColumnStretch(c, 1)

    def _on_search_changed(self, text: str):
        self._search_text = text.strip().casefold()
        self._filter_cards()

    def _on_role_filter_changed(self, role: Role | None):
        self._current_role_filter = role
        self._filter_cards()

    def _filter_cards(self):
        for card in self._cards:
            h = card.hero
            matches_search = not self._search_text or self._search_text in h.name.casefold()
            matches_role = (self._current_role_filter is None) or (h.role == self._current_role_filter)
            card.setVisible(matches_search and matches_role)
        self._relayout_grid_columns()

    def _toggle(self, name: str, checked: bool):
        if checked:
            if not self._ban_manager.can_ban(name):
                err = self._ban_manager.ban_error(name) or "Límite de baneos alcanzado."
                main_win = self.window()
                if hasattr(main_win, "show_toast"):
                    main_win.show_toast(f"⚠️ {err}", "warning")
                self._update_view()
                return

            self._ban_manager.banned.add(name)
            main_win = self.window()
            if hasattr(main_win, "_egg_manager"):
                canon_name = resolve_canonical_name(name)
                main_win._egg_manager.on_fav_hero_banned(canon_name, main_win, is_random=False)
        else:
            self._ban_manager.banned.discard(name)

        self._update_view(emit=True)

    def _trim_bans(self):
        requested = self._ban_manager.banned.copy()
        self._ban_manager.banned.clear()
        for hero in self._heroes:
            if hero.name in requested and self._ban_manager.can_ban(hero.name):
                self._ban_manager.banned.add(hero.name)
        self._update_view(emit=True)

    def _update_view(self, emit: bool = False):
        banned_set = self._ban_manager.banned

        for card in self._cards:
            card.set_banned(card.hero.name in banned_set)

        self.lbl_stats.setText(f"Baneos: {len(banned_set)} / {self._ban_manager.max_bans}")

        counts = " · ".join(
            f"{ROLE_LABEL[role]} {self._ban_manager.banned_in_role(role)}/{self._ban_manager.max_bans_per_role}"
            for role in Role
        )
        self.summary_title.setText(f"⛔  HÉROES BANEADOS ({len(banned_set)})  ·  {counts}")

        while self.summary_items.count():
            item = self.summary_items.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not banned_set:
            empty_lbl = QLabel(
                "No hay héroes baneados actualmente. Pulsa '🎲 Sortear Baneos' abajo o haz clic en un héroe.",
                getattr(self, "summary_container", self),
            )
            empty_lbl.setStyleSheet("color: #727684; font-size: 11px; font-weight: 600; padding: 4px 0; background: transparent;")
            self.summary_items.addWidget(empty_lbl)
            self.summary_box.setFixedHeight(72)
        else:
            for name in sorted(banned_set):
                hero = self._ban_manager.hero_by_name(name)
                if not hero:
                    continue
                chip = self._create_banned_chip(hero)
                self.summary_items.addWidget(chip)

            count = len(banned_set)
            if count <= 7:
                self.summary_box.setFixedHeight(85)
            elif count <= 14:
                self.summary_box.setFixedHeight(120)
            else:
                self.summary_box.setFixedHeight(150)

        self._relayout_summary()

        if emit:
            banned_list = self.get_banned()
            self.bans_changed.emit(banned_list)
            main_win = self.window()
            if hasattr(main_win, "_egg_manager"):
                main_win._egg_manager.check_trinity_ban(banned_list, main_win)

    def _create_banned_chip(self, hero: Hero) -> QWidget:
        chip = QFrame(getattr(self, "summary_container", self))
        chip.setObjectName("bannedHeroChip")
        chip.setStyleSheet("""
            QFrame#bannedHeroChip {
                background-color: #201417;
                border: 1px solid #5A2228;
                border-radius: 6px;
            }
        """)
        hlayout = QHBoxLayout(chip)
        hlayout.setContentsMargins(6, 3, 6, 3)
        hlayout.setSpacing(6)

        thumb = QLabel()
        thumb.setFixedSize(20, 20)
        img_path = hero_portrait_path(hero.name)
        if img_path:
            pix = QPixmap(str(img_path))
            if not pix.isNull():
                thumb.setPixmap(get_rounded_pixmap(pix, size=20, radius=4.0))
        thumb.setStyleSheet("background: transparent; border: none;")
        hlayout.addWidget(thumb)

        lbl_name = QLabel(hero.name)
        lbl_name.setStyleSheet("font-size: 11px; font-weight: 800; color: #FFFFFF; background: transparent; border: none;")
        hlayout.addWidget(lbl_name)

        btn_unban = QPushButton("✕")
        btn_unban.setToolTip(f"Desbanear a {hero.name}")
        btn_unban.setFixedSize(16, 16)
        btn_unban.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_unban.setStyleSheet("""
            QPushButton {
                font-size: 10px; font-weight: 800; color: #FF7777; background: transparent; border: none;
            }
            QPushButton:hover { color: #FFFFFF; }
        """)
        btn_unban.clicked.connect(lambda _, n=hero.name: self._toggle(n, False))
        hlayout.addWidget(btn_unban)

        return chip

    def _prompt_rename_hero(self, hero: Hero):
        current_display = hero.name
        new_name, ok = QInputDialog.getText(
            self, "Cambiar nombre de héroe",
            f"Introduce un apodo / nuevo nombre para '{hero.original_name or hero.name}':\n(Conservará su foto original y rol)",
            text=current_display,
        )
        if ok and new_name.strip():
            cleaned = new_name.strip()
            if cleaned.casefold() == (hero.original_name or hero.name).casefold():
                self._restore_hero_name(hero)
                return
            if hero.original_name is None:
                hero.original_name = hero.name
            hero.name = cleaned
            self._persist_hero_updates()
            main_win = self.window()
            if hasattr(main_win, "show_toast"):
                main_win.show_toast(f"✏️ Héroe renombrado a '{cleaned}'", "success")

    def _restore_hero_name(self, hero: Hero):
        if hero.original_name:
            orig = hero.original_name
            hero.name = orig
            hero.original_name = None
            self._persist_hero_updates()
            main_win = self.window()
            if hasattr(main_win, "show_toast"):
                main_win.show_toast(f"🔄 Restaurado nombre original '{orig}'", "info")

    def _prompt_add_tag_to_hero(self, hero: Hero):
        all_keys = sorted({k for h in self._heroes for k in getattr(h, "tags", {}).keys()})
        from owervach_tmixer.ui.dialogs.hero_tags_dialog import AddTagPromptDialog
        diag = AddTagPromptDialog(hero.name, existing_categories=all_keys, parent=self)
        if diag.exec() == QDialog.DialogCode.Accepted:
            k, v = diag.get_data()
            if k:
                hero.tags[k] = v
                self._persist_hero_updates()
                main_win = self.window()
                if hasattr(main_win, "show_toast"):
                    main_win.show_toast(f"🏷️ Etiqueta '{k}: {v}' asignada a {hero.name}", "success")

    def _remove_tag_from_hero(self, hero: Hero, key: str):
        if key in hero.tags:
            del hero.tags[key]
            self._persist_hero_updates()
            main_win = self.window()
            if hasattr(main_win, "show_toast"):
                main_win.show_toast(f"🗑️ Etiqueta '{key}' quitada de {hero.name}", "info")

    def _persist_hero_updates(self):
        update_nickname_cache(self._heroes)
        self.heroes_changed.emit(self._heroes)
        main_win = self.window()
        if hasattr(main_win, "_on_heroes_changed"):
            main_win._on_heroes_changed(self._heroes)
        self._rebuild_cards()

    def _randomize_bans(self):
        main_win = self.window()
        from owervach_tmixer.ui.easter_eggs import is_sathara_in_match
        import random

        # 5% de probabilidad secreta si Sathara está activo
        if is_sathara_in_match(main_win) and random.random() < 0.05:
            mains = ["Wrecking Ball", "Pharah", "Brigitte"]
            all_other = [h.name for h in self._heroes if h.name not in mains]
            random.shuffle(all_other)
            needed = max(0, self._ban_manager.max_bans - len(mains))
            self._ban_manager.banned = set(mains + all_other[:needed])
        else:
            self._ban_manager.randomize_bans()

        self._update_view(emit=True)
        if hasattr(main_win, "_egg_manager"):
            for h_name in self._ban_manager.banned:
                canon = resolve_canonical_name(h_name)
                main_win._egg_manager.on_fav_hero_banned(canon, main_win, is_random=True)

    def _clear_bans(self):
        self._ban_manager.clear_bans()
        self._update_view(emit=True)

    def _import_heroes(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importar héroes", "", "JSON (*.json)")
        if not path:
            return
        try:
            from owervach_tmixer.core.storage import Storage

            heroes = Storage().import_heroes(path)
            self.set_heroes(heroes)
            self.heroes_changed.emit(heroes)
        except Exception as exc:
            main_win = self.window()
            if hasattr(main_win, "show_toast"):
                main_win.show_toast(f"Error al importar: {exc}", "danger")

    def _export_heroes(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar héroes", "heroes.json", "JSON (*.json)")
        if not path:
            return
        try:
            from owervach_tmixer.core.storage import Storage

            Storage().export_heroes(self._heroes, path)
            main_win = self.window()
            if hasattr(main_win, "show_toast"):
                main_win.show_toast(f"Héroes exportados a '{Path(path).name}'", "success")
        except Exception as exc:
            main_win = self.window()
            if hasattr(main_win, "show_toast"):
                main_win.show_toast(f"Error al exportar: {exc}", "danger")
