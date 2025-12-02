#!/bin/bash

echo "Checking for SWIG..."
if ! command -v swig &> /dev/null; then
    echo "SWIG not found. Installing..."
    if [ -f /etc/debian_version ]; then
        sudo apt-get update
        sudo apt-get install -y swig
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y swig
    elif [ -f /etc/arch-release ]; then
        sudo pacman -S --noconfirm swig
    else
        echo "Unsupported OS. Please install 'swig' manually."
        exit 1
    fi
else
    echo "SWIG is already installed."
fi

echo "Running FANN fix script..."
if [ -f "venv/bin/python" ]; then
    echo "Using Virtual Environment..."
    venv/bin/python resources/tools/install_fann_fix.py
else
    echo "Using System Python (WARNING: May fail on managed systems)..."
    python3 resources/tools/install_fann_fix.py
fi

echo "Done. Please restart the service: sudo systemctl restart neo.service"
