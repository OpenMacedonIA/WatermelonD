# Registro de Problemas y Soluciones

## Problemas Encontrados

### 1. Bloqueo en Bucle de Voz (VoiceManager)
- **Síntoma**: El sistema consumía mucha CPU o se quedaba bloqueado en el bucle de escucha.
- **Causa**: El método `stream.read` de PyAudio podía bloquearse o retornar muy rápido en caso de error, creando un bucle infinito ("busy loop").
- **Solución**: Se añadió un manejo de excepciones robusto con `time.sleep(1)` en caso de error y se optimizó la lógica de pausa cuando el sistema está procesando.

### 2. Fallo en Búsqueda de Recuerdos (Database)
- **Síntoma**: La función `search_memories` fallaba al intentar recuperar la fecha de los recuerdos.
- **Causa**: Las tablas virtuales FTS5 no almacenan columnas adicionales por defecto y la consulta SQL no hacía el JOIN correcto con la tabla principal.
- **Solución**: Se corrigió la consulta SQL para hacer un `JOIN` explícito entre `episodic_memory` y `memory_fts`.

### 3. "God Object" NeoCore
- **Síntoma**: `NeoCore.py` tenía más de 500 líneas y manejaba lógica de negocio (citas, resumen matutino) mezclada con orquestación.
- **Solución**: Se movió la lógica específica a `OrganizerSkill` y `SystemSkill`, dejando `NeoCore` solo como orquestador.

### 4. Duplicidad en Skills
- **Síntoma**: Lógica redundante en `modules/sysadmin.py` y `modules/skills/system.py`.
- **Solución**: Se clarificó la separación: `SysAdminManager` es la capa de bajo nivel (driver) y `SystemSkill` es la capa de alto nivel (interfaz de voz).

## Estado Actual
El sistema es ahora más modular y robusto. La refactorización ha eliminado código muerto y optimizado los flujos críticos.
