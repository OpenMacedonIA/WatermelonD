# NEOPapaya Face: Interfaz Visual Reactiva y Automatización

Hemos dotado a NEOPapaya de una "cara" digital estilo Robot/Emo, automatizado el arranque y optimizado el rendimiento.

## ¿Qué es NEOPapaya Face?
Es una interfaz web minimalista que muestra unos ojos digitales estilo OLED/Robot. Estos ojos reaccionan en tiempo real al estado del asistente:
- **Azul (Idle)**: Parpadean y miran alrededor aleatoriamente.
- **Verde (Escuchando)**: Se abren más y brillan intensamente cuando detectan la palabra clave ("NEOPapaya"/"Tío").
- **Morado (Pensando)**: Se contraen y pulsan mientras procesan tu comando.
- **Cyan (Hablando)**: Vibran al ritmo de la respuesta.

**Mejoras Visuales (Emo Style):**
- **Diseño Sólido**: Ojos rectangulares redondeados con brillo "glow" intenso.
- **Responsivo**: Se adapta a cualquier tamaño de pantalla (usa unidades relativas `vw`/`vh`).
- **Animaciones Suaves**: Movimientos robóticos fluidos.

**Optimizaciones de Rendimiento:**
- **Carga Instantánea**: CSS y JS integrados en un solo archivo (`face.html`) para minimizar peticiones.
- **Renderizado Previo**: El estado "Idle" se renderiza por CSS antes de que cargue el script.

## Cómo Usarlo (Método Automatizado)

Hemos creado un "Script Maestro" que se encarga de todo: limpiar procesos antiguos, arrancar el núcleo, esperar al servidor y lanzar la interfaz.

1. **Ejecución**:
 ```bash
 chmod +x start.sh
 ./start.sh
 ```

2. **¿Qué verás?**
 - Se abrirá el navegador en pantalla completa con los ojos de NEOPapaya.
 - En la terminal, verás los **logs avanzados en tiempo real** con colores.

## Solución de Problemas
- **El servidor web no arranca**: Hemos cambiado el modo de `SocketIO` a `threading` para evitar conflictos con el audio.
- **Logs**: Si algo falla, el script te mostrará los errores en rojo en la terminal principal.

## Detalles Técnicos
- **Tecnología**: HTML5/CSS3 + WebSockets (`flask-socketio`).
- **Automatización**: Bash scripting con gestión de PIDs y `tail` para logs.
- **Integración**: `NeoCore.py` emite eventos en tiempo real a través del servidor web integrado.
