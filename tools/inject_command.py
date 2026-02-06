import sys
import os
import time

# Ensure we can import from parent/modules
# Try to resolve project root. Assuming this script is in tools/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.bus_client import BusClient

def inject(text):
    bus = BusClient(name="Injector", port=5000)
    print(f"Connecting to Message Bus at port 5000...")
    # Quick connect
    bus.connect()
    print(f"Injecting Command: '{text}'")
    bus.emit('command:inject', {'text': text})
    time.sleep(0.5) # Wait for emit to flush
    bus.close()
    print("Done.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tools/inject_command.py 'command text'")
    else:
        inject(" ".join(sys.argv[1:]))
