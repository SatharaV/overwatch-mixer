"""Common helpers and card box styles for settings tabs."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QAbstractSpinBox, QComboBox, QGroupBox

from owervach_tmixer.ui.styles import theme


class NoWheelEventFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel and isinstance(obj, (QAbstractSpinBox, QComboBox)):
            return True
        return super().eventFilter(obj, event)


def create_card_box(title: str) -> QGroupBox:
    box = QGroupBox(title)
    accent = theme.accent()
    box.setStyleSheet(f"""
        QGroupBox {{
            font-size: 12px; font-weight: 800; color: {accent};
            background-color: #17181D; border: 1px solid #282A33;
            border-radius: 8px; margin-top: 14px; padding: 16px 14px 14px 14px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin; subcontrol-position: top left;
            padding: 0 8px; background-color: #121316;
        }}
        QLineEdit, QSpinBox, QComboBox {{
            background-color: #1A1C24; border: 1px solid #2F3342;
            border-radius: 6px; padding: 6px 10px; color: #FFFFFF; font-weight: 600;
        }}
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border-color: {accent}; }}
    """)
    return box
