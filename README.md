# WatermelonD (v3.0.0-Experimental)

[🇺🇸 English](#english) | [🇪🇸 Español](#español)

---

## English

> [!WARNING]
> **Beta Stability**: This release (v3.0.0) is on the `main` branch. While feature-complete, you may encounter bugs or instability as we optimize the new WatermelonD architecture. Report issues on GitHub!

**WatermelonD** (formerly NEOPapaya) is a proactive and modular personal assistant designed to run locally on modest hardware. It combines the efficiency of a rule-based system for system control and home automation with the intelligence of a local LLM (**Gemma 2B**) for natural conversations and reasoning.

![Status](https://img.shields.io/badge/Status-Beta-yellow)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![License](https://img.shields.io/badge/License-GPLv3-green)

### 🌟 Project Structure (The Fruit Bowl)

* **🍉 WatermelonD (Core)**: The main container. A heavy, solid shell that holds everything else together.
* **🧠 BrainNut (AI)**: The brain. Hard shell on the outside, complex logic and memory on the inside.
* **🍊 TangerineUI (Web)**: The peel (shell). Easy to peel, bright, segmented, and user-friendly.
* **🫐 BlueberrySkills (Skills)**: Small, powerful, and numerous. Atomic functions scattered throughout the system.
* **🍇 BerryConnect (Network)**: Interconnected druplets. Mesh, nodes, and strong connections.
* **🍒 Watermelon-extras (Plugins)**: "The cherry on top." Custom extras and final touches added by the user.

### 🚀 Key Features

#### 🧠 Hybrid Intelligence

* **Local LLM**: Integration with **Gemma 2B** (4-bit) for fluid conversations.
* **BrainNut AI**: **MANGO T5** model for robust Natural Language to Bash translation.
* **Memory**: Long-term memory system and alias learning.
* **RAG (Retrieval-Augmented Generation)**: Query local documents.

#### 🗣️ Natural Interaction

* **TangerineUI**: Reactive "Face" (Web UI) showing states (listening, thinking, speaking).
* **Speech**: Natural synthesis with **Piper TTS** and offline recognition (Vosk/Whisper).

#### 🛡️ Security & Maintenance

* **WatermelonGuard**: IDS (Intrusion Detection System) that monitors logs and resources.
* **Auto-Diagnosis**: WatermelonD can read its own logs, find errors, and use AI to explain what is failing.

### 🔧 Installation

**Quick Install (One-line command):**

```bash
wget -O install.sh https://raw.githubusercontent.com/OpenMacedonIA/WatermelonD/refs/heads/main/install.sh && chmod +x install.sh && ./install.sh
```

**Manual Installation:**

```bash
# Clone the repository
git clone https://github.com/OpenMacedonIA/WatermelonD
cd WatermelonD

# Run the installer
./install.sh
```

### ⚙️ Configuration

Main configuration: `config/config.json`.
Access the Web Interface at `http://localhost:5000`.

---

## Español

> [!WARNING]
> **Estabilidad Beta**: Esta versión (v3.0.0) está en la rama `main`. Aunque es funcional, puedes encontrar errores mientras pulimos la nueva arquitectura de WatermelonD. ¡Reporta fallos en GitHub!

**WatermelonD** (antes NEOPapaya) es un asistente personal proactivo y modular diseñado para ejecutarse localmente.

![Status](https://img.shields.io/badge/Status-Beta-yellow)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![License](https://img.shields.io/badge/License-GPLv3-green)

### 🌟 Estructura del Proyecto (El Frutero)

* **🍉 WatermelonD (Core)**: El contenedor principal.
* **🧠 BrainNut (AI)**: El cerebro. Lógica compleja en el interior.
* **🍊 TangerineUI (Web)**: La cáscara. Interfaz amigable y segmentada.
* **🫐 BlueberrySkills (Skills)**: Funciones atómicas dispersas por el sistema.
* **🍇 BerryConnect (Network)**: Red conectada. Malla, nodos y conexiones fuertes.
* **🍒 Watermelon-extras (Plugins)**: "La guinda del pastel". Extras personalizados.

### 🚀 Características Principales

#### 🧠 Inteligencia Híbrida

* **LLM Local**: **Gemma 2B** para conversaciones.
* **BrainNut AI**: **MANGO T5** para comandos Bash.
* **Memoria**: Memoria a largo plazo y RAG.

#### 🗣️ Interacción Natural

* **Voz**: Reconocimiento offline con **Vosk** o **Whisper**.
* **Habla**: Síntesis natural con **Piper TTS**.
* **TangerineUI**: Interfaz visual reactiva.

#### 🛡️ Capacidades Avanzadas

* **WatermelonGuard**: Monitor de seguridad en tiempo real.
* **Auto-Diagnóstico**: Análisis de logs asistido por IA.

### 🔧 Instalación

**Instalación Rápida (Comando único):**

```bash
wget -O install.sh https://raw.githubusercontent.com/OpenMacedonIA/WatermelonD/refs/heads/main/install.sh && chmod +x install.sh && ./install.sh
```

**Instalación Manual:**

```bash
git clone https://github.com/OpenMacedonIA/WatermelonD
cd WatermelonD
./install.sh
```

### 🖥️ Uso

* **Interfaz Web**: `http://localhost:5000`
* **Logs**: `journalctl --user -u neo.service -f`
