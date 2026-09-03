"""Compact map strip shown on the match tab (replaces the big MAPA frame)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

from owervach_tmixer.ui.styles import theme


class MapBadge(QFrame):
    """A slim single-row bar showing the current map and its mode."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mapBadge")
        self.setMinimumHeight(34)
        self.setMaximumHeight(64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        self.title_label = QLabel("🗺️ Mapa")
        self.title_label.setObjectName("mapBadgeTitle")
        layout.addWidget(self.title_label)

        self.name_label = QLabel("—")
        self.name_label.setObjectName("mapBadgeName")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.name_label, 1)

        self.mode_label = QLabel("—")
        self.mode_label.setObjectName("mapBadgeMode")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.mode_label)

        self.apply_theme()

    def set_map(self, name: str | None, mode: str | None):
        self.name_label.setText(name or "—")
        self.mode_label.setText(mode or "—")

    def apply_theme(self):
        self.setStyleSheet(f"""
            QFrame#mapBadge {{
                background-color: #252525;
                border: 1px solid #333333;
                border-radius: 8px;
            }}
            QLabel#mapBadgeTitle {{
                font-size: 11px;
                font-weight: 600;
                color: {theme.accent()};
                letter-spacing: 1px;
            }}
            QLabel#mapBadgeName {{
                font-size: 14px;
                font-weight: 600;
                color: #FFFFFF;
            }}
            QLabel#mapBadgeMode {{
                font-size: 11px;
                font-weight: 600;
                color: {theme.accent()};
                letter-spacing: 1px;
            }}
        """)
