"""Banner widget for displaying the active map with magnetic bottom corners and centered magical AI aura."""

from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPixmap, QLinearGradient, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.core.models import Map
from owervach_tmixer.ui.widgets.map_card import MODE_COLORS, map_image_path, get_cached_map_banner
from owervach_tmixer.ui.styles import theme


_PANORAMA_CACHE: dict[str, QPixmap] = {}


class MatchMapBanner(QFrame):
    """Panoramic match banner with magnetic bottom corners and magical centered AI text."""

    reroll_requested = Signal()
    clear_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._map_obj: Map | None = None
        self._raw_pixmap: QPixmap | None = None

        self.setObjectName("matchMapBanner")
        self.setMinimumHeight(130)
        self.setMaximumHeight(340)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._setup_ui()
        self._update_display()

    def _setup_ui(self):
        # 1. Layout Principal (Base Horizontal)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(22, 12, 22, 14)
        main_layout.setSpacing(12)

        # ------------------------------------------------------------------
        # Columna Izquierda: Imantada al borde inferior izquierdo
        # ------------------------------------------------------------------
        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(4)
        left_col.addStretch(1)  # Resorte superior que imanta el contenido abajo

        self.lbl_mode = QLabel(self)
        self.lbl_mode.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.lbl_mode.setStyleSheet("""
            QLabel {
                font-size: 10px;
                font-weight: 800;
                padding: 2px 7px;
                border-radius: 4px;
                color: #FFFFFF;
                background-color: #333333;
            }
        """)
        left_col.addWidget(self.lbl_mode, 0, Qt.AlignLeft)

        self.lbl_name = QLabel(self)
        self.lbl_name.setStyleSheet("""
            QLabel {
                font-size: 26px;
                font-weight: 900;
                color: #FFFFFF;
                background: transparent;
                letter-spacing: 0.5px;
            }
        """)
        name_shadow = QGraphicsDropShadowEffect(self.lbl_name)
        name_shadow.setColor(QColor(0, 0, 0, 220))
        name_shadow.setBlurRadius(10)
        name_shadow.setOffset(1, 2)
        self.lbl_name.setGraphicsEffect(name_shadow)
        left_col.addWidget(self.lbl_name, 0, Qt.AlignLeft)

        self.lbl_subtitle = QLabel(self)
        self.lbl_subtitle.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: 600;
                color: #A0A4B2;
                background: transparent;
            }
        """)
        left_col.addWidget(self.lbl_subtitle, 0, Qt.AlignLeft)

        main_layout.addLayout(left_col, 1)

        # Gran espacio central libre (la IA se posiciona por encima de forma absoluta)
        main_layout.addStretch(1)

        # ------------------------------------------------------------------
        # Columna Derecha: Imantada al borde inferior derecho
        # ------------------------------------------------------------------
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(6)
        right_col.addStretch(1)  # Resorte superior que imanta los botones abajo

        # Botón Quitar (Arriba a la derecha, X roja, outline blanco, 40% transparencia)
        self.btn_clear = QPushButton(self)
        self.btn_clear.setToolTip("Deseleccionar mapa actual")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: rgba(16, 18, 24, 0.40);
                border: 1px solid rgba(255, 255, 255, 0.35);
                border-radius: 6px;
                padding: 4px 10px;
                min-width: 78px;
            }
            QPushButton:hover {
                background-color: rgba(70, 20, 26, 0.65);
                border-color: #FF5555;
            }
            QPushButton:pressed {
                background-color: rgba(40, 15, 18, 0.85);
            }
        """)
        btn_clear_layout = QHBoxLayout(self.btn_clear)
        btn_clear_layout.setContentsMargins(6, 2, 6, 2)
        btn_clear_layout.setSpacing(4)
        btn_clear_layout.setAlignment(Qt.AlignCenter)

        lbl_x = QLabel("✕", self.btn_clear)
        lbl_x.setStyleSheet("color: #FF4444; font-weight: 900; font-size: 12px; background: transparent; border: none;")
        lbl_clear_txt = QLabel("Quitar", self.btn_clear)
        lbl_clear_txt.setStyleSheet("color: #FFFFFF; font-weight: 700; font-size: 11px; background: transparent; border: none;")
        btn_clear_layout.addWidget(lbl_x)
        btn_clear_layout.addWidget(lbl_clear_txt)

        self.btn_clear.clicked.connect(self.clear_requested.emit)
        right_col.addWidget(self.btn_clear, 0, Qt.AlignRight)

        # Botón Mapa Aleatorio (Abajo a la derecha, outline blanco, 40% transparencia)
        self.btn_reroll = QPushButton("🎲  Mapa Aleatorio", self)
        self.btn_reroll.setToolTip("Sortear un mapa aleatorio del pool activo")
        self.btn_reroll.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reroll.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                font-weight: 800;
                padding: 6px 14px;
                color: #FFFFFF;
                background-color: rgba(16, 18, 24, 0.40);
                border: 1px solid rgba(255, 255, 255, 0.35);
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(30, 36, 48, 0.65);
                border-color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: rgba(15, 17, 24, 0.85);
            }
        """)
        self.btn_reroll.clicked.connect(self.reroll_requested.emit)
        right_col.addWidget(self.btn_reroll, 0, Qt.AlignRight)

        main_layout.addLayout(right_col, 0)

        # ------------------------------------------------------------------
        # 2. Aura Mágica de la IA (Completamente Desacoplada, Centro Muerto)
        # ------------------------------------------------------------------
        self.hologram_widget = QWidget(self)
        self.hologram_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hologram_widget.setStyleSheet("background: transparent;")

        holo_layout = QVBoxLayout(self.hologram_widget)
        holo_layout.setContentsMargins(0, 0, 0, 0)
        holo_layout.setSpacing(2)
        holo_layout.setAlignment(Qt.AlignCenter)

        self.lbl_holo_title = QLabel("◈ TRANSMISIÓN DE IA // PROTOCOLO SENTIENT", self.hologram_widget)
        self.lbl_holo_title.setAlignment(Qt.AlignCenter)
        self.lbl_holo_title.setStyleSheet("""
            QLabel {
                color: #61ab02;
                font-size: 9.5px;
                font-weight: 900;
                letter-spacing: 1px;
                background-color: rgba(10, 18, 12, 0.85);
                border-radius: 4px;
                padding: 3px 10px;
                border: none;
            }
        """)
        holo_layout.addWidget(self.lbl_holo_title)

        self.lbl_hologram = QLabel(self.hologram_widget)
        self.lbl_hologram.setAlignment(Qt.AlignCenter)
        self.lbl_hologram.setWordWrap(True)
        self.lbl_hologram.setStyleSheet("""
            QLabel {
                color: #D4FF88;
                font-size: 14px;
                font-weight: 800;
                letter-spacing: 0.2px;
                background-color: rgba(12, 24, 14, 0.82);
                border-radius: 10px;
                padding: 7px 18px;
                border: none;
            }
        """)
        holo_layout.addWidget(self.lbl_hologram)

        # Glow mágico esmeralda difuso
        glow = QGraphicsDropShadowEffect(self.hologram_widget)
        glow.setColor(QColor("#61ab02"))
        glow.setBlurRadius(34)
        glow.setOffset(0, 0)
        self.hologram_widget.setGraphicsEffect(glow)

        self._holo_opacity = QGraphicsOpacityEffect(self.hologram_widget)
        self.hologram_widget.setGraphicsEffect(self._holo_opacity)
        self._holo_opacity.setOpacity(0.0)
        self.hologram_widget.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_hologram()

    def _reposition_hologram(self):
        if hasattr(self, "hologram_widget"):
            # Ancho dinámico pero acotado para no colisionar con esquinas
            max_w = min(580, max(280, self.width() - 360))
            self.hologram_widget.setMaximumWidth(max_w)
            self.hologram_widget.adjustSize()

            # Centro exacto matemático absoluto del banner (cero vibración / cero saltos)
            hw = self.hologram_widget.width()
            hh = self.hologram_widget.height()
            target_x = (self.width() - hw) // 2
            target_y = (self.height() - hh) // 2
            self.hologram_widget.move(target_x, target_y)
            self.hologram_widget.raise_()

    def show_transmission(self, message: str, duration_ms: int = 6000):
        """Displays magical emerald AI aura text (6.0s duration) positioned at exact center."""
        if not hasattr(self, "hologram_widget"):
            return

        clean_msg = message.replace("🤖 [Sistema]:", "").replace("◈", "").strip()
        self.lbl_hologram.setText(clean_msg)
        self._reposition_hologram()
        self.hologram_widget.show()
        self.hologram_widget.raise_()

        anim_in = QPropertyAnimation(self._holo_opacity, b"opacity", self.hologram_widget)
        anim_in.setDuration(220)
        anim_in.setStartValue(self._holo_opacity.opacity())
        anim_in.setEndValue(1.0)
        anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_in.start()

        def _fade_out():
            anim_out = QPropertyAnimation(self._holo_opacity, b"opacity", self.hologram_widget)
            anim_out.setDuration(400)
            anim_out.setStartValue(1.0)
            anim_out.setEndValue(0.0)
            anim_out.setEasingCurve(QEasingCurve.Type.InQuad)
            anim_out.finished.connect(self.hologram_widget.hide)
            anim_out.start()

        QTimer.singleShot(duration_ms, _fade_out)

    def set_map(self, map_obj: Map | None):
        self._map_obj = map_obj
        self._raw_pixmap = None
        if map_obj is not None:
            # Caché Full-HD nativa en memoria RAM (nitidez 1080p absoluta a 0ms)
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
        if self._map_obj is None:
            self.lbl_mode.setVisible(False)
            self.lbl_name.setText("🗺️ Sin mapa asignado")
            self.lbl_name.setStyleSheet("font-size: 18px; font-weight: 800; color: #E0E0E0; background: transparent;")
            self.lbl_subtitle.setText("Sortea un mapa aleatorio o elígelo desde la pestaña 'Mapas'.")
            self.lbl_subtitle.setVisible(True)
        else:
            mode = self._map_obj.mode
            mode_color = MODE_COLORS.get(mode, "#6B7280")
            self.lbl_mode.setText(mode.upper())
            self.lbl_mode.setStyleSheet(f"""
                QLabel {{
                    font-size: 10px;
                    font-weight: 800;
                    padding: 2px 7px;
                    border-radius: 4px;
                    color: {mode_color};
                    background-color: rgba(255, 255, 255, 0.08);
                    border: 1px solid {mode_color};
                }}
            """)
            self.lbl_mode.setVisible(True)
            m_name = self._map_obj.name.upper()
            f_size = "22px" if len(m_name) > 18 else "26px"
            self.lbl_name.setText(m_name)
            self.lbl_name.setStyleSheet(f"""
                QLabel {{
                    font-size: {f_size};
                    font-weight: 900;
                    color: #FFFFFF;
                    background: transparent;
                    letter-spacing: 0.5px;
                }}
            """)
            self.lbl_subtitle.setVisible(False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w = self.width()
        h = self.height()
        radius = 10.0

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
            painter.fillRect(0, 0, w, h, QColor("#14151B"))

        vert_grad = QLinearGradient(0, 0, 0, h)
        vert_grad.setColorAt(0.0, QColor(0, 0, 0, 0))
        vert_grad.setColorAt(0.40, QColor(0, 0, 0, 25))
        vert_grad.setColorAt(0.75, QColor(8, 9, 14, 140))
        vert_grad.setColorAt(1.0, QColor(6, 7, 10, 200))
        painter.fillRect(0, 0, w, h, vert_grad)

        horiz_grad = QLinearGradient(0, 0, w, 0)
        horiz_grad.setColorAt(0.0, QColor(8, 9, 14, 160))
        horiz_grad.setColorAt(0.35, QColor(10, 11, 16, 80))
        horiz_grad.setColorAt(0.70, QColor(12, 13, 18, 20))
        horiz_grad.setColorAt(1.0, QColor(14, 15, 20, 0))
        painter.fillRect(0, 0, w, h, horiz_grad)

        painter.setClipping(False)
        pen_color = QColor(theme.accent()) if self._map_obj else QColor("#282B36")
        pen_width = 1.0
        pen = QPen(pen_color, pen_width)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(pen_width / 2.0, pen_width / 2.0, w - pen_width, h - pen_width, radius, radius)
        painter.end()

        super().paintEvent(event)
