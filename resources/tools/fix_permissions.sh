#!/bin/bash

# Este script configura permisos sudo sin contraseña para el usuario actual
# necesarios para que WatermelonD pueda reiniciar servicios (bluetooth, etc.) automáticamente.

USER_NAME=$(whoami)
SUDOERS_FILE="/etc/sudoers.d/watermelond_perms"
SYSTEMCTL_PATH=$(which systemctl)

echo "========================================"
echo "   Fix Permisos WatermelonD (Sudoers)   "
echo "========================================"
echo "Usuario actual: $USER_NAME"
echo "Systemctl path: $SYSTEMCTL_PATH"
echo ""

if [ -z "$SYSTEMCTL_PATH" ]; then
    echo "ERROR: No se encontró 'systemctl'. ¿Estás en un sistema con systemd?"
    exit 1
fi

echo "Se creará el archivo $SUDOERS_FILE con el contenido:"
echo "$USER_NAME ALL=(ALL) NOPASSWD: $SYSTEMCTL_PATH"
echo ""
echo "Será necesario introducir tu contraseña de sudo una última vez."
echo ""

read -p "¿Proceder? (s/n): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Ss]$ ]]; then
    echo "Cancelado."
    exit 0
fi

# Crear archivo temporal
TMP_FILE=$(mktemp)
echo "$USER_NAME ALL=(ALL) NOPASSWD: $SYSTEMCTL_PATH" > "$TMP_FILE"

# Mover con sudo y establecer permisos correctos
sudo mv "$TMP_FILE" "$SUDOERS_FILE"
sudo chown root:root "$SUDOERS_FILE"
sudo chmod 0440 "$SUDOERS_FILE"

echo ""
if [ -f "$SUDOERS_FILE" ]; then
    echo "✅ Éxito: Permisos aplicados."
    echo "Ahora NeoCore podrá reiniciar servicios sin pedir contraseña."
else
    echo "❌ Error: No se pudo crear el archivo."
fi
