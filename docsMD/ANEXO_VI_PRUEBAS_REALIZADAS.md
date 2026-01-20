# ANEXO VIII: PRUEBAS DE VALIDACIÓN Y RENDIMIENTO

**Proyecto:** WatermelonD (Language Copilot for Group and Administration Environments)
**Fecha:** 06/12/2025
**Versión del Documento:** 1.0

---

## 1. INTRODUCCIÓN

Este documento detalla la batería de pruebas realizadas para validar la funcionalidad, estabilidad y rendimiento del sistema WatermelonD Se incluyen pruebas unitarias de componentes críticos, pruebas de integración del pipeline completo y pruebas de estrés/rendimiento en hardware objetivo (Raspberry Pi 4/5).

---

## 2. PRUEBAS UNITARIAS Y DE COMPONENTES

### 2.1. Validación del Sistema RAG (Retrieval-Augmented Generation)

**Objetivo:** Verificar que el sistema puede ingerir documentos locales y recuperar contextos relevantes ante una consulta.

* **Script de Prueba:** `test_rag_temp.py`
* **Metodología:**

1. Inicialización de `KnowledgeBase` con una base de datos temporal.
2. Ingesta forzada de documentos del directorio `docs/`.
3. Ejecución de consulta de prueba: "arquitectura cognitiva".
4. Verificación de que el resultado contiene palabras clave relevantes.

* **Resultados:**
* **Ingesta:** Correcta (Vectorización de documentos Markdown).
* **Búsqueda:** Recuperación de fragmentos de `ANEXO_III` con alta similitud semántica.
* **Tiempo de Respuesta:** < 200ms para búsqueda en base de datos local (ChromaDB/SQLite).

### 2.2. Pruebas del Bus de Eventos (MQTT)

**Objetivo:** Asegurar la comunicación asíncrona entre módulos.

* **Herramienta:** `mosquitto_sub` / `mosquitto_pub` y scripts internos.
* **Casos de Prueba:**

1. **Publicación de Telemetría:** Verificar que `home/agents/{hostname}/telemetry` recibe datos cada 60s.
2. **Recepción de Comandos:** Enviar JSON a `home/agents/{hostname}/commands` y verificar reacción.

* **Resultados:**
* Latencia de mensaje: < 10ms en red local.
* Persistencia: Mensajes `retained` (como `discovery`) se mantienen tras reinicio del suscriptor.

---

## 3. PRUEBAS DE INTEGRACIÓN (PIPELINE COMPLETO)

### 3.1. Prueba End-to-End de Voz

**Objetivo:** Validar el flujo completo: Audio -> STT -> NLU -> Lógica -> TTS.

* **Script de Prueba:** `test_pipeline.py`
* **Metodología:**

1. Inyección simulada de texto ("qué hora es") en el bus MQTT (`recognizer_loop:utterance`), saltando la etapa de micrófono para aislar la lógica.
2. Escucha del evento `speak` en el bus.
3. Medición del tiempo total de ida y vuelta.

* **Resultados:**
* **NLU:** Intención `time_query` detectada correctamente con score > 0.8.
* **Respuesta:** El sistema generó el evento `speak` con la hora actual.
* **Tiempo de Ejecución:** ~0.5s (sin contar síntesis de voz real).

### 3.2. Pruebas de Interrupción (Barge-in)

**Objetivo:** Verificar que el usuario puede interrumpir al asistente mientras habla.

* **Escenario:**

1. El asistente comienza a leer un texto largo.
2. El usuario dice "WatermelonD, para".

* **Resultados:**
* El módulo de audio detecta energía (VAD) durante el estado `SPEAKING`.
* Se envía señal `tts:stop`.
* El audio se detiene en < 300ms.

---

## 4. PRUEBAS DE RENDIMIENTO Y ESTRÉS

### 4.1. Consumo de Recursos en Reposo (Idle)

**Hardware:** Raspberry Pi 4 (4GB RAM).

| Métrica                | Valor Medido | Objetivo | Estado |
| :---------------------- | :----------- | :------- | :----- |
| **CPU Load**      | 2-5%         | < 10%    | Pasa   |
| **RAM (Sistema)** | 450 MB       | < 1 GB   | Pasa   |
| **Temperatura**   | 45°C        | < 50°C  | Pasa   |

### 4.2. Consumo durante Inferencia (Thinking)

**Modelo:** Gemma-2B-IT (Quantized q4_k_m).

| Métrica              | Valor Medido   | Notas                                     |
| :-------------------- | :------------- | :---------------------------------------- |
| **CPU Load**    | 380% (4 cores) | Saturación esperada durante generación. |
| **RAM (Pico)**  | 1.8 GB         | Dentro del margen de 4GB.                 |
| **Tokens/seg**  | ~4-6 t/s       | Aceptable para lectura en tiempo real.    |
| **Temperatura** | 65-70°C       | Requiere disipación activa (ventilador). |

### 4.3. Latencia del Sistema (Latency)

Desglose del tiempo de respuesta para una consulta simple ("Hola").

1. **VAD + Grabación:** 500ms (Buffer de silencio final).
2. **STT (Whisper/Vosk):** 800ms - 1.5s (Depende de la longitud).
3. **LLM (Pre-fill):** 500ms (Procesamiento del prompt).
4. **TTS (Generación):** 200ms (Primer byte de audio).
5. **Total Percibido:** ~2.5 - 3.0 segundos.

---

## 5. CONCLUSIONES DE LAS PRUEBAS

1. **Estabilidad:** El sistema es estable para interacciones cortas y medias. No se observaron fugas de memoria (memory leaks) significativas tras 24h de operación continua, gracias a la gestión de `gc.collect()`.
2. **Cuello de Botella:** El principal cuello de botella es la CPU durante la inferencia del LLM y el STT.
3. **Recomendación:** Para entornos de producción, se recomienda encarecidamente el uso de **Raspberry Pi 5** o un mini-PC x86, lo que reduciría la latencia total a < 1.5s.
