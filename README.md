# 🎮 Overwatch Team Mixer

<p align="center">
  <img src="owervach_tmixer/assets/overwatch-logo-white.svg" alt="Overwatch Logo" width="100"/>
</p>

<p align="center">
  <strong>El orquestador definitivo de partidas personalizadas, MMR inteligente, baneos competitivos y explorador de mapas para Overwatch.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Versi%C3%B3n-1.0%20Oficial-00B4FF?style=for-the-badge&logo=github" alt="Version 1.0">
  <img src="https://img.shields.io/badge/Tests-153%2F153%20Passing-brightgreen?style=for-the-badge&logo=pytest" alt="Tests">
  <img src="https://img.shields.io/badge/Rendimiento-144%20FPS%20%7C%20Zero--Lag-A4E062?style=for-the-badge" alt="Performance">
  <img src="https://img.shields.io/badge/Plataformas-Windows%20%7C%20Linux-orange?style=for-the-badge" alt="Platforms">
  <img src="https://img.shields.io/badge/Framework-PySide6%20(Qt6)-41CD52?style=for-the-badge&logo=qt" alt="PySide6">
</p>

---

## 🌟 ¿Qué es Overwatch Team Mixer?

**Overwatch Team Mixer** es una suite de escritorio diseñada para comunidades, ligas amateur, creadores de contenido y grupos de amigos que buscan llevar sus partidas personalizadas (scrims) al siguiente nivel.

El software balancea equipos con algoritmos matemáticos, gestiona el pool de mapas en tiempo real, aplica baneos de héroes competitivos y calibra el nivel real de cada jugador automáticamente con el paso del tiempo.

---

## ✨ Características Destacadas

### ⚔️ Motor de Partidas (5v5 & 6v6)
* **Flexibilidad Total:** Cambia dinámicamente entre formatos 5v5 y 6v6 con un solo toque.
* **Balanceo Inteligente & Tolerancia:** Algoritmo heurístico que minimiza la brecha de habilidad entre ambos bandos.
* **Intercambio Fluido (Drag & Drop):** Arrastra y suelta jugadores entre celdas, equipos y la banca con animaciones instantáneas.
* **Roles Configurables:** Modos automático, visualización ligera por emojis (🛡️, ⚔️, 💉) o bloqueo manual de roles.

### 🧠 Motor de Auto-MMR Bayesiano
* **Calibración Empírica Continua:** Ajuste matemático dinámico basado en victorias, derrotas y roles jugados.
* **Perfiles Detallados:** Historial de rendimiento individual por jugador y métricas de impacto por partida.

### 🗺️ Explorador & Sorteo de Mapas
* **Catálogo Completo:** Soporte oficial para todos los modos (Control, Hybrid, Escort, Push, Flashpoint, Clash, Assault).
* **Filtros Dinámicos & Prevención de Repetición:** Algoritmo de memoria que evita que salgan los mismos mapas jugados recientemente.
* **Diseño Obsidian:** Tarjetas visuales HD con renderizado optimizado directamente en memoria RAM (0 ms de delay).

### 🚫 Sistema de Baneos Esports
* **Exclusiones Temáticas:** Bloqueo rápido de héroes por rol con distribución geométrica centrada.
* **Audio FX Integrado:** Efectos de sonido temáticos de baja latencia con voces icónicas.

### 🏆 Tier Maker (Ratam Maker Edition)
* **Creador de Tier Lists Integrado:** Organiza y clasifica héroes o jugadores con un canvas interactivo de alta resolución, franja Obsidian y watermark oficial de exportación.

### 👑 The Sentient AI Referee
* **Easter Egg Core:** Una red neuronal simulada con personalidad cínica y divertida que reacciona a las decisiones de la partida, comentarios de MMR y momentos clave.

---

## 🚀 Descarga para Jugadores (Windows Standalone)

No requieres instalar Python ni configurar nada en tu equipo:
1. Dirígete a la sección de Releases en el panel derecho de este repositorio.
2. Descarga el archivo ejecutable **Overwatch-Mixer.exe**.
3. ¡Doble clic y a jugar!

---

## 💻 Instalación desde Código Fuente (Para Desarrolladores)

1. Clonar el repositorio:
   git clone https://github.com/TU-USUARIO/overwatch-team-mixer.git
2. Crear entorno virtual:
   python -m venv venv
3. Instalar dependencias oficiales:
   pip install -r requirements.txt
4. Ejecutar la aplicación:
   python -m owervach_tmixer.main
5. Correr la suite de pruebas (153 tests):
   pytest

---

## 📦 Compilación de Ejecutables

Para empaquetar el binario standalone optimizado:
python build.py

---

## 👑 Créditos & Dirección

* **Director Creativo & de Producto:** Sathara 👑
* **Desarrollo de Software & Arquitectura:** Asistido por Inteligencia Artificial
* **Licencia:** Distribuido bajo Licencia MIT. Libre para uso, modificación y distribución comunitaria.