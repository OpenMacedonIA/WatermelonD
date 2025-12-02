#!/bin/bash

# start_face.sh
# Lanza la interfaz visual de Neo en modo Kiosko (Pantalla completa)

URL="http://localhost:5000/face"

# Esperar a que el servidor web esté listo
echo "Esperando a que Neo Core inicie el servidor web..."
until curl -s $URL > /dev/null; do
    sleep 2
done
echo "Servidor web detectado. Lanzando interfaz..."

# Detectar navegador
if command -v firefox &> /dev/null; then
    echo "Usando Firefox..."
    firefox --kiosk "$URL" &
elif command -v chromium-browser &> /dev/null; then
    echo "Usando Chromium..."
    chromium-browser --kiosk --app="$URL" &
elif command -v chromium &> /dev/null; then
    echo "Usando Chromium..."
    chromium --kiosk --app="$URL" &
elif command -v google-chrome &> /dev/null; then
    echo "Usando Chrome..."
    google-chrome --kiosk --app="$URL" &
else
    echo "ERROR: No se encontró ningún navegador compatible (Firefox, Chromium, Chrome)."
    exit 1
fi

echo "Interfaz lanzada."
