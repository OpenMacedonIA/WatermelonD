#!/bin/bash

# install.sh
# Script de instalación UNIFICADO para el proyecto Neo Papaya.
# Soporta Instalación Completa, Cliente Web, Satélites y Herramientas.

# Detiene el script si algún comando falla
set -e


echo "========================================="
echo "===     Instalador WatermelonD        ==="
echo "========================================="
echo ""

# --- 0. ARRANQUE / COMPROBACIÓN AUTO-CLONADO ---
# Comprobar si estamos dentro del repositorio git. Si no, necesitamos clonarlo.
if [ ! -d ".git" ]; then
    echo "========================================="
    echo "===   MODO BOOTSTRAP / AUTO-CLONE   ==="
    echo "========================================="
    echo "No se ha detectado un repositorio git en el directorio actual."
    echo "Se procederá a descargar el código fuente..."
    echo ""

    # 1. Instalar Git si es necesario
    if ! command -v git &> /dev/null; then
        echo "Git no está instalado. Instalando git..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y git
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y git
        else
            echo "ERROR: No se pudo instalar git. Por favor instálalo manualmente."
            exit 1
        fi
    fi

    # Asegurar que whiptail está instalado
    if ! command -v whiptail &> /dev/null; then
        echo "Instalando whiptail para interfaz gráfica..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y whiptail
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y newt
        fi
    fi

    # 2. Definir Directorio de Instalación
    DEFAULT_DIR="$HOME/WatermelonD"
    
    CUSTOM_DIR=$(whiptail --inputbox "Directorio de instalación\n\nDeja vacío para usar el predeterminado: $DEFAULT_DIR" 12 70 "" 3>&1 1>&2 2>&3)
    
    TARGET_DIR="${CUSTOM_DIR:-$DEFAULT_DIR}"
    
    whiptail --msgbox "Instalando en: $TARGET_DIR" 8 60

    # 2.1 Seleccionar Rama
    BRANCH_OPT=$(whiptail --title "Selección de Rama" --menu "Elige la rama a instalar:" 15 70 2 \
        "1" "Main (Estable) - Recomendado para producción" \
        "2" "RC (Release Candidate) - Próxima versión (Inestable)" \
        3>&1 1>&2 2>&3)
    
    if [[ "$BRANCH_OPT" == "2" ]]; then
        BRANCH="rc"
    else
        BRANCH="main"
    fi
    
    whiptail --msgbox "Rama seleccionada: $BRANCH" 8 50
    
    # 3. Clonar Repositorio
    if [ -d "$TARGET_DIR" ]; then
        if [ -z "$(ls -A $TARGET_DIR)" ]; then
             echo "Directorio vacío detectado. Clonando..."
             git clone -b "$BRANCH" https://github.com/OpenMacedonIA/WatermelonD.git "$TARGET_DIR"
             cd "$TARGET_DIR"
             git submodule update --init --recursive
        else
             if ! whiptail --title "Directorio Existente" --yesno "AVISO: El directorio $TARGET_DIR ya existe y no está vacío.\n\n¿Continuar y tratar de actualizar/instalar ahí?" 12 70; then
                 whiptail --msgbox "Instalación cancelada por el usuario." 8 50
                 exit 0
             fi
        fi
    else
        echo "Creando directorio $TARGET_DIR y clonando..."
        git clone -b "$BRANCH" https://github.com/OpenMacedonIA/WatermelonD.git "$TARGET_DIR"
        cd "$TARGET_DIR"
        git submodule update --init --recursive
    fi

    # 4. Traspaso de ejecución
    echo ""
    echo "Repositorio listo. Transfiriendo control al instalador del repositorio..."
    echo "----------------------------------------------------------------"
    
    cd "$TARGET_DIR"
    chmod +x install.sh
    exec ./install.sh "$@"
    exit 0
fi

# --- 0.1 COMPROBACIÓN DE AUTO-ACTUALIZACIÓN (DENTRO DEL REPO) ---
echo "[ACTUALIZACIÓN] Buscando cambios en el repositorio..."
if [ -d ".git" ] && command -v git &> /dev/null; then
    # Guardar el hash actual
    CURRENT_HASH=$(git rev-parse HEAD 2>/dev/null)
    
    # Intentar actualizar
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    echo "Actualizando desde rama: $CURRENT_BRANCH"
    if git pull origin "$CURRENT_BRANCH" && git submodule update --init --recursive; then
        NEW_HASH=$(git rev-parse HEAD 2>/dev/null)
        if [ "$CURRENT_HASH" != "$NEW_HASH" ]; then
            echo "----------------------------------------------------------------"
            echo "¡Se han descargado actualizaciones!"
            echo "Reiniciando el instalador para aplicar los cambios..."
            echo "----------------------------------------------------------------"
            exec "$0" "$@"
        fi
    else
        echo "  Error al actualizar (git pull falló). Continuando con la versión actual..."
    fi
else
    echo "No se detectó repositorio git o git no está instalado. Saltando actualización."
fi
echo ""

# ==============================================================================
# DEFINICIÓN DE FUNCIONES
# ==============================================================================

function install_standard() {
    echo ""
    echo "========================================="
    echo "===     INSTALACIÓN NODO PRINCIPAL    ==="
    echo "========================================="

    # --- CONFIGURACIÓN DE TMPDIR ---
    export TMPDIR="$(pwd)/temp_build"
    mkdir -p "$TMPDIR"
    echo "Directorio temporal: $TMPDIR"

    # --- 1. DETECCIÓN DEL SISTEMA ---
    echo "[PASO 1/6] Detectando sistema operativo..."
    if command -v apt-get &> /dev/null; then
        PKG_MANAGER="apt"
        echo "Sistema Debian/Ubuntu detectado."
        
        # Dependencias Base
        DEPENDENCIES=(
            git python3-pip vim nano htop tree net-tools ufw
            dnsutils network-manager iputils-ping vlc libvlc-dev
            portaudio19-dev python3-pyaudio flac alsa-utils espeak-ng
            unzip sqlite3 wget curl python3 cmake make libopenblas-dev
            libfann-dev swig nmap whois mosquitto mosquitto-clients
            libbluetooth-dev build-essential libssl-dev zlib1g-dev
            libbz2-dev libreadline-dev libsqlite3-dev libffi-dev
            liblzma-dev ffmpeg git-lfs bluez bluez-tools
            evince okular feh eog xdg-utils
            wireless-tools iw
            # Security Tools (Antivirus, IDS, Audit, Rootkits)
            clamav clamav-daemon fail2ban lynis chkrootkit rkhunter aide tripwire tiger
        )
        
        sudo apt-get update
        INSTALL_CMD="sudo apt-get install -y"

    else
        echo "----------------------------------------------------------------"
        echo "  Sistema NO-Debian detectado."
        echo "Para garantizar la compatibilidad, se recomienda usar Distrobox."
        echo "----------------------------------------------------------------"
        chmod +x setup_distrobox.sh
        exec ./setup_distrobox.sh
        return # Detener ejecución aquí ya que exec reemplaza proceso usualmente, pero por seguridad
    fi

    echo ""
    # --- PREGUNTAS DE CONFIGURACIÓN ---
    echo "----------------------------------------------------------------"
    echo "OPCIONES DE INSTALACIÓN"
    echo "----------------------------------------------------------------"
    
    # GUI vs Headless (Interfaz Gráfica vs Sin Cabeza)
    read -p "¿Instalar Interfaz Gráfica (Kiosk Mode)? (s/n) [s]: " INSTALL_GUI_OPT
    INSTALL_GUI_OPT=${INSTALL_GUI_OPT:-s} # Por defecto sí

    if [[ "$INSTALL_GUI_OPT" =~ ^[Ss]$ ]]; then
        INSTALL_GUI=true
        DEPENDENCIES+=(xorg openbox chromium x11-xserver-utils wmctrl xdotool)
        echo "-> Se instalará entorno gráfico."
    else
        INSTALL_GUI=false
        echo "-> Modo Headless (Sin entorno gráfico)."
    fi

    # Minimal / Optimize (Mínimo / Optimizar)
    read -p "¿Aplicar optimizaciones de sistema (hostname OpenMacendonIA, limpiar bloatware)? (s/n) [n]: " OPTIMIZE_OPT
    OPTIMIZE_OPT=${OPTIMIZE_OPT:-n}

    if [[ "$OPTIMIZE_OPT" =~ ^[Ss]$ ]]; then
        echo "-> Se aplicarán optimizaciones."
        sudo hostnamectl set-hostname OpenMacendonIA
        if ! grep -q "127.0.1.1.*OpenMacendonIA" /etc/hosts; then
            sudo sed -i 's/127.0.1.1.*/127.0.1.1\tOpenMacendonIA/g' /etc/hosts
        fi
        sudo apt-get purge -y libreoffice* aisleriot gnomine mahjongg quadrapassel *sudoku* || true
        sudo apt-get autoremove -y
    fi
    echo "----------------------------------------------------------------"
    
    # Instalar Dependencias
    echo "Instalando paquetes del sistema..."
    $INSTALL_CMD "${DEPENDENCIES[@]}"

    # Habilitar Mosquitto
    if systemctl list-unit-files | grep -q mosquitto.service; then
        sudo systemctl enable mosquitto
        sudo systemctl start mosquitto
    fi
    
    # --- CONFIGURAR PERMISOS DE RED ---
    # Agregar usuario al grupo netdev para NetworkManager (escaneo WiFi, etc.)
    echo "Configurando permisos de red..."
    if ! groups $USER | grep -q netdev; then
        sudo usermod -aG netdev $USER
        echo " Usuario agregado al grupo 'netdev' (NetworkManager)"
        echo "  NOTA: Debes cerrar sesión y volver a entrar para que los cambios surtan efecto"
    else
        echo " Usuario ya pertenece al grupo 'netdev'"
    fi

    # --- CONFIGURACIÓN DE PYTHON ---
    # --- CONFIGURACIÓN DE PYTHON CON UV ---
    echo "[PASO 3/6] Configurando Python 3.10 con uv..."
    
    # 1. Instalar uv si no existe
    if ! command -v uv &> /dev/null; then
        echo "Instalando uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        if [ -f "$HOME/.local/bin/env" ]; then
            source "$HOME/.local/bin/env"
        elif [ -f "$HOME/.cargo/env" ]; then
            source "$HOME/.cargo/env"
        fi
    fi

    # Asegurar que uv está en PATH (por si acaso el source falló en subshell o no persistió)
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

    # 2. Utilizar uv para gestionar Python
    # uv python install 3.10  <-- Opcional, pero uv puede gestionar versiones de python también
    # Por ahora mantenemos la lógica pero dejamos que uv maneje el venv
    
    VENV_DIR="$(pwd)/venv"
    if [ -d "$VENV_DIR" ]; then
        echo "Recreando entorno virtual con uv..."
        rm -rf "$VENV_DIR"
    fi
    
    echo "Creando venv con Python 3.10..."
    # uv venv crea el entorno. Podemos especificar versión si queremos, pero usará la del sistema o descargará una
    uv venv "$VENV_DIR" --python 3.10
    
    echo "Instalando dependencias con uv..."
    source "$VENV_DIR/bin/activate"
    
    # uv pip install es mucho más rápido
    uv pip install --upgrade pip
    
    # Ejecutar script de arreglo de fann antes de instalar requirements si es necesario
    # Nota: install_fann_fix.py usa 'pip' internamente? Si es así, podría fallar si no está en PATH
    # o si usa el pip del venv. Como estamos en venv activado, 'python' es el del venv.
    python resources/tools/install_fann_fix.py
    
    uv pip install -r requirements.txt
    uv pip install Flask-WTF eventlet Flask-Limiter

    # --- DIRECTORIOS ---
    DIRS=("logs" "config" "database" "models" "piper/voices" "docs/brain_memory")
    for dir in "${DIRS[@]}"; do
        mkdir -p "$dir"
        chmod 775 "$dir"
    done
    # Config initialization (use .example as template)
    if [ ! -f "config/config.json" ]; then
        if [ -f "config/config.json.example" ]; then
            echo "Creando config.json desde template..."
            cp config/config.json.example config/config.json
            echo "config.json creado. Editar para personalizar."
        else
            echo "ADVERTENCIA: config.json.example no encontrado. Creando config vacio."
            echo "{}" > config/config.json
        fi
    fi

    # --- PERSONALIZACIÓN INTERACTIVA (NUEVA SECCIÓN) ---
    if whiptail --title "Personalización" --yesno \
        "¿Deseas personalizar la configuración del sistema?\n\nPuedes elegir entre modo simple o avanzado." \
        12 60; then
        configure_personalization
    else
        whiptail --msgbox "Saltando personalización.\n\nPuedes editar config/config.json manualmente después de la instalación." 10 60
    fi

    # --- INICIALIZACIÓN BD ---
    echo "[PASO 3.2/6] Inicializando BD..."
    # (Autocuración eliminada por brevedad, asumiendo que el archivo existe o el usuario lo restaura)
    export PYTHONPATH=$(pwd)
    $VENV_DIR/bin/python database/init_db.py

    # --- MODELOS ---
    echo "[PASO 4/6] Configurando Modelos..."
    
    # Sherpa-ONNX (Default STT Engine)
    if [ ! -d "models/sherpa/sherpa-onnx-whisper-medium" ]; then
        echo "Descargando Sherpa-ONNX Whisper Medium..."
        if [ -f "resources/tools/download_sherpa_model.py" ]; then
            $VENV_DIR/bin/python resources/tools/download_sherpa_model.py --model small
        else
            echo "ERROR: No se encontró el script de descarga de Sherpa-ONNX."
            echo "Instalación continúa, pero STT no funcionará hasta descargar el modelo."
        fi
    else
        echo " Sherpa-ONNX Whisper Medium ya instalado"
    fi

    # Piper
    [ -f "resources/tools/install_piper.py" ] && $VENV_DIR/bin/python resources/tools/install_piper.py

    # Gemma
    # Gemma (MANGO Legacy - Removed in favor of Grape)
    if [ ! -d "models/gemma-2-2b-it-Q4_K_M.gguf" ]; then
         [ -f "resources/tools/download_model.py" ] && $VENV_DIR/bin/python resources/tools/download_model.py
    fi

    # Configurar Git LFS para modelos
    git lfs install

    # Comprobación de Whisper - DESHABILITADO
    # read -p "¿Instalar Whisper (STT Local Avanzado - 1.5GB)? (s/n) [n]: " WHISPER_OPT
    # if [[ "$WHISPER_OPT" =~ ^[Ss]$ ]]; then
    #     $VENV_DIR/bin/pip install faster-whisper
    #     [ -f "resources/tools/download_whisper_model.py" ] && $VENV_DIR/bin/python resources/tools/download_whisper_model.py
    # fi

    # Nuevos Modelos Grape (HuggingFace)
    echo "Descargando modelos Grape..."
    
    # Grape-Chardonnay
    if [ ! -d "models/chardonnay" ]; then
        echo "Descargando Grape-Chardonnay..."
        git clone https://huggingface.co/jrodriiguezg/grape-chardonnay models/chardonnay
    fi

    # Grape-Malbec
    if [ ! -d "models/malbec" ]; then
        echo "Descargando Grape-Malbec..."
        git clone https://huggingface.co/jrodriiguezg/grape-malbec models/malbec
    fi

    # Grape-Pinot
    if [ ! -d "models/pinot" ]; then
        echo "Descargando Grape-Pinot..."
        git clone https://huggingface.co/jrodriiguezg/grape-pinot models/pinot
    fi

    # Decision Router Model (Grape-Route)
    # Removing potential bad clones (HTML files) from non-LFS downloads
    [ -d "models/grape-route" ] && rm -rf "models/grape-route"

    if [ ! -d "models/grape-route" ]; then
        echo "Descargando modelo Decision Router (Grape-Route)..."
        git clone https://huggingface.co/jrodriiguezg/minilm-l12-grape-route models/grape-route
    fi

    # Grape-Syrah (Network)
    if [ ! -d "models/syrah" ]; then
        echo "Descargando Grape-Syrah..."
        git clone https://huggingface.co/jrodriiguezg/grape-syrah models/syrah
    fi

    # Socket.IO
    mkdir -p "TangerineUI/static/js"
    if [ ! -f "TangerineUI/static/js/socket.io.min.js" ]; then
        wget -q -O "TangerineUI/static/js/socket.io.min.js" https://cdn.socket.io/4.7.2/socket.io.min.js
    fi

    # --- SERVICIOS ---
    echo "[PASO 5/6] Configurando Systemd (Modo Usuario)..."
    
    # Detectar usuario
    if [ "$EUID" -eq 0 ]; then
        USER_NAME="$SUDO_USER"
    else
        USER_NAME=$(whoami)
    fi
    USER_ID=$(id -u $USER_NAME)
    USER_HOME=$(eval echo ~$USER_NAME)
    
    # Crear servicios
    mkdir -p "$USER_HOME/.config/systemd/user"
    echo ""
    echo "Configurando servicios systemd..."
    
    # neo.service
    cat <<EOT > "$USER_HOME/.config/systemd/user/neo.service"
[Unit]
Description=Neo Core Backend Service (WatermelonD)
After=network.target sound.target

[Service]
Type=simple
Environment=PYTHONUNBUFFERED=1
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python $(pwd)/NeoCore.py
Restart=always
RestartSec=5
SyslogIdentifier=watermelon_core

[Install]
WantedBy=default.target
EOT

    # Configure sudo for WiFi scanning (no password required)
    echo "Configurando permisos sudo para escaneo WiFi..."
    sudo tee /etc/sudoers.d/watermelond-wifi > /dev/null <<EOF
# WatermelonD WiFi Scanning - No password required
$USER_NAME ALL=(ALL) NOPASSWD: /usr/sbin/iwlist * scan
$USER_NAME ALL=(ALL) NOPASSWD: /usr/sbin/iw dev * scan
$USER_NAME ALL=(ALL) NOPASSWD: /usr/bin/nmcli device wifi *
EOF
    sudo chmod 0440 /etc/sudoers.d/watermelond-wifi
    echo "✓ Permisos de escaneo WiFi configurados"

    # Recargar y Habilitar (Solo Core)
    sudo loginctl enable-linger $USER_NAME
    sudo -u $USER_NAME XDG_RUNTIME_DIR=/run/user/$USER_ID systemctl --user daemon-reload
    sudo -u $USER_NAME XDG_RUNTIME_DIR=/run/user/$USER_ID systemctl --user enable neo.service
    sudo -u $USER_NAME XDG_RUNTIME_DIR=/run/user/$USER_ID systemctl --user restart neo.service

    # Servicio Grape Updater (Auto-Update Models on Boot)
    cat <<EOT > "$USER_HOME/.config/systemd/user/grape_updater.service"
[Unit]
Description=Grape Models Auto-Updater
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory=$(pwd)
ExecStart=/bin/bash $(pwd)/resources/tools/update_grape_models.sh
SyslogIdentifier=grape_updater

[Install]
WantedBy=default.target
EOT

    sudo -u $USER_NAME XDG_RUNTIME_DIR=/run/user/$USER_ID systemctl --user enable grape_updater.service

    # --- CONFIGURACIÓN DE KIOSK ---
    if [ "$INSTALL_GUI" = true ]; then
        echo "[PASO 6/6] Configurando Kiosk (Auto-login)..."
        
        # Auto-login tty1
        sudo mkdir -p "/etc/systemd/system/getty@tty1.service.d"
        sudo bash -c "cat <<EOT > /etc/systemd/system/getty@tty1.service.d/override.conf
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USER_NAME --noclear %I \$TERM
EOT"

        # .bash_profile
        if [ -f ~/.bash_profile ]; then
            if ! grep -q "exec startx" ~/.bash_profile; then
                echo 'if [[ -z $DISPLAY ]] && [[ $(tty) = /dev/tty1 ]]; then exec startx; fi' >> ~/.bash_profile
            fi
        else
            echo 'if [[ -z $DISPLAY ]] && [[ $(tty) = /dev/tty1 ]]; then exec startx; fi' >> ~/.bash_profile
        fi

        # .xinitrc
        cat <<EOT > ~/.xinitrc
#!/bin/bash
xset -dpms
xset s off
xset s noblank
openbox &
echo "Esperando backend..."
while ! curl -s http://localhost:5000/face > /dev/null; do sleep 2; done
CHROMIUM_BIN="chromium"
command -v chromium-browser &> /dev/null && CHROMIUM_BIN="chromium-browser"
while true; do
  \$CHROMIUM_BIN --kiosk --no-first-run --disable-infobars --disable-session-crashed-bubble --disable-restore-session-state http://localhost:5000/face
  sleep 2
done
EOT
        chmod +x ~/.xinitrc
    fi

    # SSL y Seguridad
    mkdir -p config/certs
    if command -v openssl >/dev/null 2>&1 && [ ! -f "config/certs/neo.key" ]; then
        openssl req -x509 -newkey rsa:4096 -keyout "config/certs/neo.key" -out "config/certs/neo.crt" -days 3650 -nodes -subj "/CN=$(hostname)"
        chmod 600 config/certs/neo.key
        
        # Show certificate information to user
        CERT_PATH="$(pwd)/config/certs/neo.crt"
        echo ""
        echo "================================================================"
        echo "   CERTIFICADO HTTPS GENERADO"
        echo "================================================================"
        echo ""
        echo "[INFO] Se ha generado un certificado SSL autofirmado para HTTPS"
        echo "       Ubicación: $CERT_PATH"
        echo ""
        echo "[IMPORTANTE] Para evitar advertencias de seguridad en navegadores:"
        echo ""
        echo "  1. En navegadores (Chrome/Firefox):"
        echo "     - Copia el certificado a tu máquina cliente"
        echo "     - Agrégalo como 'Autoridad de certificación raíz de confianza'"
        echo ""
        echo "  2. Linux (máquina cliente):"
        echo "     sudo cp $CERT_PATH /usr/local/share/ca-certificates/watermelond.crt"
        echo "     sudo update-ca-certificates"
        echo ""
        echo "  3. Windows (máquina cliente):"
        echo "     - Abre el archivo .crt"
        echo "     - Instalar certificado → Equipo local"
        echo "     - Colocar en 'Entidades de certificación raíz de confianza'"
        echo ""
        echo "================================================================"
        echo ""
        read -p "Presiona ENTER para continuar..."
    fi

    # Configurar sudoers para acciones sin contraseña
    echo "[PASO 5.5/6] Configurando sudoers para WatermelonD..."
    SUDOERS_FILE="/etc/sudoers.d/watermelond"
    
    sudo bash -c "cat > $SUDOERS_FILE" <<EOT
# WatermelonD - Comandos sin contraseña para operaciones administrativas
$USER_NAME ALL=(ALL) NOPASSWD: /usr/bin/apt-get update
$USER_NAME ALL=(ALL) NOPASSWD: /usr/bin/apt-get upgrade
$USER_NAME ALL=(ALL) NOPASSWD: /usr/bin/apt-get clean
$USER_NAME ALL=(ALL) NOPASSWD: /usr/bin/apt-get autoremove
$USER_NAME ALL=(ALL) NOPASSWD: /usr/bin/dnf update
$USER_NAME ALL=(ALL) NOPASSWD: /usr/bin/dnf clean
$USER_NAME ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart networking
$USER_NAME ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart NetworkManager
EOT
    
    sudo chmod 440 "$SUDOERS_FILE"
    echo "Sudoers configurado en $SUDOERS_FILE"

    # Contraseña
    [ -f "resources/tools/password_helper.py" ] && $VENV_DIR/bin/python resources/tools/password_helper.py --user admin --password admin

    echo ""
    echo " Instalación Completa Finalizada."
}

# ==============================================================================
# FUNCIONES DE PERSONALIZACIÓN
# ==============================================================================

function configure_personalization() {
    # Seleccionar modo de configuración
    CONFIG_MODE=$(whiptail --title "Modo de Configuración" --menu \
        "Elige el nivel de personalización:" 15 70 2 \
        "1" "Simple - Solo opciones esenciales (Recomendado)" \
        "2" "Avanzado - Todas las opciones disponibles" \
        3>&1 1>&2 2>&3)
    
    # Si el usuario cancela, usar modo simple por defecto
    if [ $? -ne 0 ]; then
        whiptail --msgbox "Usando configuración simple por defecto." 8 50
        CONFIG_MODE="1"
    fi
    
    # Variables globales para configuración
    USER_NICKNAME="Usuario"
    CUSTOM_WAKE_WORDS=""
    WEB_PORT="5000"
    
    if [ "$CONFIG_MODE" = "1" ]; then
        configure_simple_mode
    else
        configure_advanced_mode
    fi
    
    # Aplicar todas las configuraciones
    apply_personalization_config
}

function configure_simple_mode() {
    whiptail --title "Modo Simple" --msgbox \
        "Configuraremos solo las opciones esenciales:\n\n• Nombre de usuario\n• Palabras de activación\n• Puerto web (opcional)" \
        12 60
    
    # 1. Nombre de Usuario
    USER_NICKNAME=$(whiptail --inputbox \
        "¿Cómo quieres que te llame el asistente?" \
        10 60 "Usuario" 3>&1 1>&2 2>&3)
    
    if [ $? -ne 0 ] || [ -z "$USER_NICKNAME" ]; then
        USER_NICKNAME="Usuario"
    fi
    
    # 2. Wake Words Personalizadas (Opcional)
    if whiptail --title "Palabras de Activación" --yesno \
        "Palabras actuales: neo, tio, bro\n\n¿Deseas añadir palabras personalizadas?" \
        10 60; then
        
        CUSTOM_WAKE_WORDS=$(whiptail --inputbox \
            "Introduce palabras adicionales separadas por comas:\n\nEjemplo: asistente,hola" \
            12 60 "" 3>&1 1>&2 2>&3)
    fi
    
    # 3. Puerto Web Admin (Opcional)
    if whiptail --title "Puerto Web" --yesno \
        "El puerto por defecto es 5000.\n\n¿Deseas cambiarlo?" \
        10 60; then
        
        WEB_PORT=$(whiptail --inputbox \
            "Puerto para la interfaz web:" \
            10 60 "5000" 3>&1 1>&2 2>&3)
        
        if [ $? -ne 0 ] || [ -z "$WEB_PORT" ]; then
            WEB_PORT="5000"
        fi
    fi
    
    whiptail --msgbox "Configuración simple completada." 8 50
}

function configure_advanced_mode() {
    whiptail --title "Modo Avanzado" --msgbox \
        "Configuraremos todas las opciones disponibles:\n\n• Nombre de usuario\n• Palabras de activación\n• Servidores SSH\n• Alias de red\n• Puerto web\n• Preferencias TTS" \
        14 60
    
    # 1. Nombre de Usuario
    USER_NICKNAME=$(whiptail --inputbox \
        "¿Cómo quieres que te llame el asistente?" \
        10 60 "Usuario" 3>&1 1>&2 2>&3)
    
    if [ $? -ne 0 ] || [ -z "$USER_NICKNAME" ]; then
        USER_NICKNAME="Usuario"
    fi
    
    # 2. Wake Words Personalizadas
    if whiptail --title "Palabras de Activación" --yesno \
        "Palabras actuales: neo, tio, bro\n\n¿Deseas añadir palabras personalizadas?" \
        10 60; then
        
        CUSTOM_WAKE_WORDS=$(whiptail --inputbox \
            "Introduce palabras adicionales separadas por comas:\n\nEjemplo: asistente,hola,jarvis" \
            12 60 "" 3>&1 1>&2 2>&3)
    fi
    
    # 3. Servidores SSH
    if whiptail --title "Servidores SSH" --yesno \
        "¿Deseas configurar servidores SSH remotos?\n\nPuedes agregar servidores como 'syrah' para control remoto." \
        12 60; then
        
        setup_ssh_servers_whiptail
    fi
    
    # 4. Alias de Red
    if whiptail --title "Alias de Red" --yesno \
        "¿Deseas configurar alias de red?\n\nEjemplo: router=192.168.1.1, nas=192.168.1.50" \
        12 60; then
        
        setup_network_aliases_whiptail
    fi
    
    # 5. Puerto Web Admin
    WEB_PORT=$(whiptail --inputbox \
        "Puerto para la interfaz web:" \
        10 60 "5000" 3>&1 1>&2 2>&3)
    
    if [ $? -ne 0 ] || [ -z "$WEB_PORT" ]; then
        WEB_PORT="5000"
    fi
    
    # 6. Preferencias TTS (Solo informar por ahora)
    whiptail --title "Configuración TTS" --msgbox \
        "Las preferencias de voz TTS se pueden configurar después de la instalación editando:\n\nconfig/config.json\n\nCampo: 'tts.piper_model'" \
        12 60
    
    whiptail --msgbox "Configuración avanzada completada." 8 50
}

function setup_ssh_servers_whiptail() {
    mkdir -p jsons
    echo "{}" > jsons/servers.json
    
    while true; do
        # Preguntar si desea añadir otro servidor
        if [ -f "jsons/servers.json" ] && [ "$(cat jsons/servers.json)" != "{}" ]; then
            if ! whiptail --title "Servidores SSH" --yesno \
                "¿Deseas añadir otro servidor SSH?" 8 50; then
                break
            fi
        fi
        
        # Alias del servidor
        SSH_ALIAS=$(whiptail --inputbox \
            "Alias del servidor (ej: syrah, produccion, desarrollo):" \
            10 60 "" 3>&1 1>&2 2>&3)
        
        if [ $? -ne 0 ] || [ -z "$SSH_ALIAS" ]; then
            break
        fi
        
        # Host/IP
        SSH_HOST=$(whiptail --inputbox \
            "Host o dirección IP del servidor:" \
            10 60 "" 3>&1 1>&2 2>&3)
        
        if [ $? -ne 0 ] || [ -z "$SSH_HOST" ]; then
            continue
        fi
        
        # Usuario
        SSH_USER=$(whiptail --inputbox \
            "Usuario SSH:" \
            10 60 "root" 3>&1 1>&2 2>&3)
        
        if [ $? -ne 0 ] || [ -z "$SSH_USER" ]; then
            SSH_USER="root"
        fi
        
        # Puerto
        SSH_PORT=$(whiptail --inputbox \
            "Puerto SSH:" \
            10 60 "22" 3>&1 1>&2 2>&3)
        
        if [ $? -ne 0 ] || [ -z "$SSH_PORT" ]; then
            SSH_PORT="22"
        fi
        
        # Método de autenticación
        SSH_AUTH=$(whiptail --title "Autenticación SSH" --menu \
            "Selecciona el método de autenticación:" 12 70 2 \
            "1" "Clave SSH (Recomendado)" \
            "2" "Contraseña" \
            3>&1 1>&2 2>&3)
        
        if [ "$SSH_AUTH" = "1" ]; then
            SSH_KEY=$(whiptail --inputbox \
                "Ruta a la clave privada SSH:\n\nEjemplo: ~/.ssh/id_rsa" \
                12 60 "$HOME/.ssh/id_rsa" 3>&1 1>&2 2>&3)
            
            if [ $? -ne 0 ] || [ -z "$SSH_KEY" ]; then
                whiptail --msgbox "Clave SSH no proporcionada. Servidor no añadido." 8 50
                continue
            fi
            
            python3 -c "import json; data=json.load(open('jsons/servers.json')); data['$SSH_ALIAS']={'host':'$SSH_HOST','user':'$SSH_USER','port':$SSH_PORT,'key_path':'$SSH_KEY','password':None}; json.dump(data, open('jsons/servers.json','w'), indent=4)"
        else
            SSH_PASS=$(whiptail --passwordbox \
                "Contraseña SSH para $SSH_USER@$SSH_HOST:" \
                10 60 3>&1 1>&2 2>&3)
            
            if [ $? -ne 0 ] || [ -z "$SSH_PASS" ]; then
                whiptail --msgbox "Contraseña no proporcionada. Servidor no añadido." 8 50
                continue
            fi
            
            # Ofuscar contraseña con base64
            ENC_PASS=$(echo -n "$SSH_PASS" | base64)
            python3 -c "import json; data=json.load(open('jsons/servers.json')); data['$SSH_ALIAS']={'host':'$SSH_HOST','user':'$SSH_USER','port':$SSH_PORT,'key_path':None,'password':'$ENC_PASS'}; json.dump(data, open('jsons/servers.json','w'), indent=4)"
        fi
        
        whiptail --msgbox "✓ Servidor '$SSH_ALIAS' añadido correctamente" 8 50
    done
    
    # Mostrar resumen
    if [ -f "jsons/servers.json" ] && [ "$(cat jsons/servers.json)" != "{}" ]; then
        SERVER_COUNT=$(python3 -c "import json; print(len(json.load(open('jsons/servers.json'))))")
        whiptail --msgbox "Configuración SSH completada.\n\nServidores añadidos: $SERVER_COUNT" 10 50
    fi
}

function setup_network_aliases_whiptail() {
    whiptail --title "Alias de Red" --msgbox \
        "Configura alias para dispositivos de red.\n\nEjemplos:\n• router = 192.168.1.1\n• nas = 192.168.1.50\n• servidor = 10.0.0.100" \
        14 60
    
    while true; do
        # Preguntar si desea añadir otro alias
        CURRENT_ALIASES=$(python3 -c "import json; data=json.load(open('config/skills.json')); print(len(data.get('network',{}).get('config',{}).get('aliases',{})))" 2>/dev/null || echo "0")
        
        if [ "$CURRENT_ALIASES" -gt "0" ]; then
            if ! whiptail --title "Alias de Red" --yesno \
                "Alias configurados: $CURRENT_ALIASES\n\n¿Deseas añadir otro?" 10 50; then
                break
            fi
        fi
        
        # Nombre del alias
        ALIAS_NAME=$(whiptail --inputbox \
            "Nombre del alias (ej: router, nas, servidor):" \
            10 60 "" 3>&1 1>&2 2>&3)
        
        if [ $? -ne 0 ] || [ -z "$ALIAS_NAME" ]; then
            break
        fi
        
        # IP del dispositivo
        ALIAS_IP=$(whiptail --inputbox \
            "Dirección IP de '$ALIAS_NAME':" \
            10 60 "" 3>&1 1>&2 2>&3)
        
        if [ $? -ne 0 ] || [ -z "$ALIAS_IP" ]; then
            continue
        fi
        
        # Agregar a skills.json usando Python
        python3 -c "import json; data=json.load(open('config/skills.json')); data.setdefault('network',{}).setdefault('config',{}).setdefault('aliases',{})['$ALIAS_NAME']='$ALIAS_IP'; json.dump(data, open('config/skills.json','w'), indent=4, ensure_ascii=False)"
        
        whiptail --msgbox "✓ Alias '$ALIAS_NAME' → '$ALIAS_IP' añadido" 8 50
    done
    
    # Mostrar resumen
    if [ "$CURRENT_ALIASES" -gt "0" ]; then
        whiptail --msgbox "Configuración de alias de red completada.\n\nTotal de alias: $CURRENT_ALIASES" 10 50
    fi
}

function apply_personalization_config() {
    # Crear/Actualizar config.json con las personalizaciones
    python3 << EOF
import json
import os

config_path = 'config/config.json'
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
else:
    config = {}

# Aplicar user_nickname
config['user_nickname'] = "$USER_NICKNAME"

# Aplicar wake_words personalizadas
default_wake_words = ['neo', 'tio', 'bro']
if "$CUSTOM_WAKE_WORDS".strip():
    custom = [w.strip() for w in "$CUSTOM_WAKE_WORDS".split(',')]
    config['wake_words'] = default_wake_words + custom
else:
    config['wake_words'] = default_wake_words

# Aplicar puerto web admin
if 'web_admin' not in config:
    config['web_admin'] = {}
config['web_admin']['port'] = int("$WEB_PORT")
config['web_admin']['host'] = '0.0.0.0'
config['web_admin']['debug'] = False

# Guardar
with open(config_path, 'w') as f:
    json.dump(config, f, indent=4, ensure_ascii=False)

print(" Configuración personalizada guardada")
EOF
    
    whiptail --msgbox "¡Personalización completada!\n\nTu nombre: $USER_NICKNAME\nPuerto web: $WEB_PORT" 10 50
}

# ==============================================================================
# FIN FUNCIONES DE PERSONALIZACIÓN
# ==============================================================================


function install_web_client() {
    echo "========================================="
    echo "===   Instalación Cliente Web Remoto  ==="
    echo "========================================="
    
    read -p "IP del Servidor NeoCore (ej: http://192.168.1.50:5000): " NEO_IP
    NEO_IP=${NEO_IP:-http://localhost:5000}
    
    if [[ ! "$NEO_IP" =~ ^http ]]; then NEO_IP="http://$NEO_IP"; fi
    
    echo "Instalando dependencias mínimas..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y python3-flask python3-requests python3-flask-wtf
    else
        pip install flask requests flask-wtf
    fi
    
    echo "Creando lanzador run_client.sh..."
    echo "#!/bin/bash" > run_client.sh
    echo "export NEO_API_URL='$NEO_IP'" >> run_client.sh
    echo "python3 TangerineUI/app.py" >> run_client.sh
    chmod +x run_client.sh
    
    echo "Listo. Ejecuta ./run_client.sh para iniciar."
}

function install_satellite() {
    echo "Lanzando instalador de Network Bros..."
    chmod +x resources/NB/install_nb.sh
    ./resources/NB/install_nb.sh
}

function install_dev_repos() {
    echo "Configurando entorno de desarrollo (Multi-repo)..."
    chmod +x setup_repos.sh
    ./setup_repos.sh
}

function run_tool_diagnose() {
    chmod +x resources/tools/diagnose.sh
    ./resources/tools/diagnose.sh
}

function run_tool_fix_kiosk() {
    chmod +x resources/tools/fix_kiosk.sh
    ./resources/tools/fix_kiosk.sh
}

function maintenance_menu() {
    while true; do
        echo "========================================="
        echo "===     Herramientas y Mantenimiento  ==="
        echo "========================================="
        echo "1) Diagnosticar Sistema"
        echo "2) Reparar Kiosk (Pantalla negra/Crashes)"
        echo "3) Fix Dependencias NLU"
        echo "0) Volver al menú principal"
        read -p "Opción: " TOOL_OPT
        
        case $TOOL_OPT in
            1) run_tool_diagnose ;;
            2) run_tool_fix_kiosk ;;
            3) 
                chmod +x resources/tools/fix_nlu_dependencies.sh
                ./resources/tools/fix_nlu_dependencies.sh 
                ;;
            0) break ;;
            *) echo "Opción no válida" ;;
        esac
        echo ""
        read -p "Presiona Enter para continuar..."
    done
}


# ==============================================================================
# MENÚ PRINCIPAL
# ==============================================================================

# Asegurar whiptail en menú principal también
if ! command -v whiptail &> /dev/null; then
    echo "Instalando whiptail para interfaz gráfica..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y whiptail
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y newt
    fi
fi

while true; do
    OPTION=$(whiptail --title "Instalador WatermelonD" --menu "Seleccione una opción de instalación:" 20 78 6 \
        "1" "Instalación ESTÁNDAR (Nodo Principal)" \
        "2" "Cliente Web Remoto" \
        "3" "Satélite (Network Bros)" \
        "4" "Configuración Developer (Split Repos)" \
        "5" "Herramientas / Mantenimiento" \
        "0" "Salir" \
        3>&1 1>&2 2>&3)
    
    # Si se cancela (ESC), salir
    if [ $? -ne 0 ]; then
        whiptail --msgbox "Instalación cancelada." 8 40
        exit 0
    fi

    case $OPTION in
        1) 
            whiptail --title "Instalación Estándar" --msgbox "Iniciando instalación del nodo principal...\n\nEsto instalará:\n- Core del sistema\n- Interfaz Web\n- Base de datos\n- Dependencias necesarias" 12 60
            install_standard
            exit 0
            ;;
        2) 
            whiptail --title "Cliente Web" --msgbox "Iniciando instalación del cliente web remoto..." 8 60
            install_web_client
            exit 0
            ;;
        3) 
            whiptail --title "Satélite" --msgbox "Configurando dispositivo como satélite..." 8 60
            install_satellite
            exit 0
            ;;
        4) 
            whiptail --title "Developer" --msgbox "Configurando repositorios para desarrollo..." 8 60
            install_dev_repos
            exit 0
            ;;
        5) 
            maintenance_menu
            ;;
        0) 
            whiptail --msgbox "¡Hasta pronto!" 8 40
            exit 0
            ;;
        *) 
            whiptail --msgbox "Opción inválida. Por favor intenta de nuevo." 8 50
            ;;
    esac
done
