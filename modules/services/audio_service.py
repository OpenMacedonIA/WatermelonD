import time
import threading
import logging
import pyaudio
import numpy as np
import struct
import os
import sys
import base64

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from modules.bus_client import BusClient
from modules.utils import no_alsa_error

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [AUDIO] - %(levelname)s - %(message)s')
logger = logging.getLogger("AudioService")

class AudioService:
    def __init__(self):
        self.bus = BusClient(name="AudioService")
        self.is_listening = False
        self.is_paused = False
        
        self.bus.connect()
        self.bus.on('speak', self.on_speak_start)
        self.bus.on('speak:done', self.on_speak_done)

    def on_speak_start(self, data):
        self.is_paused = True

    def on_speak_done(self, data):
        self.is_paused = False

    def run(self):
        self.is_listening = True
        threading.Thread(target=self.mic_loop, daemon=True).start()
        self.bus.run_forever()

    def mic_loop(self):
        logger.info("Starting Microphone Loop...")
        CHUNK = 1024
        RATE = 16000
        THRESHOLD = 500 # Energy threshold
        SILENCE_LIMIT = 20 # Frames of silence to consider end of speech
        
        with no_alsa_error():
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
            stream.start_stream()
        
        audio_buffer = []
        silence_frames = 0
        is_recording = False
        
        while self.is_listening:
            if self.is_paused:
                time.sleep(0.1)
                continue

            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                
                # Simple Energy VAD
                shorts = struct.unpack("%dh" % (len(data) / 2), data)
                rms = np.sqrt(np.mean(np.square(shorts)))
                
                if rms > THRESHOLD:
                    if not is_recording:
                        is_recording = True
                        logger.info("Speech detected...")
                        self.bus.emit("recognizer_loop:record_begin")
                    silence_frames = 0
                else:
                    if is_recording:
                        silence_frames += 1
                
                if is_recording:
                    audio_buffer.append(data)
                    
                    if silence_frames > SILENCE_LIMIT:
                        # End of speech
                        logger.info("End of speech. Sending audio...")
                        self.bus.emit("recognizer_loop:record_end")
                        
                        raw_data = b''.join(audio_buffer)
                        # Encode to base64 for JSON transport
                        b64_data = base64.b64encode(raw_data).decode('utf-8')
                        
                        self.bus.emit("recognizer_loop:audio", {
                            "data": b64_data,
                            "rate": RATE,
                            "width": 2, # 16-bit
                            "channels": 1
                        })
                        
                        audio_buffer = []
                        is_recording = False
                        silence_frames = 0
                        
            except Exception as e:
                logger.error(f"Mic Loop Error: {e}")
                time.sleep(1)

if __name__ == "__main__":
    service = AudioService()
    service.run()
