import os
import json
import time
import threading
import logging
from datetime import datetime
from modules.sysadmin import SysAdminManager

# Configure Logging
logger = logging.getLogger("HealthManager")

class HealthManager:
    """
    Gestor de Auto-curación y Mantenimiento Predictivo.
    - Reactivo: Detecta servicios caídos y los reinicia.
    - Predictivo: Aprende patrones de fallo basándose en historial.
    """
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.sys_admin = SysAdminManager()
        self.running = False
        self.thread = None
        
        # Estado de los servicios monitorizados
        # Estado de los servicios monitorizados
        self.monitored_services = [
            'nginx', 'apache2', 'lighttpd',       # Web Servers
            'mosquitto',                          # MQTT
            'ollama',                             # AI
            'networking', 'NetworkManager',       # Network
            'cron',                               # Scheduling
            'mysql', 'mariadb', 'postgresql',     # Databases
            'redis', 'mongodb', 
            'ssh', 'sshd',                        # Remote Access
            'fail2ban', 'ufw',                    # Security
            'docker',                             # Containers
            'bluetooth', 'avahi-daemon'           # Hardware/Discovery
        ]
        
        # Historial de incidentes
        self.history_file = 'data/health_history.json'
        self.incident_history = self._load_history()
        
        # Configuración de recuperación
        self.recovery_attempts = {} # {service: count}
        self.max_attempts = 3
        self.cooldown_window = 300 # 5 minutos para resetear intentos
        self.last_recovery_time = {} # {service: timestamp}

    def start(self):
        """Inicia el hilo de monitorización."""
        if self.running: return
        
        # Check for systemd (Fix for Distrobox/Containers)
        if not os.path.exists("/run/systemd/system"):
            logger.warning("Systemd not detected (Container/Distrobox?). Disabling service auto-healing.")
            self.monitored_services = []
        else:
            # Filter services that are not installed
            valid_services = []
            for srv in self.monitored_services:
                if self.sys_admin.is_service_installed(srv):
                    valid_services.append(srv)
                else:
                    logger.info(f"ℹ️ Skipping {srv}: Service not found on system.")
            self.monitored_services = valid_services
            
        logger.info(f"HealthManager checking: {self.monitored_services}")

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("HealthManager started (Self-Healing active)")

    def stop(self):
        """Detiene la monitorización."""
        self.running = False
        if self.thread:
            self.thread.join()

    def _monitor_loop(self):
        """Bucle principal de vigilancia."""
        while self.running:
            try:
                # 1. Comprobación Reactiva (Estado actual)
                self._check_services()
                
                # 2. Análisis Predictivo (Futuro)
                self._analyze_risks()
                
            except Exception as e:
                logger.error(f"Error in HealthManager loop: {e}")
                
            time.sleep(30) # Comprobar cada 30 segundos

    def _check_services(self):
        """Comprueba el estado de los servicios críticos y actúa si fallan."""
        # Check only specific services we care about
        services_status = self.sys_admin.get_services(self.monitored_services) 

        
        for srv in services_status:
            name = srv['name']
            status = srv['status']
            
            # Solo nos importan los que estamos vigilando explícitamente
            if name not in self.monitored_services and name != 'cron': # cron a veces viene por defecto
                continue

            if status != 'active':
                logger.warning(f"⚠️ Service DOWN detected: {name}")
                self._handle_failure(name)
            else:
                # Si está activo, reseteamos contadores si ha pasado tiempo suficiente
                if name in self.last_recovery_time:
                    if time.time() - self.last_recovery_time[name] > self.cooldown_window:
                        self.recovery_attempts[name] = 0

    def _handle_failure(self, service_name):
        """Intenta recuperar un servicio caído."""
        attempts = self.recovery_attempts.get(service_name, 0)
        
        if attempts < self.max_attempts:
            logger.info(f"🚑 Attempting recovery for {service_name} ({attempts + 1}/{self.max_attempts})")
            
            # Registrar incidente antes de recuperar (para tener contexto del crash)
            self._log_incident(service_name, "CRASH_DETECTED")
            
            # Intentar reinicio
            success, msg = self.sys_admin.control_service(service_name, 'restart')
            
            # Increment attempts regardless of outcome to avoid infinite loops
            self.recovery_attempts[service_name] = attempts + 1
            self.last_recovery_time[service_name] = time.time()

            if success:
                logger.info(f"✅ Recovery successful for {service_name}")
                self._log_incident(service_name, "RECOVERY_SUCCESS")
            else:
                logger.error(f"❌ Recovery failed for {service_name}: {msg}")
                self._log_incident(service_name, "RECOVERY_FAILED")
        else:
            logger.critical(f"💀 Give up on {service_name}. Max attempts reached.")
            # Aquí podríamos enviar una notificación urgente al usuario

    def _analyze_risks(self):
        """
        Análisis predictivo simple.
        Busca correlaciones entre uso de recursos y fallos previos.
        """
        # Obtener estado actual
        try:
            cpu = float(self.sys_admin.get_cpu_usage().replace('%', ''))
            ram = float(self.sys_admin.get_ram_usage().replace('%', ''))
            
            # Regla Heurística 1: Alta Carga Persistente
            if cpu > 90 or ram > 90:
                logger.warning("🔥 System Stress: High load components risking stability.")
                # Si tuviéramos un sistema de mensajería al usuario, aquí enviaríamos "High Load Alert"
                
            # Regla Heurística 2: Patrón de fallo recurrente (Aprendizaje simple)
            # Analizamos si fallos recientes coinciden con ciertas horas o condiciones
            # Por ahora, implementación simple basada en frecuencia.
            recent_crashes = [i for i in self.incident_history if (time.time() - i['timestamp']) < 86400 and i['event'] == 'CRASH_DETECTED']
            
            if len(recent_crashes) > 5:
                logger.warning("🔮 Prediction: System instability detected. High frequency of crashes in last 24h.")
                
        except Exception:
            pass

    def _log_incident(self, target, event):
        """Registra un evento en el historial con contexto del sistema."""
        snapshot = {
            'cpu': self.sys_admin.get_cpu_usage(),
            'ram': self.sys_admin.get_ram_usage(),
            'disk': self.sys_admin.get_disk_usage(),
            'temp': self.sys_admin.get_cpu_temp()
        }
        
        entry = {
            'timestamp': time.time(),
            'date': datetime.now().isoformat(),
            'target': target,
            'event': event,
            'context': snapshot
        }
        
        self.incident_history.append(entry)
        self._save_history()

    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_history(self):
        # Asegurar directorio
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        # Guardar solo los últimos 1000 eventos para no llenar disco
        keep = self.incident_history[-1000:]
        with open(self.history_file, 'w') as f:
            json.dump(keep, f, indent=4)
