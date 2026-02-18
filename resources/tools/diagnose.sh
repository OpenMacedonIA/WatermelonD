#!/bin/bash
echo "🔍 DIAGNÓSTICO DE COLEGA (Debian 12)"
echo "========================================"

echo "1. ESTADO DEL SERVICIO:"
systemctl --user status neo.service --no-pager
echo "----------------------------------------"

echo "2. PUERTOS ESCUCHANDO (5000):"
ss -tuln | grep 5000
echo "----------------------------------------"

echo "3. ÚLTIMOS LOGS DE APP (Python):"
tail -n 30 logs/app.log
echo "----------------------------------------"

echo "4. ÚLTIMOS LOGS DE VOSK (Voz):"
tail -n 30 logs/vosk.log
echo "----------------------------------------"

echo "5. LOGS DE SYSTEMD (Error de arranque):"
journalctl --user -u neo.service -n 50 --no-pager
echo "========================================"
echo "COPIA Y PÉGAME TODO ESTE CONTENIDO"
