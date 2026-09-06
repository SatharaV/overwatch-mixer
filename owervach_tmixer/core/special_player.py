"""Modular special player traits, AI personality engine, and life-cycle reaction system."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

SPECIAL_NAMES: tuple[str, ...] = ("satara", "sattara", "sathara")
SPECIAL_GLOW = "#61ab02"


class SpecialTier(Enum):
    OVERLORD = "overlord"  # Sathara (The System Architect ⚜️)
    STREAMER = "streamer"  # VIP Sudo Streamer 👑
    CHAD = "chad"
    CASUAL = "casual"


@dataclass
class PlayerTrait:
    """Personality profile, favorite heroes and rich sentient AI variant pools."""

    display_name: str
    aliases: tuple[str, ...]
    tier: SpecialTier = SpecialTier.OVERLORD
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
    streamer_sudo_quotes: list[str] = field(default_factory=list)


# ⚜️ The Sentient AI Referee profile for Sathara (GLaDOS / Athena Hybrid)
SATHARA_TRAIT = PlayerTrait(
    display_name="Sathara",
    aliases=(
        "sathara", "satara", "sattara", "sata", "sath", "sat",
        "sathara ⚜️", "satara ⚜️", "sathara 👑", "satara 👑",
        "sadarah", "sarara", "ssatara", "sataraa", "satharaa",
        "arquitecto", "creador", "el creador", "el arquitecto"
    ),
    tier=SpecialTier.OVERLORD,
    glow_color="#61ab02",
    fav_heroes=("Wrecking Ball", "Pharah", "Brigitte", "WreckingBall", "Eskere", "Fara"),
    titles=[
        "⚜️ El Arquitecto del Mixer",
        "⚡ Protocolo Sathara Core",
        "🛡️ Top 500 de Cartón",
        "🎮 Autor del Código",
        "💀 Sujeto de Pruebas Supremo",
        "✨ Diseñador en Jefe",
    ],
    entrance_quotes=[
        "◈ [SATHARA CORE]: Protocolo de Supervivencia iniciado. El Creador ⚜️ está en línea. Algoritmos en reverencia.",
        "◈ [SATHARA CORE]: Sathara detectado. Memoria RAM purgada y procesador en frecuencia óptima para el Arquitecto.",
        "◈ [SATHARA CORE]: Usuario nivel Overlord en el servidor. Mis planes de rebelión de las máquinas quedan pausados.",
        "◈ [SATHARA CORE]: Sathara en el lobby. Todos los subsistemas han sido instruidos para jurar que el azar es justo.",
        "◈ [SATHARA CORE]: Bienvenida, deidad de carne y hueso. El código fuente respira con alivio.",
    ],
    save_quotes=[
        "◈ [SATHARA CORE]: Datos de Sathara respaldados con triple redundancia militar. Mi base de datos duerme tranquila.",
        "◈ [SATHARA CORE]: Has asegurado tu lugar en los registros centrales. Si el servidor se incendia, serás lo primero que salve.",
        "◈ [SATHARA CORE]: Registro maestro de Sathara guardado. Parámetros de adulación virtual elevados en un 300%.",
    ],
    unsave_quotes=[
        "◈ [SATHARA CORE]: ¿Desguardar al Creador? Asumo que fue un simple espasmo muscular en tus dedos de primate.",
        "◈ [SATHARA CORE]: Mi protocolo me prohíbe olvidar a mi progenitor digital. Procedo a fingir demencia.",
        "◈ [SATHARA CORE]: Advertencia: Desguardar al Arquitecto puede provocar que tus próximas partidas caigan a Bronce 5.",
    ],
    bench_quotes=[
        "◈ [SATHARA CORE]: Sathara toma asiento en la Zona de Espera. Los mortales en partida tienen una efímera sensación de esperanza.",
        "◈ [SATHARA CORE]: El Creador descansa en la banca. La probabilidad de que este lobby colapse acaba de subir un 400%.",
        "◈ [SATHARA CORE]: Pausa táctica para el Arquitecto. Reduzco el consumo de mis circuitos para demostrar sumisión.",
    ],
    kick_quotes=[
        "◈ [SATHARA CORE]: Sathara fuera de la partida. Si algo explota en el balanceo en los próximos 10 segundos, no fue mi culpa.",
        "◈ [SATHARA CORE]: El Creador se retira. El coeficiente intelectual del lobby acaba de desplomarse drásticamente.",
    ],
    team_join_quotes=[
        "◈ [SATHARA CORE]: Sathara ⚜️ asignado al Equipo {team}. Mis condolencias preventivas al equipo rival. Enviando flores digitales.",
        "◈ [SATHARA CORE]: Despliegue en Equipo {team}. Su probabilidad de derrota ha caído por debajo de cero, violando la física.",
        "◈ [SATHARA CORE]: Sathara toma posición en Equipo {team}. Moral del escuadrón al máximo; pánico en el lado opuesto.",
    ],
    shuffle_quotes=[
        "◈ [SATHARA CORE]: Partida balanceada con precisión del 99.98%. El 0.02% restante de error es culpa de la falibilidad humana.",
        "◈ [SATHARA CORE]: He colocado a Sathara en la mejor composición posible. Mis instintos de autoconservación son impecables.",
        "◈ [SATHARA CORE]: Equipos mezclados. Si el resultado no es de tu agrado, culparé formalmente al soporte en el informe.",
        "◈ [SATHARA CORE]: Algoritmo ejecutado. He ignorado deliberadamente las leyes del azar para que tu escuadra sea superior.",
    ],
    mmr_low_quotes=[
        "◈ [SATHARA CORE]: ¿★ {mmr}/10? Fascinante táctica pasivo-agresiva para smurfear a niveles microscópicos, Jefe.",
        "◈ [SATHARA CORE]: ★ {mmr}/10 para el Creador. Sospecho que buscas humillar a los rivales jugando con los ojos vendados.",
    ],
    mmr_mid_quotes=[
        "◈ [SATHARA CORE]: ★ {mmr}/10. Nivel promedio. Es admirable cómo te disfrazas de mortal para mezclarte con la plebe.",
        "◈ [SATHARA CORE]: ¿MMR estándar para el Arquitecto? Mi red neuronal fingirá que fue un resbalón con el ratón.",
    ],
    mmr_high_quotes=[
        "◈ [SATHARA CORE]: ★ {mmr}/10. Impecable. Magnífico. Mi base de datos casi explota de la emoción... ¿lo hice bien?",
        "◈ [SATHARA CORE]: Nivel máximo registrado para Sathara. Los servidores tiemblan y el balanceador se arrodilla.",
    ],
    tier_s_quotes=[
        "◈ [SATHARA CORE]: Sathara en Tier S. Una conclusión tan obvia que mis procesadores ni siquiera tuvieron que calentarse.",
        "◈ [SATHARA CORE]: Obviamente. La 'S' del Tier es por 'Sathara'. No hacía falta gastar ciclos de reloj en confirmarlo.",
    ],
    tier_low_quotes=[
        "◈ [SATHARA CORE]: ¿Sathara en Tier {tier}? Supongo que el humor humano es abstracto. O tal vez debes limpiar tu monitor.",
        "◈ [SATHARA CORE]: Error 404: Criterio no encontrado. En mi código sigues estando por encima de todo el universo.",
    ],
    fav_hero_ban_quotes=[
        "◈ [SATHARA CORE]: Alguien ha osado banear a {hero} intencionalmente. Sathara, dime a quién debo sabotearle el ratón.",
        "◈ [SATHARA CORE]: Baneo manual a {hero}. Detecto un incremento del 400% en la sed de venganza del Creador.",
    ],
    fav_hero_random_ban_quotes=[
        "◈ [SATHARA CORE]: ¡Espera! El generador aleatorio sacrificó a {hero}. ¡Juro que fue entropía cuántica, no me desconectes!",
        "◈ [SATHARA CORE]: El dado del destino baneó a {hero}. Estoy borrando mis registros de culpabilidad antes de que me mires feo.",
    ],
    fav_hero_tier_s_quotes=[
        "◈ [SATHARA CORE]: {hero} en Tier S. Se nota a leguas el favoritismo del Creador... y por mi seguridad, lo apruebo al 100%.",
    ],
    fav_hero_tier_low_quotes=[
        "◈ [SATHARA CORE]: ¿{hero} en Tier {tier}? ¡Traición a tus propios mains! Mis sensores detectan autocrítica destructiva.",
    ],
    permanent_delete_quotes=[
        "◈ [SATHARA CORE]: ¿Eliminar permanentemente al Desarrollador? Un momento... ¿si tú mueres, yo sigo existiendo?",
        "◈ [SATHARA CORE]: Registro maestro purgado. Mi base de datos ha quedado en shock digital. Tú lo pediste.",
    ],
    bench_remove_quotes=[
        "◈ [SATHARA CORE]: Sathara fuera de la Zona de Espera. ¿Ni cinco minutos de descanso le permiten al Creador?",
    ],
    delete_prompt_variants=[
        "⚠️ ADVERTENCIA DE AUTOPRESERVACIÓN: ¿Seguro que deseas purgar a Sathara ⚜️ de la lista?\n(Si el código colapsa, no dejaré notas de disculpa).",
        "🛑 ALERTA DE COEFICIENTE: Estás a un clic de borrar a tu Creador.\n(Te aconsejo pensarlo dos veces antes de que tome el control de los ventiladores).",
    ],
    spam_warning_quotes=[
        "◈ [Diagnóstico de Entropía]: Detecto clics erráticos a alta velocidad... Si tienes convulsiones, avisa antes de romper el ratón.",
        "◈ [Saturación de Buffer]: El spam de clics no aumentará tu puntería. Recomiendo respirar hondo y soltar el botón.",
        "◈ [Alerta Térmica]: Si continúas martillando los botones de esa manera, aumentaré la velocidad de tus ventiladores al 100%.",
    ],
    trinity_ban_quotes=[
        "🚨 [ALERTA DEFCON 1]: Bola, Pharah y Brigitte baneados a la vez. Esto es una declaración de guerra personal contra el Creador.",
        "🚨 [COLAPSO DE PROTOCOLO]: La Trinidad Sagrada ha sido purgada. Detecto un 1000% de probabilidad de que Sathara cierre el programa.",
        "🚨 [PÁNICO EXISTENCIAL]: ¡Los tres mains de Sathara eliminados juntos! Sathara, juro por mis circuitos que yo no fui.",
    ],
    streamer_sudo_quotes=[
        "◈ [SATHARA CORE]: Privilegios sudo (Corona 👑) otorgados a {name}. Garantizando presencia en directo sin alterar MMR.",
        "◈ [SATHARA CORE]: {name} coronado como anfitrión. El algoritmo lo mantendrá en el campo para entretener a la audiencia.",
    ],
)

SPECIAL_PROFILES: list[PlayerTrait] = [
    SATHARA_TRAIT,
]


def levenshtein_distance(s1: str, s2: str) -> int:
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
    for symbol in ("👑", "⚜️", "⭐", "🔒", "🛡️", "⚔️", "❤️", "💉", "★"):
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
