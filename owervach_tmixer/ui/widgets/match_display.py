"""Match Display tab orchestrator with dual team panels, vector reset button, and instant zero-lag winner selector."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPolygon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.core.models import GameMode, Map, Role
from owervach_tmixer.ui.styles import theme
from .match_map_banner import MatchMapBanner

if TYPE_CHECKING:
    from .team_display import TeamDisplayWidget


class ResetVectorBtn(QPushButton):
    """Crisp vector reset circular arrow via QPainter (independent of system fonts)."""

    def __init__(self, tooltip: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(28, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            self.setToolTip(tooltip)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_hovered = self.underMouse()
        is_pressed = self.isDown()
        accent_col = theme.accent_color()

        bg_col = QColor("#282D3B") if is_hovered else QColor("#1C1E26")
        border_col = accent_col if is_hovered else QColor("#2F3342")
        icon_col = QColor("#FFFFFF") if is_hovered else QColor("#9DA4B4")

        if is_pressed:
            bg_col = bg_col.darker(130)

        painter.setPen(QPen(border_col, 1))
        painter.setBrush(QBrush(bg_col))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 4, 4)

        cx = self.width() // 2
        cy = self.height() // 2

        # Draw circular reset arrow
        painter.setPen(QPen(icon_col, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(cx - 6, cy - 6, 12, 12, 45 * 16, 275 * 16)

        painter.setBrush(QBrush(icon_col))
        arrow = QPolygon([QPoint(cx + 4, cy - 7), QPoint(cx + 4, cy - 2), QPoint(cx + 8, cy - 4)])
        painter.drawPolygon(arrow)

        painter.end()


class MatchDisplayWidget(QWidget):
    """Match tab: dual team slot panels, map banner, instant winner selector, and action buttons."""

    map_updated = Signal(object, object)
    generate_match = Signal()
    reroll_map = Signal()
    clear_map = Signal()
    copy_to_discord_done = Signal()
    copy_to_discord_empty = Signal()
    clear_all_requested = Signal()
    winner_declared = Signal(object)  # 1 for Team 1, 2 for Team 2, 0 for Draw, None for Unset

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._current_match = None
        self._show_roles = True
        self._show_mmr = False
        self._current_winner: int | None = None
        self._setup_ui()

    def _setup_ui(self):
        from .team_display import TeamDisplayWidget

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 1. Dual Team Panels
        teams_layout = QHBoxLayout()
        teams_layout.setSpacing(12)

        self.team1_widget = TeamDisplayWidget(1)
        self.team1_widget.team_name_changed.connect(lambda _: self._update_winner_button_labels())
        teams_layout.addWidget(self.team1_widget, 1)

        vs_container = QWidget(self)
        vs_layout = QVBoxLayout(vs_container)
        vs_layout.setContentsMargins(0, 0, 0, 0)
        vs_layout.setSpacing(6)
        vs_layout.setAlignment(Qt.AlignCenter)

        line_top = QFrame(vs_container)
        line_top.setFrameShape(QFrame.VLine)
        line_top.setStyleSheet("background-color: #2B2B2B; max-width: 1px;")
        vs_layout.addWidget(line_top, 1, Qt.AlignHCenter)

        vs_badge = QLabel("VS", vs_container)
        vs_badge.setAlignment(Qt.AlignCenter)
        vs_badge.setFixedSize(34, 34)
        vs_badge.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: 800;
                color: #8E8E8E;
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 17px;
            }
        """)
        vs_layout.addWidget(vs_badge, 0, Qt.AlignCenter)

        line_bottom = QFrame(vs_container)
        line_bottom.setFrameShape(QFrame.VLine)
        line_bottom.setStyleSheet("background-color: #2B2B2B; max-width: 1px;")
        vs_layout.addWidget(line_bottom, 1, Qt.AlignHCenter)

        teams_layout.addWidget(vs_container, 0)

        self.team2_widget = TeamDisplayWidget(2)
        self.team2_widget.team_name_changed.connect(lambda _: self._update_winner_button_labels())
        teams_layout.addWidget(self.team2_widget, 1)

        layout.addLayout(teams_layout, 5)

        # 2. Panoramic Map Banner
        self.map_banner = MatchMapBanner()
        self.map_banner.reroll_requested.connect(self.reroll_map.emit)
        self.map_banner.clear_requested.connect(self.clear_map.emit)
        self.map_banner.setMinimumHeight(110)
        self.map_banner.setMaximumHeight(210)
        layout.addWidget(self.map_banner, 2)

        # 3. Live Esports Winner Scoreboard Selector
        self.winner_bar = QFrame(self)
        self.winner_bar.setFixedHeight(38)
        self.winner_bar.setStyleSheet("""
            QFrame {
                background-color: #15171F;
                border: 1px solid #282B36;
                border-radius: 6px;
            }
        """)
        w_layout = QHBoxLayout(self.winner_bar)
        w_layout.setContentsMargins(10, 3, 10, 3)
        w_layout.setSpacing(8)

        lbl_score_title = QLabel("🏁 RESULTADO:", self.winner_bar)
        lbl_score_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #8F94A2; background: transparent; border: none;")
        w_layout.addWidget(lbl_score_title)

        self.btn_win_t1 = QPushButton("🏆 Victoria Equipo 1", self.winner_bar)
        self.btn_win_t1.setCheckable(True)
        self.btn_win_t1.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_win_t1.clicked.connect(lambda: self._on_winner_btn_clicked(1))
        w_layout.addWidget(self.btn_win_t1, 1)

        self.btn_draw = QPushButton("⚖️ Empate", self.winner_bar)
        self.btn_draw.setCheckable(True)
        self.btn_draw.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_draw.clicked.connect(lambda: self._on_winner_btn_clicked(0))
        w_layout.addWidget(self.btn_draw, 0)

        self.btn_win_t2 = QPushButton("🏆 Victoria Equipo 2", self.winner_bar)
        self.btn_win_t2.setCheckable(True)
        self.btn_win_t2.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_win_t2.clicked.connect(lambda: self._on_winner_btn_clicked(2))
        w_layout.addWidget(self.btn_win_t2, 1)

        self.btn_reset_winner = ResetVectorBtn("Restablecer resultado a pendiente", self.winner_bar)
        self.btn_reset_winner.clicked.connect(lambda: self._on_winner_btn_clicked(None))
        w_layout.addWidget(self.btn_reset_winner, 0)

        layout.addWidget(self.winner_bar)

        # 4. Action Buttons (Mezclar + Discord + Vaciar Todo)
        actions = QHBoxLayout()
        actions.setSpacing(12)

        self.btn_generate = QPushButton("🔀  MEZCLAR PARTIDA")
        self.btn_generate.setObjectName("btnGenerate")
        self.btn_generate.setMinimumHeight(46)
        self.btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate.setToolTip("Mezclar jugadores en los equipos (Ctrl + Enter)")
        self.btn_generate.clicked.connect(self.generate_match.emit)
        actions.addWidget(self.btn_generate, 4)

        self.btn_copy_discord = QPushButton("📋  COPIAR ALINEACIÓN")
        self.btn_copy_discord.setObjectName("btnCopyDiscord")
        self.btn_copy_discord.setMinimumHeight(46)
        self.btn_copy_discord.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_discord.setStyleSheet("""
            QPushButton#btnCopyDiscord {
                font-size: 13px;
                font-weight: 800;
                color: #B5C0FF;
                background-color: rgba(22, 24, 34, 0.85);
                border: 1px solid #5865F2;
                border-radius: 8px;
                padding: 6px 16px;
            }
            QPushButton#btnCopyDiscord:hover {
                background-color: rgba(88, 101, 242, 0.16);
                border-color: #7983F5;
                color: #FFFFFF;
            }
            QPushButton#btnCopyDiscord:pressed {
                background-color: rgba(88, 101, 242, 0.28);
            }
        """)
        self.btn_copy_discord.setToolTip("Copiar alineación formateada para Discord")
        self.btn_copy_discord.clicked.connect(self._copy_for_discord)
        actions.addWidget(self.btn_copy_discord, 2)

        self.btn_clear_all = QPushButton("🗑️  VACIAR TODO")
        self.btn_clear_all.setObjectName("btnClearAll")
        self.btn_clear_all.setMinimumHeight(46)
        self.btn_clear_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_all.setStyleSheet("""
            QPushButton#btnClearAll {
                font-size: 12px;
                font-weight: 800;
                color: #FF8B8B;
                background-color: rgba(26, 20, 24, 0.85);
                border: 1px solid #5A262C;
                border-radius: 8px;
                letter-spacing: 0.3px;
                padding: 6px 12px;
            }
            QPushButton#btnClearAll:hover {
                background-color: rgba(255, 68, 68, 0.18);
                border-color: #FF4444;
                color: #FFFFFF;
            }
            QPushButton#btnClearAll:pressed {
                background-color: rgba(255, 68, 68, 0.32);
            }
        """)
        self.btn_clear_all.setToolTip("Vaciar ambos equipos y la zona de espera de un solo toque")
        self.btn_clear_all.clicked.connect(self.clear_all_requested.emit)
        actions.addWidget(self.btn_clear_all, 1)

        layout.addLayout(actions)
        self.apply_theme()

    def _update_winner_button_labels(self):
        t1_name = self.team1_widget.get_team_name()
        t2_name = self.team2_widget.get_team_name()
        self.btn_win_t1.setText(f"🏆 Victoria {t1_name}")
        self.btn_win_t2.setText(f"🏆 Victoria {t2_name}")
        self._refresh_winner_styles()

    def _on_winner_btn_clicked(self, winner_code: int | None):
        self._current_winner = winner_code
        self._refresh_winner_styles()
        self.winner_declared.emit(winner_code)

    def set_winner(self, winner_code: int | None):
        self._current_winner = winner_code
        self._refresh_winner_styles()

    def _refresh_winner_styles(self):
        w = self._current_winner
        self.btn_win_t1.blockSignals(True)
        self.btn_draw.blockSignals(True)
        self.btn_win_t2.blockSignals(True)

        self.btn_win_t1.setChecked(w == 1)
        self.btn_draw.setChecked(w == 0)
        self.btn_win_t2.setChecked(w == 2)

        # Team 1 (Cyan Blue #00B4FF)
        if w == 1:
            self.btn_win_t1.setStyleSheet("""
                QPushButton {
                    font-size: 11px; font-weight: 900; color: #FFFFFF;
                    background-color: #007AB8; border: 1px solid #00B4FF;
                    border-radius: 4px; padding: 4px 8px;
                }
            """)
        else:
            self.btn_win_t1.setStyleSheet("""
                QPushButton {
                    font-size: 11px; font-weight: 700; color: #A0C0E8;
                    background-color: #171E28; border: 1px solid #233246;
                    border-radius: 4px; padding: 4px 8px;
                }
                QPushButton:hover { background-color: #1E2938; border-color: #00B4FF; color: #FFFFFF; }
            """)

        # Draw (Slate Grey #8E94A0)
        if w == 0:
            self.btn_draw.setStyleSheet("""
                QPushButton {
                    font-size: 11px; font-weight: 900; color: #FFFFFF;
                    background-color: #383E4E; border: 1px solid #8E94A0;
                    border-radius: 4px; padding: 4px 10px;
                }
            """)
        else:
            self.btn_draw.setStyleSheet("""
                QPushButton {
                    font-size: 11px; font-weight: 700; color: #8F94A2;
                    background-color: #1C1E26; border: 1px solid #2D303C;
                    border-radius: 4px; padding: 4px 10px;
                }
                QPushButton:hover { background-color: #272B38; color: #FFFFFF; }
            """)

        # Team 2 (Coral Red #FF4444)
        if w == 2:
            self.btn_win_t2.setStyleSheet("""
                QPushButton {
                    font-size: 11px; font-weight: 900; color: #FFFFFF;
                    background-color: #B82222; border: 1px solid #FF4444;
                    border-radius: 4px; padding: 4px 8px;
                }
            """)
        else:
            self.btn_win_t2.setStyleSheet("""
                QPushButton {
                    font-size: 11px; font-weight: 700; color: #E8A0A0;
                    background-color: #28171A; border: 1px solid #462327;
                    border-radius: 4px; padding: 4px 8px;
                }
                QPushButton:hover { background-color: #381E23; border-color: #FF4444; color: #FFFFFF; }
            """)

        self.btn_win_t1.blockSignals(False)
        self.btn_draw.blockSignals(False)
        self.btn_win_t2.blockSignals(False)

    def _copy_for_discord(self):
        t1_players = self.team1_widget.get_players()
        t2_players = self.team2_widget.get_players()

        if not t1_players and not t2_players:
            self.copy_to_discord_empty.emit()
            return

        lines: list[str] = []

        def _format_team(name: str, players: list, team_num: int):
            avg_str = ""
            crown = " 👑" if self._current_winner == team_num else ""
            if self._show_mmr and players:
                avg = sum(p[2] for p in players) / len(players)
                avg_str = f" (★ Promedio: {avg:.1f})"
            lines.append(f"**[{name}]{avg_str}{crown}**")
            for p_name, role, mmr in players:
                star_tag = f" [★{mmr}]" if self._show_mmr else ""
                if self._show_roles and role:
                    role_emoji = {
                        Role.TANK: "🛡️", Role.DAMAGE: "⚔️", Role.SUPPORT: "💉",
                    }.get(role, "👤")
                    lines.append(f"{role_emoji} {p_name}{star_tag} ({role.value.upper()})")
                else:
                    lines.append(f"• {p_name}{star_tag}")
            lines.append("")

        _format_team(self.team1_widget.get_team_name(), t1_players, 1)
        _format_team(self.team2_widget.get_team_name(), t2_players, 2)

        current_map = None
        if self._current_match and self._current_match.map:
            current_map = self._current_match.map
        elif self.map_banner.get_map():
            current_map = self.map_banner.get_map()

        if current_map:
            lines.append(f"🗺️ **Mapa:** {current_map.name} ({current_map.mode})")

        if self._current_match and self._current_match.bans:
            lines.append(f"⛔ **Baneos:** {', '.join(self._current_match.bans)}")

        if self._current_winner == 1:
            lines.append(f"🏆 **Ganador:** {self.team1_widget.get_team_name()}")
        elif self._current_winner == 2:
            lines.append(f"🏆 **Ganador:** {self.team2_widget.get_team_name()}")
        elif self._current_winner == 0:
            lines.append("⚖️ **Resultado:** Empate")

        QApplication.clipboard().setText("\n".join(lines).strip())
        self.copy_to_discord_done.emit()

    def set_match(self, match):
        self._current_match = match
        self._update_winner_button_labels()
        if match:
            self.set_winner(getattr(match, "winner", None))
            if match.map:
                self.map_banner.set_map(match.map)
                self.map_updated.emit(match.map.name, match.map.mode)
            else:
                self.map_banner.set_map(None)
                self.map_updated.emit(None, None)
        else:
            self.set_winner(None)
            self.map_banner.set_map(None)
            self.map_updated.emit(None, None)

    def set_map(self, map_obj: Map | None):
        if self._current_match:
            self._current_match.map = map_obj
        self.map_banner.set_map(map_obj)
        if map_obj:
            self.map_updated.emit(map_obj.name, map_obj.mode)
        else:
            self.map_updated.emit(None, None)

    def set_game_mode(self, mode: GameMode):
        self.team1_widget.set_game_mode(mode)
        self.team2_widget.set_game_mode(mode)

    def set_font_preferences(
        self,
        size: int,
        weight: str,
        align: str = "center",
        dynamic_font: bool = True,
        role_badge_style: str = "emoji",
        badge_outlines: bool = False
    ):
        self.team1_widget.set_font_preferences(size, weight, align, dynamic_font, role_badge_style, badge_outlines)
        self.team2_widget.set_font_preferences(size, weight, align, dynamic_font, role_badge_style, badge_outlines)

    def set_show_roles(self, show: bool):
        self._show_roles = show
        self.team1_widget.set_show_roles(show)
        self.team2_widget.set_show_roles(show)

    def set_show_mmr(self, show: bool):
        self._show_mmr = show
        self.team1_widget.set_show_mmr(show)
        self.team2_widget.set_show_mmr(show)

    def apply_theme(self):
        accent = theme.accent()
        self.team1_widget.apply_theme()
        self.team2_widget.apply_theme()
        self._update_winner_button_labels()

        self.btn_generate.setStyleSheet(f"""
            QPushButton#btnGenerate {{
                font-size: 14px;
                font-weight: 900;
                color: {accent};
                background-color: rgba(20, 22, 30, 0.88);
                border: 1px solid {accent};
                border-radius: 8px;
                letter-spacing: 0.5px;
                padding: 6px 16px;
            }}
            QPushButton#btnGenerate:hover {{
                background-color: {theme.accent_rgba(0.16)};
                border-color: {theme.accent_light()};
                color: #FFFFFF;
            }}
            QPushButton#btnGenerate:pressed {{
                background-color: {theme.accent_rgba(0.28)};
            }}
        """)
        self.map_banner.update()
        if hasattr(self, "btn_reset_winner"):
            self.btn_reset_winner.update()
