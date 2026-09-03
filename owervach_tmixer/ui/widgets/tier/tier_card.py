"""Draggable item card for heroes, maps, and players in Tier Maker with special player aura."""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import platformdirs
from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QColor, QDrag, QFont, QImage, QImageReader, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from owervach_tmixer import APP_NAME
from owervach_tmixer.core.special_player import is_special_player_name
from owervach_tmixer.ui.styles import theme
from owervach_tmixer.ui.widgets.hero_widget import hero_portrait_path
from owervach_tmixer.utils import get_resource_path

if TYPE_CHECKING:
    from .tier_row import TierRowWidget

MIME_TIER_ITEM = "application/x-ow-tier-item"
_THUMB_CACHE: dict[str, QPixmap] = {}


def normalize_str(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_str = "".join(c for c in nfkd if not unicodedata.combining(c))
    return "".join(c for c in ascii_str.lower() if c.isalnum())


def find_matching_file(directory: Path, target_name: str) -> Optional[Path]:
    if not directory.exists():
        return None

    target_norm = normalize_str(target_name)
    for file_path in directory.iterdir():
        if not file_path.is_file() or file_path.suffix.lower() not in (
            ".png", ".jpg", ".jpeg", ".webp"
        ):
            continue
        if normalize_str(file_path.stem) == target_norm:
            return file_path
    return None


def get_cached_item_pixmap(
    kind: str,
    name: str,
    subtext: str = "",
    target_size: tuple[int, int] = (76, 76),
) -> QPixmap:
    cache_key = f"{kind}_{name}_{subtext}_{target_size[0]}x{target_size[1]}"
    if cache_key in _THUMB_CACHE:
        return _THUMB_CACHE[cache_key]

    w, h = target_size
    img_path: Optional[Path] = None

    if kind == "hero":
        img_path = hero_portrait_path(name)
    elif kind == "map":
        mode = subtext
        user_dir = Path(platformdirs.user_data_dir(APP_NAME)) / "Maps" / mode
        img_path = find_matching_file(user_dir, name)
        if not img_path and mode:
            bundled_mode_dir = get_resource_path(f"assets/Maps/{mode}")
            img_path = find_matching_file(bundled_mode_dir, name)
        if not img_path:
            maps_root = get_resource_path("assets/Maps")
            if maps_root.exists():
                for sub in maps_root.iterdir():
                    if sub.is_dir():
                        found = find_matching_file(sub, name)
                        if found:
                            img_path = found
                            break

    if img_path and img_path.exists():
        reader = QImageReader(str(img_path))
        reader.setAutoTransform(True)
        reader.setScaledSize(reader.size().scaled(w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding))
        img = reader.read()
        if not img.isNull():
            x_offset = max(0, (img.width() - w) // 2)
            y_offset = max(0, (img.height() - h) // 2)
            cropped_img = img.copy(x_offset, y_offset, w, h)

            rounded = QPixmap(w, h)
            rounded.fill(Qt.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            path = QPainterPath()
            path.addRoundedRect(0, 0, w, h, 6, 6)
            painter.setClipPath(path)
            painter.drawImage(0, 0, cropped_img)
            painter.end()

            _THUMB_CACHE[cache_key] = rounded
            return rounded

    fallback = QPixmap(w, h)
    fallback.fill(QColor("#181A22"))
    p = QPainter(fallback)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QColor("#B8BCC8"))
    p.setFont(QFont("Segoe UI", 12, QFont.Bold))
    label_txt = name[:4] if len(name) <= 4 else name[:3]
    p.drawText(fallback.rect(), Qt.AlignCenter, label_txt)
    p.end()

    _THUMB_CACHE[cache_key] = fallback
    return fallback


class TierItemCard(QFrame):
    card_clicked = Signal(object)
    dropped_on_card = Signal(object, dict)

    def __init__(
        self,
        kind: str,
        name: str,
        subtext: str = "",
        extra_data: Optional[dict] = None,
        dimensions: tuple[int, int] = (125, 75),
        map_font_size: int = 14,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.kind = kind
        self.item_name = name
        self.subtext = subtext
        self.extra_data = extra_data or {}
        self.current_row: Optional[TierRowWidget] = None

        self.setObjectName("tierItemCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAcceptDrops(True)
        self.setProperty("dropTarget", False)
        self.setProperty("cardHovered", False)

        card_w, card_h = dimensions
        self.setFixedSize(card_w, card_h)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"{name} ({subtext})" if subtext else name)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if self.kind == "player":
            is_sp = is_special_player_name(name)
            custom_col = self.extra_data.get("custom_color")

            if is_sp:
                container_bg = "#1D261A"
                border_css = "border: 1px solid #48781B;"
                name_col = "#A4E062"
                badge_style = """
                    QLabel {
                        color: #C2F87A;
                        font-size: 11px;
                        font-weight: 800;
                        background-color: rgba(97, 171, 2, 0.20);
                        border: 1px solid rgba(97, 171, 2, 0.45);
                        border-radius: 4px;
                        padding: 2px 8px;
                    }
                """
            elif custom_col:
                container_bg = "#171A24"
                border_css = f"border: 1px solid {custom_col};"
                name_col = custom_col
                badge_style = """
                    QLabel {
                        color: #FFAA00;
                        font-size: 11px;
                        font-weight: 800;
                        background-color: rgba(255, 170, 0, 0.15);
                        border: 1px solid rgba(255, 170, 0, 0.40);
                        border-radius: 4px;
                        padding: 2px 8px;
                    }
                """
            else:
                container_bg = "#171A24"
                border_css = "border: 1px solid #2B3042;"
                name_col = "#FFFFFF"
                badge_style = """
                    QLabel {
                        color: #FFAA00;
                        font-size: 11px;
                        font-weight: 800;
                        background-color: rgba(255, 170, 0, 0.15);
                        border: 1px solid rgba(255, 170, 0, 0.40);
                        border-radius: 4px;
                        padding: 2px 8px;
                    }
                """

            p_container = QWidget(self)
            self._p_container = p_container
            p_container.setStyleSheet(f"""
                QWidget {{
                    background-color: {container_bg};
                    {border_css}
                    border-radius: 6px;
                }}
            """)
            p_layout = QVBoxLayout(p_container)
            p_layout.setContentsMargins(6, 6, 6, 6)
            p_layout.setSpacing(4)
            p_layout.setAlignment(Qt.AlignCenter)

            lbl_name = QLabel(name, p_container)
            self._lbl_name = lbl_name
            lbl_name.setAlignment(Qt.AlignCenter)
            lbl_name.setWordWrap(True)
            lbl_name.setStyleSheet(f"""
                QLabel {{
                    color: {name_col};
                    font-size: 13px;
                    font-weight: 900;
                    border: none;
                    background: transparent;
                }}
            """)
            p_layout.addWidget(lbl_name)

            lbl_mmr = QLabel(subtext, p_container)
            lbl_mmr.setAlignment(Qt.AlignCenter)
            lbl_mmr.setStyleSheet(badge_style)
            p_layout.addWidget(lbl_mmr)
            layout.addWidget(p_container)

        else:
            self.lbl_thumb = QLabel(self)
            self.lbl_thumb.setFixedSize(card_w - 2, card_h - 2)
            self.lbl_thumb.setAlignment(Qt.AlignCenter)
            self.lbl_thumb.setStyleSheet(
                "border-radius: 6px; background-color: #101115;"
            )

            lookup_img_name = self.extra_data.get("original_name") or name
            pix = get_cached_item_pixmap(
                kind, lookup_img_name, subtext, (card_w - 2, card_h - 2)
            )
            self.lbl_thumb.setPixmap(pix)
            layout.addWidget(self.lbl_thumb)

            if self.kind == "map":
                lbl_title = QLabel(name, self.lbl_thumb)
                lbl_title.setGeometry(0, 0, card_w - 2, card_h - 2)
                lbl_title.setAlignment(Qt.AlignCenter)
                lbl_title.setWordWrap(True)
                lbl_title.setStyleSheet(f"""
                    QLabel {{
                        background-color: rgba(8, 10, 15, 0.50);
                        color: #FFFFFF;
                        font-size: {map_font_size}px;
                        font-weight: 900;
                        border-radius: 6px;
                        padding: 4px;
                    }}
                    QLabel:hover {{
                        background-color: rgba(8, 10, 15, 0.28);
                    }}
                """)

        self.apply_theme()

    def update_custom_color(self, color_hex: str | None):
        if self.kind != "player":
            return
        if not self.extra_data:
            self.extra_data = {}
        self.extra_data["custom_color"] = color_hex

        if hasattr(self, "_p_container"):
            is_sp = is_special_player_name(self.item_name)
            if is_sp:
                border_css = "border: 1px solid #48781B;"
                name_col = "#A4E062"
            elif color_hex:
                border_css = f"border: 1px solid {color_hex};"
                name_col = color_hex
            else:
                border_css = "border: 1px solid #2B3042;"
                name_col = "#FFFFFF"

            self._p_container.setStyleSheet(f"""
                QWidget {{
                    background-color: #171A24;
                    {border_css}
                    border-radius: 6px;
                }}
            """)
            if hasattr(self, "_lbl_name"):
                self._lbl_name.setStyleSheet(f"""
                    QLabel {{
                        color: {name_col};
                        font-size: 13px;
                        font-weight: 900;
                        border: none;
                        background: transparent;
                    }}
                """)
        self.apply_theme()

    def _repolish(self):
        style = self.style()
        if style:
            style.unpolish(self)
            style.polish(self)
        self.update()

    def set_drop_highlight(self, highlight: bool):
        self.setProperty("dropTarget", highlight)
        self._repolish()

    def enterEvent(self, event):
        self.setProperty("cardHovered", True)
        self._repolish()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setProperty("cardHovered", False)
        self._repolish()
        super().leaveEvent(event)

    def apply_theme(self):
        accent = theme.accent()
        is_sp = (self.kind == "player" and is_special_player_name(self.item_name))
        custom_col = self.extra_data.get("custom_color") if self.kind == "player" else None

        if is_sp:
            border_col = "#48781B"
            bg_col = "#1D261A"
            hover_bg = "#243220"
            hover_border = "#61ab02"
        elif custom_col:
            border_col = custom_col
            bg_col = "#161820"
            hover_bg = "#202432"
            hover_border = custom_col
        else:
            border_col = "#2B2F3E"
            bg_col = "#161820"
            hover_bg = "#202432"
            hover_border = accent

        self.setStyleSheet(f"""
            QFrame#tierItemCard {{
                background-color: {bg_col};
                border: 1px solid {border_col};
                border-radius: 6px;
            }}
            QFrame#tierItemCard[cardHovered=\"true\"] {{
                border: 1.5px solid {hover_border};
                background-color: {hover_bg};
            }}
            QFrame#tierItemCard[dropTarget=\"true\"] {{
                border: 2px solid {accent} !important;
                background-color: {theme.accent_rgba(0.24)} !important;
            }}
        """)
        self.setProperty("dropTarget", False)
        self.setProperty("cardHovered", False)
        self._repolish()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.pos()
        elif event.button() == Qt.RightButton:
            self.card_clicked.emit(self)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.card_clicked.emit(self)
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if (
            event.pos() - getattr(self, "_drag_start_pos", QPoint())
        ).manhattanLength() < 3:
            return

        drag = QDrag(self)
        mime = QMimeData()
        payload = {
            "kind": self.kind,
            "name": self.item_name,
            "subtext": self.subtext,
            "extra": self.extra_data,
        }
        mime.setData(MIME_TIER_ITEM, json.dumps(payload).encode("utf-8"))
        drag.setMimeData(mime)

        pix = self.grab()
        drag.setPixmap(pix)
        drag.setHotSpot(QPoint(pix.width() // 2, pix.height() // 2))

        drag.exec(Qt.MoveAction)

        w = self.window()
        if w:
            for card in w.findChildren(TierItemCard):
                card.setProperty("dropTarget", False)
                card.setProperty("cardHovered", False)
                card._repolish()
        self.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(MIME_TIER_ITEM):
            event.acceptProposedAction()
            self.setProperty("dropTarget", True)
            self._repolish()

    def dragLeaveEvent(self, event):
        self.setProperty("dropTarget", False)
        self._repolish()

    def dropEvent(self, event):
        self.setProperty("dropTarget", False)
        self._repolish()
        if event.mimeData().hasFormat(MIME_TIER_ITEM):
            data = json.loads(
                event.mimeData().data(MIME_TIER_ITEM).data().decode("utf-8")
            )
            self.dropped_on_card.emit(self, data)
            event.acceptProposedAction()
