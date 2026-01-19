#!/bin/bash
set -e

# Configurar identidad global si no existe (usando valores del usuario actual o genericos)
git config --global user.name "Neo Agent" || true
git config --global user.email "neo@colega.ai" || true

# 1. SKILLS (BlueberrySkills)
echo "Configurando BlueberrySkills..."
cd ../BlueberrySkills
git init
git add .
git commit -m "Initial commit: Extracted Skills from WatermelonD"
git branch -M main
git remote add origin https://github.com/OpenMacedonIA/BlueberrySkills
echo "BlueberrySkills listo."

# 2. WEB (TangerineUI)
echo "Configurando TangerineUI..."
cd ../TangerineUI
git init
git add .
git commit -m "Initial commit: Extracted Web Client from WatermelonD"
git branch -M main
git remote add origin https://github.com/OpenMacedonIA/TangerineUI
echo "TangerineUI listo."

# 3. AI (BrainNut)
echo "Configurando BrainNut..."
cd ../BrainNut
# Cear gitignore para evitar subir modelos gigantes
echo "MANGOT5/" > .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pt" >> .gitignore
echo "*.bin" >> .gitignore

git init
git add .
git commit -m "Initial commit: Extracted AI Engine from WatermelonD"
git branch -M main
git remote add origin https://github.com/OpenMacedonIA/BrainNut
echo "BrainNut listo."
