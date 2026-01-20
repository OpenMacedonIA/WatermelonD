# Evolución del Sistema NEOPapaya

## Fase 1: Prototipo (Legacy)
- Sistema monolítico.
- Reconocimiento de voz básico.
- Sin memoria persistente real.

## Fase 2: Modularización
- Separación en `modules/`.
- Introducción de `WatermelonD` como orquestador.
- Implementación de `Brain` (SQLite).

## Fase 3: Inteligencia Local (Actual)
- **Motor AI**: Migración a Gemma-2B (local) con `llama-cpp-python`.
- **Voz**: Implementación de Faster-Whisper y Vosk con gramática dinámica.
- **TTS**: Integración de Piper TTS (neuronal) con fallback a binario para estabilidad.
- **Optimización**:
 - Reducción de hilos de LLM.
 - Caché de intenciones (`IntentManager`).
 - Refactorización de `WatermelonD` para delegar lógica a Skills.

## Futuro (Roadmap)
- **Fase 4**: Interfaz Web Avanzada (React/Vue).
- **Fase 5**: Integración IoT completa (Home Assistant).
- **Fase 6**: Ecosistema distribuido (Network Bros).
