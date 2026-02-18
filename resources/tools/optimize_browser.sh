#!/bin/bash

# Function to install Lightweight Browser
install_browser() {
    echo "Detecting OS..."
    if [ -f /etc/fedora-release ]; then
        echo "Fedora detected."
        echo "Installing Epiphany (GNOME Web)..."
        sudo dnf install -y epiphany
    elif [ -f /etc/debian_version ]; then
        echo "Debian/Ubuntu detected."
        echo "Installing Epiphany and Chromium..."
        sudo apt-get update
        # Try Epiphany first, then Firefox ESR as fallback for lightweight
        sudo apt-get install -y epiphany-browser || sudo apt-get install -y firefox-esr
        # Ensure Chromium is installed if user wants to use it
        sudo apt-get install -y chromium
    else
        echo "Unsupported OS. Please install a browser manually."
        return 1
    fi
    echo "Browsers installed successfully."
}

# Function to launch Lightweight Browser
launch_lightweight() {
    echo "Launching Lightweight Browser..."
    if command -v epiphany-browser &> /dev/null; then
        epiphany-browser --application-mode --profile=/tmp/epiphany-kiosk http://localhost:5000/face
    elif command -v epiphany &> /dev/null; then
        epiphany --application-mode --profile=/tmp/epiphany-kiosk http://localhost:5000/face
    elif command -v firefox-esr &> /dev/null; then
        firefox-esr --kiosk http://localhost:5000/face
    elif command -v midori &> /dev/null; then
        midori -e Fullscreen -a http://localhost:5000/face
    else
        echo "No lightweight browser found. Please run Option 1 to install."
    fi
}

# Function to launch Chromium Optimized
launch_chromium_optimized() {
    echo "Launching Chromium with Memory Optimizations..."
    
    # Detect executable name
    if command -v chromium &> /dev/null; then
        CMD="chromium"
    elif command -v chromium-browser &> /dev/null; then
        CMD="chromium-browser"
    elif command -v google-chrome &> /dev/null; then
        CMD="google-chrome"
    else
        echo "Chromium not found. Please run Option 1 to install it."
        return 1
    fi

    $CMD \
        --kiosk \
        --disable-infobars \
        --disable-extensions \
        --disable-translate \
        --disk-cache-dir=/dev/null \
        --disk-cache-size=1 \
        "http://localhost:5000/face"
}

echo "Choose an option:"
echo "1) Install Browsers (Epiphany/Chromium)"
echo "2) Launch Lightweight Browser (Epiphany/Firefox)"
echo "3) Launch Chromium (Optimized)"
read -p "Option: " opt

case $opt in
    1) install_browser ;;
    2) launch_lightweight ;;
    3) launch_chromium_optimized ;;
    *) echo "Invalid option" ;;
esac
