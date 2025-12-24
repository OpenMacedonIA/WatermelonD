import time
import json
import threading
import logging
import numpy as np
import struct
import os
import sys
import base64
import wave

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from modules.bus_client import BusClient
from modules.config_manager import ConfigManager
from modules.utils import normalize_text

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [STT] - %(levelname)s - %(message)s')
logger = logging.getLogger("STTService")

# Optional Imports
try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

try:
    import sherpa_onnx
    SHERPA_AVAILABLE = True
except ImportError:
    SHERPA_AVAILABLE = False

class STTService:
    def __init__(self):
        self.bus = BusClient(name="STTService")
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get('stt', {})
        
        # Models
        self.vosk_model = None
        self.vosk_recognizer = None
        self.sherpa_recognizer = None
        
        self.setup_stt()
        
        # Connect to Bus
        self.bus.connect()
        self.bus.on('recognizer_loop:audio', self.on_audio)

    def setup_stt(self):
        engine = self.config.get('engine', 'vosk') # Default to vosk if not set
        logger.info(f"Setting up STT Engine: {engine}")
        
        if engine == 'sherpa':
            self.setup_sherpa()
        else:
            self.setup_vosk()

    def setup_vosk(self):
        if not VOSK_AVAILABLE:
            logger.error("Vosk not installed.")
            return
        
        model_path = self.config.get('model_path', "vosk-models/es")
        if os.path.exists(model_path):
            try:
                self.vosk_model = vosk.Model(model_path)
                self.vosk_recognizer = vosk.KaldiRecognizer(self.vosk_model, 16000)
                logger.info("Vosk Model loaded.")
            except Exception as e:
                logger.error(f"Failed to load Vosk: {e}")
        else:
            logger.warning(f"Vosk model not found at {model_path}")

    def setup_sherpa(self):
        if not SHERPA_AVAILABLE:
            logger.error("Sherpa-ONNX not installed.")
            return
        
        model_dir = self.config.get('sherpa_model_path', "models/sherpa")
        encoder = os.path.join(model_dir, "tiny-encoder.onnx")
        decoder = os.path.join(model_dir, "tiny-decoder.onnx")
        tokens = os.path.join(model_dir, "tiny-tokens.txt")
        
        if os.path.exists(encoder):
            try:
                self.sherpa_recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
                    encoder=encoder, decoder=decoder, tokens=tokens,
                    language="es", task="transcribe", num_threads=1
                )
                logger.info("Sherpa-ONNX loaded.")
            except Exception as e:
                logger.error(f"Failed to load Sherpa: {e}")
        else:
            logger.error(f"Sherpa models not found in {model_dir}")

    def on_audio(self, message):
        """
        Handle audio data from AudioService.
        """
        data = message.get('data', {})
        b64_data = data.get('data')
        rate = data.get('rate', 16000)
        
        if not b64_data:
            return
            
        try:
            raw_data = base64.b64decode(b64_data)
            logger.info(f"Received audio data: {len(raw_data)} bytes")
            
            # --- DEBUG: SAVE AUDIO TO FILE ---
            try:
                with wave.open("debug_last_audio.wav", "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(rate)
                    wf.writeframes(raw_data)
                logger.info("Saved debug_last_audio.wav")
            except Exception as e:
                logger.error(f"Failed to save debug audio: {e}")
            # ---------------------------------

            text = ""
            if self.sherpa_recognizer:
                text = self.transcribe_sherpa(raw_data, rate)
            elif self.vosk_model:
                text = self.transcribe_vosk(raw_data, rate)
            
            if text:
                self.process_text(text)
                
        except Exception as e:
            logger.error(f"Error processing audio: {e}")

    def transcribe_sherpa(self, raw_data, rate):
        samples = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
        s = self.sherpa_recognizer.create_stream()
        s.accept_waveform(rate, samples)
        self.sherpa_recognizer.decode_stream(s)
        return s.result.text.strip()

    def transcribe_vosk(self, raw_data, rate):
        if not self.vosk_recognizer:
            return ""
            
        # Feed the entire audio chunk
        self.vosk_recognizer.AcceptWaveform(raw_data)
        
        # Force a final result since AudioService sends complete utterances
        res = json.loads(self.vosk_recognizer.FinalResult())
        text = res.get('text', '')
        
        if text:
            logger.info(f"Vosk FinalResult: '{text}'")
            
        return text

    def check_wake_word(self, text):
        wake_words = self.config_manager.get('wake_words', ['neo', 'tio', 'bro'])
        if isinstance(wake_words, str): wake_words = [wake_words]
        
        text_lower = text.lower()
        for ww in wake_words:
            if ww.lower() in text_lower:
                return ww.lower()
        return None

    def process_text(self, text):
        logger.info(f"Transcribed: {text}")
        ww = self.check_wake_word(text)
        
        if ww:
            logger.info(f"Wake Word Detected: {ww}")
            self.bus.emit("recognizer_loop:wakeword", {"wakeword": ww})
            # Remove wake word
            text = text.replace(ww, "").strip()
        
        if text:
            self.bus.emit("recognizer_loop:utterance", {"utterances": [text]})

    def run(self):
        logger.info("STT Service Started")
        self.bus.run_forever()

if __name__ == "__main__":
    service = STTService()
    service.run()
