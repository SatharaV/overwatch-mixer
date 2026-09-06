"""Inline-editable player slot card with true-center/left names, SVG role badges, and clean drag lifecycle."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QDrag, QFont, QFontMetrics, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QWidget,
)

from owervach_tmixer.core.models import Player, Role
from owervach_tmixer.core.special_player import (
    SPECIAL_GLOW,
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
    """Renders and caches crisp vector role icons from assets SVGs."""
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

        # Tinting pass
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
    """Esports Stat Card player cell with dynamic Left/Center alignment and clean glow lifecycle."""

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
        self._font_size = 15

        self._font_weight = "bold"
        self._text_align = "center"
        self._dynamic_font = True
        self._role_badge_style = "emoji"
        self._badge_outlines = False

        self.setObjectName("playerSlot")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # Mayor altura para permitir una tipografía descansada y legible
        self.setMinimumHeight(36)
        self.setMaximumHeight(74)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAcceptDrops(True)
        register_slot(self)

        self._setup_ui()

    def _setup_ui(self):
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(10, 4, 10, 4)
        self._layout.setSpacing(6)

        # 1. Left Wing (MMR + Badges) - 76px Zero-Shift
        self.left_wing = QWidget(self)
        self.left_wing.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.left_layout = QHBoxLayout(self.left_wing)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(4)
        self.left_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.lbl_mmr_badge = QLabel(self.left_wing)
        self.lbl_mmr_badge.setAlignment(Qt.AlignCenter)
        self.left_layout.addWidget(self.lbl_mmr_badge)

        self.lbl_icons = QLabel(self.left_wing)
        self.lbl_icons.setAlignment(Qt.AlignCenter)
        self.lbl_icons.setFixedWidth(18)
        self.left_layout.addWidget(self.lbl_icons)

        self._layout.addWidget(self.left_wing, 0, Qt.AlignLeft | Qt.AlignVCenter)

        # 2. Name Editor
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

        # 3. Right Wing (Role Badge) - 76px Zero-Shift
        self.right_wing = QWidget(self)
        self.right_wing.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.right_layout = QHBoxLayout(self.right_wing)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(4)
        self.right_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.lbl_role_badge = QLabel(self.right_wing)
        self.lbl_role_badge.setAlignment(Qt.AlignCenter)
        self.right_layout.addWidget(self.lbl_role_badge)

        self._layout.addWidget(self.right_wing, 0, Qt.AlignRight | Qt.AlignVCenter)

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

                width_needed = max(18, 14 * len(icons) + 4)
                if getattr(self, "_text_align", "center") == "left":
                    self.lbl_icons.setFixedWidth(max(26, width_needed))
                    self.lbl_icons.setFixedHeight(22)
                    self.lbl_icons.show()
                else:
                    if icons:
                        self.lbl_icons.setFixedWidth(width_needed)
                        self.lbl_icons.setFixedHeight(18)
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

        # Renderizado vectorial SVG (prioritario si el tema usa franja lateral o el usuario pide SVG)
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

        # Fallback estándar / Obsidian / Material
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
        self._font_size = max(11, min(22, size))
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

        css_weight = "800" if getattr(self, "_font_weight", "bold") == "bold" else (
            "600" if getattr(self, "_font_weight", "medium") == "medium" else "500"
        )

        font_name = t.font_family.split(",")[0].strip(' "\'')

        if not getattr(self, "_dynamic_font", True):
            target_size = max(12, getattr(self, "_font_size", 14))
        else:
            h = max(36, min(74, self.height()))
            # Escalado generoso: 36px -> 14px | 50px -> 16px | 74px -> 20px
            base_size = int(14 + (h - 36) * (20 - 14) / (74 - 36))
            base_size = max(13, min(22, base_size))

            avail_w = max(40, self._editor.width() - 8)
            f = QFont(font_name, base_size)
            fm = QFontMetrics(f)
            name_text = self._editor.text().strip() or (self._player.name if self._player else "➕")
            text_w = fm.horizontalAdvance(name_text)

            size = base_size
            while text_w > avail_w and size > 11:
                size -= 1
                f = QFont(font_name, size)
                fm = QFontMetrics(f)
                text_w = fm.horizontalAdvance(name_text)

            target_size = max(11, size)

        cache_key = (name_color, target_size, css_weight, font_name)
        if getattr(self, "_cached_editor_key", None) == cache_key:
            return
        self._cached_editor_key = cache_key

        ph_family = t.font_family_display if t.id == "overwatch" else t.font_family
        ph_style = "italic" if t.id == "overwatch" else "normal"
        ph_spacing = "2px" if t.id == "overwatch" else "0px"
        self._editor.setStyleSheet(f"""
            QLineEdit {{
                font-family: {t.font_family};
                background-color: transparent;
                border: none;
                padding: 0px 4px;
                color: {name_color};
                font-size: {target_size}px;
                font-weight: {css_weight};
            }}
            QLineEdit::placeholder {{
                color: #5F738E;
                font-family: {ph_family};
                font-size: {target_size}px;
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
            # En Overwatch las ranuras NO tienen outlines inactivos: son placas sólidas limpias
            if t.id == "overwatch":
                border = t.accent if fixed else "transparent"
                background = t.bg_surface
                name_color = t.text_primary
                hover_border = "#00F0FF"  # Cian Neón reactivo en hover
                hover_bg = t.bg_elevated
            else:
                border = t.accent if fixed else t.border_subtle
                background = t.bg_surface
                name_color = t.accent_light() if fixed else t.text_primary
                hover_border = team_accent
                hover_bg = t.bg_elevated

        self._apply_glow(special)
        self._update_editor_style()
        if self._player:
            self._refresh_role_badge(self._player)

        css_weight = "800" if self._font_weight == "bold" else ("600" if self._font_weight == "medium" else "500")

        # En Overwatch se proyecta la franja lateral de color de bando (Azul vs Rojo) de la Captura 1
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
                font-weight: {css_weight};
            }}
        """)

    def _apply_glow(self, special: bool):
        if special:
            if not isinstance(self._editor.graphicsEffect(), QGraphicsDropShadowEffect):
                glow = QGraphicsDropShadowEffect(self._editor)
                glow.setColor(QColor(SPECIAL_GLOW))
                glow.setBlurRadius(14)
                glow.setOffset(0, 0)
                self._editor.setGraphicsEffect(glow)
        else:
            if self._editor.graphicsEffect() is not None:
                self._editor.setGraphicsEffect(None)


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
