# Manual Técnico Integral: WatermelonD Nano (TFG Edition)

**Versión del Documento:** 4.0 (Final TFG)
**Fecha:** Diciembre 2025
**Proyecto:** WatermelonD Nano - Asistente Inteligente Offline
**Autor:** [Tu Nombre / Usuario]

---

## Índice de Contenidos

1. [Introducción y Alcance](#1-introducción-y-alcance)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
 * [Diagrama de Componentes](#21-diagrama-de-componentes)
 * [Flujo de Datos](#22-flujo-de-datos)
3. [Núcleo del Sistema (WatermelonD)](#3-núcleo-del-sistema-WatermelonD)
 * [Ciclo de Vida](#31-ciclo-de-vida)
 * [Gestión de Eventos](#32-gestión-de-eventos)
4. [Módulos de Percepción](#4-módulos-de-percepción)
 * [Voice Manager (Oído)](#41-voice-manager-oído)
 * [Vision Manager (Ojos)](#42-vision-manager-ojos)
5. [Módulos de Acción e Interacción](#5-módulos-de-acción-e-interacción)
 * [Speaker (Habla)](#51-speaker-habla)
 * [Cast Manager (Multimedia)](#52-cast-manager-multimedia)
 * [Bluetooth Manager (Conectividad)](#53-bluetooth-manager-conectividad)
6. [Herramientas de Administración (SysAdmin)](#6-herramientas-de-administración-sysadmin)
 * [SSH Manager](#61-ssh-manager)
 * [File Manager](#62-file-manager)
 * [Terminal Web](#63-terminal-web)
7. [Inteligencia y Memoria](#7-inteligencia-y-memoria)
 * [BrainNut (Base de Datos)](#71-BrainNut-base-de-datos)
 * [Intent Manager (NLU)](#72-intent-manager-nlu)
 * [AI Engine (LLM)](#73-ai-engine-llm)
8. [Referencia de Configuración](#8-referencia-de-configuración)
9. [API y Desarrollo](#9-api-y-desarrollo)
10. [Solución de Problemas (Troubleshooting)](#10-solución-de-problemas-troubleshooting)
11. [Anexos](#11-anexos)

---

## 1. Introducción y Alcance

**WatermelonD Nano** es un asistente virtual de código abierto diseñado para operar en entornos locales (Edge Computing) sin dependencia de la nube. Su objetivo principal es proporcionar una interfaz natural (voz y visión) para la gestión de sistemas domésticos y servidores, priorizando la privacidad y la baja latencia.

Este proyecto se diferencia de asistentes comerciales (Alexa, Google Assistant) por su capacidad de **ejecución 100% offline**, su enfoque en tareas de **administración de sistemas (SysAdmin)** y su arquitectura modular extensible.

---

## 2. Arquitectura del Sistema

El sistema sigue una arquitectura modular centrada en eventos, orquestada por un núcleo central (`WatermelonD`).

### 2.1. Diagrama de Componentes

```mermaid
graph TD
 User((Usuario)) <--> Mic[Micrófono]
 User <--> Cam[Cámara]
 User <--> Web[Interfaz Web]
 
 subgraph "WatermelonD Nano"
 Mic --> VM[Voice Manager]
 Cam --> Vis[Vision Manager]
 
 VM --> Core{WatermelonD}
 Vis --> Core
 Web --> Core
 
 Core --> IM[Intent Manager]
 Core --> AI[AI Engine (Gemma)]
 Core --> BrainNut[(BrainNut DB)]
 
 Core --> SM[Speaker]
 Core --> Sys[SysAdmin]
 Core --> BT[Bluetooth Mgr]
 Core --> Cast[Cast Mgr]
 Core --> SSH[SSH Mgr]
 Core --> File[File Mgr]
 end
 
 SM --> Spk[Altavoces]
 Sys --> OS[Sistema Operativo]
 BT --> Devices[Dispositivos BT]
 SSH --> Remote[Servidores Remotos]
```

### 2.2. Flujo de Datos

1. **Entrada**: El usuario emite un comando de voz o aparece frente a la cámara.
2. **Procesamiento**:
 * `VoiceManager` transcribe el audio a texto (STT).
 * `VisionManager` detecta presencia o identifica al usuario.
3. **Decisión**:
 * `WatermelonD` recibe el evento.
 * Consulta a `IntentManager` para ver si es un comando conocido.
 * Si no, deriva a `AI Engine` para una respuesta generativa.
4. **Ejecución**: Se invoca el módulo correspondiente (ej. `SSHManager` para conectar a un servidor).
5. **Respuesta**: `Speaker` sintetiza la respuesta vocal (TTS) y/o se actualiza la UI Web.

---

## 3. Núcleo del Sistema (WatermelonD)

Ubicación: `WatermelonD.py`

Es el punto de entrada (`__main__`) y el orquestador. Inicializa todos los subsistemas y mantiene el bucle principal de la aplicación.

### 3.1. Ciclo de Vida
1. **Boot**: Carga configuración, inicializa logs y conecta a la base de datos.
2. **Init Modules**: Instancia los managers (Voice, Vision, Bluetooth, etc.) en hilos separados.
3. **Event Loop**: Entra en un bucle infinito esperando señales de interrupción o eventos críticos.
4. **Shutdown**: Cierra conexiones y termina hilos ordenadamente al recibir `SIGINT`.

### 3.2. Gestión de Eventos
WatermelonD expone métodos de callback que los módulos llaman:
* `on_voice_command(text)`: Invocado cuando se detecta una frase completa.
* `on_vision_event(type, data)`: Invocado al detectar movimiento o caras.

---

## 4. Módulos de Percepción

### 4.1. Voice Manager (Oído)
Ubicación: `modules/voice_manager.py`

Responsable de convertir audio en texto. Soporta múltiples motores:
* **Vosk**: Motor principal offline. Usa modelos de Kaldi.
 * *Optimización*: Implementa "Gramática Dinámica" para restringir el vocabulario a los comandos conocidos, mejorando drásticamente la precisión.
* **Faster-Whisper**: Motor secundario basado en Transformer. Más preciso pero más pesado.
* **Sherpa-ONNX**: Implementación ultraligera de Whisper para dispositivos muy limitados.

**Características Clave**:
* **Wake Word Fuzzy**: Usa `RapidFuzz` para detectar la palabra de activación ("WatermelonD", "Tío") incluso con ruido o mala pronunciación.
* **VAD (Voice Activity Detection)**: Detecta silencio para cortar la grabación automáticamente.

### 4.2. Vision Manager (Ojos)
Ubicación: `modules/vision.py`

Sistema de visión computacional eficiente.
* **Pipeline de 3 Etapas**:
 1. **Detección de Movimiento**: Diferencia de frames (muy bajo consumo). Si no hay movimiento, no hace nada más.
 2. **Detección Facial**: Haar Cascades (rápido). Si hay movimiento, busca caras.
 3. **Reconocimiento**: (Opcional) `face_recognition` (dlib) para identificar quién es.
* **Wake-up Visual**: Si el sistema está en reposo y detecta una cara, se "despierta" (activa la UI y saluda).

---

## 5. Módulos de Acción e Interacción

### 5.1. Speaker (Habla)
Ubicación: `modules/speaker.py`

Gestor de Text-to-Speech (TTS).
* **Motor**: Piper TTS (Neural, Offline). Calidad casi humana con baja latencia.
* **Caché**: Almacena frases comunes en disco (MD5 hash) para respuesta instantánea.
* **Prioridad**: Puede interrumpir el audio actual si llega un mensaje de alerta.

### 5.2. Cast Manager (Multimedia)
Ubicación: `modules/cast_manager.py`

Controlador para dispositivos Google Cast (Chromecast, Google Home).
* **Descubrimiento**: Escanea la red local (mDNS) buscando dispositivos compatibles.
* **Funciones**: Play, Stop, Volumen.
* **Uso**: "Pon el vídeo X en la tele del salón".

### 5.3. Bluetooth Manager (Conectividad)
Ubicación: `modules/bluetooth_manager.py`

Servidor RFCOMM para comunicación directa sin Wi-Fi.
* **Rol**: Actúa como servidor, esperando conexiones de agentes satélite o apps móviles.
* **Protocolo**: JSON sobre RFCOMM.
* **Fallback**: Permite recibir alertas críticas o telemetría incluso si la red principal cae.

---

## 6. Herramientas de Administración (SysAdmin)

### 6.1. SSH Manager
Ubicación: `modules/ssh_manager.py`

Cliente SSH integrado para gestión remota.
* **Gestión de Perfiles**: Guarda hosts, usuarios y claves en `servers.json`.
* **Persistencia**: Mantiene conexiones vivas (`paramiko`) para ejecución rápida de comandos secuenciales.
* **Seguridad**: Permite uso de claves SSH para no almacenar contraseñas.

### 6.2. File Manager
Ubicación: `modules/file_manager.py`

Explorador de archivos backend.
* **Funciones**: Listar directorios, leer archivos (con límite de tamaño), guardar cambios.
* **Búsqueda**: Integra el comando `find` del sistema para búsquedas rápidas por nombre.
* **API**: Expone estas funciones a la interfaz web y al control por voz ("Busca el archivo error.log").

### 6.3. Terminal Web
Ubicación: `modules/web_admin.py` (Frontend en JS)

Emulador de terminal en el navegador.
* **Funcionamiento**: Envía comandos vía AJAX al backend, que los ejecuta con `subprocess` manteniendo el estado del directorio actual (`cwd`) en la sesión del usuario.

---

## 7. Inteligencia y Memoria

### 7.1. BrainNut (Base de Datos)
Ubicación: `modules/BrainNut.py` / `database/`

Memoria persistente basada en SQLite.
* **Tablas**:
 * `memory`: Hechos aprendidos ("El servidor X es 192.168.1.5").
 * `aliases`: Comandos personalizados enseñados por el usuario.
 * `history`: Registro de interacciones.

### 7.2. Intent Manager (NLU)
Ubicación: `modules/intent_manager.py`

Motor de comprensión de lenguaje natural.
* **Matching**: Compara la frase del usuario con una lista de `triggers` definidos en `intents.json`.
* **Algoritmo**: RapidFuzz (Levenshtein distance) para permitir variaciones naturales en el habla.

### 7.3. AI Engine (LLM)
Ubicación: `modules/ai_engine.py`

Cerebro generativo de respaldo.
* **Modelo**: Google Gemma 2B (formato GGUF).
* **Motor de Inferencia**: `llama.cpp` (vía `llama-cpp-python`).
* **Función**: Si `IntentManager` no reconoce el comando, se envía a Gemma. Gemma tiene un "System Prompt" que le da la personalidad de T.I.O. (Tecnico Informático Operativo) y acceso al contexto de la conversación.

---

## 8. Referencia de Configuración

El archivo `config/config.json` controla el comportamiento del sistema.

| Sección | Clave | Tipo | Descripción |
| :--- | :--- | :--- | :--- |
| **General** | `wake_words` | Lista | Palabras que activan el asistente (ej. "WatermelonD", "Tío"). |
| | `admin_user` | String | Usuario para la interfaz web. |
| | `admin_pass` | String | Contraseña para la interfaz web. |
| **STT** | `engine` | String | Motor de voz: "vosk", "whisper", "sherpa". |
| | `model_path` | Path | Ruta al modelo de Vosk. |
| | `input_device_index` | Int | Índice del micrófono (ver `arecord -l`). |
| | `use_grammar` | Bool | Activar gramática dinámica (mejora precisión, limita vocabulario). |
| **TTS** | `engine` | String | Motor de síntesis: "piper", "espeak", "gtts". |
| | `model_path` | Path | Ruta al modelo de voz de Piper (.onnx). |
| **Paths** | `sounds` | Path | Directorio de efectos de sonido. |
| | `logs` | Path | Directorio de logs. |

### Ejemplo de `config.json`

```json
{
 "wake_words": ["neo", "computadora"],
 "stt": {
 "engine": "vosk",
 "model_path": "vosk-models/es",
 "input_device_index": 1,
 "use_grammar": true
 },
 "tts": {
 "engine": "piper",
 "model_path": "piper/es_ES-davefx-medium.onnx"
 }
}
```

---

## 9. API y Desarrollo

### 9.1. API REST (Web Admin)

La interfaz web se comunica con el backend mediante endpoints JSON.

#### `GET /api/stats`
Devuelve el estado actual del hardware.
* **Respuesta**:
 ```json
 {
 "cpu": 15.2,
 "ram": 45.8,
 "temp": "42.0°C",
 "disk": "12GB / 32GB"
 }
 ```

#### `POST /api/terminal`
Ejecuta un comando en la terminal virtual.
* **Body**: `{"command": "ls -la"}`
* **Respuesta**:
 ```json
 {
 "success": true,
 "output": "total 40\ndrwxr-xr-x 2 pi pi 4096...",
 "cwd": "/home/pi/WatermelonD_nano"
 }
 ```

#### `POST /api/ssh/connect`
Inicia una conexión SSH persistente.
* **Body**: `{"alias": "servidor_web"}`
* **Respuesta**: `{"success": true, "msg": "Conectado a 192.168.1.10"}`

### 9.2. Protocolo Bluetooth (RFCOMM)

Los agentes satélite envían JSONs terminados en `\n`.

* **Formato**:
 ```json
 {
 "agent": "Sensor_Salon",
 "type": "telemetry",
 "data": {
 "temperature": 22.5,
 "humidity": 60
 }
 }
 ```

### 9.3. Creación de Skills

Para añadir una nueva habilidad, edita `jsons/intents.json`:

```json
{
 "name": "mi_skill",
 "triggers": ["activa mi skill", "ejecuta prueba"],
 "action": "run_my_skill",
 "responses": ["Ejecutando skill de prueba..."]
}
```

Luego, en `WatermelonD.py`, registra la función en el mapa de acciones:

```python
# En WatermelonD.execute_action
actions = {
# ...
 "run_my_skill": self.action_run_my_skill
}

def action_run_my_skill(self, response, **kwargs):
# Tu lógica aquí
 self.speak(response)
```

---

## 10. Solución de Problemas (Troubleshooting)

### 10.1. Problemas de Audio

**Síntoma**: "Error opening stream" en los logs.
**Causa**: PyAudio no encuentra el dispositivo de entrada o está ocupado.
**Solución**:
1. Cierra otras apps que usen el micro.
2. Ejecuta `arecord -L` y busca el dispositivo `plughw`.
3. Actualiza `input_device_index` en `config.json`.

**Síntoma**: El asistente no responde al Wake Word.
**Causa**: Nivel de micrófono bajo o ruido ambiental.
**Solución**:
1. Ajusta la ganancia con `alsamixer`.
2. Verifica que el modelo Vosk está cargado correctamente en los logs.

### 10.2. Problemas de Rendimiento

**Síntoma**: Respuesta muy lenta (>5 segundos).
**Causa**: Uso de CPU al 100%.
**Solución**:
1. Si usas Raspberry Pi 3, cambia el modelo STT a "vosk-small".
2. Desactiva la visión (`VisionManager`) si no tienes cámara o consume mucho.
3. Asegúrate de que no hay procesos de compilación en segundo plano.

### 10.3. Problemas de Red/Bluetooth

**Síntoma**: "Bluetooth not supported".
**Causa**: Falta `libbluetooth-dev` o el usuario no está en el grupo `bluetooth`.
**Solución**:
1. `sudo apt install libbluetooth-dev`
2. `sudo usermod -aG bluetooth $USER`

---

## 11. Anexos

### Anexo A: Lista de Dependencias (Python)

* `vosk`: Reconocimiento de voz offline.
* `sounddevice` / `pyaudio`: Captura y reproducción de audio.
* `opencv-python`: Visión artificial.
* `face_recognition`: Identificación facial (dlib).
* `flask`: Servidor web y API.
* `paramiko`: Cliente SSH.
* `pychromecast`: Control de Google Cast.
* `psutil`: Monitorización del sistema.
* `llama-cpp-python`: Inferencia de LLMs (Gemma).

### Anexo B: Estructura de Archivos

```
/home/pi/WatermelonD_nano/
├── WatermelonD.py# Main
├── install.sh# Instalador
├── config/
│ ├── config.json
│ └── faces.json# DB de caras
├── modules/
│ ├── voice_manager.py
│ ├── vision.py
│ ├── bluetooth_manager.py
│ └── ...
├── models/# Modelos IA (Gemma, Whisper)
├── vosk-models/# Modelos Vosk
└── web/# Frontend
 ├── templates/
 └── static/
```

---
**Fin del Documento**
