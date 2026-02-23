import threading
import os
import queue
import time
import logging
import locale
import json
import random
from datetime import datetime, date, timedelta
from functools import lru_cache

# --- Módulos Internos ---
from modules.logger import app_logger
from modules.speaker import Speaker
from modules.calendar_manager import CalendarManager
from modules.alarms import AlarmManager
from modules.config_manager import ConfigManager
from modules.BlueberrySkills.system import SystemSkill
from modules.BlueberrySkills.network import NetworkSkill
from modules.BlueberrySkills.time_date import TimeDateSkill

from modules.BlueberrySkills.media import MediaSkill
from modules.BlueberrySkills.organizer import OrganizerSkill
from modules.BlueberrySkills.ssh import SSHSkill
from modules.BlueberrySkills.files import FilesSkill
from modules.BlueberrySkills.finder import FinderSkill
from modules.BlueberrySkills.docker import DockerSkill
from modules.BlueberrySkills.diagnosis import DiagnosisSkill
from modules.BlueberrySkills.visual import VisualSkill
from modules.ssh_manager import SSHManager
from modules.wifi_manager import WifiManager
# from modules.vision import VisionManager # Carga perezosa para evitar segfaults de CV2
from modules.file_manager import FileManager
from modules.bus_client import BusClient
from modules.cast_manager import CastManager
from modules.utils import load_json_data
from modules.mqtt_manager import MQTTManager
from modules.ai_engine import AIEngine
from modules.voice_manager import VoiceManager
from modules.intent_manager import IntentManager
from modules.keyword_router import KeywordRouter
from modules.chat import ChatManager
from modules.BrainNut.engine import MangoManager # MANGO T5
from modules.health_manager import HealthManager # Self-Healing
from modules.bluetooth_manager import BluetoothManager
from modules.plugin_loader import PluginLoader
from modules.decision_router import DecisionRouter
from modules.onnx_runner import SpecificModelRunner # New ONNX Runtime Runner
from modules.text_normalizer import TextNormalizer # Text Normalization Module


# --- Módulos Opcionales ---
try:
    from modules.sysadmin import SysAdminManager
except ImportError:
    SysAdminManager = None

try:
    from modules.brain import Brain
except ImportError:
    Brain = None

try:
    from modules.secure_intent_matcher import SecureIntentMatcher
except ImportError:
    SecureIntentMatcher = None

try:
    import modules.web_admin as web_admin_module
    from modules.web_admin import run_server, update_face, set_audio_status
    WEB_ADMIN_DISPONIBLE = True
except ImportError as e:
    app_logger.error(f"No se pudo importar Web Admin: {e}")
    WEB_ADMIN_DISPONIBLE = False
    web_admin_module = None
    update_face = None

try:
    from modules.network import NetworkManager
except ImportError:
    NetworkManager = None

try:
    from modules.guard import Guard
except ImportError:
    Guard = None

try:
    from modules.sherlock import Sherlock
except ImportError:
    Sherlock = None

try:
    import vlc
except ImportError:
    vlc = None

class SocketLogHandler(logging.Handler):
    """Manejador para transmitir logs al cliente web a través de SocketIO."""
    def __init__(self, socketio):
        super().__init__()
        self.socketio = socketio
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        try:
            msg = self.format(record)
            self.socketio.emit('log_message', {'msg': msg}, namespace='/')
        except Exception:
            self.handleError(record)

app_logger.info("El registro de logs ha sido iniciado (desde NeoCore Refactored).")

class NeoCore:
    """
    Controlador principal de Neo.
    Orquesta VoiceManager, IntentManager, AI Engine y Skills.
    """
    def __init__(self):
        # --- Asignar Logger al objeto para que los Skills lo usen ---
        self.app_logger = app_logger
        self.app_logger.info("Iniciando Neo Core (System v2.5.0 - Optimized)...")

        try:
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        except locale.Error:
            self.app_logger.warning("Localización 'es_ES.UTF-8' no encontrada. Usando configuración por defecto.")
            # --- Configuración ---
            CONFIG_FILE = "config/config.json"
            try:
                locale.setlocale(locale.LC_TIME, '')
            except:
                pass

        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_all()
        
        # --- Variables de Estado ---
        self.last_find_results = None

        self.event_queue = queue.Queue()
        # --- Corrección para Segfaults de Distrobox/Jack ---
        jack_no_start = self.config.get('audio', {}).get('jack_no_start_server', '1')
        os.environ["JACK_NO_START_SERVER"] = str(jack_no_start)
        # --- Salida de Audio (Altavoz) ---
        try:
            self.speaker = Speaker(self.event_queue)
            self.audio_output_enabled = True
            self.app_logger.info("[OK] Audio Output (Speaker) initialized successfully.")
        except Exception as e:
            self.app_logger.error(f"[ERROR] Failed to initialize Speaker: {e}. Using Mock.")
            self.speaker = type('MockSpeaker', (object,), {'speak': lambda self, t: self.app_logger.info(f"[MOCK SPEAK]: {t}"), 'play_random_filler': lambda self: None, 'is_busy': False})()
            self.audio_output_enabled = False
        
        # --- Alias para compatibilidad con Skills ---
        self.skills_config = self.config.get('skills', {})
        
        # --- Gestores de IA y Núcleo ---
        model_path = self.config.get('ai_model_path')
        self.ai_engine = AIEngine(model_path=model_path) 
        self.intent_manager = IntentManager(self.config_manager)
        self.decision_router = DecisionRouter(self.config_manager)
        self.onnx_runner = SpecificModelRunner() # Initialize specialized runner
        self.text_normalizer = TextNormalizer() # Initialize normalizer
        self.keyword_router = KeywordRouter(self)
        # --- Entrada de Audio (Gestor de Voz) ---
        try:
            self.voice_manager = VoiceManager(
                self.config_manager, 
                self.speaker, 
                self.on_voice_command,
                update_face
            )
            self.audio_input_enabled = True
            self.app_logger.info("[OK] Audio Input (VoiceManager) initialized successfully.")
        except Exception as e:
            self.app_logger.error(f"[ERROR] Failed to initialize VoiceManager: {e}. Using Mock.")
            self.voice_manager = type('MockVoice', (object,), {'start_listening': lambda self, i: None, 'stop_listening': lambda self: None, 'set_processing': lambda self, p: None, 'is_listening': False})()
            self.audio_input_enabled = False

        # --- Cliente de Bus (Inyección CLI / Externa) ---
        self.bus = BusClient(name="NeoCore")
        self.bus.on('command:inject', self.handle_injected_command)
        app_logger.info(f"BusClient configured for {self.bus.host}:{self.bus.port}. Starting thread.")
        # Iniciar hilo del bus
        threading.Thread(target=self.bus.run_forever, daemon=True).start()
        
        # Actualizar estado del Web Admin
        if WEB_ADMIN_DISPONIBLE:
            set_audio_status(getattr(self, 'audio_output_enabled', False), getattr(self, 'audio_input_enabled', False))
            self.web_server = web_admin_module
            
            # Adjuntar manejador de logs de SocketIO
            try:
                # Eliminar manejadores de socket existentes para evitar duplicados al reiniciar
                for h in self.app_logger.handlers[:]:
                    if isinstance(h, SocketLogHandler):
                        self.app_logger.removeHandler(h)
                
                socket_handler = SocketLogHandler(self.web_server.socketio)
                self.app_logger.addHandler(socket_handler)
                self.app_logger.info("[OK] Log Streaming to WebClient enabled.")
            except Exception as e:
                self.app_logger.warning(f"Could not attach Socket Log Handler: {e}")
        else:
            self.web_server = None
            
        self.chat_manager = ChatManager(self.ai_engine)
        self.mango_manager = MangoManager() # Initialize MANGO T5
        self.health_manager = HealthManager(self.config_manager)
        
        # Iniciar ingesta de RAG en segundo plano
        self._rag_thread = threading.Thread(target=self.chat_manager.knowledge_base.ingest_docs, daemon=True, name="RAG_Ingest")
        self._rag_thread.start()

        # --- Gestores Heredados ---
        self.calendar_manager = CalendarManager()
        self.alarm_manager = AlarmManager()
        self.sysadmin_manager = SysAdminManager() if SysAdminManager else None
        self.ssh_manager = SSHManager()
        self.wifi_manager = WifiManager()

        # --- Inyectar Gestores en Web Admin (Estado Compartido) ---
        if WEB_ADMIN_DISPONIBLE and self.web_server:
             self.web_server.ssh_manager = self.ssh_manager
             # Inyectar otros si es necesario, p. ej. sysadmin
             if self.sysadmin_manager:
                 self.web_server.sys_admin = self.sysadmin_manager
             if self.wifi_manager:
                 self.web_server.wifi_manager = self.wifi_manager
        
        # Visión (Opcional y deshabilitado por defecto para evitar Segfaults)
        if self.config.get('vision_enabled', False):
            try:
                from modules.vision import VisionManager
                self.vision_manager = VisionManager(self.event_queue)
                self.vision_manager.start()
            except ImportError as e:
                self.app_logger.error(f"No se pudo cargar VisionManager (cv2 missing?): {e}")
                self.vision_manager = None
            except Exception as e:
                self.app_logger.error(f"Error fatal iniciando VisionManager: {e}")
                self.vision_manager = None
        else:
            self.vision_manager = None
            self.app_logger.info("VisionManager deshabilitado por configuración (evita Segfaults).")
        self.file_manager = FileManager()
        self.cast_manager = CastManager()
        self.cast_manager.start_discovery() # Start looking for TVs/Speakers
        
        # --- Motor de IA (Gemma 2B) ---
        # self.ai_engine ya inicializado arriba
        
        # --- CEREBRO (Memoria & Aprendizaje & BD RAG) ---
        self.brain = Brain()
        self.brain.set_ai_engine(self.ai_engine) # Inject AI for consolidation
        # --- Alias de BD para FilesSkill (usando el Gestor de BD del Cerebro) ---
        # Si Brain tiene un db_manager, lo exponemos como self.db
        if self.brain and hasattr(self.brain, 'db'):
             self.db = self.brain.db
        else:
             # Fallback: intentar cargar la base de datos manualmente o mock
             self.db = None
             self.app_logger.warning("No se ha podido vincular self.db (Brain DB Manager). FilesSkill podría fallar.")
        
        # --- Gestor de Chat (Personalidad e Historial) ---
        self.chat_manager.brain = self.brain # Inject Brain for RAG
        
        self.network_manager = NetworkManager() if NetworkManager else None
        self.guard = Guard(self.event_queue) if Guard else None
        self.sherlock = Sherlock(self.event_queue) if Sherlock else None
        
        # --- MQTT (Hermanos de Red) ---
        self.mqtt_manager = MQTTManager(self.event_queue)
        self.mqtt_manager.start() # No bloqueante, falla elegantemente si no hay broker
        
        # --- Bluetooth (Respaldo) ---
        self.bluetooth_manager = BluetoothManager(self.event_queue)
        self.bluetooth_manager.start() # No bloqueante
        
        # --- Habilidades ---
        self.skills_system = SystemSkill(self)
        self.skills_network = NetworkSkill(self)
        self.skills_time = TimeDateSkill(self)
        self.skills_media = MediaSkill(self) # Ensure MediaSkill has access to core.cast_manager

        self.skills_organizer = OrganizerSkill(self)
        self.skills_ssh = SSHSkill(self)
        self.skills_files = FilesSkill(self)
        self.skills_docker = DockerSkill(self)
        self.skills_finder = FinderSkill(self)
        self.skills_visual = VisualSkill(self)
        self.skills_diagnosis = DiagnosisSkill(self)

        # --- Plugins Dinámicos (Extensiones) ---
        self.plugin_loader = PluginLoader(self)
        self.plugin_loader.load_plugins()
        
        # --- Habilidades Opcionales (Autenticación de Voz) ---
        try:
            from modules.BlueberrySkills.optional.voice_auth import VoiceAuthSkill
            self.voice_auth_skill = VoiceAuthSkill(self)
        except ImportError:
             self.voice_auth_skill = None
             app_logger.info("Habilidad Opcional 'VoiceAuth' no encontrada.")
        
        self.vlc_instance, self.player = self.setup_vlc()
        
        # --- Carga de Contenido (Recursos) ---
        self.load_resources()
        
        # --- Variables de estado ---
        self.consecutive_failures = 0
        self.morning_summary_sent_today = False
        self.waiting_for_timer_duration = False
        self.active_timer_end_time = None
        self.is_processing_command = False 
        
        # --- Variables para diálogos ---
        self.waiting_for_reminder_date = False
        self.pending_reminder_description = None
        self.waiting_for_reminder_confirmation = False
        self.pending_reminder_data = None
        
        self.waiting_for_alarm_confirmation = False
        self.pending_alarm_data = None

        self.pending_mango_command = None # Para confirmar comandos de shell potencialmente peligrosos
        
        self.waiting_for_learning = None # Almacena la clave que intentamos aprender
        self.pending_suggestion = None # Almacena la intención ambigua sobre la que estamos preguntando

        self.last_spoken_text = "" 
        self.last_intent_name = None
        self.active_listening_end_time = 0 
        self.dynamic_actions = {} # Registro para acciones de plugins 

        # --- Manejadores de Hilos ---
        self._thread_events = None
        self._thread_proactive = None
        self._thread_web = None

        self.start_background_tasks()
        
        # El bucle principal se movió a run()

    def handle_injected_command(self, data):
        """Maneja los comandos inyectados a través del Bus (CLI/Externa)."""
        self.app_logger.info(f" DEBUG: handle_injected_command called with data: {data}")
        # BusClient pasa el payload completo del mensaje: {type, data, context}
        # Extraer el texto real del comando del campo anidado 'data'
        text = data.get('data', {}).get('text')
        self.app_logger.info(f" DEBUG: Extracted text: {text}")
        if text:
            self.app_logger.info(f" Command Injected via Bus: '{text}'")
            # Simular comando detectado
            # Usar 'neo' como palabra de activación detectada para asegurar el procesamiento
            self.on_voice_command(text, 'neo')
        else:
            self.app_logger.warning(f"Received command:inject with no text: {data}")

    def _watchdog_check(self):
        """Realiza comprobaciones periódicas de salud en hilos y servicios."""
        # Registro de mantenimiento activo simple por ahora
        # En el futuro esto podría reiniciar hilos inactivos
        if self.app_logger:
            self.app_logger.debug("Watchdog: System OK")

    def run(self):
        """Bloqueo principal del servicio."""
        self.app_logger.info("NeoCore Service Running.")
        try:
            while True:
                time.sleep(10)
                self._watchdog_check()
        except KeyboardInterrupt:
            self.on_closing()

    def _check_conversational_shortcuts(self, text):
        """
        Verifica si el texto coincide con patrones simples de saludo/despedida/estado
        para evitar llamar al LLM innecesariamente.
        """
        import re
        import random
        
        text = text.lower().strip()
        nickname = self.config_manager.get('user_nickname', 'Usuario')
        
        # 1. SALUDOS
        if re.search(r'^(hola|buenas|hey|hi|qué pasa|que pasa|buenos días|buenas tardes|buenas noches)', text):
            responses = [
                f"Hola {nickname}, ¿en qué puedo ayudarte?",
                f"Buenas, {nickname}.",
                f"Aquí estoy, {nickname}.",
                f"Hola {nickname}, sistemas listos."
            ]
            return random.choice(responses)
            
        # 2. ESTADO DEL SISTEMA (Comprobación Inteligente)
        if re.search(r'(cómo|como|qué|que) (estás|estas|tal|te sientes|vamos)|reporte de estado|status', text):
            # Obtener métricas reales si es posible
            status_msg = f"Todo operativo, {nickname}."
            
            if self.sysadmin_manager:
                try:
                    cpu = self.sysadmin_manager.get_cpu_usage()
                    ram = self.sysadmin_manager.get_ram_usage()
                    temp = self.sysadmin_manager.get_cpu_temp()
                    
                    details = []
                    if cpu: details.append(f"CPU al {cpu}%")
                    if ram: details.append(f"RAM al {ram}%")
                    if temp and "N/A" not in str(temp): details.append(f"Temperatura {temp}")
                    
                    if details:
                        status_msg = f"Sistemas operativos, {nickname}. " + ", ".join(details) + "."
                except Exception as e:
                    self.app_logger.error(f"Error getting stats for greeting: {e}")
            
            return status_msg
            
        # 3. DESPEDIDAS
        if re.search(r'^(adiós|chao|hasta luego|bai|nos vemos|apágate|descansa)', text):
            responses = [
                f"Hasta luego, {nickname}.",
                f"Nos vemos, {nickname}.",
                f"Quedo a la espera, {nickname}.",
                "Cerrando canales de comunicación."
            ]
            return random.choice(responses)

        # 4. AGRADECIMIENTOS
        if re.search(r'(gracias|muchas gracias)', text):
             responses = [
                 f"De nada, {nickname}.",
                 "Para eso estoy.",
                 "Un placer."
             ]
             return random.choice(responses)
            
        return None

    def start_background_tasks(self):
        """Inicia los hilos en segundo plano."""
        # 1. Escucha de voz
        self.voice_manager.start_listening(self.intent_manager.intents)
        
        # 2. Procesamiento de eventos (hablar, acciones)
        self._thread_events = threading.Thread(target=self.process_event_queue, daemon=True, name="Events_Loop")
        self._thread_events.start()
        
        # 3. Tareas proactivas (alarmas, etc)
        self._thread_proactive = threading.Thread(target=self.proactive_update_loop, daemon=True, name="Proactive_Loop")
        self._thread_proactive.start()

        # 4. Web Admin (si está disponible)
        if WEB_ADMIN_DISPONIBLE:
            self._thread_web = threading.Thread(target=run_server, daemon=True, name="Web_Server")
            self._thread_web.start()
            app_logger.info("Servidor Web Admin iniciado en segundo plano.")

        # 5. Autorreparación
        self.health_manager.start()

    def on_vision_event(self, event_type, data):
        """Callback for vision events."""
        if event_type == "known_face":
            self.speak(f"Hola, {data}. Me alegra verte.")
        elif event_type == "unknown_face":
            self.speak("Detecto una presencia desconocida. ¿Quién eres?")

    def speak(self, text):
        """Pone un mensaje en la cola de eventos para que el Speaker lo diga."""
        # --- VISUAL FEEDBACK: AI RESPONSE ---
        if self.web_server:
            try:
                self.web_server.socketio.emit('ai:response', {'text': text}, namespace='/')
                if update_face: update_face('speaking')
            except: pass
            
        self.event_queue.put({'type': 'speak', 'text': text})
        
        # Reset face lazily (approx duration)
        if self.web_server and update_face:
             threading.Timer(len(text)/12, lambda: update_face('idle')).start()

    def log_to_inbox(self, command_text):
        """Log unrecognized command to inbox for future aliasing."""
        import os
        import json
        import time
        try:
            inbox_path = self.config_manager.get('paths', {}).get('nlu_inbox', 'data/nlu_inbox.json')
            
            # Ensure proper JSON structure
            if os.path.exists(inbox_path):
                with open(inbox_path, 'r', encoding='utf-8') as f:
                    try:
                        inbox = json.load(f)
                    except:
                        inbox = []
            else:
                inbox = []

            # Check duplication
            if not any(entry['text'] == command_text for entry in inbox):
                inbox.append({
                    'text': command_text,
                    'timestamp': time.time()
                })
                
                # Limit size
                inbox = sorted(inbox, key=lambda x: x['timestamp'], reverse=True)[:50]

                with open(inbox_path, 'w', encoding='utf-8') as f:
                    json.dump(inbox, f, indent=4, ensure_ascii=False)
                
                app_logger.info(f"Command '{command_text}' added to NLU Inbox.")
        except Exception as e:
            app_logger.error(f"Error logging to inbox: {e}")

        pass

    def load_resources(self):
        """Carga recursos estáticos (NLP, Seguridad, Visión)."""
        app_logger.info("Cargando recursos del sistema...")
        
        # 1. NLP Resources
        try:
            # Check for sentiment.json (mentioned in logs as missing)
            sentiment_path = "resources/nlp/sentiment.json"
            if not os.path.exists(sentiment_path):
                 app_logger.warning(f"Fichero {sentiment_path} no encontrado (NLP limitado).")
        except Exception as e:
            app_logger.error(f"Error loading NLP resources: {e}")

        # 2. Security Resources
        try:
            sec_path = "resources/security/attack_signatures.json"
            if not os.path.exists(sec_path):
                app_logger.warning(f"No se encontró {sec_path}. Neo Guard inactivo.")
        except Exception as e:
            app_logger.error(f"Error loading Security resources: {e}")

        # 3. Vision Resources
        if self.vision_manager:
            try:
                # Si VisionManager tuviera un método de carga explícito, lo llamaríamos aquí.
                # Por ahora asumimos que inicia en su propio hilo.
                pass
            except Exception as e:
                app_logger.error(f"Error loading Vision resources: {e}")

    def setup_vlc(self):
        """Inicializa la instancia de VLC para reproducción de radio."""
        if vlc:
            instance = vlc.Instance()
            return instance, instance.media_player_new()
        return None, None

    def on_closing(self):
        """Limpieza al cerrar."""
        app_logger.info("Cerrando Neo Core...")
        self.voice_manager.stop_listening()
        if self.player:
            self.player.stop()
        if self.vision_manager:
            self.vision_manager.stop()
        if self.mqtt_manager:
            self.mqtt_manager.stop()
        if self.bluetooth_manager:
            self.bluetooth_manager.stop()
        if self.health_manager:
            self.health_manager.stop()
        os._exit(0)

    def on_voice_command(self, command, wake_word, audio_buffer=None):
        """Callback cuando VoiceManager detecta voz."""
        app_logger.info(f" VOICE RECEIVED: '{command}' (WW: {wake_word})")
        command_lower = command.lower()
        
        # --- VISUAL FEEDBACK: STT RESULT ---
        # --- VISUAL FEEDBACK: STT RESULT ---
        if self.web_server:
             try:
                 app_logger.info(f"Emitting STT Result: {command}")
                 self.web_server.socketio.emit('stt:result', {'text': command}, namespace='/')
             except Exception as e:
                 app_logger.error(f"Failed to emit STT result: {e}")
        
        # Check Active Listening Window
        is_active_listening = time.time() < self.active_listening_end_time
        
        # Wake Word Check OR Active Listening
        # FORCE ENABLE: Bypassing strict wake word check to unblock user
        if True: # is_active_listening or wake_word in command_lower:
             if update_face: update_face('thinking')
             self.is_processing_command = True
             self.voice_manager.set_processing(True)
             
             # --- Filler Word (Zero Latency Feel) ---
             # Play a random "thinking" sound immediately
             self.speaker.play_random_filler()
             
             # Remove wake word from command if present
             command_clean = command_lower.replace(wake_word, "").strip() if wake_word in command_lower else command_lower
             
             # Extend active listening for follow-up
             self.active_listening_end_time = time.time() + 8
             
             self.handle_command(command_clean, audio_buffer)
             
             self.voice_manager.set_processing(False)

    def _handle_mango_logic(self, command_text):
        """Procesa comandos de sistema usando MANGO (T5). Retorna True si manejó el comando."""
        # --- Context Injection (Simplified) ---
        try:
            raw_files = os.listdir('.')
        except:
            raw_files = []
            
        ignored = {'.git', '__pycache__', 'venv', 'env', '.config', 'node_modules', '.gemini'}
        filtered_files = [
            f for f in raw_files 
            if f not in ignored and not f.startswith('.') 
            and not f.endswith(('.pyc', '.Log'))
        ]
        
        # Truncate if too many files (Top 25)
        if len(filtered_files) > 25:
            filtered_files = filtered_files[:25] + ['...']
            
        context_str = str(filtered_files)
        mango_prompt = f"Contexto: {context_str} | Instrucción: {command_text}"
        
        self.app_logger.info(f"MANGO Prompt: '{mango_prompt}'")
        
        # --- SELF-CORRECTION LOOP (DISABLED) ---
        max_retries = 0 # Disabled per user request
        
        # REPAIR_PROMPTS = [
        #     "El comando '{cmd}' falló con error: '{err}'. Corrígelo.",
        #     "Error ejecutando '{cmd}': '{err}'. Dame la solución.",
        #     "Fallo: '{err}' al ejecutar '{cmd}'. Arréglalo.",
        #     "Corrige el comando '{cmd}' dado este error: '{err}'",
        #     "He recibido este error: '{err}' tras lanzar '{cmd}'. ¿Qué hago?",
        #     "Intento hacer '{cmd}' pero sale '{err}'.",
        #     "Ayuda, '{cmd}' no funciona. Error: '{err}'.",
        #     "Repara este comando: '{cmd}'. El error es '{err}'.",
        #     "Salida de error: '{err}' para el comando '{cmd}'.",
        #     "Fix: '{cmd}' -> '{err}'."
        # ]
        
        attempt = 0
        command_to_run = None
        
        # First attempt
        mango_cmd, mango_conf = self.mango_manager.infer(mango_prompt)
        
        if mango_cmd and mango_conf > 0.85:
            command_to_run = mango_cmd
        
        # GIT Security Filter
        if command_to_run and command_to_run.strip().startswith('git'):
            cleaned_cmd = " ".join(command_to_run.strip().split())
            if not cleaned_cmd.startswith('git push'):
                self.speak(f"Comando git bloqueado por seguridad: {command_to_run}")
                self.app_logger.warning(f"BLOCKED Git Command: {command_to_run}")
                return True # Handled (Blocked)

        if command_to_run:
            while attempt <= max_retries:
                 self.app_logger.info(f"MANGO Exec Attempt {attempt+1}: {command_to_run}")
                 
                 # 0. Flag Validation
                 is_valid_cmd, val_msg = self.sysadmin_manager.validate_command_flags(command_to_run)
                 
                 if not is_valid_cmd:
                     self.app_logger.warning(f"MANGO Validation Failed: {val_msg}")
                     success = False
                     output = f"Command validation failed: {val_msg}"
                 else:
                     # 1. Risk Analysis
                     risk_level = self.sysadmin_manager.analyze_command_risk(command_to_run)
                     self.app_logger.info(f"Risk Level for '{command_to_run}': {risk_level.upper()}")
                     
                     should_execute = False
                     
                     if risk_level == 'safe':
                         if attempt == 0: self.speak(f"Ejecutando: {command_to_run}")
                         should_execute = True
                         
                     elif risk_level == 'caution':
                         self.pending_mango_command = command_to_run
                         self.speak(f"He generado: {command_to_run}. ¿Ejecuto?")
                         return True # Handled (Waiting confirm)
                         
                     elif risk_level == 'danger':
                         self.pending_mango_command = command_to_run
                         self.speak(f"¡Atención! {command_to_run} puede ser destructivo. ¿Seguro?")
                         return True # Handled (Waiting confirm)

                     if should_execute:
                         success, output = self.sysadmin_manager.run_command(command_to_run)
                     else:
                         return True

                 # Result Handling
                 if success:
                     self.handle_action_result_with_chat(command_text, output)
                     return True
                 else:
                     error_msg = output
                     self.app_logger.warning(f"MANGO Command Failed: {error_msg}")
                     
                     if attempt < max_retries:
                         attempt += 1
                         
                         # Dynamic Repair Prompt
                         template = random.choice(REPAIR_PROMPTS)
                         repair_prompt = template.format(cmd=command_to_run, err=error_msg)
                         
                         self.app_logger.info(f"MANGO Repair Prompt ({attempt}/{max_retries}): {repair_prompt}")
                         
                         fixed_cmd, fixed_conf = self.mango_manager.infer(repair_prompt)
                         if fixed_cmd:
                             command_to_run = fixed_cmd
                             self.speak(f"Error detectado. Corrigiendo...")
                             continue
                         else:
                             self.speak("No he podido corregir el error.")
                             break
                     else:
                         self.speak(f"No he podido ejecutarlo. Error: {error_msg}")
                         return True
        return False

    def handle_command(self, command_text, audio_buffer=None):
        """Procesa el comando de texto."""
        try:
                # --- VOICE AUTH CHECK ---
                current_user = "unknown"
                if self.voice_auth_skill and self.voice_auth_skill.enabled and audio_buffer is not None:
                     current_user, confidence = self.voice_auth_skill.identify_speaker(audio_buffer)
                     app_logger.info(f" Speaker identified as: {current_user} (Conf: {confidence:.2f})")
                
                # --- FIND COMMAND RESULTS INTERCEPTION ---
                cmd_lower = command_text.lower()
                if self.last_find_results and any(kw in cmd_lower for kw in ['muéstra', 'muestra', 'enseña', 'dime cuales', 'dime cuáles', 'léelos', 'lee los archivos']):
                    results = self.last_find_results
                    self.last_find_results = None  # Clear after reading
                    self.speak(f"Estos son los archivos: {results}")
                    return

                # Diálogos activos
                if self.waiting_for_timer_duration:
                    self.handle_timer_duration_response(command_text)
                    return
                if self.waiting_for_reminder_date:
                    self.handle_reminder_date_response(command_text)
                    return
                if self.waiting_for_reminder_confirmation:
                    self.handle_reminder_confirmation(command_text)
                    return
                if self.waiting_for_alarm_confirmation:
                    self.handle_alarm_confirmation(command_text)
                    return

                if self.pending_mango_command:
                    self.handle_mango_confirmation(command_text)
                    return

                if self.waiting_for_learning:
                    self.handle_learning_response(command_text)
                    return

                if not command_text:
                    return

                # --- 0. VOICE ENROLLMENT (Priority High) ---
                import re
                match_learn = re.search(r"(?:soy|me llamo|mi nombre es)\s+(.+)", command_text, re.IGNORECASE)
                if match_learn:
                    name = match_learn.group(1).strip()
                    
                    # Voice Enrollment
                    if self.voice_auth_skill and self.voice_auth_skill.enabled and audio_buffer is not None:
                        self.speak(f"Hola {name}. Procesando tu voz para el sistema de seguridad...")
                        success, msg = self.voice_auth_skill.enroll_user(name, audio_buffer)
                        self.speak(msg)
                        return

                    # Face Enrollment (Legacy)
                    if self.vision_manager:
                         self.speak(f"Hola {name}. Mírame a la cámara mientras aprendo tu cara...")
                         # Run in background to not block
                         def learn_task():
                              success, msg = self.vision_manager.learn_user(name)
                              self.speak(msg)
                         threading.Thread(target=learn_task).start()
                         return
                    else:
                        if not self.voice_auth_skill:
                             self.speak("Lo siento, mis sistemas biométricos no están activos.")
                        return

                # --- 1. EJECUCIÓN DEL COMANDO (Prioridad 1) ---
                # Intentar ejecutar a través del mapa de acciones
                result = self.execute_command(command_text)
                if result:
                    # Comprobar si result es un stream de texto (generator)
                    if hasattr(result, '__iter__') and not isinstance(result, (str, bytes, dict)):
                        # Respuesta en streaming
                        try:
                             buffer = ""
                             for chunk in result:
                                 if chunk:
                                     buffer += chunk
                                     # Heurística: hablar en los límites de oraciones
                                     if any(punct in buffer for punct in ['.', '!', '?', '\n']):
                                          import re
                                          # Dividir manteniendo delimitadores
                                          parts = re.split(r'([.!?\n])', buffer)
                                          
                                          if len(parts) > 1:
                                              while len(parts) >= 2:
                                                  sentence = parts.pop(0) + parts.pop(0)
                                                  sentence = sentence.strip()
                                                  if sentence:
                                                      self.speak(sentence)
                                                      
                                              buffer = "".join(parts)
                             # Hablar lo restante
                             if buffer.strip():
                                 self.speak(buffer)
                        except Exception as e:
                              app_logger.error(f"Error streaming action result: {e}")
                              self.speak("He hecho lo que pediste, pero me he liado al contártelo.")
                    return

                # Comprobar "Soy {name}" o "Aprende mi cara"
                import re
                match_learn = re.search(r"(?:soy|me llamo|mi nombre es)\s+(.+)", command_text, re.IGNORECASE)
                if match_learn:
                    name = match_learn.group(1).strip()
                    # Filtrar rellenos puramente conversacionales si es necesario, pero por ahora tomar la captura
                    if self.vision_manager:
                        self.speak(f"Hola {name}. Mírame a la cámara mientras aprendo tu cara...")
                        # Ejecutar en segundo plano para no bloquear
                        def learn_task():
                             success, msg = self.vision_manager.learn_user(name)
                             self.speak(msg)
                        threading.Thread(target=learn_task).start()
                        return
                    else:
                        self.speak("Lo siento, mis sistemas de visión no están activos.")
                        return


                # --- ATAJOS CONVERSACIONALES (Antes del Router) ---
                # Comprobar si esto es una consulta simple de saludo/despedida/estado
                # Combinar _check_conversational_shortcuts() con detección de intenciones
                shortcut_response = self._check_conversational_shortcuts(command_text)
                if shortcut_response:
                    # Es un saludo/despedida/agradecimiento - responder directamente
                    self.speak(shortcut_response)
                    return
                
                # También comprobar el gestor de intenciones para saludo/despedida para capturar variaciones
                best_intent = self.intent_manager.find_best_intent(command_text)
                if best_intent and best_intent.get('name') in ['saludo', 'despedida', 'agradecimiento']:
                    # Saludo/despedida de alta o media confianza del gestor de intenciones
                    confidence = float(best_intent.get('confidence', 0))
                    if confidence >= 80:  # Alta confianza
                        # Usar respuesta de atajo si está disponible, de lo contrario genérica
                        shortcut_response = self._check_conversational_shortcuts(command_text)
                        if shortcut_response:
                            self.speak(shortcut_response)
                        else:
                            # Respaldo genérico
                            if best_intent['name'] == 'saludo':
                                nickname = self.config_manager.get('user_nickname', 'Usuario')
                                self.speak(f"Hola {nickname}, ¿en qué puedo ayudarte?")
                            elif best_intent['name'] == 'despedida':
                                self.speak("Hasta luego.")
                            else:
                                self.speak("De nada.")
                        return

                # --- 1. NUEVA ARQUITECTURA DE ENRUTADOR ---
                # "Capa de Normalización"
                command_text = self.text_normalizer.normalize(command_text)

                # "Capa de Clasificación (Router)"
                router_label, router_score = self.decision_router.predict(command_text)
                
                app_logger.info(f"ROUTER Decision: label='{router_label}', score={router_score:.3f}")
                
                # Emitir decisión del router a la UI/CLI (incluso para nulos)
                if self.web_server:
                    try:
                        self.web_server.socketio.emit('router:decision', {
                            'category': router_label if router_label else 'null', 
                            'score': router_score if router_score else 0.0,
                            'command': command_text
                        }, namespace='/')
                    except Exception as e:
                        app_logger.debug(f"Failed to emit router decision: {e}")
                
                # Manejando categoría 'null' o 'gemma' - Intentar respaldo de intenciones primero
                if router_label in ["null", "gemma", None]:
                    # --- RESPALDO DE INTENCIONES ---
                    # Intentar hacer coincidir con intenciones/acciones registradas antes de rendirse
                    app_logger.info(f"Router returned {router_label}. Trying intent fallback...")
                    
                    fallback_result = self.execute_command(command_text)
                    if fallback_result:
                        # ¡Se encontró una intención coincidente!
                        app_logger.info(f"[OK] Intent fallback succeeded for '{command_text}'")
                        self.speak(fallback_result if isinstance(fallback_result, str) else "Hecho")
                        return
                    
                    # Aún no se encuentra - manejar como conversacional
                    if router_label == "gemma":
                        # --- COMPARADOR DE RUTA RÁPIDA ---
                        shortcut_response = self._check_conversational_shortcuts(command_text)
                        if shortcut_response:
                            self.speak(shortcut_response)
                            return

                        # Respaldo a consultas de chat/generales
                        final_response = self.chat_manager.get_response(command_text)
                        self.speak(final_response)
                        return
                    else:
                        # null - realmente no entendió
                        self.speak("No he entendido el comando.")
                        app_logger.info("Router returned NULL and no intent matched.")
                        return
                
                # Categorías Técnicas (malbec, syrah, tempranillo, pinot, chandonay, cabernet)
                else:
                    try:
                        # "Capa de Ejecución": ONNX Runner
                        # INYECTAR CONTEXTO basado en el tipo de enrutador

                        # --- Estrategia de inyección de contexto ---
                        # Modelos de red (syrah/cabernet): SÓLO alias de red
                        # Otros modelos: Contexto completo del sistema de archivos (pwd + ls)
                        # =========================
                        # MANEJADOR DE CATEGORÍA SEGURA
                        # =========================
                        if router_label == "secure":
                            app_logger.info(f" SECURE category detected. Using SecureIntentMatcher...")
                            
                            if not self.secure_intent_matcher:
                                self.speak("El sistema de seguridad no está disponible.")
                                return
                            
                            # Intentar match con SecureIntentMatcher
                            match_result = self.secure_intent_matcher.match_intent(command_text)
                            
                            if match_result:
                                cmd, context, category, is_python = match_result
                                
                                app_logger.info(f" Intent matched: category={category}, context={context}")
                                
                                # Si es función Python (SecuritySkill)
                                if is_python:
                                    try:
                                        # Parsear: SecuritySkill.method()
                                        if 'SecuritySkill.' in cmd:
                                            method_name = cmd.split('SecuritySkill.')[1].replace('()', '')
                                            
                                            # Ejecutar método del SecuritySkill
                                            if hasattr(self, 'skills_manager') and self.skills_manager:
                                                from modules.BlueberrySkills.security import SecuritySkill
                                                # Crear instancia temporal si no existe
                                                skill = SecuritySkill(self)
                                                if hasattr(skill, method_name):
                                                    method = getattr(skill, method_name)
                                                    method(command_text, "")
                                                    return
                                        
                                        self.speak("Función de seguridad no disponible.")
                                        return
                                        
                                    except Exception as e:
                                        app_logger.error(f"Error ejecutando función Python: {e}")
                                        self.speak("Error ejecutando comando de seguridad.")
                                        return
                                
                                # Si es comando shell
                                else:
                                    # Comandos destructivos requieren confirmación
                                    destructive_keywords = ['rm', 'delete', 'ban', 'block', 'kill']
                                    needs_confirmation = any(kw in cmd.lower() for kw in destructive_keywords)
                                    
                                    if needs_confirmation:
                                        # Guardar para confirmación
                                        self.pending_mango_command = cmd
                                        self.speak(f"Voy a ejecutar: {cmd}. ¿Confirmas?")
                                        return
                                    else:
                                        # Ejecutar directo
                                        success, output = self.sysadmin_manager.run_command(cmd)
                                        
                                        if success:
                                            # Filtrar output largo
                                            if len(output) > 500:
                                                lines = output.split('\n')
                                                summary = '\n'.join(lines[:10])
                                                self.speak(f"Comando ejecutado. Primeras líneas: {summary}")
                                            else:
                                                self.speak(f"Resultado: {output}")
                                        else:
                                            self.speak(f"Error: {output}")
                                        
                                        return
                            else:
                                # No hay coincidencia en SecureIntentMatcher
                                app_logger.warning(f" No intent match for secure command: {command_text}")
                                self.speak("No reconozco ese comando de seguridad. ¿Puedes reformularlo?")
                                return
                        
                        # =========================
                        # CATEGORÍAS DE RED/SISTEMA
                        # =========================
                        elif router_label in ["syrah", "syrach", "cabernet"]:
                            # Modelos de red: Sólo alias SSH/red
                            fs_context = "[]"
                            try:
                                server_entries = []
                                if self.ssh_manager and hasattr(self.ssh_manager, 'servers'):
                                    for alias, data in self.ssh_manager.servers.items():
                                        host = data.get('host', 'unknown')
                                        server_entries.append(f"'{alias}={host}'")
                                
                                # Inyectar network_aliases desde configuración
                                if self.config_manager:
                                    network_aliases = self.config_manager.get('network_aliases', {})
                                    for alias, ip in network_aliases.items():
                                        server_entries.append(f"'{alias}={ip}'")

                                if server_entries:
                                    network_context_str = ", ".join(server_entries)
                                    fs_context = f"[{network_context_str}]"
                            except Exception as e:
                                self.app_logger.error(f"Error building network context: {e}")
                        else:
                            # Otros modelos obtienen contexto completo del sistema de archivos
                            fs_context = self._get_filesystem_context()
                        # --------------------------------------------------------

                        final_prompt = f"Contexto: {fs_context} | Instrucción: {command_text}"
                        self.app_logger.info(f"ONNX Prompt: {final_prompt}")

                        generated_command = self.onnx_runner.generate_command(final_prompt, router_label)
                        self.app_logger.info(f" ONNX Generated Command: {generated_command}")
                        
                        if not generated_command:
                            self.speak("El modelo no generó ningún comando.")
                            return

                    except FileNotFoundError as e:
                        # "Fallo elegante": Falta modelo
                        self.app_logger.error(f"Missing Model for {router_label}: {e}")
                        self.speak(f"No encuentro el modelo especializado para {router_label}. Continuando...")
                        return # Restart loop
                        
                    except Exception as e:
                         self.app_logger.error(f"Error in ONNX Runner: {e}")
                         self.speak("Hubo un error al ejecutar el modelo especializado.")
                         return

                # "Capa de Post-Procesamiento"
                if generated_command:
                    # 1. Lógica de Contenido Visual
                    visual_tokens = ["cat ", "gedit ", "nano ", "vim ", "ls ", "tree", "top", "htop", "less ", "more "]
                    is_visual = any(token in generated_command for token in visual_tokens)
                    
                    if is_visual and self.web_server: 
                         self.app_logger.info("Visual command detected. Emitting CLI event.")
                    
                    # 2. Validar y Ejecutar vía SysAdminManager
                    if self.sysadmin_manager:
                        is_valid, val_msg = self.sysadmin_manager.validate_command_flags(generated_command)
                        if not is_valid:
                             self.speak(f"Comando inválido: {val_msg}")
                             return
                        
                        success, output = self.sysadmin_manager.run_command(generated_command)
                        
                        # "Capa de Finalizacion"
                        if success:
                            if is_visual and self.web_server:
                                 try:
                                     # Emitir salida a consola web
                                     self.web_server.socketio.emit('cli:output', {'cmd': generated_command, 'output': output}, namespace='/')
                                 except: pass
                            
                            # Heurística: Si la salida es corta/legible, háblala.
                            if generated_command.strip().startswith('find'):
                                lines_found = len([line for line in output.splitlines() if line.strip()])
                                if lines_found == 0:
                                    self.speak("No he encontrado ningún archivo.")
                                    self.last_find_results = None
                                elif lines_found == 1:
                                    self.speak("He encontrado 1 archivo.")
                                    self.last_find_results = output
                                else:
                                    self.speak(f"He encontrado {lines_found} archivos.")
                                    self.last_find_results = output
                            elif len(output) < 200:
                                self.speak(f"Hecho: {output}")
                            else:
                                self.speak("Comando ejecutado.")


                        else:
                            self.speak(f"Error ejecutando comando: {output}")
                    else:
                         self.speak("Gestor de sistema no disponible.")
                
                return

                # --- Enrutador de palabras clave (Llamada de función legada) ---
                router_result = self.keyword_router.process(command_text)
                if router_result:
                    app_logger.info(f"Keyword Router Action Result: {router_result}")
                    # Usar Gemma para generar una respuesta natural basada en el resultado
                    final_response = self.chat_manager.get_response(command_text, system_context=router_result)
                    self.speak(final_response)
                    return

                # --- CEREBRO: Comprobar alias ---
                if self.brain:
                    alias_command = self.brain.process_input(command_text)
                    if alias_command:
                        app_logger.info(f"Alias detectado: '{command_text}' -> '{alias_command}'")
                        command_text = alias_command

                app_logger.info(f"Comando: '{command_text}'. Buscando intención...")

                # --- Flujo de sugerencias / Aprendizaje ---
                if self.pending_suggestion:
                    if command_text.lower() in ['sí', 'si', 'claro', 'yes', 'correcto', 'eso es']:
                        # ¡Usuario confirmado!
                        original_cmd = self.pending_suggestion['original']
                        target_intent = self.pending_suggestion['intent']
                        
                        # 1. Aprender Alias
                        if self.brain:
                            # Usar el primer activador como comando canónico
                            canonical = target_intent['triggers'][0]
                            self.brain.learn_alias(original_cmd, canonical)
                            self.speak(f"Entendido. Aprendo que '{original_cmd}' es '{canonical}'.")
                        
                        # 2. Ejecutar Acción
                        self.pending_suggestion = None
                        best_intent = target_intent # Proceder a ejecutar
                        # Pasar al bloque de ejecución de abajo...
                    
                    elif command_text.lower() in ['no', 'negativo', 'cancelar']:
                        self.speak("Vale, perdona. ¿Qué querías decir?")
                        self.pending_suggestion = None
                        return
                    else:
                  
                        self.pending_suggestion = None
                        # Pasar al procesamiento normal

                # --- 3. COMPROBACIÓN DE AMBIGÜEDAD (Intenciones Legadas) ---
                # Si estamos aquí, significa:
                # 1. La intención NO era de Alta Confianza.
                # 2. Mango NO era de Alta Confianza (o falló).
                
                if best_intent:
                    # Coincidencia Baja/Media -> Preguntar al usuario
                    self.pending_suggestion = {
                        'original': command_text,
                        'intent': best_intent
                    }
                    suggestion_text = best_intent['triggers'][0]
                    self.speak(f"No estoy seguro. ¿Te refieres a '{suggestion_text}'?")
                    return
                
                # --- Respaldo de MANGO T5 (Comandos de Sistema de Baja Confianza) ---
                # Si IntentManager también falló, comprobar Mango de nuevo con un umbral más bajo (ej. 0.6)
                # Esto capta cosas que parecen comandos de sistema pero Mango no estaba súper seguro.
                if mango_cmd and mango_conf > 0.6: 
                     # Misma lógica anterior pero tratándolo efectivamente como "Último recurso" antes del Chat
                     if mango_cmd.startswith("echo ") or mango_cmd == "ls" or mango_cmd.startswith("ls "):
                         self.speak(f"Ejecutando: {mango_cmd}")
                         success, output = self.sysadmin_manager.run_command(mango_cmd)
                         result_text = output if success else f"Error: {output}"
                         self.handle_action_result_with_chat(command_text, result_text)
                         return
                     else:
                         self.pending_mango_command = mango_cmd
                         self.speak(f"He generado el comando: {mango_cmd}. ¿Ejecuto?")
                         return

                # Si no es un comando, loguear para aprendizaje y hablar con Gemma
                self.log_to_inbox(command_text)
                self.handle_unrecognized_command(command_text)
                


        except Exception as e:
            app_logger.error(f"Error CRÍTICO en handle_command: {e}", exc_info=True)
            self.speak("Ha ocurrido un error interno procesando tu comando.")

        finally:
            if not self.speaker.is_busy:
                self.is_processing_command = False
                if update_face: update_face('idle')

    def handle_action_result_with_chat(self, command_text, result_text):
        """Procesa el resultado de una acción y decide cómo responder (Smart Filtering)."""
        app_logger.info(f"Procesando resultado de acción. Longitud: {len(result_text)}")

        # 1. Filtro para 'ls' / listar archivos
        if "ls " in command_text.lower() or "listar" in command_text.lower() or "lista" in command_text.lower():
            # Intentar contar líneas
            lines = result_text.strip().split('\n')
            num_files = len(lines)
            if num_files > 5:
                # Resumen
                response = f"He encontrado {num_files} elementos en el directorio."
                if num_files < 15:
                    # Si son pocos (pero > 5), leer solo los nombres si son cortos
                    response += " Los primeros son: " + ", ".join(lines[:3])
                self.speak(response)
                return

        # 2. Filtro para Logs
        if "log" in command_text.lower():
            lines = result_text.strip().split('\n')
            if len(lines) > 3:
                last_lines = "\n".join(lines[-2:]) # Leer las últimas 2
                self.speak(f"El log es largo. Aquí tienes lo último: {last_lines}")
                return

        # 3. Filtro Genérico por Longitud
        if len(result_text) > 400:
            # Guardar en archivo
            filename = f"resultado_{int(time.time())}.txt"
            filepath = os.path.join(os.getcwd(), filename)
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(result_text)
                self.speak(f"La salida es muy larga ({len(result_text)} caracteres). La he guardado en el archivo {filename}.")
            except Exception as e:
                self.speak("La salida es muy larga y no he podido guardarla.")
            return

        # 4. Salida Corta -> Dejar que Gemma lo explique o leerlo directo
        # Si es muy corto, leer directo
        if len(result_text) < 150:
            self.speak(result_text)
        else:
            # Si es medio, dejar que Gemma resuma
            try:
                stream = self.chat_manager.get_response_stream(command_text, system_context=result_text)
                buffer = ""
                for chunk in stream:
                    buffer += chunk
                    import re
                    parts = re.split(r'([.!?\n])', buffer)
                    if len(parts) > 1:
                        while len(parts) >= 2:
                            sentence = parts.pop(0) + parts.pop(0)
                            sentence = sentence.strip()
                            if sentence:
                                self.speak(sentence)
                        buffer = "".join(parts)
                if buffer.strip():
                    self.speak(buffer)
            except Exception as e:
                app_logger.error(f"Error streaming action result: {e}")
                self.speak("He ejecutado el comando.")

    def handle_unrecognized_command(self, command_text):
        """Usa Gemma para responder en Streaming."""
        try:
            stream = self.chat_manager.get_response_stream(command_text)
            
            buffer = ""
            self.consecutive_failures = 0
            
            for chunk in stream:
                buffer += chunk
                
                # Comprobar delimitadores de oraciones
                # Heurística simple: dividir por puntuación
                import re
                # Dividir manteniendo delimitadores
                parts = re.split(r'([.!?\n])', buffer)
                
                if len(parts) > 1:
                    # Tenemos al menos una oración completa
                    # partes = ['Oración 1', '.', 'Oración 2', '?', 'Parcial']
                    
                    # Procesar pares (texto + delimitador)
                    while len(parts) >= 2:
                        sentence = parts.pop(0) + parts.pop(0)
                        sentence = sentence.strip()
                        if sentence:
                            app_logger.info(f"Stream Sentence: {sentence}")
                            self.speak(sentence)
                    
                    # La parte restante es el nuevo buffer
                    buffer = "".join(parts)
            
            # Hablar el buffer restante
            if buffer.strip():
                app_logger.info(f"Stream Final: {buffer}")
                self.speak(buffer)
                
        except Exception as e:
            app_logger.error(f"Error en Streaming: {e}")
            self.speak("Lo siento, me he liado.")

    def process_event_queue(self):
        """Procesa eventos de la cola (principalmente hablar)."""
        while True:
            try:
                action = self.event_queue.get()
                action_type = action.get('type')

                if action_type == 'speak':
                    text_to_speak = action.get('text')
                    app_logger.info(f"Procesando evento SPEAK: {text_to_speak}")
                    self.is_processing_command = True
                    
                    # Emitir respuesta IA a la UI
                    if self.web_server:
                        try:
                            self.web_server.socketio.emit('ai:response', {'text': text_to_speak}, namespace='/')
                        except Exception as e:
                             app_logger.warning(f"Error emitting ai:response: {e}")

                    if update_face: update_face('speaking')
                    self.last_spoken_text = text_to_speak
                    self.speaker.speak(text_to_speak)
                elif action_type == 'speaker_status':
                    if action['status'] == 'idle':
                        self.is_processing_command = False
                        # Activar ventana de escucha activa (8 segundos)
                        self.active_listening_end_time = time.time() + 8
                        if update_face: update_face('listening') # Mantener cara de escucha
                        app_logger.info("Ventana de escucha activa iniciada (8s).") 
                
                elif action_type == 'mqtt_alert':
                    # Alerta crítica de un agente
                    agent = action.get('agent')
                    msg = action.get('msg')
                    self.speak(f"Alerta de {agent}: {msg}")
                    if update_face: update_face('alert', {'msg': msg})

                elif action_type == 'mqtt_telemetry':
                    # Datos de telemetría -> Actualizar UI (Pop-up)
                    agent = action.get('agent')
                    data = action.get('data')
                    # Solo mostramos pop-up si es un mensaje de "estado" o cada X tiempo
                    # Para cumplir el requisito de "aviso pop up deslizante avisando de la conexion",
                    # podemos asumir que si recibimos telemetría, está conectado.
                    # Delegamos a la UI la lógica de no spammear.
                    if update_face: update_face('notification', {'title': f"Agente {agent}", 'body': "Conectado/Datos recibidos"}) 
            except Exception as e:
                app_logger.error(f"Error procesando cola de eventos: {e}")
            finally:
                self.event_queue.task_done()

    def proactive_update_loop(self):
        """Bucle para tareas periódicas (alarmas, recordatorios, resumen matutino)."""
        last_hourly_check = time.time()

        while True:
            self._check_frequent_tasks()

            now = datetime.now()
            current_time = time.time()

            if now.hour == 9 and not self.morning_summary_sent_today:
                self.give_morning_summary() 
                self.morning_summary_sent_today = True
            elif now.hour != 9: 
                self.morning_summary_sent_today = False

            if current_time - last_hourly_check > 3600: 
                self._check_hourly_tasks()
                last_hourly_check = current_time
            
            # Dormir para evitar el sobreuso de CPU
            time.sleep(0.5)  # Comprobar cada 500ms en lugar de bucle continuo
            
            # Tareas horarias (limpieza, mantenimiento)
            if int(time.time()) % 3600 == 0:
                # self.clean_tts_cache() # Asumiendo que esta función existe en otro lugar o fue eliminada
                if self.brain:
                    self.brain.consolidate_memory() # Intentar consolidar la memoria de ayer

            # Restablecer la cara si expiró la escucha activa
            if self.active_listening_end_time > 0 and time.time() > self.active_listening_end_time:
                if update_face: update_face('idle')
                self.active_listening_end_time = 0

            # Perro guardián: comprobar si el hilo de voz está vivo
            if self.voice_manager.is_listening:
                 if not hasattr(self.voice_manager, 'listener_thread') or not self.voice_manager.listener_thread.is_alive():
                     self.app_logger.warning(" Watchdog: Voice Thread Died! Restarting...")
                     self.voice_manager.stop_listening() # Restablecer banderas
                     time.sleep(1)
                     self.voice_manager.start_listening(self.intent_manager.intents)
                     self.app_logger.info(" Watchdog: Voice Thread Restarted.")

            time.sleep(1) # Reducido para mejor capacidad de respuesta

    def _check_frequent_tasks(self):
        """Verifica alarmas y temporizadores."""
        alarm_actions = self.alarm_manager.check_alarms(datetime.now())
        for action in alarm_actions:
            self.event_queue.put(action)
        
        if self.active_timer_end_time and datetime.now() >= self.active_timer_end_time:
            self.event_queue.put({'type': 'speak', 'text': "¡El tiempo del temporizador ha terminado!"})
            self.active_timer_end_time = None

    def check_calendar_events(self):
            """Verifica eventos del calendario para hoy."""
            today_str = date.today().isoformat()
            events_today = self.calendar_manager.get_events_for_day(date.today().year, date.today().month, date.today().day)
            for event in events_today:
                if event['date'] == today_str:
                    msg = f"Te recuerdo que hoy a las {event['time']} tienes una cita: {event['description']}"
                    self.event_queue.put({'type': 'speak', 'text': msg})

    def execute_action(self, name, cmd, params, resp, intent_name=None):
        """Ejecuta la función asociada a una intención."""
        
        # Mapa de acciones simplificado
        action_map = {
            # --- Sistema y Admin ---
            "accion_apagar": self.skills_system.apagar,
            "check_system_status": self.skills_system.check_status,
            "queja_factura": self.skills_system.queja_factura,
            "diagnostico": self.skills_system.diagnostico,
            "system_restart_service": self.skills_system.restart_service,
            "system_update": self.skills_system.update_system,
            "system_find_file": self.skills_system.find_file,
            "realizar_diagnostico": self.skills_diagnosis.realizar_diagnostico,
            
            # --- Hora y Fecha ---
            "decir_hora_actual": self.skills_time.decir_hora_fecha,
            "decir_fecha_actual": self.skills_time.decir_hora_fecha,
            "decir_dia_semana": self.skills_time.decir_dia_semana,
            
            # --- Organizador (Calendario, Alarmas, Temporizadores) ---
            "consultar_citas": self.skills_organizer.consultar_citas,
            "crear_recordatorio_voz": self.skills_organizer.crear_recordatorio_voz, 
            "crear_alarma_voz": self.skills_organizer.crear_alarma_voz, 
            "consultar_recordatorios_dia": self.skills_organizer.consultar_recordatorios_dia, 
            "consultar_alarmas": self.skills_organizer.consultar_alarmas, 
            "iniciar_dialogo_temporizador": self.skills_organizer.iniciar_dialogo_temporizador, 
            "consultar_temporizador": self.skills_organizer.consultar_temporizador, 
            "crear_temporizador_directo": self.skills_organizer.crear_temporizador_directo,
            
            # --- Medios & Cast ---
            "controlar_radio": self.skills_media.controlar_radio,
            "detener_radio": self.skills_media.detener_radio, 
            "cast_video": self.skills_media.cast_video,
            "stop_cast": self.skills_media.stop_cast,
            
            # --- Contenido & Diversión (Migrado a Plugin) ---
            # "contar_chiste": self.skills_content.contar_contenido_aleatorio, 
            # "decir_frase_celebre": self.skills_content.decir_frase_celebre,
            # "contar_dato_curioso": self.skills_content.contar_contenido_aleatorio,
            # "aprender_alias": self.skills_content.aprender_alias,
            # "aprender_dato": self.skills_content.aprender_dato,
            # "consultar_dato": self.skills_content.consultar_dato,
            
            # --- Red & SSH & Archivos ---
            "network_scan": self.skills_network.scan,
            "network_ping": self.skills_network.ping,
            "network_whois": self.skills_network.whois,
            "public_ip": self.skills_network.public_ip,
            "check_service": self.skills_system.check_service,
            "disk_usage": self.skills_system.disk_usage,
            "escalar_cluster": self.skills_network.escalar_cluster,
            "ssh_connect": self.skills_ssh.connect,
            "ssh_execute": self.skills_ssh.execute,
            "ssh_disconnect": self.skills_ssh.disconnect,
            "buscar_archivo": self.skills_files.search_file,
            "buscar_archivo": self.skills_files.search_file,
            "leer_archivo": self.skills_files.read_file,
            
            # Habilidad Visual - Visor de archivos inteligente
            "visual_show_file": self.skills_visual.show_file,
            "visual_close": self.skills_visual.close_viewer,
            
            # --- Genérico ---
            "responder_simple": lambda command, response, **kwargs: self.speak(response)
        }
        
        # --- Fusionar Acciones Dinámicas de Plugin ---
        if hasattr(self, 'dynamic_actions'):
            action_map.update(self.dynamic_actions)
        
        # --- CEREBRO: Almacenar interacción ---
        if self.brain:
            self.brain.store_interaction(cmd, resp, intent_name)
            
        if name in action_map:
            return action_map[name](command=cmd, params=params, response=resp)
        else:
            app_logger.warning(f"Acción '{name}' no definida o no soportada en modo headless.")
            self.is_processing_command = False 
            return None 

    def give_morning_summary(self):
        """Ofrece un resumen matutino con el estado del sistema."""
        self.skills_system.give_morning_summary()

    def handle_learning_response(self, command_text):
        """Maneja la respuesta del usuario cuando se le pregunta por un dato desconocido."""
        key = self.waiting_for_learning
        if not key:
            self.waiting_for_learning = None
            return

        # Si el usuario dice "no lo sé" o "cancelar"
        if "cancelar" in command_text.lower() or "no lo sé" in command_text.lower():
            self.speak("Vale, no pasa nada.")
            self.waiting_for_learning = None
            return

        # Guardar el dato
        if self.brain:
            self.brain.add_fact(key, command_text)
            self.speak(f"Entendido. He aprendido que {key} es {command_text}.")
        else:
            self.speak("No tengo cerebro disponible para guardar eso.")
        
        self.waiting_for_learning = None

    def execute_command(self, command_text):
        """Intenta ejecutar un comando usando los diferentes gestores (Intent, Keyword, etc)."""
        # 1. Gestor de Intenciones (NLP)
        intent = self.intent_manager.find_best_intent(command_text)
        if intent and intent.get('score', 0) > 70:
             app_logger.info(f"Intent detectado: {intent.get('name', 'Unknown')} ({intent.get('confidence', 'N/A')})")
             # Aquí iría la lógica de ejecución de intents, por ahora devolvemos respuesta simple o delegamos
             # En la versión refactorizada, NeoCore delegaba esto.
             # Para simplificar: si hay intent, podríamos mapearlo a una acción.
             # Pero dado que el refactor es complejo, usaremos el KeywordRouter como fallback principal
             pass # TODO: Implementar ejecución completa de intents si es necesario

        # 2. Keyword Router (Comandos directos)
        router_response = self.keyword_router.process(command_text)
        if router_response:
             app_logger.info(f"Keyword Router ejecutó: {command_text}")
             if isinstance(router_response, str):
                 self.speak(router_response)
             return router_response

        # 3. System Admin Actions (si no fue capturado por router)
        if self.sysadmin_manager:
             # Comprobar frases de sistema comunes
             pass

        return None

    def handle_mango_confirmation(self, text):
        """Confirma o cancela un comando de sistema propuesto por Mango."""
        command = self.pending_mango_command
        self.pending_mango_command = None # Restablecer estado

        if any(w in text.lower() for w in ['sí', 'si', 'hazlo', 'dale', 'ejecuta', 'vale', 'ok']):
            self.speak("Ejecutando.")
            
            # Ejecutar comando
            try:
                import subprocess
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                output = result.stdout.strip() or result.stderr.strip()
                if output:
                    # Limitar salida hablada
                    spoken_output = output[:200]
                    self.speak(f"Resultado: {spoken_output}")
                else:
                    self.speak("Comando terminado sin salida.")
            except Exception as e:
                self.speak(f"Error al ejecutar: {e}")
                
        else:
            self.speak("Vale, cancelado.")

    def _get_filesystem_context(self):
        """Genera cadena de contexto con pwd y los top 5 archivos (por tamaño)."""
        try:
            cwd = os.getcwd()
            files = []
            try:
                # Usar scandir para mejor rendimiento y acceso a stat
                with os.scandir(cwd) as entries:
                    for entry in entries:
                        # Saltarse archivos ocultos
                        if not entry.name.startswith('.'):
                            try:
                                stats = entry.stat()
                                files.append((entry.name, stats.st_size))
                            except OSError:
                                pass # Saltar archivos a los que no podemos acceder
            except OSError:
                app_logger.warning(f"Could not scan directory: {cwd}")
                files = []
            
            # Ordenar por tamaño (descendente) y tomar top 5
            files.sort(key=lambda x: x[1], reverse=True)
            top_files = [f[0] for f in files[:5]]
            
            # Formato: 'ls=archivo1, archivo2, ...'
            ls_str = ", ".join(top_files)
            
            # Formato final según requerimiento: "Contexto: ['pwd=...', 'ls=...'] | "
            return f"['pwd={cwd}', 'ls={ls_str}']"
        except Exception as e:
            app_logger.error(f"Error generating FS context: {e}")
            return "['pwd=.', 'ls=']"

if __name__ == "__main__":
    app = NeoCore()
    app.run()
