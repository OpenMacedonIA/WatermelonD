# Estructura del Proyecto WatermelonD (WatermelonD)

Este documento detalla la estructura de archivos del proyecto y la finalidad de cada uno.

## Árbol de Directorios

```
.
├── config/# Archivos de configuración JSON
├── database/# Base de datos SQLite y scripts de inicialización
├── docker/# Configuración para contenerización (Docker/Podman)
├── docs/# Documentación del proyecto
│ ├── systemsec.md# Guía completa de seguridad y hardening
│ └── ... (ver árbol detallado)
├── jsons/# Archivos JSON de datos estáticos
├── modules/# Código fuente modular del núcleo (Backend)
│ ├── services/# Servicios del sistema (bus de mensajes, skills)
│ └── skills/# Lógica de habilidades específicas
├── piper/# Modelos y binarios para TTS (Piper)
├── piper_bin/# Binarios ejecutables de Piper
├── resources/# Recursos externos, scripts de herramientas y tests
│ ├── esp32_cam/# Firmware para cámaras ESP32
│ ├── experiments/# Scripts experimentales y datasets
│ ├── MNB/# Micro WatermelonD BrainNut (Agentes ligeros)
│ ├── NB/# WatermelonD BrainNut (Agentes intermedios)
│ ├── sounds/# Archivos de audio (efectos, fillers)
│ ├── tests/# Tests unitarios e integración
│ └── tools/# Scripts de utilidad y mantenimiento
├── web/# Interfaz Web (Frontend)
│ ├── static/# Assets (CSS, JS, Imágenes)
│ └── templates/# Plantillas HTML (Jinja2)
├── WatermelonD.py# **Punto de Entrada Principal** de la aplicación
├── install.sh# Script de instalación para Debian/Ubuntu
├── requirements.txt# Dependencias de Python
├── run_WatermelonD_distrobox.sh# Launcher para entorno aislado en Fedora
├── setup_distrobox.sh# instalador robusto para Fedora (vía Distrobox)
└── start.sh# Script de inicio (detecta entorno virtual)
```

## Descripción Detallada de Archivos

### Raíz del Proyecto
* **`WatermelonD.py`**: El corazón del sistema. Inicializa todos los gestores (`VoiceManager`, `BrainNut`, `WebAdmin`, etc.), arranca los hilos de ejecución y gestiona el bucle principal de la aplicación.
* **`start.sh`**: Script facilitador para iniciar la aplicación. Detecta automáticamente si se debe usar el entorno virtual estándar (`venv`) o el de Distrobox (`venv_distrobox`) y lanza `WatermelonD.py`.
* **`install.sh`**: Script de instalación "clásico" pensado para sistemas Debian/Ubuntu. Instala paquetes del sistema con `apt` y dependencias de Python.
* **`setup_distrobox.sh`**: Script de instalación avanzado para sistemas inmutables o incompatibles (como Fedora moderno). Crea un contenedor Debian aislado, instala todo dentro y prepara el entorno.
* **`run_WatermelonD_distrobox.sh`**: Script generado por `setup_distrobox.sh`. Sirve para lanzar la aplicación directamente dentro del contenedor sin tener que entrar manualmente.
* **`requirements.txt`**: Lista de todas las librerías de Python necesarias (`flask`, `vosk`, `opencv`, etc.) para que pip las instale.
* **`debug_kiosk.sh`**: Script auxiliar para depurar la interfaz gráfica en modo kiosco (pantalla completa).

### Directorio `config/`
Contiene la configuración persistente del sistema en formato JSON.
* **`config.json`**: Configuración principal (claves API, rutas de modelos, preferencias de usuario).
* **`intents.json`**: Definiciones de "intenciones" para el NLU (qué frases activan qué acciones).
* **`skills.json`**: Configuración específica para cada habilidad (habilitado/deshabilitado, parámetros).
* **`alarms.json`, `reminders.json`**: Persistencia de alarmas y recordatorios.
* **`radios.json`**: Lista de emisoras de radio por internet.
* **`network_intents.json`**: Intenciones específicas para gestión de red.
* **`sentiment.json`**: Configuración o historial de análisis de sentimientos.

### Directorio `modules/`
Contiene la lógica de negocio dividida en módulos.
* **`ai_engine.py`**: Interfaz con modelos de IA generativa (Llama, Ollama).
* **`alarms.py`**: Gestor de alarmas (crear, sonar, posponer).
* **`BrainNut.py`**: El "Cerebro". Gestiona la memoria a corto/largo plazo y el aprendizaje.
* **`calendar_manager.py`**: Gestión de eventos de calendario (Google Calendar o local). *Renombrado de calendar.py para evitar conflictos*.
* **`cast_manager.py`**: Control de dispositivos Chromecast/Google Home.
* **`chat.py`**: Lógica conversacional, historial de chat y personalidad.
* **`config_manager.py`**: Utilidad para leer/escribir archivos JSON de configuración de forma segura.
* **`dashboard_data.py`**: Agrega datos del sistema para mostrarlos en el Dashboard web.
* **`database.py`**: Capa de abstracción para SQLite. Maneja interacciones, logs y memoria.
* **`file_manager.py`**: Utilidades para gestión de archivos del sistema virtual.
* **`intent_manager.py`**: Motor de NLU. Decide qué hacer con el texto reconocido (Padatious/Fuzzy).
* **`keyword_router.py`**: Enrutador rápido para comandos simples sin pasar por IA compleja.
* **`knowledge_base.py`**: Sistema RAG (Retrieval Augmented Generation) que gestiona la ingestión y consulta de documentos.
* **`logger.py`**: Configuración centralizada de logs.
* **`mqtt_manager.py`**: Cliente MQTT para comunicarse con dispositivos IoT (Home Assistant, ESP32).
* **`network.py`**: Utilidades de red (escaneo, speedtest).
* **`services/`**:
 * **`skills_service.py`**: Servicio que carga y ejecuta las skills dinámicamente.
* **`skills/`**: Carpeta con las habilidades concretas (ej: `files.py`, `system.py`).
* **`speaker.py`**: Motor de TTS (Text-to-Speech). Gestiona Piper, Espeak o reproducción de audio.
* **`sysadmin.py`**: Funciones de administración del sistema (CPU, RAM, actualizaciones).
* **`vision.py`**: Módulo de visión por computador (OpenCV, Face Recognition).
* **`voice_manager.py`**: Responsable de escuchar (STT - Speech to Text). Integra Vosk, Whisper y gestiona el micrófono.
* **`web_admin.py`**: Servidor Flask que sirve la interfaz web.
* **`wifi_manager.py`**: Gestión de conexiones WiFi.

### Directorio `web/`
Frontend de la aplicación.
* **`templates/`**: Archivos HTML con sintaxis Jinja2.
 * **`base.html`**: Plantilla maestra con el diseño común (sidebar, cabecera).
 * **`dashboard.html`**: Página principal con widgets.
 * **`knowledge.html`**: Gestión de Memoria y Alimentador de Cerebro (RAG).
 * **`login.html`**, **`settings.html`**, **`terminal.html`**, etc.: Páginas específicas.
* **`static/`**: Archivos estáticos servidos directamente.
 * **`css/style.css`**: Estilos globales.
 * **`js/`**: Scripts de JavaScript para el frontend.

### Directorio `docker/`
* **`Dockerfile`**: Receta para construir la imagen de contenedor del proyecto.
* **`docker-compose.yml`**: Define el servicio, volúmenes y redes para desplegar con una sola orden.
* **`deploy.sh`**: Script para construir y desplegar el contenedor automáticamente.
* **`docker_clean.sh`**: Limpia contenedores e imágenes antiguas.

### Directorio `resources/`
* **`tools/`**: Scripts variados para mantenimiento (`install_piper.py`, `download_model.py`, `install_fann_fix.py`).
* **`tests/`**: Tests automatizados para verificar componentes (`test_brain.py`, `test_speaker.py`).
* **`sounds/`**: Archivos `.wav` para feedback sonoro (beeps, fillers).
* **`esp32_cam/`**: Código Arduino/C++ para flashear en cámaras remotas.
* **`experiments/`**: Zona de pruebas para nuevas funcionalidades antes de integrarlas.
