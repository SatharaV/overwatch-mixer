"""Global Obsidian Esports Stylesheet with dynamic theme replacement tokens and modal dialog styling."""

from owervach_tmixer.utils import get_resource_path

_ASSETS = get_resource_path("assets")

STYLESHEET_TEMPLATE = """
/* Global Obsidian Stylesheet */

QWidget {
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    color: #F0F0F0;
}

QMainWindow {
    background-color: #121316;
}

QFrame {
    background-color: transparent;
    border: none;
}

/* Splitter handles */
QSplitter::handle {
    background-color: #20232E;
}
QSplitter::handle:hover {
    background-color: @ACCENT@;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #14151B;
    width: 8px;
    border: none;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #2D303D;
    min-height: 24px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: @ACCENT@;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

/* Buttons */
QPushButton {
    background-color: #1E2028;
    border: 1px solid #2B2F3D;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 700;
    color: #FFFFFF;
    min-height: 18px;
}
QPushButton:hover {
    background-color: #282C38;
    border-color: #3E4558;
}
QPushButton:pressed {
    background-color: #15171E;
}
QPushButton:disabled {
    background-color: #16171D;
    color: #555966;
    border-color: #232630;
}

QPushButton[primary="true"] {
    background-color: @ACCENT@;
    border-color: @ACCENT_LIGHT@;
    color: #FFFFFF;
}
QPushButton[primary="true"]:hover {
    background-color: @ACCENT_LIGHTER@;
}

QPushButton[danger="true"] {
    background-color: #2D1418;
    border-color: #6E222B;
    color: #FF7788;
}
QPushButton[danger="true"]:hover {
    background-color: #4A1920;
    border-color: #FF4444;
    color: #FFFFFF;
}

/* Global QMenu (Dark Obsidian Look - Opaque on Wayland/Hyprland) */
QMenu {
    background-color: #16171E !important;
    background: #16171E !important;
    border: 1px solid #282B36;
    border-radius: 6px;
    padding: 5px 0px;
    color: #E2E6F0;
    font-size: 12px;
    font-weight: 600;
}
QMenu::item {
    padding: 6px 20px 6px 12px;
    border-radius: 4px;
    margin: 1px 5px;
}
QMenu::item:selected {
    background-color: @ACCENT_RGBA_18@;
    color: @ACCENT@;
}
QMenu::separator {
    height: 1px;
    background-color: #242734;
    margin: 4px 8px;
}

/* Global QComboBox (Obsidian AAA) */
QComboBox {
    background-color: #17181F;
    border: 1px solid #282A33;
    border-radius: 6px;
    padding: 6px 12px;
    color: #FFFFFF;
    font-weight: 600;
}
QComboBox:hover {
    border-color: #3E4352;
}
QComboBox:focus {
    border-color: @ACCENT@;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: none;
}
QComboBox::down-arrow {
    image: url(assets/chevron_down.svg);
    width: 11px;
    height: 11px;
}

/* Dropdown Container & Popup View (Solid Opaque Obsidian) */
QComboBoxPrivateContainer,
QComboBoxPrivateContainer QFrame,
QComboBoxPrivateContainer QWidget {
    background-color: #16171E !important;
    background: #16171E !important;
    border: 1px solid #282B36;
    border-radius: 6px;
    padding: 0px;
    margin: 0px;
}

QComboBox QAbstractItemView,
QComboBox QAbstractItemView::viewport,
QComboBox QListView,
QComboBox QListView::viewport,
QListView,
QListView::viewport {
    background-color: #16171E !important;
    background: #16171E !important;
    border: 1px solid #282B36;
    border-radius: 6px;
    color: #FFFFFF;
    selection-background-color: @ACCENT_RGBA_22@;
    selection-color: @ACCENT@;
    padding: 4px;
    outline: 0px;
}
QComboBox QAbstractItemView::item,
QComboBox QListView::item,
QListView::item {
    padding: 6px 10px;
    border-radius: 4px;
    color: #E2E6F0;
    min-height: 20px;
}
QComboBox QAbstractItemView::item:selected,
QComboBox QAbstractItemView::item:hover,
QComboBox QListView::item:selected,
QComboBox QListView::item:hover,
QListView::item:selected,
QListView::item:hover {
    background-color: @ACCENT_RGBA_22@;
    color: @ACCENT@;
}

/* Line Edit */
QLineEdit {
    background-color: #17181F;
    border: 1px solid #282A33;
    border-radius: 6px;
    padding: 6px 10px;
    color: #FFFFFF;
    selection-background-color: @ACCENT@;
}
QLineEdit:focus {
    border-color: @ACCENT@;
}

/* Spin Box */
QSpinBox {
    background-color: #17181F;
    border: 1px solid #282A33;
    border-radius: 6px;
    padding: 6px 10px;
    color: #FFFFFF;
}
QSpinBox:focus {
    border-color: @ACCENT@;
}

/* Check Box */
QCheckBox {
    spacing: 8px;
    color: #FFFFFF;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1.5px solid #363B48;
    border-radius: 4px;
    background-color: #17181F;
}
QCheckBox::indicator:checked {
    background-color: @ACCENT@;
    border-color: @ACCENT@;
    image: url(assets/check.svg);
}

/* Global Dialog & MessageBox Dark Theme */
QDialog {
    background-color: #121316;
}

QMessageBox {
    background-color: #15171F;
    border: 1px solid #2B2F3D;
    border-radius: 8px;
}
QMessageBox QLabel {
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 600;
    padding: 8px;
    background: transparent;
}
QMessageBox QPushButton {
    font-size: 12px;
    font-weight: 700;
    color: #FFFFFF;
    background-color: #1E222B;
    border: 1px solid #343A4A;
    border-radius: 6px;
    padding: 6px 16px;
    min-width: 75px;
}
QMessageBox QPushButton:hover {
    background-color: #2B3242;
    border-color: @ACCENT@;
    color: #FFFFFF;
}
QMessageBox QPushButton:pressed {
    background-color: #14171E;
}
"""

STYLESHEET_TEMPLATE = STYLESHEET_TEMPLATE.replace(
    "url(assets/check.svg)", f"url({(_ASSETS / 'check.svg').as_posix()})"
).replace(
    "url(assets/chevron_down.svg)", f"url({(_ASSETS / 'chevron_down.svg').as_posix()})"
)
