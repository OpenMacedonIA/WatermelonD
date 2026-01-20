# ANEXO I: MANUAL DE USUARIO Y ADMINISTRACIÓN
# PROYECTO WatermelonD

**Versión del Documento:** 1.2
**Fecha:** 02/12/2025
**Proyecto:** WatermelonD (Copiloto de Lenguaje para Entornos de Grupo y Administración)

---

## ÍNDICE DE CONTENIDOS

1. [INTRODUCCIÓN](#1-introducción)
 1.1. Propósito del Documento
 1.2. Audiencia Objetivo
 1.3. Alcance del Sistema
 1.4. Glosario de Términos

2. [INSTALACIÓN Y DESPLIEGUE](#2-instalación-y-despliegue)
 2.1. Requisitos del Sistema
 2.1.1. Hardware
 2.1.2. Software
 2.2. Preparación del Entorno
 2.3. Proceso de Instalación Automatizada
 2.4. Verificación de la Instalación
 2.5. Configuración del Modo Kiosk (Interfaz Visual)

3. [CONFIGURACIÓN DEL SISTEMA](#3-configuración-del-sistema)
 3.1. Archivo de Configuración Principal (`config.json`)
 3.2. Personalización de la Palabra de Activación (Wake Word)
 3.3. Configuración de Modelos de IA
 3.4. Configuración de Red y MQTT
 3.5. Gestión de Usuarios y Permisos

4. [MANUAL DE USUARIO](#4-manual-de-usuario)
 4.1. Interacción por Voz
 4.1.1. Comandos de Sistema
 4.1.2. Comandos de Red y SSH
 4.1.3. Comandos de Organización (Calendario, Alarmas)
 4.1.4. Comandos Multimedia
 4.2. Interacción Conversacional (Gemma 2B)
 4.3. Interfaz Visual (Web UI)
 4.3.1. Estados de la "Cara"
 4.3.2. Notificaciones y Alertas
 4.4. Uso del Explorador de Archivos

5. [MANUAL DE ADMINISTRACIÓN](#5-manual-de-administración)
 5.1. Gestión del Servicio `systemd`
 5.2. Monitorización y Logs
 5.3. Gestión de Redes (Network Bros)
 5.4. Administración Remota (SSH Manager)
 5.5. Seguridad y "Guard"
 5.6. Mantenimiento y Actualizaciones

6. [SOLUCIÓN DE PROBLEMAS (TROUBLESHOOTING)](#6-solución-de-problemas)
 (Ver ANEXO IV)

7. [GUÍA DE DESARROLLO (EXTENSIÓN DE SKILLS)](#7-guía-de-desarrollo)
 (Ver ANEXO V)

8. [CONFIGURACIÓN AVANZADA](#8-configuración-avanzada)
 8.1. Ajuste Fino de Vosk
 8.2. Personalización de la UI Web
 8.3. Parámetros Ocultos

9. [SEGURIDAD AVANZADA](#9-seguridad-avanzada)
 9.1. Hardening del Sistema Operativo
 9.2. Configuración de Firewall (UFW)
 9.3. Auditoría de Accesos

10. [GLOSARIO TÉCNICO EXTENDIDO](#10-glosario-técnico-extendido)
 10.1. Términos de IA
 10.2. Términos de Redes
 10.3. Términos del Sistema

11. [LICENCIA Y CRÉDITOS](#11-licencia-y-créditos)
 11.1. Licencia del Proyecto
 11.2. Librerías Open Source Utilizadas

12. [ANEXOS](#12-anexos)
 12.1. Referencia Rápida de Comandos
 12.2. Estructura de Directorios

---

## 1. INTRODUCCIÓN

### 1.1. Propósito del Documento
El presente documento, **ANEXO I: Manual de Usuario y Administración**, tiene como objetivo proporcionar una guía exhaustiva y detallada para la instalación, configuración, uso y administración del sistema **WatermelonD**. Este manual sirve como referencia tanto para usuarios finales que interactúan con el asistente como para administradores de sistemas encargados de su despliegue y mantenimiento.

### 1.2. Audiencia Objetivo
Este manual está dirigido a dos tipos de usuarios principales:
* **Usuarios Finales:** Personas que utilizarán el asistente para tareas cotidianas, consultas de información, control domótico y gestión básica.
* **Administradores de Sistemas (SysAdmins):** Personal técnico responsable de la instalación en hardware específico (Raspberry Pi, Mini PCs), configuración de red, integración con otros dispositivos y resolución de incidencias técnicas.
* **Desarrolladores:** Programadores que deseen extender la funcionalidad del asistente mediante nuevos módulos o "Skills".

### 1.3. Alcance del Sistema
WatermelonD es un asistente personal híbrido que combina:
* **Control Determinista:** Ejecución precisa de comandos para tareas críticas (apagar sistema, conectar SSH, gestionar archivos).
* **Inteligencia Generativa:** Uso de un LLM local (Gemma 2B) para mantener conversaciones naturales, responder preguntas complejas y ofrecer una personalidad definida.
* **Gestión de Infraestructura:** Herramientas integradas para el escaneo de redes, gestión de servidores remotos y monitorización de servicios.

### 1.4. Glosario de Términos
* **Wake Word:** Palabra clave que activa la escucha del asistente (ej. "WatermelonD", "Tío").
* **LLM (Large Language Model):** Modelo de lenguaje grande (Gemma 2B) utilizado para generar texto.
* **STT (Speech-to-Text):** Tecnología de reconocimiento de voz (Vosk/Whisper).
* **TTS (Text-to-Speech):** Tecnología de síntesis de voz (Piper).
* **MQTT:** Protocolo de mensajería ligera usado para la comunicación entre agentes ("Network Bros").
* **Kiosk Mode:** Modo de ejecución del navegador a pantalla completa para mostrar la interfaz visual.
* **Skill:** Módulo de software que añade una capacidad específica al asistente (ej. Skill de Spotify, Skill de Domótica).

---

## 2. INSTALACIÓN Y DESPLIEGUE

### 2.1. Requisitos del Sistema

Para garantizar un funcionamiento fluido, especialmente del modelo LLM Gemma 2B, se deben cumplir los siguientes requisitos.

#### 2.1.1. Hardware
* **Procesador (CPU):**
 * Arquitectura: ARM64 (Raspberry Pi 4/5) o x86_64 (PC/Portátil).
 * Instrucciones: Se recomienda soporte para **AVX2** en x86 para mejorar la inferencia del LLM.
 * Núcleos: Mínimo 4 núcleos físicos.
* **Memoria RAM:**
 * Mínimo absoluto: 4 GB (El sistema funcionará, pero Gemma será lento y podría sufrir *swapping*).
 * Recomendado: **8 GB** o más para una experiencia fluida con el LLM cargado en memoria.
* **Almacenamiento:**
 * Tipo: **SSD** (SATA o NVMe) altamente recomendado. Las tarjetas SD estándar pueden causar cuellos de botella severos durante la carga de modelos y escritura de logs.
 * Espacio: Mínimo 16 GB libres. Se recomienda 32 GB o más para almacenar modelos, bases de datos y logs.
* **Periféricos de Audio:**
 * Micrófono: USB de buena calidad o HAT para Raspberry Pi (ej. ReSpeaker).
 * Altavoces: Salida Jack 3.5mm, HDMI o USB.

#### 2.1.2. Software
* **Sistema Operativo:**
 * **Debian 11/12 (Bullseye/Bookworm)**: Recomendado para estabilidad.
 * **Ubuntu 22.04/24.04 LTS**: Totalmente soportado.
 * **Raspberry Pi OS (64-bit)**: Esencial usar la versión de 64 bits para soportar los modelos de IA modernos.
 * **Fedora 38+**: Soportado experimentalmente.
* **Dependencias Base:** `git`, `curl`, `python3`.

### 2.2. Preparación del Entorno

Antes de iniciar la instalación, asegúrese de que el sistema esté actualizado y tenga configurada la red.

1. **Actualizar el sistema:**
 ```bash
 sudo apt update && sudo apt upgrade -y
 ```

2. **Instalar Git:**
 ```bash
 sudo apt install git -y
 ```

3. **Clonar el Repositorio:**
 Descargue el código fuente en el directorio de usuario (se recomienda no usar `root` para la descarga).
 ```bash
 cd ~
 git clone https://github.com/jrodriiguezg/WatermelonD.git
 cd WatermelonD
 ```

### 2.3. Proceso de Instalación Automatizada

WatermelonD incluye un script `install.sh` que automatiza la configuración. Este script realiza las siguientes acciones:
1. Detecta el gestor de paquetes (`apt` o `dnf`).
2. Instala dependencias del sistema (compiladores, librerías de audio, herramientas de red).
3. Instala y configura **Pyenv** para gestionar la versión de Python.
4. Instala **Python 3.10** (versión requerida para compatibilidad con ciertas librerías de IA).
5. Crea un entorno virtual (`venv`) e instala las dependencias de Python (`requirements.txt`).
6. Descarga los modelos necesarios:
 * Vosk (Reconocimiento de voz).
 * Piper (Síntesis de voz).
 * Gemma 2B (LLM).
 * Faster-Whisper (Opcional, para mayor precisión).
7. Configura el servicio `systemd` para ejecución en segundo plano.

**Ejecución del Script:**
```bash
chmod +x install.sh
./install.sh
```
*Nota: El script solicitará la contraseña de `sudo` para instalar paquetes del sistema.*

### 2.4. Verificación de la Instalación

Una vez finalizado el script, verifique que todo esté correcto:

1. **Comprobar el servicio:**
 ```bash
 systemctl --user status neo.service
 ```
 Debe aparecer como `active (running)`.

2. **Verificar Logs en tiempo real:**
 ```bash
 journalctl --user -u neo.service -f
 ```
 Busque mensajes como "WatermelonD Core iniciado", "Modelos cargados correctamente".

3. **Prueba de Audio:**
 El sistema debería emitir un sonido de inicio o un saludo verbal si los altavoces están configurados correctamente.

### 2.5. Configuración del Modo Kiosk (Interfaz Visual)

Si dispone de una pantalla conectada, el instalador puede configurar un modo "Kiosk" para mostrar la cara del asistente automáticamente al inicio.

El script configura:
* Auto-login en la terminal `tty1`.
* Inicio automático del servidor gráfico (`startx`).
* Lanzamiento de `Chromium` en modo pantalla completa apuntando a `http://localhost:5000/face`.

Para activar/desactivar esto manualmente, revise el archivo `~/.xinitrc`.

---

## 3. CONFIGURACIÓN DEL SISTEMA

### 3.1. Archivo de Configuración Principal (`config.json`)

Toda la configuración reside en `config/config.json`. Este archivo es un JSON estándar que puede editarse con cualquier editor de texto.

**Estructura Básica:**
```json
{
 "secret_key": "...",
 "stt": {
 "engine": "vosk",
 "input_device_index": 10
 },
 "web_admin": {
 "host": "0.0.0.0",
 "port": 5000,
 "debug": false
 },
 "audio": {
 "jack_no_start_server": "1",
 "driver": "alsa"
 },
 "ai_model_path": "models/gemma-2b-it-q4_k_m.gguf",
 "experimental": {
 "voice_auth_enabled": false
 },
 "mqtt": {
 "broker": "localhost",
 "port": 1883
 }
}
```
```

### 3.2. Personalización de la Palabra de Activación (Wake Word)

Para cambiar el nombre al que responde el asistente:
1. Edite `config/config.json`.
2. Modifique el valor de `"wake_word"`. Puede ser una lista de palabras.
 ```json
 "wake_word": ["WatermelonD", "tío", "robot"]
 ```
3. Reinicie el servicio:
 ```bash
 systemctl --user restart neo.service
 ```

### 3.3. Configuración de Modelos de IA

* **LLM (Gemma):** La ruta al modelo `.gguf` se define en `ai_model_path`. Si desea usar un modelo diferente (ej. TinyLlama), descargue el archivo `.gguf` en la carpeta `models/` y actualice la ruta.
* **Voz (Piper):** Los modelos de voz se encuentran en `piper/`. Para cambiar la voz, debe descargar el modelo `.onnx` y su `.json` correspondiente, y actualizar las referencias en el código o configuración (actualmente la selección de voz suele estar hardcodeada en `Speaker.py` o config, revisar `modules/speaker.py`).

### 3.4. Configuración de Red y MQTT

WatermelonD utiliza MQTT para comunicarse con otros dispositivos ("Network Bros").
* **Broker:** Por defecto usa `localhost`. Si tiene un broker central en la red, cambie `"broker": "IP_DEL_BROKER"`.
* **Topic Base:** Los agentes publican en `home/agents/{hostname}/...`.

### 3.5. Gestión de Usuarios y Permisos

El asistente se ejecuta en el espacio de usuario (User Mode). Esto es más seguro que ejecutarlo como `root`. Sin embargo, algunas acciones (como `shutdown` o `reboot`) requieren permisos.
* Asegúrese de que el usuario tenga permisos de `sudo` sin contraseña para comandos específicos si es necesario, o utilice `polkit` para gestionar permisos de apagado/reinicio.

---

## 4. MANUAL DE USUARIO

### 4.1. Interacción por Voz

La forma principal de interactuar es mediante la voz. Diga la palabra de activación seguida del comando.

#### 4.1.1. Comandos de Sistema
* **Apagar/Reiniciar:** "WatermelonD, apaga el sistema", "WatermelonD, reinicia el ordenador".
* **Estado:** "WatermelonD, ¿cómo estás?", "WatermelonD, dame un diagnóstico del sistema".
* **Volumen:** "WatermelonD, sube el volumen", "WatermelonD, silencio".

#### 4.1.2. Comandos de Red y SSH
* **IP Pública:** "WatermelonD, ¿cuál es mi IP pública?".
* **Escaneo de Red:** "WatermelonD, escanea la red en busca de intrusos".
* **Ping:** "WatermelonD, haz un ping a google.com".
* **SSH:** "WatermelonD, conéctate al servidor principal", "WatermelonD, ejecuta 'ls -la' en el servidor".

#### 4.1.3. Comandos de Organización
* **Hora/Fecha:** "¿Qué hora es?", "¿Qué día es hoy?".
* **Alarmas:** "Pon una alarma a las 8 de la mañana".
* **Temporizadores:** "Pon un temporizador de 10 minutos para la pasta".
* **Recordatorios:** "Recuérdame comprar leche mañana a las 5".
* **Calendario:** "¿Qué tengo en la agenda para hoy?".

#### 4.1.4. Comandos Multimedia
* **Radio:** "Pon la radio", "Pon Rock FM".
* **Cast:** "Envía este video a la tele del salón".

#### 4.1.5. Comandos de Contenedores (Docker)
Ahora potenciados por **MANGO T5**, lo que permite una mayor flexibilidad en el lenguaje natural.
* **Estado:** "¿Qué contenedores hay?", "Dime los dockers activos", "Lista de contenedores". (MANGO interpretará tu intención y ejecutará el comando `docker ps` adecuado).
* **Gestión:** "Reinicia el contenedor pihole", "Para el contenedor de base de datos".
 * *Nota:* Comandos críticos requerirán confirmación ("¿Seguro que quieres reiniciar...?").

#### 4.1.6. Filtrado Inteligente de Salida (Smart Output)
WatermelonD procesa inteligentemente las respuestas largas de comandos para no saturar el canal de voz:
* **Listas (`ls`):** Si hay muchos archivos, dirá el total y leerá solo los primeros 3.
* **Logs:** Leerá solo las últimas 2 líneas para dar el contexto más reciente.
* **Salidas Extensas:** Si el resultado supera los 400 caracteres, lo guardará automáticamente en un archivo de texto y te avisará de su ubicación, en lugar de leerlo entero.

### 4.2. Interacción Conversacional (Gemma 2B)

Si el comando no coincide con una instrucción predefinida, WatermelonD usará su "cerebro" (Gemma 2B) para responder.
* **Preguntas generales:** "¿Quién fue Nikola Tesla?", "¿Cuál es la capital de Australia?".
* **Conversación:** "Hola, ¿qué tal te sientes hoy?", "Cuéntame un chiste".
* **Razonamiento:** "Tengo tres manzanas y me como una, ¿cuántas quedan?".

*Nota: Las respuestas generativas pueden tardar unos segundos dependiendo del hardware.*

### 4.3. Interfaz Visual (Web UI)

La interfaz web (`http://localhost:5000/face`) ha sido rediseñada con el tema **"Cosmic"**, una estética moderna con efectos de cristal (glassmorphism).

#### 4.3.1. Características de la Interfaz
* **Tema Adaptable:** Botón en la cabecera (Sol/Luna) para alternar instantáneamente entre **Modo Oscuro** (tonos violetas profundos) y **Modo Claro** (tonos grises y azules suaves).
* **Estados de la "Cara":**
 * **Idle (Reposo):** Ojos parpadeando suavemente. Esperando comando.
 * **Listening (Escuchando):** Ojos abiertos o indicador visual activo. El sistema está capturando audio.
 * **Thinking (Pensando):** Animación de carga. El LLM está procesando la respuesta.
 * **Speaking (Hablando):** La boca (si la hay) o los ojos se mueven al ritmo de la voz.
* **Responsividad:** La barra lateral y paneles como el explorador de archivos se adaptan automáticamente a móviles y tablets.

#### 4.3.2. Notificaciones y Alertas
Las alertas del sistema (ej. "CPU caliente", "Intruso detectado en red") aparecen como pop-ups superpuestos en la interfaz visual.

### 4.4. Uso del Explorador de Archivos

WatermelonD permite buscar archivos localmente.
* **Búsqueda:** "Busca el archivo 'presupuesto.pdf'".
* **Lectura:** "Léeme el archivo 'notas.txt'".

### 4.5. Gestión del Conocimiento (RAG)
WatermelonD puede aprender de tus documentos.
1. Ve a la web `http://localhost:5000/knowledge`.
2. Arrastra archivos `.pdf`, `.txt` o `.md` al área de subida.
3. Pulsa el botón **"Entrenar / Re-indexar"**.
4. Después, puedes preguntar sobre el contenido: "¿Qué dice el manual sobre la seguridad?".

---

## 5. MANUAL DE ADMINISTRACIÓN

### 5.1. Gestión del Servicio `systemd`

El servicio se llama `neo.service` y corre a nivel de usuario.

* **Iniciar:** `systemctl --user start neo.service`
* **Detener:** `systemctl --user stop neo.service`
* **Reiniciar:** `systemctl --user restart neo.service`
* **Ver Estado:** `systemctl --user status neo.service`
* **Habilitar al inicio:** `systemctl --user enable neo.service`

### 5.2. Monitorización y Logs

Los logs son vitales para el diagnóstico. Se almacenan en `logs/` y en el journal del sistema.
* **Ver logs en vivo:** `journalctl --user -u neo.service -f`
* **Rotación de logs:** El sistema gestiona automáticamente los archivos en `logs/` para no llenar el disco, pero se recomienda revisarlos periódicamente.

### 5.3. Gestión de Redes (Network Bros)

El módulo `NetworkManager` y `MQTTManager` permiten la interoperabilidad.
* **Añadir nuevos agentes:** Simplemente configure otro dispositivo con un cliente MQTT que publique en el topic `home/agents/NUEVO_AGENTE/status`. WatermelonD lo detectará automáticamente.
* **Seguridad:** Revise `modules/guard.py` para configurar reglas de bloqueo de IPs o alertas de escaneo de puertos.

### 5.4. Administración Remota (SSH Manager)

Los perfiles SSH se guardan (cifrados o en texto plano según configuración) en la base de datos o JSON.
* **Añadir servidor:** Actualmente se realiza editando la configuración o mediante comandos de voz si la función de "aprender servidor" está habilitada.
* **Seguridad:** Las claves SSH deben gestionarse mediante `ssh-agent` del sistema operativo para evitar guardar contraseñas en texto plano.

### 5.5. Seguridad y "Guard"

El módulo `Guard` monitorea logs del sistema (ej. `/var/log/auth.log`) en busca de intentos fallidos de acceso.
* **Configuración:** En `config.json` puede definir el umbral de intentos fallidos antes de lanzar una alerta.
* **Alertas:** Las alertas se anuncian por voz y se muestran en la UI.

### 5.7. Gestión de Contenedores (Docker)
En `http://localhost:5000/docker` encontrará un panel dedicado:
* Visualización de contenedores activos/inactivos.
* Botones de control rápido (Start, Stop, Restart).
* **Logs en tiempo real:** Haga clic en "Logs" para depurar problemas sin abrir una terminal.

### 5.6. Mantenimiento y Actualizaciones

#### Opción A: Desde la Web (Recomendado)
1. Vaya a la sección **Acciones** de la interfaz web.
2. Pulse el botón **"Actualizar WatermelonD"**.
3. El sistema descargará los cambios (`git pull`) y se reiniciará automáticamente.

#### Opción B: Manual (Terminal)
1. Vaya al directorio del proyecto: `cd ~/WatermelonD`
2. Descargue cambios: `git pull`
3. Si hay cambios en dependencias: `source venv/bin/activate && pip install -r requirements.txt`
4. Reinicie el servicio: `systemctl --user restart neo.service`

---

## 6. SOLUCIÓN DE PROBLEMAS (TROUBLESHOOTING)

> **Nota:** Esta sección se ha movido a un documento dedicado para facilitar su consulta.
> Por favor, consulte el **[ANEXO IV: RESOLUCIÓN DE PROBLEMAS](ANEXO_IV_RESOLUCION_DE_PROBLEMAS.md)** para ver la guía completa de solución de problemas de audio, voz, conectividad y errores de IA.

---

## 7. GUÍA DE DESARROLLO (EXTENSIÓN DE SKILLS)

> **Nota:** La guía de desarrollo se ha expandido y movido a su propio documento.
> Por favor, consulte el **[ANEXO V: PROGRAMACIÓN Y CREACIÓN DE SKILLS](ANEXO_V_PROGRAMACION_Y_SKILLS.md)** para aprender a crear nuevas habilidades, registrar intents e interactuar con el núcleo del sistema.

---

## 8. CONFIGURACIÓN AVANZADA

### 8.1. Ajuste Fino de Vosk

El reconocimiento de voz usa Vosk. Puede ajustar su comportamiento en `modules/voice_manager.py`.
* **Sample Rate:** Por defecto 16000Hz. Si su micrófono soporta 44100Hz o 48000Hz, puede intentar cambiarlo, pero asegúrese de que el modelo Vosk lo soporte.
* **Gramática:** Puede restringir el vocabulario pasando una lista de palabras al constructor del modelo (función avanzada, requiere modificar código).

### 8.2. Personalización de la UI Web

La interfaz web puede personalizarse de dos formas:
* **Desde Ajustes (Fácil):** Vaya a **Ajustes > Apariencia** e introduzca su código CSS en el campo "CSS Personalizado". Esto permite cambiar colores, fuentes y ocultar elementos sin tocar archivos.
* **Archivos Fuente (Avanzado):** Modifique directamente `TangerineUI/templates/base.html` o los archivos en `TangerineUI/static/css/` para cambios estructurales profundos.
* **Imágenes:** Reemplace los archivos en `TangerineUI/static/images/` para cambiar los avatares o iconos.

### 8.3. Parámetros Ocultos

Algunos parámetros no están en `config.json` por defecto pero pueden añadirse:
* `"debug_mode": true`: Habilita logs más verbosos en consola.
* `"tts_engine": "espeak"`: Fuerza el uso de Espeak si Piper falla.

---

## 9. SEGURIDAD AVANZADA

### 9.1. Hardening del Sistema Operativo

Dado que WatermelonD tiene capacidades de administración (SSH, apagado), es crucial asegurar el host.
1. **Deshabilitar Root SSH:** Edite `/etc/ssh/sshd_config` y establezca `PermitRootLogin no`.
2. **Actualizaciones Automáticas:** Instale `unattended-upgrades` para parches de seguridad.
 ```bash
 sudo apt install unattended-upgrades
 ```

### 9.2. Configuración de Firewall (UFW)

Se recomienda usar `ufw` para cerrar puertos innecesarios.
```bash
sudo apt install ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh# Puerto 22
sudo ufw allow 1883/tcp# MQTT
sudo ufw allow 5000/tcp# Web UI
sudo ufw enable
```

### 9.3. Auditoría de Accesos

Revise regularmente quién accede al sistema.
* Comando `last`: Muestra los últimos inicios de sesión.
* Comando `lastb`: Muestra intentos de inicio de sesión fallidos.
* El módulo `Guard` de WatermelonD automatiza parte de esto, pero la revisión manual es insustituible.

---

## 10. GLOSARIO TÉCNICO EXTENDIDO

### 10.1. Términos de IA
* **Cuantización (Quantization):** Proceso de reducir la precisión de los números en un modelo (ej. de 16-bit a 4-bit) para reducir el uso de memoria y acelerar la inferencia, con una mínima pérdida de calidad.
* **Inferencia:** El proceso de usar un modelo entrenado para hacer predicciones o generar texto.
* **Context Window:** La cantidad de texto (tokens) que el modelo puede "recordar" de la conversación actual.
* **Temperatura:** Parámetro que controla la creatividad de las respuestas. Valores altos (0.8+) producen respuestas más variadas; valores bajos (0.2) más deterministas.

### 10.2. Términos de Redes
* **Broker MQTT:** Servidor central que recibe y distribuye mensajes entre dispositivos IoT.
* **Payload:** El contenido útil de un mensaje (ej. el comando JSON enviado por MQTT).
* **Port Scanning:** Técnica para descubrir puertos abiertos en un host, usada por el módulo de seguridad para detectar vulnerabilidades.
* **Latency (Latencia):** El tiempo que tarda un paquete de datos en viajar de un punto a otro.

### 10.3. Términos del Sistema
* **Daemon:** Un programa que se ejecuta en segundo plano (como `neo.service`).
* **Virtual Environment (venv):** Un entorno aislado de Python que evita conflictos entre librerías de diferentes proyectos.
* **Swap:** Espacio en disco usado como memoria RAM virtual cuando la RAM física se agota.

---

## 11. LICENCIA Y CRÉDITOS

### 11.1. Licencia del Proyecto
Este proyecto se distribuye bajo la licencia **GNU General Public License v3.0 (GPLv3)**. Esto garantiza que el software sea libre para usar, estudiar, compartir y modificar.

### 11.2. Librerías Open Source Utilizadas
WatermelonD es posible gracias al gigante ecosistema de código abierto:
* **Vosk:** Reconocimiento de voz offline.
* **Piper:** Síntesis de voz neuronal rápida.
* **Llama.cpp / Python-llama-cpp:** Inferencia eficiente de LLMs.
* **Flask:** Servidor web ligero.
* **Paho-MQTT:** Cliente MQTT para Python.
* **PyAudio:** Grabación y reproducción de audio.

---

## 12. ANEXOS

### 12.1. Referencia Rápida de Comandos

| Categoría | Comando Ejemplo | Acción |
| :--- | :--- | :--- |
| **Sistema** | "Apaga el sistema" | Inicia secuencia de apagado. |
| **Sistema** | "Reinicia el servicio" | Reinicia `neo.service`. |
| **Red** | "¿Cuál es mi IP?" | Dice la IP local y pública. |
| **Red** | "Escanea la red" | Ejecuta nmap rápido. |
| **SSH** | "Conecta al servidor X" | Inicia sesión SSH. |
| **Tiempo** | "¿Qué hora es?" | Dice la hora actual. |
| **Alarma** | "Alarma en 5 minutos" | Crea una alarma. |
| **Multimedia** | "Pon música" | Reproduce radio/música aleatoria. |
| **General** | "Cuéntame algo" | LLM genera un dato curioso. |
| **Archivos** | "Busca informe.pdf" | Busca en el directorio home. |
| **Archivos** | "Lee notas.txt" | Lee el contenido por TTS. |

### 12.2. Estructura de Directorios

* `~/WatermelonD/`
 * `WatermelonD.py`: Archivo principal.
 * `config/`:
 * `config.json`: Configuración general.
 * `intents.json`: Definición de comandos.
 * `skills.json`: Configuración de skills.
 * `modules/`:
 * `skills/`: Lógica de habilidades.
 * `voice_manager.py`: STT.
 * `speaker.py`: TTS.
 * `ai_engine.py`: LLM Wrapper.
 * `models/`: Modelos de IA (GGUF, Vosk).
 * `logs/`: Archivos de registro.
 * `docs/`: Documentación.
 * `web/`: Archivos de la interfaz web (HTML/CSS/JS).
 * `venv/`: Entorno virtual de Python.

---
**Fin del Documento**
