# ANEXO VII: RETOS DE DESARROLLO Y SOLUCIONES ADOPTADAS

**Proyecto:** WatermelonD (Language Copilot for Group and Administration Environments) 
**Fecha:** 06/12/2025 
**Versión del Documento:** 1.0

---

## 1. INTRODUCCIÓN

Este anexo documenta los principales obstáculos técnicos encontrados durante el ciclo de desarrollo del proyecto WatermelonD, así como las soluciones de ingeniería implementadas para superarlos. A diferencia del *Anexo IV (Troubleshooting)*, que se centra en el usuario final, este documento se centra en las decisiones de arquitectura y optimización de bajo nivel.

---

## 2. RETOS DE AUDIO Y LATENCIA

### 2.1. El Problema de PulseAudio/PipeWire en Headless
**Problema:** Inicialmente, el sistema utilizaba las capas de abstracción de audio estándar de Linux (PulseAudio). En la Raspberry Pi, esto introducía una latencia variable de 200ms a 500ms y un consumo de CPU del 5-10% solo por mantener el servidor de audio activo, lo cual es crítico en un sistema embebido.
**Solución:**
* Se migró a **ALSA (Advanced Linux Sound Architecture)** directo mediante `PyAudio`.
* Se implementó un acceso exclusivo al dispositivo de hardware (`hw:X,Y`), eliminando capas intermedias de mezcla.
* **Resultado:** Reducción de latencia de captura a < 50ms y liberación de CPU.

### 2.2. Cancelación de Eco (AEC)
**Problema:** El micrófono captaba la propia voz del asistente (TTS), creando un bucle de retroalimentación infinito donde el asistente se escuchaba a sí mismo y se respondía.
**Solución:**
* Implementación de un mecanismo de **"Semáforo de Audio"**. Cuando el estado del sistema es `SPEAKING`, se suspende temporalmente la entrada del micrófono o se descartan los frames de audio entrantes.
* Aunque existen soluciones de software para AEC (WebRTC), consumían demasiada CPU. La solución lógica (mutear input al hablar) resultó ser la más eficiente para este hardware.

---

## 3. RETOS DE INTELIGENCIA ARTIFICIAL (LLM)

### 3.1. Inferencia Lenta en CPU ARM
**Problema:** Ejecutar modelos de 7B parámetros (como Llama-2-7b) resultaba en tiempos de generación de > 10 segundos por token, haciendo el sistema inusable.
**Solución:**
* **Cambio de Modelo:** Migración a **Gemma-2B**, un modelo más pequeño optimizado por Google.
* **Cuantización:** Uso del formato **GGUF** (Q4_K_M) mediante `llama.cpp`. Esto reduce el uso de memoria y aprovecha las instrucciones NEON del procesador ARM.
* **Resultado:** Velocidad de 4-6 tokens/segundo, suficiente para una conversación fluida.

### 3.2. Alucinaciones y "Verborrea"
**Problema:** Los modelos pequeños tienden a perder el hilo o generar respuestas excesivamente largas y poéticas para comandos simples (ej. "¿Qué hora es?" -> "El tiempo es una construcción relativa...").
**Solución:**
* **Ingeniería de Prompts (System Prompt):** Se diseñó un prompt estricto que define la "personalidad" del asistente como concisa y servicial.
* **Stop Tokens:** Configuración de tokens de parada para cortar la generación si el modelo intenta alucinar una continuación del diálogo del usuario.

---

## 4. RETOS DE SISTEMA Y MEMORIA

### 4.1. OOM Killer (Out of Memory)
**Problema:** Al cargar el modelo LLM y el modelo de Whisper simultáneamente, el consumo de RAM superaba los 4GB de la Raspberry Pi, provocando que el kernel matara el proceso `python`.
**Solución:**
* **Carga Diferida (Lazy Loading):** No cargar todos los modelos al inicio si no es estrictamente necesario (aunque para latencia se prefiere tenerlos en RAM).
* **ZRAM:** Configuración de un bloque de Swap comprimido en RAM (`zstd`). Esto permite "estirar" la memoria efectiva hasta unos 6-7GB con un coste mínimo de CPU.
* **Monitorización:** Implementación de `gc.collect()` forzado tras cada ciclo de inferencia grande.

### 4.2. Corrupción de Tarjeta SD
**Problema:** Las constantes escrituras de logs y bases de datos temporales degradaban la tarjeta SD, riesgo común en RPi.
**Solución:**
* **Logs en RAM:** Montaje de `/var/log` y directorios temporales en `tmpfs`.
* **Modo WAL en SQLite:** Configuración de Write-Ahead Logging para minimizar el riesgo de corrupción de base de datos ante cortes de energía.

---

## 5. CONCLUSIÓN

El desarrollo de WatermelonD ha demostrado que es posible ejecutar IA generativa moderna en hardware de bajo coste (Edge AI), siempre y cuando se apliquen optimizaciones agresivas a nivel de sistema operativo y se elijan las arquitecturas de modelos adecuadas (SLMs vs LLMs).
