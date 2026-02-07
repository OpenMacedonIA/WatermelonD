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
    
    response_received = False
    
    # Event Handlers
    def on_response(data):
        nonlocal response_received
        print(f"\n🤖 [AI RESPONSE]: {data.get('text')}")
        response_received = True

    def on_stt(data):
        print(f"\n[MIC] [COMMAND RECEIVED]: {data.get('text')}")

    def on_command_execution(data):
        print(f"\n[EXEC]  [EXECUTING]: {data.get('cmd')}")
    
    def on_command_output(data):
        output = data.get('output', '')
        if len(output) > 200:
            output = output[:200] + "..."
        print(f"\n📄 [OUTPUT]: {output}")
    
    def on_router_decision(data):
        category = data.get('category')
        score = data.get('score', 0)
        print(f"\n🧭 [ROUTER]: Category='{category}' (confidence: {score:.2f})")

    # Register handlers on the RAW SIO Client for specific events
    bus.sio.on('ai:response', on_response)
    bus.sio.on('stt:result', on_stt)
    bus.sio.on('router:decision', on_router_decision)
    bus.sio.on('command:execution', on_command_execution)
    bus.sio.on('command:output', on_command_output)
    
    # Connect
    try:
        bus.connect()
    except Exception as e:
        print(f"[ERROR] Error connecting: {e}")
        return

    # Wait for connection state to be confirmed
    timeout = 5
    while not bus.connected and timeout > 0:
        time.sleep(0.1)
        timeout -= 0.1
    
    if not bus.connected:
        print("[ERROR] Error: Connected to socket but BusClient state is not 'connected'.")
        return

    print(f"\n[INJECT] Injecting Command: '{text}'")
    bus.emit('command:inject', {'text': text})
    
    print("⏳ Waiting for response (Ctrl+C to cancel)...")
    try:
        # Wait up to 15 seconds for response
        start_time = time.time()
        while time.time() - start_time < 15 and not response_received:
            time.sleep(0.1)
        
        if not response_received:
            print("\n[WARN] No response received within 15 seconds.")
    except KeyboardInterrupt:
        print("\n[ERROR] Cancelled.")
    finally:
        if bus.connected:
            bus.close()
        print("\n[OK] Done.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tools/inject_command.py 'command text'")
    else:
        inject(" ".join(sys.argv[1:]))
