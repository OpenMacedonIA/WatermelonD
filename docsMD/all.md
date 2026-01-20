# Documentación Maestra: NEOPapaya Nano (TFG)

**Proyecto:** NEOPapaya Nano
**Versión:** 4.0 (Release Candidate TFG)
**Fecha:** Diciembre 2025
**Repositorio:** https://github.com/jrodriiguezg/NEOPapaya_nano

---

# Resumen Ejecutivo

**NEOPapaya Nano** es un asistente inteligente de código abierto diseñado para la **Soberanía Digital**. A diferencia de las soluciones comerciales que procesan datos en la nube, Nano ejecuta toda su pila tecnológica (Reconocimiento de Voz, Inteligencia Artificial, Síntesis de Voz y Automatización) localmente en el dispositivo (Edge Computing).

Este documento consolida toda la información técnica, guías de despliegue y referencia de desarrollo para el Trabajo de Fin de Grado.

---

# PARTE I: GUÍA DE DESPLIEGUE

Esta sección detalla cómo instalar y configurar el sistema desde cero.

## 1. Requisitos del Sistema

### Hardware
* **Plataforma**: Raspberry Pi 4 (4GB+), Orange Pi 5, o PC x86_64.
* **Almacenamiento**: Mínimo 16GB (32GB Recomendado para modelos LLM grandes).
* **Audio**: Micrófono USB (ReSpeaker 2-Mics HAT recomendado) y Altavoces.

### Software
* **OS**: Debian 11/12, Raspberry Pi OS (64-bit), Ubuntu 22.04+, Fedora 38+.
* **Python**: 3.10 (Gestionado automáticamente por `pyenv`).

## 2. Instalación Paso a Paso

### 2.1. Obtención del Código
```bash
cd ~
git clone https://github.com/jrodriiguezg/NEOPapaya_nano.git
cd NEOPapaya_nano
```

### 2.2. Ejecución del Script de Instalación
El script `install.sh` es el método recomendado. Realiza las siguientes tareas:
1. Instala dependencias de sistema (`apt` o `dnf`).
2. Configura `pyenv` y compila Python 3.10.
3. Crea un entorno virtual (`venv`).
4. Descarga modelos de IA (Vosk, Gemma, Piper).
5. Configura el servicio `systemd`.

```bash
chmod +x install.sh
./install.sh
```

**Nota**: La compilación de Python en una Raspberry Pi puede tardar 15-20 minutos.

### 2.3. Verificación Post-Instalación
Tras reiniciar, verifica que el servicio está corriendo:

```bash
systemctl --user status neo.service
```

Si está activo, deberías poder acceder a la interfaz web en `http://<IP>:5000`.

## 3. Configuración de Hardware

### 3.1. Audio
El archivo `config/config.json` define qué dispositivo de audio usar.
Si tienes problemas, usa `arecord -l` para encontrar el ID de tu tarjeta.

```json
"stt": {
 "input_device_index": 1, // Cambiar según arecord -l
 "engine": "vosk"
}
```

### 3.2. Bluetooth
Para usar el módulo Bluetooth, asegúrate de que el usuario tiene permisos:
```bash
sudo usermod -aG bluetooth $USER
```

---

# PARTE II: MANUAL TÉCNICO

Esta sección profundiza en la arquitectura y los módulos del sistema.

## 4. Arquitectura del Sistema

NEOPapaya Nano utiliza una arquitectura **Event-Driven** (basada en eventos).

### 4.1. WatermelonD (`WatermelonD.py`)
Es el orquestador central. No procesa la lógica de negocio directamente, sino que delega en "Managers" y coordina la comunicación entre ellos.

* **Bucle Principal**: Un `while True` que mantiene el proceso vivo y gestiona señales de parada.
* **Cola de Eventos**: Aunque Python tiene GIL, NEOPapaya usa colas (`queue.Queue`) para comunicar hilos de manera segura.

### 4.2. Módulos Principales

#### Voice Manager (`modules/voice_manager.py`)
Encargado de la audición.
* **Motores Soportados**:
 * **Vosk**: Rápido, offline, basado en Kaldi. Ideal para comandos fijos.
 * **Whisper**: Lento pero muy preciso. Ideal para dictado libre.
 * **Sherpa-ONNX**: Versión optimizada de Whisper para hardware muy limitado.
* **Gramática Dinámica**: Cuando se usa Vosk, el sistema inyecta una lista JSON de palabras permitidas al reconocedor. Esto reduce el espacio de búsqueda y elimina casi todos los falsos positivos.

#### Vision Manager (`modules/vision.py`)
Encargado de la visión.
* **Optimización**: Usa un pipeline en cascada para ahorrar CPU.
 1. **Detección de Movimiento**: Compara el frame actual con el anterior (resta de matrices). Coste computacional casi nulo.
 2. **Detección de Caras**: Solo si hay movimiento, ejecuta Haar Cascades.
 3. **Reconocimiento**: Solo si hay cara, ejecuta la red neuronal de `face_recognition`.

#### AI Engine (`modules/ai_engine.py`)
El cerebro generativo.
* **Modelo**: Google Gemma 2B (Instruction Tuned).
* **Formato**: GGUF (para inferencia en CPU con `llama.cpp`).
* **Contexto**: Mantiene un buffer de los últimos turnos de conversación para mantener la coherencia.

#### Intent Manager (`modules/intent_manager.py`)
El sistema de comprensión determinista.
* **Lógica**: Compara la entrada del usuario con una base de datos de "Triggers" (`intents.json`).
* **Fuzzy Matching**: Usa `RapidFuzz` para calcular la similitud (Levenshtein).
 * Score > 80: Coincidencia segura.
 * Score > 60: Coincidencia posible (requiere confirmación o contexto).

---

# PARTE III: PROFUNDIZACIÓN TÉCNICA (DEEP DIVE)

Esta sección analiza en detalle la implementación de los componentes más complejos.

## 5. Análisis del Motor de IA (AI Engine)

El archivo `modules/ai_engine.py` encapsula la complejidad de ejecutar un LLM localmente.

### 5.1. Carga del Modelo
El sistema busca modelos en el directorio `models/` con la siguiente prioridad:
1. Ruta personalizada en `config.json`.
2. `gemma-2b-tio.gguf` (Modelo Fine-Tuned para la personalidad de TIO).
3. `gemma-2-2b-it-Q4_K_M.gguf` (Modelo base cuantizado).

La carga se realiza con `llama_cpp.Llama`:
```python
self.llm = Llama(
 model_path=self.model_path,
 n_ctx=2048,# Ventana de contexto
 n_threads=3# Hilos de CPU dedicados
)
```

### 5.2. Generación de Respuesta
Se utilizan dos métodos:
* `generate_response`: Bloqueante. Espera a que termine toda la frase.
* `generate_response_stream`: Usa `yield` para devolver tokens a medida que se generan. Esto permite que la interfaz web muestre el texto "escribiéndose" en tiempo real, mejorando la percepción de latencia.

### 5.3. Prompt Engineering
Para que Gemma se comporte como "TIO", se inyecta un System Prompt invisible al usuario:
> "Eres TIO, un asistente técnico sarcástico pero útil. Responde de forma breve y técnica."

## 6. Análisis del Gestor de Intenciones (Intent Manager)

El archivo `modules/intent_manager.py` es crítico para la reactividad del sistema.

### 6.1. Algoritmo de Coincidencia
Se ha implementado un algoritmo de dos fases para equilibrar velocidad y precisión:

1. **Fase Rápida (Token Sort Ratio)**:
 * Ignora el orden de las palabras ("encender luz" == "luz encender").
 * Es muy rápido pero puede fallar con frases complejas.
 * Umbral: 80%.

2. **Fase Refinada (Partial Ratio + Penalización)**:
 * Si la fase 1 falla, se busca si la frase clave está *contenida* en el comando.
 * **Innovación**: Se aplica una penalización basada en la diferencia de longitud.
 * *Ejemplo*: Si el trigger es "IP" y el usuario dice "Dime cuál es tu dirección IP ahora mismo", el Partial Ratio daría 100%. Sin la penalización, esto podría activar comandos no deseados. La penalización reduce el score si el comando es mucho más largo que el trigger, a menos que sea muy específico.

```python
# Lógica de penalización
len_diff = abs(len(command_text) - len(p_trigger))
if len_diff > 5:
 length_penalty = 15
final_score = p_score - length_penalty
```

## 7. Análisis del Subsistema de Voz (Voice Manager)

El archivo `modules/voice_manager.py` maneja la complejidad del audio en tiempo real.

### 7.1. Detección de Wake Word
Para detectar "NEOPapaya" o "Tío" sin falsos positivos, se usa una estrategia híbrida:
1. **Match Exacto**: Si la transcripción contiene la palabra exacta.
2. **Fuzzy Match**: Si contiene una palabra fonéticamente similar (ej. "Leo" en vez de "NEOPapaya").
 * Se usa `RapidFuzz` para comparar cada palabra de la frase con la lista de Wake Words.

### 7.2. Gestión de Hilos de Audio
PyAudio es bloqueante. Para evitar congelar la interfaz:
* El bucle de escucha corre en un `threading.Thread` daemon.
* Se usa `exception_on_overflow=False` al leer del stream para evitar crashes si la CPU se satura momentáneamente.

---

# PARTE IV: GUÍA DE DESARROLLO

## 8. Creación de Nuevas Habilidades (Skills)

El sistema es extensible mediante la adición de nuevas entradas en `intents.json` y funciones en `WatermelonD.py`.

### Paso 1: Definir la Intención
Edita `config/intents.json`:
```json
{
 "name": "check_server_status",
 "triggers": ["estado del servidor", "cómo va el servidor"],
 "action": "action_check_server",
 "responses": ["Comprobando estado...", "Dame un segundo."]
}
```

### Paso 2: Implementar la Lógica
Edita `WatermelonD.py`:

```python
def action_check_server(self, response, **kwargs):
# 1. Ejecutar lógica (ej. ping)
 import subprocess
 res = subprocess.run(["ping", "-c", "1", "8.8.8.8"], capture_output=True)
 
# 2. Formatear respuesta
 if res.returncode == 0:
 final_text = "El servidor está online."
 else:
 final_text = "El servidor no responde."
 
# 3. Hablar
 self.speak(final_text)
```

### Paso 3: Registrar la Acción
En el método `execute_action` de `WatermelonD.py`:
```python
actions = {
# ...
 "action_check_server": self.action_check_server
}
```

## 9. API de Referencia

### 9.1. Estructura de Eventos (WebSocket)
El bus de mensajes usa JSON.

**Evento de Voz Detectada**:
```json
{
 "type": "voice_command",
 "text": "encender la luz",
 "wake_word": "neo"
}
```

**Evento de Respuesta (TTS)**:
```json
{
 "type": "speak",
 "text": "Luz encendida",
 "priority": "normal"
}
```

**Evento de Visión**:
```json
{
 "type": "vision_wake",
 "msg": "User present"
}
```

---

# PARTE V: REFERENCIA COMPLETA DE CONFIGURACIÓN

A continuación se detalla cada parámetro del archivo `config.json`.

```json
{
 // --- GENERAL ---
 "wake_words": ["neo", "tio", "bro"], // Palabras que activan la escucha
 "admin_user": "admin", // Usuario para la web
 "admin_pass": "admin", // Contraseña para la web
 "language": "es-ES", // Idioma del sistema

 // --- STT (Speech to Text) ---
 "stt": {
 "engine": "vosk", // Motor: "vosk", "whisper", "sherpa"
 "model_path": "vosk-models/es", // Ruta relativa al modelo
 "input_device_index": null, // null = default, int = ID específico
 "use_grammar": true, // true = Restringir vocabulario (Más rápido)
 "whisper_model": "medium", // Tamaño de modelo Whisper (si se usa)
 "sherpa_model_path": "models/sherpa" // Ruta para Sherpa-ONNX
 },

 // --- TTS (Text to Speech) ---
 "tts": {
 "engine": "piper", // Motor: "piper", "espeak", "gtts"
 "model_path": "piper/es_ES-davefx-medium.onnx", // Ruta al modelo ONNX
 "cache_dir": "tts_cache", // Directorio para guardar audios generados
 "volume": 1.0 // Volumen por software (0.0 - 1.0)
 },

 // --- RUTAS ---
 "paths": {
 "sounds": "resources/sounds", // Efectos de sonido (ding.wav)
 "logs": "logs", // Archivos de log
 "intents": "config/intents.json", // Definición de comandos
 "servers": "jsons/servers.json" // Base de datos de servidores SSH
 },

 // --- MÓDULOS ---
 "modules": {
 "vision": true, // Activar/Desactivar cámara
 "bluetooth": true, // Activar/Desactivar servidor BT
 "cast": true, // Activar/Desactivar Chromecast
 "ssh": true // Activar/Desactivar cliente SSH
 }
}
```

---

# PARTE VI: GLOSARIO TÉCNICO

* **ASR (Automatic Speech Recognition)**: Tecnología que convierte audio en texto. En este proyecto usamos Vosk y Whisper.
* **TTS (Text-to-Speech)**: Tecnología que convierte texto en audio sintético. Usamos Piper.
* **LLM (Large Language Model)**: Modelo de IA generativa entrenado con grandes cantidades de texto. Usamos Gemma 2B.
* **GGUF (GPT-Generated Unified Format)**: Formato de archivo binario para guardar modelos de IA optimizados para inferencia en CPU.
* **VAD (Voice Activity Detection)**: Algoritmo que detecta si hay voz humana en una señal de audio, ignorando el silencio y el ruido de fondo.
* **Wake Word**: Palabra clave que saca al asistente del modo de espera (ej. "NEOPapaya").
* **Intent (Intención)**: Lo que el usuario quiere hacer (ej. "encender_luz").
* **Slot / Entity**: Parámetros dentro de una intención (ej. "cocina" en "encender luz cocina").
* **Edge Computing**: Procesamiento de datos en el propio dispositivo, sin enviarlos a la nube.
* **RFCOMM**: Protocolo de transporte de puerto serie sobre Bluetooth.

---

# PARTE VII: SOLUCIÓN DE PROBLEMAS AVANZADA

## 10. Errores Comunes

### 10.1. "ALSA lib pcm.c:8526:(snd_pcm_recover) underrun occurred"
Este error es común en Raspberry Pi y significa que el procesador no pudo entregar datos de audio lo suficientemente rápido.
* **Solución**: Ignorable si es esporádico. Si es constante, aumenta el tamaño del buffer en `voice_manager.py` (`frames_per_buffer=8192`).

### 10.2. El modelo Gemma carga muy lento o crashea
* **Causa**: Falta de RAM.
* **Solución**: Asegúrate de tener al menos 2GB de RAM libres. Si usas RPi 4 de 2GB, activa ZRAM o aumenta la Swap.

### 10.3. Permisos de Micrófono
Si usas USB, a veces el dispositivo cambia de ID al reiniciar.
* **Solución**: Fija el dispositivo por nombre en `/etc/asound.conf` en lugar de por índice, o usa un script de inicio que detecte el índice dinámicamente.

### 10.4. Error "Address already in use" (Puerto 5000)
* **Causa**: Otra instancia de NEOPapaya o servicio está usando el puerto.
* **Solución**: `sudo lsof -i :5000` para ver quién es. Matar el proceso o cambiar el puerto en `web_admin.py`.

### 10.5. El servicio no arranca o "Unit neo.service could not be found"
* **Causa**: El archivo de servicio ha sido borrado o no está en la ruta correcta.
* **Solución**: Verificar `~/.config/systemd/user/neo.service`. Si no existe, recrearlo con los paths absolutos correctos y ejecutar `systemctl --user daemon-reload`.

### 10.6. Vosk carga muy lento o falla
* **Causa**: Modelo corrupto o falta de RAM.
* **Solución**: Verificar hash del modelo en `vosk-models/`. Asegurar al menos 500MB de RAM libre.

### 10.7. La cámara no se inicia
* **Causa**: Falta de permisos o cámara ocupada.
* **Solución**: Verificar que el usuario pertenece al grupo `video` (`sudo usermod -aG video $USER`). Probar con `ffplay /dev/video0`.

### 10.8. Bluetooth no conecta
* **Causa**: El servicio bluetoothd no está corriendo en modo compatibilidad.
* **Solución**: Editar `/etc/systemd/system/dbus-org.bluez.service` y añadir `-C` al `ExecStart`.

### 10.9. SSH Manager falla al conectar
* **Causa**: Clave no aceptada o host no alcanzable.
* **Solución**: Probar conexión manual `ssh user@host` para verificar huellas digitales y claves.

### 10.10. Piper TTS suena "robótico" o lento
* **Causa**: CPU sobrecargada.
* **Solución**: Cambiar a un modelo "low" quality o usar `espeak` como fallback.

---

# PARTE VIII: REFERENCIA DE CÓDIGO (API INTERNA)

Esta sección documenta las clases y métodos principales del código fuente para referencia de desarrolladores.

## 12. Módulo `WatermelonD` (`WatermelonD.py`)

La clase `WatermelonD` es el punto de entrada de la aplicación.

### `__init__(self)`
Constructor principal.
* Inicializa el sistema de logs.
* Carga la configuración desde `config.json`.
* Instancia todos los gestores (`VoiceManager`, `IntentManager`, `AIEngine`, etc.).
* Inicia los hilos en segundo plano llamando a `start_background_tasks()`.
* Entra en un bucle infinito (`while True`) para mantener el programa vivo.

### `start_background_tasks(self)`
Inicia los hilos daemon que ejecutan tareas concurrentes:
1. `voice_manager.start_listening()`: Hilo de escucha de voz.
2. `process_event_queue()`: Hilo consumidor de eventos.
3. `proactive_update_loop()`: Hilo de tareas periódicas (cron).
4. `run_server()`: Hilo del servidor web (Flask).

### `on_voice_command(self, command, wake_word)`
Callback invocado por `VoiceManager` cuando se detecta una frase completa.
* **Parámetros**:
 * `command`: Texto transcrito.
 * `wake_word`: Palabra de activación detectada (si la hubo).
* **Lógica**:
 1. Verifica si estamos en "Escucha Activa" o si se dijo el Wake Word.
 2. Si es válido, reproduce un sonido de "pensando" (`speaker.play_random_filler()`).
 3. Llama a `handle_command()` con el texto limpio.

### `handle_command(self, command_text)`
El cerebro de la toma de decisiones.
* **Lógica**:
 1. Verifica si hay diálogos activos (esperando respuesta a una pregunta).
 2. Verifica si es un comando directo (`KeywordRouter`).
 3. Verifica si es un alias aprendido (`Brain`).
 4. Busca la intención (`IntentManager`).
 5. Si hay intención clara -> Ejecuta acción (`execute_action`).
 6. Si es ambigua -> Pregunta al usuario.
 7. Si no hay intención -> Llama a `handle_unrecognized_command` (Gemma).

### `execute_action(self, name, cmd, params, resp, intent_name=None)`
Despachador de acciones. Mapea nombres de intención (strings) a funciones Python.
* Contiene un diccionario `action_map` gigante que vincula `check_system_status` -> `self.skills_system.check_status`.

### `process_event_queue(self)`
Consumidor de la cola de eventos.
* Procesa eventos tipo `speak` (TTS), `mqtt_alert` (Alertas), `vision_wake` (Saludo).
* Garantiza que las acciones se ejecuten secuencialmente para no solapar audio.

### `proactive_update_loop(self)`
Bucle de mantenimiento (1Hz).
* Verifica alarmas y temporizadores.
* Envía el resumen matutino a las 9:00 AM.
* Gestiona la expiración de la ventana de escucha activa.

## 13. Módulo `SysAdminManager` (`modules/sysadmin.py`)

Proporciona la interfaz con el sistema operativo Linux.

### `get_cpu_temp(self)`
Obtiene la temperatura de la CPU.
* Intenta usar `psutil.sensors_temperatures()`.
* Si falla (común en RPi), lee `/sys/class/thermal/thermal_zone0/temp`.

### `run_command(self, command, cwd=None)`
Ejecuta comandos de shell de forma segura.
* Usa `subprocess.run` con `timeout=10` para evitar bloqueos.
* Captura `stdout` y `stderr`.

### `control_service(self, service_name, action)`
Gestiona servicios systemd.
* Soporta `start`, `stop`, `restart`.
* Distingue entre servicios de usuario (`neo.service`) y de sistema (`nginx`).

### `get_network_info(self)`
Devuelve una lista de interfaces de red activas y sus IPs, filtrando `localhost`.

## 14. Módulo `VoiceManager` (`modules/voice_manager.py`)

Gestiona la entrada de audio y el reconocimiento de voz.

### `__init__(self, ...)`
Carga los modelos (Vosk/Whisper) según la configuración.

### `start_listening(self, intents=None)`
Inicia el hilo de escucha. Si se usa Vosk, compila la gramática dinámica basada en los `intents` pasados para optimizar la precisión.

### `_continuous_voice_listener(self, intents)`
El bucle principal de audio.
1. Abre un stream de `PyAudio` (16kHz, Mono).
2. Lee chunks de 4096 bytes.
3. Pasa los datos al reconocedor (`recognizer.AcceptWaveform(data)`).
4. Si hay resultado, invoca el callback `on_command_detected`.

### `_check_wake_word(self, text)`
Verifica si el texto contiene la palabra de activación.
* Usa `RapidFuzz` para permitir coincidencias aproximadas (ej. "Leo" en vez de "NEOPapaya").

## 15. Módulo `IntentManager` (`modules/intent_manager.py`)

Motor de Entendimiento de Lenguaje Natural (NLU).

### `find_best_intent(self, command_text)`
Busca la mejor coincidencia para un comando.
* Usa `rapidfuzz.process.extractOne` con `token_sort_ratio` para ignorar el orden de palabras.
* Si el score es bajo, intenta `partial_ratio` con penalización por longitud.
* Devuelve un objeto `intent` con un campo `confidence` ('high' o 'low').

## 16. Módulo `AIEngine` (`modules/ai_engine.py`)

Wrapper para `llama-cpp-python`.

### `generate_response_stream(self, prompt)`
Generador Python que produce texto token a token.
* Permite que la interfaz web muestre el texto progresivamente.
* Maneja el contexto de la conversación inyectando el historial reciente.

---

# PARTE IX: HOJA DE RUTA (ROADMAP)

El desarrollo de NEOPapaya Nano continúa. Estas son las características planeadas para la versión 5.0.

## 1. Soporte Multi-Idioma
* Implementación de `gettext` para internacionalización (i18n).
* Carga dinámica de modelos de voz según el idioma configurado.

## 2. Integración con Home Assistant
* Nuevo módulo `HassManager` para controlar dispositivos IoT vía API WebSocket de Home Assistant.
* Mapeo automático de entidades (luces, interruptores) a comandos de voz.

## 3. Visión Avanzada
* Reconocimiento de objetos (YOLOv8 Nano).
* Control por gestos (MediaPipe Hand Tracking).

## 4. Agentes Distribuidos (Swarm)
* Mejora del protocolo Bluetooth para permitir una red en malla de satélites Nano que comparten un mismo "Cerebro" central.

---

# PARTE X: GUÍA DE CONTRIBUCIÓN

¡Gracias por tu interés en contribuir a NEOPapaya Nano!

## 1. Reportar Bugs
Por favor, usa la pestaña de Issues en GitHub. Incluye:
* Logs completos (`logs/app.log`).
* Descripción del hardware (modelo de Raspberry Pi, micrófono).
* Pasos para reproducir el error.

## 2. Pull Requests
1. Haz un Fork del repositorio.
2. Crea una rama para tu feature (`git checkout -b feature/nueva-cosa`).
3. Asegúrate de seguir el estilo de código PEP-8.
4. Documenta tus cambios en `docs/changelog.md`.

---

# PARTE XI: LICENCIA

Este proyecto se distribuye bajo la licencia **MIT**.

```text
MIT License

Copyright (c) 2025 NEOPapaya Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

# Anexo: Estructura del Proyecto

```
NEOPapaya_nano/
├── config/# Configuración JSON
├── database/# SQLite (BrainNut.db)
├── docs/# Documentación
├── logs/# Archivos de registro
├── models/# Modelos GGUF (Gemma)
├── modules/# Código fuente modular
│ ├── ai_engine.py# Integración LLM
│ ├── bluetooth_manager.py
│ ├── BrainNut.py# Gestión de DB
│ ├── cast_manager.py# Chromecast
│ ├── file_manager.py# Sistema de archivos
│ ├── intent_manager.py# NLU
│ ├── ssh_manager.py# Cliente SSH
│ ├── vision.py# Computer Vision
│ ├── voice_manager.py# STT (Vosk/Whisper)
│ └── web_admin.py# Servidor Flask
├── resources/# Herramientas y scripts
├── vosk-models/# Modelos de voz
├── install.sh# Script de instalación
├── WatermelonD.py# Punto de entrada
└── requirements.txt# Dependencias Python
```

---
**Fin de la Documentación**
