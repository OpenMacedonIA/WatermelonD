#!/usr/bin/env python3
import socketio
import json
import time
import sys
import os

# Add root to path
if os.path.exists('modules'):
    sys.path.append(os.getcwd())
else:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

try:
    from modules.bus_client import BusClient
except ImportError:
    print("Error: Could not import BusClient. Run from project root.")
    sys.exit(1)

sio = socketio.Client()
connected = False

@sio.event
def connect():
    global connected
    connected = True
    print("\n[OK] Connected to Message Bus!")
    print("Waiting for messages... (Ctrl+C to stop)\n")

@sio.event
def disconnect():
    global connected
    connected = False
    print("\n[ERROR] Disconnected from Message Bus")

@sio.event
def message(data):
    msg_type = data.get('type')
    msg_data = data.get('data', {})
    
    # Filter out boring audio blobs to keep output readable
    if msg_type == 'recognizer_loop:audio':
        size = len(msg_data.get('data', ''))
        print(f"[AUDIO] received {size} bytes")
        return

    print(f"[{msg_type}]")
    if msg_data:
        print(json.dumps(msg_data, indent=2))
    print("-" * 40)

def main():
    print("==========================================")
    print("   NEO BUS MONITOR")
    print("==========================================")
    
    url = "http://localhost:8181"
    
    try:
        sio.connect(url)
        sio.wait()
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Is the service running? (systemctl --user status neo.service)")

if __name__ == "__main__":
    main()
