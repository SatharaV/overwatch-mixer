"""Obsidian Esports Glassmorphic Toasts and Sentient AI Top-HUD Holographic Flyouts."""

from __future__ import annotations

import time
from typing import Optional

from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QObject,
    QPoint,
    QPropertyAnimation,
    Qt,
    QTimer,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.ui.styles import theme


class AITransmissionFlyout(QFrame):
    """Futuristic holographic Top-HUD card for sentient AI personality transmissions."""

    def __init__(self, message: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("aiFlyout")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._is_paused = False

        self.setStyleSheet("""
            QFrame#aiFlyout {
                background-color: rgba(10, 14, 20, 0.96);
                border: 1px solid rgba(97, 171, 2, 0.45);
                border-top: 2.5px solid #61ab02;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 10, 18, 12)
        layout.setSpacing(5)

        # Header Bar: Telemetry Status
        header = QHBoxLayout()
        header.setSpacing(6)

        lbl_sys = QLabel("🤖  [ PROTOCOLO IA // SATHARA CORE ]", self)
        lbl_sys.setStyleSheet("""
            QLabel {
                color: #61ab02;
                font-size: 9.5px;
                font-weight: 900;
                letter-spacing: 1.2px;
                background: transparent;
            }
        """)
        header.addWidget(lbl_sys)
        header.addStretch()

        lbl_status = QLabel("🟢 EN LÍNEA", self)
        lbl_status.setStyleSheet("""
            QLabel {
                color: #A3F558;
                font-size: 8.5px;
                font-weight: 800;
                background-color: rgba(97, 171, 2, 0.16);
                border: 1px solid rgba(97, 171, 2, 0.35);
                border-radius: 3px;
                padding: 1px 5px;
            }
        """)
        header.addWidget(lbl_status)
        layout.addLayout(header)

        # Clean AI message body
        clean_msg = message
        for pfx in ("🤖 [Sistema]:", "[Sistema]:", "🤖", "✨", "👑"):
            if clean_msg.startswith(pfx):
                clean_msg = clean_msg[len(pfx):].strip()

        self.lbl_text = QLabel(clean_msg, self)
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setStyleSheet("""
            QLabel {
                color: #F0FDF4;
                font-size: 12.5px;
                font-weight: 700;
                line-height: 1.4;
                background: transparent;
                letter-spacing: 0.2px;
            }
        """)
        layout.addWidget(self.lbl_text)

        # Dimensiones de lectura
        self.setFixedWidth(min(520, max(360, len(clean_msg) * 7 + 80)))
        self.adjustSize()

        # Resplandor esmeralda inicial
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setColor(QColor("#61ab02"))
        self.glow.setBlurRadius(28)
        self.glow.setOffset(0, 0)
        self.setGraphicsEffect(self.glow)

    def enterEvent(self, event):
        self._is_paused = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_paused = False
        super().leaveEvent(event)


class Toast(QFrame):
    """A sleek Glassmorphic standard toast pill for general operations."""

    def __init__(self, message: str, kind: str = "info", parent: QWidget | None = None):
        super().__init__(parent)
        self.kind = kind
        self.message = message
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        acc = theme.accent()
        themes = {
            "success": {"accent": "#00E599", "glow": "#00E599", "icon": "✅"},
            "warning": {"accent": "#FFB020", "glow": "#FFB020", "icon": "⚠️"},
            "danger": {"accent": "#FF4D6D", "glow": "#FF4D6D", "icon": "❌"},
            "error": {"accent": "#FF4D6D", "glow": "#FF4D6D", "icon": "❌"},
            "info": {"accent": acc if acc != "#61ab02" else "#00B4FF", "glow": "#00B4FF", "icon": "ℹ️"},
        }

        theme_data = themes.get(kind, themes["info"])
        accent_color = theme_data["accent"]
        glow_color = theme_data["glow"]

        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(14, 16, 22, 0.94);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-left: 3px solid {accent_color};
                border-radius: 18px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 7, 18, 7)
        layout.setSpacing(8)

        self.lbl_icon = QLabel(theme_data["icon"])
        self.lbl_icon.setStyleSheet("font-size: 12px; background: transparent; border: none;")
        layout.addWidget(self.lbl_icon)

        clean_msg = message
        for pfx in ("✅", "⚠️", "❌", "✨", "ℹ️", "⚖️", "⭐", "🗺️", "🎭", "📦", "🔄", "☢️", "📤", "🎲", "✏️", "🗑️"):
            if clean_msg.startswith(pfx):
                clean_msg = clean_msg[len(pfx):].strip()
                break

        self.lbl_text = QLabel(clean_msg)
        self.lbl_text.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 11.5px;
                font-weight: 700;
                background: transparent;
                border: none;
                letter-spacing: 0.2px;
            }
        """)
        layout.addWidget(self.lbl_text)
        self.adjustSize()

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setColor(QColor(glow_color))
        self.shadow.setBlurRadius(16)
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)


# Compatibility alias
ToastItem = Toast


class ToastManager(QObject):
    """Orchestrates Bottom Toasts and Sentient AI Top-HUD Flyouts seamlessly."""

    MAX_ACTIVE_TOASTS = 2

    def __init__(self, parent_window: QWidget):
        super().__init__(parent_window)
        self.window = parent_window
        self._active_toasts: list[Toast] = []
        self._current_ai_flyout: Optional[AITransmissionFlyout] = None
        self._last_messages: dict[str, float] = {}

        if self.window:
            self.window.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched == self.window and event.type() == QEvent.Type.Resize:
            self._reposition_toasts(animated=False)
            self._reposition_ai_flyout()
        return super().eventFilter(watched, event)

    def show_toast(self, message: str, kind: str = "info", duration_ms: int = 2800):
        if not self.window:
            return

        # Notificación Top-HUD para mensajes especiales o con prefijo IA
        if kind == "special" or message.startswith("🤖"):
            self.show_ai_flyout(message)
            return

        now = time.time()
        if message in self._last_messages and (now - self._last_messages[message]) < 1.6:
            return
        self._last_messages[message] = now

        while len(self._active_toasts) >= self.MAX_ACTIVE_TOASTS:
            oldest = self._active_toasts.pop(0)
            self._fast_dismiss_toast(oldest)

        toast = Toast(message, kind, self.window)
        self._active_toasts.append(toast)
        toast.adjustSize()

        win_w = self.window.width()
        win_h = self.window.height()
        tw = toast.width()
        th = toast.height()
        target_x = (win_w - tw) // 2
        target_y = win_h - 40 - th

        toast.move(target_x, target_y + 14)
        toast.show()
        toast.raise_()

        anim_pos = QPropertyAnimation(toast, b"pos", toast)
        anim_pos.setDuration(220)
        anim_pos.setStartValue(QPoint(target_x, target_y + 14))
        anim_pos.setEndValue(QPoint(target_x, target_y))
        anim_pos.setEasingCurve(QEasingCurve.Type.OutBack)
        anim_pos.start()

        self._reposition_toasts(animated=True)
        QTimer.singleShot(duration_ms, lambda: self._dismiss_toast(toast))

    def show_ai_flyout(self, message: str, custom_duration_ms: int | None = None):
        """Displays the prominent sentient AI transmission at the Top-Center."""
        if not self.window:
            return

        if self._current_ai_flyout is not None:
            try:
                self._current_ai_flyout.deleteLater()
            except Exception:
                pass
            self._current_ai_flyout = None

        flyout = AITransmissionFlyout(message, self.window)
        self._current_ai_flyout = flyout
        flyout.adjustSize()

        win_w = self.window.width()
        fw = flyout.width()
        target_x = (win_w - fw) // 2
        target_y = 56

        flyout.move(target_x, target_y - 20)
        flyout.show()
        flyout.raise_()

        anim_pos = QPropertyAnimation(flyout, b"pos", flyout)
        anim_pos.setDuration(280)
        anim_pos.setStartValue(QPoint(target_x, target_y - 20))
        anim_pos.setEndValue(QPoint(target_x, target_y))
        anim_pos.setEasingCurve(QEasingCurve.Type.OutBack)
        anim_pos.start()

        calc_duration = max(4600, min(6500, len(message) * 70))
        duration = custom_duration_ms or calc_duration

        self._schedule_ai_dismiss(flyout, duration)

    def _schedule_ai_dismiss(self, flyout: AITransmissionFlyout, remaining_ms: int):
        def _check_and_dismiss():
            if flyout is not self._current_ai_flyout:
                return
            if flyout._is_paused:
                QTimer.singleShot(500, _check_and_dismiss)
                return
            self._dismiss_ai_flyout(flyout)

        QTimer.singleShot(remaining_ms, _check_and_dismiss)

    def _dismiss_ai_flyout(self, flyout: AITransmissionFlyout):
        if flyout is not self._current_ai_flyout:
            return
        self._current_ai_flyout = None

        effect = QGraphicsOpacityEffect(flyout)
        flyout.setGraphicsEffect(effect)
        anim_fade = QPropertyAnimation(effect, b"opacity", flyout)
        anim_fade.setDuration(300)
        anim_fade.setStartValue(1.0)
        anim_fade.setEndValue(0.0)
        anim_fade.setEasingCurve(QEasingCurve.Type.InQuad)
        anim_fade.finished.connect(flyout.deleteLater)
        anim_fade.start()

    def _fast_dismiss_toast(self, toast: Toast):
        try:
            toast.deleteLater()
        except Exception:
            pass

    def _dismiss_toast(self, toast: Toast):
        if toast not in self._active_toasts:
            return
        self._active_toasts.remove(toast)

        effect = QGraphicsOpacityEffect(toast)
        toast.setGraphicsEffect(effect)
        anim_fade = QPropertyAnimation(effect, b"opacity", toast)
        anim_fade.setDuration(240)
        anim_fade.setStartValue(1.0)
        anim_fade.setEndValue(0.0)
        anim_fade.setEasingCurve(QEasingCurve.Type.InQuad)
        anim_fade.finished.connect(toast.deleteLater)
        anim_fade.start()

        self._reposition_toasts(animated=True)

    def _reposition_ai_flyout(self):
        if self._current_ai_flyout and self.window:
            fw = self._current_ai_flyout.width()
            target_x = (self.window.width() - fw) // 2
            self._current_ai_flyout.move(target_x, 56)
            self._current_ai_flyout.raise_()

    def _reposition_toasts(self, animated: bool = True):
        if not self.window:
            return

        margin_bottom = 40
        spacing = 8
        win_w = self.window.width()
        win_h = self.window.height()
        curr_y = win_h - margin_bottom

        for toast in reversed(self._active_toasts):
            toast.adjustSize()
            tw = toast.width()
            th = toast.height()
            x = (win_w - tw) // 2
            curr_y -= th
            new_target = QPoint(x, curr_y)

            toast.raise_()
            if animated and toast.pos() != new_target:
                anim = QPropertyAnimation(toast, b"pos", toast)
                anim.setDuration(180)
                anim.setStartValue(toast.pos())
                anim.setEndValue(new_target)
                anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                anim.start()
            else:
                toast.move(new_target)

            curr_y -= spacing
