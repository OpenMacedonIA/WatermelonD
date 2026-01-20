# ANEXO II: MANUAL TÉCNICO DE DESPLIEGUE (INGENIERÍA)

**Proyecto:** WatermelonD (Language Copilot for Group and Administration Environments) 
**Versión del Documento:** 2.1 (Revisión Técnica Extendida) 
**Fecha:** 03/12/2025 
**Estado:** Release Candidate 
**Nivel de Acceso:** Ingeniería / DevOps

---

## ÍNDICE DE CONTENIDOS

1. [INTRODUCCIÓN TÉCNICA](#1-introducción-técnica)
 1.1. Propósito y Diferenciación
 1.2. Stack Tecnológico Detallado
 1.3. Filosofía de Diseño (Edge Computing)
2. [ARQUITECTURA INTERNA Y FLUJO DE DATOS](#2-arquitectura-interna-y-flujo-de-datos)
 2.1. Diagrama de Componentes (Nivel Kernel)
 2.2. Esquema de Mensajería MQTT (Network Bros)
 2.3. Pipeline de Audio (ALSA -> VAD -> STT)
 2.4. Gestión de Memoria y Ciclo de Vida
3. [INSTALACIÓN DE BAJO NIVEL (DEEP DIVE)](#3-instalación-de-bajo-nivel-deep-dive)
 3.1. Compilación de Dependencias Críticas
 3.2. Configuración del Entorno Python (PEP 582 vs Venv)
 3.3. Despliegue de Modelos (GGUF & ONNX)
 3.4. Troubleshooting de Compilación
4. [TUNING Y OPTIMIZACIÓN DEL KERNEL](#4-tuning-y-optimización-del-kernel)
 4.1. Parámetros Sysctl para Baja Latencia
 4.2. Configuración de Prioridad de Procesos (Nice/Renice)
 4.3. Gestión de Memoria (ZRAM y OOM Killer)
 4.4. Gobernanza de CPU (CPUFreq)
5. [INFRAESTRUCTURA COMO CÓDIGO (IaC)](#5-infraestructura-como-código-iac)
 5.1. Dockerfile de Referencia (Producción)
 5.2. Orquestación con Docker Compose
 5.3. Despliegue en Kubernetes (K3s)
 5.4. Estrategia de Persistencia
6. [INTEGRACIÓN CONTINUA (CI/CD)](#6-integración-continua-cicd)
 6.1. Pipeline de Tests Automatizados (GitHub Actions)
 6.2. Análisis Estático de Código (Linting & Typing)
 6.3. Release Management
7. [SEGURIDAD Y HARDENING AVANZADO](#7-seguridad-y-hardening-avanzado)
 7.1. Aislamiento de Red (Namespaces)
 7.2. Políticas de AppArmor/SELinux
 7.3. Protección contra Fuerza Bruta (Fail2Ban)
 7.4. Gestión de Secretos y Certificados SSL
8. [ANEXOS TÉCNICOS](#8-anexos-técnicos)
 8.1. Mapa de Memoria (Memory Footprint)
 8.2. Códigos de Error y Debugging (Ver ANEXO IV)

---

## 1. INTRODUCCIÓN TÉCNICA

### 1.1. Propósito y Diferenciación
A diferencia del *Manual de Usuario y Administración (Anexo I)*, que se centra en la operación funcional y la interacción diaria, este documento detalla la **ingeniería subyacente** del sistema. Está diseñado para ingenieros de DevOps, SREs (Site Reliability Engineers) y desarrolladores *backend* que necesitan entender cómo el sistema interactúa con el hardware, el kernel de Linux y la red a bajo nivel.

Mientras que el Anexo I explica "cómo usar" el sistema, este Anexo II explica "cómo funciona" por dentro y "cómo desplegarlo" de manera robusta y escalable.

### 1.2. Stack Tecnológico Detallado
El sistema se construye sobre un stack moderno y eficiente, priorizando el rendimiento en hardware limitado:

* **Lenguaje Core:** Python 3.10+ (Uso extensivo de `asyncio` para I/O bound y `threading` para CPU bound).
* **Inferencia LLM:** `llama.cpp` (vía `llama-cpp-python`) con soporte para instrucciones vectoriales AVX2/AVX512 y aceleración Metal (macOS) o CUDA (NVIDIA).
* **Audio I/O:** `PyAudio` (wrapper de PortAudio) interactuando directamente con la capa ALSA de Linux para minimizar latencia, evitando servidores de sonido de usuario como PulseAudio en entornos headless.
* **STT Engine (Speech-to-Text):**
 * *Vosk:* Basado en Kaldi, utiliza modelos de grafos FST (Finite State Transducers). Robusto pero pesado en memoria.
 * *Sherpa-ONNX:* Motor de inferencia de próxima generación basado en Transducer/Whisper, optimizado con ONNX Runtime.
* **TTS Engine (Text-to-Speech):** *Piper*, un sintetizador neuronal rápido optimizado para ejecutarse en CPU (incluso en Raspberry Pi Zero 2).
* **Vector Database:** *ChromaDB* para el sistema RAG (Memoria documental).
* **NL2Bash Engine:** *MANGO T5* (Transformers/Torch) para traducción de comandos complejos.
* **Bus de Eventos:** MQTT v3.1.1 (Mosquitto) para la comunicación inter-procesos e inter-dispositivos.
* **Base de Datos:** SQLite 3 con modo WAL (Write-Ahead Logging) para concurrencia.

### 1.3. Filosofía de Diseño (Edge Computing)
WatermelonD sigue una filosofía "Local-First".
* **Privacidad:** Ningún dato de voz o texto sale de la red local.
* **Latencia:** El procesamiento en el borde (Edge) elimina la latencia de red hacia la nube.
* **Resiliencia:** El sistema funciona 100% offline (excepto para funciones que explícitamente requieren internet, como `speedtest` o `clima`).

---

## 2. ARQUITECTURA INTERNA Y FLUJO DE DATOS

### 2.1. Diagrama de Componentes (Nivel Kernel)
El núcleo `WatermelonD` actúa como un *Event Loop* híbrido que orquesta hilos bloqueantes (Audio I/O) y no bloqueantes (MQTT, Web Server).

```mermaid
graph TD
 subgraph "Kernel Space (ALSA)"
 HW[Hardware Audio]
 end

 subgraph "User Space (WatermelonD)"
 Mic[PyAudio Stream] -->|PCM Raw| RingBuffer
 RingBuffer -->|Chunks| VAD[Voice Activity Detection]
 VAD -->|Speech Frames| STT[STT Engine]
 STT -->|Text| Intent[Intent Manager]
 
 Intent -->|Match| Skill[Skill Executor]
 Intent -->|No Match| LLM[AI Engine (Gemma)]
 
 LLM -->|Token Stream| TTS[TTS Engine]
 TTS -->|WAV Data| Speaker[PyAudio Output]
 
 Skill -->|JSON| MQTT_Client[Paho MQTT]
 end
 
 subgraph "External"
 MQTT_Broker[Mosquitto Broker]
 WebClient[Browser UI]
 end

 HW <--> Mic
 HW <--> Speaker
 MQTT_Client <--> MQTT_Broker
 WebClient <--> Flask_Server
```

### 2.2. Esquema de Mensajería MQTT (Network Bros)
El protocolo de comunicación entre agentes sigue una estructura jerárquica estricta para garantizar la interoperabilidad y el descubrimiento automático.

**Topic Base:** `tio/agents/{hostname}/{type}`

| Nivel | Valor | Descripción |
| :--- | :--- | :--- |
| Root | `tio` | Namespace global del proyecto. |
| Group | `agents` | Subgrupo para agentes inteligentes. |
| ID | `{hostname}` | Identificador único del dispositivo (ej. `neo-pi4`, `desktop-lab`). |
| Type | `telemetry` | Datos periódicos de estado (Heartbeat). |
| Type | `alerts` | Eventos críticos (seguridad, errores de hardware). |
| Type | `commands` | (Suscripción) Comandos remotos a ejecutar por el agente. |
| Type | `discovery` | (Retained) Mensaje de "Hola" al conectarse. |

**Payloads JSON Definidos:**

**1. Telemetría (`.../telemetry`):**
Se envía cada 60 segundos por defecto.
```json
{
 "cpu_usage": 15.4, // Porcentaje de uso de CPU
 "ram_usage": 42.1, // Porcentaje de uso de RAM
 "temperature": 45.0, // Temperatura del SoC en Celsius
 "uptime": 3600, // Tiempo de actividad en segundos
 "status": "idle", // Estados: boot, idle, listening, thinking, speaking, error
 "ip_address": "192.168.1.50"
}
```

**2. Alertas (`.../alerts`):**
Se envía inmediatamente al ocurrir un evento. QoS 2 recomendado.
```json
{
 "level": "critical", // info, warning, critical
 "code": "AUTH_FAIL", // Código de error interno estandarizado
 "msg": "Intento de acceso SSH fallido desde 192.168.1.50",
 "source": "GuardModule",
 "timestamp": 1701620000
}
```

**3. Comandos (`.../commands`):**
Para control remoto.
```json
{
 "action": "reboot",
 "force": true,
 "auth_token": "JWT_TOKEN_SI_APLICA"
}
```

### 2.3. Pipeline de Audio (ALSA -> VAD -> STT)
El sistema evita el uso de PulseAudio/PipeWire en entornos *headless* para reducir latencia y consumo de CPU.

1. **Captura:** `PyAudio` abre un stream directo al dispositivo `hw:X,Y` (donde X es la tarjeta y Y el dispositivo). Se usa un tamaño de chunk de 1024 frames (aprox 64ms a 16kHz).
2. **VAD (Voice Activity Detection):**
 * *Energía (RMS):* Cálculo rápido de `sqrt(mean(square(samples)))`. Es extremadamente ligero.
 * *Lógica:* Si `RMS > Umbral` durante `N` frames consecutivos, se considera inicio de voz.
 * *Silencio:* Se mantiene un buffer circular. Si el nivel cae por debajo del umbral durante `M` frames (ej. 1 segundo), se corta el segmento y se envía a procesar.
3. **Buffer:** Los frames de audio se acumulan en un `RingBuffer` antes de enviarse al decodificador para evitar *buffer underruns* si la CPU está ocupada.
4. **Safe Mode (Modo Seguro):** Si la inicialización de PyAudio o Jack falla (común en entornos contenerizados o mal configurados), el sistema captura la excepción e inicializa objetos `Mock` (simulados). Esto permite que el núcleo (`WatermelonD`) arranque completamente en modo "Sordo/Mudo", manteniendo operativas las funciones de red y la interfaz web sin crashear. El estado se refleja globalmente en `AUDIO_STATUS`.

### 2.4. Gestión de Memoria y Ciclo de Vida
* **Carga Perezosa (Lazy Loading):** Los modelos pesados (Gemma) no se cargan en RAM hasta el primer uso o solicitud explícita, a menos que se configure `preload: true`.
* **Descarga Automática:** Si la memoria es crítica, el sistema puede descargar el modelo LLM después de un tiempo de inactividad (TTL configurable).
* **Garbage Collection:** Se fuerza `gc.collect()` tras inferencias grandes para liberar memoria fragmentada.

---

## 3. INSTALACIÓN DE BAJO NIVEL (DEEP DIVE)

### 3.1. Compilación de Dependencias Críticas
Ciertas librerías requieren compilación específica para aprovechar las instrucciones del procesador (NEON en ARM, AVX en x86). Instalar los binarios genéricos de PyPI puede resultar en una pérdida de rendimiento del 50-300%.

**FANN (Fast Artificial Neural Network):**
Utilizada por `Padatious` para la clasificación de intenciones mediante redes neuronales simples.
```bash
# Dependencias de compilación
sudo apt install libfann-dev swig
# Instalación con pip forzando compilación desde fuente
pip install fann2 --no-binary :all:
```

**Llama-cpp-python:**
El motor del LLM. Debe compilarse con las flags correctas para el hardware específico.

*Para CPU x86 moderna (Intel/AMD con AVX2):*
```bash
CMAKE_ARGS="-DGGML_AVX2=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

*Para Raspberry Pi 4/5 (ARM64 con NEON):*
```bash
CMAKE_ARGS="-DGGML_NEON=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

*Para NVIDIA GPU (CUDA):*
```bash
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### 3.2. Configuración del Entorno Python (PEP 582 vs Venv)
Se recomienda el uso de `venv` estándar por su estabilidad, pero asegurando aislamiento total de `site-packages` del sistema para evitar conflictos con librerías de la distribución (ej. `python3-numpy` de apt vs `numpy` de pip).

* **Path:** `/home/usuario/WatermelonD/venv`
* **Pip.conf:** Configurar `global.index-url` si se usa un mirror corporativo o caché local (ej. `devpi`) para acelerar despliegues repetitivos.

### 3.3. Despliegue de Modelos (GGUF & ONNX)
El sistema soporta carga dinámica, pero se recomienda pre-descarga ("baking") en imágenes de despliegue o durante el aprovisionamiento.

* **GGUF (Gemma):** Mapeado en memoria (`mmap`). Requiere que el archivo no esté fragmentado en disco para un rendimiento óptimo. Se recomienda usar sistemas de archivos como EXT4 o XFS.
* **ONNX (Sherpa/Piper):** Ejecución mediante `onnxruntime`.
 * *Optimización:* Usar `onnxruntime-gpu` si existe GPU NVIDIA, o `onnxruntime-openvino` para CPUs Intel para acelerar el STT/TTS.

### 3.4. Troubleshooting de Compilación
> **Nota:** Esta sección se ha movido al **[ANEXO IV: RESOLUCIÓN DE PROBLEMAS](ANEXO_IV_RESOLUCION_DE_PROBLEMAS.md)**.

---

## 4. TUNING Y OPTIMIZACIÓN DEL KERNEL

### 4.1. Parámetros Sysctl para Baja Latencia
Para un asistente de voz, la latencia de audio es crítica. Añadir a `/etc/sysctl.d/99-neo-latency.conf`:

```ini
# Aumentar la frecuencia máxima de interrupciones RTC (para temporizadores precisos)
dev.hpet.max-user-freq = 2048

# Swappiness bajo para evitar paginación de modelos de IA a disco
vm.swappiness = 10
# Preferir mantener inodos/dentries en caché
vm.vfs_cache_pressure = 50

# Aumentar buffers de red para MQTT/WebSockets (importante para streaming de audio si se implementa)
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216

# Optimización de TCP
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_slow_start_after_idle = 0
```

Aplicar cambios con: `sudo sysctl -p /etc/sysctl.d/99-neo-latency.conf`

### 4.2. Configuración de Prioridad de Procesos (Nice/Renice)
El servicio debe tener prioridad sobre procesos de fondo, pero no tanta como para bloquear el kernel.
En `neo.service`:
```ini
[Service]
# Política Round Robin (Soft Real-Time)
CPUSchedulingPolicy=rr
CPUSchedulingPriority=50
# Nice negativo para mayor prioridad en el scheduler estándar
Nice=-10
```
*Nota: Requiere permisos de Real-Time (RT) configurados en `/etc/security/limits.conf` para el usuario.*

### 4.3. Gestión de Memoria (ZRAM y OOM Killer)
Para evitar que el kernel mate el proceso `python` durante un pico de inferencia (ej. cargando contexto largo):

1. **OOM Score:** Ajustar en systemd `OOMScoreAdjust=-500`. Esto reduce la probabilidad de que el OOM Killer elija este proceso como víctima (rango -1000 a 1000).
2. **ZRAM:** Configurar compresión `zstd` o `lz4` para la swap en RAM. Esto efectivamente duplica la RAM disponible para datos comprimibles (texto, logs, estructuras JSON).

### 4.4. Gobernanza de CPU (CPUFreq)
En dispositivos ARM (Raspberry Pi), el cambio de frecuencia de CPU puede introducir latencia en el procesamiento de audio.
Se recomienda fijar el gobernador en `performance` durante la operación:

```bash
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```
O configurar `cpufrequtils` para hacerlo persistente.

---

## 5. INFRAESTRUCTURA COMO CÓDIGO (IaC)

### 5.1. Dockerfile de Referencia (Producción)
Para despliegues contenerizados (ej. Kubernetes/K3s en Edge). Este Dockerfile utiliza *multi-stage builds* para mantener la imagen final ligera.

```dockerfile
# Stage 1: Builder
FROM python:3.10-slim-bookworm AS builder

# Instalar build tools y librerías de desarrollo
RUN apt-get update && apt-get install -y \
 build-essential cmake git libopenblas-dev libfann-dev swig \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
# Instalar dependencias en .local para copiar después
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.10-slim-bookworm

# Instalar solo librerías de runtime necesarias
RUN apt-get update && apt-get install -y \
 libportaudio2 libgomp1 libatomic1 libfann2 \
 mosquitto-clients \
 && rm -rf /var/lib/apt/lists/*

# Copiar librerías instaladas desde el builder
COPY --from=builder /root/.local /root/.local
COPY . /app
WORKDIR /app

# Configurar entorno
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV LD_LIBRARY_PATH=/root/.local/lib:$LD_LIBRARY_PATH

# Crear usuario no-root por seguridad
RUN useradd -m -u 1000 neo && chown -R neo:neo /app
USER neo

# Exponer puertos
EXPOSE 5000 1883

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
 CMD curl -f http://localhost:5000/api/status || exit 1

CMD ["python", "start_services.py"]
```

### 5.2. Orquestación con Docker Compose
Para desplegar el stack completo (WatermelonD + Mosquitto + UI).

```yaml
version: '3.8'

services:
 neo-core:
 build: .
 image: WatermelonD-core:latest
 container_name: neo_core
 restart: unless-stopped
 devices:
 - "/dev/snd:/dev/snd"# Acceso directo a audio
 volumes:
 - ./config:/app/config
 - ./database:/app/database
 - ./models:/app/models
 - ./logs:/app/logs
 environment:
 - MQTT_BROKER=mosquitto
 - TZ=Europe/Madrid
 depends_on:
 - mosquitto
 network_mode: host# Recomendado para acceso a hardware y mDNS

 mosquitto:
 image: eclipse-mosquitto:2
 container_name: neo_mqtt
 restart: always
 ports:
 - "1883:1883"
 - "9001:9001"
 volumes:
 - ./mosquitto/config:/mosquitto/config
 - ./mosquitto/data:/mosquitto/data
 - ./mosquitto/log:/mosquitto/log
```

### 5.3. Despliegue en Kubernetes (K3s)
Ejemplo de `Deployment` para un clúster K3s en Raspberry Pi.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
 name: neo-assistant
spec:
 replicas: 1
 selector:
 matchLabels:
 app: neo
 template:
 metadata:
 labels:
 app: neo
 spec:
 containers:
 - name: neo
 image: WatermelonD-core:arm64-v2.1
 resources:
 requests:
 memory: "512Mi"
 cpu: "500m"
 limits:
 memory: "2Gi"
 cpu: "2000m"
 securityContext:
 privileged: true# Necesario para acceso a /dev/snd en algunos setups
 volumeMounts:
 - name: audio-dev
 mountPath: /dev/snd
 volumes:
 - name: audio-dev
 hostPath:
 path: /dev/snd
```

### 5.4. Estrategia de Persistencia
Los contenedores deben tratar el sistema de archivos como efímero.
* **Configuración (`/app/config`):** Montar como `ConfigMap` o volumen de solo lectura.
* **Base de Datos (`/app/database`):** Montar `PersistentVolumeClaim` (PVC) respaldado por almacenamiento local rápido (LocalPath) o NFS.
* **Modelos (`/app/models`):** Usar un volumen compartido o "initContainer" que descargue los modelos al inicio si no existen.

---

## 6. INTEGRACIÓN CONTINUA (CI/CD)

### 6.1. Pipeline de Tests Automatizados (GitHub Actions)
Se sugiere un pipeline robusto que valide cada commit.

```yaml
name: CI Pipeline

on: [push, pull_request]

jobs:
 test:
 runs-on: ubuntu-latest
 strategy:
 matrix:
 python-version: ["3.10"]

 steps:
 - uses: actions/checkout@v3
 
 - name: Set up Python ${{ matrix.python-version }}
 uses: actions/setup-python@v4
 with:
 python-version: ${{ matrix.python-version }}
 
 - name: Install System Dependencies
 run: |
 sudo apt-get update
 sudo apt-get install -y libportaudio2 libfann-dev swig mosquitto
 
 - name: Install Python Dependencies
 run: |
 python -m pip install --upgrade pip
 pip install -r requirements.txt
 pip install pytest pytest-asyncio flake8 mypy
 
 - name: Lint with Flake8
 run: |
# stop the build if there are Python syntax errors or undefined names
 flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
 
 - name: Type Check with Mypy
 run: mypy modules/ --ignore-missing-imports
 
 - name: Run Unit Tests
 run: pytest tests/unit/
 
 - name: Run Integration Tests
 run: |
# Start Mosquitto in background
 mosquitto -d
 pytest tests/integration/
```

### 6.2. Análisis Estático de Código (Linting & Typing)
* **Flake8:** Para estilo (PEP 8) y errores de sintaxis.
* **Mypy:** Para chequeo de tipos estáticos. Es crítico en `WatermelonD` para evitar `TypeError` en tiempo de ejecución que podrían detener el servicio en producción.
* **Bandit:** Para análisis de seguridad (búsqueda de hardcoded passwords, uso inseguro de `eval`, etc.).

### 6.3. Release Management
* **Versionado Semántico:** Seguir SemVer (MAJOR.MINOR.PATCH).
* **Tags de Git:** Crear un tag (ej. `v2.1.0`) debe disparar el build de la imagen Docker y su push al registro (Docker Hub / GHCR).

---

## 7. SEGURIDAD Y HARDENING AVANZADO

### 7.1. Aislamiento de Red (Namespaces)
Si se ejecuta con Systemd nativo, se pueden usar las directivas de sandboxing para aislar el proceso:

```ini
[Service]
# Solo permitir acceso a red, no a /home (excepto RW paths explícitos)
ProtectHome=read-only
ReadWritePaths=/home/usuario/WatermelonD/database /home/usuario/WatermelonD/logs
# Aislar /tmp (crea un /tmp privado para el proceso)
PrivateTmp=true
# Prohibir escalada de privilegios (sudo, suid)
NoNewPrivileges=true
# Restringir acceso a dispositivos (solo permitir sonido y null/zero/random)
DeviceAllow=/dev/snd/* rw
DeviceAllow=/dev/null rw
DeviceAllow=/dev/zero rw
DeviceAllow=/dev/urandom r
DevicePolicy=closed
```

### 7.2. Políticas de AppArmor/SELinux
Para entornos de alta seguridad (ej. oficinas gubernamentales), se debe generar un perfil AppArmor que restrinja estrictamente al proceso Python.

**Perfil AppArmor Básico (`/etc/apparmor.d/usr.bin.neo`):**
```apparmor
#include <tunables/global>

profile neo /home/usuario/WatermelonD/venv/bin/python3 {
#include <abstractions/base>
#include <abstractions/python>
#include <abstractions/audio>

# Network access
 network inet tcp,
 network inet udp,

# Read project files
 /home/usuario/WatermelonD/** r,
 
# Write logs and db
 /home/usuario/WatermelonD/logs/** rw,
 /home/usuario/WatermelonD/database/** rw,
 
# Deny execution of other binaries
 deny /bin/bash x,
 deny /usr/bin/curl x,
}
```

### 7.3. Protección contra Fuerza Bruta (Fail2Ban)
Si se expone SSH o la Web UI, configurar Fail2Ban.

**Jail para SSH (`/etc/fail2ban/jail.local`):**
```ini
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
```

### 7.4. Gestión de Secretos y Certificados SSL
* **Secretos:** No guardar tokens o claves API en `config.json`. Usar variables de entorno (`NEO_API_KEY=...`) y leerlas con `os.getenv()`.
* **SSL/TLS:** Generar certificados autofirmados para pruebas o usar Let's Encrypt para producción.

**Generar Certificado Autofirmado:**
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```
Configurar Flask para usar estos certificados (`ssl_context=('cert.pem', 'key.pem')`).

---

## 8. ANEXOS TÉCNICOS

### 8.1. Mapa de Memoria (Memory Footprint)
Estimación de consumo en reposo vs carga máxima.

| Componente | RAM (Idle) | RAM (Load) | Notas |
| :--- | :--- | :--- | :--- |
| Kernel + OS | 150 MB | 200 MB | Headless Debian (Minimizado) |
| WatermelonD (Python) | 80 MB | 120 MB | Base overhead del intérprete |
| Vosk Model | 120 MB | 150 MB | Modelo 'small' (es) |
| Gemma 2B (q4_k) | 0 MB | 1.8 GB | Carga bajo demanda (mmap) |
| ChromaDB | 50 MB | 200 MB | Base vectorial (depende de nº docs) |
| Mango T5 | 0 MB | 300 MB | Carga bajo demanda (PyTorch) |
| Whisper (Medium) | 0 MB | 1.5 GB | Si se usa en lugar de Vosk |
| **TOTAL (Min)** | **~350 MB** | **~2.3 GB** | Requiere Swap en RPi 2GB |

### 8.2. Códigos de Error y Debugging
> **Nota:** Los códigos de error y la guía de GDB se han movido al **[ANEXO IV: RESOLUCIÓN DE PROBLEMAS](ANEXO_IV_RESOLUCION_DE_PROBLEMAS.md)**.


---
**Fin del Documento Técnico**
