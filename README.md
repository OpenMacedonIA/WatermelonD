# WatermelonD (v3.0-Dev)

[English](#english) | [Español](#español)

---

## English

> **Dev Status**: This is the **WatermelonD** development branch. We are transitioning from the legacy "NeoPapaya" architecture to the new modular **WatermelonD** system.




**WatermelonD** is a proactive and modular personal assistant designed to run locally on modest hardware. It combines the efficiency of a rule-based system for system control with the intelligence of a local LLM and the new **Lime Router** for fluid interactions.

![Status](https://img.shields.io/badge/Status-Beta-yellow)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![License](https://img.shields.io/badge/License-GPLv3-green)

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
* **SysAdmin AI**: **Lime + Grape Models** (T5) for robust Natural Language instruction processing.
* **Memory (Brain)**: Long-term memory system and alias learning.
* **RAG (Retrieval-Augmented Generation)**: Query local documents.

#### Natural Interaction

* **Visual Interface**: **TangerineUI** ("Mandarina") - Reactive "Face" and dashboard.
* **Speech**: Natural synthesis with **Piper TTS** and offline recognition (Vosk/Whisper).

#### Security & Maintenance (Advanced)

* **WatermelonGuard**: IDS (Intrusion Detection System) that monitors logs and resources.
* **Auto-Diagnosis**: WatermelonD self-diagnostics.



### Installation

**Quick Install (One-line command):**

```bash
wget -O install.sh https://raw.githubusercontent.com/OpenMacedonIA/WatermelonD/refs/heads/next/install.sh && chmod +x install.sh && ./install.sh
```

**Manual Installation:**

```bash
# Clone the repository
git clone -b next https://github.com/OpenMacedonIA/WatermelonD
cd WatermelonD

# Run the installer
./install.sh
```

### Configuration

Main configuration: `config/config.json`.
Access the Web Interface at `http://localhost:5000`.

---

## Español

> **Estado Dev**: Esta es la rama de desarrollo de **WatermelonD**. Estamos transicionando de la arquitectura "NeoPapaya" al nuevo sistema modular **WatermelonD**.


**WatermelonD** es un asistente personal proactivo y modular diseñado para ejecutarse localmente.

![Status](https://img.shields.io/badge/Status-Beta-yellow)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![License](https://img.shields.io/badge/License-GPLv3-green)

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
* **SysAdmin AI**: **Lime + Modelos Grape** (T5) para procesamiento robusto de instrucciones.
* **Memoria (Brain)**: Memoria a largo plazo y RAG.

#### Interacción Natural

* **Voz**: Reconocimiento offline con **Vosk** o **Whisper**.
* **Habla**: Síntesis natural con **Piper TTS**.
* **Interfaz Visual**: "Cara" reactiva que muestra estados del asistente.

#### Advanced Capabilities

* **WatermelonGuard**: Monitor de seguridad en tiempo real.
* **Auto-Diagnóstico**: Análisis de logs asistido por IA.
* **Multi-Room**: Control de dispositivos Cast.

#### Administración de Sistemas & Redes

### Instalación

**Instalación Rápida (Comando único):**


```bash
wget -O install.sh https://raw.githubusercontent.com/OpenMacedonIA/WatermelonD/refs/heads/next/install.sh && chmod +x install.sh && ./install.sh
```

**Manual Installation:**

```bash
git clone -b next https://github.com/OpenMacedonIA/WatermelonD
cd WatermelonD
./install.sh
```

### Uso

* **Interfaz Web**: `http://localhost:5000`
* **Logs**: `journalctl --user -u neo.service -f`
