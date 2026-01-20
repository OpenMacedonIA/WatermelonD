# Guía de Despliegue: WatermelonD Nano

Esta guía detalla el proceso completo para desplegar **WatermelonD Nano** en un entorno Linux (Raspberry Pi OS, Debian, Ubuntu o Fedora).

## 1. Requisitos Previos

### Hardware Recomendado
* **Placa**: Raspberry Pi 4 (4GB+ RAM) / Orange Pi 5 / PC x86_64.
* **Almacenamiento**: Tarjeta SD o SSD con al menos 16GB libres.
* **Periféricos**:
 * Micrófono USB (Recomendado: ReSpeaker o Webcam USB con mic).
 * Altavoces (Jack 3.5mm o HDMI).
 * Webcam (Opcional, para WatermelonD Vision).

### Software Base
* **Sistema Operativo**:
 * Debian 11/12 (Bullseye/Bookworm).
 * Raspberry Pi OS (64-bit recomendado).
 * Fedora 38+ (Workstation o Server).
* **Acceso a Internet**: Requerido para la instalación (descarga de paquetes y modelos).
* **Usuario**: Un usuario no-root con permisos `sudo`.

## 2. Instalación Automatizada

El proyecto incluye un script `install.sh` que automatiza el 95% del proceso.

### Paso 2.1: Clonar el Repositorio

Abre una terminal y ejecuta:

```bash
cd ~
git clone https://github.com/jrodriiguezg/WatermelonD_nano.git
cd WatermelonD_nano
```

### Paso 2.2: Ejecutar el Instalador

Da permisos de ejecución y lanza el script. **Nota**: Se te pedirá tu contraseña de `sudo` para instalar dependencias del sistema.

```bash
chmod +x install.sh
./install.sh
```

### ¿Qué hace el script?
1. **Detección de OS**: Identifica si usas `apt` (Debian) o `dnf` (Fedora).
2. **Dependencias de Sistema**: Instala Python 3, PyAudio, VLC, FFMpeg, Mosquitto, etc.
3. **Entorno Python**:
 * Instala `pyenv` para gestionar versiones de Python.
 * Compila e instala **Python 3.10.13** (versión recomendada para compatibilidad).
 * Crea un entorno virtual en `venv/`.
 * Instala las librerías desde `requirements.txt`.
4. **Base de Datos**: Inicializa `database/BrainNut.db` con las tablas necesarias.
5. **Modelos de IA**:
 * Descarga el modelo de voz **Vosk** (Español).
 * Descarga el modelo LLM **Gemma 2B** (GGUF).
 * Descarga/Configura **Piper TTS** para síntesis de voz.
6. **Servicio Systemd**: Configura WatermelonD para arrancar automáticamente al inicio como servicio de usuario (`neo.service`).

## 3. Configuración Post-Instalación

Una vez finalizado el script, es posible que necesites ajustar la configuración de hardware.

### 3.1. Configurar Audio (Micrófono y Altavoces)

Edita el archivo de configuración principal:

```bash
nano config/config.json
```

Busca la sección `"stt"` (Speech-to-Text) y `"tts"` (Text-to-Speech).

* **Input Device**: Si tienes múltiples micrófonos, necesitas saber el índice.
 * Ejecuta `arecord -l` para listar dispositivos de captura.
 * En `config.json`, ajusta `"input_device_index": X` (donde X es el número de tarjeta/dispositivo).
 * Si lo dejas en `null`, usará el predeterminado del sistema.

### 3.2. Configurar API Keys (Opcional)

Si deseas usar servicios externos (como clima o noticias), añade tus claves en `config.json`.

## 4. Gestión del Servicio

WatermelonD se ejecuta como un servicio de usuario de systemd.

* **Iniciar manualmente**:
 ```bash
 systemctl --user start neo.service
 ```
* **Detener**:
 ```bash
 systemctl --user stop neo.service
 ```
* **Reiniciar**:
 ```bash
 systemctl --user restart neo.service
 ```
* **Ver Logs (En tiempo real)**:
 ```bash
 journalctl --user -u neo.service -f
 ```

## 5. Verificación del Despliegue

1. Reinicia el sistema: `sudo reboot`.
2. Espera unos 30-60 segundos tras el inicio.
3. Deberías escuchar un sonido de inicio o un saludo ("Sistema WatermelonD Online").
4. Prueba decir: *"WatermelonD, ¿qué hora es?"*.
5. Accede a la interfaz web: `http://<IP-DE-TU-RASPBERRY>:5000`.

## 6. Solución de Problemas Comunes

### Error: "No module named 'vosk'"
El entorno virtual no se activó correctamente. Asegúrate de usar el python del venv:
```bash
./venv/bin/python WatermelonD.py
```

### Error: "ALSA lib pcm.c... Device or resource busy"
Otro proceso está usando el micrófono. Cierra navegadores o grabadoras. WatermelonD intenta gestionar esto, pero a veces el bloqueo es a nivel de sistema.

### El reconocimiento es muy lento
* Verifica que no estás usando una Raspberry Pi 3 o inferior (falta de RAM/CPU).
* Asegúrate de que el modelo Vosk descargado es el adecuado (Small para RPi 3, Large para RPi 4/5). Puedes cambiarlo en `config.json`.

### No se escucha nada (TTS)
* Verifica el volumen: `alsamixer`.
* Prueba audio básico: `aplay /usr/share/sounds/alsa/Front_Center.wav`.
* Si usas HDMI, asegúrate de que la salida de audio está forzada a HDMI en `raspi-config`.

---
**Soporte**: Para problemas específicos, consulta los logs en `logs/app.log` o abre un issue en el repositorio.
