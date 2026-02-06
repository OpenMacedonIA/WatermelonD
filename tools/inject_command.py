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
    
    # Event Handlers
    def on_response(data):
        print(f"\n[NEO RESPONSE]: {data.get('text')}")
        bus.close()
        sys.exit(0)

    def on_stt(data):
        print(f"[STT CONFIRMED]: {data.get('text')}")

    # Register handlers
    bus.on('ai:response', on_response)
    bus.on('stt:result', on_stt)

    # Connect
    try:
        bus.connect()
    except Exception as e:
        print(f"Error connecting: {e}")
        return

    print(f"Injecting Command: '{text}'")
    bus.emit('command:inject', {'text': text})
    
    print("Waiting for response (Ctrl+C to cancel)...")
    try:
        # Wait up to 10 seconds for response
        start_time = time.time()
        while time.time() - start_time < 10:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nCancelled.")
    finally:
        if bus.connected:
            bus.close()
            print("Done.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tools/inject_command.py 'command text'")
    else:
        inject(" ".join(sys.argv[1:]))
