# Guía de Redacción: Conclusiones y Mejoras (Sección 9 y 10)

Usa estos puntos para redactar tus conclusiones finales.

## 9. Conclusiones (Logros alcanzados)
*   **Viabilidad del LLM Local:** Se ha demostrado que es posible ejecutar modelos de lenguaje competentes (Gemma 2B / MANGO T5) en hardware modesto (i3/8GB) con tiempos de respuesta aceptables.
*   **Privacidad Real:** Se ha cumplido el objetivo de crear un sistema 100% offline, eliminando la dependencia de la nube para tareas críticas como el reconocimiento de voz (Vosk) y la síntesis (Piper).
*   **Arquitectura Modular:** La reescritura del núcleo (Core V4 / V2.5.0) ha demostrado ser robusta, permitiendo que el sistema se "autocure" (Self-Healing) y escale con nuevos módulos sin romper la base.
*   **Utilidad Real:** No es solo un chatbot; las herramientas de SysAdmin (control de servicios, SSH, Docker) aportan valor real a un perfil técnico que necesita "manos libres".

## 10. Propuestas de Mejora (Futuro)
*   **Hardware:** Migrar a una NPU (Neural Processing Unit) dedicada o hardware más moderno (como Raspberry Pi 5 con acelerador AI) para modelos más grandes (Llama 3 8B).
*   **Voz:** Mejorar el modelo acústico de Vosk o migrar completamente a Whisper (Stream) cuando el hardware lo permita para una transcripción perfecta en ambientes ruidosos.
*   **IoT:** Ampliar la compatibilidad con Home Assistant estándar en lugar de solo MQTT customizado.
*   **Seguridad:** Implementar autenticación biométrica real (Voz) que actualmente está en fase experimental.
