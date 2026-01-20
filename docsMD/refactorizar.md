# Documentación de Refactorización: NEOPapaya (SysAdmin Edition)

Este documento detalla el proceso completo de refactorización llevado a cabo para transformar el proyecto **NEOPapaya** de un Asistente de Cuidado de Mayores a un **Asistente de Administración de Sistemas (SysAdmin)**.

## 1. Visión General del Cambio

El objetivo principal fue pivotar la funcionalidad del asistente. Originalmente diseñado para interactuar con personas mayores (recordatorios de pastillas, detección de caídas, interfaz táctil simple), el sistema ahora está optimizado para usuarios técnicos (administradores de sistemas) que requieren monitorización, control de servicios y ejecución de comandos, tanto por voz como a través de una interfaz web profesional.

### Principios de Diseño
* **Headless First**: Eliminación de la dependencia de una pantalla conectada directamente (GUI local). El sistema debe funcionar como un servicio en segundo plano.
* **Accesibilidad Dual**: Control total tanto por comandos de voz (Vosk) como por interfaz web remota (Flask).
* **Profesionalidad**: La interfaz web debe ser seria, oscura y funcional, alejándose de la estética "amigable/infantil" anterior.
* **Portabilidad**: Compatibilidad garantizada tanto en Raspberry Pi (Debian) como en estaciones de trabajo (Fedora).

---

## 2. Elementos Eliminados

Para aligerar el código y eliminar funcionalidades obsoletas para el nuevo propósito, se procedió a borrar los siguientes componentes:

### 2.1. Interfaz Gráfica Local (Tkinter)
* **Archivo eliminado**: `NeoTK.py`
* **Justificación**: Un administrador de sistemas accede a los servidores remotamente (SSH, Web). Mantener una GUI local consumía recursos innecesarios y requería un entorno de escritorio activo.

### 2.2. Funcionalidades de Cuidado de Mayores
* **Archivos eliminados**:
 * `pill_manager.py`: Gestor de tomas de medicamentos.
 * `modules/contacts.py`: Agenda de contactos para llamadas de emergencia.
 * `modules/safety_manager.py`: Lógica de alertas de seguridad.
 * `jsons/pastillero.json` y `jsons/datos_emergencia.json`.
* **Justificación**: Estas funciones son irrelevantes para la administración de servidores.

### 2.3. Sensor de Video y Detección de Caídas
* **Archivo eliminado**: `video_sensor.py`
* **Dependencias eliminadas**: `opencv-python`, `mediapipe`.
* **Justificación**: El análisis de video en tiempo real es intensivo en CPU. Un asistente de SysAdmin no necesita "ver" al usuario, sino "escuchar" comandos y monitorizar el hardware. Esto liberó significativos recursos del sistema.

---

## 3. Nuevas Funcionalidades Implementadas

### 3.1. Módulo de Administración del Sistema (`modules/sysadmin.py`)
Se creó un nuevo módulo dedicado a interactuar con el sistema operativo.
* **Funciones**:
 * `get_cpu_temp()`: Obtiene la temperatura de la CPU (compatible con Raspberry Pi y PC estándar).
 * `get_ram_usage()`: Porcentaje de uso de memoria.
 * `get_disk_usage()`: Espacio en disco raíz.
 * `get_services()`: Estado de servicios systemd (ssh, docker, nginx, etc.).
 * `control_service()`: Start/Stop/Restart de servicios (vía `sudo`).
 * `run_command()`: Ejecución segura de comandos de shell con timeout.

### 3.2. Consola de Administración Web (`modules/web_admin.py`)
Se implementó un servidor web completo utilizando **Flask**.
* **Características**:
 * **Autenticación**: Login protegido con usuario/contraseña configurables.
 * **Dashboard**: Vista en tiempo real de métricas del sistema.
 * **Terminal Web**: Emulador de terminal con soporte para `cd` (cambio de directorio), historial de comandos y colores ANSI.
 * **Gestor de Servicios**: Interfaz gráfica para controlar demonios del sistema.
 * **Logs en Vivo**: Visualización de las últimas líneas del log de la aplicación.

### 3.3. Configuración Dinámica (`config.json`)
Se eliminaron las credenciales y configuraciones "hardcoded" (escritas en el código).
* **Nuevo archivo**: `config.json`
* **Contenido**: Usuario administrador, contraseña, y palabra de activación (Wake Word).
* **Ventaja**: Permite cambiar la configuración desde la interfaz web sin tocar el código fuente.

---

## 4. Refactorización del Núcleo (`WatermelonD.py`)

El archivo principal `WatermelonD.py` fue reescrito casi en su totalidad para soportar la nueva arquitectura concurrente.

### 4.1. Arquitectura de Hilos (Threading)
El sistema ahora ejecuta múltiples procesos ligeros en paralelo:
1. **Hilo Principal**: Bucle de eventos y orquestación.
2. **Hilo de Voz**: Escucha continua con Vosk.
3. **Hilo Web**: Servidor Flask (puerto 5000).
4. **Hilo Proactivo**: Tareas periódicas (alarmas, temporizadores).

### 4.2. Limpieza y Optimización
* **Imports**: Se eliminaron importaciones no utilizadas (`socket`, `subprocess` directo) y se organizaron las dependencias.
* **Docstrings**: Se añadió documentación interna a todas las clases y métodos para facilitar el mantenimiento futuro.
* **Manejo de Errores**: Se estandarizó el uso de `try-except` para evitar que un fallo en un módulo (ej. micrófono desconectado) tumbe toda la aplicación.

---

## 5. Conclusión

La refactorización ha transformado NEOPapaya en una herramienta robusta y profesional. El código es ahora más modular, fácil de mantener y eficiente, adecuado para su despliegue en entornos de producción o laboratorios domésticos (Homelab).
