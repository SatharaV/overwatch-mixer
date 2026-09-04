# 🎮 Overwatch Team Mixer

<p align="center">
  <img src="owervach_tmixer/assets/overwatch-logo-white.svg" alt="Overwatch Logo" width="100"/>
</p>

<p align="center">
  <strong>Una app para mezclar equipos, sortear mapas y dejar de discutir quién debería ir en qué equipo.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Versi%C3%B3n-1.0%20Oficial-00B4FF?style=for-the-badge&logo=github" alt="Version 1.0">
  <img src="https://img.shields.io/badge/Tests-153%2F153%20Passing-brightgreen?style=for-the-badge&logo=pytest" alt="Tests">
  <img src="https://img.shields.io/badge/Rendimiento-144%20FPS%20%7C%20En%20teor%C3%ADa-A4E062?style=for-the-badge" alt="Performance">
  <img src="https://img.shields.io/badge/Plataforma-Windows-orange?style=for-the-badge" alt="Platform">
  <img src="https://img.shields.io/badge/Framework-PySide6%20(Qt6)-41CD52?style=for-the-badge&logo=qt" alt="PySide6">
</p>

---

## ¿Qué es?

**Overwatch Team Mixer** es una aplicación de escritorio para organizar partidas personalizadas de Overwatch.

La idea era bastante sencilla: meter a los jugadores, mezclar los equipos y dejar que algún algoritmo haga las cuentas por ti.

Como pasa casi siempre, la idea sencilla terminó creciendo y ahora también hay MMR, mapas, baneos, tier lists y otras cosas que probablemente no eran necesarias.

---

## Características

### ⚔️ Mezclador de equipos — 5v5 y 6v6

Permite trabajar con partidas de **5v5 o 6v6** y cambiar entre ambos formatos sin tener que rehacer todo.

El sistema utiliza un **algoritmo heurístico de balanceo** para intentar que los equipos queden lo más parejos posible (no hay garantía).

También puede mover jugadores manualmente mediante **drag & drop**, porque a veces el algoritmo decide algo que a usted no te termina de gustar y ps ni modo, tú mandas.

Incluye soporte para distintos esquemas de roles y bloqueo manual cuando haga falta.

### 🧠 Auto-MMR

El sistema de MMR intenta estimar el nivel de cada jugador usando un modelo **Bayesiano**, teniendo en cuenta cosas como:

* victorias y derrotas
* rol jugado
* historial individual

La idea es que este valor se vaya ajustando con el tiempo según los resultados reales, en lugar de depender únicamente de un número que alguien escribió a mano y decidió que "más o menos debería estar bien".

¿Es un sistema perfecto?

No.

¿Es mejor que poner "AlgúnTontínFJ Probablemente es Muy Bueno" y que el sistema se lo crea para siempre?

También puede ser. Honestamente, tampoco era una vara muy alta.

### 🗺️ Mapas

Incluye un explorador visual de mapas de Overwatch y un **sorteador aleatorio**.

Puede filtrar mapas y modos, además de evitar repeticiones recientes para que no termine jugando el mismo mapa cuatro veces seguidas (tampoco hay garantías).

Porque aparentemente eso también había que programarlo.

### 🚫 Baneos de héroes

Sistema para seleccionar y visualizar **héroes baneados**, integrado directamente en la interfaz principal.

Pensado para partidas personalizadas donde quieren usar alguna clase de sistema de bans sin tener que llevar una lista escrita en Discord.

### 🏆 Tier Maker

Un **Tier Maker integrado** para ordenar héroes o jugadores y exportar el resultado directamente a **PNG**.

La verdad no sabía que más poner para que el programa no fuera tan simplón.

### 👑 Cosas que no eran necesarias

También hay algunas pequeñas sorpresas y easter eggs repartidos por la aplicación.

No afectan al funcionamiento de la app.

Están ahí porque podía hacerlo.

---

## Rendimiento

La aplicación está hecha con **PySide6 / Qt6** y está pensada para funcionar como una aplicación de escritorio nativa.

Se ha intentado mantener la interfaz fluida y el consumo de recursos razonable.

Los números bonitos de rendimiento están ahí arriba en los badges.

No se los tomen muy en serio.

---

## Descarga — Windows

No necesita instalar Python ni configurar nada.

Vas a **Releases**, descargas el ejecutable y ejecutas.

Según yo eso es todo.

## Descarga — Linux

Vas a **Releases**, descargas el appimage y ejecutas.

---

## Instalación desde código fuente

Para quien quiera ejecutar el proyecto directamente desde Python:

```bash
git clone https://github.com/SatharaV/overwatch-mixer.git
cd overwatch-mixer

python -m venv venv
```

Active el entorno virtual e instale las dependencias:

```bash
pip install -r requirements.txt
```

Ejecute la aplicación:

```bash
python -m owervach_tmixer.main
```

Para correr las pruebas:

```bash
pytest
```

Actualmente la suite cuenta con **153 pruebas**.

Sí, las hice.

No, no recuerdo para qué sirven todas.

---

## Compilación

Para generar el ejecutable standalone:

```bash
python build.py
```

El resultado será un ejecutable listo para distribuir sin necesidad de instalar Python, la intención siempre fue hacer una aplicación independiente y offline lista para usar.

---

## Créditos

**Director Creativo & de Producto:** Sathara

**Desarrollo:** Asistido por Inteligencia Artificial

**Licencia:** MIT Puede usarse, modificarse y distribuirse libremente sin restricciones.

**Disclaimer:** El equipo de desarrollo no se hace responsable por el mal funcionamiento, uso indebido o consecuencias derivadas del uso de este software, incluyendo fraudes, pérdida de información o daños a sistemas y/o equipos. En cualquier caso, este software no cuenta con la capacidad técnica para causar daños de ese tipo.
