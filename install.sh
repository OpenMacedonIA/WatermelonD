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

# --- 0. AUTO-UPDATE CHECK ---
echo "[PASO 0/5] Buscando actualizaciones..."
if [ -d ".git" ] && command -v git &> /dev/null; then
    echo "Repositorio git detectado. Ejecutando git pull..."
    
    # Guardar el hash actual
    CURRENT_HASH=$(git rev-parse HEAD 2>/dev/null)
    
    # Intentar actualizar
    if git pull; then
        NEW_HASH=$(git rev-parse HEAD 2>/dev/null)
        if [ "$CURRENT_HASH" != "$NEW_HASH" ]; then
            echo "----------------------------------------------------------------"
            echo "¡Se han descargado actualizaciones!"
            echo "Reiniciando el instalador para aplicar los cambios..."
            echo "----------------------------------------------------------------"
            exec "$0" "$@"
        fi
    else
        echo "⚠️  Error al actualizar (git pull falló). Continuando con la versión actual..."
    fi
else
    echo "No se detectó repositorio git o git no está instalado. Saltando actualización."
fi
echo ""
# --- CONFIGURACIÓN DE TMPDIR (Para evitar errores de espacio en /tmp) ---
# Usamos un directorio temporal dentro del proyecto porque /tmp suele ser pequeño
export TMPDIR="$(pwd)/temp_build"
if [ ! -d "$TMPDIR" ]; then
    mkdir -p "$TMPDIR"
fi
echo "Directorio temporal configurado en: $TMPDIR"
echo ""

# --- 1. DETECCIÓN DEL SISTEMA Y GESTOR DE PAQUETES ---
echo "[PASO 1/5] Detectando sistema operativo..."

if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt"
    echo "Sistema detectado: Debian/Ubuntu/Raspberry Pi OS (usando apt)"
    
    DEPENDENCIES=(
        git
        python3-pip
        # Basic Admin Tools
        vim
        nano
        htop
        tree
        net-tools
        ufw
        # Network Analysis Tools
        dnsutils
        network-manager
        iputils-ping
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
        ffmpeg
    )
    
    sudo apt-get update
    INSTALL_CMD="sudo apt-get install -y"

else
    echo "----------------------------------------------------------------"
    echo "⚠️  Sistema NO-Debian detectado."
    echo "Para garantizar la compatibilidad, Colega requiere ejecutarse en un contenedor Debian."
    echo "Se procederá a configurar Distrobox automáticamente."
    echo "----------------------------------------------------------------"
    
    chmod +x setup_distrobox.sh
    exec ./setup_distrobox.sh
fi

echo ""
# --- 1.1 CONFIGURACIÓN INTERACTIVA (MINIMAL / OPTIMIZACIÓN) ---
echo "----------------------------------------------------------------"
echo "¿Deseas aplicar una configuración MINIMAL y OPTIMIZADA para Debian?"
echo "Esto hará lo siguiente:"
echo "  1. Configurar hostname como 'COLEGA'."
echo "  2. Eliminar bloatware (LibreOffice, juegos, etc.)."
echo "  3. Instalar herramientas de gestión de ventanas (wmctrl, xdotool)."
echo "----------------------------------------------------------------"
read -p "¿Optimizar sistema? (s/n): " OPTIMIZE_OPT

# Configurar Hostname (Siempre a COLEGA)
echo "Configurando hostname a 'COLEGA'..."
sudo hostnamectl set-hostname COLEGA
# Actualizar /etc/hosts para evitar warnings de sudo
if ! grep -q "127.0.1.1.*COLEGA" /etc/hosts; then
    sudo sed -i 's/127.0.1.1.*/127.0.1.1\tCOLEGA/g' /etc/hosts
fi

if [[ "$OPTIMIZE_OPT" =~ ^[Ss]$ ]]; then
    echo "Aplicando optimizaciones..."
    
    # Añadir herramientas de ventana a la lista de dependencias
    DEPENDENCIES+=(wmctrl xdotool)
    
    # Eliminar Bloatware común en instalaciones desktop standard
    echo "Eliminando software innecesario..."
    sudo apt-get purge -y libreoffice* aisleriot gnomine mahjongg quadrapassel *sudoku* || true
    sudo apt-get autoremove -y
else
    echo "Instalación estándar (sin eliminar paquetes)."
fi
echo "----------------------------------------------------------------"
echo ""

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
$VENV_DIR/bin/pip install -U pip --no-cache-dir

# Fix FANN2 installation (Padatious dependency)
echo "Aplicando corrección para fann2..."
$VENV_DIR/bin/python resources/tools/install_fann_fix.py

$VENV_DIR/bin/pip install -r requirements.txt --no-cache-dir
echo "Librerías de Python instaladas correctamente."
echo ""

# --- 3.1. PREPARACIÓN DE DIRECTORIOS ---
echo "[PASO 3.1/5] Preparando estructura de directorios..."

# Directorios críticos
DIRS=(
    "logs"
    "config"
    "database"
    "models"
    "piper/voices"
    "docs/brain_memory"
)

for dir in "${DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "Creando directorio: $dir"
        mkdir -p "$dir"
    fi
    # Asegurar permisos del usuario actual (no root) si se creó con sudo antes
    chown -R $(whoami):$(whoami) "$dir" 2>/dev/null || true
    chmod 775 "$dir"
done

# --- 3.2. INICIALIZACIÓN DE LA BASE DE DATOS ---
echo "[PASO 3.2/5] Inicializando base de datos (Neo Brain)..."

# Self-healing: Check if script exists (corruption check)
if [ ! -f "database/init_db.py" ]; then
    echo "⚠️  AVISO: No se encuentra database/init_db.py."
    echo "Recreando el archivo faltante..."
    
    mkdir -p database
    cat <<EOT > database/init_db.py
from modules.database import DatabaseManager
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)

def init():
    print("Initializing Neo Brain Database...")
    try:
        db = DatabaseManager()
        # The __init__ method of DatabaseManager calls init_db(), which creates tables if they don't exist.
        # We can also explicitly check connection here.
        conn = db.get_connection()
        print("Database 'brain.db' created/verified successfully.")
        db.close()
    except Exception as e:
        print(f"Error initializing database: {e}")
        exit(1)

if __name__ == "__main__":
    init()
EOT
    echo "Archivo restaurado correctamente."
fi

export PYTHONPATH=$(pwd)
$VENV_DIR/bin/python database/init_db.py

# Asegurar permisos en db
if [ -f "database/brain.db" ]; then
    chown $(whoami):$(whoami) database/brain.db
    chmod 664 database/brain.db
    echo "Base de datos verificada."
else
    echo "ADVERTENCIA: No se pudo verificar database/brain.db"
fi
echo ""

# --- 4. DESCARGA Y CONFIGURACIÓN DEL MODELO DE VOZ (VOSK) ---
echo "[PASO 4/5] Verificando modelo de voz (Vosk)..."
if [ -d "vosk-models/es" ]; then
    echo "Modelo de voz encontrado en 'vosk-models/es'."
else
    echo "----------------------------------------------------------------"
    echo "AVISO: No se encontró un modelo de voz instalado."
    echo "Para instalar uno, ejecuta manualmente el siguiente script usando el entorno virtual:"
    echo "  ./venv/bin/python resources/tools/download_vosk_model.py"
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

# --- 4.4. DESCARGA DEL MODELO MANGO T5 (NL2BASH) ---
# --- 4.4. DESCARGA DEL MODELO MANGO T5 (NL2BASH) ---
echo "[PASO 4.4/5] Descargando modelo MANGO T5 (SysAdmin AI)..."
if [ -f "resources/tools/download_mango_model.py" ]; then
    echo "----------------------------------------------------------------"
    echo "Selecciona la versión del modelo MANGO a instalar:"
    echo "   1) MANGO (Recomendado - Última versión)"
    echo "   2) MANGO2 (Legacy - Versión anterior)"
    echo "----------------------------------------------------------------"
    read -p "Opción [1-2] (Enter para MANGO): " MANGO_OPT
    
    BRANCH="main"
    if [ "$MANGO_OPT" == "2" ]; then
        BRANCH="MANGO2"
        echo "Has seleccionado: MANGO2 (Legacy)"
    else
        echo "Has seleccionado: MANGO (Recomendado)"
    fi
    
    $VENV_DIR/bin/python resources/tools/download_mango_model.py --branch "$BRANCH"
else
    echo "ERROR: No se encontró resources/tools/download_mango_model.py"
fi
echo ""

# --- 5. CONFIGURACIÓN DEL SERVICIO SYSTEMD (USER MODE) ---
echo "[PASO 5/5] Configurando el servicio systemd (Modo Usuario)..."

APP_PATH="$(pwd)/NeoCore.py"
WEB_PATH="$(pwd)/web_client/app.py"
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
WEB_SERVICE_FILE="$SERVICE_DIR/neo-web.service"

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

# --- PERMISOS DE GRUPO ---
echo "Añadiendo a $USER_NAME a los grupos de audio y video..."
sudo usermod -a -G audio,video,tty $USER_NAME || true


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
Description=Neo Core Backend Service
After=network.target sound.target

[Service]
Type=simple
Environment=PYTHONUNBUFFERED=1
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python $APP_PATH
Restart=always
RestartSec=5
SyslogIdentifier=neo_core

[Install]
WantedBy=default.target
EOT

# Crear el fichero de servicio WEB (Frontend)
cat <<EOT > "$WEB_SERVICE_FILE"
[Unit]
Description=Neo Web Client Service
After=network.target neo.service

[Service]
Type=simple
Environment=PYTHONUNBUFFERED=1
Environment=NEO_API_URL=http://localhost:5000
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python $WEB_PATH
Restart=always
RestartSec=5
SyslogIdentifier=neo_web

[Install]
WantedBy=default.target
EOT

chown $USER_NAME:$USER_NAME "$SERVICE_FILE" "$WEB_SERVICE_FILE"

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
sudo -u $USER_NAME XDG_RUNTIME_DIR=/run/user/$USER_ID systemctl --user enable neo.service neo-web.service
sudo -u $USER_NAME XDG_RUNTIME_DIR=/run/user/$USER_ID systemctl --user restart neo.service neo-web.service

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

echo "Los servicios se han configurado en modo USUARIO."
echo "Logs Core: journalctl --user -u neo.service -f"
echo "Logs Web:  journalctl --user -u neo-web.service -f"
echo ""

# --- 5.1 SEGURIDAD (SSL & PASSWORD) ---
echo "[PASO 5.1/5] Configurando seguridad..."

# 1. Generar Certificados SSL
CERT_DIR="$(pwd)/config/certs"
mkdir -p "$CERT_DIR"

if [ ! -f "$CERT_DIR/neo.key" ]; then
    echo "Generando certificados SSL autofirmados..."
    # Check for openssl
    if command -v openssl >/dev/null 2>&1; then
        openssl req -x509 -newkey rsa:4096 -keyout "$CERT_DIR/neo.key" -out "$CERT_DIR/neo.crt" -days 3650 -nodes -subj "/C=ES/ST=Madrid/L=Madrid/O=NeoCore/CN=$(hostname)"
        
        # Set permissions
        chown $(whoami):$(whoami) "$CERT_DIR/neo.key" "$CERT_DIR/neo.crt"
        chmod 600 "$CERT_DIR/neo.key"
        chmod 644 "$CERT_DIR/neo.crt"
        
        echo "✅ Certificado generado en: $CERT_DIR"
        echo "   -> Importa 'neo.crt' en tu navegador para evitar advertencias."
    else
        echo "⚠️  OpenSSL no encontrado. No se pudo generar certificado SSL."
    fi
else
    echo "Certificados SSL ya existen."
fi

# 2. Configurar Contraseña Admin
echo "Configurando credenciales de administración..."
if [ -f "resources/tools/password_helper.py" ]; then
    # Create default config if not exists to avoid errors
    if [ ! -f "config/config.json" ]; then
        echo "{}" > config/config.json
    fi
    
    # Run helper
    # We use a default first, but could prompt interactively if installer was interactive.
    # Since this script might be run non-interactively, we'll set a default ONLY IF not set.
    # But for better security, let's force a hash of 'admin' if nothing exists.
    
    echo "Estableciendo contraseña predeterminada ('admin')... ¡Cmbiala luego!"
    $VENV_DIR/bin/python resources/tools/password_helper.py --user admin --password admin
else
    echo "⚠️  Helper de contraseñas no encontrado."
fi
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

# Esperar a que el servidor Flask esté listo (puerto 8000 - Web Client)
echo "Esperando a que Neo Web Client inicie..."
while ! curl -s http://localhost:8000 > /dev/null; do
    sleep 2
done

# Detectar nombre del binario de Chromium
CHROMIUM_BIN="chromium"
if command -v chromium-browser &> /dev/null; then
    CHROMIUM_BIN="chromium-browser"
fi

# Bucle infinito para el navegador
while true; do
    \$CHROMIUM_BIN --kiosk --no-first-run --disable-infobars --disable-session-crashed-bubble --disable-restore-session-state http://localhost:8000
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
echo ""

# --- 7. HARDENING OPCIONAL ---
if [ -f "resources/tools/secure_system.sh" ]; then
    echo "----------------------------------------------------------------"
    echo "¿Quieres aplicar medidas de seguridad adicionales al sistema?"
    echo "Esto instalará UFW (Firewall), Fail2Ban y restringirá permisos de archivos."
    echo "Recomendado si este dispositivo está expuesto a red."
    echo "----------------------------------------------------------------"
    read -p "¿Ejecutar hardening de seguridad? (s/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        sudo ./resources/tools/secure_system.sh
    else
        echo "Saltando hardening. Puedes ejecutarlo luego con: sudo resources/tools/secure_system.sh"
    fi
fi
echo ""
