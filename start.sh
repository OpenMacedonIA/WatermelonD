#!/bin/bash
# start.sh - WatermelonD Manual Launcher

set -e

# --- 1. Environment Detection ---
if [ -d "venv" ]; then
    VENV_PATH="venv"
elif [ -d "venv_distrobox" ]; then
    # Legacy support
    VENV_PATH="venv_distrobox"
else
    echo "❌ CRITICAL: Virtual environment not found."
    echo "   Please run './install.sh' to set up the project."
    exit 1
fi

echo "✅ Using virtual environment: $VENV_PATH"
source $VENV_PATH/bin/activate

# --- 2. Runtime Environment Vars ---
export PYTHONUNBUFFERED=1
# Prevent Jack Audio Server from auto-spawning (common issue in bare metal)
export JACK_NO_START_SERVER=1

# --- 3. Dependency Checks ---
# Check Mosquitto (MQTT Broker)
if command -v systemctl >/dev/null; then
    if systemctl is-active --quiet mosquitto; then
        echo "✅ MQTT Broker is running."
    else
        echo "⚠️  WARNING: Mosquitto service is NOT running."
        echo "   The system might fail to communicate with satellites."
        echo "   Try: 'sudo systemctl start mosquitto'"
    fi
else
    # Fallback for non-systemd envs (like docker)
    if ! pgrep -x "mosquitto" > /dev/null; then
        echo "⚠️  WARNING: Mosquitto does not seem to be running."
    fi
fi

# --- 4. Launch ---
echo "🚀 Starting WatermelonD Core..."
echo "---------------------------------"
python NeoCore.py
