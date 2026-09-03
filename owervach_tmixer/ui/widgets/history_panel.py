"""Modern Obsidian match history panel with 0ms RAM caching, vector buttons, and winner tracking."""

from __future__ import annotations
from .smooth_scroll import SmoothScrollArea

import json
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

import platformdirs
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer import APP_NAME
from owervach_tmixer.core.history import HistoryManager
from owervach_tmixer.core.models import Match, Role
from owervach_tmixer.ui.styles import theme
from owervach_tmixer.ui.widgets.map_card import MODE_COLORS, get_cached_map_banner, map_image_path
from owervach_tmixer.utils import get_resource_path


class HistoryVectorBtn(QPushButton):
    """Vector-drawn button for history actions (100% font independent for Linux & Windows)."""

    def __init__(self, action_type: str, tooltip: str = "", size: tuple[int, int] = (30, 30), parent: QWidget | None = None):
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

        if self.action_type == "view":
            bg_col = QColor("#2A3040") if is_hovered else QColor("#1E2028")
            border_col = QColor("#00B4FF") if is_hovered else QColor("#313544")
            icon_col = QColor("#00B4FF") if is_hovered else QColor("#C0C6D8")
        else:  # del
            bg_col = QColor("#4A1A22") if is_hovered else QColor("#221418")
            border_col = QColor("#FF4444") if is_hovered else QColor("#5A2028")
            icon_col = QColor("#FFFFFF") if is_hovered else QColor("#FFAAAA")

        if is_pressed:
            bg_col = bg_col.darker(130)

        painter.setPen(QPen(border_col, 1))
        painter.setBrush(QBrush(bg_col))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 5, 5)

        cx = self.width() // 2
        cy = self.height() // 2

        if self.action_type == "view":
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(icon_col, 1.8))
            painter.drawEllipse(cx - 5, cy - 5, 8, 8)
            painter.drawLine(cx + 2, cy + 2, cx + 5, cy + 5)
        elif self.action_type == "del":
            painter.setPen(QPen(icon_col, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(cx - 4, cy - 4, cx + 4, cy + 4)
            painter.drawLine(cx + 4, cy - 4, cx - 4, cy + 4)

        painter.end()


class MatchDetailDialog(QDialog):
    """Esports match report dialog with winner crown highlights, roles, and MMR stats."""

    def __init__(self, match: Match, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Reporte Oficial de Partida")
        self.resize(620, 530)
        self.setStyleSheet("background-color: #121316;")
        self.match = match
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        title_lbl = QLabel(f"⚔️  REPORTE DE PARTIDA · {self.match.timestamp.strftime('%d/%m/%Y %H:%M')}")
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 900; color: {theme.accent()};")
        top_row.addWidget(title_lbl)
        top_row.addStretch()

        btn_close = QPushButton("✕ Cerrar")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #1E2028; border: 1px solid #333846; border-radius: 6px;
                padding: 5px 14px; font-weight: 700; color: #FFFFFF;
            }
            QPushButton:hover { background-color: #2D323E; border-color: #61ab02; }
        """)
        btn_close.clicked.connect(self.accept)
        top_row.addWidget(btn_close)
        layout.addLayout(top_row)

        # Map Card
        map_card = QFrame()
        map_card.setStyleSheet("background-color: #17181F; border: 1px solid #282A33; border-radius: 8px;")
        mc_layout = QHBoxLayout(map_card)
        mc_layout.setContentsMargins(12, 8, 12, 8)
        mc_layout.setSpacing(10)

        if self.match.map:
            thumb = QLabel()
            thumb.setFixedSize(74, 46)
            pix = get_cached_map_banner(self.match.map.name, self.match.map.mode, card_size="small")
            thumb.setPixmap(pix.scaled(74, 46, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
            thumb.setStyleSheet("border-radius: 4px; background-color: #121316;")
            mc_layout.addWidget(thumb)

            mode_color = MODE_COLORS.get(self.match.map.mode, "#888888")
            lbl_m = QLabel(f"🗺️  <b>{self.match.map.name}</b>  <span style='color:{mode_color}; font-weight:800;'>[{self.match.map.mode.upper()}]</span>")
            lbl_m.setStyleSheet("font-size: 13px; color: #FFFFFF; background: transparent;")
            mc_layout.addWidget(lbl_m, 1)
        else:
            lbl_m = QLabel("🗺️  Sin mapa asignado")
            lbl_m.setStyleSheet("font-size: 12px; color: #8C92A4; background: transparent;")
            mc_layout.addWidget(lbl_m, 1)

        if self.match.bans:
            lbl_b = QLabel(f"⛔ Bans: {', '.join(self.match.bans)}")
            lbl_b.setStyleSheet("font-size: 11px; font-weight: 800; color: #FF7777; background-color: rgba(255, 68, 68, 0.10); border: 1px solid #5A2028; border-radius: 4px; padding: 3px 8px;")
            mc_layout.addWidget(lbl_b)

        layout.addWidget(map_card)

        # Teams Row with Winner Crown
        teams_row = QHBoxLayout()
        teams_row.setSpacing(12)

        is_t1_winner = getattr(self.match, "winner", None) == 1
        is_t2_winner = getattr(self.match, "winner", None) == 2

        t1_card = self._build_team_report(self.match.team1, "#00B4FF", "🔵", is_winner=is_t1_winner)
        teams_row.addWidget(t1_card, 1)

        t2_card = self._build_team_report(self.match.team2, "#FF4444", "🔴", is_winner=is_t2_winner)
        teams_row.addWidget(t2_card, 1)

        layout.addLayout(teams_row, 1)

    def _build_team_report(self, team, color_hex: str, icon: str, is_winner: bool = False) -> QWidget:
        card = QFrame()
        crown_border = f"border: 2px solid {color_hex};" if is_winner else f"border: 1px solid #282A33; border-top: 2.5px solid {color_hex};"
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #16171E;
                {crown_border}
                border-radius: 8px;
            }}
        """)
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(12, 10, 12, 10)
        vbox.setSpacing(6)

        avg = sum(p.get_mmr_for_role(p.role) for p in team.players) / len(team.players) if team.players else 0
        crown_txt = " 👑 [VICTORIA]" if is_winner else ""
        lbl_head = QLabel(f"{icon}  <b>{team.name}</b>{crown_txt}  <span style='color:{color_hex}; font-size:11px; font-weight:800;'>★ {avg:.1f}</span>")
        lbl_head.setStyleSheet("font-size: 13px; color: #FFFFFF; background: transparent;")
        vbox.addWidget(lbl_head)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #242734; border: none; margin: 2px 0 4px 0;")
        vbox.addWidget(sep)

        role_emojis = {Role.TANK: "🛡️", Role.DAMAGE: "⚔️", Role.SUPPORT: "💉"}
        for p in team.players:
            row = QHBoxLayout()
            row.setSpacing(6)
            emoji = role_emojis.get(p.role, "•") if p.role else "•"
            lbl_p = QLabel(f"{emoji} {p.name}")
            lbl_p.setStyleSheet("font-size: 12px; font-weight: 700; color: #DDE2EE; background: transparent;")
            row.addWidget(lbl_p, 1)

            lbl_star = QLabel(f"★ {p.get_mmr_for_role(p.role)}")
            lbl_star.setStyleSheet("font-size: 10px; font-weight: 800; color: #FFAA00; background-color: rgba(255, 170, 0, 0.12); border-radius: 3px; padding: 1px 4px;")
            row.addWidget(lbl_star)
            vbox.addLayout(row)

        vbox.addStretch()
        return card


class MatchCardWidget(QFrame):
    """Interactive match card with instant 0ms RAM thumbnail loading and winner badges."""

    load_clicked = Signal(object)
    delete_clicked = Signal(object)

    def __init__(self, match: Match, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.match = match
        self.setObjectName("matchCard")
        self.setFixedHeight(84)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 14, 8)
        layout.setSpacing(14)

        # 1. Map Thumbnail (Cached directly in RAM, 0ms)
        self.thumb = QLabel(self)
        self.thumb.setFixedSize(96, 64)
        self.thumb.setStyleSheet("border-radius: 5px; background-color: #121316;")
        if match.map:
            pix = get_cached_map_banner(match.map.name, match.map.mode, card_size="small")
            self.thumb.setPixmap(pix.scaled(96, 64, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
        else:
            self.thumb.setText("SIN MAPA")
            self.thumb.setAlignment(Qt.AlignCenter)
            self.thumb.setStyleSheet("color: #666; font-size: 10px; font-weight: 800; background-color: #121316; border-radius: 5px;")
        layout.addWidget(self.thumb)

        info_col = QVBoxLayout()
        info_col.setSpacing(3)
        info_col.setAlignment(Qt.AlignVCenter)

        row_top = QHBoxLayout()
        row_top.setSpacing(8)

        lbl_date = QLabel(f"📅 {match.timestamp.strftime('%d/%m/%Y %H:%M')}")
        lbl_date.setStyleSheet("color: #8C92A4; font-size: 11px; font-weight: 700;")
        row_top.addWidget(lbl_date)

        if match.map:
            mode_col = MODE_COLORS.get(match.map.mode, "#888888")
            self.lbl_map = QLabel(f"🗺️ {match.map.name}  <span style='color:{mode_col}; font-weight:800;'>[{match.map.mode.upper()}]</span>")
            self.lbl_map.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: 800;")
            row_top.addWidget(self.lbl_map)

        if match.bans:
            lbl_bans = QLabel(f"⛔ {len(match.bans)} bans")
            lbl_bans.setStyleSheet("color: #FF7777; font-size: 10px; font-weight: 800; background-color: rgba(255, 68, 68, 0.12); padding: 1px 5px; border-radius: 3px;")
            row_top.addWidget(lbl_bans)

        # Winner Badge
        winner = getattr(match, "winner", None)
        if winner == 1:
            lbl_win = QLabel(f"🏆 {match.team1.name}")
            lbl_win.setStyleSheet("color: #00B4FF; font-size: 10px; font-weight: 900; background-color: rgba(0, 180, 255, 0.14); border: 1px solid #00B4FF; border-radius: 3px; padding: 1px 6px;")
            row_top.addWidget(lbl_win)
        elif winner == 2:
            lbl_win = QLabel(f"🏆 {match.team2.name}")
            lbl_win.setStyleSheet("color: #FF5555; font-size: 10px; font-weight: 900; background-color: rgba(255, 85, 85, 0.14); border: 1px solid #FF5555; border-radius: 3px; padding: 1px 6px;")
            row_top.addWidget(lbl_win)
        elif winner == 0:
            lbl_win = QLabel("⚖️ Empate")
            lbl_win.setStyleSheet("color: #A0A5B2; font-size: 10px; font-weight: 800; background-color: rgba(255, 255, 255, 0.08); border-radius: 3px; padding: 1px 5px;")
            row_top.addWidget(lbl_win)

        row_top.addStretch()
        info_col.addLayout(row_top)

        t1_text = ", ".join(p.name for p in match.team1.players[:3])
        if len(match.team1.players) > 3:
            t1_text += f" +{len(match.team1.players)-3}"

        t2_text = ", ".join(p.name for p in match.team2.players[:3])
        if len(match.team2.players) > 3:
            t2_text += f" +{len(match.team2.players)-3}"

        lbl_teams = QLabel(
            f"🔵 <span style='color:#00B4FF; font-weight:800;'>{match.team1.name}</span> <span style='color:#9DA4B4;'>({t1_text})</span>  "
            f"<span style='color:#62677A; font-weight:900;'>VS</span>  "
            f"🔴 <span style='color:#FF4444; font-weight:800;'>{match.team2.name}</span> <span style='color:#9DA4B4;'>({t2_text})</span>"
        )
        lbl_teams.setStyleSheet("background: transparent; border: none; font-size: 12px;")
        info_col.addWidget(lbl_teams)

        layout.addLayout(info_col, 1)

        # Actions (🎮 Cargar, 🔍 View, 🗑️ Delete con vectores QPainter)
        self.btn_load = QPushButton("🎮 Cargar")
        self.btn_load.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_load.setFixedHeight(30)
        self.btn_load.clicked.connect(lambda: self.load_clicked.emit(self.match))
        layout.addWidget(self.btn_load)

        self.btn_view = HistoryVectorBtn("view", tooltip="Ver reporte oficial de partida", parent=self)
        self.btn_view.clicked.connect(self._show_details)
        layout.addWidget(self.btn_view)

        self.btn_del = HistoryVectorBtn("del", tooltip="Eliminar del historial", parent=self)
        self.btn_del.clicked.connect(lambda: self.delete_clicked.emit(self.match))
        layout.addWidget(self.btn_del)

        self.apply_theme()

    def apply_theme(self):
        accent = theme.accent()
        self.setStyleSheet(f"""
            QFrame#matchCard {{
                background-color: #17181F;
                border: 1px solid #282B36;
                border-radius: 8px;
            }}
            QFrame#matchCard:hover {{
                border-color: #3B4152;
                background-color: #1A1C24;
            }}
        """)
        if hasattr(self, "btn_load"):
            self.btn_load.setStyleSheet(f"""
                QPushButton {{
                    font-size: 11px; font-weight: 800; color: #FFFFFF;
                    background-color: #1E222A; border: 1px solid {accent};
                    border-radius: 5px; padding: 4px 12px;
                }}
                QPushButton:hover {{
                    background-color: {theme.accent_rgba(0.14)};
                    border-color: {theme.accent_light()};
                }}
            """)
        if hasattr(self, "btn_view"):
            self.btn_view.update()
        if hasattr(self, "btn_del"):
            self.btn_del.update()

    def _show_details(self):
        diag = MatchDetailDialog(self.match, self.window())
        diag.exec()


class HistoryPanel(QWidget):
    """Match history panel with instant batch rendering and dataset training exporter."""

    match_selected = Signal(object)
    clear_requested = Signal()

    def __init__(
        self,
        history_manager: HistoryManager,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.history_manager = history_manager
        self._matches: List[Match] = []
        self._cards: List[MatchCardWidget] = []
        self._dirty = True
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet("background-color: #16171D; border: 1px solid #282A33; border-radius: 8px;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(14, 0, 14, 0)
        h_layout.setSpacing(12)

        self.title = QLabel("📜 HISTORIAL DE PARTIDAS")
        self.title.setStyleSheet("font-size: 13px; font-weight: 900; color: #FFFFFF; background: transparent; border: none; letter-spacing: 0.5px;")
        h_layout.addWidget(self.title)

        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("font-size: 11px; font-weight: 700; color: #8F94A2; background: transparent; border: none;")
        h_layout.addWidget(self.stats_label)
        h_layout.addStretch()

        self.btn_export = QPushButton("📤 Exportar Dataset")
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.setToolTip("Exportar dataset de entrenamiento (JSON / CSV) para análisis matemático de IA")
        self.btn_export.clicked.connect(self._export_history)
        h_layout.addWidget(self.btn_export)

        self.btn_clear = QPushButton("🗑️ Limpiar")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                font-size: 11px; font-weight: 800; color: #FFAAAA;
                background-color: #28171B; border: 1px solid #5E2028; border-radius: 5px; padding: 5px 12px;
            }
            QPushButton:hover { background-color: #441A22; border-color: #FF4444; color: #FFFFFF; }
        """)
        self.btn_clear.clicked.connect(self._confirm_clear)
        h_layout.addWidget(self.btn_clear)

        layout.addWidget(header)

        self.scroll = SmoothScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: #101115; border: 1px solid #20222A; border-radius: 6px;")

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background-color: #101115;")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(10, 10, 10, 10)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch()
        self.scroll.setWidget(self.cards_container)

        layout.addWidget(self.scroll, 1)
        self.apply_theme()

    def apply_theme(self):
        accent = theme.accent()
        if hasattr(self, "btn_export"):
            self.btn_export.setStyleSheet(f"""
                QPushButton {{
                    font-size: 11px; font-weight: 800; color: #FFFFFF;
                    background-color: #1E2028; border: 1px solid {accent};
                    border-radius: 5px; padding: 5px 12px;
                }}
                QPushButton:hover {{
                    background-color: {theme.accent_rgba(0.14)};
                    border-color: {theme.accent_light()};
                }}
            """)
        for card in self._cards:
            card.apply_theme()

    def _refresh(self):
        self._dirty = True
        if self.isVisible():
            self._force_refresh()

    def _force_refresh(self):
        self._dirty = False
        self._matches = self.history_manager.get_all()
        self._cards.clear()

        self.cards_container.setUpdatesEnabled(False)
        try:
            while self.cards_layout.count() > 1:
                item = self.cards_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            if not self._matches:
                empty = QLabel("ℹ️ No hay partidas registradas en el historial aún.")
                empty.setAlignment(Qt.AlignCenter)
                empty.setStyleSheet("color: #6C7180; font-size: 13px; font-weight: 600; padding: 40px 0;")
                self.cards_layout.insertWidget(0, empty)
            else:
                for match in self._matches:
                    card = MatchCardWidget(match)
                    card.load_clicked.connect(lambda m: self.match_selected.emit(m))
                    card.delete_clicked.connect(self._delete_match)
                    self._cards.append(card)
                    self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
        finally:
            self.cards_container.setUpdatesEnabled(True)

        self._update_stats()
        self.apply_theme()

    def _update_stats(self):
        stats = self.history_manager.get_stats()
        accent = theme.accent()
        if stats["total"] == 0:
            txt = "0 partidas registradas"
        else:
            parts = [f"<span style='color:{accent}; font-weight:800;'>{stats['total']}</span> partidas"]
            if stats["maps"]:
                top_map = max(stats["maps"].items(), key=lambda x: x[1])
                parts.append(f"Top Mapa: <span style='color:#FFFFFF; font-weight:800;'>{top_map[0]}</span> ({top_map[1]})")
            txt = "  •  ".join(parts)

        self.stats_label.setText(f"·  {txt}")
        self.stats_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: 700;
                color: #8F94A2;
                background: transparent;
                border: none;
                padding: 0px 4px;
            }
        """)

    def _delete_match(self, match: Match):
        reply = QMessageBox.question(
            self, "Eliminar",
            f"¿Eliminar la partida del {match.timestamp.strftime('%d/%m/%Y %H:%M')}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._matches = [m for m in self._matches if m != match]
            self.history_manager.storage.save_history(self._matches)
            self._refresh()

    def _confirm_clear(self):
        reply = QMessageBox.question(
            self, "Limpiar historial",
            "¿Eliminar TODAS las partidas del historial?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.history_manager.clear()
            self._refresh()
            self.clear_requested.emit()

    def _export_history(self):
        if not self._matches:
            QMessageBox.information(self, "Vacío", "No hay partidas registradas para exportar.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Dataset de Entrenamiento", "Overwatch_Match_Dataset.json", "JSON (*.json);;CSV (*.csv)"
        )
        if not path:
            return

        try:
            if path.endswith(".csv"):
                lines = ["timestamp,winner,map_name,map_mode,team1_name,team1_players,team2_name,team2_players,bans"]
                for m in self._matches:
                    t1_p = ";".join(f"{p.name}:{p.role.value if p.role else 'none'}:{p.get_mmr_for_role(p.role)}" for p in m.team1.players)
                    t2_p = ";".join(f"{p.name}:{p.role.value if p.role else 'none'}:{p.get_mmr_for_role(p.role)}" for p in m.team2.players)
                    map_n = m.map.name if m.map else ""
                    map_m = m.map.mode if m.map else ""
                    bans_s = ";".join(m.bans)
                    w_val = str(getattr(m, "winner", "none"))
                    lines.append(f'"{m.timestamp.isoformat()}","{w_val}","{map_n}","{map_m}","{m.team1.name}","{t1_p}","{m.team2.name}","{t2_p}","{bans_s}"')
                with open(path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
            else:
                dataset = [m.to_dict() for m in self._matches]
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(dataset, f, indent=2, ensure_ascii=False)

            p_window = self.window()
            if hasattr(p_window, "show_toast"):
                p_window.show_toast("📤 Dataset de partidas exportado con éxito", "success")
        except Exception as exc:
            QMessageBox.critical(self, "Error al exportar", f"No se pudo exportar: {exc}")

    def showEvent(self, event):
        super().showEvent(event)
        if getattr(self, "_dirty", False):
            self._force_refresh()
