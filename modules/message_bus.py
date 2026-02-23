import eventlet
# Monkey patch para eventlet (requerido para asincronía) - DEBE SER EL PRIMERO
eventlet.monkey_patch()

import logging
from flask import Flask
from flask_socketio import SocketIO, emit

# Configurar Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [BUS] - %(levelname)s - %(message)s')
logger = logging.getLogger("MessageBus")

class MessageBus:
    def __init__(self, host='0.0.0.0', port=8181):
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='eventlet')
        
        self.setup_routes()

    def setup_routes(self):
        @self.socketio.on('connect')
        def handle_connect():
            logger.info("Client connected")

        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info("Client disconnected")

        @self.socketio.on('message')
        def handle_message(data):
            """
            Emite cualquier mensaje recibido a todos los demás clientes.
            Estructura de datos esperada:
            {
                "type": "event.name",
                "data": { ... }
            }
            """
            msg_type = data.get('type', 'unknown')
            # logger.debug(f"Bus received: {msg_type}")
            # Emitir de vuelta a todos los clientes (incluido el remitente, o excluir si es necesario)
            # El bus de OVOS normalmente emite a todo el mundo.
            emit('message', data, broadcast=True, include_self=False)

    def run(self):
        logger.info(f"Starting Message Bus on {self.host}:{self.port}")
        self.socketio.run(self.app, host=self.host, port=self.port)

if __name__ == "__main__":
    bus = MessageBus()
    bus.run()
