# ANEXO IV: RESOLUCIÓN DE PROBLEMAS (TROUBLESHOOTING)

**Proyecto:** WatermelonD (Language Copilot for Group and Administration Environments) 
**Fecha:** 04/12/2025 
**Versión del Documento:** 1.0

---

## 1. INTRODUCCIÓN

Este documento consolida todas las guías de solución de problemas, códigos de error y procedimientos de depuración para el sistema WatermelonD, abarcando desde problemas de usuario final hasta depuración de bajo nivel.

---

## 2. PROBLEMAS DE USUARIO FINAL (AUDIO Y CONECTIVIDAD)

### 2.1. Problemas de Audio (Micrófono/Altavoces)
**Síntoma:** El asistente no escucha o no habla.
**Solución:**
1. Verifique dispositivos: `aplay -l` (altavoces) y `arecord -l` (micrófono).
2. Ajuste volúmenes con `alsamixer`. Asegúrese de que el micrófono no esté en "Mute" (MM).
3. Verifique logs: Busque errores de `PyAudio` o `ALSA` en el journal.

### 2.2. Problemas de Reconocimiento de Voz
**Síntoma:** Entiende mal los comandos o no reacciona.
**Solución:**
1. **Ruido ambiental:** El reconocimiento empeora con ruido. Intente hablar más cerca del micrófono.
2. **Modelo Vosk:** Si usa un modelo pequeño ("small"), intente cambiar a uno más grande si el hardware lo permite.
3. **Calibración:** Ajuste la sensibilidad en `config.json` si es necesario.

### 2.3. Problemas de Conectividad
**Síntoma:** No detecta la red o falla el ping.
**Solución:**
1. Verifique conexión física/WiFi: `ip a`.
2. Verifique DNS: `cat /etc/resolv.conf`.
3. Si falla MQTT, verifique que `mosquitto` esté corriendo: `sudo systemctl status mosquitto`.

### 2.4. Errores del Modelo LLM (Generales)
**Síntoma:** Respuestas lentas, incoherentes o el servicio se reinicia al intentar hablar.
**Solución:**
1. **Memoria Insuficiente:** Si el sistema tiene <4GB RAM, el OOM Killer puede estar matando el proceso. Revise `dmesg`. Solución: Aumentar Swap o usar un modelo cuantizado más pequeño (q2_k).
2. **Instrucciones CPU:** Si ve "Illegal Instruction", su CPU no soporta AVX/AVX2. Necesitará recompilar `llama.cpp` o usar una versión compatible con hardware antiguo.

---

## 3. TROUBLESHOOTING COGNITIVO (IA Y LÓGICA)

### 3.1. Diagnóstico de NLU (Falsos Positivos/Negativos)
Si el sistema no entiende un comando:
1. **Revisar Logs:** Buscar `IntentManager: Match Score`.
2. **Score Bajo (<60):** El trigger no se parece lo suficiente. Añadir variaciones en `intents.json`.
3. **Falso Positivo:** El sistema se activa con ruido. Aumentar `confidence_threshold` o añadir penalización por longitud.

### 3.2. Depuración de Alucinaciones del LLM
Si el LLM inventa respuestas:
1. **Bajar Temperatura:** Reducir de 0.7 a 0.2 en `config.json`.
2. **Reforzar System Prompt:** Añadir "Si no sabes la respuesta, di 'No lo sé'".
3. **Verificar Contexto:** Asegurarse de que el historial no contiene información contradictoria.

### 3.3. Problemas de Latencia en Inferencia
Si el sistema tarda >5s en responder:
1. **Hardware:** Verificar throttling térmico (`vcgencmd measure_temp`).
2. **Hilos:** Asegurar que `n_threads` no satura todos los núcleos (dejar 1 libre).
3. **Modelo:** Cambiar a una cuantización menor (ej. Q4_K_M a Q2_K).

---

## 4. PROBLEMAS DE INGENIERÍA Y DESPLIEGUE

### 4.1. Troubleshooting de Compilación
* **Error `missing Python.h`:** Falta `python3-dev`. Instalar con `sudo apt install python3-dev`.
* **Error `gcc: error: ...`:** Falta `build-essential`.
* **Error `portaudio.h not found`:** Falta `portaudio19-dev`.
* **Error `Illegal Instruction` (SIGILL):** Se compiló con flags (ej. AVX2) que la CPU actual no soporta. Recompilar sin esas flags.

### 4.2. Debugging con GDB
Si el proceso Python crashea con `Segmentation Fault` (común en librerías C++ como Vosk/Llama), usar GDB para obtener un backtrace.

```bash
sudo apt install gdb python3-dbg
gdb python3
(gdb) run start_services.py
# ... esperar al crash ...
(gdb) bt
# Copiar el output del Backtrace para reportar el bug
```

---

## 5. CÓDIGOS DE ERROR INTERNOS

Códigos estandarizados para logs y alertas MQTT.

| Código | Significado | Acción Recomendada |
| :--- | :--- | :--- |
| `E001` | Audio Device Not Found | Verificar `arecord -l` y permisos. |
| `E002` | MQTT Connection Lost | Revisar red y estado de Mosquitto. |
| `E003` | LLM OOM (Out of Memory) | Aumentar Swap o reducir hilos/contexto. |
| `W001` | High CPU Temp (>80C) | Revisar ventilación (Throttling activo). |
| `S001` | Auth Failure (Web/SSH) | Posible intrusión. Revisar logs. |
