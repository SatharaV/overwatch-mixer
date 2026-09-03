"""Bottom drawer widget displaying live selected map preview with clean single Obsidian border."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.core.models import Map
from owervach_tmixer.ui.styles import theme
from .map_card import MODE_COLORS, map_image_path


class MapSelectedDrawer(QFrame):
    """Spacious bottom drawer displaying the currently chosen map for the match."""

    clear_requested = Signal()
    avoid_recent_changed = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._current_map: Optional[Map] = None
        self._avoid_recent = 3

        self.setObjectName("mapSelectedDrawer")
        self.setFixedHeight(64)
        self._setup_ui()
        self.apply_theme()

    def _setup_ui(self):
        d_layout = QHBoxLayout(self)
        d_layout.setContentsMargins(14, 8, 14, 8)
        d_layout.setSpacing(14)

        self.drawer_thumb = QLabel(self)
        self.drawer_thumb.setFixedSize(74, 46)
        self.drawer_thumb.setStyleSheet("border-radius: 4px; background-color: #121316; border: none;")
        d_layout.addWidget(self.drawer_thumb)

        d_info = QVBoxLayout()
        d_info.setContentsMargins(0, 0, 0, 0)
        d_info.setSpacing(3)
        d_info.setAlignment(Qt.AlignVCenter)

        self.lbl_drawer_title = QLabel("🗺️  MAPA SELECCIONADO PARA LA PARTIDA", self)
        d_info.addWidget(self.lbl_drawer_title)

        d_name_row = QHBoxLayout()
        d_name_row.setContentsMargins(0, 0, 0, 0)
        d_name_row.setSpacing(8)
        d_name_row.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.lbl_drawer_name = QLabel("Ningún mapa seleccionado (Doble clic en un mapa para seleccionarlo)", self)
        self.lbl_drawer_name.setStyleSheet("font-size: 15px; font-weight: 900; color: #FFFFFF; background: transparent; border: none;")
        d_name_row.addWidget(self.lbl_drawer_name)

        self.lbl_drawer_mode = QLabel("", self)
        self.lbl_drawer_mode.setVisible(False)
        d_name_row.addWidget(self.lbl_drawer_mode)

        d_info.addLayout(d_name_row)
        d_layout.addLayout(d_info, 1)

        lbl_avoid = QLabel("Evitar recientes:", self)
        lbl_avoid.setStyleSheet("color: #CCCCCC; font-size: 11px; font-weight: 700; background: transparent; border: none;")
        d_layout.addWidget(lbl_avoid)

        self.spin_avoid = QSpinBox(self)
        self.spin_avoid.setRange(0, 20)
        self.spin_avoid.setValue(self._avoid_recent)
        self.spin_avoid.valueChanged.connect(self.avoid_recent_changed.emit)
        d_layout.addWidget(self.spin_avoid)

        self.btn_drawer_clear = QPushButton("✕ Quitar", self)
        self.btn_drawer_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_drawer_clear.setStyleSheet("""
            QPushButton {
                background-color: #28171B; border: 1px solid #5E2028; color: #FFAAAA;
                font-weight: 700; font-size: 11px; padding: 6px 12px; border-radius: 5px;
            }
            QPushButton:hover { background-color: #441A22; border-color: #FF4444; color: #FFFFFF; }
        """)
        self.btn_drawer_clear.clicked.connect(self.clear_requested.emit)
        d_layout.addWidget(self.btn_drawer_clear)

        self.set_map(None)

    def set_map(self, map_obj: Optional[Map]):
        self._current_map = map_obj
        if not map_obj:
            self.drawer_thumb.setPixmap(QPixmap())
            self.drawer_thumb.setText("SIN MAPA")
            self.drawer_thumb.setAlignment(Qt.AlignCenter)
            self.drawer_thumb.setStyleSheet(
                "color: #666; font-size: 9px; font-weight: 800; background-color: #121316; border-radius: 4px; border: none;"
            )
            self.lbl_drawer_name.setText("Ningún mapa seleccionado (Doble clic en un mapa para seleccionarlo)")
            self.lbl_drawer_mode.setVisible(False)
            self.btn_drawer_clear.setEnabled(False)
            return

        img_path = map_image_path(map_obj.name, map_obj.mode)
        if img_path:
            pix = QPixmap(str(img_path))
            if not pix.isNull():
                self.drawer_thumb.setPixmap(
                    pix.scaled(74, 46, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                )
                self.drawer_thumb.setText("")
                self.drawer_thumb.setStyleSheet("border-radius: 4px; background-color: #121316; border: none;")

        mode_color = MODE_COLORS.get(map_obj.mode, "#888888")
        self.lbl_drawer_name.setText(map_obj.name)
        self.lbl_drawer_mode.setText(map_obj.mode.upper())
        self.lbl_drawer_mode.setStyleSheet(f"""
            QLabel {{
                font-size: 9px;
                font-weight: 800;
                color: {mode_color};
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid {mode_color};
                border-radius: 4px;
                padding: 2px 6px;
            }}
        """)
        self.lbl_drawer_mode.setVisible(True)
        self.btn_drawer_clear.setEnabled(True)

    def set_avoid_recent(self, count: int):
        self._avoid_recent = count
        self.spin_avoid.setValue(count)

    def apply_theme(self):
        accent = theme.accent()
        self.setStyleSheet(f"""
            QFrame#mapSelectedDrawer {{
                background-color: #16171E;
                border: 1px solid #282A36;
                border-top: 2.5px solid {accent};
                border-radius: 8px;
            }}
        """)
        self.lbl_drawer_title.setStyleSheet(
            f"font-size: 10px; font-weight: 800; color: {accent}; letter-spacing: 0.5px; background: transparent; border: none;"
        )
