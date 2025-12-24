#!/bin/bash
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Instalador Modular de Neo ===${NC}"
echo "Seleccione el tipo de instalación:"
echo "1) Nodo Principal (NeoCore + Web Local)"
echo "2) Nodo Principal Headless (Solo NeoCore API)"
echo "3) Cliente Web Remoto (Solo Interfaz)"
read -p "Opción [1-3]: " OPCION

# Advertencia inicial sobre Distrobox/Podman vs Nativo
IS_DEBIAN=false
if command -v apt-get &> /dev/null; then
    IS_DEBIAN=true
    echo -e "${YELLOW}Sistema Debian/Ubuntu detectado.${NC}"
else
    echo -e "${YELLOW}Sistema Fedora/Atomic detectado (o sin apt).${NC}"
fi

case $OPCION in
    1)
        if [ "$IS_DEBIAN" = true ]; then
            echo -e "${YELLOW}Instalando de forma Nativa (install.sh)...${NC}"
            ./install.sh
        else
            echo -e "${YELLOW}Instalando mediante Distrobox (setup_distrobox.sh)...${NC}"
            ./setup_distrobox.sh
        fi
        ;;
    2)
        if [ "$IS_DEBIAN" = true ]; then
             echo -e "${YELLOW}Instalando Nodo Headless Nativo (install.sh)...${NC}"
             # install.sh ya configura modo servicio adecuado
             ./install.sh
        else
             echo -e "${YELLOW}Instalando Nodo Headless en Distrobox...${NC}"
             ./setup_distrobox.sh
             echo -e "${GREEN}Para ejecutar SIN web local, edite la configuración posteriormente.${NC}"
        fi
        ;;
    3)
        echo -e "${YELLOW}Instalando Cliente Web Remoto...${NC}"
        
        read -p "IP del Servidor NeoCore (ej: http://192.168.1.50:5000): " NEO_IP
        if [ -z "$NEO_IP" ]; then NEO_IP="http://localhost:5000"; fi
        
        echo "Configurando cliente para conectar a $NEO_IP..."
        
        # Install basic requirements for client
        if command -v pip &> /dev/null; then
            pip install flask requests flask-wtf
        else
            echo "Instalando dependencias python..."
            sudo apt-get install -y python3-flask python3-requests python3-flask-wtf || sudo dnf install -y python3-flask python3-requests python3-flask-wtf
        fi
        
        # Create launcher
        echo "#!/bin/bash" > run_client.sh
        echo "export NEO_API_URL='$NEO_IP'" >> run_client.sh
        echo "python3 web_client/app.py" >> run_client.sh
        chmod +x run_client.sh
        
        echo -e "${GREEN}Instalación de cliente lista.${NC}"
        echo "Ejecute ./run_client.sh para iniciar la interfaz."
        ;;
    *)
        echo "Opción inválida."
        exit 1
        ;;
esac
