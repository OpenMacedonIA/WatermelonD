#!/bin/bash

echo "=== Installing Papaya Extra Extensions ==="

# 1. Initialize Submodule
echo "Downloading extensions..."
git submodule update --init --recursive modules/extensions

# 2. Run internal setup
if [ -f "modules/extensions/setup.sh" ]; then
    echo "Running extension setup..."
    cd modules/extensions
    chmod +x setup.sh
    ./setup.sh
    cd ../..
else
    echo "Error: setup.sh not found in modules/extensions."
    exit 1
fi

echo "Extensions installed successfully."
echo "Please restart NeoCore to load new plugins."
