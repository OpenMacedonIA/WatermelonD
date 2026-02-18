import logging
import os
import sys
import queue
import threading
import time

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from modules.bus_client import BusClient
from modules.speaker import Speaker

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [TTS] - %(levelname)s - %(message)s')
logger = logging.getLogger("TTSService")

class TTSService:
    def __init__(self):
        self.bus = BusClient(name="TTSService")
        
        # Queue to receive events from Speaker
        self.event_queue = queue.Queue()
        self.speaker = Speaker(self.event_queue)
        
        self.bus.connect()
        self.bus.on('speak', self.handle_speak)
        
        # Start monitoring speaker events
        threading.Thread(target=self.monitor_speaker, daemon=True).start()

    def handle_speak(self, message):
        data = message.get('data', {})
        text = data.get('text', '')
        if text:
            logger.info(f"Speaking: {text}")
            self.speaker.speak(text)

    def monitor_speaker(self):
        """Relay speaker events to bus."""
        while True:
            try:
                event = self.event_queue.get()
                msg_type = event.get('type')
                
                if msg_type == 'speaker_status':
                    status = event.get('status')
                    if status == 'speaking':
                        self.bus.emit('speak:start', {})
                    elif status == 'idle':
                        self.bus.emit('speak:done', {})
                
                self.event_queue.task_done()
            except Exception as e:
                logger.error(f"Error monitoring speaker: {e}")

    def run(self):
        logger.info("TTS Service Started")
        self.bus.run_forever()

if __name__ == "__main__":
    service = TTSService()
    service.run()
