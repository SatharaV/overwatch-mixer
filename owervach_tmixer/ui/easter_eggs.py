"""Obsidian Easter Egg & Sentient AI Engine with strict modular presence gating."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QEasingCurve, QObject, QPoint, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QWidget

from owervach_tmixer.core.special_player import (
    SATHARA_TRAIT,
    SPECIAL_GLOW,
    SPECIAL_PROFILES,
    PlayerTrait,
    get_player_trait,
    is_special_player_name,
)

if TYPE_CHECKING:
    from owervach_tmixer.ui.main_window import MainWindow

_creator_drag_toast: Optional[QWidget] = None
_last_global_ai_time: float = 0.0
_last_trinity_ban_time: float = 0.0
_spam_clicks_count: int = 0
_last_click_instant: float = 0.0
_last_drag_warn_time: float = 0.0
_action_cooldowns: dict[str, float] = {}
_last_used_quotes: dict[str, str] = {}

DRAG_WARNINGS = [
    "⚠️ Cuidado al manipular al Creador... el código fuente es sensible.",
    "⚠️ Entidad Suprema en movimiento. Manéjese con respeto.",
    "⚠️ Manipulando al Desarrollador... Calculando trayectoria perfecta.",
    "⚠️ Estabilidad del sistema comprometida al mover al Arquitecto.",
]


def _pick_variant(pool: list[str], category_key: str) -> str:
    if not pool:
        return ""
    if len(pool) == 1:
        return pool[0]

    last = _last_used_quotes.get(category_key)
    candidates = [q for q in pool if q != last]
    if not candidates:
        candidates = pool

    chosen = random.choice(candidates)
    _last_used_quotes[category_key] = chosen
    return chosen


def is_sathara_in_match(window: MainWindow | None) -> bool:
    """True únicamente si Sathara está en un equipo o en la Zona de Espera."""
    if not window:
        return False

    roster = getattr(window, "_roster", None) or (
        getattr(window, "roster_controller", None).roster if hasattr(window, "roster_controller") else None
    )
    if roster:
        for p in roster.active_players():
            if p and is_special_player_name(p.name):
                return True
        for p in roster.bench:
            if p and is_special_player_name(p.name):
                return True

    return False


def is_sathara_in_tier(window: MainWindow | None) -> bool:
    """True únicamente si Sathara está colocado en una fila activa del Tier Maker."""
    if not window:
        return False

    tier_maker = getattr(window, "tier_maker", None)
    if tier_maker and hasattr(tier_maker, "rows"):
        for r in tier_maker.rows:
            for c in getattr(r, "cards", []):
                if getattr(c, "kind", "") == "player" and is_special_player_name(getattr(c, "item_name", "")):
                    return True

    return False


def is_sathara_active(window: MainWindow | None) -> bool:
    """True si Sathara está presente en la partida o en el Tier Maker (nunca si solo está en guardados)."""
    return is_sathara_in_match(window) or is_sara_in_tier_check(window)


def is_sara_in_tier_check(window: MainWindow | None) -> bool:
    return is_sathara_in_tier(window)


def notify_special_drag_start(window: QWidget | None):
    global _creator_drag_toast, _last_drag_warn_time
    now = time.time()
    if not window or (now - _last_drag_warn_time) < 4.0 or random.random() > 0.55:
        return

    _last_drag_warn_time = now

    if _creator_drag_toast is not None:
        try:
            _creator_drag_toast.deleteLater()
        except Exception:
            pass
        _creator_drag_toast = None

    banner = QFrame(window)
    banner.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    banner.setStyleSheet("""
        QFrame {
            background-color: rgba(10, 18, 12, 0.95);
            border: 1.5px solid #61ab02;
            border-radius: 20px;
        }
    """)
    b_layout = QHBoxLayout(banner)
    b_layout.setContentsMargins(18, 8, 20, 8)
    b_layout.setSpacing(8)

    msg_text = _pick_variant(DRAG_WARNINGS, "drag_warn")
    lbl = QLabel(msg_text, banner)
    lbl.setStyleSheet("""
        QLabel {
            color: #C2F87A;
            font-size: 12px;
            font-weight: 800;
            background: transparent;
            border: none;
            letter-spacing: 0.3px;
        }
    """)
    b_layout.addWidget(lbl)
    banner.adjustSize()

    glow = QGraphicsDropShadowEffect(banner)
    glow.setColor(QColor("#61ab02"))
    glow.setBlurRadius(24)
    glow.setOffset(0, 0)
    banner.setGraphicsEffect(glow)

    w = window.width()
    h = window.height()
    target_x = (w - banner.width()) // 2
    target_y = h - 145

    banner.move(target_x, target_y + 10)
    banner.show()
    banner.raise_()

    anim_pos = QPropertyAnimation(banner, b"pos", banner)
    anim_pos.setDuration(220)
    anim_pos.setStartValue(QPoint(target_x, target_y + 10))
    anim_pos.setEndValue(QPoint(target_x, target_y))
    anim_pos.setEasingCurve(QEasingCurve.Type.OutBack)
    anim_pos.start()

    _creator_drag_toast = banner


def notify_special_drag_end():
    global _creator_drag_toast
    if _creator_drag_toast is None:
        return

    banner = _creator_drag_toast

    def _start_fade():
        if banner:
            effect = QGraphicsOpacityEffect(banner)
            banner.setGraphicsEffect(effect)
            anim = QPropertyAnimation(effect, b"opacity", banner)
            anim.setDuration(280)
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            anim.setEasingCurve(QEasingCurve.Type.InQuad)
            anim.finished.connect(banner.deleteLater)
            anim.start()

    QTimer.singleShot(1400, _start_fade)
    _creator_drag_toast = None


@dataclass
class EggContext:
    window: Optional[MainWindow] = None
    player_name: str = ""
    egg_count: int = 0

    def special_slots(self) -> list:
        if self.window is None:
            return []
        slots = []
        for team_widget in (
            getattr(self.window.match_display, "team1_widget", None),
            getattr(self.window.match_display, "team2_widget", None),
        ):
            if not team_widget:
                continue
            for w in getattr(team_widget, "slot_widgets", []):
                if getattr(w, "_player", None) and is_special_player_name(w._player.name):
                    slots.append(w)
        return slots


class EasterEgg:
    id: str = "base"
    def trigger(self, ctx: EggContext | None):
        pass


class DetectedEgg(EasterEgg):
    id = "detected"
    def trigger(self, ctx: EggContext | None):
        if ctx and ctx.window and hasattr(ctx.window, "show_toast"):
            quote = _pick_variant(SATHARA_TRAIT.entrance_quotes, "entrance")
            ctx.self._dispatch_ai_quote(quote, window)


class ChosenEgg(EasterEgg):
    id = "chosen"
    def trigger(self, ctx: EggContext | None):
        if ctx and ctx.window and hasattr(ctx.window, "show_toast"):
            quote = _pick_variant(SATHARA_TRAIT.entrance_quotes, "entrance")
            ctx.self._dispatch_ai_quote(quote, window)


class OverdriveEgg(EasterEgg):
    id = "again"
    def trigger(self, ctx: EggContext | None):
        if ctx and ctx.window and hasattr(ctx.window, "show_toast"):
            quote = _pick_variant(SATHARA_TRAIT.entrance_quotes, "entrance")
            ctx.self._dispatch_ai_quote(quote, window)


class RandomizerEgg(EasterEgg):
    id = "randomizer"
    def trigger(self, ctx: EggContext | None):
        if ctx and ctx.window and hasattr(ctx.window, "show_toast"):
            quote = _pick_variant(SATHARA_TRAIT.entrance_quotes, "entrance")
            ctx.self._dispatch_ai_quote(quote, window)


class CrownEgg(EasterEgg):
    id = "crown"
    def trigger(self, ctx: EggContext | None):
        if ctx and ctx.window and hasattr(ctx.window, "show_toast"):
            quote = _pick_variant(SATHARA_TRAIT.entrance_quotes, "entrance")
            ctx.self._dispatch_ai_quote(quote, window)


DEFAULT_EGGS: list[EasterEgg] = [
    DetectedEgg(),
    ChosenEgg(),
    OverdriveEgg(),
    RandomizerEgg(),
    CrownEgg(),
]


class EasterEggManager(QObject):
    """Manages lobby entrances, sentient comments, and presence-gated interactions."""

    def __init__(
        self,
        eggs: list[EasterEgg] | None = None,
        rng: random.Random | None = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.eggs: list[EasterEgg] = eggs if eggs is not None else list(DEFAULT_EGGS)
        self._rng: random.Random = rng if rng is not None else random.Random()
        self.trigger_count: int = 0
        self.is_triggered: bool = False
        self.chosen_id: str | None = None

    @property
    def available_egg_ids(self) -> tuple[str, ...]:
        return tuple(egg.id for egg in self.eggs)

    def _check_cooldown(self, action_key: str, cooldown_secs: float) -> bool:
        now = time.time()
        last = _action_cooldowns.get(action_key, 0.0)
        if now - last < cooldown_secs:
            return False
        _action_cooldowns[action_key] = now
        return True

    def check_trinity_ban(self, banned_names: list[str] | set[str], window: MainWindow) -> bool:
        global _last_trinity_ban_time
        if not is_sathara_in_match(window):
            return False

        from owervach_tmixer.ui.widgets.hero_widget import normalize_token, resolve_canonical_name
        norm_set = {normalize_token(resolve_canonical_name(n)) for n in banned_names}

        has_ball = any(t in norm_set for t in ("wreckingball", "hammond", "bola"))
        has_pharah = any(t in norm_set for t in ("pharah", "fara"))
        has_brig = any(t in norm_set for t in ("brigitte", "brig"))

        if has_ball and has_pharah and has_brig:
            now = time.time()
            if now - _last_trinity_ban_time < 12.0:
                return True
            _last_trinity_ban_time = now

            trait = SATHARA_TRAIT
            if hasattr(trait, "trinity_ban_quotes") and trait.trinity_ban_quotes:
                quote = _pick_variant(trait.trinity_ban_quotes, "trinity_ban")
                self._dispatch_ai_quote(quote, window, force=True)
                return True
        return False

    def maybe_trigger(self, ctx: EggContext | None = None) -> bool:
        if self.is_triggered:
            return False
        if ctx is not None and ctx.window is not None and not is_sathara_active(ctx.window):
            return False

        if not self.eggs:
            self.is_triggered = True
            self.trigger_count += 1
            return True

        chosen_egg = self._rng.choice(self.eggs)
        self.chosen_id = chosen_egg.id
        self.is_triggered = True
        self.trigger_count += 1

        try:
            chosen_egg.trigger(ctx)
        except Exception:
            pass

        if ctx and ctx.window and ctx.player_name:
            trait = get_player_trait(ctx.player_name)
            color = trait.glow_color if trait else SPECIAL_GLOW
            slots = ctx.special_slots()
            if slots:
                self._flash_slots(slots, color)

        return True

    maybe_trigger_entrance = maybe_trigger

    def on_player_saved(self, name: str, window: MainWindow):
        if not is_special_player_name(name) or not is_sathara_in_match(window):
            return
        if not self._check_cooldown("save", 5.0) or random.random() > 0.45:
            return
        trait = get_player_trait(name)
        if trait and trait.save_quotes and hasattr(window, "show_toast"):
            quote = _pick_variant(trait.save_quotes, "save")
            self._dispatch_ai_quote(quote, window)

    def on_player_unsaved(self, name: str, window: MainWindow):
        if not is_special_player_name(name) or not is_sathara_in_match(window):
            return
        if not self._check_cooldown("unsave", 5.0) or random.random() > 0.45:
            return
        trait = get_player_trait(name)
        if trait and trait.unsave_quotes and hasattr(window, "show_toast"):
            quote = _pick_variant(trait.unsave_quotes, "unsave")
            self._dispatch_ai_quote(quote, window)

    def on_player_benched(self, name: str, window: MainWindow):
        if not is_special_player_name(name):
            return
        if not self._check_cooldown("bench", 6.0) or random.random() > 0.40:
            return
        trait = get_player_trait(name)
        if trait and trait.bench_quotes and hasattr(window, "show_toast"):
            quote = _pick_variant(trait.bench_quotes, "bench")
            self._dispatch_ai_quote(quote, window)

    def on_player_permanently_removed(self, name: str, window: MainWindow):
        if not is_special_player_name(name):
            return
        trait = get_player_trait(name)
        if trait and trait.permanent_delete_quotes and hasattr(window, "show_toast"):
            quote = _pick_variant(trait.permanent_delete_quotes, "perm_delete")
            self._dispatch_ai_quote(quote, window)

    def on_player_bench_removed(self, name: str, window: MainWindow):
        if not is_special_player_name(name):
            return
        if not self._check_cooldown("bench_remove", 5.0) or random.random() > 0.40:
            return
        trait = get_player_trait(name)
        if trait and trait.bench_remove_quotes and hasattr(window, "show_toast"):
            quote = _pick_variant(trait.bench_remove_quotes, "bench_remove")
            self._dispatch_ai_quote(quote, window)

    def on_player_removed(self, name: str, window: MainWindow):
        if not is_special_player_name(name):
            return
        if not self._check_cooldown("removed", 5.0) or random.random() > 0.40:
            return
        trait = get_player_trait(name)
        if trait and trait.kick_quotes and hasattr(window, "show_toast"):
            quote = _pick_variant(trait.kick_quotes, "kick")
            self._dispatch_ai_quote(quote, window)

    def on_player_joined_team(self, name: str, team_num: int, window: MainWindow):
        if not is_special_player_name(name):
            return
        if not self._check_cooldown("joined_team", 6.0) or random.random() > 0.40:
            return
        trait = get_player_trait(name)
        if trait and trait.team_join_quotes and hasattr(window, "show_toast"):
            raw_quote = _pick_variant(trait.team_join_quotes, "join_team")
            quote = raw_quote.format(team=team_num)
            self._dispatch_ai_quote(quote, window)

    def _dispatch_ai_quote(self, quote: str, window: MainWindow, force: bool = False):
        global _last_global_ai_time, _spam_clicks_count, _last_click_instant
        now = time.time()

        # Detección de martilleo de botones (Spam humano)
        if now - _last_click_instant < 1.3:
            _spam_clicks_count += 1
        else:
            _spam_clicks_count = 1
        _last_click_instant = now

        if _spam_clicks_count >= 4:
            _spam_clicks_count = 0
            _last_global_ai_time = now + 4.0
            if hasattr(SATHARA_TRAIT, "spam_warning_quotes") and SATHARA_TRAIT.spam_warning_quotes:
                quote = _pick_variant(SATHARA_TRAIT.spam_warning_quotes, "spam_warning")
        elif not force and (now - _last_global_ai_time < 6.0):
            return

        _last_global_ai_time = now

        is_match_tab = hasattr(window, "tabs") and window.tabs.currentIndex() == 0
        if is_match_tab and hasattr(window, "match_display") and hasattr(window.match_display, "map_banner"):
            window.match_display.map_banner.show_transmission(quote)
            return

        if hasattr(window, "show_toast"):
            self._dispatch_ai_quote(quote, window)

    def on_match_shuffled(self, special_players: list[str], window: MainWindow):
        if not special_players or not is_sathara_in_match(window):
            return
        if not self._check_cooldown("shuffle", 8.0) or random.random() > 0.35:
            return
        trait = get_player_trait(special_players[0])
        if trait and trait.shuffle_quotes:
            quote = _pick_variant(trait.shuffle_quotes, "shuffle")
            QTimer.singleShot(400, lambda: self._dispatch_ai_quote(quote, window))

    def on_player_mmr_changed(self, name: str, mmr: int, window: MainWindow):
        if not is_special_player_name(name) or not is_sathara_in_match(window) or not hasattr(window, "show_toast"):
            return
        if not self._check_cooldown("mmr_change", 3.0):
            return
        trait = get_player_trait(name)
        if not trait:
            return

        if mmr <= 3 and trait.mmr_low_quotes:
            quote = _pick_variant(trait.mmr_low_quotes, "mmr_low").format(mmr=mmr)
        elif 4 <= mmr <= 7 and trait.mmr_mid_quotes:
            quote = _pick_variant(trait.mmr_mid_quotes, "mmr_mid").format(mmr=mmr)
        elif mmr >= 8 and trait.mmr_high_quotes:
            quote = _pick_variant(trait.mmr_high_quotes, "mmr_high").format(mmr=mmr)
        else:
            return

        self._dispatch_ai_quote(quote, window)

    def on_tier_placed(self, name: str, tier_name: str, window: MainWindow):
        if not is_special_player_name(name) or not hasattr(window, "show_toast"):
            return
        if not self._check_cooldown("tier_placed", 3.0):
            return
        trait = get_player_trait(name)
        if not trait:
            return

        tier_norm = tier_name.strip().upper()
        standard_tiers = ("S", "SS", "S+", "GOD", "A", "B", "C", "D", "F")
        if tier_norm not in standard_tiers:
            meta_quotes = [
                f"🤖 [Sistema]: Mis sensores detectan la categoría no estándar '{tier_name}'... ¿Qué experimento estás haciendo, Creador?",
                f"🤖 [Sistema]: Categoría '{tier_name}' detectada. Mi base de datos no tiene parámetros para juzgar esto, pero confío en tu criterio.",
                f"🤖 [Sistema]: Colocando a Sathara en '{tier_name}'... No cuestiono los métodos del Arquitecto, solo los observo con fascinación.",
            ]
            quote = _pick_variant(meta_quotes, "meta_tier")
            self._dispatch_ai_quote(quote, window)
            return

        if tier_norm in ("S", "SS", "S+", "GOD") and trait.tier_s_quotes:
            quote = _pick_variant(trait.tier_s_quotes, "tier_s")
        elif tier_norm in ("C", "D", "F") and trait.tier_low_quotes:
            quote = _pick_variant(trait.tier_low_quotes, "tier_low").format(tier=tier_name)
        else:
            return

        self._dispatch_ai_quote(quote, window)

    def on_fav_hero_tier_placed(self, hero_name: str, tier_name: str, window: MainWindow):
        # Reacciona solo si Sathara está en partida o en el Tier Maker
        if not is_sathara_active(window) or not hasattr(window, "show_toast"):
            return
        if not self._check_cooldown("fav_tier", 3.0):
            return

        from owervach_tmixer.ui.widgets.hero_widget import normalize_token, resolve_canonical_name
        canonical = resolve_canonical_name(hero_name)
        trait = SATHARA_TRAIT
        favs_normalized = {normalize_token(f) for f in trait.fav_heroes}

        if normalize_token(canonical) in favs_normalized or normalize_token(hero_name) in favs_normalized:
            tier_norm = tier_name.strip().upper()
            standard_tiers = ("S", "SS", "S+", "GOD", "A", "B", "C", "D", "F")
            if tier_norm not in standard_tiers:
                meta_fav_quotes = [
                    f"🤖 [Sistema]: ¿{hero_name} en '{tier_name}'? Interesante taxonomía... Mi red neuronal intentará comprender este meta alternativo.",
                    f"🤖 [Sistema]: Asignando a {hero_name} en '{tier_name}'... La lógica del Creador trasciende las categorías convencionales.",
                ]
                quote = _pick_variant(meta_fav_quotes, "meta_fav_tier")
                self._dispatch_ai_quote(quote, window)
                return

            if tier_norm in ("S", "SS", "S+", "GOD") and trait.fav_hero_tier_s_quotes:
                quote = _pick_variant(trait.fav_hero_tier_s_quotes, "fav_tier_s").format(hero=hero_name)
                self._dispatch_ai_quote(quote, window)
            elif tier_norm in ("C", "D", "F") and trait.fav_hero_tier_low_quotes:
                quote = _pick_variant(trait.fav_hero_tier_low_quotes, "fav_tier_low").format(hero=hero_name, tier=tier_name)
                self._dispatch_ai_quote(quote, window)

    def on_fav_hero_banned(self, hero_name: str, window: MainWindow, is_random: bool = False):
        # Solo reacciona a baneos si Sathara está activo en la partida
        if not is_sathara_in_match(window) or not hasattr(window, "show_toast"):
            return

        if is_random and (random.random() > 0.40 or not self._check_cooldown("fav_ban_rng", 5.0)):
            return
        elif not is_random and not self._check_cooldown("fav_ban_manual", 3.0):
            return

        from owervach_tmixer.ui.widgets.hero_widget import normalize_token, resolve_canonical_name
        canonical = resolve_canonical_name(hero_name)
        trait = SATHARA_TRAIT
        favs_normalized = {normalize_token(f) for f in trait.fav_heroes}

        if normalize_token(canonical) in favs_normalized or normalize_token(hero_name) in favs_normalized:
            if is_random and trait.fav_hero_random_ban_quotes:
                quote = _pick_variant(trait.fav_hero_random_ban_quotes, "fav_ban_rng").format(hero=hero_name)
            elif trait.fav_hero_ban_quotes:
                quote = _pick_variant(trait.fav_hero_ban_quotes, "fav_ban_manual").format(hero=hero_name)
            else:
                return

            self._dispatch_ai_quote(quote, window)

    def _flash_slots(self, slots: list, color: str = SPECIAL_GLOW):
        for slot in slots:
            overlay = QWidget(slot)
            overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            overlay.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            overlay.setStyleSheet("background: transparent; border: none;")
            overlay.setGeometry(slot.rect())
            overlay.show()

            effect = QGraphicsDropShadowEffect(overlay)
            effect.setColor(QColor(color))
            effect.setBlurRadius(32)
            effect.setOffset(0, 0)
            overlay.setGraphicsEffect(effect)

            pulse = QPropertyAnimation(effect, b"blurRadius", overlay)
            pulse.setDuration(900)
            pulse.setKeyValueAt(0.0, 32.0)
            pulse.setKeyValueAt(0.5, 10.0)
            pulse.setKeyValueAt(1.0, 32.0)
            pulse.setEasingCurve(QEasingCurve.Type.InOutQuad)
            pulse.finished.connect(overlay.deleteLater)
            pulse.start()
