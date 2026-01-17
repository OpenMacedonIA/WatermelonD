import socketio
import logging
import json
import threading
import time

logger = logging.getLogger("BusClient")

class BusClient:
    def __init__(self, host='localhost', port=5000, name="UnknownClient"):
        self.sio = socketio.Client()
        self.host = host
        self.port = port
        self.name = name
        self.handlers = {} # Map event_type -> [callbacks]
        self.connected = False

        self._setup_events()

    def _setup_events(self):
        @self.sio.event
        def connect():
            self.connected = True
            logger.info(f"[{self.name}] Connected to Message Bus")
            self.emit(f"{self.name}.connected", {})

        @self.sio.event
        def disconnect():
            self.connected = False
            logger.info(f"[{self.name}] Disconnected from Message Bus")

        @self.sio.event
        def message(data):
            """
            Handle incoming messages from the bus.
            """
            msg_type = data.get('type')
            msg_data = data.get('data', {})
            
            # logger.debug(f"[{self.name}] Received: {msg_type}")
            
            if msg_type in self.handlers:
                for callback in self.handlers[msg_type]:
                    try:
                        callback(data)
                    except Exception as e:
                        logger.error(f"Error in callback for {msg_type}: {e}")

    def on(self, event_type, callback):
        """Register a callback for a specific event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(callback)

    def emit(self, event_type, data=None):
        """Send a message to the bus."""
        if data is None:
            data = {}
        
        payload = {
            "type": event_type,
            "data": data,
            "context": {"source": self.name}
        }
        
        if self.connected:
            try:
                self.sio.emit('message', payload)
            except Exception as e:
                logger.error(f"Failed to emit {event_type}: {e}")
        else:
            logger.warning(f"Cannot emit {event_type}: Not connected")

    def run_forever(self):
        """Connect and keep running (blocking)."""
        self.connect()
        self.sio.wait()

    def connect(self):
        """Connect to the bus with retry logic."""
        url = f"http://{self.host}:{self.port}"
        
        while not self.connected:
            try:
                # Force polling because server is running in threading mode (no websockets)
                self.sio.connect(url, transports=['polling'], wait_timeout=5)
                # If we get here, connection successful (event handler sets self.connected)
                # self.connected = True # Let the event handler do this
                break 
            except Exception as e:
                logger.error(f"Connection failed ({url}): {e}. Retrying in 5s...")
                time.sleep(5)

    def close(self):
        self.sio.disconnect()

if __name__ == "__main__":
    # Test Client
    logging.basicConfig(level=logging.INFO)
    client = BusClient(name="TestClient")
    client.connect()
    
    client.on("test.event", lambda msg: print(f"Got test event: {msg}"))
    
    while True:
        client.emit("test.event", {"hello": "world"})
        time.sleep(5)
