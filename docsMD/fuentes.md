# FUENTES DE INFORMACIÓN Y REFERENCIAS BIBLIOGRÁFICAS

**Proyecto:** NEOPapaya (Language Copilot for Group and Administration Environments)
**Fecha:** 04/12/2025
**Versión del Documento:** 1.1 (Versión Extendida)

---

## 1. INTRODUCCIÓN

Este documento constituye el compendio bibliográfico y de recursos técnicos del proyecto NEOPapaya Su objetivo es proporcionar una trazabilidad completa de las tecnologías, algoritmos y herramientas utilizadas, facilitando la auditoría técnica, el mantenimiento futuro y la comprensión profunda de la arquitectura del sistema.

---

## 2. LENGUAJES DE PROGRAMACIÓN Y ENTORNOS

### 2.1. Python (Core Logic)

El ecosistema Python es el pilar central debido a su predominancia en IA.

* **Documentación Oficial:** [Python 3.11 Docs](https://docs.python.org/3.11/)
* **Guía de Estilo (PEP 8):** [Style Guide for Python Code](https://peps.python.org/pep-0008/)
* **Gestión de Entornos (Venv):** [Creation of virtual environments](https://docs.python.org/3/library/venv.html)
* **Tipado Estático (Typing):** [Support for type hints](https://docs.python.org/3/library/typing.html) - Usado para mejorar la robustez del código.

### 2.2. C/C++ (High Performance)

Utilizado subyacentemente en librerías críticas como `llama.cpp` y `FANN`.

* **Referencia C++:** [cppreference.com](https://en.cppreference.com/w/)
* **Compilador GCC:** [GCC, the GNU Compiler Collection](https://gcc.gnu.org/)

### 2.3. Bash / Shell Scripting

Automatización de despliegue y tareas de sistema.

* **Bash Reference Manual:** [GNU Bash](https://www.gnu.org/software/bash/manual/)
* **ShellCheck:** [ShellCheck](https://www.shellcheck.net/) - Herramienta de análisis estático para scripts de shell.

---

## 3. SISTEMA OPERATIVO Y HARDWARE

### 3.1. Raspberry Pi OS (Debian Bookworm)

* **Documentación Oficial:** [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)
* **Configuración Headless:** [Remote Access (SSH/VNC)](https://www.raspberrypi.com/documentation/computers/remote-access.html)
* **Optimización de Energía:** [Power Management](https://www.raspberrypi.com/documentation/computers/compute-module.html#power-consumption)

### 3.2. Gestión de Procesos (Systemd)

* **Systemd Service Units:** [freedesktop.org](https://www.freedesktop.org/software/systemd/man/systemd.service.html) - Referencia para la creación de los servicios `colega.service`.
* **Journalctl:** [Debugging Systemd](https://www.freedesktop.org/software/systemd/man/journalctl.html)

---

## 4. INTELIGENCIA ARTIFICIAL GENERATIVA (LLM)

### 4.1. Modelos Fundacionales

* **Gemma (Google DeepMind):**
 * *Web:* [Gemma Open Models](https://ai.google.dev/gemma)
 * *Paper:* [Gemma Technical Report](https://storage.googleapis.com/deepmind-media/gemma/gemma-report.pdf)
 * *Licencia:* [Gemma Terms of Use](https://ai.google.dev/gemma/terms)
* **Llama 3 (Meta):**
 * *Web:* [Llama 3](https://llama.meta.com/)
 * *Model Card:* [Llama 3 Model Card](https://github.com/meta-llama/llama3/blob/main/MODEL_CARD.md)

### 4.2. Inferencia y Cuantización

* **Llama.cpp:** [GitHub Repository](https://github.com/ggerganov/llama.cpp)
 * *Optimizaciones ARM:* Uso de instrucciones NEON para aceleración en CPU.
* **Formato GGUF:** [GGUF Spec](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md)
 * *Quantization Types:* Explicación de Q4_K_M, Q8_0, etc.

---

## 5. COMPRENSIÓN DEL LENGUAJE (NLU) Y LÓGICA DIFUSA

### 5.1. Redes Neuronales Superficiales (FANN/Padatious)

* **FANN (Fast Artificial Neural Network):** [Library Reference](http://leenissen.dk/fann/wp/)
* **Padatious:** [Source Code](https://github.com/MycroftAI/Padatious)
 * *Algoritmo:* Entrenamiento de redes MLP para clasificación de intenciones con pocos datos (Few-Shot Learning).

### 5.2. Coincidencia de Cadenas (Fuzzy Matching)

* **RapidFuzz:** [Documentation](https://rapidfuzz.github.io/RapidFuzz/)
 * *Distancia de Levenshtein:* [Wikipedia Article](https://en.wikipedia.org/wiki/Levenshtein_distance) - Fundamento matemático.
 * *Jaro-Winkler Distance:* [Wikipedia Article](https://en.wikipedia.org/wiki/Jaro%E2%80%93Winkler_distance) - Métrica alternativa para cadenas cortas.

---

## 6. PROCESAMIENTO DE AUDIO Y SEÑALES (DSP)

### 6.1. Reconocimiento de Voz (ASR/STT)

* **Vosk (Kaldi-based):**
 * *Web:* [Vosk API](https://alphacephei.com/vosk/)
 * *Kaldi Toolkit:* [Kaldi ASR](https://kaldi-asr.org/) - El motor subyacente de Vosk.
* **Whisper (OpenAI):** [OpenAI Whisper](https://github.com/openai/whisper)

### 6.2. Síntesis de Voz (TTS)

* **Piper TTS:** [Piper GitHub](https://github.com/rhasspy/piper)
 * *VITS (Variational Inference with adversarial learning for end-to-end Text-to-Speech):* [Paper (arXiv:2106.06103)](https://arxiv.org/abs/2106.06103) - Arquitectura neuronal usada por Piper.

### 6.3. Librerías de Audio Python

* **PyAudio (PortAudio wrapper):** [Docs](https://people.csail.mit.edu/hubert/pyaudio/)
* **SoundFile:** [Docs](https://pysoundfile.readthedocs.io/) - Lectura/escritura de archivos WAV/FLAC.
* **NumPy (DSP):** [NumPy Reference](https://numpy.org/doc/stable/reference/) - Usado para cálculos de RMS y transformadas (FFT) si fuera necesario.

---

## 7. VISIÓN ARTIFICIAL (COMPUTER VISION)

### 7.1. OpenCV (Open Source Computer Vision Library)

Utilizado para la detección de rostros y procesamiento de imágenes.

* **Web Oficial:** [OpenCV.org](https://opencv.org/)
* **Documentación Python:** [OpenCV-Python Tutorials](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
* **Haar Cascades:** [Face Detection using Haar Cascades](https://docs.opencv.org/3.4/db/d28/tutorial_cascade_classifier.html) - Método clásico y ligero usado en el proyecto.

---

## 8. COMUNICACIÓN Y REDES

### 8.1. MQTT (Message Queuing Telemetry Transport)

Protocolo ligero para IoT.

* **Eclipse Mosquitto (Broker):** [Mosquitto Man Page](https://mosquitto.org/man/mosquitto-8.html)
* **Paho MQTT Client:** [Paho Python](https://pypi.org/project/paho-mqtt/)

### 8.2. SSH y Administración Remota

* **OpenSSH:** [OpenSSH Manual](https://www.openssh.com/manual.html)
* **Paramiko (Python SSH):** [Paramiko Docs](https://www.paramiko.org/) - Librería para implementar clientes SSH en Python (usada para administrar otros nodos).

---

## 9. PERSISTENCIA Y DATOS

### 9.1. SQLite

* **SQLite Syntax:** [SQL As Understood By SQLite](https://www.sqlite.org/lang.html)
* **JSON (JavaScript Object Notation):** [ECMA-404 Standard](https://www.json.org/json-en.html) - Formato estándar para configuración e intercambio de datos.

---

## 10. LIBRERÍAS DE UTILIDAD Y SOPORTE

### 10.1. Sistema y Procesos

* **Psutil:** [Documentation](https://psutil.readthedocs.io/) - Monitorización de CPU, memoria y temperatura.
* **Subprocess:** [Python Docs](https://docs.python.org/3/library/subprocess.html) - Ejecución de comandos del sistema.

### 10.2. Interfaz y Logs

* **Colorama:** [PyPI Page](https://pypi.org/project/colorama/) - Coloreado de terminal para logs legibles.
* **Logging:** [Python Logging Cookbook](https://docs.python.org/3/howto/logging-cookbook.html)

---

## 11. REFERENCIAS ACADÉMICAS CLAVE (PAPERS)

Lecturas recomendadas para entender la teoría profunda detrás de los componentes.

* **Transformers:** *Vaswani, A., et al. (2017). Attention Is All You Need.* [Link](https://arxiv.org/abs/1706.03762)
* **LoRA:** *Hu, E. J., et al. (2021). LoRA: Low-Rank Adaptation of Large Language Models.* [Link](https://arxiv.org/abs/2106.09685)
* **VITS (TTS):** *Kim, J., et al. (2021). Conditional Variational Autoencoder with Adversarial Learning for End-to-End Text-to-Speech.* [Link](https://arxiv.org/abs/2106.06103)
* **YOLO (Vision - Referencia):** *Redmon, J., et al. (2016). You Only Look Once: Unified, Real-Time Object Detection.* [Link](https://arxiv.org/abs/1506.02640)

---

## 12. HERRAMIENTAS DE DESARROLLO

* **Git:** [Git SCM](https://git-scm.com/doc) - Control de versiones.
* **Visual Studio Code:** [VS Code Docs](https://code.visualstudio.com/docs) - IDE recomendado.
 * *Remote - SSH Extension:* Para desarrollo remoto en la Raspberry Pi.

---

**Nota:** Todas las marcas registradas y nombres de productos mencionados pertenecen a sus respectivos propietarios. Los enlaces proporcionados estaban activos a fecha de creación del documento.
