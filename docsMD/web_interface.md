# NEOPapaya Web Interface (v3.0)

La interfaz web de **NEOPapaya v3.0** ha sido rediseñada para ser **independiente**, **robusta** y **personalizable**. Funciona como un cliente separado que se conecta a la API de `NeoCore`.

## Características Generales

- **Tecnología**: HTML5, Bootstrap 5, Vanilla JS (sin frameworks pesados).
- **Tema**: "Cosmic Dark" con efectos Glassmorphism.
- **Responsive**: Adaptada para Escritorio, Tabletas y Móviles.
- **Independencia**: Si el núcleo de la IA (`NeoCore`) se reinicia, la interfaz web permanece activa y muestra una pantalla de "Reconectando...".

## ️ Módulos Principales

### 1. Dashboard (`/`)
El centro de control principal.
- **Widgets Personalizables**: Puedes arrastrar y soltar las tarjetas (CPU, RAM, Micrófono) para ordenarlas a tu gusto. El orden se guarda automáticamente en tu navegador.
- **Control de Micrófono**: Activa o desactiva la escucha ("Stop Listening") con un clic.
- **Monitor de Sistema**: Visualización en tiempo real de CPU, RAM, Temperatura y Disco.

### 2. Terminal Web (`/terminal`)
Una consola completa en tu navegador.
- **Sesiones Persistentes**: El historial de comandos se guarda localmente.
- **Autocompletado**: Pulsa `Tab` para autocompletar nombres de archivos y directorios.
- **Ejecución Asíncrona**: Ejecuta comandos largos (`apt upgrade`) sin bloquear la interfaz.

### 3. Ajustes (`/settings`)
Configuración del sistema.
- **Actualizaciones**: Botón para comprobar y descargar la última versión de NEOPapaya desde GitHub.
- **Personalización**: Editor CSS integrado para cambiar colores o estilos.
- **Preferencias de Voz**: Selector de voz TTS (Piper) y modelo de IA.
- **Acerca de**: Información detallada de la versión y estado del sistema.

### 4. Sistema de Notificaciones
NEOPapaya v2.2 introduce un sistema de notificaciones unificado:
- **In-App Toasts**: Avisos visuales no intrusivos en la esquina inferior derecha.
- **Desktop Notifications**: Si das permiso, NEOPapaya te enviará notificaciones nativas a tu escritorio (útil si tienes la pestaña en segundo plano).

## Monitor de Conexión
La interfaz sondea continuamente el estado de `NeoCore`.
- **Online**: Todo funciona correctamente.
- **Offline / Reiniciando**: Aparecerá un overlay a pantalla completa bloqueando la interacción hasta que el sistema vuelva a estar en línea. ¡Ya no necesitas refrescar la página manualmente!

## Desarrollo
Los archivos de la interfaz se encuentran en:
- `web_client/templates/`: HTML (Jinja2).
- `web_client/static/`: CSS, JS e imágenes.
- `modules/web_admin.py`: Servidor Flask (Backend API).
