#!/bin/bash
# start.sh - Lanzador Manual de WatermelonD

set -e

# --- 1. Detección de Entorno ---
if [ -d "venv" ]; then
    VENV_PATH="venv"
elif [ -d "venv_distrobox" ]; then
    # Soporte heredado
    VENV_PATH="venv_distrobox"
else
    echo " CRÍTICO: Entorno virtual no encontrado."
    echo "   Por favor, ejecuta './install.sh' para configurar el proyecto."
    exit 1
fi

echo " Usando entorno virtual: $VENV_PATH"
source $VENV_PATH/bin/activate

# --- 2. Variables de Entorno de Tiempo de Ejecución ---
export PYTHONUNBUFFERED=1
# Prevenir que Jack Audio Server se inicie automáticamente (problema común en bare metal)
export JACK_NO_START_SERVER=1

# --- 3. Comprobación de Dependencias ---
# Comprobar Mosquitto (Broker MQTT)
if command -v systemctl >/dev/null; then
    if systemctl is-active --quiet mosquitto; then
        echo " El Broker MQTT está en ejecución."
    else
        echo "  ADVERTENCIA: El servicio Mosquitto NO está en ejecución."
        echo "   El sistema podría fallar al comunicarse con satélites."
        echo "   Prueba: 'sudo systemctl start mosquitto'"
    fi
else
    # Respaldo para entornos sin systemd (como docker)
    if ! pgrep -x "mosquitto" > /dev/null; then
        echo "  ADVERTENCIA: Mosquitto parece no estar en ejecución."
    fi
fi

# --- 4. Lanzamiento ---
echo " Iniciando WatermelonD Core..."
echo "---------------------------------"
python NeoCore.py
