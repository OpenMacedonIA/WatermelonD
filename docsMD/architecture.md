# Arquitectura del Sistema (WatermelonD v3.0 / Core v4)

Este documento describe la arquitectura interna de WatermelonD con las optimizaciones de la versión 4 del Núcleo (`WatermelonD`).

## ️ Visión General

WatermelonD sigue una arquitectura **modular y orientada a eventos**, optimizada para ejecutarse en hardware de recursos limitados (Dual Core CPUs, 8GB RAM).

### Componentes Principales

1. **WatermelonD (`WatermelonD.py`)**:
 * **Función**: Orquestador central. Gestiona el ciclo de vida de la aplicación.
 * **Threading**: Utiliza hilos ligeros para manejar tareas simultáneas (Voz, Eventos, Web).
 * **V4 Optimization**: Implementa un **Watchdog** interno que supervisa y reinicia hilos críticos si fallan, garantizando "Alta Disponibilidad" local.

2. **Web Admin (`modules/web_admin.py`)**:
 * **Función**: Servidor API y Web Interface.
 * **Tecnología**: Flask + Flask-SocketIO.
 * **Aislamiento**: Se ejecuta en su propio hilo dentro de WatermelonD, sirviendo la UI independientemente del estado de la IA.

3. **Managers (Decoupled Modules)**:
 * `VoiceManager`: Captura de audio y STT (Vosk/Whisper).
 * `MangoManager`: Inferencia de LLM especializado (T5) para comandos Bash. *Nota: Limitado a 1 hilo en V4 para no saturar CPU.*
 * `AIEngine`: Inferencia de LLM general (Gemma 2B) con `llama-cpp-python`.
 * `HealthManager`: Monitorización de servicios del sistema operativo (cron, docker, etc.).
 * **Advanced Modules**:
  * `Guard`: IDS basado en reglas y logs.
  * `CastManager`: Gestión de audio multi-habitación (Google Cast).
  * `BrainNut`: Gestión de memoria episódica y DB (SQLite).

## Flujo de Datos

1. **Input**: El usuario habla -> `VoiceManager` detecta y transcribe.
2. **Routing**: `WatermelonD.handle_command` decide:
 * Es un comando de sistema? -> `MangoManager` (T5).
 * Es una charla? -> `AIEngine` (Gemma).
 * Es una orden directa? -> `IntentManager` (Reglas/Vosk).
3. **Ejecución**: El Manager correspondiente ejecuta la acción y devuelve texto.
4. **Output**: `Speaker` sintetiza la respuesta (TTS Piper) y `WebAdmin` actualiza la UI vía WebSocket.

## Optimizaciones Core V4 (Hardware Limitado)

Para funcionar fluidamente en un i3 7th Gen:

* **PyTorch Single-Thread**: Se fuerza a PyTorch (usado por Mango T5) a usar 1 solo hilo físico. Esto previene que la inferencia de la IA bloquee el procesamiento de audio en tiempo real.
* **Garbage Collection Forzada**: Se llama explícitamente al recolector de basura de Python tras la carga de modelos pesados (2GB+) para desfragmentar la RAM.
* **Lazy Loading**: Módulos pesados como `VisionManager` (OpenCV) solo se cargan si están habilitados en la configuración, evitando el consumo de memoria en reposo.

## ️ Seguridad

* **Web**: Cabeceras estrictas (CSP, HSTS) en el servidor interno Flask.
* **Ejecución**: Comandos generados por IA (Mango) pasan por un filtro de riesgo antes de ejecutarse. Comandos destructivos (`rm`, `mkfs`) requieren confirmación de voz explícita.
