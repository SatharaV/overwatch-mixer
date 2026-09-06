"""Abstract Base Theme Strategy implementing token-driven QSS rendering."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import replace
from pathlib import Path
from owervach_tmixer.utils import get_resource_path
from owervach_tmixer.ui.styles.tokens import ThemeTokens


class BaseTheme(ABC):
    """Abstract base class for all application themes."""

    def __init__(self, accent_override: str | None = None):
        self._accent_override = accent_override.lower() if accent_override else None

    @property
    @abstractmethod
    def default_tokens(self) -> ThemeTokens:
        ...

    @property
    def tokens(self) -> ThemeTokens:
        base = self.default_tokens
        acc = (self._accent_override or base.accent).lower()
        if not self._accent_override and base.accent == acc:
            return base

        return replace(base, accent=acc, bg_active_pill=base.accent_rgba(0.18))

    def set_accent_override(self, hex_color: str | None):
        self._accent_override = hex_color.lower() if hex_color else None

    def build_stylesheet(self) -> str:
        t = self.tokens
        assets = get_resource_path("assets")
        check_path = (assets / "check.svg").as_posix()
        chevron_path = (assets / "chevron_down.svg").as_posix()

        r = t.border_radius
        r_sm = max(2, r - 2)

        return f"""
        QWidget {{
            font-family: {t.font_family};
            font-size: 13px;
            color: {t.text_primary};
        }}

        QMainWindow, QDialog {{
            background-color: {t.bg_app};
        }}

        QFrame {{
            background-color: transparent;
            border: none;
        }}

        QSplitter::handle {{
            background-color: {t.border_subtle};
        }}
        QSplitter::handle:hover {{
            background-color: {t.accent};
        }}

        QScrollBar:vertical {{
            background: {t.bg_subtle};
            width: 8px;
            border: none;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {t.border_medium};
            min-height: 24px;
            border-radius: {r_sm}px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {t.accent};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            height: 0px;
            border: none;
            background: transparent;
        }}

        QPushButton {{
            background-color: {t.bg_elevated};
            border: 1px solid {t.border_subtle};
            border-radius: {r}px;
            padding: 6px 14px;
            font-weight: 700;
            color: {t.text_primary};
            min-height: 18px;
        }}
        QPushButton:hover {{
            background-color: {t.border_medium};
            border-color: {t.accent};
        }}
        QPushButton:pressed {{
            background-color: {t.bg_surface};
        }}
        QPushButton:disabled {{
            background-color: {t.bg_subtle};
            color: {t.text_muted};
            border-color: {t.border_subtle};
        }}

        QPushButton[primary="true"] {{
            background-color: {t.accent};
            border: 1px solid {t.accent_light()};
            color: #FFFFFF;
            font-weight: 800;
        }}
        QPushButton[primary="true"]:hover {{
            background-color: {t.accent_lighter()};
            border-color: #FFFFFF;
        }}

        QPushButton[danger="true"] {{
            background-color: #2D1418;
            border: 1px solid #6E222B;
            color: #FF7788;
        }}
        QPushButton[danger="true"]:hover {{
            background-color: #4A1920;
            border-color: {t.danger};
            color: #FFFFFF;
        }}

        QMenu {{
            background-color: {t.bg_surface} !important;
            background: {t.bg_surface} !important;
            border: 1px solid {t.border_medium};
            border-radius: {r}px;
            padding: 5px 0px;
            color: {t.text_primary};
            font-size: 12px;
            font-weight: 600;
        }}
        QMenu::item {{
            padding: 6px 20px 6px 12px;
            border-radius: {r_sm}px;
            margin: 1px 5px;
        }}
        QMenu::item:selected {{
            background-color: {t.accent_rgba(0.18)};
            color: {t.accent};
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {t.border_subtle};
            margin: 4px 8px;
        }}

        QComboBox, QLineEdit, QSpinBox {{
            background-color: {t.bg_elevated};
            border: 1px solid {t.border_subtle};
            border-radius: {r}px;
            padding: 6px 10px;
            color: {t.text_primary};
            font-weight: 600;
        }}
        QComboBox:hover, QLineEdit:hover, QSpinBox:hover {{
            border-color: {t.border_medium};
        }}
        QComboBox:focus, QLineEdit:focus, QSpinBox:focus {{
            border-color: {t.accent};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 24px;
            border-left: none;
        }}
        QComboBox::down-arrow {{
            image: url({chevron_path});
            width: 11px;
            height: 11px;
        }}

        QComboBox QAbstractItemView, QListView, QListView::viewport {{
            background-color: {t.bg_surface} !important;
            background: {t.bg_surface} !important;
            border: 1px solid {t.border_medium};
            border-radius: {r}px;
            color: {t.text_primary};
            selection-background-color: {t.accent_rgba(0.22)};
            selection-color: {t.accent};
            padding: 4px;
            outline: 0px;
        }}
        QListView::item {{
            padding: 6px 10px;
            border-radius: {r_sm}px;
            color: {t.text_primary};
            min-height: 20px;
        }}
        QListView::item:selected, QListView::item:hover {{
            background-color: {t.accent_rgba(0.20)};
            color: {t.accent};
        }}

        QCheckBox {{
            spacing: 8px;
            color: {t.text_primary};
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1.5px solid {t.border_medium};
            border-radius: {r_sm}px;
            background-color: {t.bg_elevated};
        }}
        QCheckBox::indicator:hover {{
            border-color: {t.accent};
        }}
        QCheckBox::indicator:checked {{
            background-color: {t.accent};
            border-color: {t.accent};
            image: url({check_path});
        }}

        QMessageBox {{
            background-color: {t.bg_surface};
            border: 1px solid {t.border_medium};
            border-radius: {r}px;
        }}
        QMessageBox QLabel {{
            color: {t.text_primary};
            font-size: 13px;
            font-weight: 600;
            padding: 8px;
            background: transparent;
        }}
        QMessageBox QPushButton {{
            background-color: {t.bg_elevated};
            border: 1px solid {t.border_subtle};
            border-radius: {r_sm}px;
            padding: 6px 16px;
            min-width: 75px;
        }}
        QMessageBox QPushButton:hover {{
            border-color: {t.accent};
        }}
        """
