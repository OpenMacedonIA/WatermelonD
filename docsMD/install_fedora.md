# Guía de Instalación en Fedora (x86_64)

Esta guía detalla los pasos para instalar NEOPapaya Nano en un PC con Fedora 43 (Intel i3, 8GB RAM).

## 1. Preparación del Sistema

Asegúrate de tener el sistema actualizado:

```bash
sudo dnf update -y
```

Instala dependencias básicas si no las tienes (git, python3):

```bash
sudo dnf install -y git python3 python3-pip
```

## 2. Clonar el Repositorio

```bash
git clone <URL_DEL_REPO> NEOPapaya_nano
cd NEOPapaya_nano
```

## 3. Ejecutar el Instalador

El script `install.sh` detectará automáticamente que estás en Fedora y usará `dnf`.

```bash
chmod +x install.sh
./install.sh
```

Esto instalará:
- Dependencias del sistema (VLC, PortAudio, ffmpeg, etc.)
- Librerías de Python (`requirements.txt`)
- Inicializará la base de datos.
- Configurará el servicio systemd.

## 4. Configurar Audio y Voz (Hybrid STT)

Para aprovechar tu hardware, usaremos el modo Híbrido (Vosk + Whisper).

1. **Instalar Whisper**:
 ```bash
 pip install faster-whisper
 ```

2. **Optimizar y Configurar**:
 Ejecuta la herramienta de optimización. Para un i3, el modelo `base` es un buen punto de partida.
 
 ```bash
 python3 tools/optimize_whisper.py --model base --auto-configure
 ```
 
 Si ves ` config.json actualizado`, todo está listo.

3. **Seleccionar Micrófono (Opcional)**:
 Si tienes varios micrófonos, edita `config.json` y ajusta `input_device_index`. Puedes ver los índices en el log de inicio o usando `pyaudio`.

## 5. Iniciar el Servicio

```bash
sudo systemctl start neo.service
```

Verifica los logs:

```bash
journalctl -u neo.service -f
```

## 6. Interfaz Visual (NEOPapaya Face)

Si tu dispositivo tiene pantalla (como tu convertible), puedes activar los "ojos" de NEOPapaya.

1. **Iniciar NEOPapaya Core**:
 ```bash
 python3 NeoCore.py
 ```

2. **Lanzar la Interfaz**:
 En otra terminal, ejecuta:
 ```bash
 chmod +x tools/start_face.sh
 ./tools/start_face.sh
 ```
 Esto abrirá el navegador en pantalla completa con los ojos reactivos.

 *Nota: Necesitas tener Firefox o Chromium instalado.*
