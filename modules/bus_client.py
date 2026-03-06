import socketio
import logging
import json
import threading
import time

logger = logging.getLogger("BusClient")

class BusClient:
    def __init__(self, host='localhost', port=5000, name="UnknownClient"):
        # Desactivamos verificación SSL local para que pueda conectarse internamente si el server es HTTPS
        self.sio = socketio.Client(ssl_verify=False)
        self.host = host
        self.port = port
        self.name = name
        self.handlers = {} # Mapa event_type -> [callbacks]
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
            Manejar mensajes entrantes del bus.
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
        """Registrar un callback para un tipo de evento específico."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(callback)

    def emit(self, event_type, data=None):
        """Enviar un mensaje al bus."""
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
        """Conectar y mantener en ejecución (bloqueante)."""
        self.connect()
        self.sio.wait()

    def connect(self):
        """Conectar al bus probando HTTP y HTTPS localmente con lógica de reintento."""
        urls_to_try = [
            f"https://{self.host}:{self.port}",
            f"http://{self.host}:{self.port}",
        ]
        
        url_idx = 0
        while not self.connected:
            url = urls_to_try[url_idx % len(urls_to_try)]
            print(f"DEBUG: [{self.name}] BusClient connecting to {url}")
            
            try:
                # Forzar polling porque el servidor se está ejecutando en modo threading (sin websockets)
                self.sio.connect(url, transports=['polling'], wait_timeout=5)
                # Si llegamos aquí, conexión exitosa
                break 
            except Exception as e:
                if self.host != 'localhost':
                    logger.warning(f"Connection failed ({url}): {e}")
                else:
                    logger.debug(f"Connection failed ({url}): {e}")
                
                # Probar el otro protocolo en la siguiente iteración
                url_idx += 1
                if url_idx % len(urls_to_try) == 0:
                    time.sleep(3) # Solo esperar si han fallado ambos

    def close(self):
        self.sio.disconnect()

if __name__ == "__main__":
    # Cliente de Prueba
    logging.basicConfig(level=logging.INFO)
    client = BusClient(name="TestClient")
    client.connect()
    
    client.on("test.event", lambda msg: print(f"Got test event: {msg}"))
    
    while True:
        client.emit("test.event", {"hello": "world"})
        time.sleep(5)
