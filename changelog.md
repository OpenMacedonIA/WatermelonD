# Registro de Cambios (Changelog)

Todas las modificaciones notables en el proyecto **Neo Nano** se documentarán en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/), y este proyecto adhiere a Versionado Semántico.

## [2.5.0-testing] - 2025-12-24

Versión de pruebas con nuevas capacidades autónomas y herramientas para desarrolladores.

### ✨ Nuevas Características

- **Self-Healing System**: Módulo `HealthManager` que monitorea servicios (`cron`, `mosquitto`, `nginx`, etc.) y los reinicia automáticamente tras un fallo.
  - **Smart Discovery**: Detección automática de servicios instalados para evitar falsos positivos.
  - **Análisis Predictivo**: Detección de patrones de inestabilidad basada en el historial de incidentes.
- **SysAdmin AI (MANGO T5)**:
  - Integración completa del modelo **MANGO T5 770M** (Hugging Face) para traducción natural a Bash.
  - **Downloader Inteligente**: Script `download_mango_model.py` con soporte de resume y caché local.
- **Cron Manager**:
  - Interfaz web `/tasks` para gestión visual de tareas programadas.
  - API REST completa para el scheduler (`/api/tasks/*`).
- **Instalador Inteligente**:
  - `install_wizard.sh` ahora detecta automáticamente el SO (Debian vs Fedora) y elige el instalador adecuado (Nativo vs Distrobox).
  - Descarga automática de modelos (Mango T5) durante la instalación.

### 🐛 Correcciones

- Limpieza de código muerto en `web_admin.py`.
- Corrección de dependencias faltantes en `setup_distrobox.sh`.

## [2.4.0] - 2025-12-20 (Self-Healing & UX Upgrade)

Importante actualización centrada en la autonomía del sistema (Self-Healing) y una mejora sustancial en la experiencia de usuario (UX) de la interfaz web.

### 🚑 Sistema de Auto-Curación (Self-Healing)

- **HealthManager**: Nuevo módulo que monitorea servicios críticos (`nginx`, `mosquitto`, `ollama`) y los reinicia automáticamente si fallan.
- **Análisis Predictivo**: Detección heurística de patrones de fallo (ej. crashes frecuentes con alta CPU).
- **Skill de Diagnóstico Avanzado**: Capacidad de analizar logs del sistema (`app.log`) usando IA para explicar errores y proponer soluciones sin intervención humana directa.

### 🧠 Brain 2.0: MANGO (Sysadmin LLM)

- **Natural Language to Bash**: Integración de modelo **MANGO T5** (Fine-Tuned Salesforce/T5-coder) especializado en traducir instrucciones humanas complejas a comandos de terminal precisos.
- **Ejecución Híbrida**: Pipeline inteligente que discrimina entre Intenciones (Reglas), MANGO (Técnico) y Chat Llama (Conversacional).
- **Safety First**: Sistema de ejecución segura con lista blanca para comandos de lectura (`ls`, `cat`) y solicitud de confirmación obligatoria para comandos de escritura/root (`systemctl`, `rm`).

### 🖥️ Interfaz Web 2.0

- **Dashboard Personalizable**: Ahora es posible reordenar los widgets (CPU, RAM, Discos) mediante **Drag & Drop**, con persistencia automática de la disposición.
- **Terminal "Power User"**:
  - **Multi-Pestañas**: Soporte para múltiples sesiones de terminal simultáneas con directorios independientes.
  - **Autocompletado Visual**: Menú flotante inteligente al pulsar `TAB` para archivos y directorios.
  - **Historial Persistente**: Los comandos se guardan en el navegador para sobrevivir a recargas de página.
- **Health UI**: Nueva tarjeta de estado en el Dashboard que muestra incidentes recientes y estado de autocuración.

### 📚 Documentación

- **Android Client Guide**: Guía paso a paso para desplegar la interfaz web en una tablet Android usando Termux.
- **Roadmaps**: Definición de planes futuros para la [Web UI](WEB_UI_ROADMAP.md) y [Skills](SKILLS_ROADMAP.md).

### 🐛 Correcciones

- **Estabilidad API**: Mejoras en los endpoints de terminal para manejar sesiones concurrentes.

---

## [2.3.0] - 2025-11-29 (Service Architecture & Skills System)

Reingeniería total del núcleo del sistema, pasando de un monolito multihilo a una arquitectura orientada a servicios (SOA) inspirada en OVOS, comunicados por un Bus de Mensajes.

### 🏗️ Arquitectura

- **Message Bus**: Implementación de un bus de eventos WebSocket (Flask-SocketIO) que actúa como columna vertebral del sistema.
- **Microservicios**: Descomposición de `NeoCore` en servicios independientes:
  - `AudioService`: Captura de micrófono y VAD.
  - `STTService`: Transcripción de voz (Vosk/Sherpa).
  - `NLUService`: Comprensión de lenguaje natural.
  - `SkillsService`: Ejecución de lógica de negocio.
  - `TTSService`: Síntesis de voz.
  - `WebService`: Interfaz de administración.

### 🧠 NLU Avanzado

- **Motor Híbrido**: Combinación de **Padatious** (Red Neuronal con FANN) para intenciones complejas y **RapidFuzz** para coincidencias aproximadas.
- **Entrenamiento en Vivo**: El sistema entrena la red neuronal al inicio basándose en `intents.json`.
- **Alias de Red**: Capacidad de definir alias para IPs (ej. "mario" -> "192.168.1.50") y usarlos en comandos ("ping mario").

### 🔌 Gestor de Skills

- **Web UI**: Nueva sección "Habilidades" en el panel de administración.
- **Hot-Swap**: Activación y desactivación de skills en tiempo real mediante interruptores.
- **Configuración JSON**: Editor integrado para modificar la configuración de cada skill (ej. añadir alias) sin tocar código.

### 🐛 Correcciones

- **Logs**: Separación de logs por servicio en la interfaz web para facilitar la depuración.
- **Dependencias**: Script de corrección automática para `fann2` y `swig`.
- **Estabilidad**: Manejo robusto de errores en `SkillsService` para evitar caídas por excepciones en plugins.

---

## [2.2.0] - 2025-11-28 (Intelligence & Audio Overhaul)

Actualización masiva centrada en la "humanización" del asistente, mejorando drásticamente el reconocimiento de voz, la síntesis y la personalidad.

### 🧠 Inteligencia & Personalidad

- **Personalidad "Colega"**: Ajuste profundo del System Prompt. TIO ahora usa jerga española ("Tronco", "Fiera", "Máquina"), es sarcástico y tiene más "calle".
- **Base de Conocimiento Ampliada**: Inyección de +40 entradas en `chistes.json` y `datos_curiosos.json` para conversaciones más amenas.
- **Memoria Conversacional**: Aumento del buffer de historia de 10 a 20 turnos para mantener el contexto durante más tiempo.

### 👂 Reconocimiento de Voz (STT)

- **Vosk Large Model**: Migración del modelo `small` (50MB) al `large` (1.4GB) para una precisión de nivel humano.
- **Dictado Abierto**: Eliminación de la restricción de gramática (`use_grammar: false`), permitiendo entender cualquier palabra, no solo comandos predefinidos.
- **Fuzzy Wake Word**: Implementación de `rapidfuzz` para detectar la palabra de activación con tolerancia a fallos (ej. "Ey tío", "Brou", "Tio" sin tilde).

### 🗣️ Síntesis de Voz (TTS)

- **Piper Integration Fix**: Solución al crash de `synthesize_stream_raw` adaptando el código a la API moderna de Piper (`AudioChunk`).
- **Sample Rate Dinámico**: Detección automática de la frecuencia de muestreo del modelo de voz.

### 🐛 Correcciones

- **Restauración de Servicio**: Script de recuperación automática para `neo.service` en caso de borrado accidental.
- **Selector de Audio**: Herramienta para identificar y configurar el índice correcto del micrófono (`input_device_index`).

---

Esta versión introduce la personalidad **T.I.O.** (Tecnología Inteligente Operativa) y capacidades cognitivas avanzadas para Raspberry Pi.

### 🧠 Inteligencia & Memoria

- **The Cortex**: Nuevo módulo cognitivo (`modules/cortex.py`) que analiza *todo* el input del usuario para extraer conceptos y aprender patrones de uso de forma autónoma.
- **Memoria Episódica**: Capacidad de recordar eventos específicos (ej. "escalar clúster") y utilizarlos para dar respuestas contextuales ("Te lo dije...").
- **Knowledge Graph Lite**: Sistema de relaciones semánticas (ej. `nginx` -> `web server`) almacenado en SQLite para razonamiento asociativo.
- **Sherlock (Diagnóstico)**: Motor de razonamiento basado en grafos y árboles de decisión para diagnosticar problemas técnicos (`modules/sherlock.py`).
- **Empatía (Sentimiento)**: Análisis de sentimiento ligero para adaptar la memoria y las respuestas al estado de ánimo del usuario.

### 🗣️ Personalidad & Voz

- **Identidad T.I.O.**: Cambio de nombre de "Neo" a "Tío". Personalidad de "SysAdmin Colega" (informal, técnico, sarcástico).
- **Wake Word Difuso**: Detección de la palabra clave "Tío" en cualquier parte de la frase (inicio, medio, fin) usando `rapidfuzz`.
- **Intents Proactivos**: El sistema puede iniciar conversaciones ("sorpresas") si detecta obsesiones o patrones repetitivos.

### 🛠️ Técnico

- **Tests**: Suite de pruebas completa restaurada en `tests/` (`test_fuzzy_logic.py`, `test_memory.py`, `test_cortex.py`, `test_sherlock.py`, `test_sentiment.py`).

## [2.1.1] - 2025-11-26 (Audio & Performance Update)

Actualización crítica enfocada en la calidad de audio, corrección de errores de consola y optimización de rendimiento.

### 🔊 Audio (TTS)

- **Piper TTS Integrado**: Instalación automática de Piper con voz neuronal en español (`es_ES-davefx-medium`) para una experiencia mucho más natural.
- **Configuración Dinámica**: Nuevo archivo `config.json` que gestiona rutas de TTS y parámetros de rendimiento.
- **Fallback Robusto**: Sistema de respaldo automático: Piper -> Espeak -> Dummy (Logs), asegurando que el sistema nunca falle silenciosamente.

### ⚡ Rendimiento

- **Cortex Asíncrono**: El procesamiento cognitivo ahora ocurre en segundo plano, eliminando el lag en la respuesta de voz.
- **Caché de Conceptos**: Implementada caché de 5 minutos para la normalización de texto, reduciendo drásticamente las consultas a base de datos.

### 🐛 Correcciones

- **Gramática Vosk**: Solucionado el problema de acentos ("avísame" vs "avisame") y conversión de números ("100" -> "cien") para eliminar warnings de vocabulario.
- **Logs Limpios**: Supresión de errores ALSA/PyAudio a nivel de C y codificación UTF-8 correcta en logs.

---

## [2.0.0] - 2025-11-25 (SysAdmin Edition)

Esta versión representa una reescritura mayor del sistema, cambiando completamente su propósito de Asistente de Cuidados a Asistente de Administración de Sistemas.

### 🚀 Añadido

- **Neo Guard**: Sistema de detección de intrusiones (IDS) ligero. Monitorea logs (`auth.log`) y métricas (CPU, Red) para detectar ataques como Fuerza Bruta SSH, DDoS SYN Flood y anomalías de sistema.
- **Neo Chat v2**: IA conversacional avanzada con soporte de contexto (memoria de conversación) y comprensión de lenguaje natural (typos, jerga) usando N-Grams.
- **Módulo Neo NetSec**: Herramientas de red integradas (`nmap`, `ping`, `whois`) con análisis de seguridad básico.
- **Neo Turbo**: Optimizaciones de rendimiento (RapidFuzz, TTS Cache, Gramática Dinámica).
- **Neo Brain**: Sistema de memoria y aprendizaje (SQLite).
- **Módulo SysAdmin**: Nueva librería interna para monitorización de hardware (CPU, RAM, Disco) y gestión de procesos.
- **Consola Web (Flask)**: Interfaz de administración completa accesible vía navegador (Puerto 5000).
  - Dashboard con métricas en tiempo real.
  - Gestor de servicios systemd (Start/Stop/Restart).
  - Terminal web con soporte de estado (`cd`), historial y colores.
  - Visor de logs en vivo.
- **Configuración Dinámica**: Archivo `config.json` para persistencia de credenciales y configuración de voz sin modificar código.
- **Soporte Fedora**: El script de instalación `install.sh` ahora detecta Fedora y usa `dnf` automáticamente.
- **Intents Técnicos**: Nuevos comandos de voz para consultar estado del sistema e información de red.

### 🔄 Cambiado

- **Identidad**: El asistente ha sido renombrado de "Teo" a "**Neo**", y el proyecto de "OpenKompai" a "**Neo Nano**".
- **Instalación**: Script `install.sh` actualizado con nuevas dependencias (`sqlite3`, `nmap`, `whois`, `rapidfuzz`).
- **Arquitectura Headless**: Se ha eliminado toda dependencia de interfaz gráfica local. El sistema corre ahora como un servicio puro.
- **Core Refactorizado**: `NeoCore.py` ahora implementa un sistema de hilos robusto para manejar Voz, Web y Eventos simultáneamente.
- **Estética**: La interfaz web adopta un tema oscuro profesional ("Cyberpunk/SysAdmin") en lugar de colores claros.

### 🗑️ Eliminado

- **Interfaz Tkinter**: Eliminado `NeoTK.py` y todos los assets gráficos locales.
- **Módulos de Salud**: Eliminados `pill_manager.py` (pastillero) y gestión de citas médicas.
- **Contactos y Emergencias**: Eliminado sistema de llamadas SOS y agenda.
- **Visión Artificial**: Eliminado `video_sensor.py` y dependencias pesadas (`opencv`, `mediapipe`) para mejorar el rendimiento en hardware modesto.

---

## [1.0.0] - 2024-05-10 (Legacy - Elderly Care)

Versión original del proyecto presentada como Trabajo de Fin de Grado.

### Añadido

- Interfaz táctil simple con botones grandes (Tkinter).
- Recordatorios de medicación programables.
- Detección de caídas mediante cámara y MediaPipe.
- Sistema de llamadas de emergencia (SOS).
- Interacción básica por voz (Vosk + TTS).
