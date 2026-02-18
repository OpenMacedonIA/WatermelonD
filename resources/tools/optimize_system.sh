#!/bin/bash

# optimize_system.sh
# Script de limpieza y optimización para Debian 13 (TIO AI Host)
# PRECAUCIÓN: Ejecutar con privilegios de root (sudo).

if [ "$EUID" -ne 0 ]; then
  echo "Por favor, ejecuta este script como root (sudo)."
  exit 1
fi

echo "=== Iniciando Optimización del Sistema TIO AI (Debian 13) ==="

# 1. Limpieza de Paquetes (APT)
echo "[1/5] Limpiando paquetes..."
apt-get update
# Eliminar paquetes huerfanos (dependencias que ya no se usan)
apt-get autoremove -y
# Limpiar caché de paquetes descargados (.deb)
apt-get clean
# Eliminar archivos de configuración de paquetes desinstalados
dpkg -l | grep '^rc' | awk '{print $2}' | xargs -r dpkg --purge

# 2. Limpieza de Logs (Journald)
echo "[2/5] Optimizando logs..."
# Limitar el tamaño de los logs a 100MB
journalctl --vacuum-size=100M
# Limitar por tiempo (2 días)
journalctl --vacuum-time=2d

# 3. Optimización de Memoria (Swap)
echo "[3/5] Ajustando Swappiness..."
# Reducir la tendencia a usar swap (disco) en lugar de RAM.
# Valor por defecto suele ser 60. Lo bajamos a 10 para priorizar RAM.
if ! grep -q "vm.swappiness" /etc/sysctl.conf; then
    echo "vm.swappiness=10" >> /etc/sysctl.conf
    sysctl -p
    echo "Swappiness ajustado a 10."
else
    echo "Swappiness ya configurado."
fi

# 4. Desactivar Servicios Innecesarios (Bloatware común)
echo "[4/5] Gestionando servicios..."

# Función para desactivar servicio si existe
disable_service() {
    if systemctl list-unit-files | grep -q "^$1"; then
        echo "Desactivando $1..."
        systemctl stop $1
        systemctl disable $1
    fi
}

# ModemManager: Suele interferir con puertos serie/USB y no se usa si tienes WiFi fijo.
disable_service "ModemManager"

# CUPS: Servicio de impresión. Si el asistente no imprime, fuera.
disable_service "cups"
disable_service "cups-browsed"

# Avahi: Descubrimiento de red mDNS. A veces útil, pero consume recursos. 
# (Comentado por seguridad, descomentar si no se usan dispositivos Apple/mDNS)
# disable_service "avahi-daemon"

# NOTA: NO tocamos NetworkManager, SSH, ni FTP como solicitaste.

# 5. Limpieza de Cachés de Usuario (Miniaturas, etc.)
echo "[5/5] Limpiando cachés temporales..."
rm -rf /home/*/.cache/thumbnails/*
rm -rf /root/.cache/thumbnails/*

echo "=== Optimización Completada ==="
echo "Se recomienda reiniciar el sistema para aplicar todos los cambios."
echo "Ejecuta: reboot"
