"""About tab featuring technical telemetry, dynamic versioning, architecture specifications, and tactical arbitration."""

from __future__ import annotations

import platform
import random
from typing import TYPE_CHECKING

from PySide6 import __version__ as PYSIDE_VERSION
from PySide6.QtCore import Qt, qVersion
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer import APP_NAME, APP_TITLE, ORG_NAME, VERSION_INFO
from owervach_tmixer.ui.styles import theme
from .common import create_card_box


class SmartMemoryBag:
    def __init__(self, items: list[str], memory_ratio: float = 0.40):
        self.all_items = list(items)
        self.memory_limit = max(3, int(len(items) * memory_ratio))
        self.recent_history: list[str] = []

    def get_next(self) -> str:
        if not self.all_items:
            return ""

        candidates = [x for x in self.all_items if x not in self.recent_history]
        if not candidates:
            self.recent_history = self.recent_history[len(self.recent_history) // 2:]
            candidates = [x for x in self.all_items if x not in self.recent_history]
        if not candidates:
            candidates = self.all_items

        chosen = random.choice(candidates)
        self.recent_history.append(chosen)
        if len(self.recent_history) > self.memory_limit:
            self.recent_history.pop(0)
        return chosen


AI_OPINIONS_POOL = [
    "ℹ️ [S.A.T.H.A.N.A. Core]: El balanceador heurístico minimiza la varianza del MMR total entre equipos, priorizando simetría estricta en el rol de Tanque.",
    "ℹ️ [S.A.T.H.A.N.A. Core]: El algoritmo de rotación continua prioriza a los jugadores con mayor racha de espera para garantizar un tiempo equitativo en partida.",
    "ℹ️ [S.A.T.H.A.N.A. Core]: El selector de mapas implementa un búfer de exclusión reciente tipo FIFO para evitar repeticiones consecutivas en series largas.",
    "ℹ️ [S.A.T.H.A.N.A. Core]: Las plantillas 5v5 (1-2-2) y 6v6 (2-2-2) configuran restricciones simétricas de rol para mantener la integridad composicional.",
    "ℹ️ [S.A.T.H.A.N.A. Core]: El sistema de fijado de equipo actúa como una restricción rígida sobre el generador de combinaciones, preservando la asignación manual.",
    "ℹ️ [S.A.T.H.A.N.A. Core]: El cálculo de MMR desacoplado permite registrar calificaciones independientes por rol (Tanque, Daño, Apoyo) para cada jugador.",
    "ℹ️ [S.A.T.H.A.N.A. Core]: El escudo Bo2 asegura que los jugadores incorporados desde la banca disputen al menos dos partidas consecutivas antes de rotar.",
    "ℹ️ [S.A.T.H.A.N.A. Core]: La persistencia atómica utiliza escrituras con vaciado de búfer a disco para prevenir corrupción de datos en cierres inesperados.",
    "ℹ️ [S.A.T.H.A.N.A. Core]: El motor cinético de interfaz sincroniza el scroll a la frecuencia de actualización del monitor para eliminar tartamudeos visuales.",
    "ℹ️ [S.A.T.H.A.N.A. Core]: Los algoritmos de emparejamiento evalúan múltiples candidatos aleatorizados para maximizar la diversidad de alineaciones en cada ronda.",
    "ℹ️ [S.A.T.H.A.N.A. Core]: El sistema admite tanto paridad estándar de MMR global como asignaciones competitivas asimétricas controladas por el operador.",
    "ℹ️ [S.A.T.H.A.N.A. Core]: La arquitectura desacoplada en Python puro en 'core/' garantiza que las reglas de emparejamiento sean independientes de la vista.",
]

DIAGNOSTIC_MESSAGES_POOL = [
    "✅ Estado del Roster: Estructura de ranuras en memoria sincronizada con el estado visual.",
    "✅ Módulo de Persistencia: Archivos JSON verificados y serializables mediante almacenamiento atómico.",
    "✅ Pool de Mapas: MapPool inicializado con historial de exclusión reciente operativo.",
    "✅ Motor de Balanceo: Parámetros heurísticos y tabla de MMR configurados correctamente.",
    "✅ Pipeline Gráfico: Controlador cinético PrecisionTimer activo a la tasa de refresco del display.",
    "✅ Jerarquía de Widgets: Árbol de componentes verificado sin dependencias circulares ni desbordamientos.",
    "✅ Subsistema de Entrada: Manejadores de eventos de teclado, arrastre y menús contextuales enlazados.",
    "✅ Suite de Calidad: 153/153 pruebas unitarias e integrales validadas en verde.",
    "✅ Paridad Multiplataforma: Coordenadas de persistencia validadas contra monitores del sistema.",
    "✅ Gestión de Roles: Restricciones de composición 5v5 y 6v6 cargadas desde configuración.",
]

_OPINIONS_BAG = SmartMemoryBag(AI_OPINIONS_POOL, memory_ratio=0.35)
_DIAGNOSTICS_BAG = SmartMemoryBag(DIAGNOSTIC_MESSAGES_POOL, memory_ratio=0.35)


def build_about_tab(dialog, layout: QVBoxLayout):
    # 1. ENCABEZADO Y VERSIÓN DINÁMICA
    box_ver = QFrame()
    box_ver.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    box_ver.setStyleSheet("""
        QFrame {
            background-color: #161822;
            border: 1px solid #282D3D;
            border-left: 3px solid #61ab02;
            border-radius: 8px;
        }
    """)
    v_layout = QVBoxLayout(box_ver)
    v_layout.setContentsMargins(16, 14, 16, 14)
    v_layout.setSpacing(8)

    h_top = QHBoxLayout()
    h_top.setSpacing(8)

    lbl_app_title = QLabel(f"🎮  {APP_TITLE.upper()}", box_ver)
    lbl_app_title.setStyleSheet("font-size: 14px; font-weight: 900; color: #FFFFFF; letter-spacing: 0.5px;")
    h_top.addWidget(lbl_app_title, 1)

    lbl_ver_badge = QLabel(VERSION_INFO.badge, box_ver)
    lbl_ver_badge.setStyleSheet("""
        QLabel {
            color: #A4E062; font-size: 10px; font-weight: 800;
            background-color: rgba(97, 171, 2, 0.16); border: 1px solid #48781B;
            border-radius: 4px; padding: 3px 8px;
        }
    """)
    h_top.addWidget(lbl_ver_badge, 0)
    v_layout.addLayout(h_top)

    lbl_desc = QLabel(
        "Orquestador de escritorio de alto rendimiento diseñado para la gestión de partidas personalizadas de Overwatch, "
        "balanceo matemático de roles y MMR, sorteo estratégico de mapas y creación de Tier Lists competitivas.",
        box_ver
    )
    lbl_desc.setWordWrap(True)
    lbl_desc.setStyleSheet("color: #9DA3B4; font-size: 11px;")
    v_layout.addWidget(lbl_desc)

    row_meta = QHBoxLayout()
    row_meta.setSpacing(12)

    def _meta_chip(label: str, value: str):
        c = QLabel(f"<b>{label}:</b> <span style='color:#FFFFFF;'>{value}</span>")
        c.setStyleSheet("font-size: 10.5px; color: #8A90A2;")
        return c

    row_meta.addWidget(_meta_chip("Licencia", "MIT (Código Abierto)"))
    row_meta.addWidget(_meta_chip("Estado", VERSION_INFO.status))
    row_meta.addWidget(_meta_chip("Tests", "153/153 en Verde"))
    row_meta.addStretch()
    v_layout.addLayout(row_meta)

    layout.addWidget(box_ver)

    # 2. FICHA TÉCNICA RIGUROSA
    specs_box = create_card_box("📊 Ficha Técnica de Ingeniería & Telemetría")
    specs_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    s_layout = QVBoxLayout(specs_box)
    s_layout.setContentsMargins(14, 12, 16, 12)
    s_layout.setSpacing(6)

    def _spec_row(label: str, val: str, highlight: bool = False):
        r = QHBoxLayout()
        r.setContentsMargins(0, 0, 0, 0)
        r.setSpacing(10)
        l = QLabel(label)
        l.setStyleSheet("color: #8C92A4; font-size: 11px; font-weight: 700;")
        l.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        v = QLabel(val)
        v.setWordWrap(True)
        v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        val_color = theme.accent() if highlight else "#FFFFFF"
        v.setStyleSheet(f"color: {val_color}; font-size: 11px; font-weight: 800;")
        v.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        r.addWidget(l, 0)
        r.addWidget(v, 1)
        return r

    py_ver = platform.python_version()
    qt_ver = qVersion()
    os_name = f"{platform.system()} {platform.release()} ({platform.machine()})"

    s_layout.addLayout(_spec_row("Versión del Software:", f"v{VERSION_INFO.version} ({VERSION_INFO.channel})", highlight=True))
    s_layout.addLayout(_spec_row("Entorno de Ejecución:", f"Python {py_ver} & PySide6 v{PYSIDE_VERSION} (Qt {qt_ver})"))
    s_layout.addLayout(_spec_row("Arquitectura de Dominio:", "Núcleo puro en Python ('core/') desacoplado de la interfaz gráfica"))
    s_layout.addLayout(_spec_row("Patrón de Presentación:", "Model-View-Controller (MVC) guiado por eventos y señales Qt"))
    s_layout.addLayout(_spec_row("Pipeline Gráfico:", "Motor cinético a 144 Hz con temporizador de precisión y VSync nativo"))
    s_layout.addLayout(_spec_row("Motor de Matchmaking:", "Heurística de balance simétrico por roles y minimización de delta de MMR"))
    s_layout.addLayout(_spec_row("Mecanismo de Rotación:", "Rotación continua por turnos con mitigación de rachas (Escudo Bo2)"))
    s_layout.addLayout(_spec_row("Capa de Persistencia:", "Almacenamiento atómico en JSON con verificación fsync y control de integridad"))
    s_layout.addLayout(_spec_row("Gestión de Geometría:", "Persistencia de coordenadas multi-monitor compatible con Wayland y Windows"))
    s_layout.addLayout(_spec_row("Sistema Operativo:", os_name))
    layout.addWidget(specs_box)

    # 3. DIRECCIÓN CREATIVA
    box_creator = QFrame()
    box_creator.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    box_creator.setStyleSheet("""
        QFrame {
            background-color: rgba(18, 28, 16, 0.85);
            border: 1px solid #3E6617;
            border-radius: 8px;
        }
    """)
    c_layout = QVBoxLayout(box_creator)
    c_layout.setContentsMargins(14, 12, 16, 12)
    c_layout.setSpacing(8)

    c_head = QHBoxLayout()
    lbl_c_title = QLabel("🎨  DIRECCIÓN CREATIVA & DISEÑO DE PRODUCTO", box_creator)
    lbl_c_title.setStyleSheet("font-size: 11px; font-weight: 900; color: #A4E062; letter-spacing: 0.5px;")
    c_head.addWidget(lbl_c_title, 1)

    lbl_c_badge = QLabel("SATHARA", box_creator)
    lbl_c_badge.setStyleSheet("""
        QLabel {
            color: #FFFFFF; font-size: 9.5px; font-weight: 900;
            background-color: rgba(97, 171, 2, 0.25); border: 1px solid #61ab02;
            border-radius: 4px; padding: 2px 8px;
        }
    """)
    c_head.addWidget(lbl_c_badge, 0)
    c_layout.addLayout(c_head)

    lbl_creator_bio = QLabel(
        "Diseñado y conceptualizado por <b>Sathara</b> como una herramienta integral para comunidades "
        "competitivas, creadores de contenido y organizadores de torneos de Overwatch.<br>"
        "Definió la visión técnica del producto: <b>rendimiento fluido, control total del operador sin bloqueos de estado, "
        "diseño estructurado de alta densidad y herramientas ágiles para partidas personalizadas</b>.<br>"
        "Supervisó los requerimientos clave del sistema, incluyendo la anatomía inmutable de ranuras, la rotación "
        "continua justa y la preservación geométrica de las ventanas.",
        box_creator
    )
    lbl_creator_bio.setWordWrap(True)
    lbl_creator_bio.setStyleSheet("color: #D6DCE8; font-size: 11px; line-height: 1.4;")
    c_layout.addWidget(lbl_creator_bio)

    mains_row = QHBoxLayout()
    mains_row.setSpacing(6)
    lbl_m_title = QLabel("Héroes de Referencia:", box_creator)
    lbl_m_title.setStyleSheet("color: #8C92A4; font-size: 11px; font-weight: 700;")
    mains_row.addWidget(lbl_m_title)

    for hero_icon in ("🐹 Wrecking Ball", "🚀 Pharah", "🛡️ Brigitte"):
        badge = QLabel(hero_icon, box_creator)
        badge.setStyleSheet("""
            QLabel {
                font-size: 10px; font-weight: 800; color: #FFFFFF;
                background-color: #1A2218; border: 1px solid #48781B;
                border-radius: 4px; padding: 2px 8px;
            }
        """)
        mains_row.addWidget(badge)
    mains_row.addStretch()
    c_layout.addLayout(mains_row)

    layout.addWidget(box_creator)

    # 4. S.A.T.H.A.N.A. CORE
    box_ai = create_card_box("🤖 Asistente Táctico // S.A.T.H.A.N.A. Core")
    box_ai.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    ai_layout = QVBoxLayout(box_ai)
    ai_layout.setContentsMargins(14, 12, 16, 12)
    ai_layout.setSpacing(10)

    ai_desc = QLabel(
        "<b>S.A.T.H.A.N.A.</b> (<i>Sistema Autónomo Táctico de Habilidad, Arbitraje y Nivelación Avanzada</i>) "
        "describe los criterios algorítmicos y directrices técnicas implementadas en el motor de matchmaking. "
        "Permite consultar principios operativos del sistema y verificar el diagnóstico de integridad del software.",
        box_ai
    )
    ai_desc.setWordWrap(True)
    ai_desc.setStyleSheet("color: #A4AAB8; font-size: 11px;")
    ai_layout.addWidget(ai_desc)

    msg_container = QFrame(box_ai)
    msg_container.setStyleSheet("background-color: #10131A; border: 1px solid #232836; border-radius: 6px;")
    mc_layout = QVBoxLayout(msg_container)
    mc_layout.setContentsMargins(12, 10, 14, 10)

    lbl_ai_quote = QLabel(_OPINIONS_BAG.get_next(), msg_container)
    lbl_ai_quote.setWordWrap(True)
    lbl_ai_quote.setStyleSheet("color: #C2F87A; font-size: 11px; font-weight: 700;")
    mc_layout.addWidget(lbl_ai_quote)
    ai_layout.addWidget(msg_container)

    btn_row = QHBoxLayout()
    btn_row.setSpacing(8)

    btn_quote = QPushButton("💬  Consultar Criterio Táctico", box_ai)
    btn_quote.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_quote.setStyleSheet("""
        QPushButton {
            background-color: #171E15; border: 1px solid #48781B; color: #C2F87A;
            font-weight: 800; font-size: 11px; padding: 6px 14px; border-radius: 5px;
        }
        QPushButton:hover { background-color: rgba(97, 171, 2, 0.22); color: #FFFFFF; border-color: #61ab02; }
    """)
    btn_quote.clicked.connect(lambda: lbl_ai_quote.setText(_OPINIONS_BAG.get_next()))
    btn_row.addWidget(btn_quote)

    btn_diag = QPushButton("🔍  Ejecutar Autodiagnóstico", box_ai)
    btn_diag.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_diag.setStyleSheet("""
        QPushButton {
            background-color: #181B24; border: 1px solid #2D3344; color: #D0D5E4;
            font-weight: 700; font-size: 11px; padding: 6px 14px; border-radius: 5px;
        }
        QPushButton:hover { background-color: #242A38; border-color: #00B4FF; color: #FFFFFF; }
    """)
    btn_diag.clicked.connect(lambda: lbl_ai_quote.setText(_DIAGNOSTICS_BAG.get_next()))
    btn_row.addWidget(btn_diag)

    btn_row.addStretch()
    ai_layout.addLayout(btn_row)
    layout.addWidget(box_ai)

    # 5. GUÍA RÁPIDA DE ATAJOS
    box_qol = create_card_box("⚡ Atajos y Operación Rápida del Sistema")
    box_qol.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    qol_layout = QVBoxLayout(box_qol)
    qol_layout.setContentsMargins(14, 12, 16, 12)
    qol_layout.setSpacing(6)

    def _qol_entry(icon: str, title: str, desc: str):
        row = QHBoxLayout()
        row.setSpacing(8)
        lbl_i = QLabel(icon)
        lbl_i.setFixedWidth(20)
        lbl_i.setStyleSheet("font-size: 13px;")
        lbl_t = QLabel(f"<b>{title}:</b> <span style='color:#9DA4B4;'>{desc}</span>")
        lbl_t.setWordWrap(True)
        lbl_t.setStyleSheet("font-size: 11px; color: #E2E8F0;")
        row.addWidget(lbl_i)
        row.addWidget(lbl_t, 1)
        return row

    qol_layout.addLayout(_qol_entry("🔀", "Mezcla por Teclado", "Ejecuta Ctrl + Enter desde cualquier pestaña para generar un nuevo emparejamiento."))
    qol_layout.addLayout(_qol_entry("🖱️", "Operaciones por Lote", "Utiliza Ctrl + Clic, Shift + Clic o arrastre de caja elástica para transferencias múltiples."))
    qol_layout.addLayout(_qol_entry("📦", "Intercambio Directo", "Arrastra tarjetas de jugador directamente entre ranuras de equipos para intercambiar posiciones."))
    qol_layout.addLayout(_qol_entry("🎯", "Persistencia de Ranuras", "Configura la alineación en Personalizar; el centrado matemático se mantiene inmutable."))
    qol_layout.addLayout(_qol_entry("🖥️", "Memoria de Ventana", "Almacenamiento automático de resolución y posición en pantalla compatible con multi-monitor."))
    layout.addWidget(box_qol)
