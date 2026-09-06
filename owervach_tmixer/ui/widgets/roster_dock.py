"""Horizontal Command Dock — 2 Blizzard tactical tabs (Espectadores / Guardados) placed below teams."""

from __future__ import annotations

from typing import TYPE_CHECKING
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.ui.styles import theme
from owervach_tmixer.ui.widgets.bench_panel import BenchPanel
from owervach_tmixer.ui.widgets.saved_panel import SavedPanel
from owervach_tmixer.ui.widgets.dnd import payload_from


class _DockTabButton(QPushButton):
    """Drop-aware tab button with auto-switch timer on drag-hover."""
    dropped_on_tab = Signal(object, str)

    def __init__(self, tab_key: str, text: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.tab_key = tab_key
        self.setAcceptDrops(True)
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(400)
        self._hover_timer.timeout.connect(self._auto_switch)

    def _auto_switch(self):
        self.setChecked(True)

    def dragEnterEvent(self, event):
        payload = payload_from(event.mimeData())
        if payload is None:
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()
        self._hover_timer.start()

    def dragMoveEvent(self, event):
        payload = payload_from(event.mimeData())
        if payload is None:
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()

    def dragLeaveEvent(self, event):
        self._hover_timer.stop()
        event.accept()

    def dropEvent(self, event):
        self._hover_timer.stop()
        payload = payload_from(event.mimeData())
        if payload is None:
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()
        self.setChecked(True)
        self.dropped_on_tab.emit(payload, self.tab_key)


class RosterDockWidget(QFrame):
    """Unified horizontal dock positioned under the teams with 2 distinct tabs: Espectadores and Guardados."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("rosterDock")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(150)

        self._setup_ui()
        self.apply_theme()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # 1. Pestañas Horizontales Estilo Blizzard (Espectadores / Guardados)
        self.switcher_container = QWidget(self)
        s_layout = QHBoxLayout(self.switcher_container)
        s_layout.setContentsMargins(0, 0, 0, 0)
        s_layout.setSpacing(4)

        self._tab_group = QButtonGroup(self)
        self._tab_group.setExclusive(True)

        self.btn_tab_bench = _DockTabButton("bench", "ESPECTADORES (0)", self.switcher_container)
        self.btn_tab_bench.setCheckable(True)
        self.btn_tab_bench.setChecked(True)
        self.btn_tab_bench.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_tab_saved = _DockTabButton("saved", "GUARDADOS (0)", self.switcher_container)
        self.btn_tab_saved.setCheckable(True)
        self.btn_tab_saved.setChecked(False)
        self.btn_tab_saved.setCursor(Qt.CursorShape.PointingHandCursor)

        self._tab_group.addButton(self.btn_tab_bench)
        self._tab_group.addButton(self.btn_tab_saved)

        s_layout.addWidget(self.btn_tab_bench, 1)
        s_layout.addWidget(self.btn_tab_saved, 1)

        main_layout.addWidget(self.switcher_container, 0)

        # 2. Contenedor de Páginas (Stack)
        self.stack = QStackedWidget(self)
        self.bench_panel = BenchPanel(self.stack)
        self.saved_panel = SavedPanel(self.stack)

        self.stack.addWidget(self.bench_panel)
        self.stack.addWidget(self.saved_panel)
        main_layout.addWidget(self.stack, 1)

        self.btn_tab_bench.toggled.connect(lambda on: on and self._switch_tab(0))
        self.btn_tab_saved.toggled.connect(lambda on: on and self._switch_tab(1))

        self.btn_tab_bench.dropped_on_tab.connect(self._on_tab_dropped)
        self.btn_tab_saved.dropped_on_tab.connect(self._on_tab_dropped)

        self._update_tab_buttons_style()

    def _on_tab_dropped(self, payload: dict, target_key: str):
        if target_key == "bench":
            self.bench_panel.bench_drop_entry.emit(payload)
        elif target_key == "saved":
            self.saved_panel.player_dropped.emit(payload)

    def _switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        self._update_tab_buttons_style()
        if hasattr(self, "bench_panel"):
            self.bench_panel.selected_names.clear()
            self.bench_panel._refresh_selection_visuals()
        if hasattr(self, "saved_panel"):
            self.saved_panel.selected_names.clear()
            self.saved_panel._refresh_selection_visuals()

    def _update_tab_buttons_style(self):
        curr = self.stack.currentIndex()
        t = theme.tokens()
        is_ow = (t.id == "overwatch")
        f_disp = t.font_family_display if is_ow else t.font_family

        for idx, btn in enumerate((self.btn_tab_bench, self.btn_tab_saved)):
            is_active = (curr == idx)
            if is_ow:
                if is_active:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            font-family: {f_disp};
                            font-size: 15px;
                            font-weight: 900;
                            font-style: italic;
                            color: #FFFFFF;
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #005BD4, stop:1 #003894);
                            border: none;
                            border-bottom: 3px solid #00F0FF;
                            padding: 6px 18px;
                            letter-spacing: 0.8px;
                        }}
                    """)
                else:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            font-family: {f_disp};
                            font-size: 15px;
                            font-weight: 900;
                            font-style: italic;
                            color: #92A4BC;
                            background-color: rgba(10, 18, 30, 0.70);
                            border: none;
                            border-bottom: 3px solid transparent;
                            padding: 6px 16px;
                            letter-spacing: 0.8px;
                        }}
                        QPushButton:hover {{
                            color: #FFFFFF;
                            background-color: rgba(25, 40, 65, 0.85);
                        }}
                    """)
            else:
                accent = t.accent
                if is_active:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            font-size: 11px;
                            font-weight: 800;
                            color: {accent};
                            background-color: {theme.accent_rgba(0.14)};
                            border: 1px solid {accent};
                            border-radius: 5px;
                            padding: 5px 12px;
                        }}
                    """)
                else:
                    btn.setStyleSheet("""
                        QPushButton {
                            font-size: 11px;
                            font-weight: 700;
                            color: #8C92A4;
                            background-color: #171922;
                            border: 1px solid #282B36;
                            border-radius: 5px;
                            padding: 5px 12px;
                        }
                        QPushButton:hover {
                            color: #FFFFFF;
                            background-color: #21242E;
                        }
                    """)

    def update_counts(self, saved_count: int, bench_count: int):
        is_ow = (theme.tokens().id == "overwatch")
        if is_ow:
            self.btn_tab_bench.setText(f"ESPECTADORES ({bench_count})")
            self.btn_tab_saved.setText(f"GUARDADOS ({saved_count})")
        else:
            self.btn_tab_bench.setText(f"🪑 Zona de Espera ({bench_count})")
            self.btn_tab_saved.setText(f"⭐ Guardados ({saved_count})")

    @property
    def bans_panel(self):
        p = self.window()
        return getattr(p, "bans_panel", None)

    def apply_theme(self):
        self.setStyleSheet("""
            QFrame#rosterDock {
                background-color: transparent;
                border: none;
            }
        """)
        self._update_tab_buttons_style()
        self.bench_panel.apply_theme()
        self.saved_panel.apply_theme()
