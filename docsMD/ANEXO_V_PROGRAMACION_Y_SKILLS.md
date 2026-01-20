# ANEXO V: PROGRAMACIÓN Y CREACIÓN DE SKILLS

**Proyecto:** WatermelonD (Language Copilot for Group and Administration Environments) 
**Fecha:** 04/12/2025 
**Versión del Documento:** 1.0

---

## 1. INTRODUCCIÓN

Este documento es una guía técnica detallada para desarrolladores que deseen extender la funcionalidad de WatermelonD mediante la creación de nuevos módulos o "Skills".

---

## 2. ARQUITECTURA DE UNA SKILL

Las Skills se encuentran en el directorio `modules/BlueberrySkills/`. Cada Skill es una clase de Python que encapsula una funcionalidad específica.

### 2.1. Estructura Básica
Aunque el sistema soporta inyección de dependencias simple, se recomienda seguir este patrón:

```python
# modules/BlueberrySkills/ejemplo_skill.py

from modules.skills.base_skill import BaseSkill, intent

class EjemploSkill(BaseSkill):
 def __init__(self, core):
 super().__init__(name="EjemploSkill")
 self.core = core# Referencia al núcleo (WatermelonD)

 @intent("ejemplo_intent")
 def handle_ejemplo(self, message):
 """
 Maneja la intención 'ejemplo_intent'.
 """
 self.core.speak("Ejecutando la skill de ejemplo.")
 return True
```

### 2.2. Decoradores de Intención
El decorador `@intent("nombre_intent")` registra automáticamente el método en el `IntentManager` al iniciar el sistema. Esto permite una arquitectura modular donde añadir una nueva capacidad es tan simple como crear un archivo en `modules/BlueberrySkills/`.

---

## 3. REGISTRO DE INTENTS (NLU)

Para que una Skill sea accesible por voz, debe definir qué frases la activan.

### 3.1. Definición en `intents.json` (Padatious/Vosk)
El archivo `config/intents.json` define los disparadores (triggers).

```json
{
 "name": "ejemplo_intent",
 "triggers": [
 "ejecuta el ejemplo",
 "prueba la skill de ejemplo",
 "haz una prueba con parámetro {param}"
 ],
 "action": "handle_ejemplo",
 "parameters": {
 "param": "default_value"
 }
}
```

### 3.2. Extracción de Entidades
Si el trigger contiene `{param}`, el sistema extraerá esa parte de la frase y la pasará al método de la skill.

```python
 @intent("ejemplo_intent")
 def handle_ejemplo(self, message):
 param = message.entities.get('param')
 self.core.speak(f"Recibido parámetro: {param}")
```

---

## 4. ACCESO AL NÚCLEO (WatermelonD)

La instancia `self.core` proporciona acceso a todos los subsistemas críticos:

* **TTS (Hablar):** `self.core.speak("Texto a decir")`
* **Configuración:** `self.core.config.get("clave")`
* **MQTT:** `self.core.mqtt_manager.publish(topic, payload)`
* **SSH:** `self.core.ssh_manager.execute(command)`
* **Memoria:** `self.core.memory.get("clave")`

### 4.1. Gestión de Estado UI
Para actualizar la interfaz web desde un módulo o skill:
```python
from modules.web_admin import set_audio_status, update_face

# Actualizar iconos de estado de audio
set_audio_status(output_enabled=True, input_enabled=False)

# Actualizar estado de la cara (idle, listening, thinking, speaking)
update_face("thinking")
```
---

## 5. BUENAS PRÁCTICAS DE DESARROLLO

1. **No bloquear el hilo principal:**
 Si la Skill realiza una operación larga (descarga, cálculo pesado), ejecútela en un hilo separado (`threading.Thread`) para no congelar la escucha o el TTS.

 ```python
 def handle_long_task(self, message):
 threading.Thread(target=self._heavy_lifting).start()
 self.core.speak("Iniciando tarea en segundo plano.")
 ```

2. **Manejo de Errores:**
 Envuelva su código en bloques `try-except` para evitar que un error en la Skill tumbe todo el servicio `neo.service`.

3. **Logs:**
 Use `app_logger` (importado de `modules.logger`) para registrar la actividad, no `print()`.

---

## 6. EJEMPLO COMPLETO: SKILL DE CLIMA

```python
from modules.skills.base_skill import BaseSkill, intent
import requests

class WeatherSkill(BaseSkill):
 def __init__(self, core):
 super().__init__(name="WeatherSkill")

 @intent("weather_query")
 def handle_weather(self, message):
 """
 Trigger: '¿Qué tiempo hace en {city}?'
 """
 city = message.entities.get('city', 'Madrid')
 
# Llamada a API externa (ejemplo)
 try:
# Nota: Usar requests en hilo aparte en producción
 temp = self._get_fake_weather(city) 
 response = f"En {city} hace {temp} grados."
 except Exception as e:
 self.core.logger.error(f"Error clima: {e}")
 response = "No pude obtener el clima."
 
 self.core.speak(response)
 return response

 def _get_fake_weather(self, city):
 return 25# Simulación
```
