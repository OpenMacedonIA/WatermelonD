#!/bin/bash
set -e

# Configurar identidad global si no existe (usando valores del usuario actual o genericos)
git config --global user.name "Neo Agent" || true
git config --global user.email "neo@colega.ai" || true

# 1. UVAS (Skills)
echo "Configurando neo-uvas..."
cd ../neo-uvas
git init
git add .
git commit -m "Initial commit: Extracted Skills from NEOPapaya"
git branch -M main
git remote add origin https://github.com/OpenMacedonIA/neo-uvas.git
echo "neo-uvas listo."

# 2. CEREZA (Web Client)
echo "Configurando neo-cereza..."
cd ../neo-cereza
git init
git add .
git commit -m "Initial commit: Extracted Web Client from NEOPapaya"
git branch -M main
git remote add origin https://github.com/OpenMacedonIA/neo-cereza.git
echo "neo-cereza listo."

# 3. MANGO (AI Engine)
echo "Configurando neo-mango..."
cd ../neo-mango
# Cear gitignore para evitar subir modelos gigantes
echo "MANGOT5/" > .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pt" >> .gitignore
echo "*.bin" >> .gitignore

git init
git add .
git commit -m "Initial commit: Extracted AI Engine from NEOPapaya"
git branch -M main
git remote add origin https://github.com/OpenMacedonIA/neo-mango.git
echo "neo-mango listo."
