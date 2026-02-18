#!/bin/bash
echo "🔧 INICIANDO REPARACIÓN DE EMERGENCIA DE COLEGA 🔧"

# 1. Matar procesos zombies
echo ">>> Matando procesos zombies (Chromium, Python)..."
pkill -f chromium
pkill -f python
pkill -f neo.service
killall chromium 2>/dev/null

# 2. Limpiar locks
echo ">>> Limpiando bloqueos..."
rm -f /home/jrodriiguezg/.config/chromium/SingletonLock
rm -rf /home/jrodriiguezg/.config/chromium/Singleton*

# 3. Verificar dependencias críticas
echo ">>> Verificando dependencias..."
pip install --upgrade flask-socketio eventlet vosk pyaudio --break-system-packages

# 4. Asegurar puerto 5000 (no 8181)
# (Ya arreglado en código, pero aseguramos limpieza de puertos)
fuser -k 5000/tcp 2>/dev/null
fuser -k 8181/tcp 2>/dev/null

# 5. Reiniciar Servicio
echo ">>> Reiniciando Servicio Neo..."
systemctl --user daemon-reload
systemctl --user restart neo.service

echo "✅ REPARACIÓN COMPLETADA."
echo "Por favor, espera 15 segundos y di 'Neo' para probar."
echo "Monitorizando logs... (Ctrl+C para salir)"
journalctl --user -u neo.service -f -n 50
