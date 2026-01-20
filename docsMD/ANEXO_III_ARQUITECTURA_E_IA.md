# ANEXO III: ARQUITECTURA INTERNA E INTELIGENCIA ARTIFICIAL

**Proyecto:** WatermelonD (Language Copilot for Group and Administration Environments) 
**Versión del Documento:** 1.9 (Versión Completa Definitiva) 
**Fecha:** 03/12/2025 
**Estado:** Release Candidate 
**Nivel de Acceso:** Ingeniería de IA / Desarrollo Core / I+D

---

## ÍNDICE DE CONTENIDOS

1. [INTRODUCCIÓN A LA COGNICIÓN ARTIFICIAL](#1-introducción-a-la-cognición-artificial)
 1.1. Filosofía de Diseño: Híbrido Determinista-Generativo
 1.2. El Bucle Cognitivo (Percepción-Acción)
 1.3. Principios de Diseño Ético y de Seguridad
 1.4. Modelo T5 "Seq2Seq" (MANGO) para Traducción de Comandos
2. [ARQUITECTURA COGNITIVA](#2-arquitectura-cognitiva)
 2.1. Diagrama de Bloques Funcionales
 2.2. Pipeline de Procesamiento de Señales
 2.3. Máquina de Estados Emocional (Implementación FSM)
 2.4. Gestión de Prioridades y Atención
3. [COMPRENSIÓN DEL LENGUAJE NATURAL (NLU)](#3-comprensión-del-lenguaje-natural-nlu)
 3.1. Enfoque Híbrido: Fuzzy Logic vs Neural Networks
 3.2. Algoritmo de Clasificación de Intenciones (RapidFuzz)
 3.3. Redes Neuronales Superficiales (FANN/Padatious)
 3.4. Extracción de Entidades (NER)
 3.5. Teoría Matemática de la Distancia de Edición
4. [EL "CEREBRO" (SISTEMAS DE MEMORIA)](#4-el-cerebro-sistemas-de-memoria)
 4.1. Memoria a Corto Plazo (Context Window)
 4.2. Memoria a Largo Plazo (Persistencia SQLite)
 4.3. Esquema de Base de Datos (SQL Reference)
 4.4. Aprendizaje Adaptativo (Alias y Preferencias)
 4.5. Estructura de Embeddings Vectoriales (Futuro)
5. [INTELIGENCIA GENERATIVA (LLM)](#5-inteligencia-generativa-llm)
 5.1. Integración de Llama.cpp
 5.2. Ingeniería de Prompts Avanzada (CoT, ReAct)
 5.3. Estrategias de Muestreo (Sampling)
 5.4. Optimización de Inferencia (KV Cache & Batching)
 5.5. Ajuste Fino (Fine-Tuning) y LoRA
6. [PROCESAMIENTO DE SEÑALES (LOS SENTIDOS)](#6-procesamiento-de-señales-los-sentidos)
 6.1. Pipeline de Audio: VAD y Normalización
 6.2. Teoría de Procesamiento de Audio (FFT y MFCCs)
 6.3. Pipeline de Visión (Face UI y Computer Vision)
 6.4. Fusión Sensorial
7. [COGNICIÓN MULTI-AGENTE (SWARM INTELLIGENCE)](#7-cognición-multi-agente-swarm-intelligence)
 7.1. Protocolo de Consenso
 7.2. Resolución de Conflictos
 7.3. Aprendizaje Federado (Concepto)
 12.2. Bloque `voice`
 12.3. Bloque `intents`
13. [CONSIDERACIONES ÉTICAS Y DE SEGURIDAD](#13-consideraciones-éticas-y-de-seguridad)
 13.1. Sesgo Algorítmico
 13.2. Alucinaciones y Veracidad
 13.3. Protección contra Inyecciones de Prompt
14. [HOJA DE RUTA (ROADMAP) DE IA](#14-hoja-de-ruta-roadmap-de-ia)
 14.1. Multimodalidad
 14.2. RAG (Retrieval-Augmented Generation)
15. [ANEXOS DE IA](#15-anexos-de-ia)

---

## 1. INTRODUCCIÓN A LA COGNICIÓN ARTIFICIAL

### 1.1. Filosofía de Diseño: Híbrido Determinista-Generativo
WatermelonD representa un cambio de paradigma respecto a los asistentes virtuales tradicionales. No es un simple chatbot basado en reglas ni una "caja negra" puramente generativa. Su arquitectura implementa un enfoque **híbrido** que combina la precisión quirúrgica de los sistemas deterministas con la flexibilidad creativa de los Modelos de Lenguaje Grande (LLM).

* **Capa Determinista (Fast System - Sistema 1):** Responsable de acciones críticas, comandos de sistema y respuestas inmediatas. Prioriza la velocidad, la seguridad y la exactitud. Si el usuario dice "Apagar sistema", el sistema *debe* obedecer inmediatamente, sin "alucinar" una respuesta filosófica o dudar. Esta capa opera en el orden de los milisegundos (<50ms).
* **Capa Generativa (Slow System - Sistema 2):** Responsable de la interacción social, el razonamiento complejo, la síntesis de información y el manejo de consultas no estructuradas. Utiliza modelos cuantizados como Gemma-2B o Llama-3-8B para generar respuestas creativas y contextuales. Esta capa opera en el orden de los segundos (1-5s).

### 1.2. El Bucle Cognitivo (Percepción-Acción)
El sistema opera en un ciclo continuo inspirado en el bucle OODA (Observe, Orient, Decide, Act), adaptado para la latencia y los recursos de un sistema embebido:

1. **Percibir (Sensing):** Captura de datos crudos del entorno.
 * Audio PCM (Micrófono).
 * Video Frames (Cámara, si activa).
 * Telemetría de Red (MQTT).
 * Estado del Sistema (CPU, RAM, Temperatura).
2. **Procesar (Processing):** Transformación de datos crudos en información útil.
 * VAD (Voice Activity Detection) para aislar voz del ruido.
 * STT (Speech-to-Text) para transcribir fonemas a grafemas.
 * Normalización de texto (lowercase, eliminación de tildes).
3. **Comprender (Understanding):** Extracción de significado.
 * Clasificación de Intención (NLU).
 * Extracción de Entidades (NER).
 * Análisis de Sentimiento.
4. **Decidir (Decision Making):** Selección de la mejor acción.
 * ¿Es un comando conocido con alta confianza? (Sí -> Ejecutar Skill).
 * ¿Es una pregunta ambigua? (Sí -> Pedir aclaración).
 * ¿Es una conversación general? (Sí -> Consultar LLM).
5. **Actuar (Actuation):** Ejecución física o digital.
 * Ejecución de script Python.
 * Generación de respuesta de voz (TTS).
 * Cambio de expresión facial (UI).
 * Envío de comando IoT (MQTT).
6. **Aprender (Learning):** Retroalimentación del usuario (opcional).
 * Corrección de alias.
 * Ajuste de preferencias.

### 1.3. Principios de Diseño Ético y de Seguridad
Dado que el sistema tiene capacidades de administración (SSH, ejecución de comandos), la arquitectura cognitiva incorpora "guardarraíles" (guardrails):
* **Principio de Mínima Sorpresa:** El sistema siempre debe confirmar acciones destructivas.
* **Transparencia:** Si el sistema no sabe algo, debe admitirlo en lugar de inventar (alucinación reducida vía System Prompt).
* **Privacidad por Diseño:** El procesamiento de voz y texto es 100% local. No se envían datos a la nube para inferencia.

---

## 2. ARQUITECTURA COGNITIVA

### 2.1. Diagrama de Bloques Funcionales

```mermaid
graph TD
 subgraph "Percepción"
 Input[Entrada Sensorial] -->|Audio/Texto| Preproc[Pre-procesamiento]
 Preproc -->|Texto Normalizado| Router[Router Cognitivo]
 end
 
 subgraph "Razonamiento"
 Router -->|Alta Confianza| IntentEngine[Motor de Intenciones]
 Router -->|Baja Confianza| LLMEngine[Motor Generativo (LLM)]
 
 IntentEngine -->|Match| SkillExec[Ejecutor de Skills]
 LLMEngine -->|Prompt| Context[Gestor de Contexto]
 Context -->|History + Prompt| Inference[Inferencia Local]
 end
 
 subgraph "Acción"
 SkillExec -->|Resultado| ResponseGen[Generador de Respuesta]
 Inference -->|Texto| ResponseGen
 
 ResponseGen -->|Texto Final| TTS[Síntesis de Voz]
 ResponseGen -->|Estado| FaceUI[Interfaz Emocional]
 end
```

### 2.2. Pipeline de Procesamiento de Señales
El flujo de datos no es lineal; es asíncrono y basado en eventos para maximizar la reactividad.

* **Hilo de Escucha (Listener Thread):** Dedicado exclusivamente a capturar audio y detectar voz (VAD). Mantiene un buffer circular para no perder el inicio de la frase mientras el sistema "despierta".
* **Hilo de Pensamiento (Thinking Thread):** Procesa la lógica pesada (LLM/Skills).
* **Barge-in (Interrupción):** El sistema está diseñado para permitir que el usuario interrumpa al asistente mientras habla. Si el VAD detecta voz durante el estado `SPEAKING`, el sistema detiene inmediatamente el TTS y pasa a `LISTENING`.

### 2.3. Máquina de Estados Emocional (Implementación FSM)
La "personalidad" del asistente se modela mediante una máquina de estados finitos (FSM).

**Lógica de Transición (Pseudocódigo):**
```python
class EmotionalState(Enum):
 IDLE = 0
 LISTENING = 1
 THINKING = 2
 SPEAKING = 3
 CONFUSED = 4
 ERROR = 5

def update_state(event):
 if current_state == IDLE and event == WAKE_WORD:
 transition_to(LISTENING)
 elif current_state == LISTENING and event == SILENCE_DETECTED:
 transition_to(THINKING)
 elif current_state == THINKING and event == RESPONSE_READY:
 transition_to(SPEAKING)
 elif current_state == SPEAKING and event == TTS_FINISHED:
 transition_to(IDLE)
```

| Estado | Comportamiento Visual | Significado |
| :--- | :--- | :--- |
| **IDLE** | Parpadeo aleatorio, movimiento ocular suave (Saccades). | Sistema listo. |
| **LISTENING** | Ojos abiertos, pupilas dilatadas. | Capturando audio. |
| **THINKING** | Animación de carga (spinner). | Procesando. |
| **SPEAKING** | Lip-sync básico. | Comunicando respuesta. |
| **CONFUSED** | Ojos asimétricos, ceja levantada. | No entendió. |
| **ERROR** | Ojos en "X", color rojo. | Fallo crítico. |

### 2.4. Gestión de Prioridades y Atención
El sistema implementa un mecanismo de atención básico:
1. **Foco Principal:** La interacción de voz actual.
2. **Interrupciones:** Alertas críticas de sistema (ej. "Temperatura CPU Crítica") pueden interrumpir cualquier estado.
3. **Timeout:** Si el sistema espera input y no lo recibe en N segundos, vuelve a `IDLE`.

---

## 3. COMPRENSIÓN DEL LENGUAJE NATURAL (NLU)

### 3.1. Enfoque Híbrido: Fuzzy Logic vs Neural Networks
WatermelonD utiliza dos mecanismos paralelos y complementarios.

1. **RapidFuzz (Lógica Difusa):**
 * **Uso:** Comandos de sistema, control de hardware.
 * **Mecánica:** Distancia de Levenshtein.
 * **Ventaja:** Rápido (<5ms), determinista.
 * **Desventaja:** Poca generalización semántica.

2. **Padatious (Redes Neuronales):**
 * **Uso:** Comandos complejos, frases naturales.
 * **Mecánica:** Redes neuronales superficiales (FANN).
 * **Ventaja:** Generaliza variaciones gramaticales.
 * **Desventaja:** Requiere reentrenamiento.

### 3.2. Algoritmo de Clasificación de Intenciones (RapidFuzz)
El `IntentManager` implementa un algoritmo de puntuación ponderada:

1. **Token Sort Ratio:** Compara las palabras sin importar el orden.
2. **Partial Ratio:** Busca si la frase clave está contenida en la entrada.
3. **Penalización por Longitud:** `Penalty = abs(len(input) - len(trigger)) * Factor`.
4. **Score Final:** `Score = BaseScore - Penalty`.

### 3.3. Redes Neuronales Superficiales (FANN/Padatious)
Padatious utiliza la librería FANN (Fast Artificial Neural Network).
* **Arquitectura:** Perceptrón Multicapa (MLP).
* **Input:** Bag of Words (BoW) o n-gramas de la frase de entrada.
* **Hidden Layers:** Generalmente 1 capa oculta pequeña (16-32 neuronas).
* **Output:** Probabilidad para cada Intent registrado.
* **Entrenamiento:** Backpropagation rápido. Al ser una red pequeña, se entrena en segundos en la CPU.

### 3.4. Motor de Traducción de Comandos (MANGO T5)
Para comandos complejos del sistema que requieren una traducción precisa a Bash (ej. Docker, Systemd), se utiliza un modelo **Encoder-Decoder (T5)** ajustado (Fine-Tuned) en modo avanzado.

* **Rol Primario (SysAdmin Engine):** A partir de v2.5, MANGO tiene prioridad sobre el sistema de intents para operaciones técnicas. Se ejecuta *antes* que las reglas heredadas.
* **Prompt Injection (Context Aware):** El sistema inyecta dinámicamente el estado del entorno en el prompt antes de la inferencia:
 > *"Working Directory: /home/pi. User: root. Date: 2024-12-24. IP: 192.168.1.50. Task: [Input Usuario]"*
* **Self-Correction Loop (Reflexión):** Mecanismo de auto-reparación. Si un comando generado falla (Exit Code != 0), el sistema captura el `stderr` y re-invoca a MANGO con un prompt de reparación:
 > *"Previous command failed with error: [Error]. Fix it for task: [Task]"*
* **Seguridad:** Ejecución directa para comandos de lectura (`ls`, `find`, `cat`) y solicitud de confirmación obligatoria para escritura/root.

### 3.5. Extracción de Entidades (NER)
* **Método Difuso:** Extracción basada en reglas y placeholders (`{param}`).
* **Método Neuronal:** La red identifica los *slots* definidos en el entrenamiento.

### 3.6. Teoría Matemática de la Distancia de Edición
La base de RapidFuzz es la distancia de Levenshtein.
Sea $a$ y $b$ dos cadenas, la distancia $lev_{a,b}(i, j)$ se define recursivamente:

$$
lev_{a,b}(i, j) = \begin{cases}
 \max(i, j) & \text{si } \min(i, j) = 0, \\
 \min \begin{cases}
 lev_{a,b}(i-1, j) + 1 \\
 lev_{a,b}(i, j-1) + 1 \\
 lev_{a,b}(i-1, j-1) + 1_{(a_i \neq b_j)}
 \end{cases} & \text{si } \min(i, j) \neq 0.
\end{cases}
$$

---

## 4. EL "CEREBRO" (SISTEMAS DE MEMORIA)

### 4.1. Memoria a Corto Plazo (Context Window)
El LLM (Gemma) tiene una ventana de contexto limitada (2048 tokens).
* **Gestión de Turnos:** Lista FIFO de mensajes.
* **Pruning:** Se eliminan los mensajes más antiguos, preservando el `System Prompt`.

### 4.2. Memoria a Largo Plazo (Persistencia SQLite)
Almacenada en `database/BrainNut.db`.

### 4.3. Esquema de Base de Datos (SQL Reference)
```sql
CREATE TABLE IF NOT EXISTS memories (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 key TEXT NOT NULL UNIQUE,
 value TEXT NOT NULL,
 confidence REAL DEFAULT 1.0,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aliases (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_phrase TEXT NOT NULL UNIQUE,
 canonical_command TEXT NOT NULL,
 learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS history (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_input TEXT,
 assistant_response TEXT,
 intent_detected TEXT,
 timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.4. Aprendizaje Adaptativo (Alias y Preferencias)
Meta-aprendizaje simple (One-shot learning). Si el usuario corrige al asistente, se crea un alias persistente.

### 4.5. Estructura de Embeddings Vectoriales (RAG)
Implementado mediante **ChromaDB**.
* **Modelo de Embedding:** `sentence-transformers/all-MiniLM-L6-v2` (rápido, 384 dim).
* **Almacenamiento:** Base de datos persistente en local.
* **Proceso de Ingesta:** 
 1. Escaneo de carpeta `docs/`.
 2. Chunking (segmentación) de ficheros `.md`, `.txt`, `.pdf`.
 3. Generación de vectores y almacenamiento.
* **Recuperación:** Al preguntar, se buscan los 3 fragmentos más similares y se inyectan en el prompt del LLM ("Contexto Técnico").

---

## 5. INTELIGENCIA GENERATIVA (LLM)

### 5.1. Integración de Llama.cpp
Uso de `llama-cpp-python` con modelos GGUF y `mmap` para carga rápida.

### 5.2. Ingeniería de Prompts Avanzada (CoT, ReAct)
Para tareas complejas, se utilizan técnicas avanzadas en el prompt oculto.

**Chain-of-Thought (CoT):**
> "Usuario: ¿Cuánto es 23 * 4 + 10?
> Asistente: Primero multiplicamos 23 por 4, que es 92. Luego sumamos 10. El resultado es 102."

**ReAct (Reasoning + Acting):**
> "Pensamiento: El usuario quiere saber la IP.
> Acción: Ejecutar herramienta `get_ip_address`.
> Observación: 192.168.1.55
> Respuesta Final: Tu IP es 192.168.1.55."

### 5.3. Estrategias de Muestreo (Sampling)
* **Temperatura (0.7):** Balance creatividad/coherencia.
* **Top-P (0.9):** Nucleus sampling.
* **Repeat Penalty (1.1):** Evita bucles.

### 5.4. Optimización de Inferencia (KV Cache & Batching)
* **KV Cache:** Reutiliza cálculos de atención previos.
* **Batching:** Procesamiento por lotes (futuro).

### 5.5. Ajuste Fino (Fine-Tuning) y LoRA
Uso de Low-Rank Adaptation (LoRA) para adaptar el modelo base a la jerga de administración de sistemas sin reentrenamiento completo.

---

## 6. PROCESAMIENTO DE SEÑALES (LOS SENTIDOS)

### 6.1. Pipeline de Audio: VAD y Normalización
1. **Captura:** PCM 16-bit, 16kHz.
2. **Pre-énfasis:** Filtro paso alto.
3. **VAD Energético:** RMS > Umbral.
4. **Normalización:** Ajuste de ganancia.

### 6.2. Teoría de Procesamiento de Audio (FFT y MFCCs)
Para el reconocimiento de voz (Vosk/Whisper), el audio crudo se transforma en características espectrales.

1. **Ventaneo (Windowing):** Se aplica una ventana de Hamming para reducir la fuga espectral.
 $$ w(n) = 0.54 - 0.46 \cos\left(\frac{2\pi n}{N-1}\right) $$
2. **FFT (Fast Fourier Transform):** Convierte dominio tiempo a frecuencia.
3. **Banco de Filtros Mel:** Ajusta la escala de frecuencia a la percepción humana.
4. **DCT (Discrete Cosine Transform):** Descorrelaciona los coeficientes para obtener los MFCCs.

### 6.3. Pipeline de Visión
Detección de rostros con Haar Cascades y tracking de atención.

### 6.4. Fusión Sensorial
Combinación de VAD + Detección Facial para mejorar la confianza de activación.

---

## 7. COGNICIÓN MULTI-AGENTE (SWARM INTELLIGENCE)

### 7.1. Protocolo de Consenso
Evita el "efecto coro" entre dispositivos.
1. **Detección:** Todos detectan Wake Word.
2. **Evaluación:** `Score = SNR + Proximity`.
3. **Inhibición:** Líder publica `tio/consensus/claim`.
4. **Silencio:** Perdedores abortan.

### 7.2. Resolución de Conflictos
* **Jerarquía:** Master > Slave.
* **Timestamp:** Última voluntad gana.

### 7.3. Aprendizaje Federado (Concepto)
Compartición de tablas `aliases` vía MQTT.

---

## 8. DESARROLLO DE HABILIDADES (SKILLS)

> **Nota:** La guía de desarrollo de skills se ha movido al **[ANEXO V: PROGRAMACIÓN Y CREACIÓN DE SKILLS](ANEXO_V_PROGRAMACION_Y_SKILLS.md)**.

### 8.1. Skill de Docker (Nueva Integración)
Skill diseñada para la gestión de contenedores.
* **Pipeline:** Voz -> STT -> MANGO T5 (NL2Bash) -> `docker restart <container>` -> Confirmación.
* **Interfaz Web:** Endpoint `/api/docker` para visualizar logs y estado en tiempo real.

---

## 9. CASOS DE ESTUDIO DE INTERACCIÓN

### 9.1. Caso 1: Resolución de Ambigüedad
**Escenario:** El usuario dice "Apaga".
**Problema:** Hay múltiples dispositivos (Luz Salón, Luz Cocina, PC).
**Proceso Cognitivo:**
1. **NLU:** Detecta intent `turn_off` pero falta entidad `device`.
2. **Decisión:** Score de confianza bajo para ejecución directa.
3. **Acción:** El sistema pregunta "¿Qué quieres que apague?".
4. **Usuario:** "La luz del salón".
5. **NLU:** Fusiona el contexto anterior ("Apaga") con el nuevo input ("Luz salón").
6. **Ejecución:** Apaga la luz del salón.

### 9.2. Caso 2: Cambio de Contexto (Context Switching)
**Escenario:** Usuario pregunta por el clima y, a mitad de la respuesta, interrumpe.
**Proceso Cognitivo:**
1. **Estado:** `SPEAKING` (Dando el clima).
2. **Evento:** VAD detecta voz nueva ("Espera, ¿qué hora es?").
3. **Interrupción:** El hilo de audio detiene el TTS inmediatamente (`stop_speaking()`).
4. **Nuevo Proceso:** Se descarta el resto de la respuesta del clima.
5. **NLU:** Procesa "¿qué hora es?".
6. **Ejecución:** Dice la hora.

### 9.3. Caso 3: Recuperación de Errores (Self-Correction)
**Escenario:** El LLM genera un comando JSON inválido.
**Proceso Cognitivo:**
1. **Generación:** LLM produce `{"action": "turn_on", "device": "light"}` (falta `location`).
2. **Validación:** El `SkillExecutor` valida el JSON contra el esquema.
3. **Error:** `ValidationError: 'location' is required`.
4. **Re-Prompting:** El sistema envía el error de vuelta al LLM: "Error: falta location. Corrige el JSON".
5. **Corrección:** LLM genera `{"action": "turn_on", "device": "light", "location": "unknown"}`.
6. **Fallback:** El sistema pide aclaración al usuario.

---

## 10. TROUBLESHOOTING COGNITIVO

> **Nota:** La guía de solución de problemas cognitivos se ha movido al **[ANEXO IV: RESOLUCIÓN DE PROBLEMAS](ANEXO_IV_RESOLUCION_DE_PROBLEMAS.md)**.

---

## 11. REFERENCIA DE API INTERNA (AI MODULES)

### 11.1. Módulo `AIEngine`
Clase responsable de la inferencia del LLM.

* `__init__(model_path: str)`: Inicializa el modelo GGUF.
* `generate_response(prompt: str, max_tokens: int) -> str`: Genera una respuesta completa (bloqueante).
* `generate_stream(prompt: str) -> Iterator[str]`: Genera tokens uno a uno para streaming (menor latencia percibida).
* `reload_model(new_path: str)`: Cambia el modelo en caliente sin reiniciar el servicio.

### 11.2. Módulo `IntentManager`
Clase responsable del NLU y enrutamiento.

* `register_skill(skill: BaseSkill)`: Registra una nueva habilidad y sus intents.
* `parse_command(text: str) -> IntentResult`: Procesa texto y devuelve el mejor match con su score.
* `learn_alias(user_phrase: str, command: str)`: Añade una entrada a la base de datos de alias.

### 11.3. Módulo `VoiceManager`
Clase responsable del I/O de audio.

* `start_listening()`: Inicia el hilo de captura y VAD.
* `stop_listening()`: Pausa la captura (ej. mientras habla).
* `speak(text: str)`: Sintetiza voz usando el motor TTS configurado (Piper/Espeak).

---

## 12. REFERENCIA DE CONFIGURACIÓN (AI)

### 12.1. Bloque `ai_engine`
Parámetros en `config.json`:

```json
"ai_engine": {
 "model_path": "models/gemma-2b-it-q4_k_m.gguf",
 "context_window": 2048,
 "temperature": 0.7,
 "top_p": 0.9,
 "n_threads": 3,
 "system_prompt": "Eres un asistente..."
}
```

### 12.2. Bloque `voice`
```json
"voice": {
 "stt_engine": "vosk",
 "tts_engine": "piper",
 "vad_sensitivity": 2, // 0-3 (3 es más sensible)
 "wake_word": "tio"
}
```

### 12.3. Bloque `intents`
```json
"intents": {
 "confidence_threshold": 70,
 "fuzzy_matching": true,
 "learning_enabled": true
}
```

---

## 13. CONSIDERACIONES ÉTICAS Y DE SEGURIDAD

### 13.1. Sesgo Algorítmico
Mitigación mediante System Prompts neutrales.

### 13.2. Alucinaciones y Veracidad
Instrucción explícita de admitir ignorancia. Uso de motor determinista para acciones críticas.

### 13.3. Protección contra Inyecciones de Prompt
Delimitación estricta del input de usuario y re-inyección del System Prompt en cada turno.

---

## 14. HOJA DE RUTA (ROADMAP) DE IA

### 14.1. Multimodalidad
Integración de modelos LLaVA (Large Language-and-Vision Assistant) para permitir que el asistente "vea" y describa imágenes capturadas por la cámara en tiempo real.

### 14.2. RAG (Retrieval-Augmented Generation)
Conectar el LLM a la documentación técnica local (man pages, wikis) mediante una base de datos vectorial, permitiendo al asistente responder preguntas técnicas precisas citando fuentes.

---

## 15. ANEXOS DE IA

### 15.1. Estructura de Datos de Intents
```json
{
 "name": "nombre_intent",
 "triggers": ["frase 1", "frase 2 {param}"],
 "action": "funcion",
 "parameters": {"param": "default"},
 "confidence": 0.75
}
```

### 15.2. Parámetros de Inferencia Recomendados
| Parámetro | Valor |
| :--- | :--- |
| `n_ctx` | 2048 |
| `n_batch` | 512 |
| `f16_kv` | True |

### 15.3. Glosario de Términos de IA
* **Alucinación:** Invención de datos.
* **Token:** Unidad de texto.
* **Embedding:** Vector semántico.
* **LoRA:** Adaptación de bajo rango.
* **In-Context Learning:** Aprendizaje sin reentrenamiento, solo vía prompt.
* **Quantization:** Reducción de precisión (FP16 -> INT4) para ahorrar RAM.
* **Beam Search:** Algoritmo de búsqueda que explora múltiples caminos probables.
* **Perplexity:** Métrica de incertidumbre del modelo.
* **Transformer:** Arquitectura basada en mecanismos de atención (Attention is All You Need).

### 15.4. Bibliografía y Referencias
1. *Attention Is All You Need* (Vaswani et al., 2017) - Arquitectura Transformer.
2. *LoRA: Low-Rank Adaptation of Large Language Models* (Hu et al., 2021).
3. *Gemma: Open Models Based on Gemini Research and Technology* (Google DeepMind, 2024).
4. *RapidFuzz: Fast string matching in Python* (Max Bachmann).
5. *llama.cpp: Port of Facebook's LLaMA model in C/C++* (Georgi Gerganov).

### 15.5. Licencia y Derechos de Uso
Este documento técnico y la arquitectura descrita son propiedad intelectual del proyecto WatermelonD Se permite su uso, modificación y distribución bajo los términos de la licencia MIT, siempre que se mantenga la atribución original. El uso de los modelos de IA (Gemma, Llama) está sujeto a sus respectivas licencias de uso.

---
**Fin del Documento de Arquitectura e Inteligencia Artificial**
