# COLEGA (v2.5.0-testing)

[🇺🇸 English](#english) | [🇪🇸 Español](#español)

---

<a name="english"></a>
## English

> [!WARNING]
> **Testing Branch**: You are currently viewing the development version (v2.5.0-testing). Features like Self-Healing and MANGO T5 are experimental and might be unstable. Use at your own risk.

**C.O.L.E.G.A.** (Language Copilot for Group and Administration Environments)

> Formerly known as **OpenKompai Nano**

COLEGA is a proactive and modular personal assistant designed to run locally on modest hardware. It combines the efficiency of a rule-based system for system control and home automation with the intelligence of a local LLM (**Gemma 2B**) for natural conversations and reasoning.

![Status](https://img.shields.io/badge/Status-Testing-orange)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![License](https://img.shields.io/badge/License-GPLv3-green)

### 🌟 New in v2.5.0 (Testing Branch)

*   **🛡️ Self-Healing System**: Proactive "HealthManager" module that detects crashed services (`cron`, `mosquitto`, `nginx`, etc.) and automatically attempts to restart them. It also performs predictive analysis based on system load.
*   **🥭 SysAdmin AI (MANGO T5)**: Specialized 770M parameter model fine-tuned to translate natural language into `bash` commands, allowing for complex system administration tasks via voice or text.
*   **🔍 Smart Service Discovery**: Automatically detects which services are installed on the host machine to avoid false alerts.
*   **📅 Cron Automation**: New task scheduler and Web UI to manage system jobs with cron syntax.

### 🚀 Key Features

#### 🧠 Hybrid Intelligence
*   **Local LLM**: Integration with **Gemma 2B** (4-bit) for fluid conversations, personality, and complex reasoning without cloud dependency.
*   **SysAdmin AI**: **MANGO T5** model for robust Natural Language to Bash translation.
*   **Memory (Brain)**: Long-term memory system and alias learning for commands.
*   **RAG (Retrieval-Augmented Generation)**: Ability to query documents and learned data to enrich responses.

#### 🗣️ Natural Interaction
*   **Voice**: Offline voice recognition with **Vosk** (fast) or **Whisper** (accurate).
*   **Speech**: Natural and emotive speech synthesis with **Piper TTS**.
*   **Visual Interface**: Reactive "Face" (Web UI) showing states (listening, thinking, speaking) and notifications.

#### 🛠️ System & Network Administration
*   **SysAdmin**: Service control, system updates, resource monitoring (CPU/RAM/Disk), and power management.
*   **SSH Manager**: SSH connection manager to administer remote servers via voice.
*   **Network Tools**: Network scanning (Nmap), Ping, Whois, and public IP detection.

### 🏗️ Architecture

The core (`NeoCore.py`) orchestrates several independent modules:

*   **Managers**: `VoiceManager`, `IntentManager`, `AIEngine`, `HealthManager` (New), `MangoManager` (New).
*   **Skills**: Specific functional modules (`skills/system`, `skills/network`, `skills/media`, etc.).

### 🔧 Installation (Testing Branch)

**Recommended Native Installation:** (Best for System Control & Self-Healing)

```bash
# Clone the repository and switch to testing branch
git clone https://github.com/jrodriiguezg/COLEGA.git
cd COLEGA
git checkout testing && git pull

# Run the native installer (User Service Mode)
# This will download MANGO T5, Vosk, Piper, and set up the systemd service.
./install.sh
```

### ⚙️ Configuration

The main configuration is found in `config/config.json`.
*   **Wake Word**: Activation word (default "tio", "colega", etc.).
*   **Preferences**: Language, TTS voice, listening sensitivity.

### 🖥️ Usage

Once installed, COLEGA will run as a background service.
*   **Logs**: `journalctl --user -u neo.service -f`
*   **Web Interface**: Access `http://localhost:5000/face`

---

<a name="español"></a>
## Español

> [!WARNING]
> **Rama Testing**: Estás viendo la versión de desarrollo (v2.5.0-testing). Funcionalidades como Self-Healing y MANGO T5 son experimentales y podrían ser inestables. Úsalo bajo tu propia responsabilidad.

**C.O.L.E.G.A.** (COpiloto de Lenguaje para Entornos de Grupo y Administración)

> Anteriormente conocido como **OpenKompai Nano**

COLEGA es un asistente personal proactivo y modular diseñado para ejecutarse localmente en hardware modesto. Combina la eficiencia de un sistema basado en reglas para el control del sistema y domótica, con la inteligencia de un LLM local (**Gemma 2B**) para conversaciones naturales y razonamiento.

![Status](https://img.shields.io/badge/Status-Testing-orange)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![License](https://img.shields.io/badge/License-GPLv3-green)

### 🌟 Novedades en v2.5.0 (Rama Testing)

*   **🛡️ Sistema Self-Healing**: Módulo "HealthManager" proactivo que detecta servicios caídos (`cron`, `mosquitto`, `nginx`, etc.) e intenta reiniciarlos automáticamente. También realiza análisis predictivo basado en la carga del sistema.
*   **🥭 SysAdmin AI (MANGO T5)**: Modelo especializado de 770M parámetros ajustado para traducir lenguaje natural a comandos `bash`, permitiendo administración avanzada del sistema por voz o texto.
*   **🔍 Smart Service Discovery**: Detecta automáticamente qué servicios están instalados en la máquina host para evitar falsas alertas.
*   **📅 Automatización Cron**: Nueva interfaz Web y gestor para programar tareas del sistema usando sintaxis cron.

### 🚀 Características Principales

#### 🧠 Inteligencia Híbrida
*   **LLM Local**: Integración con **Gemma 2B** (4-bit) para conversaciones fluidas, personalidad y razonamiento complejo sin depender de la nube.
*   **SysAdmin AI**: Modelo **MANGO T5** para una traducción robusta de Lenguaje Natural a Bash.
*   **Memoria (Brain)**: Sistema de memoria a largo plazo y aprendizaje de alias para comandos.
*   **RAG**: Capacidad de consultar documentos locales.

#### 🗣️ Interacción Natural
*   **Voz**: Reconocimiento offline con **Vosk** o **Whisper**.
*   **Habla**: Síntesis natural con **Piper TTS**.
*   **Interfaz Visual**: "Cara" reactiva que muestra estados del asistente.

#### 🛠️ Administración de Sistemas & Redes
*   **SysAdmin**: Control de servicios, actualizaciones, monitoreo de recursos y gestión de energía.
*   **SSH Manager**: Administración de servidores remotos por voz.
*   **Network Tools**: Escaneo de red, Ping, Whois, IP pública.

### 🔧 Instalación (Rama Testing)

**Instalación Nativa Recomendada:** (Ideal para control total del sistema y Self-Healing)

```bash
# Clonar y cambiar a rama testing
git clone https://github.com/jrodriiguezg/COLEGA.git
cd COLEGA
git checkout testing && git pull

# Ejecutar instalador nativo (Modo Servicio de Usuario)
# Esto descargará MANGO T5, Vosk, Piper y configurará systemd.
./install.sh
```

### ⚙️ Configuración

Archivo principal: `config/config.json`.
*   **Wake Word**: Palabra de activación ("tio", "colega").
*   **Preferencias**: Idioma, voz TTS, sensibilidad.

### 🖥️ Uso

COLEGA funciona como servicio en segundo plano:
*   **Logs**: `journalctl --user -u neo.service -f`
*   **Interfaz Web**: `http://localhost:5000/face`
*   **Comandos**: *"Colega, reinicia el servidor nginx"*, *"Colega, busca vulnerabilidades en la red"*.
