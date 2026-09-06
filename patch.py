"""
PATCH ATÓMICO: Restauración Canónica de la Anatomía Zero-Shift y Estabilidad Visual.
Afecta:
- owervach_tmixer/ui/widgets/player_slot.py
- owervach_tmixer/ui/widgets/bans_panel.py
- owervach_tmixer/ui/widgets/team_display.py
- owervach_tmixer/ui/main_window.py
"""

import os
import py_compile
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# 1. owervach_tmixer/ui/widgets/player_slot.py
# ---------------------------------------------------------------------------
PLAYER_SLOT_CODE = r'''"""Inline-editable player slot card with true-center/left names, SVG role badges, and clean zero-shift layout."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QDrag, QFont, QFontMetrics, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QWidget,
)

from owervach_tmixer.core.models import Player, Role
from owervach_tmixer.core.special_player import (
    format_player_name,
    is_special_player_name,
)
from owervach_tmixer.ui.styles import theme
from owervach_tmixer.utils import get_resource_path
from .dnd import (
    clear_all_drop_highlights,
    make_payload,
    payload_from,
    payload_to_mime,
    register_slot,
    set_drop_highlight,
    unregister_slot,
)
from .player_slot_menu import show_slot_context_menu

ROLE_EMOJI = {Role.TANK: "🛡️", Role.DAMAGE: "⚔️", Role.SUPPORT: "💉"}
ROLE_COLOR = {Role.TANK: "#00B4FF", Role.DAMAGE: "#FF4444", Role.SUPPORT: "#FFD700"}
ROLE_BG = {
    Role.TANK: "rgba(0, 180, 255, 0.16)",
    Role.DAMAGE: "rgba(255, 68, 68, 0.16)",
    Role.SUPPORT: "rgba(255, 215, 0, 0.16)",
}

_ROLE_PIXMAP_CACHE: dict[tuple[Role, int, str], QPixmap] = {}


def _get_role_svg_pixmap(role: Role, size: int = 16, color_hex: str = "#FFFFFF") -> QPixmap:
    cache_key = (role, size, color_hex)
    if cache_key in _ROLE_PIXMAP_CACHE:
        return _ROLE_PIXMAP_CACHE[cache_key]

    file_map = {
        Role.TANK: "assets/role_tank.svg",
        Role.DAMAGE: "assets/role_damage.svg",
        Role.SUPPORT: "assets/role_support.svg",
    }
    svg_path = get_resource_path(file_map.get(role, ""))
    if not svg_path.exists():
        return QPixmap()

    try:
        from PySide6.QtSvg import QSvgRenderer
        renderer = QSvgRenderer(str(svg_path))
        base_pix = QPixmap(size, size)
        base_pix.fill(Qt.transparent)
        p = QPainter(base_pix)
        renderer.render(p)
        p.end()

        tinted = QPixmap(size, size)
        tinted.fill(Qt.transparent)
        tp = QPainter(tinted)
        tp.setCompositionMode(QPainter.CompositionMode_Source)
        tp.drawPixmap(0, 0, base_pix)
        tp.setCompositionMode(QPainter.CompositionMode_SourceIn)
        tp.fillRect(tinted.rect(), QColor(color_hex))
        tp.end()

        _ROLE_PIXMAP_CACHE[cache_key] = tinted
        return tinted
    except Exception:
        return QPixmap()


class _NameEdit(QLineEdit):
    def __init__(self, slot: PlayerSlotWidget, parent=None):
        super().__init__(parent)
        self._slot = slot
        self.setDragEnabled(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAcceptDrops(False)

    def mousePressEvent(self, event):
        self._slot._drag_pos = event.position().toPoint()
        if self._slot._player is not None and self.isReadOnly():
            self.deselect()
            self.setCursorPosition(0)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._slot._maybe_start_drag(event):
            event.accept()
            return
        if self._slot._player is not None and self.isReadOnly():
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self._slot._player is not None and not is_special_player_name(self._slot._player.name):
            self._slot._begin_edit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self._slot._player is not None and not self.isReadOnly():
            self._slot._cancel_edit()
            return
        super().keyPressEvent(event)


class PlayerSlotWidget(QFrame):
    """Esports Stat Card player cell with Zero-Shift 76px anatomy and centered alignment."""

    editingFinished = Signal()
    slot_created = Signal(str)
    slot_renamed = Signal(str)
    slot_fixed_changed = Signal(object)
    slot_role_changed = Signal(object)
    slot_mmr_changed = Signal(object, int)
    slot_color_changed = Signal(str, object)
    slot_bench = Signal()
    slot_save = Signal()
    slot_unsave = Signal()
    slot_remove = Signal()
    slot_remove_permanent = Signal()
    drop_requested = Signal(object, object)

    def __init__(self, team_num: int, slot_idx: int, parent=None):
        super().__init__(parent)
        self.team_num = team_num
        self.slot_idx = slot_idx
        self._player: Player | None = None
        self._saved = False
        self._show_roles = True
        self._show_mmr = False
        self._suppress = False
        self._drag_pos: QPoint | None = None
        self._font_size = 14

        self._font_weight = "bold"
        self._text_align = "center"
        self._dynamic_font = True
        self._role_badge_style = "emoji"
        self._badge_outlines = False

        self.setObjectName("playerSlot")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumHeight(36)
        self.setMaximumHeight(74)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAcceptDrops(True)
        register_slot(self)

        self._setup_ui()

    def _setup_ui(self):
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(8, 2, 8, 2)
        self._layout.setSpacing(4)

        # 1. Left Wing (Role / Badges) - 76px Zero-Shift
        self.left_wing = QWidget(self)
        self.left_wing.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.left_wing.setFixedWidth(76)
        self.left_layout = QHBoxLayout(self.left_wing)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(4)
        self.left_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.lbl_role_badge = QLabel(self.left_wing)
        self.lbl_role_badge.setAlignment(Qt.AlignCenter)
        self.left_layout.addWidget(self.lbl_role_badge)

        self.lbl_icons = QLabel(self.left_wing)
        self.lbl_icons.setAlignment(Qt.AlignCenter)
        self.lbl_icons.setFixedWidth(18)
        self.left_layout.addWidget(self.lbl_icons)

        self._layout.addWidget(self.left_wing, 0, Qt.AlignVCenter)

        # 2. Name Editor (Centro geométrico)
        self._editor = _NameEdit(self)
        self._editor.setObjectName("playerSlotEditor")
        self._editor.setPlaceholderText(theme.tokens().slot_empty_text)
        self._editor.setClearButtonEnabled(False)
        self._editor.setProperty("transparent", True)
        font = QFont()
        font.setPointSize(14)
        font.setWeight(QFont.Weight.Bold)
        self._editor.setFont(font)
        self._editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self._editor, 1, Qt.AlignVCenter)

        # 3. Right Wing (MMR Badge) - 76px Zero-Shift
        self.right_wing = QWidget(self)
        self.right_wing.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.right_wing.setFixedWidth(76)
        self.right_layout = QHBoxLayout(self.right_wing)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(4)
        self.right_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.lbl_mmr_badge = QLabel(self.right_wing)
        self.lbl_mmr_badge.setAlignment(Qt.AlignCenter)
        self.right_layout.addWidget(self.lbl_mmr_badge)

        self._layout.addWidget(self.right_wing, 0, Qt.AlignVCenter)

        self._decor = QLabel("", self)
        self._decor.hide()

        self._editor.editingFinished.connect(self.editingFinished.emit)
        self.editingFinished.connect(self._on_editing_finished)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda pos: show_slot_context_menu(self, self.mapToGlobal(pos)))
        self._editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self._editor.customContextMenuRequested.connect(lambda pos: show_slot_context_menu(self, self._editor.mapToGlobal(pos)))

        self._apply_alignment_layout()
        self._apply_style()

    def destroy(self, destroyWindow=True, destroySubWindows=True):
        unregister_slot(self)
        super().destroy(destroyWindow, destroySubWindows)

    def enterEvent(self, event):
        self.setProperty("hovered", True)
        self._repolish()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setProperty("hovered", False)
        self._repolish()
        super().leaveEvent(event)

    def _repolish(self):
        style = self.style()
        if style:
            style.unpolish(self)
            style.polish(self)
        self.update()

    def _begin_edit(self):
        self._suppress = True
        self._editor.setReadOnly(False)
        self._editor.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._suppress = False
        self._editor.setFocus()
        self._editor.selectAll()

    def set_player(self, player: Player | None, saved: bool, show_roles: bool, show_mmr: bool = False):
        set_drop_highlight(self, False)
        self.setProperty("hovered", False)
        self._player = player
        self._saved = saved
        self._show_roles = show_roles
        self._show_mmr = show_mmr
        self._suppress = True
        try:
            if player is None:
                self._editor.clear()
                self._editor.setReadOnly(False)
                self._editor.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                self._editor.setPlaceholderText(theme.tokens().slot_empty_text)
                self.lbl_mmr_badge.hide()
                self.lbl_icons.hide()
                self.lbl_role_badge.hide()
                self._decor.setText("")
            else:
                self._editor.setText(player.name)
                self._editor.setReadOnly(True)
                self._editor.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                self._editor.deselect()
                self._editor.setCursorPosition(0)
                self._editor.setPlaceholderText("")

                if show_mmr:
                    mmr_val = player.get_mmr_for_role(player.role)
                    self.lbl_mmr_badge.setText(f"⚡{mmr_val}")
                    self.lbl_mmr_badge.setAlignment(Qt.AlignCenter)
                    self.lbl_mmr_badge.setFixedHeight(22)
                    self.lbl_mmr_badge.setMinimumWidth(30)
                    use_outline = getattr(self, "_badge_outlines", False)
                    border_css = "border: 1px solid #FFAA00;" if use_outline else "border: none;"
                    bg_css = "rgba(255, 170, 0, 0.12)" if use_outline else "rgba(255, 170, 0, 0.16)"
                    self.lbl_mmr_badge.setStyleSheet(f"""
                        QLabel {{
                            font-size: 10px; font-weight: 900; color: #FFAA00;
                            background-color: {bg_css};
                            {border_css}
                            border-radius: 5px; padding: 0px 4px;
                        }}
                    """)
                    self.lbl_mmr_badge.show()
                else:
                    self.lbl_mmr_badge.hide()

                icons = []
                if is_special_player_name(player.name):
                    icons.append("⚜️")
                if getattr(player, "is_vip", False):
                    icons.append("👑")
                if saved:
                    icons.append("⭐")
                if player.fixed_team:
                    icons.append("🔒")

                icon_str = " ".join(icons)
                self.lbl_icons.setText(icon_str)
                self.lbl_icons.setStyleSheet("font-size: 11px; color: #E2E6F0; background: transparent; border: none;")

                if icons:
                    self.lbl_icons.setFixedWidth(max(18, 14 * len(icons)))
                    self.lbl_icons.show()
                else:
                    self.lbl_icons.hide()

                self._refresh_role_badge(player)
                self._decor.setText(_indicators(player, self._saved, self._show_roles, self._show_mmr))
        finally:
            self._suppress = False
        self._apply_alignment_layout()
        self._apply_style()

    def _refresh_role_badge(self, player: Player):
        if not (self._show_roles and player.role):
            self.lbl_role_badge.hide()
            return

        t = theme.tokens()
        r_color = ROLE_COLOR.get(player.role, "#AAA")
        r_bg = ROLE_BG.get(player.role, "rgba(255, 255, 255, 0.08)")
        r_emoji = ROLE_EMOJI.get(player.role, "")
        style = getattr(self, "_role_badge_style", "emoji")

        if (t.slot_side_stripe and style == "emoji") or style == "svg":
            svg_pix = _get_role_svg_pixmap(player.role, size=15, color_hex="#FFFFFF")
            if not svg_pix.isNull():
                self.lbl_role_badge.setPixmap(svg_pix)
                self.lbl_role_badge.setText("")
                self.lbl_role_badge.setFixedSize(26, 22)
                self.lbl_role_badge.setAlignment(Qt.AlignCenter)
                self.lbl_role_badge.setStyleSheet(f"""
                    QLabel {{
                        background-color: {r_bg};
                        border: 1px solid {r_color};
                        border-radius: 4px;
                    }}
                """)
                self.lbl_role_badge.show()
                return

        self.lbl_role_badge.setPixmap(QPixmap())
        if style == "emoji":
            badge_txt = r_emoji
            self.lbl_role_badge.setFixedSize(26, 22)
            font_px = "12px"
            pad_px = "0px"
        elif style == "initial":
            badge_txt = f"{r_emoji} {player.role.value[0].upper()}"
            self.lbl_role_badge.setFixedHeight(22)
            self.lbl_role_badge.setMinimumWidth(36)
            font_px = "10px"
            pad_px = "0px 4px"
        else:
            badge_txt = f"{r_emoji} {player.role.value.upper()}"
            self.lbl_role_badge.setFixedHeight(22)
            self.lbl_role_badge.setMinimumWidth(62)
            font_px = "9.5px"
            pad_px = "0px 6px"

        use_outline = getattr(self, "_badge_outlines", False)
        border_css = f"border: 1px solid {r_color};" if use_outline else "border: none;"
        self.lbl_role_badge.setText(badge_txt)
        self.lbl_role_badge.setAlignment(Qt.AlignCenter)
        self.lbl_role_badge.setStyleSheet(f"""
            QLabel {{
                font-size: {font_px}; font-weight: 900; color: {r_color};
                background-color: {r_bg};
                {border_css}
                border-radius: 5px; padding: {pad_px};
            }}
        """)
        self.lbl_role_badge.show()

    def text(self) -> str:
        return self._editor.text()

    def setText(self, text: str):
        self._editor.setText(text)
        self._editor.setCursorPosition(0)

    def clear(self):
        self._editor.clear()

    def isReadOnly(self) -> bool:
        return self._editor.isReadOnly()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._maybe_start_drag(event):
            event.accept()
            return
        super().mouseMoveEvent(event)

    def _maybe_start_drag(self, event) -> bool:
        if self._player is None or self._drag_pos is None:
            return False
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return False
        delta = event.position().toPoint() - self._drag_pos
        if delta.manhattanLength() < 3:
            return False
        self._drag_pos = None
        self._start_drag()
        return True

    def _start_drag(self):
        if self._player is None:
            return

        self.setProperty("hovered", False)
        set_drop_highlight(self, False)
        self._repolish()

        is_sp = is_special_player_name(self._player.name)
        if is_sp:
            from owervach_tmixer.ui.easter_eggs import notify_special_drag_start, notify_special_drag_end
            notify_special_drag_start(self.window())

        drag = QDrag(self)
        drag.setMimeData(payload_to_mime(
            make_payload("slot", self._player.name, self.team_num, self.slot_idx)))
        pixmap = self.grab()
        if pixmap.width() > 300:
            pixmap = pixmap.scaledToWidth(300, Qt.TransformationMode.SmoothTransformation)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))

        drag.exec(Qt.DropAction.MoveAction)
        clear_all_drop_highlights()

        if is_sp:
            notify_special_drag_end()

    def _is_self_drop(self, payload) -> bool:
        return (payload.get("kind") == "slot"
                and payload.get("team") == self.team_num
                and payload.get("idx") == self.slot_idx)

    def dragEnterEvent(self, event):
        payload = payload_from(event.mimeData())
        if payload is None or self._is_self_drop(payload):
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        set_drop_highlight(self, True)
        event.accept()

    def dragMoveEvent(self, event):
        payload = payload_from(event.mimeData())
        if payload is None or self._is_self_drop(payload):
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()

    def dragLeaveEvent(self, event):
        set_drop_highlight(self, False)
        event.accept()

    def dropEvent(self, event):
        payload = payload_from(event.mimeData())
        set_drop_highlight(self, False)
        clear_all_drop_highlights()
        if payload is None or self._is_self_drop(payload):
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()
        self.drop_requested.emit(payload, self.slot_idx)

    def _cancel_edit(self):
        self._suppress = True
        if self._player is not None:
            self._editor.setText(self._player.name)
            self._editor.setReadOnly(True)
            self._editor.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self._editor.setCursorPosition(0)
        self._suppress = False
        self._editor.clearFocus()

    def _on_editing_finished(self):
        if self._suppress:
            return
        text = self.text().strip()
        if not text:
            if self._player is not None:
                self._cancel_edit()
            return

        formatted = format_player_name(text, True)
        if self._player is None:
            self.slot_created.emit(formatted)
            return
        if formatted == self._player.name:
            self._cancel_edit()
            return

        self.slot_renamed.emit(formatted)

    def set_font_preferences(
        self,
        size: int,
        weight: str,
        align: str = "center",
        dynamic_font: bool = True,
        role_badge_style: str = "emoji",
        badge_outlines: bool = False
    ):
        self._font_size = max(11, min(20, size))
        self._font_weight = weight
        self._text_align = align
        self._dynamic_font = dynamic_font
        self._role_badge_style = role_badge_style
        self._badge_outlines = badge_outlines
        self._apply_alignment_layout()
        self._apply_style()
        self._update_editor_style()

    def _update_editor_style(self):
        if not hasattr(self, "_editor"):
            return

        t = theme.tokens()
        special = self._player is not None and is_special_player_name(self._player.name)
        fixed = self._player is not None and self._player.is_fixed
        custom_color = getattr(self._player, "custom_color", None) if self._player else None

        if special:
            name_color = "#A4E062"
        elif custom_color:
            name_color = custom_color
        elif self._player is None and t.id == "overwatch":
            name_color = "#5F738E"
        else:
            name_color = t.accent_light() if fixed else t.text_primary

        weight_enum = QFont.Weight.Bold if getattr(self, "_font_weight", "bold") == "bold" else (
            QFont.Weight.DemiBold if getattr(self, "_font_weight", "medium") == "medium" else QFont.Weight.Medium
        )

        font_name = t.font_family.split(",")[0].strip(' "\'')

        if not getattr(self, "_dynamic_font", True):
            target_size = max(12, getattr(self, "_font_size", 14))
        else:
            h = max(36, min(74, self.height()))
            target_size = int(13 + (h - 36) * (18 - 13) / (74 - 36))
            target_size = max(12, min(18, target_size))

        f = self._editor.font()
        f.setFamily(font_name)
        f.setPointSize(target_size)
        f.setWeight(weight_enum)
        self._editor.setFont(f)
        self._editor.setCursorPosition(0)

        ph_family = t.font_family_display if t.id == "overwatch" else t.font_family
        ph_style = "italic" if t.id == "overwatch" else "normal"
        ph_spacing = "2px" if t.id == "overwatch" else "0px"
        self._editor.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                border: none;
                padding: 0px 4px;
                color: {name_color};
            }}
            QLineEdit::placeholder {{
                color: #5F738E;
                font-family: {ph_family};
                font-weight: 800;
                font-style: {ph_style};
                letter-spacing: {ph_spacing};
            }}
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_editor_style()

    def _apply_alignment_layout(self):
        while self._layout.count():
            self._layout.takeAt(0)

        self._layout.setContentsMargins(8, 2, 8, 2)
        self._layout.setSpacing(4)
        self._editor.setMinimumWidth(40)

        while self.left_layout.count():
            self.left_layout.takeAt(0)
        while self.right_layout.count():
            self.right_layout.takeAt(0)

        align_mode = getattr(self, "_text_align", "center")

        if align_mode == "left":
            self.left_wing.setFixedWidth(28)
            self.right_wing.setFixedWidth(80)
            self._editor.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            self.left_layout.addWidget(self.lbl_icons)
            self._layout.addWidget(self.left_wing, 0, Qt.AlignVCenter)
            self._layout.addWidget(self._editor, 1, Qt.AlignVCenter)

            self.right_layout.addWidget(self.lbl_mmr_badge)
            self.right_layout.addWidget(self.lbl_role_badge)
            self._layout.addWidget(self.right_wing, 0, Qt.AlignVCenter)

        elif align_mode == "center_mirrored":
            WING_WIDTH = 76
            self.left_wing.setFixedWidth(WING_WIDTH)
            self.right_wing.setFixedWidth(WING_WIDTH)
            self._editor.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self.left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignVCenter)
            self.left_layout.addWidget(self.lbl_icons)

            self.right_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignVCenter)
            self.right_layout.addWidget(self.lbl_mmr_badge)
            self.right_layout.addWidget(self.lbl_role_badge)

            self._layout.addWidget(self.left_wing, 0, Qt.AlignVCenter)
            self._layout.addWidget(self._editor, 1, Qt.AlignVCenter)
            self._layout.addWidget(self.right_wing, 0, Qt.AlignVCenter)

        elif align_mode == "center_wings":
            WING_WIDTH = 76
            self.left_wing.setFixedWidth(WING_WIDTH)
            self.right_wing.setFixedWidth(WING_WIDTH)
            self._editor.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self.left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignVCenter)
            self.left_layout.addWidget(self.lbl_role_badge)

            self.right_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignVCenter)
            self.right_layout.addWidget(self.lbl_icons)
            self.right_layout.addWidget(self.lbl_mmr_badge)

            self._layout.addWidget(self.left_wing, 0, Qt.AlignVCenter)
            self._layout.addWidget(self._editor, 1, Qt.AlignVCenter)
            self._layout.addWidget(self.right_wing, 0, Qt.AlignVCenter)

        else:
            # PREDETERMINADO SATHARA (center) - 76px Zero-Shift simétrico
            WING_WIDTH = 76
            self.left_wing.setFixedWidth(WING_WIDTH)
            self.right_wing.setFixedWidth(WING_WIDTH)
            self._editor.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self.left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignVCenter)
            self.left_layout.addWidget(self.lbl_role_badge)
            self.left_layout.addWidget(self.lbl_icons)

            self.right_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignVCenter)
            self.right_layout.addWidget(self.lbl_mmr_badge)

            self._layout.addWidget(self.left_wing, 0, Qt.AlignVCenter)
            self._layout.addWidget(self._editor, 1, Qt.AlignVCenter)
            self._layout.addWidget(self.right_wing, 0, Qt.AlignVCenter)

        self._editor.setCursorPosition(0)

    def _apply_style(self):
        t = theme.tokens()
        special = self._player is not None and is_special_player_name(self._player.name)
        fixed = self._player is not None and self._player.is_fixed
        custom_color = getattr(self._player, "custom_color", None) if self._player else None
        is_t1 = (self.team_num == 1)

        team_accent = "#00B4FF" if is_t1 else "#FF4444"
        r = t.border_radius

        if special:
            border = "#48781B"
            background = "#1D261A"
            name_color = "#A4E062"
            hover_border = "#61ab02"
            hover_bg = "#263622"
        elif custom_color:
            border = custom_color
            background = t.bg_surface
            name_color = custom_color
            hover_border = custom_color
            hover_bg = t.bg_elevated
        else:
            if t.id == "overwatch":
                border = t.accent if fixed else "transparent"
                background = t.bg_surface
                name_color = t.text_primary
                hover_border = "#00F0FF"
                hover_bg = t.bg_elevated
            else:
                border = t.accent if fixed else t.border_subtle
                background = t.bg_surface
                name_color = t.accent_light() if fixed else t.text_primary
                hover_border = team_accent
                hover_bg = t.bg_elevated

        self._update_editor_style()
        if self._player:
            self._refresh_role_badge(self._player)

        side_border = f"border-left: 3px solid {team_accent};" if t.id == "overwatch" else f"border: 1px solid {border};"

        self.setStyleSheet(f"""
            #playerSlot {{
                background-color: {background};
                {side_border}
                border-radius: {r}px;
            }}
            #playerSlot:hover, #playerSlot[hovered="true"] {{
                background-color: {hover_bg};
                border: 1.5px solid {hover_border};
                border-radius: {r}px;
            }}
            #playerSlot[dropTarget="true"] {{
                border: 1.5px solid {t.accent} !important;
                background-color: {t.accent_rgba(0.22)} !important;
                border-radius: {r}px;
            }}
            QLineEdit#playerSlotEditor {{
                background-color: transparent;
                border: none;
                padding: 0px 4px;
                color: {name_color};
            }}
        """)
        self._editor.setCursorPosition(0)


def _indicators(player: Player, saved: bool, show_roles: bool, show_mmr: bool = False) -> str:
    parts = []
    if show_mmr:
        mmr_val = player.get_mmr_for_role(player.role)
        parts.append(f"⚡{mmr_val}")
    if is_special_player_name(player.name):
        parts.append("⚜️")
    if getattr(player, "is_vip", False):
        parts.append("👑")
    if saved:
        parts.append("⭐")
    if player.fixed_team:
        parts.append("🔒")
    if show_roles and player.role:
        emoji = ROLE_EMOJI.get(player.role, "")
        parts.append(f"{emoji}{player.role.value.upper()}")
    return " ".join(parts)
'''

# ---------------------------------------------------------------------------
# 2. owervach_tmixer/ui/widgets/bans_panel.py
# ---------------------------------------------------------------------------
BANS_PANEL_CODE = r'''"""Banned-hero section of the side column with clean centered flow and proper sizing."""

from __future__ import annotations
from .smooth_scroll import SmoothScrollArea

from typing import List, Optional

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.ui.styles import theme
from .hero_widget import hero_portrait_path, resolve_canonical_name
from .flow_layout import FlowLayout

DEFAULT_PORTRAIT = 44
MIN_PORTRAIT = 16
MAX_PORTRAIT = 64

_BORDER = 1
_BORDER_COLOR = "#FF4444"
_CLIPPED_PORTRAIT_CACHE: dict[tuple[str, int], QPixmap] = {}


def _get_clipped_pixmap(name: str, pix: QPixmap, size: int, radius: float = 6.0) -> QPixmap:
    cache_key = (name, size)
    if cache_key in _CLIPPED_PORTRAIT_CACHE:
        return _CLIPPED_PORTRAIT_CACHE[cache_key]
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

    _CLIPPED_PORTRAIT_CACHE[cache_key] = out
    return out


class BansPanel(QFrame):
    """Bans panel section listing currently banned heroes with clean responsive layout."""

    collapse_changed = Signal(bool)
    randomize_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._expanded = True
        self._banned_names: list[str] = []
        self._portrait_size = DEFAULT_PORTRAIT
        self._visible_rows = 3
        self.setObjectName("bansPanel")
        self.setMinimumHeight(44)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Header Bar
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        self.title_label = QLabel("HÉROES BANEADOS (0)", self)
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

        # Responsive Scroll Area with clean solid background
        self.scroll = SmoothScrollArea(self)
        self.scroll.setObjectName("bansScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.portraits = QWidget(self.scroll)
        self.portraits.setObjectName("bansPortraits")
        self.portraits_layout = FlowLayout(self.portraits, margin=4, h_spacing=6, v_spacing=6)

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
            QScrollArea#bansScroll, QWidget#bansPortraits, QScrollArea#bansScroll > QWidget > QWidget {
                background-color: #16171D;
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

        self.title_label.setText(f"HÉROES BANEADOS ({len(self._banned_names)})")
        self._adjust_panel_height()

    def set_visible_rows(self, rows: int):
        self._visible_rows = max(1, min(5, int(rows)))
        self._adjust_panel_height()

    def _calculate_exact_height(self, num_rows: int) -> int:
        item_size = self._portrait_size + 2 * _BORDER
        v_spacing = 6
        margin = 4
        content_h = num_rows * item_size + max(0, num_rows - 1) * v_spacing + 2 * margin
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

        vp_w = self.scroll.viewport().width() if self.scroll.viewport() else 0
        if vp_w < 50:
            vp_w = max(100, self.width() - 24)

        item_w = self._portrait_size + 2 * _BORDER + 6
        per_row = max(1, vp_w // item_w)
        needed_rows = (len(self._banned_names) + per_row - 1) // per_row

        display_rows = min(needed_rows, self._visible_rows)
        target_h = self._calculate_exact_height(display_rows)

        self.setMinimumHeight(target_h)
        self.setMaximumHeight(target_h)

        if needed_rows > self._visible_rows:
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def showEvent(self, event):
        super().showEvent(event)
        self._adjust_panel_height()

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
        image = hero_portrait_path(canonical) or hero_portrait_path(name)

        if image:
            pix = QPixmap(str(image))
            label.setPixmap(_get_clipped_pixmap(canonical, pix, self._portrait_size, radius=5.0))
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
'''

# ---------------------------------------------------------------------------
# 3. owervach_tmixer/ui/widgets/team_display.py
# ---------------------------------------------------------------------------
TEAM_DISPLAY_CODE = r'''"""Team display widget with proportional player slot expanding, alignment support, and theme sync."""

from __future__ import annotations

import random
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QCursor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.core.models import GameMode, Player, Role
from owervach_tmixer.ui.styles import theme

from .dnd import clear_all_drop_highlights, payload_from
from .player_slot import PlayerSlotWidget
from .match_display import MatchDisplayWidget

_RANDOM_TEAM_NAMES = [
    "Seoul Dynasty", "Dallas Fuel", "San Francisco Shock", "Shanghai Dragons",
    "London Spitfire", "Atlanta Reign", "Houston Outlaws", "Toronto Defiant",
    "Blackwatch", "Overwatch Strike Team", "Talon Operatives", "Null Sector",
    "Helix Security", "MEKA Squad", "Deadlock Gang", "Shimada Clan",
    "Ironclad Guild", "Vishkar Architects", "Lucio's Revolution",
    "Payload Princesses", "C9 Survivors", "Nanoblade Abusers", "Solo Grav Club",
    "W+M1 Enjoyers", "Backcap Kings", "Diff Delivery Inc.", "Chelas y Clutch",
    "Los Boop", "Support Strike Force", "Ana Sleepers", "Manco Squad",
    "Graviton Gang", "Rialto Rats", "Paseadores de Carga", "Pull & Pray"
]


class _DropTargetPanel(QFrame):
    def __init__(self, team_widget: TeamDisplayWidget):
        super().__init__()
        self._team_widget = team_widget
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        self._team_widget._panel_drag_enter(event)

    def dragMoveEvent(self, event):
        self._team_widget._panel_drag_move(event)

    def dragLeaveEvent(self, event):
        self._team_widget._panel_drag_leave(event)

    def dropEvent(self, event):
        self._team_widget._panel_drop(event)


class TeamDisplayWidget(QWidget):
    """A team panel of proportional player slots with solid esports header."""

    team_name_changed = Signal(str)
    slot_created = Signal(int, int, str)
    slot_renamed = Signal(int, int, str)
    slot_fixed_changed = Signal(int, int, object)
    slot_role_changed = Signal(int, int, object)
    slot_mmr_changed = Signal(int, int, object, int)
    slot_color_changed = Signal(str, object)
    slot_bench = Signal(int, int)
    slot_save = Signal(int, int)
    slot_unsave = Signal(int, int)
    slot_remove = Signal(int, int)
    slot_remove_permanent = Signal(int, int)
    player_drop_requested = Signal(object, int, object)
    reroll_roles = Signal()

    def __init__(self, team_num: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.team_num = team_num
        self._team_name = f"Equipo {self.team_num}"
        self.slot_widgets: list[PlayerSlotWidget] = []
        self._show_roles = True
        self._show_mmr = False
        self._font_size = 14
        self._font_weight = "bold"
        self._text_align = "center"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        is_t1 = (self.team_num == 1)
        team_color = "#00B4FF" if is_t1 else "#FF4444"

        # 1. Header Bar Frame
        self.header_frame = QFrame(self)
        self.header_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_frame.setToolTip("Doble clic o clic derecho para renombrar el equipo")
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(6)

        self.name_label = QLabel(self._team_name, self.header_frame)
        header_layout.addWidget(self.name_label, 1)

        self.header_frame.mouseDoubleClickEvent = lambda e: self._prompt_rename_team() if e.button() == Qt.LeftButton else None
        self.name_label.mouseDoubleClickEvent = lambda e: self._prompt_rename_team() if e.button() == Qt.LeftButton else None

        self.lbl_count = QLabel("0 / 5", self.header_frame)
        header_layout.addWidget(self.lbl_count, 0)

        self.btn_mix_roles = QPushButton("↻ Roles", self.header_frame)
        self.btn_mix_roles.setToolTip("Re-randomizar los roles de este equipo (respeta fijados 🔒)")
        self.btn_mix_roles.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mix_roles.clicked.connect(self.reroll_roles.emit)
        header_layout.addWidget(self.btn_mix_roles, 0)

        self.header_frame.setContextMenuPolicy(Qt.CustomContextMenu)
        self.header_frame.customContextMenuRequested.connect(self._show_header_menu)
        self.name_label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.name_label.customContextMenuRequested.connect(self._show_header_menu)

        layout.addWidget(self.header_frame)

        # 2. Panel Contenedor de Ranuras
        self.panel = _DropTargetPanel(self)
        self.panel.setObjectName(f"teamPanel{self.team_num}")
        self.panel.setProperty("team", str(self.team_num))
        self.slots_layout = QVBoxLayout(self.panel)
        self.slots_layout.setContentsMargins(8, 8, 8, 8)
        self.slots_layout.setSpacing(7)

        layout.addWidget(self.panel, 1)
        self.apply_theme()

    def apply_theme(self):
        t = theme.tokens()
        is_t1 = (self.team_num == 1)
        team_color = "#00B4FF" if is_t1 else "#FF4444"
        r = t.border_radius

        if hasattr(self, "header_frame"):
            border_css = f"border: 1px solid {t.border_subtle}; border-top: 2.5px solid {team_color};" if t.layout_type == "classic" else f"border: none; border-top: 3px solid {team_color};"
            self.header_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {t.bg_surface};
                    {border_css}
                    border-radius: {r}px;
                }}
                QFrame:hover {{
                    background-color: {t.bg_elevated};
                }}
            """)

        if hasattr(self, "name_label"):
            font_disp = t.font_family_display if t.id == "overwatch" else t.font_family
            self.name_label.setStyleSheet(f"""
                QLabel {{
                    font-family: {font_disp};
                    font-size: 16px;
                    font-weight: 900;
                    font-style: {'italic' if t.id == 'overwatch' else 'normal'};
                    color: #FFFFFF;
                    background: transparent;
                    border: none;
                    letter-spacing: 0.8px;
                }}
            """)

        if hasattr(self, "lbl_count"):
            if t.layout_type == "tactical_overwatch":
                self.lbl_count.setStyleSheet(f"""
                    QLabel {{
                        font-family: {t.font_family_display};
                        font-size: 13px;
                        font-weight: 900;
                        font-style: italic;
                        color: {team_color};
                        background-color: rgba({'0, 180, 255' if is_t1 else '255, 68, 68'}, 0.16);
                        border: 1px solid rgba({'0, 180, 255' if is_t1 else '255, 68, 68'}, 0.50);
                        border-radius: 2px;
                        padding: 2px 10px;
                        letter-spacing: 0.8px;
                    }}
                """)
            else:
                self.lbl_count.setStyleSheet(f"""
                    QLabel {{
                        font-size: 11px;
                        font-weight: 800;
                        color: {team_color};
                        background-color: rgba({'0, 180, 255' if is_t1 else '255, 68, 68'}, 0.14);
                        border: 1px solid rgba({'0, 180, 255' if is_t1 else '255, 68, 68'}, 0.40);
                        border-radius: {max(2, r - 2)}px;
                        padding: 2px 8px;
                    }}
                """)

        if hasattr(self, "panel"):
            panel_border = "border: none;" if t.id == "overwatch" else f"border: 1px solid {t.border_subtle};"
            self.panel.setStyleSheet(f"""
                QFrame#teamPanel{self.team_num} {{
                    background-color: {t.bg_app};
                    {panel_border}
                    border-radius: {r}px;
                }}
            """)

        if hasattr(self, "btn_mix_roles"):
            if t.button_secondary_style == "ice_white":
                self.btn_mix_roles.setStyleSheet("""
                    QPushButton {
                        padding: 4px 10px;
                        font-family: "Futura", "Segoe UI", sans-serif;
                        font-size: 11px;
                        font-weight: 800;
                        background-color: #EDF2F7;
                        border: none;
                        border-radius: 2px;
                        color: #151F2E;
                    }
                    QPushButton:hover {
                        background-color: #FFFFFF;
                        border: 1px solid #00F0FF;
                        color: #000000;
                    }
                """)
            else:
                self.btn_mix_roles.setStyleSheet(f"""
                    QPushButton {{
                        padding: 4px 10px;
                        font-size: 11px;
                        font-weight: 700;
                        background-color: {t.bg_elevated};
                        border: 1px solid {t.border_subtle};
                        border-radius: {max(2, r - 2)}px;
                        color: {t.text_primary};
                    }}
                    QPushButton:hover {{
                        background-color: {t.border_medium};
                        border-color: {t.border_medium};
                        color: #FFFFFF;
                    }}
                """)

        if hasattr(self, "slot_widgets"):
            for slot in self.slot_widgets:
                slot._apply_style()

    def _show_header_menu(self, pos):
        menu = QMenu(self)
        act_rename = QAction("✏️ Renombrar equipo...", self)
        act_rename.triggered.connect(self._prompt_rename_team)
        menu.addAction(act_rename)

        act_random = QAction("🎲 Sugerir nombre temático", self)
        act_random.triggered.connect(self._randomize_team_name)
        menu.addAction(act_random)

        menu.exec(QCursor.pos())

    def _prompt_rename_team(self):
        current = self.get_team_name()
        new_name, ok = QInputDialog.getText(
            self.window(),
            f"Renombrar Equipo {self.team_num}",
            "Nuevo nombre para el equipo:",
            text=current,
        )
        if ok and new_name.strip():
            self.set_team_name(new_name.strip())
            self.team_name_changed.emit(self.get_team_name())

    def _randomize_team_name(self):
        name = random.choice(_RANDOM_TEAM_NAMES)
        self.set_team_name(name)
        self.team_name_changed.emit(name)

    @property
    def name_input(self):
        class _InputCompat:
            def __init__(self, target):
                self.t = target
            def setText(self, txt):
                self.t.set_team_name(txt)
            def text(self):
                return self.t.get_team_name()
        return _InputCompat(self)

    def set_team_name(self, name: str):
        self._team_name = name.strip() or f"Equipo {self.team_num}"
        if hasattr(self, "name_label"):
            self.name_label.setText(self._team_name)

    def get_team_name(self) -> str:
        return getattr(self, "_team_name", f"Equipo {self.team_num}")

    def set_font_preferences(
        self,
        size: int,
        weight: str,
        align: str = "center",
        dynamic_font: bool = True,
        role_badge_style: str = "emoji",
        badge_outlines: bool = False
    ):
        self._font_size = size
        self._font_weight = weight
        self._text_align = align
        self._dynamic_font = dynamic_font
        self._role_badge_style = role_badge_style
        self._badge_outlines = badge_outlines
        for w in self.slot_widgets:
            w.set_font_preferences(size, weight, align, dynamic_font, role_badge_style, badge_outlines)

    def set_slots(self, slots: list[Player | None], saved_names: set[str], show_roles: bool, show_mmr: bool = False):
        self._show_roles = show_roles
        self._show_mmr = show_mmr

        while len(self.slot_widgets) < len(slots):
            idx = len(self.slot_widgets)
            w = PlayerSlotWidget(self.team_num, idx, self)
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            w.setMinimumHeight(28)
            w.setMaximumHeight(72)
            w.set_font_preferences(
                getattr(self, "_font_size", 14),
                getattr(self, "_font_weight", "bold"),
                getattr(self, "_text_align", "center"),
                getattr(self, "_dynamic_font", True),
                getattr(self, "_role_badge_style", "emoji"),
                getattr(self, "_badge_outlines", False),
            )
            w.slot_created.connect(lambda name, i=idx: self.slot_created.emit(self.team_num, i, name))
            w.slot_renamed.connect(lambda name, i=idx: self.slot_renamed.emit(self.team_num, i, name))
            w.slot_fixed_changed.connect(lambda f, i=idx: self.slot_fixed_changed.emit(self.team_num, i, f))
            w.slot_role_changed.connect(lambda r, i=idx: self.slot_role_changed.emit(self.team_num, i, r))
            w.slot_mmr_changed.connect(lambda role, mmr, i=idx: self.slot_mmr_changed.emit(self.team_num, i, role, mmr))
            w.slot_color_changed.connect(lambda name, col: self.slot_color_changed.emit(name, col))
            w.slot_bench.connect(lambda i=idx: self.slot_bench.emit(self.team_num, i))
            w.slot_save.connect(lambda i=idx: self.slot_save.emit(self.team_num, i))
            w.slot_unsave.connect(lambda i=idx: self.slot_unsave.emit(self.team_num, i))
            w.slot_remove.connect(lambda i=idx: self.slot_remove.emit(self.team_num, i))
            w.slot_remove_permanent.connect(lambda i=idx: self.slot_remove_permanent.emit(self.team_num, i))
            w.drop_requested.connect(lambda payload, i=idx: self.player_drop_requested.emit(payload, self.team_num, i))
            self.slots_layout.addWidget(w, 1)
            self.slot_widgets.append(w)

        while len(self.slot_widgets) > len(slots):
            w = self.slot_widgets.pop()
            self.slots_layout.removeWidget(w)
            w.deleteLater()

        filled = sum(1 for p in slots if p is not None)
        total = len(slots)

        if hasattr(self, "lbl_count"):
            active_p = [p for p in slots if p is not None]
            if show_mmr and active_p:
                avg = sum(p.get_mmr_for_role(p.role) for p in active_p) / len(active_p)
                self.lbl_count.setText(f"{filled} / {total} · ★ {avg:.1f}")
            else:
                self.lbl_count.setText(f"{filled} / {total}")

        for i, player in enumerate(slots):
            w = self.slot_widgets[i]
            saved = player is not None and player.name.casefold() in saved_names
            w.set_player(player, saved, show_roles, show_mmr)

    def get_players(self) -> list[tuple[str, Role | None, int]]:
        players: list[tuple[str, Role | None, int]] = []
        for w in self.slot_widgets:
            if w._player is not None:
                eff_mmr = w._player.get_mmr_for_role(w._player.role)
                players.append((w._player.name, w._player.role, eff_mmr))
        return players

    def set_show_roles(self, show: bool):
        self._show_roles = show
        for w in self.slot_widgets:
            if w._player is not None:
                w.set_player(w._player, w._saved, show, self._show_mmr)

    def set_show_mmr(self, show: bool):
        self._show_mmr = show
        for w in self.slot_widgets:
            if w._player is not None:
                w.set_player(w._player, w._saved, self._show_roles, show)

    def set_game_mode(self, mode: GameMode):
        pass

    def _panel_drag_enter(self, event):
        if payload_from(event.mimeData()) is None:
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()

    def _panel_drag_move(self, event):
        if payload_from(event.mimeData()) is None:
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()

    def _panel_drag_leave(self, event):
        pass

    def _panel_drop(self, event):
        payload = payload_from(event.mimeData())
        clear_all_drop_highlights()
        if payload is None:
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()
        self.player_drop_requested.emit(payload, self.team_num, None)
'''

FILES = {
    os.path.join("owervach_tmixer", "ui", "widgets", "player_slot.py"): PLAYER_SLOT_CODE,
    os.path.join("owervach_tmixer", "ui", "widgets", "bans_panel.py"): BANS_PANEL_CODE,
    os.path.join("owervach_tmixer", "ui", "widgets", "team_display.py"): TEAM_DISPLAY_CODE,
}

def apply_patch():
    print("=" * 70)
    print("🚀 RESTAURANDO ANATOMÍA ZERO-SHIFT 76px Y ESTABILIDAD VISUAL")
    print("=" * 70)

    for rel_path, content in FILES.items():
        abs_path = os.path.join(BASE_DIR, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content.strip() + "\n")
        print(f"  [OK] Escrito: {rel_path}")

        try:
            py_compile.compile(abs_path, doraise=True)
            print(f"  [OK] Compilado py_compile: {rel_path}")
        except Exception as e:
            print(f"  [FAIL] Error de compilación en {rel_path}: {e}")
            sys.exit(1)

    print("=" * 70)
    print("✅ RESTAURACIÓN COMPLETADA Y VERIFICADA")
    print("=" * 70)

if __name__ == "__main__":
    apply_patch()