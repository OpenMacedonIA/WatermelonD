# Guía de Mini Network Bros (MNB)

Un "Mini Network Bro" (MNB) es un microcontrolador (ESP32, RP2040) que actúa como sensor o actuador en el ecosistema WatermelonD/WatermelonD. Se comunica principalmente vía WiFi (MQTT), pero puede usar Bluetooth como respaldo si la red cae.

## Requisitos
- **Hardware**: ESP32 (DevKit V1), ESP32-CAM (para visión), o Raspberry Pi Pico W.
- **Software**: Firmware MicroPython (Recomendado) o Arduino C++.

## Flujo de Comunicación
1. **Inicio**: Intenta conectar a WiFi.
2. **Conexión MQTT**: Si hay WiFi, conecta al broker (IP de WatermelonD). Topic base: `tio/agents/{hostname}/`.
3. **Fallback Bluetooth**: Si no hay WiFi tras varios intentos, activa Bluetooth Serial.
 - Nombre BT: `MNB_{Hostname}`
 - Protocolo: JSON por Serial (RFCOMM).

## Instalación del Firmware (MicroPython)

### 1. Flashear MicroPython
Descarga la última versión de [MicroPython para ESP32](https://micropython.org/download/esp32/).
```bash
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 esp32-2023xxxx-v1.xx.bin
```

### 2. Cargar Código
Sube los archivos de `resources/MNB/firmware/` al dispositivo usando `ampy` o Thonny IDE.
- `boot.py`: Configuración inicial.
- `main.py`: Lógica principal, WiFi, MQTT y Bluetooth.
- `umqtt/simple.py`: Librería MQTT (si no está incluida).

## Configuración (main.py)
Edita las variables al inicio de `main.py`:
```python
SSID = "TuWiFi"
PASSWORD = "TuClave"
BRAIN_IP = "192.168.1.X"# IP de WatermelonD
HOSTNAME = "mnb-sensor-1"
```

## Tópicos MQTT
- **Publica en**:
 - `tio/agents/{HOSTNAME}/telemetry`: Datos de sensores (JSON).
 - `tio/agents/{HOSTNAME}/status`: "online" / "offline" (LWT).
- **Suscribe a**:
 - `tio/agents/{HOSTNAME}/command`: Comandos remotos.

## Visión por Computador (ESP32-CAM)
Para usar la cámara, usa el código Arduino en `resources/esp32_cam/`.
- La cámara transmite un stream MJPEG.
- WatermelonD (VisionManager) consume este stream para reconocimiento facial.
- URL del stream: `http://{IP_CAM}:81/stream`
