"""Row widget, vector control buttons, and drop zones for Tier Maker."""

from __future__ import annotations

import json
from typing import List, Optional

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPolygon
from PySide6.QtWidgets import (
    QColorDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.ui.styles import theme
from owervach_tmixer.ui.widgets.flow_layout import FlowLayout
from .tier_card import MIME_TIER_ITEM, TierItemCard


class TierControlBtn(QPushButton):
    def __init__(self, action_type: str, tooltip: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.action_type = action_type
        self.setFixedSize(32, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tooltip)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        is_hovered = self.underMouse()
        is_pressed = self.isDown()
        accent_col = theme.accent_color()

        if self.action_type in ("up", "down"):
            bg_col = QColor("#2D3342") if is_hovered else QColor("#1C1E26")
            border_col = accent_col if is_hovered else QColor("#383E50")
            icon_col = QColor("#FFFFFF") if is_hovered else accent_col
        elif self.action_type == "clear":
            bg_col = QColor("#3D301C") if is_hovered else QColor("#241D14")
            border_col = QColor("#FFAA00") if is_hovered else QColor("#5A4018")
            icon_col = QColor("#FFFFFF") if is_hovered else QColor("#FFAA00")
        else:
            bg_col = QColor("#461922") if is_hovered else QColor("#281318")
            border_col = QColor("#FF4444") if is_hovered else QColor("#62202A")
            icon_col = QColor("#FFFFFF") if is_hovered else QColor("#FF5566")

        if is_pressed:
            bg_col = bg_col.darker(130)

        painter.setPen(QPen(border_col, 1))
        painter.setBrush(QBrush(bg_col))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 4, 4)

        cx = self.width() // 2
        cy = self.height() // 2

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(icon_col))

        if self.action_type == "up":
            poly = QPolygon([QPoint(cx, cy - 4), QPoint(cx - 4, cy + 3), QPoint(cx + 4, cy + 3)])
            painter.drawPolygon(poly)
        elif self.action_type == "down":
            poly = QPolygon([QPoint(cx, cy + 4), QPoint(cx - 4, cy - 3), QPoint(cx + 4, cy - 3)])
            painter.drawPolygon(poly)
        elif self.action_type == "clear":
            painter.setPen(QPen(icon_col, 1.6, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            painter.drawArc(cx - 5, cy - 5, 10, 10, 45 * 16, 270 * 16)
            painter.setBrush(QBrush(icon_col))
            painter.setPen(Qt.NoPen)
            arrow = QPolygon([QPoint(cx + 3, cy - 5), QPoint(cx + 3, cy), QPoint(cx + 7, cy - 2)])
            painter.drawPolygon(arrow)
        elif self.action_type == "del":
            painter.setPen(QPen(icon_col, 2.0, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(cx - 4, cy - 4, cx + 4, cy + 4)
            painter.drawLine(cx + 4, cy - 4, cx - 4, cy + 4)

        painter.end()

class TierDropZone(QFrame):
    item_dropped = Signal(dict, QPoint)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setStyleSheet("background-color: transparent; border: none;")
        self.flow_layout = FlowLayout(self, margin=6, h_spacing=6, v_spacing=6)

    def find_insert_index(self, pos: QPoint) -> int:
        """Calculates exact geometric insertion index from cursor position."""
        owner = self.parent()
        cards = getattr(owner, "cards", [])
        if not cards:
            return 0

        for i, card in enumerate(cards):
            r = card.geometry()
            if r.top() - 10 <= pos.y() <= r.bottom() + 10:
                if pos.x() < r.center().x():
                    return i
            elif pos.y() < r.top() - 10:
                return i
        return len(cards)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(MIME_TIER_ITEM):
            event.acceptProposedAction()
            self.setStyleSheet(
                f"background-color: rgba(24, 28, 38, 0.35); border: 1px dashed {theme.accent()};"
            )

    def dragLeaveEvent(self, event):
        self.setStyleSheet("background-color: transparent; border: none;")

    def dropEvent(self, event):
        self.setStyleSheet("background-color: transparent; border: none;")
        if event.mimeData().hasFormat(MIME_TIER_ITEM):
            data = json.loads(
                event.mimeData().data(MIME_TIER_ITEM).data().decode("utf-8")
            )
            self.item_dropped.emit(data, event.pos())
            event.acceptProposedAction()


class TierRowWidget(QFrame):
    move_up_requested = Signal(object)
    move_down_requested = Signal(object)
    delete_requested = Signal(object)
    clear_requested = Signal(object)
    item_placed = Signal(object, dict, QPoint)
    item_swapped_with_card = Signal(object, object, dict)

    def __init__(
        self,
        name: str,
        color_hex: str,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.tier_name = name
        self.color_hex = color_hex
        self.cards: List[TierItemCard] = []

        self.setMinimumHeight(96)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setStyleSheet("""
            TierRowWidget {
                background-color: transparent;
                border-bottom: 2px solid #0B0C10;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.btn_label = QPushButton(self.tier_name, self)
        self.btn_label.setFixedWidth(88)
        self.btn_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.btn_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_label.setToolTip("Doble clic para renombrar o cambiar color")
        self._update_label_style()
        self.btn_label.clicked.connect(self._edit_tier_properties)
        layout.addWidget(self.btn_label)

        self.drop_zone = TierDropZone(self)
        self.drop_zone.item_dropped.connect(
            lambda data, pos: self.item_placed.emit(self, data, pos)
        )
        layout.addWidget(self.drop_zone, 1)

        self.controls_bar = QWidget(self)
        self.controls_bar.setFixedWidth(78)
        self.controls_bar.setStyleSheet(
            "background-color: #15171E; border-left: 1px solid #242734;"
        )
        c_layout = QVBoxLayout(self.controls_bar)
        c_layout.setContentsMargins(4, 4, 4, 4)
        c_layout.setSpacing(3)
        c_layout.setAlignment(Qt.AlignCenter)

        row_nav = QHBoxLayout()
        row_nav.setSpacing(3)
        self.btn_up = TierControlBtn("up", "Subir fila de Tier", self.controls_bar)
        self.btn_up.clicked.connect(lambda: self.move_up_requested.emit(self))

        self.btn_down = TierControlBtn("down", "Bajar fila de Tier", self.controls_bar)
        self.btn_down.clicked.connect(lambda: self.move_down_requested.emit(self))
        row_nav.addWidget(self.btn_up)
        row_nav.addWidget(self.btn_down)
        c_layout.addLayout(row_nav)

        row_act = QHBoxLayout()
        row_act.setSpacing(3)
        self.btn_clear = TierControlBtn("clear", "Vaciar fila y devolver al banco", self.controls_bar)
        self.btn_clear.clicked.connect(lambda: self.clear_requested.emit(self))

        self.btn_del = TierControlBtn("del", "Eliminar esta fila de Tier", self.controls_bar)
        self.btn_del.clicked.connect(lambda: self.delete_requested.emit(self))
        row_act.addWidget(self.btn_clear)
        row_act.addWidget(self.btn_del)
        c_layout.addLayout(row_act)

        layout.addWidget(self.controls_bar)

    def _update_label_style(self):
        qc = QColor(self.color_hex)
        lum = 0.299 * qc.red() + 0.587 * qc.green() + 0.114 * qc.blue()
        text_color = "#000000" if lum > 140 else "#FFFFFF"

        self.btn_label.setText(self.tier_name)
        self.btn_label.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color_hex};
                color: {text_color};
                font-size: 20px;
                font-weight: 900;
                border: none;
                border-radius: 0px;
                padding: 6px;
            }}
        """)

    def _edit_tier_properties(self):
        from PySide6.QtGui import QAction
        menu = QMenu(self)
        act_rename = QAction("✏️ Cambiar Nombre", self)
        act_rename.triggered.connect(self._prompt_rename)
        menu.addAction(act_rename)

        act_color = QAction("🎨 Cambiar Color", self)
        act_color.triggered.connect(self._prompt_color)
        menu.addAction(act_color)

        menu.exec(self.btn_label.mapToGlobal(QPoint(0, self.btn_label.height())))

    def _prompt_rename(self):
        new_name, ok = QInputDialog.getText(
            self, "Renombrar Tier", "Nombre del Tier:", text=self.tier_name
        )
        if ok and new_name.strip():
            self.tier_name = new_name.strip()
            self._update_label_style()

    def _prompt_color(self):
        color = QColorDialog.getColor(
            QColor(self.color_hex), self, "Seleccionar color del Tier"
        )
        if color.isValid():
            self.color_hex = color.name()
            self._update_label_style()

    def _rebuild_cards_layout(self):
        while self.drop_zone.flow_layout.count():
            self.drop_zone.flow_layout.takeAt(0)
        for c in self.cards:
            self.drop_zone.flow_layout.addWidget(c)
            c.show()
        self.drop_zone.flow_layout.invalidate()
        self.drop_zone.flow_layout.activate()
        self.drop_zone.updateGeometry()
        self.drop_zone.update()

    def insert_card(self, index: int, card: TierItemCard):
        card.setParent(self.drop_zone)
        card.current_row = self

        if index < 0 or index >= len(self.cards):
            self.cards.append(card)
        else:
            self.cards.insert(index, card)
        self._rebuild_cards_layout()

    def remove_card(self, card: TierItemCard):
        if card in self.cards:
            self.cards.remove(card)
            self.drop_zone.flow_layout.removeWidget(card)
            card.current_row = None
            self._rebuild_cards_layout()
