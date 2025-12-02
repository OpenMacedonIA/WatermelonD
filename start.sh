#!/bin/bash
# Script para iniciar Neo Core usando el entorno virtual correcto

# Obtener el directorio del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PYTHON="$DIR/venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: No se encontró el entorno virtual en $DIR/venv"
    echo "Por favor, ejecuta ./install.sh primero."
    exit 1
fi

echo "Iniciando Neo Core con Python 3.10 (venv)..."
exec "$VENV_PYTHON" "$DIR/NeoCore.py" "$@"
