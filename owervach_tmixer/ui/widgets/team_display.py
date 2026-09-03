"""Team display widget with proportional player slot expanding, alignment support, and theme sync."""

from __future__ import annotations

import random
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QCursor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.core.models import GameMode, Player, Role
from owervach_tmixer.ui.styles import theme

from .dnd import clear_all_drop_highlights, payload_from
from .player_slot import PlayerSlotWidget
from .match_display import MatchDisplayWidget

_RANDOM_TEAM_NAMES = [
    "Seoul Dynasty", "Dallas Fuel", "San Francisco Shock", "Shanghai Dragons",
    "London Spitfire", "Atlanta Reign", "Houston Outlaws", "Toronto Defiant",
    "Blackwatch", "Overwatch Strike Team", "Talon Operatives", "Null Sector",
    "Helix Security", "MEKA Squad", "Deadlock Gang", "Shimada Clan",
    "Ironclad Guild", "Vishkar Architects", "Lucio's Revolution",
    "Payload Princesses", "C9 Survivors", "Nanoblade Abusers", "Solo Grav Club",
    "W+M1 Enjoyers", "Backcap Kings", "Diff Delivery Inc.", "Chelas y Clutch",
    "Los Boop", "Support Strike Force", "Ana Sleepers", "Manco Squad",
    "Graviton Gang", "Rialto Rats", "Paseadores de Carga", "Pull & Pray"
]


class _DropTargetPanel(QFrame):
    def __init__(self, team_widget: TeamDisplayWidget):
        super().__init__()
        self._team_widget = team_widget
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        self._team_widget._panel_drag_enter(event)

    def dragMoveEvent(self, event):
        self._team_widget._panel_drag_move(event)

    def dragLeaveEvent(self, event):
        self._team_widget._panel_drag_leave(event)

    def dropEvent(self, event):
        self._team_widget._panel_drop(event)


class TeamDisplayWidget(QWidget):
    """A team panel of proportional player slots with solid esports header."""

    team_name_changed = Signal(str)
    slot_created = Signal(int, int, str)
    slot_renamed = Signal(int, int, str)
    slot_fixed_changed = Signal(int, int, object)
    slot_role_changed = Signal(int, int, object)
    slot_mmr_changed = Signal(int, int, object, int)
    slot_color_changed = Signal(str, object)
    slot_bench = Signal(int, int)
    slot_save = Signal(int, int)
    slot_unsave = Signal(int, int)
    slot_remove = Signal(int, int)
    slot_remove_permanent = Signal(int, int)
    player_drop_requested = Signal(object, int, object)
    reroll_roles = Signal()

    def __init__(self, team_num: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.team_num = team_num
        self._team_name = f"Equipo {self.team_num}"
        self.slot_widgets: list[PlayerSlotWidget] = []
        self._show_roles = True
        self._show_mmr = False
        self._font_size = 13
        self._font_weight = "bold"
        self._text_align = "center"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        is_t1 = (self.team_num == 1)
        team_color = "#00B4FF" if is_t1 else "#FF4444"
        team_bg = "#15181E" if is_t1 else "#1E1517"

        # Solid Header Bar Frame
        self.header_frame = QFrame(self)
        self.header_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_frame.setToolTip("Doble clic o clic derecho para renombrar el equipo")
        self.header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #171920;
                border: 1px solid #2B2F3D;
                border-top: 2.5px solid {team_color};
                border-radius: 8px;
            }}
            QFrame:hover {{
                border-color: #3E4558;
                background-color: #1B1E28;
            }}
        """)
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(6)

        self.name_label = QLabel(self._team_name, self.header_frame)
        self.name_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: 900;
                color: #FFFFFF;
                background: transparent;
                border: none;
                letter-spacing: 0.3px;
            }
        """)
        header_layout.addWidget(self.name_label, 1)

        # Doble clic restringido exclusivamente a la cabecera
        self.header_frame.mouseDoubleClickEvent = lambda e: self._prompt_rename_team() if e.button() == Qt.LeftButton else None
        self.name_label.mouseDoubleClickEvent = lambda e: self._prompt_rename_team() if e.button() == Qt.LeftButton else None

        self.lbl_count = QLabel("0 / 5", self.header_frame)
        self.lbl_count.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-weight: 800;
                color: {team_color};
                background-color: rgba({ '0, 180, 255' if is_t1 else '255, 68, 68' }, 0.14);
                border: 1px solid rgba({ '0, 180, 255' if is_t1 else '255, 68, 68' }, 0.40);
                border-radius: 4px;
                padding: 2px 8px;
            }}
        """)
        header_layout.addWidget(self.lbl_count, 0)

        self.btn_mix_roles = QPushButton("↻ Roles", self.header_frame)
        self.btn_mix_roles.setToolTip("Re-randomizar los roles de este equipo (respeta fijados 🔒)")
        self.btn_mix_roles.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_theme()
        self.btn_mix_roles.clicked.connect(self.reroll_roles.emit)
        header_layout.addWidget(self.btn_mix_roles, 0)

        self.header_frame.setContextMenuPolicy(Qt.CustomContextMenu)
        self.header_frame.customContextMenuRequested.connect(self._show_header_menu)
        self.name_label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.name_label.customContextMenuRequested.connect(self._show_header_menu)

        layout.addWidget(self.header_frame)

        self.panel = _DropTargetPanel(self)
        self.panel.setObjectName(f"teamPanel{self.team_num}")
        self.panel.setProperty("team", str(self.team_num))
        self.panel.setStyleSheet(f"""
            QFrame#teamPanel{self.team_num} {{
                background-color: {team_bg};
                border: 1px solid rgba({ '0, 180, 255' if is_t1 else '255, 68, 68' }, 0.25);
                border-radius: 8px;
            }}
        """)
        self.slots_layout = QVBoxLayout(self.panel)
        self.slots_layout.setContentsMargins(8, 8, 8, 8)
        self.slots_layout.setSpacing(7)

        layout.addWidget(self.panel, 1)

    def apply_theme(self):
        accent = theme.accent()
        self.btn_mix_roles.setStyleSheet(f"""
            QPushButton {{
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 700;
                background-color: #22252F;
                border: 1px solid #363B4B;
                border-radius: 5px;
                color: #C6CAD6;
            }}
            QPushButton:hover {{
                background-color: #2D3342;
                border-color: {accent};
                color: #FFFFFF;
            }}
            QPushButton:pressed {{ background-color: #171920; }}
            QPushButton:disabled {{ color: #555A68; border-color: #262933; background-color: #181A20; }}
        """)



    def _show_header_menu(self, pos):
        menu = QMenu(self)
        act_rename = QAction("✏️ Renombrar equipo...", self)
        act_rename.triggered.connect(self._prompt_rename_team)
        menu.addAction(act_rename)

        act_random = QAction("🎲 Sugerir nombre temático", self)
        act_random.triggered.connect(self._randomize_team_name)
        menu.addAction(act_random)

        menu.exec(QCursor.pos())

    def _prompt_rename_team(self):
        current = self.get_team_name()
        new_name, ok = QInputDialog.getText(
            self.window(),
            f"Renombrar Equipo {self.team_num}",
            "Nuevo nombre para el equipo:",
            text=current,
        )
        if ok and new_name.strip():
            self.set_team_name(new_name.strip())
            self.team_name_changed.emit(self.get_team_name())

    def _randomize_team_name(self):
        name = random.choice(_RANDOM_TEAM_NAMES)
        self.set_team_name(name)
        self.team_name_changed.emit(name)

    @property
    def name_input(self):
        class _InputCompat:
            def __init__(self, target):
                self.t = target
            def setText(self, txt):
                self.t.set_team_name(txt)
            def text(self):
                return self.t.get_team_name()
        return _InputCompat(self)

    def set_team_name(self, name: str):
        self._team_name = name.strip() or f"Equipo {self.team_num}"
        if hasattr(self, "name_label"):
            self.name_label.setText(self._team_name)

    def get_team_name(self) -> str:
        return getattr(self, "_team_name", f"Equipo {self.team_num}")

    def set_font_preferences(
        self,
        size: int,
        weight: str,
        align: str = "center",
        dynamic_font: bool = True,
        role_badge_style: str = "emoji",
        badge_outlines: bool = False
    ):
        self._font_size = size
        self._font_weight = weight
        self._text_align = align
        self._dynamic_font = dynamic_font
        self._role_badge_style = role_badge_style
        self._badge_outlines = badge_outlines
        for w in self.slot_widgets:
            w.set_font_preferences(size, weight, align, dynamic_font, role_badge_style, badge_outlines)

    def set_slots(self, slots: list[Player | None], saved_names: set[str], show_roles: bool, show_mmr: bool = False):
        self._show_roles = show_roles
        self._show_mmr = show_mmr

        while len(self.slot_widgets) < len(slots):
            idx = len(self.slot_widgets)
            w = PlayerSlotWidget(self.team_num, idx, self)
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            w.setMinimumHeight(28)
            w.setMaximumHeight(72)
            w.set_font_preferences(
                getattr(self, "_font_size", 13),
                getattr(self, "_font_weight", "bold"),
                getattr(self, "_text_align", "center"),
                getattr(self, "_dynamic_font", True),
                getattr(self, "_role_badge_style", "emoji"),
                getattr(self, "_badge_outlines", False),
            )
            w.slot_created.connect(lambda name, i=idx: self.slot_created.emit(self.team_num, i, name))
            w.slot_renamed.connect(lambda name, i=idx: self.slot_renamed.emit(self.team_num, i, name))
            w.slot_fixed_changed.connect(lambda f, i=idx: self.slot_fixed_changed.emit(self.team_num, i, f))
            w.slot_role_changed.connect(lambda r, i=idx: self.slot_role_changed.emit(self.team_num, i, r))
            w.slot_mmr_changed.connect(lambda role, mmr, i=idx: self.slot_mmr_changed.emit(self.team_num, i, role, mmr))
            w.slot_color_changed.connect(lambda name, col: self.slot_color_changed.emit(name, col))
            w.slot_bench.connect(lambda i=idx: self.slot_bench.emit(self.team_num, i))
            w.slot_save.connect(lambda i=idx: self.slot_save.emit(self.team_num, i))
            w.slot_unsave.connect(lambda i=idx: self.slot_unsave.emit(self.team_num, i))
            w.slot_remove.connect(lambda i=idx: self.slot_remove.emit(self.team_num, i))
            w.slot_remove_permanent.connect(lambda i=idx: self.slot_remove_permanent.emit(self.team_num, i))
            w.drop_requested.connect(lambda payload, i=idx: self.player_drop_requested.emit(payload, self.team_num, i))
            self.slots_layout.addWidget(w, 1)
            self.slot_widgets.append(w)

        while len(self.slot_widgets) > len(slots):
            w = self.slot_widgets.pop()
            self.slots_layout.removeWidget(w)
            w.deleteLater()

        filled = sum(1 for p in slots if p is not None)
        total = len(slots)

        if hasattr(self, "lbl_count"):
            active_p = [p for p in slots if p is not None]
            if show_mmr and active_p:
                avg = sum(p.get_mmr_for_role(p.role) for p in active_p) / len(active_p)
                self.lbl_count.setText(f"{filled} / {total} · ★ {avg:.1f}")
            else:
                self.lbl_count.setText(f"{filled} / {total}")

        for i, player in enumerate(slots):
            w = self.slot_widgets[i]
            saved = player is not None and player.name.casefold() in saved_names
            w.set_player(player, saved, show_roles, show_mmr)

    def get_players(self) -> list[tuple[str, Role | None, int]]:
        players: list[tuple[str, Role | None, int]] = []
        for w in self.slot_widgets:
            if w._player is not None:
                eff_mmr = w._player.get_mmr_for_role(w._player.role)
                players.append((w._player.name, w._player.role, eff_mmr))
        return players

    def set_show_roles(self, show: bool):
        self._show_roles = show
        for w in self.slot_widgets:
            if w._player is not None:
                w.set_player(w._player, w._saved, show, self._show_mmr)

    def set_show_mmr(self, show: bool):
        self._show_mmr = show
        for w in self.slot_widgets:
            if w._player is not None:
                w.set_player(w._player, w._saved, self._show_roles, show)

    def set_game_mode(self, mode: GameMode):
        pass

    def _panel_drag_enter(self, event):
        if payload_from(event.mimeData()) is None:
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()

    def _panel_drag_move(self, event):
        if payload_from(event.mimeData()) is None:
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()

    def _panel_drag_leave(self, event):
        pass

    def _panel_drop(self, event):
        payload = payload_from(event.mimeData())
        clear_all_drop_highlights()
        if payload is None:
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()
        self.player_drop_requested.emit(payload, self.team_num, None)
