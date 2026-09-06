"""Common helpers and Obsidian card box styles for settings tabs."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
    QGroupBox,
    QLabel,
    QVBoxLayout,
)

from owervach_tmixer.ui.styles import theme


class NoWheelEventFilter(QObject):
    """Prevents accidental value changes when scrolling through settings pages."""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel and isinstance(obj, (QAbstractSpinBox, QComboBox)):
            return True
        return super().eventFilter(obj, event)


def create_card_box(title: str, description: str | None = None) -> QGroupBox:
    """Create an esports-grade Obsidian card container with unified typography and inputs."""
    box = QGroupBox(title)
    accent = theme.accent()
    accent_subtle = theme.accent_rgba(0.08)

    box.setStyleSheet(f"""
        QGroupBox {{
            font-size: 12px;
            font-weight: 800;
            color: {accent};
            background-color: #15171F;
            border: 1px solid #262936;
            border-radius: 8px;
            margin-top: 14px;
            padding: 16px 14px 14px 14px;
        }}
        QGroupBox:hover {{
            border-color: #313545;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 1px 8px;
            background-color: #121316;
            border-radius: 4px;
        }}
        QLabel {{
            color: #E2E6F0;
        }}
        QLineEdit, QSpinBox, QComboBox {{
            background-color: #191B24;
            border: 1px solid #2B2E3D;
            border-radius: 6px;
            padding: 6px 10px;
            color: #FFFFFF;
            font-weight: 600;
            font-size: 12px;
        }}
        QLineEdit:hover, QSpinBox:hover, QComboBox:hover {{
            border-color: #3C4257;
            background-color: #1C1F2B;
        }}
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
            border-color: {accent};
            background-color: #1D202D;
        }}
        QCheckBox {{
            color: #E6EAF2;
            font-size: 12px;
            font-weight: 600;
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 17px;
            height: 17px;
            border: 1.5px solid #363B48;
            border-radius: 4px;
            background-color: #17181F;
        }}
        QCheckBox::indicator:hover {{
            border-color: {accent};
        }}
        QCheckBox::indicator:checked {{
            background-color: {accent};
            border-color: {accent};
        }}
    """)

    if description:
        lbl_sub = QLabel(description, box)
        lbl_sub.setStyleSheet("color: #8C92A4; font-size: 11px; font-weight: 500; margin-bottom: 6px;")
        lbl_sub.setWordWrap(True)
        layout = box.layout()
        if layout and isinstance(layout, QVBoxLayout):
            layout.addWidget(lbl_sub)

    return box
