# 🍉 WatermelonD - Project Roadmap & TO-DO

Este documento centraliza las tareas pendientes para completar la transición de **NeoPapaya** a **WatermelonD**, así como mejoras técnicas y de documentación.

## 🚨 Prioridad Crítica (HOTFIX)

- [x] **Reparar `install.sh`**:
    - [x] El script intenta acceder a `web_client/app.py` pero la carpeta se llama `TangerineUI`. Corregir rutas. (Corregido: referencias a `web_client` cambiadas por `TangerineUI`).
    - [x] El servicio `neo-web.service` fallará al arrancar por esta ruta errónea. (Corregido: Servicio eliminado, el Core lanza la web internamente).
- [x] **Resolver Duplicidad Web**:
    - [x] `NeoCore.py` lanza un servidor web interno (`modules/web_admin.py`).
    - [x] `install.sh` configura otro servicio web independiente (`TangerineUI/app.py`).
    - [x] **Acción**: Investigar si son redundantes y unificar en uno solo. (Unificado: `modules/web_admin.py` ahora sirve `TangerineUI` directamente. `neo-web.service` eliminado).

## 🔄 Rebranding (Neo -> WatermelonD)

La prioridad actual es eliminar las referencias antiguas para evitar confusión.

- [ ] **Renombrado del Core**:
    - [ ] `NeoCore.py` -> `WatermelonCore.py` (Clase principal y archivo).
    - [ ] Actualizar imports en `start.sh` y servicios systemd.
- [ ] **Servicios Systemd**:
    - [ ] Renombrar `neo.service` -> `watermelon.service` (Nombre interno actualizado, falta renombre de archivo).
    - [ ] Renombrar `neo-web.service` -> `watermelon-web.service` (Eliminado).
- [ ] **Script de Instalación (`install.sh`)**:
    - [ ] Cambiar textos de salida ("Instalador Unificado Neo Papaya" -> "WatermelonD Installer").
    - [ ] Actualizar rutas de logs y nombres de variables de entorno (`NEO_API_URL` -> `WATERMELON_API_URL`).

## 📚 Documentación

Sincronizar la documentación técnica con la nueva arquitectura.

- [ ] **Actualizar Referencias**:
    - [x] `README.md` actualizado con Lime (Flan-T5).
    - [ ] Barrido en `priv_docs/` para eliminar referencias a "Papaya" obsoletas.
- [ ] **Nuevas Guías**:
    - [ ] Documentar el uso del nuevo **Decision Router**.
    - [ ] Guía de migración para usuarios existentes (Neo -> Watermelon).

## 🛠️ Calidad de Código y Mantenimiento

- [ ] **Limpieza de Git**:
    - [x] Eliminar `__pycache__` de `BlueberrySkills`.
- [ ] **Testing**:
    - [ ] Crear estructura `tests/` con `pytest`.
    - [ ] Añadir tests unitarios para `BrainNut` y `DecisionRouter`.
- [ ] **Gestión de Configuración**:
    - [ ] Unificar carga de configuración (asegurar que `config/config.json` sea la única fuente de verdad).
- [ ] **Dependencias**:
    - [ ] Revisar `requirements.txt` para eliminar librerías no usadas (limpieza post-refactor).
    - [ ] Fijar versiones de librerías clave (`torch`, `transformers`) para estabilidad.

## 🚀 Features y Mejoras Técnicas

- [ ] **Validación de Lime**:
    - [ ] Verificar rendimiento de inferencia de Lime en entornos reales.
    - [ ] Ajustar prompts de "retry" si Lime es más verboso que Mango.
- [ ] **Seguridad**:
    - [ ] Revisar permisos de ejecución de comandos generados por AI.
    - [ ] Implementar sandbox más estricto para `exec()`.
- [ ] **Backup**:
    - [ ] Script automático para backup de `brain` (base de datos vectorial) y configuración.
- [ ] **Monitorización**:
    - [ ] Añadir sección de "Salud del Sistema" en `TangerineUI` (CPU/RAM en tiempo real).

## 🐛 Bugs Conocidos

- [ ] `install.sh`: La detección de repositorio git a veces falla en subdirectorios anidados.
- [ ] `VoiceManager`: Conflictos ocasionales con PulseAudio/PipeWire al iniciar.
