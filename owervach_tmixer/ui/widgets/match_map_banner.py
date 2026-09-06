"""Banner widget for displaying the active map with responsive layout and perfect symmetry."""

from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPixmap, QLinearGradient
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.core.models import Map
from owervach_tmixer.ui.widgets.map_card import MODE_COLORS, map_image_path
from owervach_tmixer.ui.styles import theme

_PANORAMA_CACHE: dict[str, QPixmap] = {}


class MatchMapBanner(QFrame):
    """Map banner with generous vertical space for 2-line titles and symmetrical action buttons."""

    reroll_requested = Signal()
    clear_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._map_obj: Map | None = None
        self._raw_pixmap: QPixmap | None = None

        self.setObjectName("matchMapBanner")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._setup_ui()
        self._update_display()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 10, 14, 12)
        main_layout.setSpacing(2)

        # 1. Fila Superior: Modo (Izq) vs Quitar (Der)
        self.top_row = QHBoxLayout()
        self.top_row.setContentsMargins(0, 0, 0, 0)
        self.top_row.setSpacing(6)

        self.lbl_mode = QLabel(self)
        self.lbl_mode.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.top_row.addWidget(self.lbl_mode, 0, Qt.AlignLeft | Qt.AlignVCenter)

        self.top_row.addStretch(1)

        self.btn_clear = QPushButton("✕  Quitar", self)
        self.btn_clear.setToolTip("Deseleccionar mapa actual")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setFixedSize(78, 24)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                font-size: 11px; font-weight: 700; color: #FF9E9E;
                background-color: rgba(90, 20, 26, 0.30);
                border: 1px solid #6E222B; border-radius: 4px; padding: 2px 8px;
            }
            QPushButton:hover { background-color: rgba(255, 68, 68, 0.25); border-color: #FF4444; color: #FFFFFF; }
        """)
        self.btn_clear.clicked.connect(self.clear_requested.emit)
        self.top_row.addWidget(self.btn_clear, 0, Qt.AlignRight | Qt.AlignVCenter)

        main_layout.addLayout(self.top_row)
        main_layout.addStretch(1)

        # 2. Fila Inferior: Título en 2 líneas (Izq) vs Mapa Aleatorio (Der)
        self.bottom_row = QHBoxLayout()
        self.bottom_row.setContentsMargins(0, 0, 0, 0)
        self.bottom_row.setSpacing(8)

        left_name_box = QVBoxLayout()
        left_name_box.setContentsMargins(0, 0, 0, 0)
        left_name_box.setSpacing(1)

        self.lbl_name = QLabel(self)
        self.lbl_name.setWordWrap(True)
        self.lbl_name.setMinimumHeight(44)
        name_shadow = QGraphicsDropShadowEffect(self.lbl_name)
        name_shadow.setColor(QColor(0, 0, 0, 240))
        name_shadow.setBlurRadius(4)
        name_shadow.setOffset(1, 1)
        self.lbl_name.setGraphicsEffect(name_shadow)
        left_name_box.addWidget(self.lbl_name, 0, Qt.AlignLeft | Qt.AlignVCenter)

        self.lbl_subtitle = QLabel("Partida de Satara", self)
        self.lbl_subtitle.hide()
        left_name_box.addWidget(self.lbl_subtitle, 0, Qt.AlignLeft)

        self.bottom_row.addLayout(left_name_box, 1)

        self.btn_reroll = QPushButton("🎲  Mapa Aleatorio", self)
        self.btn_reroll.setToolTip("Sortear un mapa aleatorio")
        self.btn_reroll.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reroll.setFixedSize(130, 24)
        self.btn_reroll.setStyleSheet("""
            QPushButton {
                font-size: 11px; font-weight: 700; color: #CCD1DE;
                background-color: rgba(23, 26, 34, 0.30);
                border: 1px solid #2C303E; border-radius: 4px; padding: 2px 8px;
            }
            QPushButton:hover { background-color: rgba(35, 39, 54, 0.55); border-color: #00B4FF; color: #FFFFFF; }
        """)
        self.btn_reroll.clicked.connect(self.reroll_requested.emit)
        self.bottom_row.addWidget(self.btn_reroll, 0, Qt.AlignRight | Qt.AlignBottom)

        main_layout.addLayout(self.bottom_row)
        self.setFixedHeight(156)

    def show_transmission(self, quote: str):
        pass

    def set_map(self, map_obj: Map | None):
        self._map_obj = map_obj
        self._raw_pixmap = None
        if map_obj is not None:
            if map_obj.name in _PANORAMA_CACHE:
                self._raw_pixmap = _PANORAMA_CACHE[map_obj.name]
            else:
                img_path = map_image_path(map_obj.name, map_obj.mode)
                if img_path and img_path.exists():
                    pix = QPixmap(str(img_path))
                    if not pix.isNull():
                        _PANORAMA_CACHE[map_obj.name] = pix
                        self._raw_pixmap = pix
        self._update_display()
        self.update()

    def get_map(self) -> Map | None:
        return self._map_obj

    def _update_display(self):
        t = theme.tokens()
        font_name = t.font_family

        if self._map_obj is None:
            self.lbl_mode.setVisible(False)
            self.lbl_name.setText("MAPA ALEATORIO")
            self.lbl_name.setStyleSheet(f"""
                QLabel {{
                    font-family: {font_name};
                    font-size: 16px;
                    font-weight: 900;
                    color: #E2E8F0;
                    background: transparent;
                    line-height: 1.15;
                }}
            """)
        else:
            mode = self._map_obj.mode
            mode_color = MODE_COLORS.get(mode, "#6B7280")
            self.lbl_mode.setText(mode.upper())
            self.lbl_mode.setStyleSheet(f"""
                QLabel {{
                    font-size: 10px;
                    font-weight: 900;
                    padding: 2px 8px;
                    border: 1px solid {mode_color};
                    border-radius: 3px;
                    color: {mode_color};
                    background: transparent;
                    background-color: transparent;
                }}
            """)
            self.lbl_mode.setVisible(True)

            m_name = self._map_obj.name.upper()
            f_size = "16px" if len(m_name) > 12 else "18px"
            self.lbl_name.setText(m_name)
            self.lbl_name.setStyleSheet(f"""
                QLabel {{
                    font-family: {font_name};
                    font-size: {f_size};
                    font-weight: 900;
                    color: #FFFFFF;
                    background: transparent;
                    letter-spacing: 0.5px;
                    line-height: 1.15;
                    padding: 2px 0px;
                }}
            """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w = self.width()
        h = self.height()
        radius = 4.0

        clip_path = QPainterPath()
        clip_path.addRoundedRect(0, 0, w, h, radius, radius)
        painter.setClipPath(clip_path)

        if self._raw_pixmap and not self._raw_pixmap.isNull():
            scaled = self._raw_pixmap.scaled(
                w, h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            crop_x = max(0, (scaled.width() - w) // 2)
            crop_y = max(0, (scaled.height() - h) // 2)
            painter.drawPixmap(0, 0, scaled, crop_x, crop_y, w, h)
        else:
            painter.fillRect(0, 0, w, h, QColor("#0E1624"))

        vert_grad = QLinearGradient(0, 0, 0, h)
        vert_grad.setColorAt(0.0, QColor(0, 0, 0, 50))
        vert_grad.setColorAt(0.40, QColor(6, 10, 18, 120))
        vert_grad.setColorAt(1.0, QColor(4, 7, 14, 225))
        painter.fillRect(0, 0, w, h, vert_grad)

        painter.end()
        super().paintEvent(event)
