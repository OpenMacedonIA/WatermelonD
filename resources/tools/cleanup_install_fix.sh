#!/bin/bash
set -e

# cleanup_install_fix.sh
# Script para limpiar caches y solucionar problemas de espacio temporal durante la instalación.

echo "========================================="
echo "===   Limpieza y Reparación de Inst.  ==="
echo "========================================="
echo "Este script liberará espacio y configurará un directorio temporal local."
echo ""

# 1. Limpieza de Caches del Sistema
echo "[1/3] Limpiando caches del sistema..."

if command -v apt-get &> /dev/null; then
    echo "Limpando cache de APT..."
    sudo apt-get clean
    sudo apt-get autoremove -y
fi

if command -v pip3 &> /dev/null; then
    echo "Limpiando cache de PIP..."
    pip3 cache purge || true
fi

# 2. Limpieza de Versiones Antiguas
echo ""
echo "[2/3] Buscando versiones antiguas..."
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$(realpath "$0")")")")"
OLD_VER_DIR="$PROJECT_ROOT/COLEGA.old"

if [ -d "$OLD_VER_DIR" ]; then
    echo "Eliminando directorio: $OLD_VER_DIR"
    rm -rf "$OLD_VER_DIR"
else
    echo "No se encontró COLEGA.old, todo correcto."
fi

# 3. Configuración de Directorio Temporal Local
echo ""
echo "[3/3] Configurando entorno de instalación..."

TEMP_BUILD_DIR="$PROJECT_ROOT/temp_build"
mkdir -p "$TEMP_BUILD_DIR"

echo "Directorio temporal establecido en: $TEMP_BUILD_DIR"
export TMPDIR="$TEMP_BUILD_DIR"

echo ""
echo "========================================="
echo "   ¡Preparación Completada!   "
echo "========================================="
echo "Ahora re-ejecuta el instalador usando este mismo terminal (para conservar la variable TMPDIR):"
echo ""
echo "  ./install.sh"
echo ""
echo "Si todavía falla, intenta instalar las librerías manualmente:"
echo "  export TMPDIR=$TEMP_BUILD_DIR"
echo "  ./venv/bin/pip install -r requirements.txt --no-cache-dir"
echo ""
