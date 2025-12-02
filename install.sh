#!/bin/bash

# install.sh
# Script de instalación para el proyecto Neo (Headless).
# Soporta Debian/Raspberry Pi OS (apt) y Fedora (dnf).

# Detiene el script si algún comando falla
set -e

echo "========================================="
echo "===   Instalador de Neo Core   ==="
echo "========================================="
echo "Este script instalará todo lo necesario para ejecutar la aplicación en modo servicio."
echo "Se requerirá tu contraseña para instalar paquetes del sistema (sudo)."
echo ""

# --- 1. DETECCIÓN DEL SISTEMA Y GESTOR DE PAQUETES ---
echo "[PASO 1/5] Detectando sistema operativo..."

if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt"
    echo "Sistema detectado: Debian/Ubuntu/Raspberry Pi OS (usando apt)"
    
    DEPENDENCIES=(
        git
        python3-pip
        vlc
        libvlc-dev
        portaudio19-dev
        python3-pyaudio
        flac
        alsa-utils
        espeak-ng
        unzip
        sqlite3
        wget
        curl
        python3
        chromium
        cmake 
        make
        make
        libopenblas-dev
        libfann-dev
        swig
        # Network Tools
        nmap
        whois
        # MQTT
        mosquitto
        mosquitto-clients
        # Bluetooth
        libbluetooth-dev
        # GUI / Kiosk
        xorg
        openbox
        chromium
        x11-xserver-utils
        # Python Build Deps (pyenv)
        build-essential
        libssl-dev
        zlib1g-dev
        libbz2-dev
        libreadline-dev
        libsqlite3-dev
        libffi-dev
        liblzma-dev
    )
    
    sudo apt-get update
    INSTALL_CMD="sudo apt-get install -y"

elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    echo "Sistema detectado: Fedora/RHEL (usando dnf)"
    
    DEPENDENCIES=(
        git
        python3-pip
        vlc
        vlc-devel
        portaudio-devel
        python3-pyaudio
        flac
        alsa-utils
        espeak-ng
        unzip
        sqlite3
        nmap
        whois
        bind-utils
        net-tools
        iputils
        gcc
        gcc-c++
        python3-devel
        wget
        gfortran
        openblas-devel
        lapack-devel
        curl
        python3
        ffmpeg
        chromium
        zlib-devel
        bzip2-devel
        readline-devel
        sqlite-devel
        openssl-devel
        tk-devel
        libffi-devel
        xz-devel
        cmake 
        make
        sox
        NetworkManager
        xorg-x11-server-Xorg
        xorg-x11-xinit
        xorg-x11-drv-libinput
        openbox
        chromium
        xset
        xrandr
    )
    
    INSTALL_CMD="sudo dnf install -y"

else
    echo "ERROR: No se encontró un gestor de paquetes compatible (apt o dnf)."
    exit 1
fi

echo "Instalando dependencias del sistema..."
$INSTALL_CMD "${DEPENDENCIES[@]}"

echo "Dependencias del sistema instaladas correctamente."
echo ""

# Habilitar servicio Mosquitto (MQTT)
if systemctl list-unit-files | grep -q mosquitto.service; then
    echo "Habilitando servicio Mosquitto..."
    sudo systemctl enable mosquitto
    sudo systemctl start mosquitto
fi

# --- 2. DESCARGA DEL CÓDIGO FUENTE ---
echo "[PASO 2/5] Verificando directorio del proyecto..."
if [ -f "start_services.py" ]; then
    echo "Directorio correcto."
else
    echo "AVISO: No se encontró start_services.py en el directorio actual."
    echo "Asegúrate de ejecutar este script desde la raíz del proyecto."
fi
echo ""

# --- 3. INSTALACIÓN DE PYTHON 3.10 CON PYENV ---
echo "[PASO 3/5] Configurando entorno Python 3.10..."

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"

if command -v pyenv 1>/dev/null 2>&1; then
    echo "Pyenv ya está instalado."
else
    echo "Instalando Pyenv..."
    curl https://pyenv.run | bash
    
    # Add to shell config if not present
    if ! grep -q 'export PYENV_ROOT="$HOME/.pyenv"' ~/.bashrc; then
        echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
        echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
        echo 'eval "$(pyenv init -)"' >> ~/.bashrc
    fi
fi

eval "$(pyenv init -)"

PYTHON_VERSION="3.10.13"
if pyenv versions | grep -q $PYTHON_VERSION; then
    echo "Python $PYTHON_VERSION ya está instalado en pyenv."
else
    echo "Instalando Python $PYTHON_VERSION (esto puede tardar unos minutos)..."
    pyenv install $PYTHON_VERSION
fi

# Crear Virtualenv
VENV_DIR="$(pwd)/venv"
if [ -d "$VENV_DIR" ]; then
    echo "Eliminando entorno virtual existente para evitar conflictos de permisos..."
    rm -rf "$VENV_DIR" || sudo rm -rf "$VENV_DIR"
fi

echo "Creando entorno virtual en $VENV_DIR..."
$HOME/.pyenv/versions/$PYTHON_VERSION/bin/python -m venv $VENV_DIR

# --- 3.1 INSTALACIÓN DE LIBRERÍAS DE PYTHON ---
echo "[PASO 3.1/5] Instalando las librerías de Python en el entorno virtual..."
$VENV_DIR/bin/pip install -U pip

# Fix FANN2 installation (Padatious dependency)
echo "Aplicando corrección para fann2..."
$VENV_DIR/bin/python resources/tools/install_fann_fix.py

$VENV_DIR/bin/pip install -r requirements.txt
echo "Librerías de Python instaladas correctamente."
echo ""

# --- 3.1. INICIALIZACIÓN DE LA BASE DE DATOS ---
echo "[PASO 3.1/5] Inicializando base de datos (Neo Brain)..."
export PYTHONPATH=$(pwd)
$VENV_DIR/bin/python database/init_db.py
# Asegurar permisos correctos para el usuario actual (que ejecutará el servicio)
if [ -f "database/brain.db" ]; then
    chown $(whoami):$(whoami) database/brain.db
    chmod 664 database/brain.db
    echo "Base de datos inicializada y permisos configurados."
else
    echo "ADVERTENCIA: No se pudo crear brain.db"
fi
echo ""

# --- 4. DESCARGA Y CONFIGURACIÓN DEL MODELO DE VOZ (VOSK) ---
echo "[PASO 4/5] Verificando modelo de voz (Vosk)..."
if [ -d "vosk-models/es" ]; then
    echo "Modelo de voz encontrado en 'vosk-models/es'."
else
    echo "----------------------------------------------------------------"
    echo "AVISO: No se encontró un modelo de voz instalado."
    echo "Para instalar uno, ejecuta manualmente el siguiente script:"
    echo "  python3 resources/tools/download_vosk_model.py"
    echo "Este script te ayudará a elegir el mejor modelo para tu sistema."
    echo "----------------------------------------------------------------"
fi
echo ""

# --- 4.1. INSTALACIÓN DE PIPER TTS ---
echo "[PASO 4.1/5] Instalando Piper TTS (Voz Natural)..."
if [ -f "resources/tools/install_piper.py" ]; then
    python3 resources/tools/install_piper.py
    # Ensure binary is executable
    if [ -f "piper/piper" ]; then
        chmod +x piper/piper
    fi
else
    echo "ADVERTENCIA: No se encontró el script resources/tools/install_piper.py. Se usará espeak como fallback."
fi
echo ""

# --- 4.2. DESCARGA DEL MODELO LLM (GEMMA 2B) ---
echo "[PASO 4.2/5] Descargando modelo Gemma 2B (GGUF)..."
if [ -f "resources/tools/download_model.py" ]; then
    echo "Descargando modelo Gemma 2B (GGUF)..."
    $VENV_DIR/bin/python resources/tools/download_model.py
else
    echo "ERROR: No se encontró resources/tools/download_model.py"
fi
# --- 4.3. DESCARGA DEL MODELO WHISPER (FASTER-WHISPER) ---
echo "[PASO 4.3/5] Descargando modelo Faster-Whisper (Medium)..."
if [ -f "resources/tools/download_whisper_model.py" ]; then
    $VENV_DIR/bin/python resources/tools/download_whisper_model.py
else
    echo "ERROR: No se encontró resources/tools/download_whisper_model.py"
fi
echo ""

# --- 5. CONFIGURACIÓN DEL SERVICIO SYSTEMD (USER MODE) ---
echo "[PASO 5/5] Configurando el servicio systemd (Modo Usuario)..."

APP_PATH="$(pwd)/start_services.py"
PROJECT_DIR="$(pwd)"

# Detect real user if run with sudo
if [ "$EUID" -eq 0 ]; then
    if [ -n "$SUDO_USER" ]; then
        USER_NAME="$SUDO_USER"
    else
        echo "ERROR: No se puede detectar el usuario real. No ejecutes este script como root directo (usa sudo ./install.sh)."
        exit 1
    fi
else
    USER_NAME=$(whoami)
fi

USER_ID=$(id -u $USER_NAME)
USER_HOME=$(eval echo ~$USER_NAME)
SERVICE_DIR="$USER_HOME/.config/systemd/user"
SERVICE_FILE="$SERVICE_DIR/neo.service"

echo "Configurando servicio para el usuario: $USER_NAME (UID: $USER_ID)"

# Asegurar directorio de logs
if [ ! -d "logs" ]; then
    mkdir -p logs
fi
chown $USER_NAME:$USER_NAME logs
chmod 755 logs

# Crear directorio de servicios de usuario
mkdir -p "$SERVICE_DIR"
chown -R $USER_NAME:$USER_NAME "$USER_HOME/.config"

# --- FIX SELINUX (Fedora/RHEL) ---
if command -v getenforce &> /dev/null && [ "$(getenforce)" != "Disabled" ]; then
    if command -v chcon &> /dev/null; then
        echo "SELinux detectado. Aplicando contextos..."
        chcon -R -t bin_t $VENV_DIR/bin/
        chcon -R -t user_home_t $(pwd)
    fi
fi

# Crear el fichero de servicio (USER SERVICE)
# Nota: No usamos User= ni Group= en user services.
# Tampoco necesitamos Environment=DISPLAY o PULSE porque se heredan.
cat <<EOT > "$SERVICE_FILE"
[Unit]
Description=Neo Assistant Service (User Mode)
After=network.target sound.target

[Service]
Type=simple
Environment=PYTHONUNBUFFERED=1
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/start_services.py
Restart=always
RestartSec=5
SyslogIdentifier=neo_core

[Install]
WantedBy=default.target
EOT

chown $USER_NAME:$USER_NAME "$SERVICE_FILE"

echo "Recargando demonio de systemd (usuario)..."

# Asegurar que el directorio runtime existe (si no hay sesión activa)
if [ ! -d "/run/user/$USER_ID" ]; then
    echo "Creando XDG_RUNTIME_DIR para el usuario..."
    mkdir -p /run/user/$USER_ID
    chown $USER_NAME:$USER_NAME /run/user/$USER_ID
    chmod 700 /run/user/$USER_ID
fi

export XDG_RUNTIME_DIR="/run/user/$USER_ID"

# Ejecutar systemctl como el usuario real con la variable de entorno correcta
sudo -u $USER_NAME XDG_RUNTIME_DIR=/run/user/$USER_ID systemctl --user daemon-reload
echo "Habilitando el servicio para que arranque al inicio de sesión..."
sudo -u $USER_NAME XDG_RUNTIME_DIR=/run/user/$USER_ID systemctl --user enable neo.service
sudo -u $USER_NAME XDG_RUNTIME_DIR=/run/user/$USER_ID systemctl --user restart neo.service

# Habilitar linger para que el servicio arranque sin login explícito
loginctl enable-linger $USER_NAME

# --- LIMPIEZA DE SERVICIO ANTIGUO (SYSTEM) ---
if [ -f "/etc/systemd/system/neo.service" ]; then
    echo "Eliminando servicio de sistema antiguo..."
    sudo systemctl stop neo.service 2>/dev/null || true
    sudo systemctl disable neo.service 2>/dev/null || true
    sudo rm /etc/systemd/system/neo.service
    sudo systemctl daemon-reload
fi

echo "El servicio se ha configurado en modo USUARIO."
echo "Logs: journalctl --user -u neo.service -f"
echo ""

# --- 6. CONFIGURACIÓN DE AUTO-LOGIN Y KIOSK (GUI) ---
echo "[PASO 6/5] Configurando Auto-login y modo Kiosk..."

# 0. Limpieza de configuración anterior (si existe)
if systemctl is-active --quiet neo-kiosk.service; then
    echo "Deteniendo servicio neo-kiosk antiguo..."
    sudo systemctl stop neo-kiosk.service
fi
if systemctl is-enabled --quiet neo-kiosk.service; then
    echo "Deshabilitando servicio neo-kiosk antiguo..."
    sudo systemctl disable neo-kiosk.service
fi
if [ -f "/etc/systemd/system/neo-kiosk.service" ]; then
    echo "Eliminando fichero de servicio neo-kiosk antiguo..."
    sudo rm /etc/systemd/system/neo-kiosk.service
    sudo systemctl daemon-reload
fi

# 1. Configurar Auto-login en tty1
echo "Configurando auto-login para el usuario $USER_NAME en tty1..."
GETTY_OVERRIDE_DIR="/etc/systemd/system/getty@tty1.service.d"
GETTY_OVERRIDE_FILE="$GETTY_OVERRIDE_DIR/override.conf"

sudo mkdir -p $GETTY_OVERRIDE_DIR
sudo bash -c "cat <<EOT > $GETTY_OVERRIDE_FILE
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USER_NAME --noclear %I \$TERM
EOT"

# 2. Configurar .bash_profile para arrancar X automáticamente
echo "Configurando .bash_profile para iniciar X automáticamente..."
if ! grep -q "exec startx" ~/.bash_profile; then
    cat <<EOT >> ~/.bash_profile

# Auto-start X on tty1
if [[ -z \$DISPLAY ]] && [[ \$(tty) = /dev/tty1 ]]; then
    exec startx
fi
EOT
fi

# 3. Configurar .xinitrc para lanzar el Kiosk
echo "Creando .xinitrc para lanzar Openbox y Chromium..."
cat <<EOT > ~/.xinitrc
#!/bin/bash
# Desactivar ahorro de energía
xset -dpms
xset s off
xset s noblank

# Iniciar gestor de ventanas
openbox &

# Esperar a que el servidor Flask esté listo (puerto 5000)
echo "Esperando a que Neo Core inicie el servidor web..."
while ! curl -s http://localhost:5000/face > /dev/null; do
    sleep 2
done

# Detectar nombre del binario de Chromium
CHROMIUM_BIN="chromium"
if command -v chromium-browser &> /dev/null; then
    CHROMIUM_BIN="chromium-browser"
fi

# Bucle infinito para el navegador
while true; do
    \$CHROMIUM_BIN --kiosk --no-first-run --disable-infobars --disable-session-crashed-bubble --disable-restore-session-state http://localhost:5000/face
    sleep 2
done
EOT

chmod +x ~/.xinitrc

echo "Configuración de Auto-login y Kiosk completada."
echo ""

# --- MENSAJES FINALES ---
echo "---------------------- ¡AVISO IMPORTANTE! ----------------------"
echo "La aplicación ahora se ejecuta como un servicio en segundo plano."
echo "Puedes ver los logs en la carpeta 'logs/' o usando:"
echo "  journalctl -u neo.service -f"
echo "----------------------------------------------------------------"
echo ""

echo "🎉 ¡Instalación completada!"
