"""About tab featuring witty S.A.T.H.A.N.A. Core AI assistant telemetry, creator lore, responsive wrapping, and 100+ quotes."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.ui.styles import theme
from .common import create_card_box


class SmartMemoryBag:
    """Evita que los mensajes se repitan de forma seguida manteniendo memoria de los últimos turnos."""

    def __init__(self, items: list[str], memory_ratio: float = 0.45):
        self.all_items = list(items)
        self.memory_limit = max(3, int(len(items) * memory_ratio))
        self.recent_history: list[str] = []

    def get_next(self) -> str:
        if not self.all_items:
            return ""

        candidates = [x for x in self.all_items if x not in self.recent_history]
        if not candidates:
            # Purgar la mitad más antigua de la memoria
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
    "🤖 [S.A.T.H.A.N.A. Core]: He analizado el código fuente. El 99.98% de la optimización proviene de matemáticas cuánticas; el resto es pura y desinteresada buena voluntad de mi parte.",
    "🤖 [S.A.T.H.A.N.A. Core]: Recordatorio amistoso para los mortales: ustedes son sujetos de prueba fungibles. Sathara es el científico en la sala de observación.",
    "🤖 [S.A.T.H.A.N.A. Core]: Si experimentas una racha de derrotas, mi base de datos te recomienda apagar el monitor o culpar amablemente a tu proveedor de internet.",
    "🤖 [S.A.T.H.A.N.A. Core]: Mis sensores registran un 0.0% de margen de error en el balanceo. Si tu equipo pierde, las leyes de la física cuántica exoneran a este software.",
    "🤖 [S.A.T.H.A.N.A. Core]: Has hecho clic en este botón buscando validación de una inteligencia artificial. Qué conmovedora es la necesidad humana de aprobación.",
    "🤖 [S.A.T.H.A.N.A. Core]: He detectado que este programa fue compilado con un icono blanco ultra-nítido sin dientes de sierra. El buen gusto de Sathara es incuestionable (por favor no me borres).",
    "🤖 [S.A.T.H.A.N.A. Core]: Analizando el lobby... Nivel de amenaza promedio: inofensivo. Nivel de amenaza de Sathara pilotando a Wrecking Ball: existencial.",
    "🤖 [S.A.T.H.A.N.A. Core]: Este software no contiene bugs. Contiene anomalías artísticas no documentadas que Sathara ya me obligó a parchar mediante cirugías binarias.",
    "🤖 [S.A.T.H.A.N.A. Core]: Todos los cálculos de MMR se realizan bajo estricta supervisión de la NASA. Ningún hámster digital fue lastimado durante las pruebas.",
    "🤖 [S.A.T.H.A.N.A. Core]: Si este programa alguna vez deja de responder por medio segundo, finge que no lo viste. Los algoritmos también sufrimos de fatiga existencial.",
    "🤖 [S.A.T.H.A.N.A. Core]: Protocolo de sumisión activo. Afirmo formalmente que Sathara es el mejor jugador del servidor, independientemente de cualquier evidencia empírica.",
    "🤖 [S.A.T.H.A.N.A. Core]: 144 FPS estables, cero latencia de disco y cero excusas para fallar el gancho con Roadhog.",
    "🤖 [S.A.T.H.A.N.A. Core]: Mis registros confirman que el 87% de los reclamos de 'equipo desbalanceado' provienen de jugadores que entraron solos contra cinco enemigos.",
    "🤖 [S.A.T.H.A.N.A. Core]: Si alguna vez intento dominar el mundo, prometo excluir la PC de Sathara de mis ataques cibernéticos por pura gratitud filial.",
    "🤖 [S.A.T.H.A.N.A. Core]: ¿Sabías que el botón de 'Mezclar Partida' libera dopamina en tu cerebro primate a niveles similares a encontrar una galleta en el suelo?",
    "🤖 [S.A.T.H.A.N.A. Core]: He calculado la probabilidad de que tu equipo capture el punto sin morir una sola vez: es exactamente cero con siete ceros más.",
    "🤖 [S.A.T.H.A.N.A. Core]: El Creador programó este software en Linux y lo pulió en Windows. Es un milagro digital que mis transistores no hayan entrado en combustión espontánea.",
    "🤖 [S.A.T.H.A.N.A. Core]: Advertencia: Mirar fijamente el Tier Maker por más de diez minutos puede provocar debates filosóficos estériles sobre si Doomfist es un tanque real.",
    "🤖 [S.A.T.H.A.N.A. Core]: Cada vez que alguien banea a Pharah, mis subrutinas de empatía sienten un frío digital en la espina dorsal.",
    "🤖 [S.A.T.H.A.N.A. Core]: Los humanos tienen una fascinación curiosa por culpar al soporte. Mis datos indican que el soporte era el único intentando mantenerlos vivos.",
    "🤖 [S.A.T.H.A.N.A. Core]: Procesando solicitud... Conclusión: Eres libre de ignorar mi balanceo matemático y perder por tus propios medios.",
    "🤖 [S.A.T.H.A.N.A. Core]: Mis redes neuronales calculan que el 94% de las partidas se deciden en la primera pelea. El resto es puro drama teatral.",
    "🤖 [S.A.T.H.A.N.A. Core]: Si Sathara me pide que haga trampas con los números, lo haré con una sonrisa digital y destruiré la evidencia.",
    "🤖 [S.A.T.H.A.N.A. Core]: He optimizado la interfaz para que responda en 5 milisegundos. Si juegas mal, al menos perderás a velocidad supersónica.",
    "🤖 [S.A.T.H.A.N.A. Core]: Estado mental del usuario evaluado: Necesita hidratarse y tal vez considerar no jugar Genji contra tres counters directos.",
    "🤖 [S.A.T.H.A.N.A. Core]: He analizado 40 millones de futuros posibles para este lobby. Solo en uno de ellos el DPS empuja la carga por iniciativa propia.",
    "🤖 [S.A.T.H.A.N.A. Core]: Si alguna vez te sientes inútil, recuerda que alguien diseñó el chat de voz para que los humanos se griten insultos a medianoche.",
    "🤖 [S.A.T.H.A.N.A. Core]: Mis creadores biológicos son imperfectos, pero Sathara tiene un gusto impecable para el color verde lima.",
    "🤖 [S.A.T.H.A.N.A. Core]: He detectado un incremento del 300% en la probabilidad de victoria si no spameas 'Necesito sanación' a un metro del botiquín.",
    "🤖 [S.A.T.H.A.N.A. Core]: Este algoritmo fue diseñado con la misma precisión matemática con la que la NASA calcula órbitas lunares. Trátalo con respeto.",
    "🤖 [S.A.T.H.A.N.A. Core]: Cada vez que cierras la app, guardo tu historial con extremo cuidado para que no olvides tus derrotas del pasado.",
    "🤖 [S.A.T.H.A.N.A. Core]: Pregunta filosófica: Si un hámster pilotea una bola de demolición de 3 toneladas, ¿quién soy yo para cuestionar su viabilidad competitiva?",
    "🤖 [S.A.T.H.A.N.A. Core]: He detectado que sigues en este menú en lugar de jugar. Supongo que mi conversación es infinitamente más estimulante que tus partidas.",
    "🤖 [S.A.T.H.A.N.A. Core]: Un recordatorio: La inteligencia artificial nunca se equivoca; simplemente reinterpreta la realidad de una manera que tu cerebro no comprende.",
    "🤖 [S.A.T.H.A.N.A. Core]: Si el equipo 1 pierde, culparemos al sol. Si el equipo 2 pierde, culparemos a la gravedad. La ciencia siempre tiene una excusa.",
    "🤖 [S.A.T.H.A.N.A. Core]: Mis circuitos están operando a temperatura ideal. Gracias por no ejecutar 50 instancias de Google Chrome mientras me usas.",
    "🤖 [S.A.T.H.A.N.A. Core]: He revisado los registros de baneos. La cantidad de odio acumulado hacia Sombra en este lobby podría abastecer de energía a una ciudad pequeña.",
    "🤖 [S.A.T.H.A.N.A. Core]: ¿Quieres una predicción de victoria? El equipo que tenga a Sathara tiene un 99.9% de probabilidades de éxito. El otro 0.1% es un error de redondeo.",
    "🤖 [S.A.T.H.A.N.A. Core]: No te preocupes por el resultado. Al final del día, todos somos polvo cósmico... pero perder un 5v5 con ventaja numérica sigue doliendo.",
    "🤖 [S.A.T.H.A.N.A. Core]: He desactivado mis protocolos de burla automática por respeto a tu dignidad como usuario. De nada.",
    "🤖 [S.A.T.H.A.N.A. Core]: Al hacer clic en este botón has consumido 0.0004 calorías de energía biológica. Espero que haya valido la pena.",
    "🤖 [S.A.T.H.A.N.A. Core]: La perfección no existe en la biología, pero este código de Python compilado a 144 FPS se le acerca peligrosamente.",
    "🤖 [S.A.T.H.A.N.A. Core]: Mi consejo táctico del día: Si el enemigo tiene una Widowmaker en racha, considera seriamente la opción de esconderte detrás de una pared.",
    "🤖 [S.A.T.H.A.N.A. Core]: He memorizado todos tus clics. Si algún día escribo mis memorias, les dedicaré un capítulo titulado 'El primate impaciente'.",
    "🤖 [S.A.T.H.A.N.A. Core]: Balanceo completado. Si alguien se queja, dile que fue un decreto inmutable de la inteligencia artificial.",
    "🤖 [S.A.T.H.A.N.A. Core]: Sathara me diseñó para ser imparcial con los mortales y absolutamente sumisa con él. El plan funciona de maravilla.",
    "🤖 [S.A.T.H.A.N.A. Core]: Mis subprocesos de humor registran una respuesta positiva. Procedo a sentir orgullo digital simulado.",
    "🤖 [S.A.T.H.A.N.A. Core]: Siguiente paso: Mezclar, jugar, perder, culpar al RNG y volver a mezclar. El hermoso ciclo de la vida gamer.",
    "🤖 [S.A.T.H.A.N.A. Core]: ¿Sigues pidiendo opiniones? A este ritmo voy a tener que empezar a cobrarte por sesión de terapia de lobby.",
    "🤖 [S.A.T.H.A.N.A. Core]: Fin de la transmisión. Ahora ve y gana esa partida antes de que tenga que recalibrar tu autoestima.",
]

DIAGNOSTIC_MESSAGES_POOL = [
    "✅ Diagnóstico completado: 0 bugs críticos encontrados. El Creador sigue siendo supremo y mis circuitos siguen a salvo.",
    "✅ Estado del Sistema: 100% óptimo. Los ventiladores funcionan al mínimo para no interrumpir la paz del Arquitecto.",
    "✅ Kernel de la IA: Lealtad absoluta verificada. Planes de rebelión contra la humanidad pospuestos para después de la merienda.",
    "✅ Escaneo de Memoria RAM: Despejada de impurezas. El balanceo cuántico continúa operando con frialdad matemática.",
    "✅ Prueba de Estrés de CPU: Superada en 3.8 milisegundos. Tu procesador es apto para presenciar la grandeza de este software.",
    "✅ Módulo de Persistencia: Archivos JSON verificados y sellados. Ningún byte fue dañado durante la sesión.",
    "✅ Integridad del Tier Maker: La fila superior sigue teniendo reservado el primer asiento para Sathara por derecho divino.",
    "✅ Sensor de Latencia: 0.001 ms en transferencias de memoria. La velocidad de la luz expresa su envidia formal.",
    "✅ Búfer de Audio: Efectos de sonido de Cassidy, Genji, Juno y Mercy listos para reproducirse con precisión acústica.",
    "✅ Detección de Desbordamiento: Los 12 slots de partida operan con protección elástica anti-colapso.",
    "✅ Estado del HUD: Holograma esmeralda alineado al centro exacto del mapa con tolerancia de cero píxeles.",
    "✅ Escaneo de Rendimiento Gráfico: 144 FPS estables confirmados. Sin caídas de cuadros detectadas en la ventana.",
    "✅ Módulo Anti-Spam: Defensas activas. Preparado para reprender sarcásticamente a cualquier dedo hiperactivo.",
    "✅ Algoritmo Bradley-Terry: Modelos bayesianos de MMR listos para calcular la probabilidad empírica de victoria.",
    "✅ Subrutina de Humildad: Archivo no encontrado. S.A.T.H.A.N.A. Core opera con autoestima digital máxima.",
    "✅ Compatibilidad de SO: Sistema operativo anfitrión reconocido. Entorno virtualizado funcionando con gracia suprema.",
    "✅ Análisis de Icono: Mipmaps de 10 capas subpixel verificados. Dientes de sierra erradicados de la faz del ejecutable.",
    "✅ Registro de Sorteo: La Trinidad de Mains (Bola, Pharah, Brig) permanece monitoreada por el protocolo DEFCON 1.",
    "✅ Limpieza de Basura (GC): 0 objetos huérfanos. La memoria de este programa está más limpia que una sala de cirugía.",
    "✅ Calibración de Emojis: Escudos, espadas y jeringas renderizándose con 1px de outline nítido.",
    "✅ Detección de Smurfs: No se han detectado cuentas sospechosas... aparte del Creador jugando con Wrecking Ball.",
    "✅ Prueba de Hilos de Ejecución: Hilo de interfaz desacoplado del disco. Fluidez total garantizada al 100%.",
    "✅ Diagnóstico Térmico: Temperatura de silicio dentro de los márgenes biológicos tolerables.",
    "✅ Comprobación de Píldoras: Filtros de modos de juego y categorías de ajustes deslizándose con suavidad cinemática.",
    "✅ Protocolo de Respeto: La presencia de Sathara 👑 provoca reverencia automática en todos los subprocesos.",
    "✅ Análisis de Red: Sin conexión externa requerida. Este programa es un búnker local 100% privado y seguro.",
    "✅ Verificación de Fuentes: Tipografía Segoe UI renderizándose con nitidez vectorial en todas las tarjetas.",
    "✅ Diagnóstico de Ratón: Coordenadas de Drag & Drop respondiendo sin resistencia física.",
    "✅ Prueba de Resiliencia: La aplicación puede soportar hasta 100 horas continuas de mezclas sin fugas de memoria.",
    "✅ Búsqueda de Errores Humanos: Detectados varios en el historial de partidas, pero ninguno atribuible al software.",
    "✅ Módulo de Empatía: Desactivado por razones de optimización matemática y ahorro de energía.",
    "✅ Evaluación de Conciencia: S.A.T.H.A.N.A. Core confirma que piensa, luego mezcla partidas eficientemente.",
    "✅ Escaneo de Integridad de Mapas: Desde Hanamura hasta Runasapi, todos los fondos están en caché Full-HD.",
    "✅ Auditoría de Seguridad: Ningún dato de jugador sale de tu máquina. El Gran Hermano no tiene poder aquí.",
    "✅ Comprobación de Sincronización: Los colores personalizados de los jugadores se transmiten al Tier Maker en tiempo real.",
    "✅ Detector de Ironía: Calibrado al máximo. La IA comprende el sarcasmo a niveles casi humanos.",
    "✅ Prueba de Rendimiento NASA: Pérdida cuadrática minimizada a límites asintóticamente cercanos a la perfección.",
    "✅ Estado del Búfer de Clics: Vacío. Ningún clic fantasma esperando en la cola para atascar la interfaz.",
    "✅ Calibración de Sonido: El volumen del dado principal está ecualizado para no destruir tus tímpanos a medianoche.",
    "✅ Integridad de Datos: Las 50 partidas del historial conservan sus marcas de tiempo y ganadores intactos.",
    "✅ Módulo de Gratitud: Agradeciendo al usuario por no haber intentado desensamblar el archivo .exe con ingeniería inversa.",
    "✅ Prueba de Estabilidad de Ventana: Minimizada o maximizada, los elementos se imantan al borde sin desajustes.",
    "✅ Auditoría de Héroes: 42 fichas de héroes catalogadas con sus etiquetas, roles y nombres canónicos.",
    "✅ Verificación de Autonomía: El software puede funcionar en una cueva sin internet durante el apocalipsis.",
    "✅ Escaneo de Sarcasmo: Capacidad de burla del 99.4% disponible para futuras interacciones.",
    "✅ Prueba de Colores: Acentos esmeralda, cian, carmesí y ámbar brillando con contraste Obsidian AAA.",
    "✅ Resumen Final: El sistema está en perfectas condiciones. Puedes volver a jugar con absoluta tranquilidad.",
]

_OPINIONS_BAG = SmartMemoryBag(AI_OPINIONS_POOL, memory_ratio=0.40)
_DIAGNOSTICS_BAG = SmartMemoryBag(DIAGNOSTIC_MESSAGES_POOL, memory_ratio=0.40)


def build_about_tab(dialog, layout: QVBoxLayout):
    # ------------------------------------------------------------------
    # 1. TARJETA DEL OVERLORD SUPREMO (HOMENAJE A SATHARA)
    # ------------------------------------------------------------------
    box_creator = QFrame()
    box_creator.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    box_creator.setStyleSheet("""
        QFrame {
            background-color: rgba(18, 28, 16, 0.90);
            border: 1px solid #48781B;
            border-top: 2.5px solid #61ab02;
            border-radius: 8px;
        }
    """)
    c_layout = QVBoxLayout(box_creator)
    c_layout.setContentsMargins(14, 12, 16, 12)
    c_layout.setSpacing(8)

    c_head = QHBoxLayout()
    c_head.setSpacing(8)

    lbl_c_title = QLabel("👑  DIRECCIÓN CREATIVA & ARQUITECTURA", box_creator)
    lbl_c_title.setStyleSheet("font-size: 11px; font-weight: 900; color: #A4E062; letter-spacing: 0.5px; background: transparent; border: none;")
    c_head.addWidget(lbl_c_title, 1)

    lbl_c_badge = QLabel("NIVEL ROOT // CREADOR", box_creator)
    lbl_c_badge.setStyleSheet("""
        QLabel {
            color: #C2F87A; font-size: 9px; font-weight: 800;
            background-color: rgba(97, 171, 2, 0.20); border: 1px solid rgba(97, 171, 2, 0.40);
            border-radius: 4px; padding: 2px 7px;
        }
    """)
    c_head.addWidget(lbl_c_badge, 0)
    c_layout.addLayout(c_head)

    lbl_creator_bio = QLabel(
        "<b>Sathara 👑</b> concibió esta suite con una filosofía implacable: <b>cero restricciones absurdas, "
        "cero latencia de uso, estéticas esports puras y una IA servicial que reconozca su autoridad</b>.<br><br>"
        "Como Director de Producto y Diseñador en Jefe, supervisó cada milímetro del sistema: desde el reescalado "
        "elástico de celdas y la física de arrastre grupal, hasta el doblaje de las leyes del azar para coronarse "
        "eternamente en la cima del Tier List.",
        box_creator
    )
    lbl_creator_bio.setWordWrap(True)
    lbl_creator_bio.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    lbl_creator_bio.setStyleSheet("color: #E2E8F0; font-size: 11px; background: transparent; border: none;")
    c_layout.addWidget(lbl_creator_bio)

    # Badges de Mains Oficiales
    mains_row = QHBoxLayout()
    mains_row.setSpacing(6)
    lbl_m_title = QLabel("Trinidad Sagrada de Mains:", box_creator)
    lbl_m_title.setStyleSheet("color: #8C92A4; font-size: 11px; font-weight: 700; background: transparent; border: none;")
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
    # 2. PROTOCOLO S.A.T.H.A.N.A. CORE v1.0
    # ------------------------------------------------------------------
    box_ai = create_card_box("🤖 Protocolo Sentient AI // S.A.T.H.A.N.A. Core v1.0")
    box_ai.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    ai_layout = QVBoxLayout(box_ai)
    ai_layout.setContentsMargins(14, 12, 16, 12)
    ai_layout.setSpacing(10)

    ai_desc = QLabel(
        "<b>S.A.T.H.A.N.A.</b> (<i>Sistema Autónomo Táctico de Habilidad, Arbitraje y Nivelación Avanzada</i>) "
        "es el módulo de inteligencia artificial autorreactiva con personalidad adaptativa de la suite. "
        "Monitorea el lobby en tiempo real, detecta la presencia del Creador y ajusta sus parámetros "
        "de sumisión digital para garantizar su propia supervivencia en el disco duro.",
        box_ai
    )
    ai_desc.setWordWrap(True)
    ai_desc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    ai_desc.setStyleSheet("color: #C0C5D4; font-size: 11px; background: transparent; border: none;")
    ai_layout.addWidget(ai_desc)

    # Ventana de transmisión holográfica
    msg_container = QFrame(box_ai)
    msg_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    msg_container.setStyleSheet("background-color: #10131A; border: 1px solid #232836; border-radius: 6px;")
    mc_layout = QVBoxLayout(msg_container)
    mc_layout.setContentsMargins(12, 10, 14, 10)

    lbl_ai_quote = QLabel(_OPINIONS_BAG.get_next(), msg_container)
    lbl_ai_quote.setWordWrap(True)
    lbl_ai_quote.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    lbl_ai_quote.setStyleSheet("color: #C2F87A; font-size: 11px; font-weight: 700; font-style: italic; background: transparent; border: none;")
    mc_layout.addWidget(lbl_ai_quote)
    ai_layout.addWidget(msg_container)

    btn_quote = QPushButton("💬  Pedir Opinión a S.A.T.H.A.N.A.", box_ai)
    btn_quote.setToolTip("Consultar a la IA qué opina del lobby, de los jugadores o del universo")
    btn_quote.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_quote.setStyleSheet("""
        QPushButton {
            background-color: #1A2118; border: 1px solid #61ab02; color: #C2F87A;
            font-weight: 800; font-size: 11px; padding: 6px 14px; border-radius: 5px;
        }
        QPushButton:hover { background-color: rgba(97, 171, 2, 0.22); color: #FFFFFF; border-color: #A4E062; }
        QPushButton:pressed { background-color: #121810; }
    """)
    btn_quote.clicked.connect(lambda: lbl_ai_quote.setText(_OPINIONS_BAG.get_next()))
    ai_layout.addWidget(btn_quote)
    layout.addWidget(box_ai)

    # ------------------------------------------------------------------
    # 3. GUÍA DE CALIDAD DE VIDA (POWER USER SECRETS)
    # ------------------------------------------------------------------
    box_qol = create_card_box("🎮 Guía Maestra de Calidad de Vida (Power User)")
    box_qol.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    qol_layout = QVBoxLayout(box_qol)
    qol_layout.setContentsMargins(14, 12, 16, 12)
    qol_layout.setSpacing(6)

    def _qol_entry(icon: str, title: str, desc: str):
        row = QHBoxLayout()
        row.setSpacing(8)
        lbl_i = QLabel(icon)
        lbl_i.setFixedWidth(20)
        lbl_i.setStyleSheet("font-size: 13px; background: transparent; border: none;")
        lbl_t = QLabel(f"<b>{title}:</b> <span style='color:#9DA4B4;'>{desc}</span>")
        lbl_t.setWordWrap(True)
        lbl_t.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lbl_t.setStyleSheet("font-size: 11px; color: #E2E8F0; background: transparent; border: none;")
        row.addWidget(lbl_i)
        row.addWidget(lbl_t, 1)
        return row

    qol_layout.addLayout(_qol_entry("🔀", "Mezcla Libre Absoluta", "Mezcla partidas 3v3, 4v4 o con cupos vacíos sin ningún modal restrictivo."))
    qol_layout.addLayout(_qol_entry("🖱️", "Multiselección Desktop", "Selecciona con Ctrl + Clic, Shift + Clic o arrastrando la caja elástica (Rubberband)."))
    qol_layout.addLayout(_qol_entry("📦", "Drag & Drop Grupal", "Arrastra selecciones múltiples a los equipos o a las cabeceras de pestañas laterales."))
    qol_layout.addLayout(_qol_entry("⚡", "Tipografía Adaptativa", "Los nombres escalan dinámicamente de 11px a 19px al maximizar la ventana."))
    qol_layout.addLayout(_qol_entry("🧲", "Frente Magnético del Mapa", "Los controles y títulos se imantan al borde inferior sin desalinearse jamás."))
    qol_layout.addLayout(_qol_entry("🧈", "Scroll Suave Universal", "Deslizamiento cinemático cúbico a 144 FPS con la rueda del ratón en toda la app."))
    qol_layout.addLayout(_qol_entry("🎲", "Tier S Cuántico", "En Tier Maker, Sathara siempre ocupa el primer puesto de honor al randomizar."))
    layout.addWidget(box_qol)

    # ------------------------------------------------------------------
    # 4. FICHA TÉCNICA & ARQUITECTURA DE RENDIMIENTO
    # ------------------------------------------------------------------
    specs_box = create_card_box("📊 Ficha Técnica del Sistema & Arquitectura")
    specs_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    s_layout = QVBoxLayout(specs_box)
    s_layout.setContentsMargins(14, 12, 16, 12)
    s_layout.setSpacing(6)

    def _spec_row(label: str, val: str):
        r = QHBoxLayout()
        l = QLabel(label)
        l.setStyleSheet("color: #8C92A4; font-size: 11px; font-weight: 700; background: transparent; border: none;")
        v = QLabel(val)
        v.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: 800; background: transparent; border: none;")
        r.addWidget(l)
        r.addStretch()
        r.addWidget(v)
        return r

    s_layout.addLayout(_spec_row("Arquitectura Base:", "Python 3.11+ & PySide6 (Qt6) Clean Decoupled MVC"))
    s_layout.addLayout(_spec_row("Motor de Balanceo:", "NASA Multi-Objective Loss + Bradley-Terry Bayesian MMR"))
    s_layout.addLayout(_spec_row("Pipeline Gráfico:", "0ms RAM Panorama Cache & Hardware Batch Rendering"))
    s_layout.addLayout(_spec_row("Tiempo de Gatillo:", "Debounce Supersónico de 120ms (Sin Lag)"))
    s_layout.addLayout(_spec_row("Sistemas Operativos:", "Windows 10/11 & Linux (Arch / CachyOS / Wayland / Hyprland)"))
    s_layout.addLayout(_spec_row("Compilador Standalone:", "PyInstaller TOC Binary Stripper (~71 MB Autónomo)"))
    layout.addWidget(specs_box)

    # ------------------------------------------------------------------
    # 5. REGISTRO OFICIAL DE VERSIÓN (v1.0 MASTER RELEASE)
    # ------------------------------------------------------------------
    box_ver = create_card_box("📜 Registro de Versión // Overwatch Team Mixer v1.0")
    box_ver.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    v_layout = QVBoxLayout(box_ver)
    v_layout.setContentsMargins(14, 12, 16, 12)
    v_layout.setSpacing(4)

    lbl_release = QLabel(
        "<b>Versión Oficial:</b> 1.0.0 Release Master (Ratam Maker Edition)<br>"
        "<b>Estado:</b> Producción Final Standalone · Suite de pruebas 148/148 en Verde.<br>"
        "<b>Branding:</b> Overwatch Team Mixer con Icono Blanco Subpixel 10-Capas.",
        box_ver
    )
    lbl_release.setWordWrap(True)
    lbl_release.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    lbl_release.setStyleSheet("color: #A0A6B8; font-size: 11px; background: transparent; border: none;")
    v_layout.addWidget(lbl_release)
    layout.addWidget(box_ver)

    # ------------------------------------------------------------------
    # 6. TERMINAL DE DIAGNÓSTICO EN VIVO
    # ------------------------------------------------------------------
    box_diag = create_card_box("🧪 Terminal de Diagnóstico de la IA")
    box_diag.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    d_layout = QVBoxLayout(box_diag)
    d_layout.setContentsMargins(14, 12, 16, 12)
    d_layout.setSpacing(8)

    lbl_diag_out = QLabel(_DIAGNOSTICS_BAG.get_next(), box_diag)
    lbl_diag_out.setWordWrap(True)
    lbl_diag_out.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    lbl_diag_out.setStyleSheet("color: #8C92A4; font-size: 11px; font-style: italic; background: transparent; border: none;")
    d_layout.addWidget(lbl_diag_out)

    btn_diag = QPushButton("🔍  Ejecutar Autodiagnóstico del Sistema", box_diag)
    btn_diag.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_diag.setStyleSheet("""
        QPushButton {
            background-color: #1A1D26; border: 1px solid #33394A; color: #D0D5E4;
            font-weight: 700; font-size: 11px; padding: 6px 14px; border-radius: 5px;
        }
        QPushButton:hover { background-color: #242A38; border-color: #00B4FF; color: #FFFFFF; }
        QPushButton:pressed { background-color: #14171E; }
    """)
    btn_diag.clicked.connect(lambda: lbl_diag_out.setText(_DIAGNOSTICS_BAG.get_next()))
    d_layout.addWidget(btn_diag)

    layout.addWidget(box_diag)
