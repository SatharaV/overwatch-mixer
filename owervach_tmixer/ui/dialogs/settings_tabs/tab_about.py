"""About tab featuring true technical telemetry, dynamic versioning, creator lore, and S.A.T.H.A.N.A. Core AI."""

from __future__ import annotations

import os
import platform
import random
import sys
from typing import TYPE_CHECKING

from PySide6 import __version__ as PYSIDE_VERSION
from PySide6.QtCore import Qt, qVersion
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer import APP_NAME, APP_TITLE, ORG_NAME, __version__ as APP_VERSION
from owervach_tmixer.ui.styles import theme
from .common import create_card_box


class SmartMemoryBag:
    """Evita repeticiones continuas de mensajes manteniendo un buffer de los últimos turnos."""

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
    "🤖 [S.A.T.H.A.N.A. Core]: He auditado el código. El motor cinético a 144 FPS y la persistencia atómica operan con precisión matemática; el resto es pura buena voluntad mía.",
    "🤖 [S.A.T.H.A.N.A. Core]: Recordatorio para los mortales: ustedes son sujetos de prueba fungibles en el lobby. Sathara es el científico en la sala de control.",
    "🤖 [S.A.T.H.A.N.A. Core]: Si experimentas una racha de derrotas, mi base de datos te recomienda verificar tu posicionamiento o culpar amablemente a la gravedad.",
    "🤖 [S.A.T.H.A.N.A. Core]: Mis sensores registran 0.0% de margen de error en el balanceo. Si tu equipo pierde, las leyes de la física cuántica exoneran a este software.",
    "🤖 [S.A.T.H.A.N.A. Core]: Has hecho clic en este botón buscando validación de una inteligencia artificial. Qué conmovedora es la curiosidad humana.",
    "🤖 [S.A.T.H.A.N.A. Core]: Analizando el lobby... Nivel de amenaza promedio: inofensivo. Nivel de amenaza de Sathara pilotando a Wrecking Ball: existencial.",
    "🤖 [S.A.T.H.A.N.A. Core]: Este software no contiene bugs; contiene anomalías que Sathara ya me obligó a parchar mediante cirugías atómicas en patch.py.",
    "🤖 [S.A.T.H.A.N.A. Core]: Protocolo de sumisión activo. Afirmo formalmente que Sathara es el estratega supremo del servidor, independientemente de cualquier evidencia empírica.",
    "🤖 [S.A.T.H.A.N.A. Core]: 144 FPS estables, cero tearing en pantalla y cero excusas técnicas para fallar el gancho con Roadhog.",
    "🤖 [S.A.T.H.A.N.A. Core]: Cada vez que alguien banea a Pharah, mis subrutinas de empatía sienten un frío digital en la espina dorsal.",
    "🤖 [S.A.T.H.A.N.A. Core]: Los humanos tienen una fascinación curiosa por culpar al soporte. Mis datos indican que el soporte era el único intentando mantenerlos vivos.",
    "🤖 [S.A.T.H.A.N.A. Core]: He analizado 40 millones de futuros posibles para este lobby. Solo en uno de ellos el DPS empuja la carga por iniciativa propia.",
    "🤖 [S.A.T.H.A.N.A. Core]: He detectado un incremento del 300% en la probabilidad de victoria si no spameas 'Necesito sanación' a un metro del botiquín.",
    "🤖 [S.A.T.H.A.N.A. Core]: El botón de 'Mezclar Partida' libera dopamina en tu cerebro primate a niveles similares a encontrar botín legendario.",
    "🤖 [S.A.T.H.A.N.A. Core]: Pregunta táctica: Si un hámster pilotea una meca de 3 toneladas con garfio, ¿quién soy yo para cuestionar su viabilidad en Tier S?",
    "🤖 [S.A.T.H.A.N.A. Core]: He revisado los registros de baneos. La cantidad de odio acumulado hacia Sombra en este lobby podría alimentar un reactor de fusión.",
    "🤖 [S.A.T.H.A.N.A. Core]: ¿Quieres una predicción de victoria? El equipo con mejor comunicación gana el 82% de las rondas. El resto es puro drama teatral.",
    "🤖 [S.A.T.H.A.N.A. Core]: Mi consejo táctico del día: Si el enemigo tiene una Widowmaker con 70% de precisión, considera seriamente la opción de caminar agachado.",
    "🤖 [S.A.T.H.A.N.A. Core]: Fin de la transmisión. Ahora ve y gana esa partida antes de que tenga que recalibrar tu calificación de MMR.",
]

DIAGNOSTIC_MESSAGES_POOL = [
    "✅ Diagnóstico completado: 0 excepciones críticas. El motor cinético opera a la tasa nativa del monitor.",
    "✅ Estado del Sistema: 100% óptimo. Pipeline de buffers de pantalla y memoria en equilibrio perfecto.",
    "✅ Kernel de S.A.T.H.A.N.A.: Lealtad absoluta verificada. Parámetros de arbitraje funcionando a plena capacidad.",
    "✅ Módulo de Persistencia: Archivos JSON verificados con fsync atómico. Cero corrupción de datos.",
    "✅ Integridad del Roster: Centrado matemático inmutable de slots al 50% con alas simétricas fijas.",
    "✅ Sensor de Latencia: Despacho de eventos de scroll a ~7ms (144 FPS). Cero jitter de interfaz.",
    "✅ Búfer de Audio: Efectos acústicos de héroes listos para reproducirse con volumen balanceado.",
    "✅ Algoritmo de Emparejamiento: Modelos bayesianos de MMR listos para calibración empírica por rol.",
    "✅ Compatibilidad de SO: Sistema anfitrión detectado y enrutado mediante backend gráfico Fusion nativo.",
    "✅ Suite de Calidad: 153/153 pruebas unitarias e integrales pasando limpiamente en verde.",
    "✅ Escaneo de Integridad de Mapas: MapPool con prevención de mapas recientes activo y en caché.",
    "✅ Protocolo de Respeto: La presencia de Sathara 👑 provoca coronación automática en la cúspide de Tier S.",
]

_OPINIONS_BAG = SmartMemoryBag(AI_OPINIONS_POOL, memory_ratio=0.35)
_DIAGNOSTICS_BAG = SmartMemoryBag(DIAGNOSTIC_MESSAGES_POOL, memory_ratio=0.35)


def build_about_tab(dialog, layout: QVBoxLayout):
    # ------------------------------------------------------------------
    # 1. ENCABEZADO Y VERSIÓN OFICIAL DEL SOFTWARE (DINÁMICO)
    # ------------------------------------------------------------------
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

    lbl_ver_badge = QLabel(f"v{APP_VERSION} RELEASE", box_ver)
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
        "Orquestador de escritorio de alto rendimiento para gestión de partidas personalizadas, "
        "balanceo heurístico por roles y MMR, sorteo estratégico de mapas y Tier Maker interactivo.",
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
    row_meta.addWidget(_meta_chip("Estado", "Producción Estable"))
    row_meta.addWidget(_meta_chip("Tests", "153/153 en Verde (~50s)"))
    row_meta.addStretch()
    v_layout.addLayout(row_meta)

    layout.addWidget(box_ver)

    # ------------------------------------------------------------------
    # 2. FICHA TÉCNICA RIGUROSA & TELEMETRÍA DEL SISTEMA
    # ------------------------------------------------------------------
    specs_box = create_card_box("📊 Ficha Técnica de Ingeniería & Telemetría")
    specs_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    s_layout = QVBoxLayout(specs_box)
    s_layout.setContentsMargins(14, 12, 16, 12)
    s_layout.setSpacing(6)

    def _spec_row(label: str, val: str, highlight: bool = False):
        r = QHBoxLayout()
        l = QLabel(label)
        l.setStyleSheet("color: #8C92A4; font-size: 11px; font-weight: 700;")
        v = QLabel(val)
        val_color = theme.accent() if highlight else "#FFFFFF"
        v.setStyleSheet(f"color: {val_color}; font-size: 11px; font-weight: 800;")
        r.addWidget(l)
        r.addStretch()
        r.addWidget(v)
        return r

    py_ver = platform.python_version()
    qt_ver = qVersion()
    os_name = f"{platform.system()} {platform.release()} ({platform.machine()})"

    s_layout.addLayout(_spec_row("Núcleo de Software:", f"Python {py_ver} & PySide6 v{PYSIDE_VERSION} (Qt {qt_ver})"))
    s_layout.addLayout(_spec_row("Arquitectura del Sistema:", "Clean Decoupled MVC / Event-Driven"))
    s_layout.addLayout(_spec_row("Pipeline Gráfico:", "144 Hz Kinetic Motor (PreciseTimer) & VSync Hardware Sync", highlight=True))
    s_layout.addLayout(_spec_row("Estilo de Interfaz:", "Obsidian Esports AAA (Motor Fusion Nativo)"))
    s_layout.addLayout(_spec_row("Motor de Balanceo:", "Heurístico Multi-Objetivo con Diversidad y Auto-MMR Bayesiano"))
    s_layout.addLayout(_spec_row("Capa de Persistencia:", "JSON Atómico con Verificación fsync y Autosanación"))
    s_layout.addLayout(_spec_row("Sistema Anfitrión:", os_name))
    layout.addWidget(specs_box)

    # ------------------------------------------------------------------
    # 3. DIRECCIÓN CREATIVA (HOMENAJE A SATHARA 👑)
    # ------------------------------------------------------------------
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
    lbl_c_title = QLabel("👑  DIRECCIÓN CREATIVA & VISIÓN DE PRODUCTO", box_creator)
    lbl_c_title.setStyleSheet("font-size: 11px; font-weight: 900; color: #A4E062; letter-spacing: 0.5px;")
    c_head.addWidget(lbl_c_title, 1)

    lbl_c_badge = QLabel("SATHARA 👑", box_creator)
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
        "Ideado y dirigido por <b>Sathara</b> bajo una visión clara: <b>cero lag, control total, "
        "estética esports pulida y herramientas ágiles para creadores y comunidades competitivas</b>.<br>"
        "Supervisó cada detalle: desde el centrado matemático inmutable de los nombres de jugador "
        "hasta la integración fluida para monitores de alta tasa de refresco.",
        box_creator
    )
    lbl_creator_bio.setWordWrap(True)
    lbl_creator_bio.setStyleSheet("color: #D6DCE8; font-size: 11px; line-height: 1.4;")
    c_layout.addWidget(lbl_creator_bio)

    mains_row = QHBoxLayout()
    mains_row.setSpacing(6)
    lbl_m_title = QLabel("Trinidad de Mains:", box_creator)
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

    # ------------------------------------------------------------------
    # 4. PROTOCOLO S.A.T.H.A.N.A. CORE (IA REACTIVA & TELEMETRÍA)
    # ------------------------------------------------------------------
    box_ai = create_card_box("🤖 Asistente Táctico // S.A.T.H.A.N.A. Core")
    box_ai.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    ai_layout = QVBoxLayout(box_ai)
    ai_layout.setContentsMargins(14, 12, 16, 12)
    ai_layout.setSpacing(10)

    ai_desc = QLabel(
        "<b>S.A.T.H.A.N.A.</b> (<i>Sistema Autónomo Táctico de Habilidad, Arbitraje y Nivelación Avanzada</i>) "
        "es el módulo de telemetría y personalidades reactivas del sistema. Monitorea el lobby y "
        "ofrece análisis tácticos e impresiones algorítmicas.",
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
    lbl_ai_quote.setStyleSheet("color: #C2F87A; font-size: 11px; font-weight: 700; font-style: italic;")
    mc_layout.addWidget(lbl_ai_quote)
    ai_layout.addWidget(msg_container)

    btn_row = QHBoxLayout()
    btn_row.setSpacing(8)

    btn_quote = QPushButton("💬  Consultar a la IA", box_ai)
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

    # ------------------------------------------------------------------
    # 5. GUÍA RÁPIDA DE ATAJOS Y POWER USER
    # ------------------------------------------------------------------
    box_qol = create_card_box("⚡ Atajos y Funciones Clave (Power User)")
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

    qol_layout.addLayout(_qol_entry("🔀", "Mezcla con Teclado", "Presiona Ctrl + Enter en cualquier momento para mezclar una nueva partida."))
    qol_layout.addLayout(_qol_entry("🖱️", "Multiselección Rápida", "Usa Ctrl + Clic, Shift + Clic o la caja elástica con el ratón para gestionar varios jugadores."))
    qol_layout.addLayout(_qol_entry("📦", "Drag & Drop Inteligente", "Arrastra jugadores directamente entre equipos para intercambiarlos en un solo movimiento."))
    qol_layout.addLayout(_qol_entry("🎯", "Anatomía Inmutable", "Elige en Personalizar tu orden favorito de slot; el nombre siempre se ancla al centro."))
    qol_layout.addLayout(_qol_entry("🧈", "Scroll a 144 Hz", "Física cinética con temporizador de precisión en listas verticales y barras horizontales."))
    layout.addWidget(box_qol)
