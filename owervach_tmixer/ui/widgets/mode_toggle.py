"""Segmented square outline toggle switch with calibrated 30px height and responsive theme sync."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QWidget

from owervach_tmixer.core.models import GameMode
from owervach_tmixer.ui.styles import theme


class ModeSwitch(QFrame):
    """Segmented square outline switch with calibrated 30px height matching neighboring header pills."""

    mode_changed = Signal(object)

    def __init__(self, mode: GameMode = GameMode.FIVE_V_FIVE, parent: QWidget | None = None):
        super().__init__(parent)
        self._mode = mode
        self.setObjectName("modeSwitch")
        self.setFixedHeight(30)
        self.setToolTip("Modo de partida (5 vs 5 = 10 jugadores, 6 vs 6 = 12 jugadores)")

        self.setStyleSheet("""
            QFrame#modeSwitch {
                background-color: #15171F;
                border: 1px solid #282C3B;
                border-radius: 6px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        self.btn_5 = QPushButton("5 vs 5", self)
        self.btn_5.setCheckable(True)
        self.btn_5.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_5.setFixedHeight(24)
        self.btn_5.clicked.connect(lambda: self.set_mode(GameMode.FIVE_V_FIVE))
        layout.addWidget(self.btn_5)

        self.btn_6 = QPushButton("6 vs 6", self)
        self.btn_6.setCheckable(True)
        self.btn_6.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_6.setFixedHeight(24)
        self.btn_6.clicked.connect(lambda: self.set_mode(GameMode.SIX_V_SIX))
        layout.addWidget(self.btn_6)

        # Compatibility aliases for tests
        self.label_5 = self.btn_5
        self.label_6 = self.btn_6
        self._knob = self.btn_6

        self.set_mode(mode)
        self.apply_theme()

    def mode(self) -> GameMode:
        return self._mode

    def set_mode(self, mode: GameMode):
        changed = (self._mode != mode)
        self._mode = mode
        self._update_styles()
        if changed:
            self.mode_changed.emit(self._mode)

    def _update_styles(self):
        accent = theme.accent()
        is_6v6 = (self._mode == GameMode.SIX_V_SIX)

        self.btn_5.blockSignals(True)
        self.btn_6.blockSignals(True)
        self.btn_5.setChecked(not is_6v6)
        self.btn_6.setChecked(is_6v6)
        self.btn_5.blockSignals(False)
        self.btn_6.blockSignals(False)

        active_style = f"""
            QPushButton {{
                background-color: {theme.accent_rgba(0.16)};
                border: 1px solid {accent};
                border-radius: 4px;
                color: {accent};
                font-size: 11px;
                font-weight: 800;
                padding: 2px 12px;
            }}
        """
        inactive_style = """
            QPushButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                color: #8C92A4;
                font-size: 11px;
                font-weight: 700;
                padding: 2px 12px;
            }
            QPushButton:hover {
                background-color: #202430;
                color: #FFFFFF;
            }
        """

        self.btn_5.setStyleSheet(active_style if not is_6v6 else inactive_style)
        self.btn_6.setStyleSheet(active_style if is_6v6 else inactive_style)

    def apply_theme(self):
        self._update_styles()
