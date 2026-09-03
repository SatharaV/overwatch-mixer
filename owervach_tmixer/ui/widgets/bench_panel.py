"""Bench panel ('Zona de Espera') with distinct separator line, outline toolbar buttons, and clean drag lifecycle."""

from __future__ import annotations
from .smooth_scroll import SmoothScrollArea

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QAction, QColor, QDrag, QCursor, QPainter, QBrush, QPen, QFont
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QPushButton,
    QRubberBand,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.core.models import Player, Role
from owervach_tmixer.core.special_player import (
    SPECIAL_GLOW,
    format_player_name,
    is_special_player_name,
)
from owervach_tmixer.ui.dialogs.player_properties_dialog import PlayerPropertiesDialog
from owervach_tmixer.ui.styles import theme
from .dnd import clear_all_drop_highlights, make_payload, payload_from, payload_to_mime, set_drop_highlight
from .marquee_label import MarqueeLabel

_NUM_COLUMNS = 2
_CHIP_HEIGHT = 36


class _BenchChip(QFrame):
    def set_selected(self, selected: bool):
        self._is_selected = selected
        self._apply_chip_style()

    def dragEnterEvent(self, event):
        payload = payload_from(event.mimeData())
        if payload and payload.get("kind") == "bench" and payload.get("name") != self.name:
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        payload = payload_from(event.mimeData())
        if payload and payload.get("kind") == "bench":
            src_name = payload.get("name")
            if src_name and src_name != self.name:
                self._panel.reorder_bench.emit(src_name, self.name)
                event.accept()
                return
        super().dropEvent(event)

    """A single compact bench-entry chip in the grid with custom colors."""

    def __init__(self, panel: BenchPanel, player: Player, saved: bool):
        super().__init__(panel)
        self._panel = panel
        self.player = player
        self.name = player.name
        self.saved = saved
        self.special = is_special_player_name(player.name)
        self._pressing = False
        self._press_pos = QPoint()
        self.setObjectName("benchChip")
        self.setFixedHeight(_CHIP_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(8)
        self.setToolTip("Arrastra para añadir a un equipo · Doble clic: añadir automáticamente · Clic derecho: opciones")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda pos, chip=self: self._panel._show_chip_menu(chip, pos))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 3, 4, 3)
        layout.setSpacing(4)

        self.indicator = QLabel(self._indicators())
        self.indicator.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.indicator.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.indicator, 0)

        self.name_label = MarqueeLabel(self.name, self, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.name_label.setMinimumWidth(8)
        self.name_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.name_label, 1)

        self.remove_btn = QPushButton("✕")
        self.remove_btn.setFixedSize(18, 18)
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_btn.setToolTip("Quitar de Zona de Espera")
        self.remove_btn.setFlat(True)
        self.remove_btn.clicked.connect(lambda: self._panel.remove_from_bench.emit(self.name))
        layout.addWidget(self.remove_btn)

        self._apply_chip_style()

    def _indicators(self) -> str:
        parts = []
        if getattr(self._panel, "_show_mmr", False):
            mmr = getattr(self.player, "mmr", 5)
            parts.append(f"⚡{mmr}")
        if self._panel._fixed_names is not None and self.name in self._panel._fixed_names:
            parts.append("🔒")
        if self.saved:
            parts.append("⭐")
        return " ".join(parts) or ""

    def _apply_chip_style(self):
        custom_color = getattr(self.player, "custom_color", None)
        accent = theme.accent()
        if getattr(self, "_is_selected", False):
            self.setStyleSheet("""
                QFrame#benchChip {
                    background-color: rgba(0, 180, 255, 0.22);
                    border: 1.5px solid #00B4FF;
                    border-radius: 6px;
                }
                QLabel { color: #FFFFFF; font-size: 11px; font-weight: 800; background: transparent; }
                QPushButton { background: transparent; border: none; color: #FFFFFF; }
            """)
            return

        if self.special:
            self.setStyleSheet("""
                QFrame#benchChip {
                    background-color: #1D261A;
                    border: 1px solid #48781B;
                    border-radius: 6px;
                }
                QFrame#benchChip:hover { background-color: #263321; border-color: #61ab02; }
                QLabel { color: #A4E062; font-size: 11px; font-weight: 700; background: transparent; }
                QPushButton { background: transparent; border: none; color: #A4E062; }
                QPushButton:hover { color: #FF6B6B; }
            """)
            glow = self._panel._make_glow(self)
            self.setGraphicsEffect(glow)
        elif custom_color:
            self.setStyleSheet(f"""
                QFrame#benchChip {{
                    background-color: #181A1E;
                    border: 1px solid {custom_color};
                    border-radius: 6px;
                }}
                QFrame#benchChip:hover {{
                    background-color: #22252C;
                }}
                QLabel {{ color: {custom_color}; font-size: 11px; font-weight: 700; background: transparent; }}
                QPushButton {{ background: transparent; border: none; color: {custom_color}; font-size: 11px; }}
                QPushButton:hover {{ color: #FF5555; }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#benchChip {{
                    background-color: #181A1E;
                    border: 1px solid #2B2E36;
                    border-radius: 6px;
                }}
                QFrame#benchChip:hover {{
                    background-color: #22252C;
                    border-color: {accent};
                }}
                QLabel {{ color: #D8D8D8; font-size: 11px; font-weight: 600; background: transparent; }}
                QPushButton {{ background: transparent; border: none; color: #777777; font-size: 11px; }}
                QPushButton:hover {{ color: #FF5555; }}
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressing = True
            self._press_pos = event.position().toPoint()
            mods = QApplication.keyboardModifiers()
            if mods & Qt.KeyboardModifier.ControlModifier:
                self._panel._toggle_select_chip(self.name)
            elif mods & Qt.KeyboardModifier.ShiftModifier:
                self._panel._range_select_chip(self.name)
            else:
                if self.name not in self._panel.selected_names:
                    self._panel._select_single_chip(self.name)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._pressing:
            self._pressing = False
            mods = QApplication.keyboardModifiers()
            if not (mods & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)):
                if len(self._panel.selected_names) > 1 and self.name in self._panel.selected_names:
                    self._panel._select_single_chip(self.name)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if (self._pressing and event.buttons() & Qt.MouseButton.LeftButton
                and (event.position().toPoint() - self._press_pos).manhattanLength()
                >= QApplication.startDragDistance()):
            self._pressing = False

            is_sp = is_special_player_name(self.name)
            if is_sp:
                from owervach_tmixer.ui.easter_eggs import notify_special_drag_start, notify_special_drag_end
                notify_special_drag_start(self.window())

            drag = QDrag(self)
            active_selected = [c.name for c in self._panel.chips if c.name in self._panel.selected_names]

            if self.name in self._panel.selected_names and len(active_selected) > 1:
                names = list(active_selected)
                if self.name in names:
                    names.remove(self.name)
                    names.insert(0, self.name)
                payload = make_payload("bench_multi", self.name, names=names)
                is_multi = True
            else:
                payload = make_payload("bench", self.name)
                is_multi = False

            drag.setMimeData(payload_to_mime(payload))
            pix = self.grab()
            if pix.width() > 220:
                pix = pix.scaledToWidth(220, Qt.TransformationMode.SmoothTransformation)

            if is_multi:
                painter = QPainter(pix)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                badge_w = 34
                badge_h = 18
                badge_rect = QRect(pix.width() - badge_w - 4, 4, badge_w, badge_h)
                painter.setBrush(QBrush(QColor("#00B4FF")))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(badge_rect, 4, 4)
                painter.setPen(QPen(QColor("#FFFFFF")))
                f = painter.font()
                f.setBold(True)
                f.setPointSize(9)
                painter.setFont(f)
                painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, f"+{len(active_selected)}")
                painter.end()

            drag.setPixmap(pix)
            drag.exec(Qt.DropAction.MoveAction)
            clear_all_drop_highlights()

            if is_sp:
                notify_special_drag_end()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressing = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        self._pressing = False
        self._panel.add_to_team.emit(self.name, 0)
        event.accept()


class BenchPanel(QFrame):
    """Grid of bench players with clear separator, outline toolbar, and custom colors."""

    add_to_team = Signal(str, object)
    remove_from_bench = Signal(str)
    remove_permanent = Signal(str)
    save_player = Signal(str)
    unsave_player = Signal(str)
    bench_drop_entry = Signal(object)
    fill_teams_requested = Signal()
    bench_all_requested = Signal()
    player_role_mmr_changed = Signal(str, object, int)
    player_renamed = Signal(str, str)
    player_color_changed = Signal(str, object)
    reorder_bench = Signal(str, str)
    bulk_save_requested = Signal(list)
    bulk_remove_requested = Signal(list)
    bulk_add_to_team_requested = Signal(list, int)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._show_mmr = False
        self.chips: list[_BenchChip] = []
        self._fixed_names: set[str] | None = None
        self.selected_names: set[str] = set()
        self._last_selected: str | None = None
        self._rubber_band = None
        self._rubber_origin = QPoint()
        self.setObjectName("benchPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 1. Outline Toolbar Row
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        self.btn_fill = QPushButton("📥 Rellenar")
        self.btn_fill.setToolTip("Rellenar huecos de los equipos con jugadores en espera")
        self.btn_fill.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fill.clicked.connect(self.fill_teams_requested.emit)
        header.addWidget(self.btn_fill, 1)

        self.btn_bench_all = QPushButton("📤 A Espera")
        self.btn_bench_all.setToolTip("Enviar todos los jugadores de los equipos a Zona de Espera")
        self.btn_bench_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_bench_all.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                font-weight: 700;
                color: #FFAAAA;
                background-color: #1C1417;
                border: 1px solid #6E222B;
                border-radius: 5px;
                padding: 6px 10px;
            }
            QPushButton:hover {
                background-color: #381A20;
                border-color: #FF4444;
                color: #FFFFFF;
            }
            QPushButton:pressed { background-color: #140E10; }
        """)
        self.btn_bench_all.clicked.connect(self.bench_all_requested.emit)
        header.addWidget(self.btn_bench_all, 1)

        layout.addLayout(header)

        # 2. Separador Obsidian Nítido
        self.sep = QFrame(self)
        self.sep.setFrameShape(QFrame.Shape.HLine)
        self.sep.setFixedHeight(1)
        self.sep.setStyleSheet("background-color: #2D3242; border: none; margin: 2px 0 2px 0;")
        layout.addWidget(self.sep)

        # 3. Grid of Chips
        self.bench_grid = QWidget()
        self.bench_grid.setObjectName("benchGrid")
        self._grid_container = QVBoxLayout(self.bench_grid)
        self._grid_container.setContentsMargins(0, 0, 0, 0)
        self._grid_container.setSpacing(6)
        self._grid = QGridLayout()
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(6)
        self._grid.setVerticalSpacing(6)
        for col in range(_NUM_COLUMNS):
            self._grid.setColumnStretch(col, 1)
        self._grid_container.addLayout(self._grid)
        self._grid_container.addStretch(1)

        self.bench_scroll = SmoothScrollArea()
        self.bench_scroll.setObjectName("benchScroll")
        self.bench_scroll.setWidgetResizable(True)
        self.bench_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bench_scroll.setWidget(self.bench_grid)
        self.bench_scroll.setAcceptDrops(True)
        self.bench_grid.setAcceptDrops(True)
        self.bench_scroll.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.bench_scroll.customContextMenuRequested.connect(lambda pos: self._show_empty_area_menu(self.bench_scroll.mapToGlobal(pos)))
        self.bench_grid.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.bench_grid.customContextMenuRequested.connect(lambda pos: self._show_empty_area_menu(self.bench_grid.mapToGlobal(pos)))
        layout.addWidget(self.bench_scroll, 1)

        self.setAcceptDrops(True)
        self.apply_theme()

    def apply_theme(self):
        accent = theme.accent()
        self.setStyleSheet(f"""
            QFrame#benchPanel {{
                background-color: #16171D;
                border: 1px solid #282A33;
                border-radius: 8px;
            }}
            QFrame#benchPanel[dropTarget="true"] {{
                border: 1.5px solid {accent};
                background-color: #1F261B;
            }}
            QScrollArea#benchScroll, QWidget#benchGrid {{
                background-color: transparent;
                border: none;
            }}
        """)
        if hasattr(self, "btn_fill"):
            self.btn_fill.setStyleSheet(f"""
                QPushButton {{
                    font-size: 11px;
                    font-weight: 700;
                    color: #FFFFFF;
                    background-color: #171A24;
                    border: 1px solid {accent};
                    border-radius: 5px;
                    padding: 6px 10px;
                }}
                QPushButton:hover {{
                    background-color: {theme.accent_rgba(0.14)};
                    border-color: {theme.accent_light()};
                    color: #FFFFFF;
                }}
                QPushButton:pressed {{ background-color: #12141C; }}
            """)
        for chip in self.chips:
            chip._apply_chip_style()

    def _make_glow(self, chip: _BenchChip):
        glow = QGraphicsDropShadowEffect(chip)
        glow.setColor(QColor(SPECIAL_GLOW))
        glow.setBlurRadius(14)
        glow.setOffset(0, 0)
        return glow

    def _dnd_enter(self, event):
        payload = payload_from(event.mimeData())
        if payload is None or payload.get("kind") not in ("slot", "saved"):
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        set_drop_highlight(self, True)
        event.accept()

    def _dnd_move(self, event):
        payload = payload_from(event.mimeData())
        if payload is None or payload.get("kind") not in ("slot", "saved"):
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()

    def _dnd_leave(self, event):
        set_drop_highlight(self, False)

    def _dnd_drop(self, event):
        payload = payload_from(event.mimeData())
        set_drop_highlight(self, False)
        if payload is None or payload.get("kind") not in ("slot", "saved"):
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()
        self.bench_drop_entry.emit(payload)

    def dragEnterEvent(self, event):
        self._dnd_enter(event)

    def dragMoveEvent(self, event):
        self._dnd_move(event)

    def dragLeaveEvent(self, event):
        self._dnd_leave(event)

    def dropEvent(self, event):
        self._dnd_drop(event)

    def set_bench(self, bench: list[Player], saved_names: set[str],
                  fixed_team: set[str] | None = None, show_mmr: bool = False):
        self._show_mmr = show_mmr
        self._fixed_names = set(fixed_team or ())
        saved_lower = {n.casefold() for n in saved_names}

        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

        # Purgar selecciones de jugadores que ya no están en la banca
        bench_names_set = {p.name for p in bench}
        self.selected_names.intersection_update(bench_names_set)
        if self._last_selected not in bench_names_set:
            self._last_selected = None

        self.chips = []
        for i, p in enumerate(bench):
            chip = _BenchChip(self, p, saved=p.name.casefold() in saved_lower)
            self._grid.addWidget(chip, i // _NUM_COLUMNS, i % _NUM_COLUMNS)
            self.chips.append(chip)

    def find_chip(self, name: str) -> _BenchChip | None:
        for chip in self.chips:
            if chip.name == name:
                return chip
        return None


    def _select_single_chip(self, name: str):
        self.selected_names = {name}
        self._last_selected = name
        self._refresh_selection_visuals()

    def _toggle_select_chip(self, name: str):
        if name in self.selected_names:
            self.selected_names.discard(name)
        else:
            self.selected_names.add(name)
            self._last_selected = name
        self._refresh_selection_visuals()

    def _range_select_chip(self, name: str):
        if not self._last_selected or not self.chips:
            self._select_single_chip(name)
            return
        names = [c.name for c in self.chips]
        try:
            i1 = names.index(self._last_selected)
            i2 = names.index(name)
            start, end = min(i1, i2), max(i1, i2)
            for n in names[start:end + 1]:
                self.selected_names.add(n)
        except ValueError:
            self.selected_names.add(name)
        self._last_selected = name
        self._refresh_selection_visuals()

    def _refresh_selection_visuals(self):
        for c in self.chips:
            c.set_selected(c.name in self.selected_names)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            mods = QApplication.keyboardModifiers()
            if not (mods & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)):
                self.selected_names.clear()
                self._refresh_selection_visuals()
            self._rubber_origin = event.pos()
            if self._rubber_band is None:
                self._rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
            self._rubber_band.setGeometry(QRect(self._rubber_origin, QSize()))
            self._rubber_band.show()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._rubber_band and self._rubber_band.isVisible():
            rect = QRect(self._rubber_origin, event.pos()).normalized()
            self._rubber_band.setGeometry(rect)
            for c in self.chips:
                chip_rect = QRect(c.mapTo(self, QPoint(0, 0)), c.size())
                if rect.intersects(chip_rect):
                    self.selected_names.add(c.name)
                else:
                    self.selected_names.discard(c.name)
            self._refresh_selection_visuals()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._rubber_band and self._rubber_band.isVisible():
            self._rubber_band.hide()
        super().mouseReleaseEvent(event)

    def _show_chip_menu(self, chip: _BenchChip, pos):
        if len(self.selected_names) > 1 and chip.name in self.selected_names:
            self._show_bulk_chip_menu(pos)
            return

        name = chip.name
        is_sp = is_special_player_name(name)
        menu = QMenu(self)
        name = chip.name
        is_sp = is_special_player_name(name)
        menu = QMenu(self)

        if not is_sp:
            act_rename = QAction("✏️ Renombrar jugador...", self)
            act_rename.triggered.connect(lambda: self._prompt_rename_chip(chip))
            menu.addAction(act_rename)

        act_props = QAction("⚙️ Ajustar Habilidad / MMR...", self)
        act_props.triggered.connect(lambda: self._open_properties_modal(chip))
        menu.addAction(act_props)

        if not is_sp:
            act_color = QAction("🎨 Asignar Color Personalizado...", self)
            act_color.triggered.connect(lambda: self._prompt_pick_color(chip))
            menu.addAction(act_color)

            if getattr(chip.player, "custom_color", None):
                act_reset_color = QAction("↺ Restablecer Color", self)
                act_reset_color.triggered.connect(lambda: self._reset_custom_color(chip))
                menu.addAction(act_reset_color)

        menu.addSeparator()

        add_menu = menu.addMenu("Añadir a la partida")
        act_t1 = QAction("Equipo 1", self)
        act_t1.triggered.connect(lambda: self.add_to_team.emit(name, 1))
        add_menu.addAction(act_t1)
        act_t2 = QAction("Equipo 2", self)
        act_t2.triggered.connect(lambda: self.add_to_team.emit(name, 2))
        add_menu.addAction(act_t2)

        menu.addSeparator()

        if not chip.saved:
            act_save = QAction("💾 Guardar jugador", self)
            act_save.triggered.connect(lambda: self.save_player.emit(name))
            menu.addAction(act_save)
            menu.addSeparator()

        act_remove = QAction("Quitar de Zona de Espera", self)
        act_remove.triggered.connect(lambda: self.remove_from_bench.emit(name))
        menu.addAction(act_remove)

        menu.exec(chip.mapToGlobal(pos))


    def _show_bulk_chip_menu(self, pos):
        menu = QMenu(self)
        n = len(self.selected_names)
        names = list(self.selected_names)

        act_save = QAction(f"⭐ Guardar {n} seleccionados", self)
        act_save.triggered.connect(lambda: self.bulk_save_requested.emit(names))
        menu.addAction(act_save)

        add_menu = menu.addMenu(f"🎮 Añadir {n} a partida")
        act_t1 = QAction(f"Equipo 1 ({n})", self)
        act_t1.triggered.connect(lambda: self.bulk_add_to_team_requested.emit(names, 1))
        add_menu.addAction(act_t1)
        act_t2 = QAction(f"Equipo 2 ({n})", self)
        act_t2.triggered.connect(lambda: self.bulk_add_to_team_requested.emit(names, 2))
        add_menu.addAction(act_t2)

        menu.addSeparator()

        act_remove = QAction(f"✕ Quitar {n} de Zona de Espera", self)
        act_remove.triggered.connect(lambda: self.bulk_remove_requested.emit(names))
        menu.addAction(act_remove)

        menu.exec(QCursor.pos())

    def _prompt_rename_chip(self, chip: _BenchChip):
        raw_name = chip.name.replace(" 👑", "").strip()
        new_name, ok = QInputDialog.getText(
            self.window(),
            "Renombrar jugador en espera",
            "Nuevo nombre del jugador:",
            text=raw_name,
        )
        if ok and new_name.strip():
            self.player_renamed.emit(chip.name, new_name.strip())

    def _prompt_pick_color(self, chip: _BenchChip):
        initial = QColor(chip.player.custom_color) if getattr(chip.player, "custom_color", None) else QColor("#61ab02")
        color = QColorDialog.getColor(initial, self.window(), f"Color para {chip.name}")
        if color.isValid():
            chip.player.custom_color = color.name()
            chip._apply_chip_style()
            self.player_color_changed.emit(chip.name, color.name())

    def _reset_custom_color(self, chip: _BenchChip):
        chip.player.custom_color = None
        chip._apply_chip_style()
        self.player_color_changed.emit(chip.name, None)

    def _open_properties_modal(self, chip: _BenchChip):
        dialog = PlayerPropertiesDialog(chip.player, self.window())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            gen, tank, dps, sup = data[:4]
            auto_mmr = data[4] if len(data) > 4 else True
            chip.player.mmr = gen
            chip.player.mmr_tank = tank
            chip.player.mmr_damage = dps
            chip.player.mmr_support = sup
            chip.player.auto_mmr_enabled = auto_mmr
            chip.indicator.setText(chip._indicators())
            self.player_role_mmr_changed.emit(chip.name, None, gen)


    def _show_empty_area_menu(self, global_pos):
        menu = QMenu(self)

        act_fill = QAction("📥 Rellenar partida con jugadores en espera", self)
        act_fill.triggered.connect(self.fill_teams_requested.emit)
        menu.addAction(act_fill)

        act_bench_all = QAction("📤 Enviar todos los jugadores de equipos a Espera", self)
        act_bench_all.triggered.connect(self.bench_all_requested.emit)
        menu.addAction(act_bench_all)

        menu.addSeparator()

        if self.chips:
            act_save_all = QAction(f"⭐ Guardar todos los jugadores en espera ({len(self.chips)})", self)
            act_save_all.triggered.connect(lambda: self.bulk_save_requested.emit([c.name for c in self.chips]))
            menu.addAction(act_save_all)

        act_add_manual = QAction("➕ Añadir nuevo jugador a espera...", self)
        act_add_manual.triggered.connect(self._prompt_add_manual_player)
        menu.addAction(act_add_manual)

        if self.chips:
            menu.addSeparator()
            act_clear = QAction("🧹 Vaciar Zona de Espera", self)
            act_clear.triggered.connect(lambda: self.bulk_remove_requested.emit([c.name for c in self.chips]))
            menu.addAction(act_clear)

        menu.exec(global_pos)

    def _prompt_add_manual_player(self):
        name, ok = QInputDialog.getText(self.window(), "Añadir a Zona de Espera", "Nombre del jugador:")
        if ok and name.strip():
            from owervach_tmixer.core.special_player import format_player_name
            formatted = format_player_name(name.strip(), True)
            p_win = self.window()
            if hasattr(p_win, "roster_controller"):
                try:
                    p_win.roster_controller.roster.add_to_bench(formatted)
                    p_win.roster_controller.after_roster_change()
                    p_win.show_toast(f"🪑 '{formatted}' añadido a Zona de Espera", "info")
                except Exception as exc:
                    p_win.show_toast(str(exc), "warning")
