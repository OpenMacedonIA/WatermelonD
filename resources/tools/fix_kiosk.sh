#!/bin/bash
# Script de reparación automática para Kiosk/Web Interface
# Ejecutar en el servidor (Debian 12)

echo "🔧 Iniciando reparación de Kiosk y Dependencias..."

# 1. Definir directorios
BASE_DIR="$(pwd)"
VENV_DIR="$BASE_DIR/venv"
STATIC_JS_DIR="$BASE_DIR/TangerineUI/static/js"

# 2. Instalar dependencias faltantes de Python
if [ -d "$VENV_DIR" ]; then
    echo "📦 Instalando librerías Python faltantes (Flask-WTF, eventlet)..."
    $VENV_DIR/bin/pip install Flask-WTF eventlet --no-cache-dir
else
    echo "❌ ERROR: No se encuentra el entorno virtual en $VENV_DIR"
    exit 1
fi

# 5. Reiniciar servicio y limpiar procesos (MODO NUCLEAR)
echo "🔪 Matando TODOS los procesos de Chromium..."
pkill -9 -f chromium
pkill -9 -f chromium-browser
killall -9 chromium chromium-browser 2>/dev/null

echo "🧹 Eliminando bloqueos y caché..."
rm -rf ~/.config/chromium/Singleton*
rm -rf ~/.cache/chromium
rm -f ~/.config/chromium/Profile*/Singleton*

echo "📝 Reescribiendo .xinitrc con limpieza automática..."
cat << 'EOF' > ~/.xinitrc
#!/bin/bash
# Desactivar ahorro de energía
xset -dpms
xset s off
xset s noblank

# LIMPIEZA DE ARRANQUE (Nuclear)
pkill -9 -f chromium
rm -rf ~/.config/chromium/Singleton*
rm -f ~/.config/chromium/Profile*/Singleton*

# Iniciar gestor de ventanas
openbox &

# Esperar a que el servidor Flask esté listo (puerto 5000)
echo "Esperando a Neo Core inicie..."
while ! curl -s http://localhost:5000 > /dev/null; do
    sleep 2
done

# Detectar nombre del binario de Chromium
CHROMIUM_BIN="chromium"
if command -v chromium-browser &> /dev/null; then
    CHROMIUM_BIN="chromium-browser"
fi

# Bucle infinito para el navegador
while true; do
    $CHROMIUM_BIN --kiosk --no-first-run --disable-infobars --disable-session-crashed-bubble --disable-restore-session-state http://localhost:5000/face
    sleep 2
done
EOF
chmod +x ~/.xinitrc

echo "🔄 Reiniciando servicio Neo..."
systemctl --user restart neo.service

echo "✅ Reparación completada. El bloqueo de Chromium debería haber desaparecido."
