import os
import json
import time
import threading
import logging
import pyaudio
from modules.utils import no_alsa_error, normalize_text
from modules.logger import vosk_logger, app_logger

try:
    import vosk
    VOSK_DISPONIBLE = True
except ImportError:
    vosk = None
    VOSK_DISPONIBLE = False

try:
    from faster_whisper import WhisperModel
    WHISPER_DISPONIBLE = True
except ImportError:
    WhisperModel = None
    WHISPER_DISPONIBLE = False

import numpy as np
import struct

class VoiceManager:
    def __init__(self, config_manager, speaker, on_command_detected, update_face_callback=None):
        self.config_manager = config_manager
        self.speaker = speaker
        self.on_command_detected = on_command_detected
        self.update_face = update_face_callback
        self.vosk_model = None
        self.whisper_model = None
        self.is_listening = False
        self.is_processing = False # Flag to pause listening during processing
        
        self.setup_vosk()
        self.setup_whisper()
        self.setup_sherpa()

    def setup_vosk(self):
        """Carga el modelo de reconocimiento de voz Vosk."""
        if VOSK_DISPONIBLE:
            model_path = self.config_manager.get('stt', {}).get('model_path', "vosk-models/es")
            if os.path.isdir(model_path):
                try:
                    self.vosk_model = vosk.Model(model_path)
                    vosk_logger.info(f"Modelo Vosk cargado desde: {model_path}")
                except Exception as e:
                    vosk_logger.error(f"Error al cargar modelo Vosk: {e}")
            else:
                vosk_logger.warning(f"Modelo Vosk no encontrado en '{model_path}'.")

    def setup_whisper(self):
        """Carga el modelo Faster-Whisper."""
        if WHISPER_DISPONIBLE:
            model_size = self.config_manager.get('stt', {}).get('whisper_model', "medium")
            model_path = "models/whisper" # Local path
            try:
                # Run on CPU with INT8 (fast enough for medium on modern CPU)
                # Or CUDA if available (auto-detected usually, but let's be safe with cpu for now or auto)
                device = "cpu" 
                compute_type = "int8"
                
                vosk_logger.info(f"Cargando Faster-Whisper ({model_size}) en {device}...")
                self.whisper_model = WhisperModel(model_size, device=device, compute_type=compute_type, download_root=model_path)
                vosk_logger.info("Faster-Whisper cargado correctamente.")
            except Exception as e:
                vosk_logger.error(f"Error cargando Faster-Whisper: {e}")

    def get_grammar(self, intents):
        """Construye la gramática para Vosk basada en los intents."""
        if not intents:
            return None
            
        words = set()
        # Wake words list
        wake_words = self.config_manager.get('wake_words', ['neo', 'tio', 'bro', 'hermano', 'colega', 'nen'])
        if isinstance(wake_words, str): wake_words = [wake_words]
        
        for ww in wake_words:
            words.add(ww.lower())
            
        for intent in intents:
            for trigger in intent.get('triggers', []):
                norm = normalize_text(trigger)
                for w in norm.split():
                    words.add(w)
                    
        numeros = ["uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez",
                   "once", "doce", "trece", "catorce", "quince", "veinte", "treinta", "cuarenta", "cincuenta",
                   "sesenta", "setenta", "ochenta", "noventa", "cien",
                   "minuto", "minutos", "hora", "horas", "alarma", "recordatorio"]
        words.update(numeros)
        
        return json.dumps(list(words), ensure_ascii=False)

    def start_listening(self, intents=None):
        """Inicia el bucle de escucha en un hilo separado."""
        app_logger.info(f"DEBUG: start_listening called. Intents: {bool(intents)}")
        self.is_listening = True
        self.listener_thread = threading.Thread(target=self._continuous_voice_listener, args=(intents,), daemon=True)
        self.listener_thread.start()
        app_logger.info("DEBUG: listener_thread started.")

    def stop_listening(self):
        self.is_listening = False

    def set_processing(self, processing):
        """Pausa o reanuda la escucha activa."""
        self.is_processing = processing

    def _check_wake_word(self, text):
        """Verifica si el texto contiene alguna palabra de activación (Fuzzy)."""
        wake_words = self.config_manager.get('wake_words', ['neo', 'tio', 'bro', 'hermano', 'colega', 'nen'])
        if isinstance(wake_words, str): wake_words = [wake_words]
        
        text_lower = text.lower()
        
        # 1. Direct Match (Fastest)
        for ww in wake_words:
            if ww.lower() in text_lower:
                return ww.lower()
        
        # 2. Fuzzy Match (RapidFuzz)
        if VOSK_DISPONIBLE: # Reusing VOSK flag for general optional libs check or check rapidfuzz explicitly
            try:
                from rapidfuzz import fuzz
                # Check each word in the text against wake words
                words = text_lower.split()
                for word in words:
                    for ww in wake_words:
                        ratio = fuzz.ratio(word, ww.lower())
                        if ratio > 85: # 85% similarity
                            vosk_logger.info(f"Fuzzy Wake Word Detected: '{word}' ~= '{ww}' ({ratio}%)")
                            return ww.lower()
            except ImportError:
                pass
                
        return None

    def _continuous_voice_listener(self, intents):
        """Bucle principal de escucha de voz."""
        stt_config = self.config_manager.get('stt', {})
        stt_engine = stt_config.get('engine', 'vosk') # Default to vosk
        app_logger.info(f"DEBUG: Listening thread running. Engine: {stt_engine} | Raw Config: {stt_config}")
        
        if stt_engine == 'sherpa':
            self._sherpa_listener()
            return

        # Disable Whisper for now as implementation is missing (causing crash loop)
        # if stt_engine == 'whisper' and self.whisper_model:
        #    self._whisper_listener()
        #    return

        if not self.vosk_model:
            vosk_logger.error("Modelo Vosk no cargado. No se puede iniciar escucha.")
            return

        app_logger.info("DEBUG: Vosk model present. initializing recognizer...")
        use_grammar = self.config_manager.get('stt', {}).get('use_grammar', True)
        
        if use_grammar and intents:
            grammar = self.get_grammar(intents)
            recognizer = vosk.KaldiRecognizer(self.vosk_model, 16000, grammar)
        else:
            recognizer = vosk.KaldiRecognizer(self.vosk_model, 16000)
            
        app_logger.info("DEBUG: Recognizer initialized. Starting PyAudio...")
            
        with no_alsa_error():
            p = pyaudio.PyAudio()
            device_index = self.config_manager.get('stt', {}).get('input_device_index', None)
            last_face_update = 0
            try:
                stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, 
                                frames_per_buffer=8192, input_device_index=device_index)
                stream.start_stream()
                vosk_logger.info(f"Escucha activa. Motor: {stt_engine}")
            except Exception as e:
                vosk_logger.error(f"Error stream audio: {e}")
                self.is_listening = False # Disable loop to prevent watchdog spam
                return

        while self.is_listening:
            try:
                # Pause if speaker is busy or system is processing a command
                if self.speaker.is_busy or self.is_processing:
                    time.sleep(0.1) 
                    continue

                data = stream.read(4096, exception_on_overflow=False)

                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    command = result.get('text', '')
                    if command:
                        ww = self._check_wake_word(command)
                        # Pass wake word if found, or just 'neo' as default if logic requires it
                        self.on_command_detected(command, ww if ww else 'neo')
                else:
                    # Check for partial results to trigger "listening" animation
                    partial = json.loads(recognizer.PartialResult())
                    if partial.get('partial') and self.update_face:
                         # Only update if we haven't recently (to avoid spamming)
                         current_time = time.time()
                         if current_time - last_face_update > 1.0:
                             self.update_face('listening')
                             last_face_update = current_time

            except IOError as e:
                # Common PyAudio overflow/underflow
                if e.errno == pyaudio.paInputOverflowed:
                    pass # Ignore overflow
                else:
                    vosk_logger.error(f"Error I/O Audio: {e}")
                    time.sleep(1)
            except Exception as e:
                vosk_logger.error(f"Error en bucle de voz: {e}")
                time.sleep(1)
        
        # Cleanup
        try:
            stream.stop_stream()
            stream.close()
            p.terminate()
            vosk_logger.info("Stream de audio cerrado correctamente.")
        except Exception as e:
            vosk_logger.error(f"Error cerrando stream: {e}")

    def _whisper_listener(self):
        """Bucle de escucha para Faster-Whisper con VAD basado en energía."""
        # ... (Existing Whisper code kept for reference or fallback) ...
        pass

    def setup_sherpa(self):
        """Carga el modelo Sherpa-ONNX (Whisper Tiny)."""
        try:
            import sherpa_onnx
            model_dir = self.config_manager.get('stt', {}).get('sherpa_model_path', "models/sherpa")
            
            # Whisper ONNX files
            encoder = os.path.join(model_dir, "tiny-encoder.onnx")
            decoder = os.path.join(model_dir, "tiny-decoder.onnx")
            tokens = os.path.join(model_dir, "tiny-tokens.txt")
            
            if not os.path.exists(encoder):
                vosk_logger.error(f"Modelo Sherpa Whisper no encontrado en {model_dir}")
                return

            vosk_logger.info(f"Cargando Sherpa-ONNX Whisper desde {model_dir}...")
            self.sherpa_recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
                encoder=encoder,
                decoder=decoder,
                tokens=tokens,
                language="es",
                task="transcribe",
                num_threads=1
            )
            vosk_logger.info("Sherpa-ONNX Whisper cargado correctamente.")
        except Exception as e:
            vosk_logger.error(f"Error cargando Sherpa-ONNX: {e}")
            self.sherpa_recognizer = None

    def _sherpa_listener(self):
        """Bucle de escucha para Sherpa-ONNX (Offline Whisper con VAD)."""
        if not self.sherpa_recognizer:
            vosk_logger.error("Sherpa Recognizer no inicializado.")
            return

        vosk_logger.info("Iniciando escucha con Sherpa-ONNX (Whisper)...")
        
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        THRESHOLD = 500 # Sensitivity (matched to debug script)
        SILENCE_LIMIT = 20 # ~1s silence to trigger
        
        p = pyaudio.PyAudio()
        device_index = self.config_manager.get('stt', {}).get('input_device_index', None)
        
        try:
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                            frames_per_buffer=CHUNK, input_device_index=device_index)
            stream.start_stream()
        except Exception as e:
            vosk_logger.error(f"Error abriendo stream PyAudio: {e}")
            return

        audio_buffer = []
        silence_frames = 0
        is_recording = False
        last_face_update = 0
        
        while self.is_listening:
            try:
                if self.speaker.is_busy or self.is_processing:
                    time.sleep(0.1)
                    continue
                
                data = stream.read(CHUNK, exception_on_overflow=False)
                shorts = struct.unpack("%dh" % (len(data) / 2), data)
                rms = np.sqrt(np.mean(np.square(shorts)))
                
                if rms > THRESHOLD:
                    is_recording = True
                    silence_frames = 0
                    
                    current_time = time.time()
                    if self.update_face and (current_time - last_face_update > 1.0):
                        self.update_face('listening')
                        last_face_update = current_time
                else:
                    if is_recording:
                        silence_frames += 1
                
                if is_recording:
                    audio_buffer.append(data)
                    
                    if silence_frames > SILENCE_LIMIT:
                        # End of speech
                        if self.update_face: self.update_face('thinking')
                        
                        raw_data = b''.join(audio_buffer)
                        samples = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
                        
                        s = self.sherpa_recognizer.create_stream()
                        s.accept_waveform(RATE, samples)
                        self.sherpa_recognizer.decode_stream(s)
                        text = s.result.text.strip()
                        
                        if text:
                            vosk_logger.info(f"Sherpa escuchó: '{text}'")
                            ww = self._check_wake_word(text)
                            self.on_command_detected(text, ww if ww else 'neo')
                        
                        audio_buffer = []
                        is_recording = False
                        silence_frames = 0
                        if self.update_face: self.update_face('idle')
                
            except Exception as e:
                vosk_logger.error(f"Error en Sherpa Listener: {e}")
                time.sleep(1)

