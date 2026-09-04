"""Saved players panel with clean separator line, outline action toolbar, and clean drag lifecycle."""

from __future__ import annotations
from .smooth_scroll import SmoothScrollArea

from typing import Optional, Set
from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QAction, QColor, QDrag, QGuiApplication, QCursor, QPainter, QBrush, QPen, QFont
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QDialog,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QRubberBand,
    QScrollArea,
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
from .flow_layout import FlowLayout


def sanitize_player_name(raw: str) -> Optional[str]:
    clean = raw.strip()
    if not clean:
        return None
    bad_tokens = (
        "<<", ">>", "import ", "from ", "class ", "def ", "return ",
        "cat <<", "echo ", "sudo ", "python", ".py", ".sh", ".json",
        "{", "}", "();", "$", "`", "\\", "/*", "*/", "==", "!=",
    )
    clean_lower = clean.lower()
    if any(tok in clean_lower for tok in bad_tokens):
        return None
    if len(clean) > 24 or "\n" in clean or "\r" in clean:
        return None
    return clean


class SavedChip(QFrame):
    def set_selected(self, selected: bool):
        self._is_selected = selected
        self._apply_chip_style()

    def dragEnterEvent(self, event):
        payload = payload_from(event.mimeData())
        if payload and payload.get("kind") == "saved" and payload.get("name") != self.name:
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        payload = payload_from(event.mimeData())
        if payload and payload.get("kind") == "saved":
            src_name = payload.get("name")
            if src_name and src_name != self.name:
                self._panel.reorder_saved.emit(src_name, self.name)
                event.accept()
                return
        super().dropEvent(event)

    """A single draggable saved-player chip with custom color and live status dot."""

    def __init__(self, panel: SavedPanel, player: Player, in_active: bool = False, in_bench: bool = False, parent: QWidget | None = None):
        super().__init__(parent or panel)
        self._panel = panel
        self.player = player
        self.name = player.name
        self.in_active = in_active
        self.in_bench = in_bench
        self.special = is_special_player_name(player.name)
        self._pressing = False
        self._press_pos = QPoint()
        self.setObjectName("savedChip")
        self.setToolTip(
            "🟢 En partida activa" if in_active else ("🟡 En Zona de Espera" if in_bench else "Arrastra para añadir a un equipo")
        )
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(
            lambda pos, chip=self: self._panel._show_chip_menu(chip, pos))

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        self.label = QLabel(self._chip_text())
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.label)

        self._apply_chip_style()

    def _chip_text(self) -> str:
        parts = []
        if self.in_active:
            parts.append("🟢")
        elif self.in_bench:
            parts.append("🟡")

        if getattr(self._panel, "_show_mmr", False):
            mmr = getattr(self.player, "mmr", 5)
            parts.append(f"⚡{mmr}")
        if self.player.fixed_team:
            parts.append("🔒")
        parts.append(self.player.name)
        if self.player.role:
            parts.append(f"· {self.player.role.value.capitalize()}")
        return "  ".join(parts)

    def _apply_chip_style(self):
        custom_color = getattr(self.player, "custom_color", None)
        accent = theme.accent()
        if getattr(self, "_is_selected", False):
            self.setStyleSheet(f"""
                QFrame#savedChip {{
                    background-color: {theme.accent_rgba(0.25)};
                    border: 1.5px solid {accent};
                    border-radius: 6px;
                }}
                QLabel {{ color: #FFFFFF; font-size: 12px; font-weight: 800; background: transparent; }}
            """)
            return

        if self.special:
            self.setStyleSheet("""
                QFrame#savedChip {
                    background-color: #1D261A;
                    border: 1px solid #48781B;
                    border-radius: 6px;
                }
                QFrame#savedChip:hover {
                    background-color: #263321;
                    border-color: #61ab02;
                }
                QLabel {
                    color: #A4E062;
                    font-size: 12px;
                    font-weight: 700;
                    background: transparent;
                }
            """)
            glow = QGraphicsDropShadowEffect(self)
            glow.setColor(QColor(SPECIAL_GLOW))
            glow.setBlurRadius(14)
            glow.setOffset(0, 0)
            self.setGraphicsEffect(glow)
        elif custom_color:
            self.setStyleSheet(f"""
                QFrame#savedChip {{
                    background-color: #181A1E;
                    border: 1px solid {custom_color};
                    border-radius: 6px;
                }}
                QFrame#savedChip:hover {{
                    background-color: #22252C;
                }}
                QLabel {{
                    color: {custom_color};
                    font-size: 12px;
                    font-weight: 700;
                    background: transparent;
                }}
            """)
        else:
            border_color = "#3A4436" if self.in_active else "#2B2E36"
            self.setStyleSheet(f"""
                QFrame#savedChip {{
                    background-color: #181A1E;
                    border: 1px solid {border_color};
                    border-radius: 6px;
                }}
                QFrame#savedChip:hover {{
                    background-color: #22252C;
                    border-color: {accent};
                }}
                QLabel {{
                    color: #D8DCE5;
                    font-size: 12px;
                    font-weight: 600;
                    background: transparent;
                }}
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
                payload = make_payload("saved_multi", self.name, names=names)
                is_multi = True
            else:
                payload = make_payload("saved", self.name)
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
                painter.setBrush(QBrush(QColor(theme.accent())))
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
        self._panel.chip_activated.emit(self.name)
        event.accept()


class SavedPanel(QFrame):
    """Clean full-height pool of permanently saved players with distinct separator and outline toolbar."""

    add_to_match = Signal(str, object)
    add_to_bench = Signal(str)
    remove_saved = Signal(str)
    bulk_saved = Signal(list)
    import_file = Signal(str)
    export_file = Signal(str)
    chip_activated = Signal(str)
    player_dropped = Signal(object)
    player_role_mmr_changed = Signal(str, object, int)
    player_renamed = Signal(str, str)
    player_color_changed = Signal(str, object)
    fill_teams_from_saved_requested = Signal()
    send_all_saved_to_bench_requested = Signal()
    reorder_saved = Signal(str, str)
    bulk_add_to_bench_requested = Signal(list)
    bulk_add_to_team_requested = Signal(list, int)
    bulk_remove_requested = Signal(list)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._show_mmr = False
        self.chips: list[SavedChip] = []
        self._buttons: list[QPushButton] = []
        self.selected_names: set[str] = set()
        self._last_selected: str | None = None
        self._rubber_band = None
        self._rubber_origin = QPoint()
        self.setObjectName("savedPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 1. Add Input Row
        add_row = QHBoxLayout()
        add_row.setSpacing(6)

        self.add_input = QLineEdit()
        self.add_input.setPlaceholderText("Guardar jugador en la lista…")
        self.add_input.returnPressed.connect(self._on_add)
        add_row.addWidget(self.add_input, 1)

        self.btn_add = QPushButton("+ Guardar")
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.clicked.connect(self._on_add)
        add_row.addWidget(self.btn_add)
        layout.addLayout(add_row)

        # 2. Outline Toolbar Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        btn_quick_fill = QPushButton("📥 Llenar")
        btn_quick_fill.setToolTip("Rellenar huecos de los equipos con jugadores guardados")
        btn_quick_fill.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_quick_fill.clicked.connect(self.fill_teams_from_saved_requested.emit)

        btn_quick_bench = QPushButton("🪑 Espera")
        btn_quick_bench.setToolTip("Enviar todos los jugadores guardados a Zona de Espera")
        btn_quick_bench.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_quick_bench.clicked.connect(self.send_all_saved_to_bench_requested.emit)

        btn_paste = QPushButton("📋 Pegar")
        btn_paste.setToolTip("Añadir jugadores desde el portapapeles")
        btn_paste.clicked.connect(self._paste_clipboard)
        btn_paste.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_import = QPushButton("📂 Import")
        btn_import.setToolTip("Cargar lista desde archivo (.json o .txt)")
        btn_import.clicked.connect(self._pick_import)
        btn_import.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_export = QPushButton("💾 Export")
        btn_export.setToolTip("Guardar lista a un archivo (.json o .txt)")
        btn_export.clicked.connect(self._pick_export)
        btn_export.setCursor(Qt.CursorShape.PointingHandCursor)

        self._buttons = [self.btn_add, btn_quick_fill, btn_quick_bench, btn_paste, btn_import, btn_export]
        for b in self._buttons[1:]:
            btn_row.addWidget(b, 1)

        layout.addLayout(btn_row)

        # 3. Separador Obsidian Nítido
        self.sep = QFrame(self)
        self.sep.setFrameShape(QFrame.Shape.HLine)
        self.sep.setFixedHeight(1)
        self.sep.setStyleSheet("background-color: #2D3242; border: none; margin: 2px 0 2px 0;")
        layout.addWidget(self.sep)

        # 4. Scrollable Pool
        self.pool = QWidget()
        self.pool.setObjectName("savedPool")
        self.pool_layout = FlowLayout(self.pool, h_spacing=6, v_spacing=6)
        self.pool_scroll = SmoothScrollArea()
        self.pool_scroll.setObjectName("savedPoolScroll")
        self.pool_scroll.setWidgetResizable(True)
        self.pool_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.pool_scroll.setWidget(self.pool)
        self.pool_scroll.viewport().setAutoFillBackground(False)
        self.pool_scroll.viewport().setStyleSheet("background-color: transparent; border: none;")
        self.pool_scroll.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.pool_scroll.customContextMenuRequested.connect(lambda pos: self._show_empty_area_menu(self.pool_scroll.mapToGlobal(pos)))
        self.pool.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.pool.customContextMenuRequested.connect(lambda pos: self._show_empty_area_menu(self.pool.mapToGlobal(pos)))
        layout.addWidget(self.pool_scroll, 1)

        self.setAcceptDrops(True)
        self.apply_theme()

    def _relayout_pool(self):
        if not hasattr(self, "pool_scroll") or not hasattr(self, "pool_layout"):
            return
        vw = self.pool_scroll.viewport().width() if self.pool_scroll.viewport() else 0
        if vw <= 0 and hasattr(self, "pool"):
            vw = self.pool.width()
        if vw <= 0:
            vw = self.width() - 24
        if vw > 0:
            self.pool.resize(vw, max(60, self.pool.height()))
            self.pool_layout.setGeometry(self.pool.rect())
        self.pool.updateGeometry()
        self.pool.update()

    def showEvent(self, event):
        super().showEvent(event)
        self._relayout_pool()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout_pool()

    def apply_theme(self):
        accent = theme.accent()
        self.setStyleSheet(f"""
            QFrame#savedPanel {{
                background-color: #16171D;
                border: 1px solid #282A33;
                border-radius: 8px;
            }}
            QFrame#savedPanel[dropTarget="true"] {{
                border: 1.5px solid {accent};
                background-color: #1F261B;
            }}
            QScrollArea#savedPoolScroll, QScrollArea#savedPoolScroll QWidget#savedPool {{
                background-color: transparent;
                border: none;
            }}
        """)

        if hasattr(self, "add_input"):
            self.add_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: #141518;
                    border: 1px solid #2B2E36;
                    border-radius: 6px;
                    padding: 6px 10px;
                    color: #FFFFFF;
                    font-size: 12px;
                }}
                QLineEdit:focus {{ border-color: {accent}; }}
            """)

        if hasattr(self, "btn_add"):
            self.btn_add.setStyleSheet(f"""
                QPushButton {{
                    background-color: #171A24;
                    border: 1px solid {accent};
                    border-radius: 6px;
                    padding: 6px 12px;
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: 800;
                }}
                QPushButton:hover {{
                    background-color: {theme.accent_rgba(0.16)};
                    border-color: {theme.accent_light()};
                }}
                QPushButton:pressed {{ background-color: #12141C; }}
            """)

        for b in getattr(self, "_buttons", [])[1:]:
            b.setStyleSheet(f"""
                QPushButton {{
                    font-size: 11px;
                    font-weight: 700;
                    color: #C0C5D4;
                    background-color: #171A24;
                    border: 1px solid #2E3344;
                    border-radius: 5px;
                    padding: 5px 3px;
                    font-size: 10.5px;
                }}
                QPushButton:hover {{
                    background-color: #222634;
                    border-color: {accent};
                    color: #FFFFFF;
                }}
                QPushButton:pressed {{ background-color: #12141A; }}
            """)

        for chip in self.chips:
            chip._apply_chip_style()

    @property
    def content(self):
        return self.pool_scroll

    def header_height(self) -> int:
        return 48

    @property
    def toggle_btn(self):
        if not hasattr(self, "_dummy_toggle"):
            btn = QPushButton(f"⭐ Guardados ({len(self.chips)})", self)
            btn.clicked.connect(lambda: self.pool_scroll.setVisible(not self.pool_scroll.isVisible()))
            self._dummy_toggle = btn
        self._dummy_toggle.setText(f"⭐ Guardados ({len(self.chips)})")
        return self._dummy_toggle

    def dragEnterEvent(self, event):
        payload = payload_from(event.mimeData())
        if payload is None or payload.get("kind") not in ("slot", "bench"):
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        set_drop_highlight(self, True)
        event.accept()

    def dragMoveEvent(self, event):
        payload = payload_from(event.mimeData())
        if payload is None or payload.get("kind") not in ("slot", "bench"):
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()

    def dragLeaveEvent(self, event):
        set_drop_highlight(self, False)

    def dropEvent(self, event):
        payload = payload_from(event.mimeData())
        set_drop_highlight(self, False)
        if payload is None or payload.get("kind") not in ("slot", "bench"):
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()
        self.player_dropped.emit(payload)

    def set_saved(
        self,
        saved: list[Player],
        active_names: Set[str] | None = None,
        bench_names: Set[str] | None = None,
        show_mmr: bool = False,
    ):
        self._show_mmr = show_mmr
        active_lower = {n.casefold() for n in (active_names or ())}
        bench_lower = {n.casefold() for n in (bench_names or ())}

        while self.pool_layout.count():
            item = self.pool_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

        # Purgar selecciones de jugadores que ya no están en guardados
        saved_names_set = {p.name for p in saved}
        self.selected_names.intersection_update(saved_names_set)
        if self._last_selected not in saved_names_set:
            self._last_selected = None

        self.chips = []
        for p in saved:
            p_fold = p.name.casefold()
            in_act = p_fold in active_lower
            in_bnc = p_fold in bench_lower
            chip = SavedChip(self, p, in_active=in_act, in_bench=in_bnc, parent=self.pool)
            self.pool_layout.addWidget(chip)
            self.chips.append(chip)
        self._relayout_pool()

    def _on_add(self):
        name = self.add_input.text().strip()
        clean = sanitize_player_name(name)
        if clean:
            formatted = format_player_name(clean, True)
            self.bulk_saved.emit([formatted])
            self.add_input.clear()
        elif name:
            p_window = self.window()
            if hasattr(p_window, "show_toast"):
                p_window.show_toast("⚠️ Nombre no válido (máx 24 caracteres sin símbolos de código)", "warning")

    def _paste_clipboard(self):
        text = QGuiApplication.clipboard().text() or ""
        valid_names = []
        for line in text.splitlines():
            s = sanitize_player_name(line)
            if s:
                formatted = format_player_name(s, True)
                if formatted and formatted not in valid_names:
                    valid_names.append(formatted)
            if len(valid_names) >= 40:
                break
        if valid_names:
            self.bulk_saved.emit(valid_names)
        else:
            p_window = self.window()
            if hasattr(p_window, "show_toast"):
                p_window.show_toast("⚠️ No se encontraron nombres válidos en el portapapeles", "warning")

    def _pick_import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar jugadores guardados", "",
            "JSON Files (*.json);;Text Files (*.txt)"
        )
        if path:
            self.import_file.emit(path)

    def _pick_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar jugadores guardados", "saved_players.json",
            "JSON Files (*.json);;Text Files (*.txt)"
        )
        if path:
            self.export_file.emit(path)


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

    def _show_chip_menu(self, chip: SavedChip, pos):
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

        act_reset_mmr = QAction("⚡ Restablecer MMR a 5", self)
        act_reset_mmr.triggered.connect(lambda: self._reset_chip_mmr(chip))
        menu.addAction(act_reset_mmr)

        act_reset_mmr = QAction("⚡ Restablecer MMR a 5", self)
        act_reset_mmr.triggered.connect(lambda: self._reset_chip_mmr(chip))
        menu.addAction(act_reset_mmr)

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
        act_t1.triggered.connect(lambda: self.add_to_match.emit(name, 1))
        add_menu.addAction(act_t1)
        act_t2 = QAction("Equipo 2", self)
        act_t2.triggered.connect(lambda: self.add_to_match.emit(name, 2))
        add_menu.addAction(act_t2)

        act_bench = QAction("Añadir a Zona de Espera", self)
        act_bench.triggered.connect(lambda: self.add_to_bench.emit(name))
        menu.addAction(act_bench)

        menu.addSeparator()

        act_del = QAction("Eliminar de guardados", self)
        act_del.triggered.connect(lambda: self.remove_saved.emit(name))
        menu.addAction(act_del)

        menu.exec(chip.mapToGlobal(pos))


    def _show_bulk_chip_menu(self, pos):
        menu = QMenu(self)
        n = len(self.selected_names)
        names = list(self.selected_names)

        act_bench = QAction(f"🪑 Añadir {n} a Zona de Espera", self)
        act_bench.triggered.connect(lambda: self.bulk_add_to_bench_requested.emit(names))
        menu.addAction(act_bench)

        add_menu = menu.addMenu(f"🎮 Añadir {n} a partida")
        act_t1 = QAction(f"Equipo 1 ({n})", self)
        act_t1.triggered.connect(lambda: self.bulk_add_to_team_requested.emit(names, 1))
        add_menu.addAction(act_t1)
        act_t2 = QAction(f"Equipo 2 ({n})", self)
        act_t2.triggered.connect(lambda: self.bulk_add_to_team_requested.emit(names, 2))
        add_menu.addAction(act_t2)

        menu.addSeparator()

        act_del = QAction(f"🗑️ Eliminar {n} de guardados", self)
        act_del.triggered.connect(lambda: self.bulk_remove_requested.emit(names))
        menu.addAction(act_del)

        menu.exec(QCursor.pos())

    def _prompt_rename_chip(self, chip: SavedChip):
        raw_name = chip.name.replace(" 👑", "").strip()
        new_name, ok = QInputDialog.getText(
            self.window(),
            "Renombrar jugador guardado",
            "Nuevo nombre del jugador:",
            text=raw_name,
        )
        if ok and new_name.strip():
            self.player_renamed.emit(chip.name, new_name.strip())

    def _prompt_pick_color(self, chip: SavedChip):
        initial = QColor(chip.player.custom_color) if getattr(chip.player, "custom_color", None) else QColor("#61ab02")
        color = QColorDialog.getColor(initial, self.window(), f"Color para {chip.name}")
        if color.isValid():
            chip.player.custom_color = color.name()
            chip._apply_chip_style()
            self.player_color_changed.emit(chip.name, color.name())

    def _reset_custom_color(self, chip: SavedChip):
        chip.player.custom_color = None
        chip._apply_chip_style()
        self.player_color_changed.emit(chip.name, None)

    def _open_properties_modal(self, chip: SavedChip):
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
            chip.label.setText(chip._chip_text())
            self.player_role_mmr_changed.emit(chip.name, None, gen)


    def _reset_chip_mmr(self, chip: SavedChip):
        chip.player.reset_mmr(5)
        chip.label.setText(chip._chip_text())
        self.player_role_mmr_changed.emit(chip.name, None, 5)
        p_win = self.window()
        if hasattr(p_win, "show_toast"):
            p_win.show_toast(f"⚡ MMR de {chip.name} restablecido a 5", "info")

    def _show_empty_area_menu(self, global_pos):
        menu = QMenu(self)

        act_to_bench = QAction("🪑 Enviar todos los guardados a Zona de Espera", self)
        act_to_bench.triggered.connect(self.send_all_saved_to_bench_requested.emit)
        menu.addAction(act_to_bench)

        act_fill = QAction("📥 Rellenar partida con jugadores guardados", self)
        act_fill.triggered.connect(self.fill_teams_from_saved_requested.emit)
        menu.addAction(act_fill)

        menu.addSeparator()

        act_paste = QAction("📋 Pegar jugadores del portapapeles", self)
        act_paste.triggered.connect(self._paste_clipboard)
        menu.addAction(act_paste)

        act_import = QAction("📂 Importar archivo (.json / .txt)...", self)
        act_import.triggered.connect(self._pick_import)
        menu.addAction(act_import)

        act_export = QAction("💾 Exportar archivo (.json / .txt)...", self)
        act_export.triggered.connect(self._pick_export)
        menu.addAction(act_export)

        if self.chips:
            menu.addSeparator()
            act_clear_all = QAction("🗑️ Vaciar todos los guardados...", self)
            act_clear_all.triggered.connect(lambda: self.bulk_remove_requested.emit([c.name for c in self.chips]))
            menu.addAction(act_clear_all)

        menu.exec(global_pos)
