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
        "1" "Main (Estable) - Para producción consolidada" \
        "2" "RC_180226 (Release Candidate) - Versión actual recomendada" \
        3>&1 1>&2 2>&3)
    
    if [[ "$BRANCH_OPT" == "1" ]]; then
        BRANCH="main"
    else
        # Por defecto y opción 2: rama RC con las últimas mejoras
        BRANCH="rc_180226"
    fi
    
    whiptail --msgbox "Rama seleccionada: $BRANCH" 8 50
    
    # 3. Clonar Repositorio
    if [ -d "$TARGET_DIR" ]; then
        if [ -z "$(ls -A $TARGET_DIR)" ]; then
             echo "Directorio vacío detectado. Clonando..."
             git clone -b "$BRANCH" https://github.com/OpenMacedonIA/WatermelonD.git "$TARGET_DIR"
             cd "$TARGET_DIR"
             git submodule update --init --remote --recursive
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
        git submodule update --init --remote --recursive
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
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
    TARGET_BRANCH="rc_180226"

    echo "Rama local actual: $CURRENT_BRANCH"

    # Si estamos en 'main' u otra rama antigua, migrar a la rama recomendada
    if [ "$CURRENT_BRANCH" != "$TARGET_BRANCH" ]; then
        echo "----------------------------------------------------------------"
        echo "  La rama actual ($CURRENT_BRANCH) no es la recomendada ($TARGET_BRANCH)."
        echo "  Migrando automáticamente a $TARGET_BRANCH..."
        echo "----------------------------------------------------------------"
        git fetch origin
        git checkout "$TARGET_BRANCH" || git checkout -b "$TARGET_BRANCH" --track "origin/$TARGET_BRANCH"
        CURRENT_BRANCH="$TARGET_BRANCH"
    fi

    # Actualizar la rama actual
    echo "Actualizando desde rama: $CURRENT_BRANCH"
    if git pull origin "$CURRENT_BRANCH" && git submodule update --init --remote --recursive; then
        NEW_HASH=$(git rev-parse HEAD 2>/dev/null)
        if [ "$CURRENT_HASH" != "$NEW_HASH" ]; then
            echo "----------------------------------------------------------------"
            echo "¡Se han descargado actualizaciones!"
            echo "Reiniciando el instalador para aplicar los cambios..."
            echo "----------------------------------------------------------------"
            exec "$0" "$@"
        else
            echo " Instalador ya en la última versión de $CURRENT_BRANCH."
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
        echo "  Elige cómo desplegar WatermelonD:"
        echo "----------------------------------------------------------------"
        choose_deployment_mode
        return
    fi

    echo ""
    echo "[PASO 2/6] Configurando opciones de instalación..."

    # ── GUI / Headless ────────────────────────────────────────────────
    if whiptail --title "Modo de Pantalla" --yesno \
        "¿Instalar en modo KIOSK (interfaz gráfica de pantalla completa)?\n\n• Sí  → Instala Xorg + Openbox + Chromium en modo kiosco\n• No → Modo headless/servidor (solo WebUI por red)" \
        12 68; then
        INSTALL_GUI=true
        DEPENDENCIES+=(xorg openbox chromium x11-xserver-utils wmctrl xdotool)
        echo "[OK] Modo Kiosk seleccionado."
    else
        INSTALL_GUI=false
        echo "[OK] Modo Headless seleccionado."
    fi

    # ── Optimizaciones del sistema ────────────────────────────────────
    if whiptail --title "Optimizaciones del Sistema" --yesno \
        "¿Aplicar optimizaciones para uso como appliance/servidor?\n\n• Hostname → OpenMacedonIA\n• Eliminar bloatware (LibreOffice, juegos...)\n• Swappiness reducida (mejor rendimiento RAM)\n• Governor CPU → performance\n• Reducir logs del sistema" \
        14 68; then
        OPTIMIZE_SYS=true
        echo "[OK] Se aplicarán optimizaciones."
    else
        OPTIMIZE_SYS=false
    fi
    echo "----------------------------------------------------------------"

    # Instalar Dependencias
    echo "Instalando paquetes del sistema..."
    $INSTALL_CMD "${DEPENDENCIES[@]}"

    # ── Aplicar optimizaciones ────────────────────────────────────────
    if [ "$OPTIMIZE_SYS" = true ]; then
        echo "[OPT] Aplicando optimizaciones..."
        # Hostname
        sudo hostnamectl set-hostname OpenMacedonIA
        if ! grep -q "127.0.1.1.*OpenMacedonIA" /etc/hosts; then
            sudo sed -i 's/127.0.1.1.*/127.0.1.1\tOpenMacedonIA/g' /etc/hosts
        fi
        # Bloatware
        sudo apt-get purge -y libreoffice* aisleriot gnome-mines mahjongg quadrapassel gnome-sudoku || true
        sudo apt-get autoremove -y
        # Swappiness (mejor para sistemas con suficiente RAM)
        echo 'vm.swappiness=10' | sudo tee /etc/sysctl.d/99-watermelond.conf > /dev/null
        echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.d/99-watermelond.conf > /dev/null
        sudo sysctl -p /etc/sysctl.d/99-watermelond.conf 2>/dev/null || true
        # CPU Governor → performance (si cpufrequtils disponible)
        if command -v cpufreq-set &>/dev/null; then
            sudo cpufreq-set -g performance 2>/dev/null || true
        elif [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
            echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null 2>&1 || true
            # Hacer persistente en el arranque
            echo 'GOVERNOR="performance"' | sudo tee /etc/default/cpufrequtils > /dev/null 2>/dev/null || true
        fi
        # Reducir journald logs
        sudo sed -i 's/#SystemMaxUse=/SystemMaxUse=200M/' /etc/systemd/journald.conf 2>/dev/null || true
        sudo sed -i 's/#RuntimeMaxUse=/RuntimeMaxUse=100M/' /etc/systemd/journald.conf 2>/dev/null || true
        sudo systemctl restart systemd-journald 2>/dev/null || true
        # UFW básico: abrir solo el puerto de Neo
        if command -v ufw &>/dev/null; then
            sudo ufw allow 5000/tcp 2>/dev/null || true
            sudo ufw --force enable 2>/dev/null || true
        fi
        echo "[OPT] Optimizaciones aplicadas."
    fi

    # Habilitar Mosquitto
    if [ -d /run/systemd/system ] && command -v systemctl &>/dev/null; then
        if systemctl list-unit-files | grep -q mosquitto.service; then
            sudo systemctl enable mosquitto || true
            sudo systemctl start mosquitto || true
        fi
    else
        echo " [INFO] Omitiendo habilitación de mosquitto via systemctl (systemd no detectado)"
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
    # Inicialización de la configuración (usar .example como plantilla)
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
    
    # Sherpa-ONNX (Motor STT por Defecto)
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
    # Gemma (MANGO Legado - Eliminado a favor de Grape)
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

    # Modelo de Decision Router (Grape-Route)
    # Eliminación de posibles clones malos (archivos HTML) de descargas sin LFS
    [ -d "models/grape-route" ] && rm -rf "models/grape-route"

    if [ ! -d "models/grape-route" ]; then
        echo "Descargando modelo Decision Router (Grape-Route)..."
        git clone https://huggingface.co/jrodriiguezg/minilm-l12-grape-route models/grape-route
    fi

    # Grape-Syrah (Red)
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

    # Configurar sudo para el escaneo WiFi (sin contraseña)
    echo "Configurando permisos sudo para escaneo WiFi..."
    sudo tee /etc/sudoers.d/watermelond-wifi > /dev/null <<EOF
# Escaneo WiFi de WatermelonD - No requiere contraseña
$USER_NAME ALL=(ALL) NOPASSWD: /usr/sbin/iwlist * scan
$USER_NAME ALL=(ALL) NOPASSWD: /usr/sbin/iw dev * scan
$USER_NAME ALL=(ALL) NOPASSWD: /usr/bin/nmcli device wifi *
EOF
    sudo chmod 0440 /etc/sudoers.d/watermelond-wifi
    echo " Permisos de escaneo WiFi configurados"

    # ── Habilitar linger para que los servicios de usuario arranquen sin login ──
    sudo loginctl enable-linger $USER_NAME

    # ── Servicio Principal: neo.service ───────────────────────────────────────
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

    # ── Servicio Grape Updater ────────────────────────────────────────────────
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

    # ── Recargar y habilitar servicios (siempre, kiosk o headless) ───────────
    sudo -u $USER_NAME XDG_RUNTIME_DIR=/run/user/$USER_ID systemctl --user daemon-reload
    sudo -u $USER_NAME XDG_RUNTIME_DIR=/run/user/$USER_ID systemctl --user enable neo.service
    sudo -u $USER_NAME XDG_RUNTIME_DIR=/run/user/$USER_ID systemctl --user enable grape_updater.service
    sudo -u $USER_NAME XDG_RUNTIME_DIR=/run/user/$USER_ID systemctl --user restart neo.service

    if [ "$INSTALL_GUI" = true ]; then
        echo "[PASO 6/6] Configurando Kiosk (Auto-login en tty1)..."

        # Auto-login tty1
        sudo mkdir -p "/etc/systemd/system/getty@tty1.service.d"
        sudo tee /etc/systemd/system/getty@tty1.service.d/override.conf > /dev/null <<EOT
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USER_NAME --noclear %I \$TERM
EOT

        # Añadir startx a .bash_profile solo si aún no está
        local PROFILE_FILE="$USER_HOME/.bash_profile"
        [ -f "$USER_HOME/.profile" ] && PROFILE_FILE="$USER_HOME/.profile"
        if ! grep -q 'exec startx' "$PROFILE_FILE" 2>/dev/null; then
            echo 'if [[ -z $DISPLAY ]] && [[ $(tty) = /dev/tty1 ]]; then exec startx; fi' >> "$PROFILE_FILE"
        fi

        # .xinitrc — detecta chromium o chromium-browser
        cat > "$USER_HOME/.xinitrc" <<'XINITEOF'
#!/bin/bash
xset -dpms
xset s off
xset s noblank
openbox &
echo "Esperando a que NeoCore arranque..."
NEO_URL="https://localhost:5000"
until curl -sk "$NEO_URL/face" > /dev/null 2>&1; do sleep 2; done
CHROMIUM_BIN="chromium"
command -v chromium-browser &>/dev/null && CHROMIUM_BIN="chromium-browser"
while true; do
  $CHROMIUM_BIN --kiosk --no-first-run --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --disable-translate \
    --noerrdialogs \
    "$NEO_URL/face"
  sleep 3
done
XINITEOF
        chmod +x "$USER_HOME/.xinitrc"

        echo "[OK] Kiosk configurado. El sistema arrancará en modo pantalla completa en tty1."
    else
        echo "[OK] Modo headless. Accede a NeoCore por red en https://$(hostname -I | awk '{print $1}'):5000"
    fi

    # SSL y Seguridad
    mkdir -p config/certs
    if command -v openssl >/dev/null 2>&1 && [ ! -f "config/certs/neo.key" ]; then
        openssl req -x509 -newkey rsa:4096 -keyout "config/certs/neo.key" -out "config/certs/neo.crt" -days 3650 -nodes -subj "/CN=$(hostname)"
        chmod 600 config/certs/neo.key
        
        # Mostrar información del certificado al usuario
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

    # 2.5 Interfaz de Usuario / Face
    if whiptail --title "Interfaz Visual de TangerineUI" --yesno \
        "¿Deseas usar la Nueva Interfaz Simple (Recomendada)?\n\n- Sí: Interfaz de cara minimalista.\n- No: Interfaz 'Legacy' con logs y gráficas en pantalla." \
        12 60; then
        USE_LEGACY_FACE="false"
    else
        USE_LEGACY_FACE="true"
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
        "Configuraremos todas las opciones:\n\n• Nombre de usuario y contraseña WebUI\n• Palabras de activación\n• Motor STT (Sherpa small/medium)\n• Idioma y voz TTS\n• Zona horaria\n• Servidores SSH\n• Alias de red\n• Puerto web" \
        16 60

    # 1. Nombre de Usuario
    USER_NICKNAME=$(whiptail --inputbox \
        "¿Cómo quieres que te llame el asistente?" \
        10 60 "Usuario" 3>&1 1>&2 2>&3)
    [ $? -ne 0 ] || [ -z "$USER_NICKNAME" ] && USER_NICKNAME="Usuario"

    # 1b. Contraseña WebUI (panel de administración)
    WEBUI_PASS=$(whiptail --passwordbox \
        "Contraseña para el panel WebUI (usuario: admin):\n\nDeja vacío para usar 'admin' por defecto." \
        10 60 3>&1 1>&2 2>&3)
    [ $? -ne 0 ] && WEBUI_PASS="admin"
    WEBUI_PASS="${WEBUI_PASS:-admin}"

    # 2. Wake Words
    if whiptail --title "Palabras de Activación" --yesno \
        "Palabras actuales: neo, tio, bro\n\n¿Deseas añadir palabras personalizadas?" \
        10 60; then
        CUSTOM_WAKE_WORDS=$(whiptail --inputbox \
            "Introduce palabras adicionales separadas por comas:\n\nEjemplo: asistente,jarvis,oye" \
            12 60 "" 3>&1 1>&2 2>&3)
    fi

    # 3. Interfaz Face
    if whiptail --title "Interfaz Visual" --yesno \
        "¿Usar la interfaz de cara minimalista (Recomendada)?\n\n• Sí → Cara animada con ojos (nueva)\n• No → Interfaz legacy con logs" \
        12 60; then
        USE_LEGACY_FACE="false"
    else
        USE_LEGACY_FACE="true"
    fi

    # 4. Motor STT
    STT_MODEL_SIZE=$(whiptail --title "Motor STT" --menu \
        "Elige el modelo de transcripción de voz:\n(Mayor = más preciso pero más lento y usa más memoria)" 14 68 2 \
        "small"  "Sherpa small  — Rápido, apto para Raspberry Pi / bajo consumo" \
        "medium" "Sherpa medium — Mayor precisión, recomendado para PC" \
        3>&1 1>&2 2>&3) || STT_MODEL_SIZE="small"

    # 5. Zona horaria
    TZ_ZONE=$(whiptail --inputbox \
        "Zona horaria del sistema:\n\nEjemplos: Europe/Madrid, America/Mexico_City, UTC" \
        10 60 "Europe/Madrid" 3>&1 1>&2 2>&3)
    [ $? -ne 0 ] || [ -z "$TZ_ZONE" ] && TZ_ZONE="Europe/Madrid"
    sudo timedatectl set-timezone "$TZ_ZONE" 2>/dev/null || true

    # 6. Servidores SSH
    if whiptail --title "Servidores SSH" --yesno \
        "¿Configurar servidores SSH remotos para control remoto?" 8 60; then
        setup_ssh_servers_whiptail
    fi

    # 7. Alias de Red
    if whiptail --title "Alias de Red" --yesno \
        "¿Configurar alias de red?\n\nEjemplo: router=192.168.1.1, nas=192.168.1.50" \
        10 60; then
        setup_network_aliases_whiptail
    fi

    # 8. Puerto Web
    WEB_PORT=$(whiptail --inputbox "Puerto para la interfaz web:" \
        8 60 "5000" 3>&1 1>&2 2>&3)
    [ $? -ne 0 ] || [ -z "$WEB_PORT" ] && WEB_PORT="5000"

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
        
        whiptail --msgbox " Servidor '$SSH_ALIAS' añadido correctamente" 8 50
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
        
        whiptail --msgbox " Alias '$ALIAS_NAME' → '$ALIAS_IP' añadido" 8 50
    done
    
    # Mostrar resumen
    if [ "$CURRENT_ALIASES" -gt "0" ]; then
        whiptail --msgbox "Configuración de alias de red completada.\n\nTotal de alias: $CURRENT_ALIASES" 10 50
    fi
}

function apply_personalization_config() {
    local _stt_model="${STT_MODEL_SIZE:-small}"
    local _tz="${TZ_ZONE:-Europe/Madrid}"
    local _webui_pass="${WEBUI_PASS:-admin}"

    # Usar python3 del venv si está disponible, si no el del sistema
    local PY_BIN="python3"
    [ -f "$(pwd)/venv/bin/python3" ] && PY_BIN="$(pwd)/venv/bin/python3"

    $PY_BIN << EOF
import json, os, subprocess

config_path = 'config/config.json'
config = {}
if os.path.exists(config_path):
    try:
        with open(config_path) as f:
            config = json.load(f)
    except Exception:
        config = {}

# Identidad
config['user_nickname'] = "$USER_NICKNAME"

# Wake words
default_ww = ['neo', 'tio', 'bro']
custom_raw = "$CUSTOM_WAKE_WORDS".strip()
if custom_raw:
    custom = [w.strip() for w in custom_raw.split(',') if w.strip()]
    config['wake_words'] = default_ww + custom
else:
    config['wake_words'] = default_ww

# WebUI
config.setdefault('web_admin', {})
config['web_admin']['port'] = int("$WEB_PORT")
config['web_admin']['host'] = '0.0.0.0'
config['web_admin']['debug'] = False

# Interfaz face
config.setdefault('tangerine', {})
config['tangerine']['use_legacy_face'] = ("$USE_LEGACY_FACE".lower() == 'true')

# STT
config.setdefault('stt', {})
config['stt']['engine'] = 'sherpa'
config['stt']['sherpa_model_path'] = f'models/sherpa/sherpa-onnx-whisper-${_stt_model}'

# Zona horaria en config
config['timezone'] = "${_tz}"

with open(config_path, 'w') as f:
    json.dump(config, f, indent=4, ensure_ascii=False)
print(' config.json actualizado correctamente')
EOF

    # Aplicar contraseña WebUI via helper
    if [ -f "resources/tools/password_helper.py" ]; then
        "$(pwd)/venv/bin/python" resources/tools/password_helper.py \
            --user admin --password "$_webui_pass" 2>/dev/null || true
    fi

    # Descargar modelo STT seleccionado si es medium y no existe
    if [ "$_stt_model" = "medium" ] && [ ! -d "models/sherpa/sherpa-onnx-whisper-medium" ]; then
        echo "Descargando modelo Sherpa-ONNX Whisper medium (esto puede tardar)..."
        [ -f "resources/tools/download_sherpa_model.py" ] && \
            "$(pwd)/venv/bin/python" resources/tools/download_sherpa_model.py --model medium || true
    fi

    whiptail --msgbox "¡Personalización completada!\n\n• Nombre: $USER_NICKNAME\n• Puerto WebUI: $WEB_PORT\n• Modelo STT: Sherpa $_stt_model\n• Zona horaria: $_tz" 12 55
}

# ==============================================================================
# FIN FUNCIONES DE PERSONALIZACIÓN
# ==============================================================================


# ==============================================================================
# MODOS DE DESPLIEGUE: DISTROBOX / DOCKER / PODMAN
# ==============================================================================

function choose_deployment_mode() {
    local DEPLOY_OPT
    DEPLOY_OPT=$(whiptail --title "Modo de Despliegue" --menu \
        "Sistema no-Debian detectado.\nElige cómo desplegar WatermelonD:" 18 72 4 \
        "1" "Distrobox    — Contenedor ligero integrado en el sistema" \
        "2" "Docker       — Contenedor Docker (requiere Docker instalado)" \
        "3" "Podman       — Alternativa rootless a Docker" \
        "4" "Instalación directa (sin contenedor, bajo tu responsabilidad)" \
        3>&1 1>&2 2>&3) || { whiptail --msgbox "Cancelado." 8 40; return; }

    case "$DEPLOY_OPT" in
        1) install_distrobox ;;
        2) install_docker    ;;
        3) install_podman    ;;
        4)
            # Continuar con la instalación estándar sin contenedor
            PKG_MANAGER="unknown"
            INSTALL_CMD="echo [DRY-RUN]"
            whiptail --msgbox "Modo directo seleccionado.\nDebes instalar manualmente las dependencias del sistema." 10 60
            ;;
    esac
}

# ── Distrobox ─────────────────────────────────────────────────────────────────

function install_distrobox() {
    echo ""
    echo "========================================="
    echo "===    DESPLIEGUE VIA DISTROBOX       ==="
    echo "========================================="

    # 1. Instalar Distrobox si no está
    if ! command -v distrobox &> /dev/null; then
        echo "Instalando Distrobox..."
        curl -s https://raw.githubusercontent.com/89luca89/distrobox/main/install | bash -s -- --prefix ~/.local
        export PATH="$HOME/.local/bin:$PATH"
    fi

    # 2. Necesitamos Podman o Docker como backend
    if ! command -v podman &> /dev/null && ! command -v docker &> /dev/null; then
        whiptail --title "Backend Requerido" --msgbox \
            "Distrobox necesita Podman o Docker como backend.\n\nInstala uno de ellos primero:\n  • Podman: https://podman.io/getting-started/installation\n  • Docker: https://docs.docker.com/get-docker/" \
            14 70
        echo "Instalando Podman como backend de Distrobox..."
        # Intentar instalar según distro
        if command -v dnf &>/dev/null;  then sudo dnf install -y podman
        elif command -v pacman &>/dev/null; then sudo pacman -Sy --noconfirm podman
        elif command -v zypper &>/dev/null; then sudo zypper install -y podman
        elif command -v xbps-install &>/dev/null; then sudo xbps-install -Sy podman
        else
            echo "No se pudo instalar Podman automáticamente. Instálalo manualmente."
            exit 1
        fi
    fi

    local BOX_NAME="watermelond"
    local BOX_IMAGE="ubuntu:22.04"

    # Preguntar imagen base
    BOX_IMAGE=$(whiptail --inputbox \
        "Imagen base para Distrobox:\n(Recomendada: ubuntu:22.04)" \
        10 60 "ubuntu:22.04" 3>&1 1>&2 2>&3) || BOX_IMAGE="ubuntu:22.04"

    echo "Creando contenedor Distrobox '$BOX_NAME' con imagen $BOX_IMAGE..."
    # --pull=newer garantiza imagen actualizada; --yes evita confirmación interactiva
    distrobox create \
        --name "$BOX_NAME" \
        --image "$BOX_IMAGE" \
        --yes \
        --no-entry 2>/dev/null || distrobox create --name "$BOX_NAME" --image "$BOX_IMAGE" --yes || true

    # Crear script temporal con los comandos de instalación dentro del box
    local SETUP_SCRIPT="/tmp/watermelond_box_setup.sh"
    cat > "$SETUP_SCRIPT" << 'BOXSETUP'
#!/bin/bash
set -e
if ! command -v git &> /dev/null; then
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y git
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y git
    elif command -v pacman &> /dev/null; then
        sudo pacman -Sy --noconfirm git
    elif command -v zypper &> /dev/null; then
        sudo zypper install -y git
    fi
fi
cd "$HOME"
if [ ! -d WatermelonD ]; then
    git clone https://github.com/OpenMacedonIA/WatermelonD.git
fi
cd WatermelonD
git submodule update --init --remote --recursive
bash install.sh
BOXSETUP
    chmod +x "$SETUP_SCRIPT"

    echo "Instalando WatermelonD dentro de Distrobox..."
    distrobox enter "$BOX_NAME" -- bash "$SETUP_SCRIPT"
    rm -f "$SETUP_SCRIPT"

    # Crear lanzador en el host
    mkdir -p "$HOME/.local/bin"
    cat > "$HOME/.local/bin/watermelond" << 'LAUNCHER'
#!/bin/bash
distrobox enter watermelond -- bash -c 'cd ~/WatermelonD && source venv/bin/activate && python NeoCore.py'
LAUNCHER
    chmod +x "$HOME/.local/bin/watermelond"

    # Añadir ~/.local/bin al PATH si no está
    if ! grep -q 'HOME/.local/bin' "$HOME/.bashrc" 2>/dev/null; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    fi

    whiptail --msgbox "Distrobox configurado.\n\nLanza WatermelonD con:\n  watermelond\n\nO accede al contenedor con:\n  distrobox enter watermelond" 14 62
}

# ── Docker ────────────────────────────────────────────────────────────────────

function install_docker() {
    echo ""
    echo "========================================="
    echo "===     DESPLIEGUE VIA DOCKER         ==="
    echo "========================================="

    # 1. Comprobar/instalar Docker
    if ! command -v docker &> /dev/null; then
        echo "Docker no encontrado. Instalando..."
        if command -v apt-get &>/dev/null; then
            curl -fsSL https://get.docker.com | sudo bash
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y docker
            sudo systemctl enable --now docker
        elif command -v pacman &>/dev/null; then
            sudo pacman -Sy --noconfirm docker
            sudo systemctl enable --now docker
        else
            whiptail --msgbox "Instala Docker manualmente desde:\nhttps://docs.docker.com/get-docker/" 10 60
            exit 1
        fi
        sudo usermod -aG docker "$USER"
        echo "[AVISO] Puede que necesites cerrar sesión para aplicar grupo docker."
    fi

    # 2. Comprobar/instalar docker-compose (v2 o v1)
    if ! docker compose version &>/dev/null && ! command -v docker-compose &>/dev/null; then
        echo "Instalando docker-compose plugin..."
        sudo apt-get install -y docker-compose-plugin 2>/dev/null || \
        pip3 install docker-compose 2>/dev/null || \
        echo "[AVISO] docker-compose no instalado. Instala manualmente si lo necesitas."
    fi

    # 3. Generar Dockerfile si no existe
    _generate_dockerfile

    # 4. Generar docker-compose.yml si no existe
    _generate_docker_compose

    # 5. Preguntar modo de arranque
    local DOCKER_MODE
    DOCKER_MODE=$(whiptail --title "Modo Docker" --menu \
        "Elige cómo lanzar WatermelonD:" 14 70 3 \
        "1" "docker-compose up   (recomendado, con volumen persistente)" \
        "2" "docker run          (simple, sin compose)" \
        "3" "Solo generar imagen (sin levantar)" \
        3>&1 1>&2 2>&3) || DOCKER_MODE="1"

    echo "Construyendo imagen watermelond..."
    docker build -t watermelond:latest .

    case "$DOCKER_MODE" in
        1)
            echo "Levantando con docker-compose..."
            if docker compose version &>/dev/null; then
                docker compose up -d
            else
                docker-compose up -d
            fi
            ;;
        2)
            echo "Levantando con docker run..."
            docker run -d \
                --name watermelond \
                --restart unless-stopped \
                --device /dev/snd \
                --privileged \
                -p 5000:5000 \
                -v "$(pwd)/config:/app/config" \
                -v "$(pwd)/models:/app/models" \
                -v "$(pwd)/database:/app/database" \
                -v "$(pwd)/logs:/app/logs" \
                watermelond:latest
            ;;
        3)
            echo "Imagen construida. Usa 'docker run' o 'docker-compose up' para lanzar."
            ;;
    esac

    whiptail --msgbox "Docker configurado.\n\nComandos útiles:\n  docker ps                    → ver contenedores\n  docker compose logs -f       → ver logs\n  docker compose restart       → reiniciar\n  docker exec -it watermelond bash → entrar" 14 70
}

# ── Podman ────────────────────────────────────────────────────────────────────

function install_podman() {
    echo ""
    echo "========================================="
    echo "===     DESPLIEGUE VIA PODMAN         ==="
    echo "========================================="

    # 1. Comprobar/instalar Podman
    if ! command -v podman &> /dev/null; then
        echo "Podman no encontrado. Instalando..."
        if command -v apt-get &>/dev/null;   then sudo apt-get install -y podman
        elif command -v dnf &>/dev/null;     then sudo dnf install -y podman
        elif command -v pacman &>/dev/null;  then sudo pacman -Sy --noconfirm podman
        elif command -v zypper &>/dev/null;  then sudo zypper install -y podman
        elif command -v xbps-install &>/dev/null; then sudo xbps-install -Sy podman
        else
            whiptail --msgbox "Instala Podman manualmente desde:\nhttps://podman.io/getting-started/installation" 10 60
            exit 1
        fi
    fi

    # 2. Generar Dockerfile y compose si no existen
    _generate_dockerfile
    _generate_docker_compose "podman"

    # 3. Preguntar modo
    local PODMAN_MODE
    PODMAN_MODE=$(whiptail --title "Modo Podman" --menu \
        "Elige cómo lanzar WatermelonD:" 14 70 3 \
        "1" "podman-compose up   (recomendado, persistente)" \
        "2" "podman run          (simple, sin compose)" \
        "3" "Solo construir imagen" \
        3>&1 1>&2 2>&3) || PODMAN_MODE="1"

    echo "Construyendo imagen con Podman (rootless)..."
    podman build -t watermelond:latest .

    case "$PODMAN_MODE" in
        1)
            if ! command -v podman-compose &>/dev/null; then
                echo "Instalando podman-compose..."
                pip3 install podman-compose 2>/dev/null || \
                    echo "[AVISO] Instala podman-compose manualmente si es necesario."
            fi
            podman-compose up -d
            ;;
        2)
            podman run -d \
                --name watermelond \
                --restart unless-stopped \
                --privileged \
                -p 5000:5000 \
                -v "$(pwd)/config:/app/config:Z" \
                -v "$(pwd)/models:/app/models:Z" \
                -v "$(pwd)/database:/app/database:Z" \
                -v "$(pwd)/logs:/app/logs:Z" \
                watermelond:latest

            # Autostart con systemd rootless (compatible Podman 3.x y 4.x)
            mkdir -p "$HOME/.config/systemd/user"
            # Podman 4.x: usar `podman generate systemd` (aún funciona aunque deprecated)
            # Podman 5.x: usar quadlets (archivo .container en ~/.config/containers/systemd/)
            local PODMAN_MAJOR
            PODMAN_MAJOR=$(podman --version | grep -oP '\d+' | head -1)
            if [ "${PODMAN_MAJOR:-3}" -ge 5 ]; then
                # Quadlet (Podman 5+)
                mkdir -p "$HOME/.config/containers/systemd"
                cat > "$HOME/.config/containers/systemd/watermelond.container" << QUADLET
[Unit]
Description=WatermelonD NeoCore
After=network-online.target

[Container]
Image=watermelond:latest
PublishPort=5000:5000
Volume=$(pwd)/config:/app/config:Z
Volume=$(pwd)/models:/app/models:Z
Volume=$(pwd)/logs:/app/logs:Z
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
QUADLET
            else
                # Podman 3/4: generate systemd
                cd /tmp
                podman generate systemd --name watermelond --files --new 2>/dev/null && \
                    mv /tmp/container-watermelond.service "$HOME/.config/systemd/user/" || true
                cd - > /dev/null
            fi
            systemctl --user daemon-reload
            systemctl --user enable --now container-watermelond.service 2>/dev/null || \
            systemctl --user enable --now watermelond 2>/dev/null || true
            ;;
        3)
            echo "Imagen Podman construida. Usa 'podman run' o 'podman-compose up' para lanzar."
            ;;
    esac

    whiptail --msgbox "Podman configurado.\n\nComandos útiles:\n  podman ps                        → contenedores\n  podman logs -f watermelond       → logs\n  podman restart watermelond       → reiniciar\n  podman exec -it watermelond bash → entrar" 14 72
}

# ── Generadores de Dockerfile y Compose ───────────────────────────────────────

function _generate_dockerfile() {
    if [ -f "Dockerfile" ]; then
        echo " Dockerfile ya existe, no se sobreescribe."
        return
    fi
    echo "Generando Dockerfile..."
    cat > Dockerfile << 'DOCKEREOF'
# WatermelonD — Dockerfile
# Compatible con Docker y Podman
FROM ubuntu:22.04

LABEL org.opencontainers.image.title="WatermelonD"
LABEL org.opencontainers.image.description="NeoCore AI Assistant Backend"
LABEL org.opencontainers.image.source="https://github.com/OpenMacedonIA/WatermelonD"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    JACK_NO_START_SERVER=1 \
    TZ=Europe/Madrid

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-dev python3-pip python3-venv \
    portaudio19-dev python3-pyaudio \
    alsa-utils alsa-base libasound2 \
    libvlc-dev vlc-bin \
    ffmpeg git git-lfs curl wget sqlite3 cmake \
    libbluetooth-dev bluez bluez-tools \
    network-manager wireless-tools iw \
    mosquitto mosquitto-clients \
    build-essential libssl-dev libffi-dev \
    libfann-dev swig pkg-config \
    whiptail nano \
    && rm -rf /var/lib/apt/lists/*

# Compilar e instalar libfann desde código fuente (requerido para el wheel de fann2)
RUN git clone https://github.com/libfann/fann.git /tmp/fann && \
    cd /tmp/fann && cmake . && make && make install && \
    ldconfig && rm -rf /tmp/fann

# Crear usuario no-root para el servicio
RUN useradd -ms /bin/bash neo
WORKDIR /app
COPY --chown=neo:neo . .

# Crear venv e instalar dependencias Python
RUN python3 -m venv venv && \
    venv/bin/pip install --upgrade pip && \
    venv/bin/pip install -r requirements.txt && \
    venv/bin/pip install Flask-WTF eventlet Flask-Limiter

# Crear directorios necesarios
RUN mkdir -p logs config database models piper/voices && \
    chown -R neo:neo /app

# Copiar config base si no existe
RUN [ -f config/config.json ] || ([ -f config/config.json.example ] && cp config/config.json.example config/config.json) || echo '{}' > config/config.json

USER neo

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/dashboard || exit 1

CMD ["venv/bin/python", "NeoCore.py"]
DOCKEREOF
    echo " Dockerfile generado."
}

function _generate_docker_compose() {
    local ENGINE="${1:-docker}"
    if [ -f "docker-compose.yml" ] || [ -f "compose.yml" ]; then
        echo " docker-compose.yml ya existe, no se sobreescribe."
        return
    fi
    echo "Generando docker-compose.yml..."
    # La etiqueta :Z en volumes es necesaria para Podman con SELinux
    local VOL_SUFFIX=""
    [ "$ENGINE" = "podman" ] && VOL_SUFFIX=":Z"

    cat > docker-compose.yml << COMPOSEEOF
# WatermelonD — docker-compose.yml
# Compatible con docker compose v2 y podman-compose
name: watermelond

services:
  neocore:
    build: .
    image: watermelond:latest
    container_name: watermelond
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - ./config:/app/config${VOL_SUFFIX}
      - ./models:/app/models${VOL_SUFFIX}
      - ./database:/app/database${VOL_SUFFIX}
      - ./logs:/app/logs${VOL_SUFFIX}
      - ./piper:/app/piper${VOL_SUFFIX}
    environment:
      - PYTHONUNBUFFERED=1
      - JACK_NO_START_SERVER=1
      - TZ=Europe/Madrid
    # Acceso a audio del host (micrófono y altavoz)
    # En Podman puede necesitar --privileged o configuración de /dev
    devices:
      - /dev/snd:/dev/snd
    group_add:
      - audio
    # healthcheck integrado en el Dockerfile
    # Descomentar para logs detallados:
    # logging:
    #   driver: "json-file"
    #   options:
    #     max-size: "10m"
    #     max-file: "3"
COMPOSEEOF
    echo " docker-compose.yml generado."
}


function install_web_client() {
    echo ""
    echo "========================================="
    echo "===   Instalación Cliente Web Remoto  ==="
    echo "========================================="

    NEO_IP=$(whiptail --inputbox \
        "Dirección del servidor NeoCore:\n\nEjemplo: https://192.168.1.50:5000" \
        10 68 "https://" 3>&1 1>&2 2>&3) || NEO_IP=""
    [ -z "$NEO_IP" ] && { whiptail --msgbox "Cancelado. No se configuró el cliente." 8 50; return; }
    [[ ! "$NEO_IP" =~ ^http ]] && NEO_IP="https://$NEO_IP"

    echo "Instalando dependencias mínimas..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y python3-flask python3-requests python3-flask-wtf
    elif command -v pip3 &>/dev/null; then
        pip3 install flask requests flask-wtf
    fi

    echo "Creando lanzador run_client.sh..."
    cat > run_client.sh << CLIENTEOF
#!/bin/bash
export NEO_API_URL='$NEO_IP'
exec python3 TangerineUI/app.py
CLIENTEOF
    chmod +x run_client.sh

    whiptail --msgbox "Cliente web configurado.\n\nServidor: $NEO_IP\n\nEjecuta ./run_client.sh para iniciar." 10 60
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
        local TOOL_OPT
        TOOL_OPT=$(whiptail --title "Herramientas y Mantenimiento" --menu \
            "Selecciona una herramienta:" 20 72 8 \
            "1" "Diagnosticar Sistema" \
            "2" "Reparar Kiosk (pantalla negra / crashes)" \
            "3" "Fix Dependencias NLU" \
            "4" "Ver estado servicios systemd" \
            "5" "Ver logs de NeoCore en vivo" \
            "6" "Reiniciar servicio NeoCore" \
            "7" "Actualizar modelos Grape (git pull)" \
            "0" "Volver al menú principal" \
            3>&1 1>&2 2>&3) || break

        case $TOOL_OPT in
            1) run_tool_diagnose ;;
            2) run_tool_fix_kiosk ;;
            3)
                [ -f resources/tools/fix_nlu_dependencies.sh ] && \
                    chmod +x resources/tools/fix_nlu_dependencies.sh && \
                    ./resources/tools/fix_nlu_dependencies.sh
                ;;
            4)
                systemctl --user status neo.service 2>&1 | head -30
                read -p "Presiona Enter para continuar..."
                ;;
            5)
                journalctl --user -u neo.service -f --no-pager 2>/dev/null || \
                    tail -f logs/app.log 2>/dev/null || \
                    echo "No se pudo abrir el log. Revisa logs/app.log manualmente."
                ;;
            6)
                local U_NAME=$(whoami)
                local U_ID=$(id -u)
                sudo -u $U_NAME XDG_RUNTIME_DIR=/run/user/$U_ID systemctl --user restart neo.service && \
                    whiptail --msgbox "Servicio NeoCore reiniciado." 8 40 || \
                    whiptail --msgbox "Error al reiniciar. Comprueba que neo.service está instalado." 8 60
                ;;
            7)
                echo "Actualizando modelos Grape..."
                for model_dir in models/chardonnay models/malbec models/pinot models/syrah models/grape-route; do
                    if [ -d "$model_dir/.git" ]; then
                        echo "Actualizando $model_dir..."
                        git -C "$model_dir" pull 2>/dev/null || echo "  [WARN] No se pudo actualizar $model_dir"
                    fi
                done
                whiptail --msgbox "Actualización de modelos completada." 8 50
                ;;
            0) break ;;
        esac
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
    OPTION=$(whiptail --title "Instalador WatermelonD" --menu "Seleccione una opción de instalación:" 24 78 9 \
        "1" "Instalación ESTÁNDAR (Nodo Principal — sistema Debian/Ubuntu)" \
        "2" "Despliegue via Distrobox (cualquier distro, ligero)" \
        "3" "Despliegue via Docker" \
        "4" "Despliegue via Podman (rootless)" \
        "5" "Cliente Web Remoto" \
        "6" "Satélite (Network Bros)" \
        "7" "Configuración Developer (Split Repos)" \
        "8" "Herramientas / Mantenimiento" \
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
            whiptail --title "Distrobox" --msgbox "Configurando WatermelonD en un contenedor Distrobox..." 8 60
            install_distrobox
            exit 0
            ;;
        3)
            whiptail --title "Docker" --msgbox "Configurando despliegue con Docker..." 8 60
            install_docker
            exit 0
            ;;
        4)
            whiptail --title "Podman" --msgbox "Configurando despliegue con Podman (rootless)..." 8 60
            install_podman
            exit 0
            ;;
        5)
            whiptail --title "Cliente Web" --msgbox "Iniciando instalación del cliente web remoto..." 8 60
            install_web_client
            exit 0
            ;;
        6)
            whiptail --title "Satélite" --msgbox "Configurando dispositivo como satélite..." 8 60
            install_satellite
            exit 0
            ;;
        7)
            whiptail --title "Developer" --msgbox "Configurando repositorios para desarrollo..." 8 60
            install_dev_repos
            exit 0
            ;;
        8)
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
