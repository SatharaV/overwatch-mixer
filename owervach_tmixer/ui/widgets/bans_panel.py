"""Banned-hero section of the side column with true geometrically centered symmetric rows."""

from __future__ import annotations
from .smooth_scroll import SmoothScrollArea

from typing import List, Optional

from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, QRect, QSize, Qt, Signal
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.ui.styles import theme
from .hero_widget import hero_portrait_path, resolve_canonical_name

DEFAULT_PORTRAIT = 44
MIN_PORTRAIT = 16
MAX_PORTRAIT = 64

_BORDER = 1
_BORDER_COLOR = "#FF4444"


def _get_clipped_pixmap(pix: QPixmap, size: int, radius: float = 6.0) -> QPixmap:
    if pix.isNull():
        return pix
    scaled = pix.scaled(
        size, size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    crop_x = max(0, (scaled.width() - size) // 2)
    crop_y = max(0, (scaled.height() - size) // 2)
    cropped = scaled.copy(crop_x, crop_y, size, size)

    out = QPixmap(size, size)
    out.fill(Qt.transparent)
    painter = QPainter(out)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    path = QPainterPath()
    path.addRoundedRect(0, 0, size, size, radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, cropped)
    painter.end()
    return out


class CenteredFlowLayout(QLayout):
    """Flow layout that dynamically centers every row of items horizontally."""

    def __init__(self, parent: QWidget | None = None, margin: int = 2, h_spacing: int = 5, v_spacing: int = 5):
        super().__init__(parent)
        self._items = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item):
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), apply_geom=False)

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self._do_layout(rect, apply_geom=True)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect: QRect, apply_geom: bool = True) -> int:
        m = self.contentsMargins()
        eff = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x = eff.x()
        y = eff.y()
        line_height = 0
        lines = []
        current_line = []

        for item in self._items:
            item_w = item.sizeHint().width()
            item_h = item.sizeHint().height()
            next_x = x + item_w + self._h_spacing

            if next_x - self._h_spacing > eff.right() and current_line:
                lines.append((current_line, line_height, y))
                x = eff.x()
                y = y + line_height + self._v_spacing
                next_x = x + item_w + self._h_spacing
                line_height = 0
                current_line = []

            current_line.append((item, item_w, item_h))
            x = next_x
            line_height = max(line_height, item_h)

        if current_line:
            lines.append((current_line, line_height, y))

        if apply_geom:
            for line, l_height, l_y in lines:
                total_w = sum(w for _, w, _ in line) + max(0, len(line) - 1) * self._h_spacing
                start_x = eff.x() + max(0, (eff.width() - total_w) // 2)
                cur_x = start_x
                for item, w, h in line:
                    item.setGeometry(QRect(cur_x, l_y + (l_height - h) // 2, w, h))
                    cur_x += w + self._h_spacing

        if lines:
            last_line, last_h, last_y = lines[-1]
            return last_y + last_h - rect.y() + m.bottom()
        return m.top() + m.bottom()


class BansPanel(QFrame):
    """Section listing currently banned heroes with true centered symmetrical expansion."""

    collapse_changed = Signal(bool)
    randomize_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._expanded = True
        self._banned_names: list[str] = []
        self._portrait_size = DEFAULT_PORTRAIT
        self._visible_rows = 2
        self.setObjectName("bansPanel")
        self.setMinimumHeight(44)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Header Bar
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        self.title_label = QLabel("⛔ HÉROES BANEADOS (0)", self)
        self.title_label.setStyleSheet("font-size: 11px; font-weight: 900; color: #FF5555; background: transparent;")
        header.addWidget(self.title_label, 1)

        self.btn_randomize = QPushButton("🎲", self)
        self.btn_randomize.setFixedSize(24, 22)
        self.btn_randomize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_randomize.setToolTip("Sortear baneos de héroes aleatoriamente")
        self.btn_randomize.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                background-color: #26191D;
                border: 1px solid #5A2228;
                border-radius: 4px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #4A1E24;
                border-color: #FF5555;
            }
        """)
        self.btn_randomize.clicked.connect(self.randomize_requested.emit)
        header.addWidget(self.btn_randomize, 0)

        self.btn_visibility = QPushButton("👁️", self)
        self.btn_visibility.setFixedSize(24, 22)
        self.btn_visibility.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_visibility.setToolTip("Ocultar / Mostrar sección de baneos")
        self.btn_visibility.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                background-color: #1F222B;
                border: 1px solid #323746;
                border-radius: 4px;
                color: #A0A5B2;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #2E3445;
                color: #FFFFFF;
                border-color: #61ab02;
            }
        """)
        self.btn_visibility.clicked.connect(self._toggle_visibility)
        header.addWidget(self.btn_visibility, 0)

        layout.addLayout(header)

        # Responsive Scroll Area with Centered Flow Layout
        self.scroll = SmoothScrollArea(self)
        self.scroll.setObjectName("bansScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.portraits = QWidget(self.scroll)
        self.portraits.setObjectName("bansPortraits")
        self.portraits_layout = CenteredFlowLayout(self.portraits, margin=2, h_spacing=5, v_spacing=5)

        self.scroll.setWidget(self.portraits)
        layout.addWidget(self.scroll, 1)

        self.apply_theme()

    @property
    def toggle_btn(self):
        return self.btn_visibility

    def portrait_count(self) -> int:
        return len(self._banned_names)

    def portrait_size(self) -> int:
        return self._portrait_size

    def preferred_height(self) -> int:
        return 150 if self._expanded else 44

    def min_expanded_height(self) -> int:
        return 85

    def max_expanded_height(self) -> int:
        return 220

    def apply_theme(self):
        self.setStyleSheet("""
            QFrame#bansPanel {
                background-color: #16171D;
                border: 1px solid #282A33;
                border-radius: 8px;
            }
            QScrollArea#bansScroll, QWidget#bansPortraits {
                background-color: transparent;
                border: none;
            }
            QScrollArea#bansScroll QScrollBar:vertical {
                background: #14151B;
                width: 6px;
                border: none;
                margin: 0px;
            }
            QScrollArea#bansScroll QScrollBar::handle:vertical {
                background: #2D303D;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollArea#bansScroll QScrollBar::handle:vertical:hover {
                background: #FF4444;
            }
        """)

    def set_expanded(self, expanded: bool):
        if self._expanded != expanded:
            self._toggle_visibility()

    def set_banned(self, banned: list[str] | set[str]):
        self._banned_names = list(banned)
        self._rebuild()

    def set_portrait_size(self, size: int):
        size = min(MAX_PORTRAIT, max(MIN_PORTRAIT, int(size)))
        if size == self._portrait_size:
            return
        self._portrait_size = size
        self._rebuild()

    def _rebuild(self):
        while self.portraits_layout.count():
            item = self.portraits_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

        if not self._banned_names:
            empty_lbl = QLabel("Sin héroes baneados", self.portraits)
            empty_lbl.setAlignment(Qt.AlignCenter)
            empty_lbl.setStyleSheet("color: #626673; font-size: 11px; font-weight: 600; padding: 6px 0;")
            self.portraits_layout.addWidget(empty_lbl)
        else:
            for name in self._banned_names:
                self.portraits_layout.addWidget(self._portrait_label(name))

        self.title_label.setText(f"⛔ HÉROES BANEADOS ({len(self._banned_names)})")
        self._adjust_panel_height()

    def set_visible_rows(self, rows: int):
        self._visible_rows = max(1, min(5, int(rows)))
        self._adjust_panel_height()

    def _calculate_exact_height(self, num_rows: int) -> int:
        item_size = self._portrait_size + 2 * _BORDER
        v_spacing = self.portraits_layout._v_spacing
        margin = self.portraits_layout.contentsMargins().top()
        content_h = num_rows * item_size + max(0, num_rows - 1) * v_spacing + 2 * margin
        # Overhead: 16 (panel margins) + 22 (header) + 6 (spacing) + 4 (padding) = 48px
        return content_h + 48

    def _adjust_panel_height(self):
        if not self._expanded:
            self.setFixedHeight(44)
            return

        if not self._banned_names:
            self.setMinimumHeight(70)
            self.setMaximumHeight(70)
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            return

        # Calcular cuántos retratos caben por fila según el ancho disponible
        w = max(100, self.portraits.width() if self.portraits.width() > 50 else self.width() - 24)
        item_w = self._portrait_size + 2 * _BORDER + self.portraits_layout._h_spacing
        per_row = max(1, (w + self.portraits_layout._h_spacing) // item_w)
        needed_rows = (len(self._banned_names) + per_row - 1) // per_row

        display_rows = min(needed_rows, self._visible_rows)
        target_h = self._calculate_exact_height(display_rows)

        self.setMinimumHeight(target_h)
        self.setMaximumHeight(target_h)

        if needed_rows > self._visible_rows:
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._adjust_panel_height()

    def _portrait_label(self, name: str) -> QLabel:
        label = QLabel(self.portraits)
        total_size = self._portrait_size + 2 * _BORDER
        label.setFixedSize(total_size, total_size)
        label.setStyleSheet(f"""
            QLabel {{
                border: 1px solid {_BORDER_COLOR};
                border-radius: 6px;
                background-color: #121316;
            }}
        """)

        canonical = resolve_canonical_name(name)
        image = hero_portrait_path(name)

        if image:
            pix = QPixmap(str(image))
            label.setPixmap(_get_clipped_pixmap(pix, self._portrait_size, radius=5.0))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            label.setText(name[:2].upper() if name else "?")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"""
                QLabel {{
                    color: #FFFFFF; font-weight: 800; font-size: 11px;
                    background-color: #222222;
                    border: 1px solid {_BORDER_COLOR};
                    border-radius: 6px;
                }}
            """)

        tooltip = f"{name} (Original: {canonical})" if canonical != name else name
        label.setToolTip(tooltip)
        return label

    def _toggle_visibility(self):
        self._expanded = not self._expanded
        self.scroll.setVisible(self._expanded)
        self.btn_visibility.setText("👁️" if self._expanded else "🙈")

        if not self._expanded:
            self.setFixedHeight(44)
        else:
            self.setMinimumHeight(85)
            self.setMaximumHeight(220)
            self._adjust_panel_height()

        parent_win = self.window()
        if hasattr(parent_win, "settings_manager"):
            parent_win.settings_manager.settings.bans_panel_expanded = self._expanded
            parent_win.settings_manager.save()

        self.collapse_changed.emit(self._expanded)
