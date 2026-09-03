"""Obsidian Command Dock — unified right-side panel with drop-aware tab headers and resizable ban splitter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.ui.styles import theme
from owervach_tmixer.ui.widgets.bans_panel import BansPanel
from owervach_tmixer.ui.widgets.bench_panel import BenchPanel
from owervach_tmixer.ui.widgets.saved_panel import SavedPanel
from owervach_tmixer.ui.widgets.dnd import payload_from

if TYPE_CHECKING:
    from owervach_tmixer.core.models import Player


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
    """Unified right-side dock with drop-aware tabs and resizable vertical bans panel."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("rosterDock")
        self.setMinimumWidth(320)
        self.setMaximumWidth(420)

        self._setup_ui()
        self.apply_theme()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # 1. Top Segmented Switcher
        switcher_container = QWidget(self)
        switcher_container.setStyleSheet("""
            QWidget {
                background-color: #16171E;
                border: 1px solid #282B36;
                border-radius: 8px;
            }
        """)
        s_layout = QHBoxLayout(switcher_container)
        s_layout.setContentsMargins(6, 6, 6, 6)
        s_layout.setSpacing(6)

        self._tab_group = QButtonGroup(self)
        self._tab_group.setExclusive(True)

        self.btn_tab_bench = _DockTabButton("bench", "🪑 Zona de Espera (0)", switcher_container)
        self.btn_tab_bench.setCheckable(True)
        self.btn_tab_bench.setChecked(True)
        self.btn_tab_bench.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_tab_saved = _DockTabButton("saved", "⭐ Guardados (0)", switcher_container)
        self.btn_tab_saved.setCheckable(True)
        self.btn_tab_saved.setChecked(False)
        self.btn_tab_saved.setCursor(Qt.CursorShape.PointingHandCursor)

        self._tab_group.addButton(self.btn_tab_bench)
        self._tab_group.addButton(self.btn_tab_saved)

        s_layout.addWidget(self.btn_tab_bench, 1)
        s_layout.addWidget(self.btn_tab_saved, 1)
        main_layout.addWidget(switcher_container, 0)

        # 2. Vertical Splitter
        self.vertical_splitter = QSplitter(Qt.Orientation.Vertical, self)
        self.vertical_splitter.setHandleWidth(6)
        self.vertical_splitter.setChildrenCollapsible(False)
        self.vertical_splitter.setStyleSheet("""
            QSplitter::handle:vertical {
                background-color: #20232E;
                height: 6px;
                border-radius: 3px;
                margin: 2px 8px;
            }
            QSplitter::handle:vertical:hover {
                background-color: #61ab02;
            }
        """)

        self.stack = QStackedWidget(self.vertical_splitter)
        self.bench_panel = BenchPanel(self.stack)
        self.saved_panel = SavedPanel(self.stack)

        self.bench_panel.setMaximumHeight(16777215)
        self.saved_panel.setMaximumHeight(16777215)

        self.stack.addWidget(self.bench_panel)
        self.stack.addWidget(self.saved_panel)
        self.vertical_splitter.addWidget(self.stack)

        self.btn_tab_bench.toggled.connect(lambda on: on and self._switch_tab(0))
        self.btn_tab_saved.toggled.connect(lambda on: on and self._switch_tab(1))

        # Drops directos a las pestañas
        self.btn_tab_bench.dropped_on_tab.connect(self._on_tab_dropped)
        self.btn_tab_saved.dropped_on_tab.connect(self._on_tab_dropped)

        self.bans_panel = BansPanel(self.vertical_splitter)
        self.vertical_splitter.addWidget(self.bans_panel)

        self.vertical_splitter.setStretchFactor(0, 4)
        self.vertical_splitter.setStretchFactor(1, 1)
        self.vertical_splitter.setSizes([380, 130])

        main_layout.addWidget(self.vertical_splitter, 1)
        self._update_tab_buttons_style()

    def _on_tab_dropped(self, payload: dict, target_key: str):
        if target_key == "bench":
            self.bench_panel.bench_drop_entry.emit(payload)
        elif target_key == "saved":
            self.saved_panel.player_dropped.emit(payload)

    def _switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        self._update_tab_buttons_style()
        # Limpiar selecciones residuales al cambiar de pestaña
        if hasattr(self, "bench_panel"):
            self.bench_panel.selected_names.clear()
            self.bench_panel._refresh_selection_visuals()
        if hasattr(self, "saved_panel"):
            self.saved_panel.selected_names.clear()
            self.saved_panel._refresh_selection_visuals()

    def _update_tab_buttons_style(self):
        curr = self.stack.currentIndex()
        accent = theme.accent()

        if curr == 0:
            self.btn_tab_bench.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 180, 255, 0.14);
                    border: 1px solid #00B4FF;
                    border-radius: 6px;
                    color: #00B4FF;
                    font-size: 11px;
                    font-weight: 900;
                    padding: 6px 10px;
                }
            """)
            self.btn_tab_saved.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 6px;
                    color: #8C92A4;
                    font-size: 11px;
                    font-weight: 700;
                    padding: 6px 10px;
                }
                QPushButton:hover {
                    color: #FFFFFF;
                    background-color: #21242E;
                }
            """)
        else:
            self.btn_tab_saved.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme.accent_rgba(0.14)};
                    border: 1px solid {accent};
                    border-radius: 6px;
                    color: {accent};
                    font-size: 11px;
                    font-weight: 900;
                    padding: 6px 10px;
                }}
            """)
            self.btn_tab_bench.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 6px;
                    color: #8C92A4;
                    font-size: 11px;
                    font-weight: 700;
                    padding: 6px 10px;
                }
                QPushButton:hover {
                    color: #FFFFFF;
                    background-color: #21242E;
                }
            """)

    def update_counts(self, saved_count: int, bench_count: int):
        self.btn_tab_bench.setText(f"🪑 Zona de Espera ({bench_count})")
        self.btn_tab_saved.setText(f"⭐ Guardados ({saved_count})")

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
        self.bans_panel.apply_theme()
