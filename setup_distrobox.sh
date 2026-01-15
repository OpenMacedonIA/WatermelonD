#!/bin/bash

# setup_distrobox.sh
# Script de configuración del entorno Distrobox para NeoCore.
# Ideal para sistemas inmutables (Fedora Atomic/Silverblue) o para aislar dependencias.

# Definición de colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Configuración de Entorno Distrobox para NeoCore ===${NC}"

# 1. Comprobar instalación de Distrobox
if ! command -v distrobox &> /dev/null; then
    echo -e "${YELLOW}Distrobox no detectado. Instalando...${NC}"
    if command -v dnf &> /dev/null; then
        sudo dnf install -y distrobox podman
    elif command -v apt &> /dev/null; then
        sudo apt install -y distrobox podman
    else
        echo -e "${RED}No se pudo instalar distrobox automáticamente. Por favor instálalo manualmente.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}Distrobox ya está instalado.${NC}"
fi

CONTAINER_NAME="neocore-box"
IMAGE="debian:12" # Stable Bookworm

# 2. Comprobar/Crear Contenedor
echo -e "${YELLOW}Verificando contenedor '${CONTAINER_NAME}'...${NC}"
if distrobox list | grep -q "$CONTAINER_NAME"; then
    echo -e "${GREEN}El contenedor existe.${NC}"
else
    echo -e "${YELLOW}Creando contenedor '${CONTAINER_NAME}' con imagen '${IMAGE}'...${NC}"
    distrobox create -n "$CONTAINER_NAME" -i "$IMAGE" -Y
fi

# 2.5 Asegurar Permisos
echo -e "${YELLOW}Asegurando permisos del directorio de trabajo...${NC}"
# Arreglar archivos potencialmente propiedad de root de ejecuciones sudo anteriores
sudo chown -R $(id -u):$(id -g) .
chmod -R u+rw .

# 3. Entrar y Configurar
echo -e "${GREEN}Instalando dependencias dentro de Distrobox...${NC}"

# Script para ejecutar DENTRO del contenedor
SETUP_SCRIPT="
set -e
echo 'Actualizando repositorios...'
sudo apt-get update && sudo apt-get install -y \
    python3 python3-pip python3-venv \
    git build-essential cmake swig libopenblas-dev wget unzip \
    libvlc-dev vlc \
    portaudio19-dev libasound2-dev \
    libgl1 libglib2.0-0 \
    ffmpeg

echo 'Creando entorno virtual (venv_distrobox)...'
cd \"$PWD\"
if [ ! -d \"venv_distrobox\" ]; then
    python3 -m venv venv_distrobox
fi

source venv_distrobox/bin/activate

echo 'Instalando pip requirements...'
pip install --upgrade pip wheel setuptools
# Fix fann2 por separado si es necesario
if grep -q 'fann2' requirements.txt; then
    # Clonar y construir fann primero si falta la librería del sistema
    if [ ! -f /usr/lib/libfann.so ] && [ ! -f /usr/local/lib/libfann.so ]; then
       echo 'Compilando libfann C...'
       if [ ! -d \"FANN\" ]; then
           git clone https://github.com/libfann/fann.git FANN
       fi
       cd FANN
       cmake .
       sudo make install
       cd ..
       sudo ldconfig
    fi
fi

pip install -r requirements.txt

echo '--- Descargando Modelos AI ---'
# Crear directorios de config/modelos si es necesario
if [ ! -d "models" ]; then mkdir -p models; fi
if [ ! -d "vosk-models" ]; then mkdir -p vosk-models; fi

# Ejecutar Descargadores usando el python/venv del contenedor
echo 'Descargando Gemma...'
python3 resources/tools/download_model.py

# echo 'Descargando Whisper...'
# python3 resources/tools/download_whisper_model.py

echo 'Descargando MANGO (T5)...'
# Por defecto MANGO (Main/v1) por estabilidad a menos que se especifique otra cosa
python3 resources/tools/download_mango_model.py --branch main

echo 'Instalación Completada en Distrobox.'
"

# Ejecutar setup dentro de distrobox
distrobox enter "$CONTAINER_NAME" -- bash -c "$SETUP_SCRIPT"

# 4. Crear Lanzador (Acceso directo)
LAUNCHER_SCRIPT="run_neocore_distrobox.sh"
echo "#!/bin/bash" > "$LAUNCHER_SCRIPT"
echo "echo 'Iniciando NeoCore en Distrobox...'" >> "$LAUNCHER_SCRIPT"
echo "distrobox enter $CONTAINER_NAME -- bash -c 'cd \"$PWD\" && source venv_distrobox/bin/activate && ./start.sh'" >> "$LAUNCHER_SCRIPT"
chmod +x "$LAUNCHER_SCRIPT"

echo -e "${GREEN}==============================================${NC}"
echo -e "${GREEN}Configuración del contenedor completada.${NC}"

# 5. Configuración del HOST (Auto-Setup)
echo -e "${YELLOW}Configurando sistema HOST...${NC}"

# 5.1 Config.json
if [ ! -f "config/config.json" ]; then
    echo "Creando configuración por defecto..."
    if [ ! -d "config" ]; then mkdir -p config; fi
    echo "{}" > config/config.json
    # No podemos ejecutar fácilmente el helper de contraseñas desde el host si no hay python,
    # ¡pero podemos intentar ejecutarlo vía contenedor!
    echo "Estableciendo contraseña 'admin'..."
    distrobox enter "$CONTAINER_NAME" -- bash -c "cd \"$PWD\" && source venv_distrobox/bin/activate && python3 resources/tools/password_helper.py --user admin --password admin"
fi

# 5.2 Certificados SSL
CERT_DIR="$(pwd)/config/certs"
if [ ! -f "$CERT_DIR/neo.key" ]; then
    echo "Generando certificados SSL (Host)..."
    mkdir -p "$CERT_DIR"
    if command -v openssl >/dev/null 2>&1; then
        openssl req -x509 -newkey rsa:4096 -keyout "$CERT_DIR/neo.key" -out "$CERT_DIR/neo.crt" -days 3650 -nodes -subj "/C=ES/ST=Madrid/L=Madrid/O=NeoCore/CN=$(hostname)"
        chmod 600 "$CERT_DIR/neo.key"
        chmod 644 "$CERT_DIR/neo.crt"
        echo "Certificados generados."
    else
        echo "OpenSSL no encontrado en host. Se intentará generar dentro del contenedor..."
         distrobox enter "$CONTAINER_NAME" -- bash -c "mkdir -p config/certs && openssl req -x509 -newkey rsa:4096 -keyout config/certs/neo.key -out config/certs/neo.crt -days 3650 -nodes -subj '/C=ES/ST=Madrid/L=Madrid/O=NeoCore/CN=NeoBox'"
    fi
fi

# 5.3 Servicio Systemd (Modo Usuario)
echo "Configurando servicio systemd (Usuario)..."
SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$SERVICE_DIR"
SERVICE_FILE="$SERVICE_DIR/neo.service"
PROJECT_DIR="$(pwd)"
LAUNCHER_PATH="$PROJECT_DIR/$LAUNCHER_SCRIPT"

cat <<EOT > "$SERVICE_FILE"
[Unit]
Description=Neo Assistant Service (Distrobox Mode)
After=network.target sound.target

[Service]
Type=simple
Environment=PYTHONUNBUFFERED=1
WorkingDirectory=$PROJECT_DIR
ExecStart=$LAUNCHER_PATH
Restart=always
RestartSec=10
SyslogIdentifier=neo_distrobox

[Install]
WantedBy=default.target
EOT

# Recargar y Habilitar
echo "Habilitando servicio..."
systemctl --user daemon-reload
systemctl --user enable neo.service
systemctl --user restart neo.service
loginctl enable-linger $(whoami)

echo -e "${GREEN}==============================================${NC}"
echo -e "${GREEN}¡Instalación COMPLETADA!${NC}"
echo -e "NeoCore se está ejecutando en segundo plano (dentro de Distrobox)."
echo -e "Logs: journalctl --user -u neo.service -f"
echo -e "${GREEN}==============================================${NC}"
