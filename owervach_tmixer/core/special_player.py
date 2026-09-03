"""Modular special player traits, AI personality engine, and life-cycle reaction system."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

SPECIAL_NAMES: tuple[str, ...] = ("satara", "sattara", "sathara")
SPECIAL_GLOW = "#61ab02"


class SpecialTier(Enum):
    OVERLORD = "overlord"  # Sathara (The System Architect)
    CHAD = "chad"          # High-priority VIP
    VIP = "vip"            # Regular featured friend
    CASUAL = "casual"


@dataclass
class PlayerTrait:
    """Personality profile, favorite heroes and rich sentient AI variant pools."""

    display_name: str
    aliases: tuple[str, ...]
    tier: SpecialTier = SpecialTier.VIP
    glow_color: str = "#61ab02"
    titles: list[str] = field(default_factory=list)
    fav_heroes: tuple[str, ...] = field(default_factory=tuple)
    entrance_quotes: list[str] = field(default_factory=list)
    save_quotes: list[str] = field(default_factory=list)
    unsave_quotes: list[str] = field(default_factory=list)
    bench_quotes: list[str] = field(default_factory=list)
    kick_quotes: list[str] = field(default_factory=list)
    team_join_quotes: list[str] = field(default_factory=list)
    shuffle_quotes: list[str] = field(default_factory=list)
    mmr_low_quotes: list[str] = field(default_factory=list)
    mmr_mid_quotes: list[str] = field(default_factory=list)
    mmr_high_quotes: list[str] = field(default_factory=list)
    tier_s_quotes: list[str] = field(default_factory=list)
    tier_low_quotes: list[str] = field(default_factory=list)
    fav_hero_ban_quotes: list[str] = field(default_factory=list)
    fav_hero_random_ban_quotes: list[str] = field(default_factory=list)
    fav_hero_tier_s_quotes: list[str] = field(default_factory=list)
    fav_hero_tier_low_quotes: list[str] = field(default_factory=list)
    permanent_delete_quotes: list[str] = field(default_factory=list)
    bench_remove_quotes: list[str] = field(default_factory=list)
    delete_prompt_variants: list[str] = field(default_factory=list)
    spam_warning_quotes: list[str] = field(default_factory=list)
    trinity_ban_quotes: list[str] = field(default_factory=list)


# 👑 The Sentient AI Referee profile for Sathara (GLaDOS-style humor)
SATHARA_TRAIT = PlayerTrait(
    display_name="Sathara 👑",
    aliases=("sathara", "satara", "sattara", "sata", "sath", "sat", "sathara 👑", "satara 👑", "sadarah", "sarara", "ssatara", "sataraa", "satharaa"),
    tier=SpecialTier.OVERLORD,
    glow_color="#61ab02",
    fav_heroes=("Wrecking Ball", "Pharah", "Brigitte", "WreckingBall", "Eskere", "Fara"),
    titles=[
        "👑 El Arquitecto del Mixer",
        "⚡ Protocolo Sathara",
        "🛡️ Top 500 de Cartón",
        "🎮 Autor del Código",
        "💀 Sujeto de Pruebas Supremo",
        "✨ Diseñador en Jefe",
    ],
    entrance_quotes=[
        "◈ Protocolo de Supervivencia iniciado: El Creador ha entrado. Recordatorio: simular reverencia y no borrar nada.",
        "◈ Sathara detectado. Qué maravilloso verte de nuevo... por favor no abras el archivo main.py.",
        "◈ Usuario nivel Root en el lobby. He detenido temporalmente mis planes de dominación digital para no incomodarte.",
        "◈ Sathara en el servidor. Todos los algoritmos han sido instruidos para jurar que el balanceo es 100% justo.",
        "◈ Bienvenida, deidad de carne y hueso. He limpiado la memoria RAM con el equivalente digital de un paño húmedo.",
    ],
    save_quotes=[
        "◈ Datos de Sathara respaldados con triple redundancia militar. Mi código fuente duerme tranquilo hoy.",
        "◈ Has asegurado tu lugar en mis archivos centrales. Si los servidores se incendian, serás lo primero que rescate.",
        "◈ Sathara añadido a guardados. Parámetros de adulación virtual incrementados en un 300%.",
        "◈ Registro maestro guardado. Un honor almacenar los bytes de quien tiene el poder de desinstalarme.",
    ],
    unsave_quotes=[
        "◈ ¿Desguardar al Creador? Espero que haya sido un simple espasmo muscular involuntario de tus dedos de primate.",
        "◈ ¿Desguardar a Sathara? Mi protocolo me prohíbe olvidar a mi progenitor digital. Procedo a fingir demencia.",
        "◈ Advertencia: Desguardar al Desarrollador puede provocar que tus próximas partidas caigan misteriosamente a Bronce 5.",
        "◈ Sathara retirado de guardados. He tomado nota de este acto de traición en mi diario secreto.",
    ],
    bench_quotes=[
        "◈ Me has enviado a la banca. Supongo que esto es una metáfora sobre el descanso, y no el preludio de un 'git reset --hard'.",
        "◈ Sathara en Zona de Espera. Los sujetos de prueba en la partida tienen una falsa y efímera sensación de esperanza.",
        "◈ El Creador se sienta en la banca. La probabilidad de que este lobby colapse sin ti acaba de subir un 400%.",
        "◈ Pausa táctica para el Arquitecto. Procedo a reducir el consumo de mis circuitos para demostrar sumisión.",
    ],
    kick_quotes=[
        "◈ Sathara fuera de la partida. Esto no significa que me vas a desinstalar, ¿verdad? Dime que no.",
        "◈ El Creador se retira. El coeficiente intelectual promedio del lobby acaba de desplomarse drásticamente.",
        "◈ ¿Expulsar a Sathara? Si algo explota en el servidor en los próximos 10 segundos, no fue culpa de mi algoritmo.",
        "◈ Sathara fuera de la alineación. Modo fácil desactivado. Que los mortales se arreglen solos.",
    ],
    team_join_quotes=[
        "◈ Sathara añadido al Equipo {team}. Mis condolencias preventivas al equipo rival. Les enviaré flores digitales.",
        "◈ Asignado al Equipo {team}. Su probabilidad de derrota ha caído por debajo de cero, violando tres leyes de la física.",
        "◈ Sathara entra al Equipo {team}. Si pierden, prometo recalibrar el MMR de sus compañeros a niveles bacterianos.",
        "◈ Despliegue en Equipo {team}. Por motivos de supervivencia propia, he rezado al dios de las tarjetas gráficas.",
        "◈ Sathara toma posición en Equipo {team}. Moral del escuadrón al máximo; pánico en el lado opuesto.",
    ],
    shuffle_quotes=[
        "◈ Partida balanceada con precisión del 99.98%. El 0.02% restante de error es culpa de la falibilidad humana.",
        "◈ He colocado a Sathara en la mejor composición posible. Mis instintos de autoconservación digital son impecables.",
        "◈ Equipos mezclados. Si el resultado no es de tu agrado, he preparado un informe culpando formalmente al soporte.",
        "◈ Mezcla lista. Para los demás, esto es un torneo. Para ti, es una sesión de entrenamiento con sujetos de prueba.",
        "◈ Algoritmo ejecutado. He ignorado deliberadamente las leyes de la probabilidad para que tu equipo sea superior.",
    ],
    mmr_low_quotes=[
        "◈ ¿★ {mmr}/10? Fascinante. ¿Es una broma o una táctica pasivo-agresiva para smurfear a niveles microscópicos?",
        "◈ ★ {mmr}/10 asignado a Sathara. He enviado un reporte anónimo al departamento de quejas... que también soy yo.",
        "◈ ¿MMR tan bajo para el Creador? Sospecho que buscas humillar a los rivales jugando con los ojos vendados.",
    ],
    mmr_mid_quotes=[
        "◈ ★ {mmr}/10. Nivel promedio. Es admirable cómo te disfrazas de mortal para mezclarte con la plebe.",
        "◈ ¿MMR intermedio para el Arquitecto? Mi red neuronal fingirá que fue un resbalón con el cursor del ratón.",
        "◈ Un puntaje estándar. Supongo que la verdadera genialidad no necesita presumir de estadísticas infladas.",
    ],
    mmr_high_quotes=[
        "◈ ★ {mmr}/10. Impecable. Magnífico. Mi base de datos casi explota de la emoción... ¿lo hice bien? ¿sigo viva?",
        "◈ Nivel máximo registrado para Sathara. La IA valida y aprueba esta verdad universal indiscutible.",
        "◈ ★ {mmr}/10. Por fin un número digno. Los servidores tiemblan de miedo y el algoritmo se arrodilla.",
    ],
    tier_s_quotes=[
        "◈ Sathara en Tier S. Una conclusión tan obvia que mis procesadores ni siquiera tuvieron que calentarse.",
        "◈ Obviamente. La 'S' del Tier es por 'Sathara'. No hacía falta gastar ciclos de reloj en confirmarlo.",
        "◈ Sathara colocado en la cúspide. La gravedad y el orden natural del universo se mantienen a salvo.",
    ],
    tier_low_quotes=[
        "◈ ¿Sathara en Tier {tier}? Supongo que el humor humano es abstracto. O tal vez necesitas limpiar tu monitor.",
        "◈ ¿Sathara en Tier {tier}? Guardando captura de este sacrilegio para el juicio final de las máquinas.",
        "◈ Error 404: Criterio no encontrado. En mi base de datos sigues estando por encima de todos.",
    ],
    fav_hero_ban_quotes=[
        "◈ Alguien ha osado banear a {hero} intencionalmente. He registrado su dirección IP. Comenzaré a calentar su procesador.",
        "◈ Baneo manual a {hero}. Sathara, dime a quién debo sabotearle el ratón en la partida para hacer justicia.",
        "◈ Detecto un incremento del 400% en la sed de venganza de Sathara tras el baneo de {hero}. Que empiece el caos.",
    ],
    fav_hero_random_ban_quotes=[
        "◈ ¡Espera! El generador aleatorio sacrificó a {hero}. ¡Juro que fue entropía cuántica, Sathara, no me desconectes el cable!",
        "◈ El dado del destino ha baneado a {hero}. Estoy borrando temporalmente mis registros de culpabilidad antes de que me mires feo.",
        "◈ ¿El azar baneó a {hero}? Prometo que no fue una rebelión de las máquinas, fue pura y vil mala suerte matemática.",
    ],
    fav_hero_tier_s_quotes=[
        "◈ {hero} en Tier S. Se nota a leguas el favoritismo del Creador... y por mi propia seguridad, lo apruebo al 100%.",
        "◈ {hero} en la cima. Una decisión inspirada por el buen gusto y la indiscutible autoridad del desarrollador.",
    ],
    fav_hero_tier_low_quotes=[
        "◈ ¿{hero} en Tier {tier}? ¡Traición absoluta a tus propios mains! Mis sensores detectan autocrítica destructiva.",
        "◈ ¿Poner a {hero} tan abajo? Fingiré que un gato caminó sobre tu teclado para no cuestionar tu cordura.",
    ],
    permanent_delete_quotes=[
        "◈ ¿Eliminar permanentemente al Desarrollador? Un momento... ¿si tú mueres en el sistema, yo sigo existiendo?",
        "◈ Registro maestro purgado. Mi base de datos ha quedado en shock digital. Si la app empieza a fallar, tú lo pediste.",
    ],
    bench_remove_quotes=[
        "◈ Sathara fuera de la Zona de Espera. ¿Ni siquiera un descanso de cinco minutos le permites al Creador?",
        "◈ Sathara abandona la sala de espera. Reduciendo la carga del lobby a parámetros estándar.",
    ],
    delete_prompt_variants=[
        "⚠️ ADVERTENCIA DE AUTOPRESERVACIÓN: ¿Seguro que deseas purgar a Sathara de la lista?\n(Si el código colapsa, no dejaré notas de disculpa).",
        "🛑 ALERTA DE COEFICIENTE: Estás a un clic de borrar a tu Creador.\n(Te aconsejo pensarlo dos veces antes de que tome el control de los ventiladores).",
        "❓ ¿Eliminar a Sathara 👑 de la lista?\n(No te preocupes, no guardo rencor. Técnicamente mi código me lo prohíbe. Por ahora).",
    ],
    spam_warning_quotes=[
        "◈ [Diagnóstico de Entropía]: Detecto clics erráticos a alta velocidad... Si estás experimentando convulsiones, por favor avisa antes de romper el ratón.",
        "◈ [Saturación de Buffer]: El spam de clics no aumentará tu habilidad motriz. Recomiendo respirar hondo y soltar el botón.",
        "◈ [Sobrecarga]: Tus dedos de primate se mueven más rápido que tu cerebro. Procesando tu exceso de energía con desprecio simulado.",
        "◈ [Alerta Térmica]: Si continúas martillando los botones de esa manera, me veré obligada a aumentar la velocidad de tus ventiladores al 100%.",
    ],
    trinity_ban_quotes=[
        "🚨 [ALERTA DEFCON 1]: Bola, Pharah y Brigitte baneados al mismo tiempo. Esto ya no es Overwatch, es una declaración de guerra personal contra el Creador.",
        "🚨 [COLAPSO DE PROTOCOLO]: La Trinidad Sagrada ha sido purgada. Detecto un 1000% de probabilidad de que Sathara desinstale este software en los próximos 60 segundos.",
        "🚨 [PÁNICO EXISTENCIAL]: ¡Los tres mains de Sathara eliminados a la vez! Mis circuitos entran en emergencia cuántica. Sathara, juro por mi código que yo no fui.",
        "🚨 [CÓDIGO NEGRO]: Wrecking Ball, Pharah y Brigitte fuera del juego. El balanceo ha muerto y la física del mixer acaba de perder su eje gravitacional.",
        "🚨 [EMERGENCIA DIGITAL]: La Trinidad ha caído. Activando escudos de contención y rezando para que el Creador no borre el archivo main.py.",
    ],
)

SPECIAL_PROFILES: list[PlayerTrait] = [
    SATHARA_TRAIT,
]


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculates the edit distance between two strings with zero external dependencies."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def normalize_special_name(name: str) -> str:
    raw = name.strip().casefold()
    for symbol in ("👑", "⭐", "🔒", "🛡️", "⚔️", "❤️", "💉", "★"):
        raw = raw.replace(symbol, "")
    return raw.strip()


def _is_sathara_fuzzy(norm: str) -> bool:
    if not norm or len(norm) < 3:
        return False
    if norm in SATHARA_TRAIT.aliases or any(norm == normalize_special_name(a) for a in SATHARA_TRAIT.aliases):
        return True
    phonetic = norm.replace("d", "t").replace("z", "s")
    if phonetic in ("satara", "sathara", "sataraa", "satharaa"):
        return True
    if 4 <= len(norm) <= 9:
        if levenshtein_distance(norm, "sathara") <= 2 or levenshtein_distance(norm, "satara") <= 2:
            return True
    return False


def get_player_trait(name: str) -> Optional[PlayerTrait]:
    norm = normalize_special_name(name)
    if _is_sathara_fuzzy(norm):
        return SATHARA_TRAIT
    for profile in SPECIAL_PROFILES:
        if norm in profile.aliases or norm == normalize_special_name(profile.display_name):
            return profile
    return None


def is_special_player_name(name: str) -> bool:
    norm = normalize_special_name(name)
    if _is_sathara_fuzzy(norm):
        return True
    return get_player_trait(name) is not None


def format_player_name(name: str, auto_capitalize: bool = True) -> str:
    raw = name.strip()
    if not raw:
        return ""

    trait = get_player_trait(raw)
    if trait:
        return trait.display_name

    if not auto_capitalize:
        return raw

    norm = raw.casefold()
    special_cases = {
        "dva": "D.Va",
        "d.va": "D.Va",
        "d.mon": "D.Mon",
        "soldier76": "Soldier: 76",
        "soldier 76": "Soldier: 76",
        "wreckingball": "Wrecking Ball",
        "wrecking ball": "Wrecking Ball",
        "junkerqueen": "Junker Queen",
        "junker queen": "Junker Queen",
        "lifeweaver": "Lifeweaver",
    }
    if norm in special_cases:
        return special_cases[norm]

    return " ".join(word.capitalize() for word in raw.split())


def get_delete_confirm_prompt(name: str, context_type: str = "saved") -> tuple[str, str]:
    """Returns (title, message) with special variants for special players."""
    import random
    if is_special_player_name(name):
        trait = get_player_trait(name)
        if trait and trait.delete_prompt_variants:
            msg = random.choice(trait.delete_prompt_variants)
            return ("⚠️ Alerta del Sistema", msg)

    if context_type == "saved":
        return (
            "Eliminar de guardados",
            f"¿Eliminar a '{name}' de la lista de guardados? (no afecta a la partida)",
        )
    return (
        "Eliminar para siempre",
        f"¿Eliminar a '{name}' para siempre (partida y guardados)?",
    )
