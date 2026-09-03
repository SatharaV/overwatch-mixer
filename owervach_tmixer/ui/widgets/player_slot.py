"""Inline-editable player slot card with true-center/left names, borderless micro-badges, and clean drag lifecycle."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QDrag, QFont, QFontMetrics
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
        self.setMinimumHeight(28)
        self.setMaximumHeight(72)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAcceptDrops(True)
        register_slot(self)

        self._setup_ui()

    def _setup_ui(self):
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(10, 4, 10, 4)
        self._layout.setSpacing(6)

        # 1. Left Wing (MMR + Badges)
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
        self._editor.setPlaceholderText("➕")
        self._editor.setClearButtonEnabled(False)
        self._editor.setProperty("transparent", True)
        font = QFont()
        font.setPointSize(12)
        font.setWeight(QFont.Weight.Medium)
        self._editor.setFont(font)
        self._editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self._editor, 1, Qt.AlignVCenter)

        # 3. Right Wing (Role Badge)
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
                self._editor.setPlaceholderText("➕")
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
                            font-size: 9.5px; font-weight: 900; color: #FFAA00;
                            background-color: {bg_css};
                            {border_css}
                            border-radius: 5px; padding: 0px 4px;
                        }}
                    """)
                    self.lbl_mmr_badge.show()
                else:
                    self.lbl_mmr_badge.hide()

                icons = []
                if saved:
                    icons.append("⭐")
                if player.fixed_team:
                    icons.append("🔒")

                icon_str = " ".join(icons)
                self.lbl_icons.setText(icon_str)
                self.lbl_icons.setStyleSheet("font-size: 11px; color: #E2E6F0; background: transparent; border: none;")

                if getattr(self, "_text_align", "center") == "left":
                    # Reserva de espacio fija de 26px para mantener la columna simétrica
                    self.lbl_icons.setFixedWidth(36 if len(icons) > 1 else 26)
                    self.lbl_icons.setFixedHeight(22)
                    self.lbl_icons.show()
                else:
                    if icons:
                        self.lbl_icons.setFixedWidth(34 if len(icons) > 1 else 18)
                        self.lbl_icons.setFixedHeight(18)
                        self.lbl_icons.show()
                    else:
                        self.lbl_icons.hide()

                if show_roles and player.role:
                    r_color = ROLE_COLOR.get(player.role, "#AAA")
                    r_bg = ROLE_BG.get(player.role, "rgba(255, 255, 255, 0.08)")
                    r_emoji = ROLE_EMOJI.get(player.role, "")

                    style = getattr(self, "_role_badge_style", "emoji")
                    if style == "emoji":
                        badge_txt = r_emoji
                        self.lbl_role_badge.setFixedWidth(24)
                        b_padding = "0px 2px"
                    elif style == "initial":
                        badge_txt = f"{r_emoji} {player.role.value[0].upper()}"
                        self.lbl_role_badge.setFixedWidth(34)
                        b_padding = "0px 3px"
                    else:  # "full"
                        badge_txt = f"{r_emoji} {player.role.value.upper()}"
                        self.lbl_role_badge.setMinimumWidth(56)
                        self.lbl_role_badge.setMaximumWidth(78)
                        b_padding = "0px 5px"

                    self.lbl_role_badge.setText(badge_txt)
                    self.lbl_role_badge.setAlignment(Qt.AlignCenter)
                    if style == "emoji":
                        self.lbl_role_badge.setFixedSize(26, 22)
                        font_px = "12px"
                        pad_px = "0px"
                    elif style == "initial":
                        self.lbl_role_badge.setFixedHeight(22)
                        self.lbl_role_badge.setMinimumWidth(36)
                        font_px = "10px"
                        pad_px = "0px 4px"
                    else:
                        self.lbl_role_badge.setFixedHeight(22)
                        self.lbl_role_badge.setMinimumWidth(62)
                        font_px = "9.5px"
                        pad_px = "0px 6px"

                    use_outline = getattr(self, "_badge_outlines", False)
                    border_css = f"border: 1px solid {r_color};" if use_outline else "border: none;"
                    self.lbl_role_badge.setStyleSheet(f"""
                        QLabel {{
                            font-size: {font_px}; font-weight: 900; color: {r_color};
                            background-color: {r_bg};
                            {border_css}
                            border-radius: 5px; padding: {pad_px};
                        }}
                    """)
                    self.lbl_role_badge.show()
                else:
                    self.lbl_role_badge.hide()

                self._decor.setText(_indicators(player, self._saved, self._show_roles, self._show_mmr))
        finally:
            self._suppress = False
        self._apply_alignment_layout()
        self._apply_style()

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
        self._font_size = max(10, min(20, size))
        self._font_weight = weight
        self._text_align = align
        self._dynamic_font = dynamic_font
        self._role_badge_style = role_badge_style
        self._badge_outlines = badge_outlines
        qweight = (
            QFont.Weight.Bold
            if weight == "bold"
            else (QFont.Weight.DemiBold if weight == "medium" else QFont.Weight.Normal)
        )
        font = self._editor.font()
        font.setPointSize(self._font_size)
        font.setWeight(qweight)
        self._editor.setFont(font)
        self._apply_alignment_layout()
        self._apply_style()
        self._update_editor_style()
        self._refresh_badges()

    def _refresh_badges(self):
        if self._player is None:
            self.lbl_mmr_badge.hide()
            self.lbl_role_badge.hide()
            return

        # 1. MMR / Habilidad Naranjita
        if self._show_mmr:
            mmr_val = self._player.get_mmr_for_role(self._player.role)
            self.lbl_mmr_badge.setText(f"⚡{mmr_val}")
            self.lbl_mmr_badge.setAlignment(Qt.AlignCenter)
            self.lbl_mmr_badge.setFixedHeight(22)
            self.lbl_mmr_badge.setMinimumWidth(30)
            use_outline = getattr(self, "_badge_outlines", False)
            border_css = "border: 1px solid #FFAA00;" if use_outline else "border: none;"
            bg_css = "rgba(255, 170, 0, 0.12)" if use_outline else "rgba(255, 170, 0, 0.16)"
            self.lbl_mmr_badge.setStyleSheet(f"""
                QLabel {{
                    font-size: 9.5px; font-weight: 900; color: #FFAA00;
                    background-color: {bg_css};
                    {border_css}
                    border-radius: 5px; padding: 0px 4px;
                }}
            """)
            self.lbl_mmr_badge.show()
        else:
            self.lbl_mmr_badge.hide()

        # 2. Insignia de Rol
        if self._show_roles and self._player.role:
            r_color = ROLE_COLOR.get(self._player.role, "#AAA")
            r_bg = ROLE_BG.get(self._player.role, "rgba(255, 255, 255, 0.08)")
            r_emoji = ROLE_EMOJI.get(self._player.role, "")
            style = getattr(self, "_role_badge_style", "emoji")
            if style == "emoji":
                badge_txt = r_emoji
                self.lbl_role_badge.setFixedSize(26, 22)
                font_px = "12px"
                pad_px = "0px"
            elif style == "initial":
                badge_txt = f"{r_emoji} {self._player.role.value[0].upper()}"
                self.lbl_role_badge.setFixedHeight(22)
                self.lbl_role_badge.setMinimumWidth(36)
                font_px = "10px"
                pad_px = "0px 4px"
            else:
                badge_txt = f"{r_emoji} {self._player.role.value.upper()}"
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
        else:
            self.lbl_role_badge.hide()

    def _update_editor_style(self):
        if not hasattr(self, "_editor"):
            return

        special = self._player is not None and is_special_player_name(self._player.name)
        fixed = self._player is not None and self._player.is_fixed
        custom_color = getattr(self._player, "custom_color", None) if self._player else None

        if special:
            name_color = "#A4E062"
        elif custom_color:
            name_color = custom_color
        else:
            name_color = theme.accent_light() if fixed else "#E2E6F0"

        css_weight = "800" if getattr(self, "_font_weight", "bold") == "bold" else (
            "600" if getattr(self, "_font_weight", "medium") == "medium" else "500"
        )

        if not getattr(self, "_dynamic_font", True):
            target_size = getattr(self, "_font_size", 13)
        else:
            h = max(28, min(72, self.height()))
            # Escalado elástico: 28px -> 11px | 50px -> 15px | 72px -> 19px
            base_size = int(11 + (h - 28) * (19 - 11) / (72 - 28))
            base_size = max(11, min(20, base_size))

            avail_w = max(40, self._editor.width() - 8)
            f = QFont("Segoe UI", base_size)
            fm = QFontMetrics(f)
            name_text = self._editor.text().strip() or (self._player.name if self._player else "➕")
            text_w = fm.horizontalAdvance(name_text)

            size = base_size
            while text_w > avail_w and size > 10:
                size -= 1
                f = QFont("Segoe UI", size)
                fm = QFontMetrics(f)
                text_w = fm.horizontalAdvance(name_text)

            target_size = max(10, size)

        self._editor.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                border: none;
                padding: 0px 4px;
                color: {name_color};
                font-size: {target_size}px;
                font-weight: {css_weight};
            }}
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_editor_style()

    def _apply_alignment_layout(self):
        while self._layout.count():
            self._layout.takeAt(0)

        self._layout.setContentsMargins(8, 2, 8, 2)
        self._layout.setSpacing(6)
        self._editor.setMinimumWidth(40)

        if self._text_align == "left":
            # MODO IZQUIERDA (SATHARA MASTER): [Estrella / Reserva] [Jugador] [Espacio libre] [Habilidad] [Rol]
            self._editor.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._layout.addWidget(self.lbl_icons, 0, Qt.AlignVCenter)
            self._layout.addWidget(self._editor, 0, Qt.AlignVCenter)
            self._layout.addStretch(1)
            self._layout.addWidget(self.lbl_mmr_badge, 0, Qt.AlignVCenter)
            self._layout.addWidget(self.lbl_role_badge, 0, Qt.AlignVCenter)
        else:
            # MODO CENTRADO (DEFAULT): [Rol] [Candado / Estrella] [Nombre Centrado] [MMR]
            self._editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._layout.addWidget(self.lbl_role_badge, 0, Qt.AlignVCenter)
            self._layout.addWidget(self.lbl_icons, 0, Qt.AlignVCenter)
            self._layout.addWidget(self._editor, 1, Qt.AlignVCenter)
            self._layout.addWidget(self.lbl_mmr_badge, 0, Qt.AlignVCenter)
    def _apply_style(self):
        special = self._player is not None and is_special_player_name(self._player.name)
        fixed = self._player is not None and self._player.is_fixed
        custom_color = getattr(self._player, "custom_color", None) if self._player else None
        is_t1 = (self.team_num == 1)

        team_accent = "#00B4FF" if is_t1 else "#FF4444"

        if special:
            border = "#48781B"
            background = "#1D261A"
            name_color = "#A4E062"
            hover_border = "#61ab02"
            hover_bg = "#263622"
        elif custom_color:
            border = custom_color
            background = "#181A22"
            name_color = custom_color
            hover_border = custom_color
            hover_bg = "#222735"
        else:
            border = theme.accent() if fixed else "#282A33"
            background = "#17181D"
            name_color = theme.accent_light() if fixed else "#E2E6F0"
            hover_border = team_accent
            hover_bg = "#202532"

        self._apply_glow(special)
        self._update_editor_style()
        css_weight = "800" if self._font_weight == "bold" else ("600" if self._font_weight == "medium" else "500")

        self.setStyleSheet(f"""
            #playerSlot {{
                background-color: {background};
                border: 1px solid {border};
                border-radius: 5px;
            }}
            #playerSlot:hover, #playerSlot[hovered="true"] {{
                background-color: {hover_bg};
                border: 1px solid {hover_border};
                border-radius: 5px;
            }}
            #playerSlot[dropTarget="true"] {{
                border: 1px solid {theme.accent()} !important;
                background-color: {theme.accent_rgba(0.20)} !important;
                border-radius: 5px;
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
    if saved:
        parts.append("⭐")
    if player.fixed_team:
        parts.append("🔒")
    if show_roles and player.role:
        emoji = ROLE_EMOJI.get(player.role, "")
        parts.append(f"{emoji}{player.role.value.upper()}")
    return " ".join(parts)
