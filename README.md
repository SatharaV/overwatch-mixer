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

Vas a **Releases**, descargas el appimage y ejecutas, eso es todo.

---

## 🛠️ Instalación y Ejecución desde Código Fuente

```markdown

Si deseas ejecutar, modificar o compilar el proyecto directamente desde el código fuente, sigue los pasos correspondientes a tu sistema operativo.

### 📋 Requisitos Previos
* **Python 3.10 o superior** (Recomendado: Python 3.11 a 3.14).
* **Git** instalado en el sistema.

---

### 1. Clonar el Repositorio

Abre tu terminal favorita y clona el proyecto:

```bash
git clone https://github.com/SatharaV/overwatch-mixer.git
cd overwatch-mixer
```

---

### 2. Configuración del Entorno Virtual y Dependencias

#### 🐧 En Linux (Arch, Ubuntu, Fedora, CachyOS, etc.)

Crea el entorno virtual:
```bash
python -m venv venv
```

Activa el entorno virtual según tu shell:

* **En Bash o Zsh:**
  ```bash
  source venv/bin/activate
  ```

* **En Fish Shell:**
  ```fish
  source venv/bin/activate.fish
  ```

Instala las dependencias:
```bash
pip install -r requirements.txt
```

---

#### 🪟 En Windows (10 / 11)

Crea el entorno virtual:
```cmd
python -m venv venv
```

Activa el entorno virtual según tu consola:

* **En PowerShell:**
  > *Nota: Si PowerShell te muestra un error de políticas de ejecución de scripts, ejecuta primero:*  
  > `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```

* **En Símbolo del Sistema (CMD):**
  ```cmd
  venv\Scripts\activate.bat
  ```

Instala las dependencias:
```bash
pip install -r requirements.txt
```

---

### 3. Ejecutar la Aplicación

Con el entorno virtual activado (`(venv)` al inicio de tu línea de comandos):

```bash
python -m owervach_tmixer.main
```

> **Tip:** En Linux también puedes lanzarlo directamente sin activar el entorno con:  
> `./venv/bin/python -m owervach_tmixer.main`

---

### 🧪 Suite de Pruebas Automatizadas

La aplicación cuenta con una estricta suite de pruebas unitarias e integrales que validan la persistencia atómica, el motor de MMR bayesiano, los algoritmos de mezcla y la interfaz gráfica.

Para ejecutar los tests con el entorno virtual activo:

```bash
pytest
```

> **Métrica de calidad:** La suite completa debe finalizar con **153/153 pruebas en verde** (`100% passing`) en aproximadamente **40 a 60 segundos**.

---

### 📦 Compilación y Empaquetado (`build.py`)

El proyecto incluye un script de compilación inteligente multiplataforma que detecta tu sistema operativo y empaqueta el software en un solo comando:

```bash
python build.py
```

* **En Windows:** Genera un ejecutable autónomo optimizado (`dist/Overwatch-Mixer.exe`, ~72 MB) con ícono nítido y temporizador multimedia a 1 ms.
* **En Linux:** Genera el binario nativo y empaqueta automáticamente el **`.AppImage` oficial para Gearlever / KDE Plasma / GNOME** en `dist/Overwatch-Mixer-x86_64.AppImage`, con metadatos de versión (`v1.1.0`), ícono PNG de 256x256 e integración con el sistema.
```

---

### 🎯 Puntos clave que soluciona esta documentación:
1. **Rutas y Enlaces Actualizados:** Enlaza al nuevo repositorio oficial `https://github.com/SatharaV/overwatch-mixer.git`.
2. **Fish Shell vs Bash:** Aclara el uso de `.activate.fish` para que nadie en Linux se tope con el `Unknown command` que experimentaste.
3. **PowerShell en Windows:** Incluye la instrucción de `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, que es el error #1 por el cual la gente en Windows no puede activar `venv`.
4. **Instrucción de Compilación:** Explica cómo usar `build.py` tanto para el `.exe` como para el `.AppImage` de Gearlever.
5. **Métricas Verídicas:** Refleja con precisión los **153/153 tests en 40-60s**. Sí, las hice. No, no recuerdo para qué sirven todas.

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
