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
    QStackedWidget,
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
_TEAM1_BORDER = "#00B4FF"
_TEAM2_BORDER = "#FF4444"


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


class _UniformTeamRow(QLayout):
    """Layout that distributes portraits evenly to avoid orphan single items.

    Fits all items in one centered row when possible; otherwise splits the
    count into balanced rows (e.g. 5 -> 3+2, 6 -> 3+3), never leaving a lone
    portrait trailing on its own row.
    """

    def __init__(self, parent: QWidget | None = None, spacing: int = 5, margin: int = 2):
        super().__init__(parent)
        self._items: list = []
        self._spacing = spacing
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

    @staticmethod
    def _balanced_rows(n: int, per_row: int) -> list[int]:
        """Split n items into rows of at most per_row, balanced (no orphans)."""
        if n <= 0:
            return []
        rows_n = (n + per_row - 1) // per_row
        base = n // rows_n
        extra = n % rows_n
        return [base + (1 if i < extra else 0) for i in range(rows_n)]

    def _do_layout(self, rect: QRect, apply_geom: bool = True) -> int:
        m = self.contentsMargins()
        eff = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        n = len(self._items)
        if n == 0:
            return m.top() + m.bottom()

        item_h = next(iter(self._items)).sizeHint().height()
        item_w = next(iter(self._items)).sizeHint().width()
        slot_w = item_w + self._spacing
        per_row = max(1, (eff.width() + self._spacing) // slot_w)

        groups = self._balanced_rows(n, per_row)
        y = eff.y()
        idx = 0
        for g in groups:
            row_total_w = g * item_w + max(0, g - 1) * self._spacing
            start_x = eff.x() + max(0, (eff.width() - row_total_w) // 2)
            cur_x = start_x
            for _ in range(g):
                item = self._items[idx]
                if apply_geom:
                    item.setGeometry(QRect(cur_x, y + (item_h - item.sizeHint().height()) // 2, item_w, item_h))
                cur_x += slot_w
                idx += 1
            y += item_h + self._spacing

        return y - self._spacing - rect.y() + m.bottom()


class BansPanel(QFrame):
    """Section listing currently banned heroes with true centered symmetrical expansion."""

    collapse_changed = Signal(bool)
    randomize_requested = Signal()
    mode_changed = Signal(str)

    MODE_BANS = "bans"
    MODE_DRAFT = "draft"

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._expanded = True
        self._banned_names: list[str] = []
        self._portrait_size = DEFAULT_PORTRAIT
        self._visible_rows = 3
        self._mode = self.MODE_BANS
        self._draft_t1: list[str] = []
        self._draft_t2: list[str] = []
        self._t1_title = "Gatitos"
        self._t2_title = "Perritas"
        self.setObjectName("bansPanel")
        self.setMinimumHeight(74)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Row 1: Dock-style pill tabs [ 🚫 BANEOS ] [ 🎲 DRAFT ]
        tabs_row = QHBoxLayout()
        tabs_row.setContentsMargins(0, 0, 0, 0)
        tabs_row.setSpacing(4)

        self.btn_mode_bans = QPushButton("🚫 BANEOS", self)
        self.btn_mode_draft = QPushButton("🎲 DRAFT", self)
        for btn in (self.btn_mode_bans, self.btn_mode_draft):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setFixedHeight(26)
        self.btn_mode_bans.clicked.connect(lambda: self.set_mode(self.MODE_BANS, emit=True))
        self.btn_mode_draft.clicked.connect(lambda: self.set_mode(self.MODE_DRAFT, emit=True))
        self._apply_mode_switch_style()
        tabs_row.addWidget(self.btn_mode_bans, 1)
        tabs_row.addWidget(self.btn_mode_draft, 1)
        layout.addLayout(tabs_row)

        # Row 2: Sub-header with status label (left) and actions [ 🎲 ] [ 👁️ ] (right)
        sub_header = QHBoxLayout()
        sub_header.setContentsMargins(0, 0, 0, 0)
        sub_header.setSpacing(6)

        self.title_label = QLabel("HÉROES BANEADOS (0)", self)
        self.title_label.setStyleSheet("font-size: 10px; font-weight: 900; color: #FF5555; background: transparent; letter-spacing: 0.5px;")
        sub_header.addWidget(self.title_label, 1)

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
        sub_header.addWidget(self.btn_randomize, 0)

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
        sub_header.addWidget(self.btn_visibility, 0)
        layout.addLayout(sub_header)

        # Stacked body: Page 0 = Bans view, Page 1 = Draft view
        self.stack = QStackedWidget(self)
        self.stack.setObjectName("bansStack")

        # Page 0: Responsive Scroll Area with Centered Flow Layout (Bans)
        self.scroll = SmoothScrollArea(self)
        self.scroll.setObjectName("bansScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.portraits = QWidget(self.scroll)
        self.portraits.setObjectName("bansPortraits")
        self.portraits_layout = CenteredFlowLayout(self.portraits, margin=4, h_spacing=5, v_spacing=5)

        self.scroll.setWidget(self.portraits)
        self.stack.addWidget(self.scroll)

        # Page 1: Draft view — two labeled team sections with uniform row distribution
        self.draft_scroll = SmoothScrollArea(self)
        self.draft_scroll.setObjectName("draftScroll")
        self.draft_scroll.setWidgetResizable(True)
        self.draft_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.draft_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.draft_container = QWidget(self.draft_scroll)
        self.draft_container.setObjectName("draftContainer")
        draft_v = QVBoxLayout(self.draft_container)
        draft_v.setContentsMargins(0, 2, 0, 2)
        draft_v.setSpacing(6)

        self.draft_empty_label = QLabel("Sin draft generado · Pulsa 🎲", self.draft_container)
        self.draft_empty_label.setAlignment(Qt.AlignCenter)
        self.draft_empty_label.setStyleSheet("color: #626673; font-size: 11px; font-weight: 600; padding: 6px 0;")
        draft_v.addWidget(self.draft_empty_label)

        self.label_t1 = QLabel("● GATITOS · 0 HÉROES", self.draft_container)
        self.label_t1.setObjectName("draftTeam1Label")
        self.label_t1.setStyleSheet(
            "font-size: 10px; font-weight: 900; letter-spacing: 0.5px; color: #00B4FF; "
            "background-color: rgba(0, 180, 255, 0.12); border: 1px solid rgba(0, 180, 255, 0.35); "
            "border-radius: 5px; padding: 3px 10px;"
        )
        self.label_t1.setAlignment(Qt.AlignCenter)
        draft_v.addWidget(self.label_t1)

        self.draft_t1_portraits = QWidget(self.draft_container)
        self.draft_t1_portraits.setObjectName("draftTeam1Portraits")
        self.draft_t1_layout = _UniformTeamRow(self.draft_t1_portraits, spacing=5)
        draft_v.addWidget(self.draft_t1_portraits)

        # Thin separator between Team 1 portraits and Team 2 badge
        self.draft_separator = QFrame(self.draft_container)
        self.draft_separator.setObjectName("draftSeparator")
        self.draft_separator.setFixedHeight(1)
        self.draft_separator.setStyleSheet("background-color: #252834; border: none;")
        draft_v.addWidget(self.draft_separator)

        self.label_t2 = QLabel("● PERRITAS · 0 HÉROES", self.draft_container)
        self.label_t2.setObjectName("draftTeam2Label")
        self.label_t2.setStyleSheet(
            "font-size: 10px; font-weight: 900; letter-spacing: 0.5px; color: #FF4444; "
            "background-color: rgba(255, 68, 68, 0.12); border: 1px solid rgba(255, 68, 68, 0.35); "
            "border-radius: 5px; padding: 3px 10px;"
        )
        self.label_t2.setAlignment(Qt.AlignCenter)
        draft_v.addWidget(self.label_t2)

        self.draft_t2_portraits = QWidget(self.draft_container)
        self.draft_t2_portraits.setObjectName("draftTeam2Portraits")
        self.draft_t2_layout = _UniformTeamRow(self.draft_t2_portraits, spacing=5)
        draft_v.addWidget(self.draft_t2_portraits)

        self.draft_scroll.setWidget(self.draft_container)
        self.stack.addWidget(self.draft_scroll)

        layout.addWidget(self.stack, 1)

        self.apply_theme()

    def _apply_mode_switch_style(self):
        bans_active = self._mode == self.MODE_BANS
        self.btn_mode_bans.setChecked(bans_active)
        self.btn_mode_draft.setChecked(not bans_active)

        style_inactive = """
            QPushButton {
                font-size: 10px; font-weight: 800; letter-spacing: 0.5px;
                background-color: #1A1C23; border: 1px solid #2B2E3D;
                border-radius: 6px; color: #8E92A4; padding: 4px 0px;
            }
            QPushButton:hover { background-color: #242731; color: #FFFFFF; }
        """
        style_active_bans = """
            QPushButton {
                font-size: 10px; font-weight: 900; letter-spacing: 0.5px;
                background-color: #2B1619; border: 1px solid #FF4444;
                border-radius: 6px; color: #FFAAAA; padding: 4px 0px;
            }
        """
        style_active_draft = """
            QPushButton {
                font-size: 10px; font-weight: 900; letter-spacing: 0.5px;
                background-color: #122232; border: 1px solid #00B4FF;
                border-radius: 6px; color: #8CD6FF; padding: 4px 0px;
            }
        """
        self.btn_mode_bans.setStyleSheet(style_active_bans if bans_active else style_inactive)
        self.btn_mode_draft.setStyleSheet(style_active_draft if not bans_active else style_inactive)

    def set_mode(self, mode: str, emit: bool = True):
        if mode not in (self.MODE_BANS, self.MODE_DRAFT):
            mode = self.MODE_BANS
        if mode == self._mode and self.stack.currentIndex() == (0 if mode == self.MODE_BANS else 1):
            self._apply_mode_switch_style()
            return
        self._mode = mode
        self.stack.setCurrentIndex(0 if mode == self.MODE_BANS else 1)
        if mode == self.MODE_DRAFT:
            # Persistencia bidireccional: NUNCA se vacían _draft_t1/_draft_t2 aquí.
            # Si están vacíos, recuperarlos de la partida activa antes del label vacío.
            if not (self._draft_t1 or self._draft_t2):
                self._recover_draft_from_match()
            if self._draft_t1 or self._draft_t2:
                self._rebuild_draft()
        self._sync_title()
        self._apply_mode_switch_style()
        self._adjust_panel_height()
        if emit:
            self.mode_changed.emit(self._mode)

    def _recover_draft_from_match(self):
        """Recupera el draft desde la partida activa (window()._current_match) sin vaciar nada."""
        win = self.window()
        match = getattr(win, "_current_match", None) if win is not None else None
        if match is None:
            return
        t1 = list(getattr(match, "team1_draft", None) or [])
        t2 = list(getattr(match, "team2_draft", None) or [])
        if not (t1 or t2):
            return
        self._draft_t1 = t1
        self._draft_t2 = t2
        md = getattr(win, "match_display", None)
        if md is not None:
            self._t1_title = md.team1_widget.get_team_name() or self._t1_title
            self._t2_title = md.team2_widget.get_team_name() or self._t2_title

    def current_mode(self) -> str:
        return self._mode

    def _sync_title(self):
        if self._mode == self.MODE_DRAFT:
            total = len(self._draft_t1) + len(self._draft_t2)
            self.title_label.setText(f"DRAFT DE HÉROES ({total})")
            self.btn_randomize.setToolTip("Sortear un nuevo draft de héroes")
        else:
            self.title_label.setText(f"HÉROES BANEADOS ({len(self._banned_names)})")
            self.btn_randomize.setToolTip("Sortear baneos de héroes aleatoriamente")

    def set_draft(self, team1_names: list[str], team2_names: list[str],
                  team1_title: str = "Gatitos", team2_title: str = "Perritas"):
        self._draft_t1 = list(team1_names)
        self._draft_t2 = list(team2_names)
        self._t1_title = team1_title or "Gatitos"
        self._t2_title = team2_title or "Perritas"
        self._rebuild_draft()
        self._sync_title()
        self._adjust_panel_height()

    def _rebuild_draft(self):
        self._clear_flow(self.draft_t1_layout)
        self._clear_flow(self.draft_t2_layout)

        has_any = bool(self._draft_t1 or self._draft_t2)
        self.draft_empty_label.setVisible(not has_any)

        self.label_t1.setText(f"● {self._t1_title.upper()} · {len(self._draft_t1)} HÉROES")
        self.label_t2.setText(f"● {self._t2_title.upper()} · {len(self._draft_t2)} HÉROES")
        self.label_t1.setVisible(has_any)
        self.draft_t1_portraits.setVisible(has_any)
        self.draft_separator.setVisible(has_any)
        self.label_t2.setVisible(has_any)
        self.draft_t2_portraits.setVisible(has_any)

        if not has_any:
            return

        for name in self._draft_t1:
            self.draft_t1_layout.addWidget(self._portrait_label(
                name, parent=self.draft_t1_portraits,
                border_color=_TEAM1_BORDER, hover_color="#80D8FF"))
        for name in self._draft_t2:
            self.draft_t2_layout.addWidget(self._portrait_label(
                name, parent=self.draft_t2_portraits,
                border_color=_TEAM2_BORDER, hover_color="#FF8585"))

    @staticmethod
    def _clear_flow(flow: CenteredFlowLayout):
        while flow.count():
            item = flow.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

    @property
    def toggle_btn(self):
        return self.btn_visibility

    def portrait_count(self) -> int:
        return len(self._banned_names)

    def portrait_size(self) -> int:
        return self._portrait_size

    def preferred_height(self) -> int:
        if not self._expanded:
            return 74
        return 275 if self._mode == self.MODE_DRAFT else 190

    def min_expanded_height(self) -> int:
        return 110

    def max_expanded_height(self) -> int:
        return 320

    def apply_theme(self):
        self.setStyleSheet("""
            QFrame#bansPanel {
                background-color: #16171D;
                border: 1px solid #282A33;
                border-radius: 8px;
            }
            QScrollArea#bansScroll, QWidget#bansPortraits,
            QScrollArea#draftScroll, QWidget#draftContainer,
            QWidget#draftTeam1Portraits, QWidget#draftTeam2Portraits {
                background-color: transparent;
                border: none;
            }
            QScrollArea#bansScroll QScrollBar:vertical,
            QScrollArea#draftScroll QScrollBar:vertical {
                background: #14151B;
                width: 6px;
                border: none;
                margin: 0px;
            }
            QScrollArea#bansScroll QScrollBar::handle:vertical,
            QScrollArea#draftScroll QScrollBar::handle:vertical {
                background: #2D303D;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollArea#bansScroll QScrollBar::handle:vertical:hover,
            QScrollArea#draftScroll QScrollBar::handle:vertical:hover {
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
        if self._draft_t1 or self._draft_t2:
            self._rebuild_draft()

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

        self._sync_title()
        self._adjust_panel_height()

    def set_visible_rows(self, rows: int):
        self._visible_rows = max(1, min(5, int(rows)))
        self._adjust_panel_height()

    def _calculate_exact_height(self, num_rows: int) -> int:
        item_size = self._portrait_size + 2 * _BORDER
        v_spacing = self.portraits_layout._v_spacing
        margin = self.portraits_layout.contentsMargins().top()
        content_h = num_rows * item_size + max(0, num_rows - 1) * v_spacing + 2 * margin
        # Overhead: 2 header rows (26+24=50) + panel margins (8+8=16) + vertical spacings (6+4=10)
        return content_h + 76

    def _draft_rows_and_height(self) -> tuple[int, int]:
        """Calcula filas balanceadas y altura de contenido de las dos secciones de draft."""
        layout = self.draft_t1_layout
        item_size = self._portrait_size + 2 * _BORDER
        spacing = layout._spacing
        margin = layout.contentsMargins().top()

        vp_w = self.draft_scroll.viewport().width() if self.draft_scroll.viewport() else 0
        if vp_w < 50:
            vp_w = max(100, self.width() - 24)
        slot_w = item_size + spacing
        per_row = max(1, (vp_w + spacing) // slot_w)

        content_h = 0
        total_rows = 0
        for names in (self._draft_t1, self._draft_t2):
            rows = self._balanced_draft_rows(len(names), per_row)
            total_rows += len(rows)
            if rows:
                content_h += len(rows) * item_size + max(0, len(rows) - 1) * spacing + 2 * margin

        # 2 badges (20px) + separator (1px) + section spacing (~22px)
        content_h += 43 if (self._draft_t1 or self._draft_t2) else 0
        return total_rows, content_h

    @staticmethod
    def _balanced_draft_rows(n: int, per_row: int) -> list[int]:
        return _UniformTeamRow._balanced_rows(n, per_row)

    def _adjust_panel_height(self):
        if not self._expanded:
            self.setFixedHeight(74)
            return

        if self._mode == self.MODE_DRAFT:
            if not (self._draft_t1 or self._draft_t2):
                self.setMinimumHeight(105)
                self.setMaximumHeight(105)
                self.draft_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                return

            # Altura óptima: 2 badges + 2 filas de retratos + separador + cabecera 2 niveles
            target_h = 275
            self.setMinimumHeight(target_h)
            self.setMaximumHeight(target_h)
            self.draft_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.draft_container.updateGeometry()
            return

        if not self._banned_names:
            self.setMinimumHeight(105)
            self.setMaximumHeight(105)
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            return

        vp_w = self.scroll.viewport().width() if self.scroll.viewport() else 0
        if vp_w < 50:
            vp_w = max(100, self.width() - 24)

        self.portraits.resize(vp_w, max(40, self.portraits.height()))
        self.portraits_layout.setGeometry(self.portraits.rect())

        item_w = self._portrait_size + 2 * _BORDER + self.portraits_layout._h_spacing
        per_row = max(1, (vp_w + self.portraits_layout._h_spacing) // item_w)
        needed_rows = (len(self._banned_names) + per_row - 1) // per_row

        display_rows = min(needed_rows, self._visible_rows)
        target_h = self._calculate_exact_height(display_rows)

        self.setMinimumHeight(target_h)
        self.setMaximumHeight(target_h)

        if needed_rows > self._visible_rows:
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.portraits.updateGeometry()
        self.portraits.update()

    def showEvent(self, event):
        super().showEvent(event)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._adjust_panel_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._adjust_panel_height()

    def _portrait_label(self, name: str, parent: QWidget | None = None,
                       border_color: str = _BORDER_COLOR, hover_color: str | None = None) -> QLabel:
        label = QLabel(parent if parent is not None else self.portraits)
        total_size = self._portrait_size + 2 * _BORDER
        label.setFixedSize(total_size, total_size)
        if hover_color is not None:
            label.setCursor(Qt.CursorShape.PointingHandCursor)
        hover_rule = (
            f"QLabel:hover {{ border: 1px solid {hover_color}; }}"
            if hover_color is not None else ""
        )
        label.setStyleSheet(f"""
            QLabel {{
                border: 1px solid {border_color};
                border-radius: 6px;
                background-color: #121316;
            }}
            {hover_rule}
        """)

        canonical = resolve_canonical_name(name)
        image = hero_portrait_path(canonical) or hero_portrait_path(name)

        if image:
            pix = QPixmap(str(image))
            label.setPixmap(_get_clipped_pixmap(pix, self._portrait_size, radius=5.0))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            label.setText(name[:2].upper() if name else "?")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hover_rule = (
                f"QLabel:hover {{ border: 1px solid {hover_color}; }}"
                if hover_color is not None else ""
            )
            label.setStyleSheet(f"""
                QLabel {{
                    color: #FFFFFF; font-weight: 800; font-size: 11px;
                    background-color: #222222;
                    border: 1px solid {border_color};
                    border-radius: 6px;
                }}
                {hover_rule}
            """)

        tooltip = f"{name} (Original: {canonical})" if canonical != name else name
        label.setToolTip(tooltip)
        return label

    def _toggle_visibility(self):
        self._expanded = not self._expanded
        self.stack.setVisible(self._expanded)
        # Ocultar también los scrolls directamente para que isHidden() refleje el estado
        self.scroll.setVisible(self._expanded)
        self.draft_scroll.setVisible(self._expanded)
        self.btn_visibility.setText("👁️" if self._expanded else "🙈")

        if not self._expanded:
            self.setFixedHeight(74)
        else:
            self.setMinimumHeight(110)
            self.setMaximumHeight(320)
            self._adjust_panel_height()

        parent_win = self.window()
        if hasattr(parent_win, "settings_manager"):
            parent_win.settings_manager.settings.bans_panel_expanded = self._expanded
            parent_win.settings_manager.save()

        self.collapse_changed.emit(self._expanded)
