#!/bin/bash

echo "============================================"
echo "    Actualizador de Sistema NEOPapaya"
echo "============================================"

# Diretorio base
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE_DIR"

echo "📂 Directorio: $BASE_DIR"

# 1. Actualizar repositorio principal
echo "⬇️  Actualizando repositorio principal..."
git pull origin main || echo "⚠️ Aviso: No se pudo hacer git pull (¿cambios locales?)"

# 2. Actualizar submódulos (núcleo y extras)
echo "📦 Actualizando submódulos (Skills, Web, Extensions)..."
git submodule update --init --recursive

# 3. Actualizar dependencias Python (por si hay nuevas)
if [ -d "venv" ]; then
    echo "🐍 Verificando nuevas dependencias Python..."
    source venv/bin/activate
    # Usar uv si está instalado, si no pip
    if command -v uv &> /dev/null; then
        uv pip install -r requirements.txt
    else
         pip install -r requirements.txt
    fi
    
    # Dependencias de extensiones
    if [ -f "modules/extensions/requirements.txt" ]; then
        echo "🔌 Actualizando dependencias de extensiones..."
        if command -v uv &> /dev/null; then
            uv pip install -r modules/extensions/requirements.txt
        else
            pip install -r modules/extensions/requirements.txt
        fi
    fi
fi

# 4. Reiniciar servicios
echo "🔄 Reiniciando servicios..."
# Detectar si es usuario normal o root (systemd --user vs system)
if systemctl --user is-active --quiet neo.service; then
    systemctl --user restart neo.service
    echo "✅ Servicio 'neo.service' (Usuario) reiniciado."
else
    echo "ℹ️  No se detectó neo.service activo. Si lo usas manualmente, reinícialo tú."
fi

echo "============================================"
echo "✅ Actualización Completada."
echo "============================================"
