import threading
import queue
import os
import subprocess
import hashlib
import json
import time
import shlex
from modules.logger import tts_logger

try:
    from piper import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False

CACHE_DIR = "tts_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

class Speaker:
    def __init__(self, event_queue):
        self.speak_queue = queue.Queue()
        self.event_queue = event_queue
        self._is_busy = False
        self.is_available = False
        self.voice = None # Instancia de PiperVoice
        
        # Cargar configuración
        self.config = self._load_config()
        tts_config = self.config.get('tts', {})
        
        self.engine = tts_config.get('engine', 'piper')
        self.piper_model = tts_config.get('piper_model', 'piper/voices/es_ES-davefx-medium.onnx')
        self.espeak_args = tts_config.get('espeak_args', '-v es')
        
        # Resolver rutas
        cwd = os.getcwd()
        if not os.path.exists(self.piper_model):
            potential_model = os.path.join(cwd, self.piper_model)
            if os.path.exists(potential_model):
                self.piper_model = potential_model

        # Comprobar disponibilidad
        self.is_available = self._check_engine()

        if self.is_available:
            tts_logger.info(f"Motor de voz '{self.engine}' inicializado correctamente.")
        else:
            tts_logger.warning("No se encontró motor de voz. Usando modo 'Dummy' (solo logs).")
            self.engine = 'dummy'
            self.is_available = True

        self.speak_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.speak_thread.start()

    def _load_config(self):
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except:
            return {}

    def _check_engine(self):
        """Verifica si el motor seleccionado es viable."""
        if self.engine == 'piper':
            if not PIPER_AVAILABLE:
                tts_logger.warning("Módulo 'piper' no instalado. Buscando binario...")
                if os.path.exists("piper_bin/piper/piper"):
                    tts_logger.info("Binario Piper encontrado.")
                    # Comprobar existencia del modelo
                    if os.path.isfile(self.piper_model):
                        return True
                    else:
                        tts_logger.error(f"Modelo Piper no encontrado en {self.piper_model}")
                        return False
                else:
                    tts_logger.error("Ni módulo ni binario de Piper encontrados.")
                    return False
                
            if os.path.isfile(self.piper_model):
                try:
                    # Cargar modelo una vez
                    self.voice = PiperVoice.load(self.piper_model)
                    tts_logger.info(f"Modelo Piper cargado: {self.piper_model}")
                    return True
                except Exception as e:
                    tts_logger.error(f"Error cargando modelo Piper: {e}")
                    return False
            else:
                tts_logger.warning(f"Modelo Piper no encontrado en {self.piper_model}")
                return False
            
            # Comprobar utilidad aplay
            import shutil
            if not shutil.which('aplay'):
                tts_logger.error("Comando 'aplay' no encontrado. Instala alsa-utils.")
                return False
                
            return True
        
        if self.engine == 'espeak':
            # Comprobar si espeak está instalado
            try:
                subprocess.run(['which', 'espeak'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except subprocess.CalledProcessError:
                try:
                    subprocess.run(['which', 'espeak-ng'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.engine = 'espeak-ng' 
                    return True
                except:
                    tts_logger.error("Espeak no encontrado.")
                    return False
        
        return False

    def _process_queue(self):
        """Procesa la cola de habla (TTS)."""
        while True:
            # Get bloqueante con tiempo de espera - evita que la CPU se revolucione
            try:
                item = self.speak_queue.get(timeout=1.0)
            except queue.Empty:
                # Si no hay items en la cola, continuar el bucle
                continue
            
            # Manejar el archivo WAV directamente
            if isinstance(item, dict) and item.get('type') == 'wav':
                file_path = item.get('path')
                tts_logger.info(f"Reproduciendo WAV: {file_path}")
                self._is_busy = True
                try:
                    self.event_queue.put({'type': 'speaker_status', 'status': 'speaking'})
                    subprocess.run(f'aplay -q "{file_path}"', shell=True, check=True, timeout=5)
                except Exception as e:
                    tts_logger.error(f"Error reproduciendo WAV: {e}")
                finally:
                    self._is_busy = False
                    self.event_queue.put({'type': 'speaker_status', 'status': 'idle'})
                    self.speak_queue.task_done()
                continue

            # Manejar Texto
            text = item
            tts_logger.info(f"Speaker Queue recibió: '{text}'")
            self._is_busy = True
            try:
                tts_logger.info(f"Intentando decir ({self.engine}): '{text}'")
                
                # --- DUMMY MODE ---
                if self.engine == 'dummy':
                    # print(f"\n[T.I.O. DICE]: {text}\n") # Verbosidad reducida
                    time.sleep(1) 

                    # La lógica continúa hasta el bloque finally
                
                else:
                    # --- TTS CACHE ---
                    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
                    cache_file = os.path.join(CACHE_DIR, f"{text_hash}_{self.engine}.wav")
                    
                    command = None
                    
                    if os.path.exists(cache_file):
                        tts_logger.info(f"Usando audio en caché: {cache_file}")
                        command = f'aplay -q "{cache_file}"'
                        if command:
                            self.event_queue.put({'type': 'speaker_status', 'status': 'speaking'})
                            subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
                    else:
                        # Generar audio

                        if self.engine == 'piper':
                            self.event_queue.put({'type': 'speaker_status', 'status': 'speaking'})
                            
                            if self.voice:
                                # Modo de API de Python
                                try:
                                    stream = self.voice.synthesize(text)
                                    first_chunk = next(stream)
                                    rate = str(first_chunk.sample_rate)
                                    aplay_cmd = ['aplay', '-r', rate, '-f', 'S16_LE', '-t', 'raw', '-q']
                                    with subprocess.Popen(aplay_cmd, stdin=subprocess.PIPE) as proc:
                                        proc.stdin.write(first_chunk.audio_int16_bytes)
                                        for chunk in stream:
                                            proc.stdin.write(chunk.audio_int16_bytes)
                                        proc.stdin.close()
                                        proc.wait(timeout=15)
                                except StopIteration:
                                    pass
                                except Exception as e:
                                    tts_logger.error(f"Error crítico en Piper (Python): {e}")
                            
                            else:
                                # Modo Binario
                                piper_bin = "piper_bin/piper/piper"
                                if os.path.exists(piper_bin):
                                    try:
                                        # echo 'text' | ./piper --model model.onnx --output_raw | aplay ...
                                        # El binario de Piper devuelve raw 16-bit mono PCM firmado
                                        # Necesitamos saber la frecuencia de muestreo. Normalmente 22050 para modelos medianos.
                                        # Lo podemos parchear desde la config json pero asumiremos 22050 por ahora o la leemos desde la config.
                                        
                                        # Construir tubería de comandos (pipeline)
                                        # echo text | piper ... | aplay ...
                                        
                                        safe_text = shlex.quote(text)
                                        model_path = self.piper_model
                                        
                                        # Comprobar si existe el modelo
                                        if not os.path.exists(model_path):
                                            tts_logger.error(f"Modelo no encontrado: {model_path}")
                                            return

                                        cmd = f'echo {safe_text} | "{piper_bin}" --model "{model_path}" --output_raw | aplay -r 22050 -f S16_LE -t raw -q'
                                        
                                        tts_logger.info(f"Ejecutando Piper Binary: {cmd}")
                                        subprocess.run(cmd, shell=True, check=True, timeout=15)
                                        
                                    except subprocess.CalledProcessError as e:
                                        tts_logger.error(f"Error ejecutando Piper Binary: {e}")
                                    except Exception as e:
                                        tts_logger.error(f"Error general en Piper Binary: {e}")
                                else:
                                    tts_logger.error("No se encontró ni módulo Python ni binario de Piper.")

                        elif self.engine.startswith('espeak'):
                            safe_text = shlex.quote(text)
                            bin_name = 'espeak-ng' if self.engine == 'espeak-ng' else 'espeak'
                            gen_cmd = f'{bin_name} {self.espeak_args} -w "{cache_file}" {safe_text}'
                            subprocess.run(gen_cmd, shell=True, check=True, timeout=10)
                            command = f'aplay -q "{cache_file}"'
                            
                            if command:
                                self.event_queue.put({'type': 'speaker_status', 'status': 'speaking'})
                                subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
                                
            except subprocess.TimeoutExpired:
                tts_logger.error(f"Timeout en Speaker ({self.engine}) procesando: '{text}'")
            except Exception as e:
                tts_logger.error(f"Error en Speaker ({self.engine}): {e}")
            finally:
                self._is_busy = False
                self.event_queue.put({'type': 'speaker_status', 'status': 'idle'})
                self.speak_queue.task_done()

    def speak(self, text):
        if self.is_available: self.speak_queue.put(text)
    
    def play_wav(self, file_path):
        """Reproduce un archivo WAV directamente."""
        if self.is_available and os.path.exists(file_path):
            self.speak_queue.put({'type': 'wav', 'path': file_path})

    def play_random_filler(self):
        """Reproduce una palabra de relleno aleatoria."""
        filler_dir = "resources/sounds/fillers"
        if not os.path.exists(filler_dir):
            return
        
        try:
            files = [f for f in os.listdir(filler_dir) if f.endswith('.wav')]
            if files:
                import random
                selected = random.choice(files)
                self.play_wav(os.path.join(filler_dir, selected))
        except Exception as e:
            tts_logger.error(f"Error seleccionando filler: {e}")

    @property
    def is_busy(self): return self._is_busy or not self.speak_queue.empty()

