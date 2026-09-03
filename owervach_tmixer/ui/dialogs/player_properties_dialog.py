"""Player properties dialog with empirical winrate stats, role MMR, and Bayesian Auto-MMR toggle."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.core.models import Player, Role
from owervach_tmixer.ui.styles import theme


class PlayerPropertiesDialog(QDialog):
    """Esports player skill tuning modal with empirical statistics and Auto-MMR switch."""

    def __init__(self, player: Player, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.player = player
        self.setWindowTitle(f"Habilidad y Rendimiento — {player.name}")
        self.resize(440, 520)
        self.setStyleSheet("background-color: #121316;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # 1. Header con Nombre y Color
        header = QHBoxLayout()
        header.setSpacing(10)

        custom_col = getattr(self.player, "custom_color", None) or theme.accent()
        lbl_avatar = QLabel("👤", self)
        lbl_avatar.setFixedSize(36, 36)
        lbl_avatar.setAlignment(Qt.AlignCenter)
        lbl_avatar.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                background-color: rgba(255, 255, 255, 0.06);
                border: 1.5px solid {custom_col};
                border-radius: 6px;
            }}
        """)
        header.addWidget(lbl_avatar)

        name_col = QVBoxLayout()
        name_col.setSpacing(2)
        lbl_name = QLabel(self.player.name, self)
        lbl_name.setStyleSheet(f"font-size: 15px; font-weight: 900; color: {custom_col};")
        name_col.addWidget(lbl_name)

        lbl_sub = QLabel("Perfil de Habilidad y Balanceo Competitivo", self)
        lbl_sub.setStyleSheet("font-size: 11px; color: #8F94A2;")
        name_col.addWidget(lbl_sub)
        header.addLayout(name_col, 1)

        layout.addLayout(header)

        # 2. Tarjeta de Rendimiento Empírico (Data Real de Partidas)
        stats_box = QFrame(self)
        stats_box.setStyleSheet("""
            QFrame {
                background-color: #17181F;
                border: 1px solid #282A33;
                border-radius: 8px;
            }
        """)
        s_layout = QVBoxLayout(stats_box)
        s_layout.setContentsMargins(12, 10, 12, 10)
        s_layout.setSpacing(6)

        lbl_st_title = QLabel("📊 RENDIMIENTO EMPÍRICO (HISTORIAL)", stats_box)
        lbl_st_title.setStyleSheet(f"font-size: 10.5px; font-weight: 800; color: {theme.accent()}; background: transparent; border: none;")
        s_layout.addWidget(lbl_st_title)

        total_m = self.player.total_matches
        winrate = self.player.winrate
        calc_mmr = self.player.calculated_mmr if self.player.calculated_mmr is not None else float(self.player.mmr)

        row_metrics = QHBoxLayout()
        row_metrics.setSpacing(8)

        def _make_badge(title: str, val: str, col: str = "#FFF"):
            f = QFrame()
            f.setStyleSheet("background-color: #121316; border: 1px solid #22252E; border-radius: 5px;")
            fl = QVBoxLayout(f)
            fl.setContentsMargins(6, 4, 6, 4)
            fl.setSpacing(1)
            t = QLabel(title)
            t.setAlignment(Qt.AlignCenter)
            t.setStyleSheet("font-size: 9px; font-weight: 700; color: #7B8090; background: transparent; border: none;")
            v = QLabel(val)
            v.setAlignment(Qt.AlignCenter)
            v.setStyleSheet(f"font-size: 12px; font-weight: 900; color: {col}; background: transparent; border: none;")
            fl.addWidget(t)
            fl.addWidget(v)
            return f

        row_metrics.addWidget(_make_badge("PARTIDAS", str(total_m), "#E2E6F0"))
        row_metrics.addWidget(_make_badge("RÉCORD", f"{self.player.wins}W - {self.player.losses}L", "#FFAA00"))
        row_metrics.addWidget(_make_badge("WINRATE", f"{winrate:.1f}%", "#00B4FF" if winrate >= 50 else "#FF5555"))
        row_metrics.addWidget(_make_badge("MMR IA", f"★ {calc_mmr:.1f}", theme.accent()))
        s_layout.addLayout(row_metrics)

        # Checkbox de Autocalibración de IA
        self.chk_auto_mmr = QCheckBox("🤖 Activar Auto-Calibración Dinámica de IA", stats_box)
        self.chk_auto_mmr.setToolTip("Si está activo, el sistema ajusta su nivel automáticamente según sus victorias reales")
        self.chk_auto_mmr.setChecked(getattr(self.player, "auto_mmr_enabled", True))
        self.chk_auto_mmr.setStyleSheet("color: #FFFFFF; font-weight: 700; font-size: 11px; margin-top: 4px; background: transparent; border: none;")
        s_layout.addWidget(self.chk_auto_mmr)

        layout.addWidget(stats_box)

        # 3. Sliders de MMR Manual (Base / Prior)
        box_manual = QFrame(self)
        box_manual.setStyleSheet("background-color: #17181F; border: 1px solid #282A33; border-radius: 8px;")
        form = QFormLayout(box_manual)
        form.setContentsMargins(14, 12, 14, 12)
        form.setSpacing(10)

        lbl_m_title = QLabel("✏️  MMR MANUAL / VALORES FIJOS (1 a 10)", box_manual)
        lbl_m_title.setStyleSheet(f"font-size: 10.5px; font-weight: 800; color: {theme.accent()}; background: transparent; border: none;")
        form.addRow(lbl_m_title)

        self.spin_general = self._create_spin(getattr(self.player, "mmr", 5))
        form.addRow("★ Nivel General:", self.spin_general)

        self.spin_tank = self._create_spin(self.player.mmr_tank if self.player.mmr_tank is not None else getattr(self.player, "mmr", 5))
        form.addRow("🛡️ Nivel Tanque:", self.spin_tank)

        self.spin_damage = self._create_spin(self.player.mmr_damage if self.player.mmr_damage is not None else getattr(self.player, "mmr", 5))
        form.addRow("⚔️ Nivel Daño:", self.spin_damage)

        self.spin_support = self._create_spin(self.player.mmr_support if self.player.mmr_support is not None else getattr(self.player, "mmr", 5))
        form.addRow("💉 Nivel Apoyo:", self.spin_support)

        layout.addWidget(box_manual)

        # 4. Botones de Acción
        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addStretch()

        btn_cancel = QPushButton("Cancelar", self)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("background-color: #1E2028; border: 1px solid #333846; border-radius: 6px; padding: 6px 14px; font-weight: 700; color: #FFFFFF;")
        btn_cancel.clicked.connect(self.reject)
        actions.addWidget(btn_cancel)

        btn_save = QPushButton("Guardar", self)
        btn_save.setProperty("primary", True)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet(f"background-color: {theme.accent()}; color: #000; font-weight: 900; border-radius: 6px; padding: 6px 18px;")
        btn_save.clicked.connect(self.accept)
        actions.addWidget(btn_save)

        layout.addLayout(actions)

    def _create_spin(self, initial_val: int) -> QSpinBox:
        spin = QSpinBox(self)
        spin.setRange(1, 10)
        spin.setValue(int(initial_val) if initial_val else 5)
        spin.setStyleSheet("""
            QSpinBox {
                background-color: #121316; border: 1px solid #2B2F3D; border-radius: 5px;
                padding: 4px 8px; color: #FFFFFF; font-weight: 700; font-size: 12px;
            }
            QSpinBox:focus { border-color: #61ab02; }
        """)
        return spin

    def get_data(self) -> tuple[int, int, int, int, bool]:
        return (
            self.spin_general.value(),
            self.spin_tank.value(),
            self.spin_damage.value(),
            self.spin_support.value(),
            self.chk_auto_mmr.isChecked(),
        )
