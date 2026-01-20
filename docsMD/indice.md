# Índice del Proyecto (TFC) - Guía de Referencia (Normativa 25-26)

Este índice sigue estrictamente el **GUION PROYECTO 25-26** proporcionado. Utiliza los archivos indicados para completar cada sección de tu memoria.

---

## 1. Objetivo principal de tu proyecto
**Objetivo:** Desarrollar un asistente inteligente modular (NEOPapaya: Copiloto de Lenguaje para Entornos de Grupo y Administración) diseñado específicamente para optimizar tareas de administración de sistemas y gestión de infraestructuras IT, operando de forma 100% local para garantizar la soberanía de los datos.

El proyecto aborda la necesidad de una automatización inteligente capaz de ejecutar comandos complejos (Shell/Bash) mediante lenguaje natural, sin depender de APIs de terceros ni conexión a internet. A diferencia de los asistentes comerciales genéricos, NEOPapaya combina:
1.  **Inteligencia Híbrida:** Un motor de reglas determinista para acciones críticas (start/stop servicios) junto con Modelos de Lenguaje Pequeños (SLMs como Gemma 2B y MANGO T5) para razonamiento y comprensión contextual.
2.  **Seguridad Proactiva:** Módulos integrados (NEOPapayaGuard) para la detección de intrusiones y monitorización de anomalías en tiempo real.
3.  **Eficiencia en Recursos:** Optimización profunda para hardware de consumo (doble núcleo, 8GB RAM), permitiendo su despliegue en servidores perimetrales o estaciones de trabajo estándar.

Este enfoque permite a las empresas y administradores reducir la carga cognitiva en tareas repetitivas, mantener un control estricto sobre la privacidad de la información y disponer de una interfaz de operación multimodal (Voz, Web, Terminal) altamente personalizable.

- **Fuentes:**
  - `README.md` (Descripción principal).
  - `docs/resumen.md` (Visión general).

## 1.1. Herramientas a usar
**Objetivo:** Enumerar el stack tecnológico y las herramientas clave seleccionadas para el desarrollo.

*   **Lenguajes de Programación:**
    *   **Python 3.10+**: Lenguaje principal del Core (WatermelonD) y módulos de IA.
    *   **Bash/Shell**: Scripts de despliegue (`install.sh`) y automatización del sistema.
    *   **HTML5 / CSS3 / JavaScript (Vanilla)**: Interfaz web responsiva y ligera.
*   **Inteligencia Artificial (Local):**
    *   **Conversación (LLM):** Gemma 2B It (vía `llama-cpp-python` y GGUF 4-bit) para razonamiento y diálogo.
    *   **Comandos (T5):** MANGO T5 (vía `transformers`) para traducción precisa de Lenguaje Natural a Bash.
    *   **Voz (STT/TTS):** Vosk (offline ultrarrápido) y Whisper (precisión) para entrada; Piper TTS para síntesis de voz neural.
*   **Frameworks y Soluciones:**
    *   **Backend Web:** Flask y Flask-SocketIO para comunicación en tiempo real.
    *   **Visión Artificial:** OpenCV y `face_recognition` para detección biométrica (opcional en despliegue sysadmin).
    *   **Sistema:** `psutil` para métricas de hardware y `systemd` para gestión de demonios.
*   **Fuentes Detalladas:**
    - `docs/ANEXO_II_MANUAL_TECNICO_DE_DESPLIEGUE.md` (Stack completo).
    - `requirements.txt` (Hojas de dependencias exactas).

## 2. Antecedentes
**Objetivo:** Explicar el origen del proyecto, su filosofía y su evolución técnica.

NEOPapaya nace de la necesidad de un asistente personal, privado y autónomo, centrado en la administración de sistemas. La idea principal de su diseño es eliminar cualquier dependencia de la nube, garantizando que los datos pertenecen exclusivamente al usuario.

El desarrollo se fundamenta en tres pilares clave:
*   **Privacidad y Soberanía:** A diferencia de los asistentes comerciales, NEOPapaya se ejecuta 100% en local. No hay envío de audio ni telemetría externa.
*   **Eficiencia:** Diseñado para hardware modesto (desde Raspberry Pi hasta estaciones de trabajo), optimizando el uso de recursos para democratizar el acceso a asistentes inteligentes sin requerir GPUs costosas.
*   **Modularidad:** Arquitectura abierta basada en Python que permite ampliar funciones fácilmente.

**Evolución del Proyecto:**
Inicialmente concebido como *NEOPapaya* (un asistente para el cuidado de mayores), el proyecto pivotó hacia una herramienta técnica para administradores de sistemas (*SysAdmin AI*), refactorizando el código para eliminar dependencias gráficas (GUI) y centrarse en la operación "headless" y por consola.

- **Fuentes:**
    - `docs/refactorizar.md` (Historia del pivote de NEOPapaya a NEOPapaya).
    - `docs/evolucion.md` (Fases de desarrollo: Prototipo -> Modular -> IA Local).
    - `docs/resumen.md` (Filosofía de diseño).

## 3. Descripción del proyecto
**Objetivo:** Introducción general y objetivos.
- **Fuentes:**
    - `README.md` (Definición clara del proyecto).
    - `docs/resumen.md` (Visión general, justificación inicial).
    - `docs/manual_tecnico_completo.md` (Sección 1.1 Propósito).
    - `docs/refactorizar.md` (Evolución y pivote del proyecto SysAdmin).
    - `docs/evolucion.md` (Historial de cambios).

## 4. Descripción del entorno de trabajo
**Objetivo:** Entorno socioeconómico, empresa ficticia/real, mercado laboral.
- **Fuentes (NUEVO):**
    - `docs/contexto_empresarial.md` (Guía generada para este apartado).
**Modelo de Negocio:** Solución Open Source para entornos empresariales. El modelo se basa en ofrecer servicios profesionales de despliegue, implantación, soporte técnico y personalización a medida para clientes corporativos.

## 5. Estudio de necesidades
**Objetivo:** Requisitos de la empresa y expectativas que cubre el proyecto.
- **Fuentes:**
    - `docs/ANEXO_V_PROGRAMACION_Y_SKILLS.md` (Funcionalidades técnicas que cubren necesidades).
    - `docs/manual_tecnico_completo.md` (Listado de requisitos funcionales y no funcionales).
    - `docs/resumen.md` (Sección "Necesidad del Negocio" o similar).

## 6. Recursos necesarios
**Objetivo:** Hardware, Software, RRHH, Temporalización.
- **Fuentes:**
    - `docs/despliegue.md` (Lista de Hardware detallada).
    - `docs/ANEXO_II_MANUAL_TECNICO_DE_DESPLIEGUE.md` (Stack de Software).
    - *Temporalización:* Revisa tu propio diagrama de Gantt o usa los datos de `docs/roadmap.md` para estimar fases pasadas.

## 7. Propuesta técnica y justificación
**Objetivo:** Tecnologías, Herramientas, Seguridad, Justificación de decisiones.
- **Fuentes:**
    - `docs/architecture.md` (Arquitectura general).
    - `docs/ANEXO_III_ARQUITECTURA_E_IA.md` (Detalle profundo de IA y diseño).
    - `docs/systemsec.md` (Seguridad Hardware/Software - **Importante para apartado 7.2**).
    - `docs/MANGO.md` y `docs/MANGOv2.md` (Justificación de elección de modelo T5 vs otros).
    - `docs/IMPLANTACION_MANGOT5.md` (Detalles de integración técnica de Mango T5).
    - `docs/BrainNut.md` (Arquitectura de memoria y aprendizaje).
    - `docs/atackdb.md` (Base de datos de firmas de seguridad - NEOPapaya Guard).
    - `docs/web_interface.md` (Diseño de la Interfaz Web y UX).
    - `docs/whisper_manual.md` (Configuración y optimización de Voz/Whisper).
    - `docs/info.md` (Información general del sistema).
    - `docs/tio_personality.md` (Definición de personalidad del agente).
    - *Justificación general:* `docs/resumen.md` (Por qué local vs nube).

## 8. Implantación
**Objetivo:** Proceso de puesta en marcha, etapas, fases.
- **Fuentes:**
    - `docs/anexo_i_manual_usuario_admin.md` (Capítulo 1: Instalación).
    - `docs/ANEXO_II_MANUAL_TECNICO_DE_DESPLIEGUE.md` (Despliegue bajo nivel y compilación).
    - `docs/ANDROID_CLIENT_GUIDE.md` (Guía de despliegue de WebUI en Android).
    - `docs/MNB_guide.md` (Guía de nodos distribuidos MNB).

## 9. Conclusiones
**Objetivo:** Qué se ha logrado con el proyecto.
- **Fuentes (NUEVO):**
    - `docs/conclusiones.md` (Puntos clave sugeridos basados en el éxito del proyecto).

## 10. Propuestas de mejora
**Objetivo:** Futuras ampliaciones.
- **Fuentes:**
    - `docs/roadmap.md` (Futuro general).
    - `docs/WEB_UI_ROADMAP.md` (Mejoras de interfaz).
    - `docs/SKILLS_ROADMAP.md` (Nuevas habilidades).
    - `docs/ANEXO_VII_RETOS_DE_DESARROLLO.md` (Cosas que costaron y se podrían mejorar).

## 11. Fuentes utilizadas
**Objetivo:** Bibliografía y Webgrafía.
- **Fuentes:**
    - `docs/ANEXO_VIII_REFERENCIAS_Y_BIBLIOGRAFIA.md`.
    - `docs/fuentes.md`.

---

## 12. ANEXOS (Pruebas Obligatorias)

### Pruebas Realizadas (Obligatorio)
- **Fuente:** `docs/ANEXO_VI_PRUEBAS_REALIZADAS.md`.
- **Apoyo:** `docs/experiments.md`.

### Manual de Uso (Obligatorio)
- **Fuente:** `docs/anexo_i_manual_usuario_admin.md`.
- **Complementario:** `docs/knowledge_manual.md` (Manual de gestión de conocimiento).

### Resolución de Problemas (Obligatorio)
- **Fuente:** `docs/ANEXO_IV_RESOLUCION_DE_PROBLEMAS.md`.

### Glosario (Opcional pero recomendado en PDF)
- **Fuente:** `docs/GLOSARIO_TERMINOS_TECNICOS.md`.

### Otros Anexos Técnicos
- `docs/ANEXO_III_ARQUITECTURA_E_IA.md` (Para profundizar en la memoria si se queda corta).
