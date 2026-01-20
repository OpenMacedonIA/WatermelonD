# Funciones Experimentales y Roadmap Futuro

Este documento recopila ideas, propuestas y funcionalidades experimentales planificadas para futuras versiones de **WatermelonD **. Estas características están en fase de investigación y pueden ser inestables o requerir hardware específico.

---

## 1. Clonación de Voz y TTS Personalizado
**Estado:** Propuesta
**Objetivo:** Permitir que WatermelonD hable con voces personalizadas o clonadas en local, sin depender de modelos pre-entrenados genéricos.
**Implementación Potencial:**
* Integrar **Coqui TTS** o **Tortoise TTS** para generación offline de alta calidad.
* Crear un script de "grabación de muestras" donde el usuario lee frases para entrenar un *embed* de su propia voz.
* **Desafío:** La inferencia en tiempo real de modelos de clonación requiere mucha CPU/GPU.

## 2. Audio Multi-Habitación (Sincronización)
**Estado:** Propuesta
**Objetivo:** Reproducir música o TTS perfectamente sincronizado en múltiples dispositivos "Micro WatermelonD BrainNut" (ESP32 o Pi Zero) distribuidos por la casa.
**Implementación Potencial:**
* Implementar un servidor **Snapcast** en el núcleo.
* Configurar los satélites como clientes Snapcast.
* Permitir "Follow Me" audio: la música te sigue de habitación en habitación usando detección de presencia (Bluetooth/Visión).

## 3. Aprendizaje Continuo (Fine-tuning Local)
**Estado:** En Investigación
**Objetivo:** Que el LLM (Llama/Gemma) aprenda el estilo de hablar y los datos específicos del usuario no solo mediante RAG, sino re-entrenando capas del modelo (LoRA).
**Implementación Potencial:**
* Pipeline nocturno que toma las interacciones del día (ya guardadas en `database.py`).
* Usar `llama.cpp` o `Unsloth` para ajustar un adaptador LoRA ligero.
* **Beneficio:** El asistente se vuelve verdaderamente único para cada usuario.

## ️ 4. Gestos Visuales "Sin Contacto"
**Estado:** Propuesta
**Objetivo:** Controlar funciones básicas (parar alarma, siguiente canción) mediante gestos con la mano frente a la cámara, sin usar la voz.
**Implementación Potencial:**
* Usar **MediaPipe Hands** sobre el stream de la cámara actual.
* Detectar gestos simples: "Palma abierta" (Stop), "Pulgar arriba" (Confirmar), "Deslizar" (Siguiente).
* Útil para cuando hay mucho ruido ambiente o es de noche.

## 5. Autenticación Biométrica Multinodal
**Estado:** Propuesta
**Objetivo:** Capa de seguridad estricta para comandos sensibles (ej: "Abrir puerta", "Apagar servidor").
**Implementación Potencial:**
* Requerir **dos factores simultáneos**: Reconocimiento Facial + Huella de Voz.
* Si la cámara no ve al usuario autorizado, se deniega el comando aunque la voz coincida (anti-spoofing).

## 6. Inteligencia Emocional Adaptativa
**Estado:** Propuesta
**Objetivo:** Que WatermelonD detecte el estado de ánimo tu voz y adapte su respuesta (tono, brevedad).
**Implementación Potencial:**
* Analizar prosodia (tono, velocidad) del audio de entrada.
* Si el usuario suena estresado/urgente -> Respuestas cortas y directas ("Hecho.").
* Si el usuario suena relajado -> Respuestas más conversacionales y detalladas.

## 7. Hub Domótico Offline (Matter/Zigbee)
**Estado:** Propuesta
**Objetivo:** Eliminar dependencia de Home Assistant para funciones básicas.
**Implementación Potencial:**
* Integrar soporte directo para dongles Zigbee (CC2531).
* Implementar servidor **Matter** local usando librerías de Python.
* Control directo de bombillas y enchufes con latencia cero.

---

> *¿Tienes una idea? Añádela a esta lista haciendo un Pull Request o editando este archivo.*
