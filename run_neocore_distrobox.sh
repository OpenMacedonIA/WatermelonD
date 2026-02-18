#!/bin/bash
echo 'Iniciando NeoCore en Distrobox...'
distrobox enter neocore-box -- bash -c 'cd "/home/jrodriiguezg/Documentos/codigos/COLEGA" && source venv_distrobox/bin/activate && ./start.sh'
