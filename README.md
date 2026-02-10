# WatermelonD (v3.0-RC)

[English](#english) | [Español](#español)

---

## English

> **RC Status**: This is the **WatermelonD** release candidate branch. Stable and ready for testing before final release.




**WatermelonD** is a proactive and modular personal assistant designed to run locally on modest hardware. It combines the efficiency of a rule-based system for system control with the intelligence of a local LLM and the new **Lime Router** for fluid interactions.

![Status](https://img.shields.io/badge/Status-Beta-yellow)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![License](https://img.shields.io/badge/License-GPLv3-green)

### Recent Improvements (February 2026)

* **Security**: Fernet encryption (AES-128) for SSH passwords (replaced Base64)
* **Quality**: Removed emojis from logs for terminal compatibility
* **Reliability**: UTF-8 encoding explicit in file operations
* **Performance**: WiFi interface caching to reduce log spam
* **UX**: HTTPS certificate installation instructions in installer

### New in v2.5.0 (Experimental)

* **WatermelonD Core**: Optimized modular core.
  * **BerryConnect**: Connectivity modules.
  * **BlueberrySkills**: Modular skill system.
  * **BrainNut**: Knowledge and memory management.
* **TangerineUI (Web V3)**:
  * **Drag-and-Drop Dashboard**: Customize your workspace.
  * **Unified Notifications**: Modern Toast system + Desktop Notifications.
  * **Connection Monitor**: Auto-detection of system restarts.
* **SysAdmin AI (Lime/Grape)**: **New!** Powered by the **Lime Router** and **[Grape Models (T5)](https://huggingface.co/collections/jrodriiguezg/grape-models)**.


### Key Features

#### Hybrid Intelligence

* **Local LLM**: Integration with **Gemma 2B** (4-bit) for fluid conversations.
* **SysAdmin AI (BrainNut)**: **Lime + Grape Models** (T5) for Natural Language to Bash translation.

#### Natural Interaction

* **Visual Interface**: **TangerineUI** ("Mandarina") - Reactive "Face" and dashboard.
* **Speech**: Natural synthesis with **Piper TTS** and offline recognition (Vosk/Whisper).

#### Security & Maintenance (Advanced)

* **WatermelonGuard**: IDS (Intrusion Detection System) that monitors logs and resources.
* **Auto-Diagnosis**: WatermelonD self-diagnostics.



### Installation

```bash
wget -O install.sh https://raw.githubusercontent.com/OpenMacedonIA/WatermelonD/refs/heads/main/install.sh && chmod +x install.sh && ./install.sh
```

**Manual Installation:**

```bash
# Clone the repository
git clone  https://github.com/OpenMacedonIA/WatermelonD
cd WatermelonD

# Run the installer
./install.sh
```

### Configuration

Main configuration: `config/config.json`.
Access the Web Interface at `http://localhost:5000`.

---

## Español

> **Estado RC**: Esta es la rama candidata a release de **WatermelonD**. Estable y lista para pruebas antes del lanzamiento final.


**WatermelonD** es un asistente personal proactivo y modular diseñado para ejecutarse localmente.

![Status](https://img.shields.io/badge/Status-Beta-yellow)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![License](https://img.shields.io/badge/License-GPLv3-green)

### Mejoras Recientes (Febrero 2026)

* **Seguridad**: Encriptacion Fernet (AES-128) para contrasenas SSH (reemplaza Base64)
* **Calidad**: Eliminados emojis de logs para compatibilidad con terminales
* **Confiabilidad**: Encoding UTF-8 explicito en operaciones de archivo
* **Rendimiento**: Cache de interfaz WiFi para reducir spam en logs
* **UX**: Instrucciones de instalacion de certificados HTTPS en el instalador

### Novedades en v2.5.0 (Experimental)

* **WatermelonD Core**: Core modular optimizado.
  * **BerryConnect**: Módulos de conectividad.
  * **BlueberrySkills**: Sistema de habilidades modular.
  * **BrainNut**: Gestión de memoria y conocimiento.
* **TangerineUI (Web V2.2)**:
  * **Dashboard Personalizable**: Organiza los widgets con **Drag-and-Drop**.
  * **Notificaciones Unificadas**: Sistema de Toasts moderno.
* **SysAdmin AI (Lime/Grape)**: Impulsado por el **Router Lime** y los **[Modelos Grape (T5)](https://huggingface.co/collections/jrodriiguezg/grape-models)**.

### Características Principales

#### Inteligencia Híbrida

* **LLM Local**: **Gemma 2B** para conversaciones.
* **SysAdmin AI (BrainNut)**: **Lime + Modelos Grape** (T5) para traduccion lenguaje natural a Bash.

#### Interacción Natural

* **Voz**: Reconocimiento offline con **Vosk** o **Whisper**.
* **Habla**: Síntesis natural con **Piper TTS**.
* **Interfaz Visual**: "Cara" reactiva que muestra estados del asistente.

#### Seguridad y Automatizacion

* **WatermelonGuard**: IDS que detecta brute-force SSH, DoS y anomalias del sistema.
* **Auto-Diagnostico**: Analisis de logs asistido por IA.
* **Multi-Room Cast**: Control de dispositivos Chromecast (requiere pychromecast).

### Instalación

```bash
wget -O install.sh https://raw.githubusercontent.com/OpenMacedonIA/WatermelonD/refs/heads/main/install.sh && chmod +x install.sh && ./install.sh
```

**Manual Installation:**

```bash
git clone -b rc https://github.com/OpenMacedonIA/WatermelonD
cd WatermelonD
./install.sh
```

### Uso

* **Interfaz Web**: `http://localhost:5000`
* **Logs**: `journalctl --user -u neo.service -f`
