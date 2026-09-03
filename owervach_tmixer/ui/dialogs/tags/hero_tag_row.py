"""Interactive hero row and crisp QPainter vector buttons for tag management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPixmap, QPolygon
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.core.models import Hero, Role
from owervach_tmixer.ui.widgets.hero_widget import get_rounded_pixmap, hero_portrait_path
from .tag_prompt_dialog import AddTagPromptDialog

if TYPE_CHECKING:
    from owervach_tmixer.ui.dialogs.hero_tags_dialog import HeroTagsDialog

ROLE_BADGE_COLOR = {
    Role.TANK: "#00B4FF",
    Role.DAMAGE: "#FF4444",
    Role.SUPPORT: "#FFD700",
}


class TagVectorBtn(QPushButton):
    """Crisp vector button via QPainter (100% font-independent for Linux/Wayland & Windows)."""

    def __init__(self, action_type: str, tooltip: str = "", size: tuple[int, int] = (30, 28), parent: QWidget | None = None):
        super().__init__(parent)
        self.action_type = action_type
        w, h = size
        self.setFixedSize(w, h)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            self.setToolTip(tooltip)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_hovered = self.underMouse()
        is_pressed = self.isDown()

        if self.action_type in ("left", "right"):
            bg_col = QColor("#2E3646") if is_hovered else QColor("#222630")
            border_col = QColor("#61ab02") if is_hovered else QColor("#363D4E")
            icon_col = QColor("#FFFFFF") if is_hovered else QColor("#84E01B")
        elif self.action_type == "del":
            bg_col = QColor("#5A1E24") if is_hovered else QColor("#2E181C")
            border_col = QColor("#FF4444") if is_hovered else QColor("#66242C")
            icon_col = QColor("#FFFFFF") if is_hovered else QColor("#FFAAAA")
        else:
            bg_col = QColor("#2A2D38") if is_hovered else QColor("#1C1F26")
            border_col = QColor("#444A5C") if is_hovered else QColor("#2E3240")
            icon_col = QColor("#E0E4F0")

        if is_pressed:
            bg_col = bg_col.darker(130)

        painter.setPen(QPen(border_col, 1))
        painter.setBrush(QBrush(bg_col))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 4, 4)

        cx = self.width() // 2
        cy = self.height() // 2

        if self.action_type == "left":
            poly = QPolygon([QPoint(cx - 4, cy), QPoint(cx + 3, cy - 5), QPoint(cx + 3, cy + 5)])
            painter.setPen(QPen(icon_col, 1))
            painter.setBrush(QBrush(icon_col))
            painter.drawPolygon(poly)
        elif self.action_type == "right":
            poly = QPolygon([QPoint(cx + 4, cy), QPoint(cx - 3, cy - 5), QPoint(cx - 3, cy + 5)])
            painter.setPen(QPen(icon_col, 1))
            painter.setBrush(QBrush(icon_col))
            painter.drawPolygon(poly)
        elif self.action_type == "del":
            painter.setPen(QPen(icon_col, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(cx - 4, cy - 4, cx + 4, cy + 4)
            painter.drawLine(cx + 4, cy - 4, cx - 4, cy + 4)

        painter.end()


class HeroTagRow(QFrame):
    """Interactive hero row with selection checkbox and inline tags."""

    def __init__(self, hero: Hero, dialog: HeroTagsDialog, parent: QWidget | None = None):
        super().__init__(parent)
        self.hero = hero
        self.dialog = dialog
        self.setStyleSheet("""
            QFrame {
                background-color: #17181D;
                border: 1px solid #282A33;
                border-radius: 8px;
            }
            QFrame:hover {
                border-color: #383D4A;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        self.chk_select = QCheckBox()
        self.chk_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_select.toggled.connect(lambda _: self.dialog._on_selection_changed())
        layout.addWidget(self.chk_select)

        thumb = QLabel()
        thumb.setFixedSize(34, 34)
        img_path = hero_portrait_path(self.hero.original_name or self.hero.name)
        if img_path:
            pix = QPixmap(str(img_path))
            if not pix.isNull():
                thumb.setPixmap(get_rounded_pixmap(pix, size=34, radius=6.0))
        thumb.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(thumb)

        name_col = QVBoxLayout()
        name_col.setSpacing(2)

        name_lbl = QLabel(self.hero.name)
        name_lbl.setStyleSheet("font-size: 13px; font-weight: 800; color: #FFFFFF; background: transparent;")
        name_col.addWidget(name_lbl)

        role_lbl = QLabel(self.hero.role.value.capitalize())
        role_lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {ROLE_BADGE_COLOR.get(self.hero.role, '#AAA')}; background: transparent;")
        name_col.addWidget(role_lbl)

        name_col_widget = QWidget()
        name_col_widget.setFixedWidth(110)
        name_col_widget.setLayout(name_col)
        name_col_widget.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(name_col_widget)

        self.tags_layout = QHBoxLayout()
        self.tags_layout.setSpacing(6)
        self.rebuild_chips()
        layout.addLayout(self.tags_layout, 1)

        btn_add = QPushButton("+ Etiqueta")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton {
                font-size: 11px; font-weight: 700; color: #C0C5D2;
                background-color: #22252D; border: 1px solid #363B48;
                border-radius: 5px; padding: 5px 10px;
            }
            QPushButton:hover { background-color: #2D323E; border-color: #61ab02; color: #FFFFFF; }
        """)
        btn_add.clicked.connect(self._prompt_add_tag)
        layout.addWidget(btn_add)

    def is_selected(self) -> bool:
        return self.chk_select.isChecked()

    def set_selected(self, selected: bool):
        self.chk_select.setChecked(selected)

    def rebuild_chips(self):
        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.hero.tags:
            empty = QLabel("Sin etiquetas")
            empty.setStyleSheet("color: #555A68; font-size: 11px; font-style: italic; background: transparent; border: none;")
            self.tags_layout.addWidget(empty)
            return

        for k, v in list(self.hero.tags.items()):
            chip = QFrame()
            chip.setStyleSheet("""
                QFrame {
                    background-color: #1F232B;
                    border: 1px solid #333845;
                    border-radius: 5px;
                }
            """)
            c_layout = QHBoxLayout(chip)
            c_layout.setContentsMargins(8, 3, 8, 3)
            c_layout.setSpacing(6)

            display_text = f"<b>{k}</b>" if (not v or v == "✓" or v == k) else f"<b>{k}:</b> {v}"
            lbl = QLabel(display_text)
            lbl.setStyleSheet("font-size: 11px; color: #E0E4F0; background: transparent; border: none;")
            c_layout.addWidget(lbl)

            btn_del = TagVectorBtn("del", tooltip=f"Quitar etiqueta '{k}' de {self.hero.name}", size=(18, 18), parent=chip)
            btn_del.clicked.connect(lambda _, key=k: self._remove_tag(key))
            c_layout.addWidget(btn_del)

            self.tags_layout.addWidget(chip)

        self.tags_layout.addStretch()

    def _prompt_add_tag(self):
        existing_keys = self.dialog.get_all_category_keys()
        diag = AddTagPromptDialog(self.hero.name, existing_categories=existing_keys, parent=self)
        if diag.exec() == QDialog.DialogCode.Accepted:
            k, v = diag.get_data()
            if k:
                self.hero.tags[k] = v
                self.rebuild_chips()
                self.dialog._persist_changes()

    def _remove_tag(self, key: str):
        if key in self.hero.tags:
            del self.hero.tags[key]
            self.rebuild_chips()
            self.dialog._persist_changes()
