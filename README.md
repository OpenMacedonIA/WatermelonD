# COLEGA
**C.O.L.E.G.A.** (COpiloto de Lenguaje para Entornos de Grupo y Administración)

> Este sistema se basa en un proyecto anterior https://github.com/jrodriiguezg/OpenKompai_nano

COLEGA es un asistente personal proactivo y modular diseñado para ejecutarse localmente en hardware modesto. Combina la eficiencia de un sistema basado en reglas para el control del sistema y domótica, con la inteligencia de un LLM local (**Gemma 2B**) para conversaciones naturales y razonamiento.

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![License](https://img.shields.io/badge/License-GPLv3-green)

## 🚀 Características Principales

### 🧠 Inteligencia Híbrida
*   **LLM Local**: Integración con **Gemma 2B** (4-bit) para conversaciones fluidas, personalidad y razonamiento complejo sin depender de la nube.
*   **Memoria (Brain)**: Sistema de memoria a largo plazo y aprendizaje de alias para comandos.
*   **RAG (Retrieval-Augmented Generation)**: Capacidad de consultar documentos y datos aprendidos para enriquecer las respuestas.

### 🗣️ Interacción Natural
*   **Voz**: Reconocimiento de voz offline con **Vosk** (rápido) o **Whisper** (preciso).
*   **Habla**: Síntesis de voz natural y emotiva con **Piper TTS**.
*   **Interfaz Visual**: "Cara" reactiva (Web UI) que muestra estados (escuchando, pensando, hablando) y notificaciones.

### 🛠️ Administración de Sistemas & Redes
*   **SysAdmin**: Control de servicios, actualizaciones del sistema, monitoreo de recursos (CPU/RAM/Disco) y gestión de energía.
*   **SSH Manager**: Gestor de conexiones SSH para administrar servidores remotos mediante voz.
*   **Network Tools**: Escaneo de red (Nmap), Ping, Whois, y detección de IP pública.
*   **File Manager**: Búsqueda y lectura de archivos en el sistema local.

### 🏠 Domótica & Organización
*   **Organizador**: Gestión de calendarios, alarmas, temporizadores y recordatorios.
*   **Media**: Reproducción de radio online y capacidad de **Cast** (enviar video/audio) a dispositivos compatibles (DLNA/Chromecast).
*   **Network Bros**: Protocolo de comunicación entre agentes (MQTT) para alertas y telemetría distribuida.
*   **Bluetooth**: Soporte para comunicación y control vía Bluetooth.

## 🏗️ Arquitectura

El núcleo (`NeoCore.py`) orquesta varios módulos independientes:

*   **Managers**: `VoiceManager`, `IntentManager`, `AIEngine`, `MQTTManager`, `SSHManager`, etc.
*   **Skills**: Módulos funcionales específicos (`skills/system`, `skills/network`, `skills/media`, etc.).
*   **Web Admin**: Panel de control web para gestión y visualización. (`localhost:5000`)

## 📋 Requisitos

*   **Sistema Operativo**: Linux (Debian, Ubuntu).
*   **Hardware**:
    *   CPU: Procesador con soporte para AVX2. 
    *   RAM: Mínimo 4GB (8GB recomendado para Gemma 2B).
    *   Almacenamiento: 16GB+ (SSD).
*   **Audio**: Micrófono y Altavoces conectados.

## 🔧 Instalación

El proyecto incluye un script de instalación automatizado que configura todo el entorno (Python, dependencias, servicios, modelos).

```bash
# Clona el repositorio
git clone https://github.com/jrodriiguezg/COLEGA.git
cd COLEGA

# Ejecuta el instalador
./install.sh
```

El instalador realizará las siguientes acciones:
1.  Instalará dependencias del sistema (`apt` o `dnf`).
2.  Configurará Python 3.10 usando `pyenv`.
3.  Creará un entorno virtual e instalará las librerías necesarias.
4.  Descargará los modelos de IA (Vosk, Piper, Gemma, Whisper).
5.  Configurará el servicio `systemd` para que COLEGA arranque automáticamente.
6.  (Opcional) Configurará el modo Kiosk para la interfaz visual.

## ⚙️ Configuración

La configuración principal se encuentra en `config/config.json`. Puedes modificarla manualmente o a través del **Web Admin**.

*   **Wake Word**: Palabra de activación (por defecto "tio", "colega", etc.).
*   **Rutas**: Directorios de escaneo, modelos, etc.
*   **Preferencias**: Idioma, voz TTS, sensibilidad de escucha.

## 🖥️ Uso

Una vez instalado, COLEGA funcionará como un servicio en segundo plano.

*   **Interfaz Web**: Accede a `http://localhost:5000/face` (o la IP del dispositivo) para ver la "cara" del asistente. 
*   **Logs**: Puedes ver la actividad en tiempo real con:
    ```bash
    journalctl --user -u neo.service -f
    ```
*   **Comandos de Voz**: Simplemente di la palabra de activación y tu comando (ej: *"Colega, ¿qué hora es?", "Colega, pon la radio", "Colega, escanea la red"*).

## 🤝 Contribución

¡Las contribuciones son bienvenidas! Por favor, abre un *issue* o envía un *pull request* para mejoras o correcciones.

## 📄 Licencia

Este proyecto está licenciado bajo la **GNU General Public License v3.0 (GPLv3)**. Consulta el archivo `LICENSE` para más detalles.
