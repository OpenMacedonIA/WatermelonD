import logging
import os
import sys
import threading

# Añadir raíz a la ruta de búsqueda
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from modules.bus_client import BusClient
from modules.web_admin import app, socketio

# Configurar registro
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [WEB] - %(levelname)s - %(message)s')
logger = logging.getLogger("WebService")

class WebService:
    def __init__(self):
        self.bus = BusClient(name="WebService")
        self.bus.connect()
        
        # Registrar Eventos del Bus para enviar al Navegador
        self.bus.on('speak:start', self.on_speak_start)
        self.bus.on('speak:done', self.on_speak_done)
        self.bus.on('recognizer_loop:wakeword', self.on_wakeword)
        self.bus.on('recognizer_loop:record_begin', self.on_listening)
        self.bus.on('recognizer_loop:record_end', self.on_thinking)
        
        # También escuchar actualizaciones genéricas de interfaz si las hay
        self.bus.on('face.update', self.on_face_update)
        
        # Eventos de Habilidades Visuales
        self.bus.on('visual:show', self.on_visual_show)
        self.bus.on('visual:close', self.on_visual_close)

        # Escuchar comandos de texto de la GUI
        socketio.on_event('gui:text_command', self.on_gui_text_command)

    def on_gui_text_command(self, data):
        """Inyecta texto desde la GUI como si fuera una locución hablada."""
        text = data.get('text')
        if text:
            logger.info(f"Injecting GUI Command: {text}")
            # Emular el evento del bucle reconocedor de Mycroft/OVOS
            self.bus.emit("recognizer_loop:utterance", {
                "utterances": [text],
                "lang": "es-es",
                "session": "gui_user"
            })

    def update_face(self, state, data=None):
        if data is None: data = {}
        logger.info(f"Updating Face: {state}")
        socketio.emit('face_update', {'state': state, 'data': data})

    def on_speak_start(self, data):
        self.update_face('speaking')

    def on_speak_done(self, data):
        self.update_face('idle')

    def on_wakeword(self, data):
        self.update_face('listening')

    def on_listening(self, data):
        self.update_face('listening')

    def on_thinking(self, data):
        self.update_face('thinking')

    def on_face_update(self, message):
        data = message.get('data', {})
        state = data.get('state', 'idle')
        payload = data.get('data', {})
        self.update_face(state, payload)

    def on_visual_show(self, message):
        """Reenvía evento de mostrar contenido visual."""
        data = message.get('data', {}) # {'url': ..., 'type': ...}
        logger.info(f"Visual Show: {data}")
        socketio.emit('visual:show', data)

    def on_visual_close(self, message):
        """Reenvía evento de cerrar contenido visual."""
        logger.info("Visual Close")
        socketio.emit('visual:close', {})

    def run(self):
        logger.info("Starting Web Service (Flask + SocketIO)...")
        # Ejecutar Flask-SocketIO
        # Nota: Usamos allow_unsafe_werkzeug=True como en el código original
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)

if __name__ == "__main__":
    service = WebService()
    service.run()
