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
        "2" "Next (Testing) - Últimas funciones (Inestable)" \
        3>&1 1>&2 2>&3)
    
    if [[ "$BRANCH_OPT" == "2" ]]; then
        BRANCH="next"
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
    if git pull && git submodule update --init --recursive; then
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

    # --- INICIALIZACIÓN BD ---
    echo "[PASO 3.2/6] Inicializando BD..."
    # (Autocuración eliminada por brevedad, asumiendo que el archivo existe o el usuario lo restaura)
    export PYTHONPATH=$(pwd)
    $VENV_DIR/bin/python database/init_db.py

    # --- MODELOS ---
    echo "[PASO 4/6] Configurando Modelos..."
    
    # Vosk
    if [ ! -d "vosk-models/es" ]; then
        echo "Descargando Vosk ES..."
        mkdir -p vosk-models
        wget -q -O vosk.zip https://alphacephei.com/vosk/models/vosk-model-es-0.42.zip
        unzip -q vosk.zip -d vosk-models/
        mv vosk-models/vosk-model-es-0.42 vosk-models/es
        rm vosk.zip
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
