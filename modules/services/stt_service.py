import time
import json
import threading
import logging
import numpy as np
import struct
import os
import sys
import base64

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from modules.bus_client import BusClient
from modules.config_manager import ConfigManager
from modules.utils import normalize_text
from modules.stt_postprocessor import get_processor

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [STT] - %(levelname)s - %(message)s')
logger = logging.getLogger("STTService")

# Optional Imports
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
        self.sherpa_recognizer = None
        
        # Post-processor for error correction
        self.postprocessor = get_processor(self.config_manager)
        
        self.setup_stt()
        
        # Connect to Bus
        self.bus.connect()
        self.bus.on('recognizer_loop:audio', self.on_audio)

    def setup_stt(self):
        engine = 'sherpa'
        logger.info(f"Setting up STT Engine: {engine}")
        self.setup_sherpa()

    def setup_sherpa(self):
        if not SHERPA_AVAILABLE:
            logger.error("Sherpa-ONNX not installed.")
            return
        
        model_dir = self.config.get('sherpa_model_path', "models/sherpa/sherpa-onnx-whisper-medium")
        
        # Auto-detect model if path points to generic dir but specific model exists
        if model_dir == "models/sherpa" and os.path.exists("models/sherpa/sherpa-onnx-whisper-medium"):
             model_dir = "models/sherpa/sherpa-onnx-whisper-medium"
        
        encoder = os.path.join(model_dir, "encoder.onnx")
        decoder = os.path.join(model_dir, "decoder.onnx")
        tokens = os.path.join(model_dir, "tokens.txt")
        
        # Fallback for old file names (tiny-encoder.onnx, etc)
        if not os.path.exists(encoder):
            # Try finding any *encoder.onnx
            files = os.listdir(model_dir) if os.path.exists(model_dir) else []
            for f in files:
                if f.endswith("encoder.onnx"): encoder = os.path.join(model_dir, f)
                if f.endswith("decoder.onnx"): decoder = os.path.join(model_dir, f)
                if f.endswith("tokens.txt"): tokens = os.path.join(model_dir, f)

        if os.path.exists(encoder):
            try:
                # Determine thread count
                num_threads = int(self.config.get('num_threads', 2))
                
                self.sherpa_recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
                    encoder=encoder, decoder=decoder, tokens=tokens,
                    language="es", task="transcribe", num_threads=num_threads
                )
                logger.info(f"Sherpa-ONNX loaded from {model_dir}")
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
            
            text = ""
            if self.sherpa_recognizer:
                text = self.transcribe_sherpa(raw_data, rate)
            
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



    def check_wake_word(self, text):
        wake_words = self.config_manager.get('wake_words', ['neo', 'tio', 'bro'])
        if isinstance(wake_words, str): wake_words = [wake_words]
        
        text_lower = text.lower()
        for ww in wake_words:
            if ww.lower() in text_lower:
                return ww.lower()
        return None

    def process_text(self, text):
        # Apply post-processing corrections
        text = self.postprocessor.process(text)
        
        logger.info(f"Transcribed (post-processed): {text}")
        ww = self.check_wake_word(text)
        
        if ww:
            logger.info(f"Wake Word Detected: {ww}")
            self.bus.emit("recognizer_loop:wakeword", {"wakeword": ww})
            # Remove wake word using post-processor
            text = self.postprocessor.remove_wake_word(text, [ww])
        
        if text:
            self.bus.emit("recognizer_loop:utterance", {"utterances": [text]})

    def run(self):
        logger.info("STT Service Started")
        self.bus.run_forever()

if __name__ == "__main__":
    service = STTService()
    service.run()
