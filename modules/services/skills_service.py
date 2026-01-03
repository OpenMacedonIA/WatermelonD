import logging
import os
import sys
import queue
import threading
import time
import random
from datetime import datetime, date
# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from modules.utils import load_json_data
from modules.bus_client import BusClient
from modules.config_manager import ConfigManager
from modules.logger import app_logger
from modules.database import DatabaseManager

# Managers
from modules.calendar_manager import CalendarManager
from modules.alarms import AlarmManager
from modules.ssh_manager import SSHManager
from modules.wifi_manager import WifiManager
from modules.file_manager import FileManager
from modules.cast_manager import CastManager
from modules.mqtt_manager import MQTTManager
from modules.bluetooth_manager import BluetoothManager
from modules.ai_engine import AIEngine
from modules.chat import ChatManager
from modules.brain import Brain

# Optional Managers
try:
    from modules.sysadmin import SysAdminManager
except ImportError:
    SysAdminManager = None
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

# Skills
from modules.skills.system import SystemSkill
from modules.skills.network import NetworkSkill
from modules.skills.time_date import TimeDateSkill
from modules.skills.content import ContentSkill
from modules.skills.media import MediaSkill
from modules.skills.organizer import OrganizerSkill
from modules.skills.ssh import SSHSkill
from modules.skills.files import FilesSkill
from modules.skills.files import FilesSkill
from modules.skills.visual import VisualSkill

# Mango (NL2Bash)
try:
    from modules.mango_manager import MangoManager
except ImportError:
    MangoManager = None

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [SKILLS] - %(levelname)s - %(message)s')
logger = logging.getLogger("SkillsService")

class EventQueueWrapper:
    def __init__(self, bus):
        self.bus = bus

    def put(self, item):
        """Intercepts event_queue.put and emits to bus."""
        msg_type = item.get('type')
        if msg_type == 'speak':
            self.bus.emit('speak', {'text': item.get('text')})
        elif msg_type == 'mqtt_alert':
            # Re-emit as bus event
            self.bus.emit('mqtt.alert', item)
        else:
            logger.warning(f"Unknown event type in queue: {msg_type}")

class SkillsService:
    def __init__(self):
        self.bus = BusClient(name="SkillsService")
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_all()
        
        # Emulate NeoCore interface for skills
        self.event_queue = EventQueueWrapper(self.bus)
        
        # Initialize Managers
        # Initialize Managers
        self.init_managers()
        
        # Load Config BEFORE Skills (so they can access it)
        self.load_intents()
        
        # Expose logger as app_logger for skills
        self.app_logger = logger
        
        # Initialize Skills
        self.init_skills()
        
        # Action Map
        self.build_action_map()
        
        # Connect to Bus
        # Connect to Bus
        # Connect to Bus handled in run()
        self.register_intents()

    def load_intents(self):
        self.intents_data = load_json_data('config/intents.json', 'intents')
        self.intents_map = {i['name']: i for i in self.intents_data} if self.intents_data else {}
        
        # Load Skills Config
        self.skills_config = load_json_data('config/skills.json')
        if not self.skills_config:
            # Default fallback
            self.skills_config = {}
            logger.warning("Could not load config/skills.json")

    def init_managers(self):
        logger.info("Initializing Managers...")
        self.calendar_manager = CalendarManager()
        self.db = DatabaseManager()
        self.alarm_manager = AlarmManager()
        self.sysadmin_manager = SysAdminManager() if SysAdminManager else None
        self.ssh_manager = SSHManager()
        self.wifi_manager = WifiManager()
        self.file_manager = FileManager()
        self.cast_manager = CastManager()
        # self.cast_manager.start_discovery() # Optional
        
        self.network_manager = NetworkManager() if NetworkManager else None
        self.guard = Guard(self.event_queue) if Guard else None
        self.sherlock = Sherlock(self.event_queue) if Sherlock else None
        
        # AI & Brain
        model_path = self.config.get('ai_model_path')
        self.ai_engine = AIEngine(model_path=model_path)
        self.brain = Brain()
        self.brain.set_ai_engine(self.ai_engine)
        self.chat_manager = ChatManager(self.ai_engine)
        self.chat_manager.brain = self.brain
        
        # Initialize Mango
        self.mango_manager = MangoManager() if MangoManager else None
        if self.mango_manager:
            logger.info("MangoManager initialized for Sysadmin duties.")
        else:
            logger.warning("MangoManager not available.")

    def init_skills(self):
        logger.info("Initializing Skills...")
        self.skills_system = SystemSkill(self)
        self.skills_network = NetworkSkill(self)
        self.skills_time = TimeDateSkill(self)
        self.skills_media = MediaSkill(self)
        self.skills_content = ContentSkill(self)
        self.skills_organizer = OrganizerSkill(self)
        self.skills_ssh = SSHSkill(self)
        self.skills_files = FilesSkill(self)
        self.skills_visual = VisualSkill(self)
        
        # Map instances to names for permission checking
        self.skill_instance_map = {
            self.skills_system: "system",
            self.skills_network: "network",
            self.skills_time: "time",
            self.skills_media: "media",
            self.skills_content: "content",
            self.skills_organizer: "organizer",
            self.skills_ssh: "ssh",
            self.skills_files: "files",
            self.skills_visual: "visual"
        }

    def build_action_map(self):
        self.action_map = {
            # System
            "accion_apagar": self.skills_system.apagar,
            "check_system_status": self.skills_system.check_status,
            "queja_factura": self.skills_system.queja_factura,
            "diagnostico": self.skills_system.diagnostico,
            "system_restart_service": self.skills_system.restart_service,
            "system_update": self.skills_system.update_system,
            "system_find_file": self.skills_system.find_file,
            "list_services": self.skills_system.list_services,
            # Time
            "decir_hora_actual": self.skills_time.decir_hora_fecha,
            "decir_fecha_actual": self.skills_time.decir_hora_fecha,
            "decir_dia_semana": self.skills_time.decir_dia_semana,
            # Organizer
            "consultar_citas": self.skills_organizer.consultar_citas,
            "crear_recordatorio_voz": self.skills_organizer.crear_recordatorio_voz,
            "crear_alarma_voz": self.skills_organizer.crear_alarma_voz,
            "consultar_recordatorios_dia": self.skills_organizer.consultar_recordatorios_dia,
            "consultar_alarmas": self.skills_organizer.consultar_alarmas,
            "iniciar_dialogo_temporizador": self.skills_organizer.iniciar_dialogo_temporizador,
            "consultar_temporizador": self.skills_organizer.consultar_temporizador,
            "crear_temporizador_directo": self.skills_organizer.crear_temporizador_directo,
            # Media
            "controlar_radio": self.skills_media.controlar_radio,
            "detener_radio": self.skills_media.detener_radio,
            "cast_video": self.skills_media.cast_video,
            "stop_cast": self.skills_media.stop_cast,
            # Content
            "contar_chiste": self.skills_content.contar_contenido_aleatorio,
            "decir_frase_celebre": self.skills_content.decir_frase_celebre,
            "contar_dato_curioso": self.skills_content.contar_contenido_aleatorio,
            "aprender_alias": self.skills_content.aprender_alias,
            "aprender_dato": self.skills_content.aprender_dato,
            "consultar_dato": self.skills_content.consultar_dato,
            # Network/SSH/Files
            "network_scan": self.skills_network.scan,
            "network_ping": self.skills_network.ping,
            "network_whois": self.skills_network.whois,
            "public_ip": self.skills_network.public_ip,
            "speedtest": self.skills_network.speedtest,
            "check_service": self.skills_system.check_service,
            "disk_usage": self.skills_system.disk_usage,
            "system_info": self.skills_system.system_info,
            "network_status": self.skills_system.network_status,
            "escalar_cluster": self.skills_network.escalar_cluster,
            "ssh_connect": self.skills_ssh.connect,
            "ssh_execute": self.skills_ssh.execute,
            "ssh_disconnect": self.skills_ssh.disconnect,
            "buscar_archivo": self.skills_files.search_file,
            "leer_archivo": self.skills_files.read_file,
            'search_file': self.skills_files.search_file,
            'read_file': self.skills_files.read_file,
            'scan_files': self.skills_files.scan_now,
            
            'visual_show': self.skills_visual.show_last_file,
            'visual_close': self.skills_visual.close_content,
            # Generic
            "responder_simple": self.responder_simple,
            "saludo": self.responder_simple,
            "despedida": self.responder_simple,
            "agradecimiento": self.responder_simple,
        }

    def responder_simple(self, command, response, **kwargs):
        """Simplemente dice la respuesta predefinida."""
        if response:
            self.speak(response)
        else:
            # Fallback to AI if no response defined
            self.handle_unknown({"data": {"utterance": command}})

    def register_intents(self):
        # Register for all intents in action_map
        for intent_name in self.action_map:
            self.bus.on(intent_name, self.handle_intent)
            
        # Also register for unknown intent (fallback to Chat)
        self.bus.on("recognizer_loop:unknown_intent", self.handle_unknown)

    def handle_intent(self, message):
        intent_type = message.get('type')
        data = message.get('data', {})
        utterance = data.get('utterance', '')
        params = data.get('parameters', {})
        
        logger.info(f"Executing Skill for: {intent_type}")
        
        if intent_type in self.action_map:
            # Get response from intents
            response = ""
            intent_def = self.intents_map.get(intent_type)
            if intent_def and 'responses' in intent_def:
                responses = intent_def['responses']
                if responses:
                    response = random.choice(responses)
            
            try:
                method = self.action_map[intent_type]
                
                # Check if skill is enabled
                skill_instance = getattr(method, '__self__', None)
                if skill_instance:
                    skill_name = self.skill_instance_map.get(skill_instance)
                    if skill_name:
                        # Reload config to be sure (or we could listen for updates)
                        # For performance, we might want to cache this, but for now reload is safer for immediate effect
                        self.skills_config = load_json_data('config/skills.json') or {}
                        
                        skill_info = self.skills_config.get(skill_name, {})
                        if not skill_info.get('enabled', True):
                            logger.info(f"Skill '{skill_name}' is DISABLED. Blocking action.")
                            self.bus.emit('speak', {'text': f"La habilidad {skill_name} está desactivada."})
                            return

                method(command=utterance, response=response, **params)
            except Exception as e:
                logger.error(f"Error executing skill {intent_type}: {e}")
                self.bus.emit('speak', {'text': "Hubo un error ejecutando esa acción."})

    def handle_unknown(self, message):
        logger.info(f"Received unknown intent event: {message}")
        data = message.get('data', {})
        utterance = data.get('utterance', '')
        
        if not utterance:
             logger.warning("Unknown intent event received but no utterance found.")
             return

        # 1. Try Mango (Sysadmin/Command) First
        if self.mango_manager and self.mango_manager.is_ready:
            logger.info(f"Consulting Mango for: {utterance}")
            command, confidence = self.mango_manager.infer(utterance)
            
            # Threshold matches user preference for Mango priority
            if command and confidence >= 0.8: 
                logger.info(f"Mango identified command: {command} (Conf: {confidence})")
                
                if self.sysadmin_manager:
                    self.bus.emit('speak', {'text': "Ejecutando..."})
                    
                    # Security Check (Basic)
                    forbidden = ["rm ", "mkfs", "dd ", ">", "mv ", "shutdown", "reboot"]
                    if any(bad in command for bad in forbidden):
                        self.bus.emit('speak', {'text': "Comando bloqueado por seguridad."})
                        return

                    success, output = self.sysadmin_manager.run_command(command)
                    if success:
                        # Smart Summary for TTS
                        speak_text = self.summarize_output(output, command)
                        self.bus.emit('speak', {'text': speak_text})
                    else:
                        self.bus.emit('speak', {'text': "Error en la ejecución."})
                else:
                    self.bus.emit('speak', {'text': f"Entendido: {command}. Pero no tengo módulo de administración."})
                
                return
            else:
                 logger.info(f"Mango ignored input (Conf: {confidence}). Falling back to Gemma.")

    def summarize_output(self, output, command):
        """Generates a TTS-friendly summary of command output."""
        output = output.strip()
        lines = output.split('\n')
        count = len(lines)
        
        # 1. Detect 'ls -l' style output (drwxr-xr-x ...)
        if count > 0 and (lines[0].startswith('total ') or lines[0].startswith('drwx') or lines[0].startswith('-rw')):
            # It's a file list
            file_count = 0
            dir_count = 0
            files = []
            
            for line in lines:
                if line.startswith('total '): continue
                parts = line.split()
                if len(parts) > 8:
                    name = " ".join(parts[8:]) # Username/date etc are before this
                    if line.startswith('d'):
                        dir_count += 1
                    else:
                        file_count += 1
                        files.append(name)
            
            total_items = file_count + dir_count
            
            if total_items > 5:
                # Too many: Just count
                msg = f"Se encontraron {total_items} elementos"
                if dir_count > 0: msg += f", {dir_count} carpetas"
                if file_count > 0: msg += f" y {file_count} archivos"
                msg += "."
                return msg
            elif total_items > 0:
                # Few: Read names
                return f"Hay {total_items} elementos: {', '.join(files)}."
            else:
                return "El directorio está vacío."

        # 2. General Output Handling
        if len(output) < 300 and count <= 5:
             # Short enough to read fully
             return f"Salida: {output}"
        else:
             # Too long, read summary
             preview = ". ".join(lines[:2]) # Read first 2 lines only
             
             # Save full output
             filename = os.path.join(os.path.expanduser("~"), "resultado_comando.txt")
             try:
                 with open(filename, 'w') as f:
                     f.write(output)
                 return f"Salida extensa: {preview}. Resultado completo guardado en resultado_comando.txt."
             except Exception:
                 return f"Salida: {preview}. Y más texto."

        # 2. Fallback to Chat (Gemma)
        logger.info(f"Chatting with AI: {utterance}")
        try:
            # Use ChatManager
            response = self.chat_manager.get_response(utterance)
            logger.info(f"AI Response: {response}")
            self.bus.emit('speak', {'text': response})
        except Exception as e:
            logger.error(f"Error in ChatManager: {e}")
            self.bus.emit('speak', {'text': "Lo siento, me he quedado en blanco."})

    def run(self):
        logger.info("Skills Service Started")
        self.bus.run_forever()

    # Helper for skills that might call self.core.speak directly (if any)
    def speak(self, text):
        self.bus.emit('speak', {'text': text})

    def on_closing(self):
        # Cleanup
        pass

if __name__ == "__main__":
    service = SkillsService()
    service.run()
