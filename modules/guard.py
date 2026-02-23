import json
import time
import threading
import logging
import os
import psutil
from collections import deque
from modules.virus_scanner import VirusScanner

logger = logging.getLogger("NeoGuard")

SIGNATURES_FILE = "resources/security/attack_signatures.json"
AUTH_LOG_PATH = "/var/log/auth.log" # Ajustar según distro (auth.log en Debian/Ubuntu)

class Guard:
    def __init__(self, event_queue):
        self.event_queue = event_queue
        self.signatures = self.load_signatures()
        self.running = False
        self.thread = None
        
        # Estado para contadores de ventana de tiempo
        # Estructura: { "signature_id": [timestamp1, timestamp2, ...] }
        self.state = {}
        
        # Escáner de Virus (Integración ClamAV)
        self.virus_scanner = VirusScanner()
        self.scanned_files = set()  # Rastrear los ya escaneados para no repetir 

    def load_signatures(self):
        if not os.path.exists(SIGNATURES_FILE):
            logger.warning(f"No se encontró {SIGNATURES_FILE}. Neo Guard inactivo.")
            return []
        try:
            with open(SIGNATURES_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando firmas de ataques: {e}")
            return []

    def start(self):
        if not self.signatures:
            return
        self.running = True
        self.thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Neo Guard (Sistema de Detección) iniciado.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def monitor_loop(self):
        # Abrir log si existe
        log_file = None
        if os.path.exists(AUTH_LOG_PATH):
            try:
                log_file = open(AUTH_LOG_PATH, 'r')
                log_file.seek(0, 2) # Ir al final del archivo
            except Exception as e:
                logger.error(f"No se pudo abrir {AUTH_LOG_PATH}: {e}")

        while self.running:
            try:
                # 1. Analizar Logs (Log-based Signatures)
                if log_file:
                    line = log_file.readline()
                    while line:
                        self.check_log_signatures(line)
                        line = log_file.readline()

                # 2. Analizar Sistema (Metric-based Signatures)
                self.check_system_signatures()
                
                # 3. Escanear descargas (Virus Scanner)
                self.scan_recent_downloads()

                time.sleep(5) # Intervalo de chequeo (cada 5 segundos)
            except Exception as e:
                logger.error(f"Error en ciclo de Neo Guard: {e}")
                time.sleep(5)

    def check_log_signatures(self, line):
        current_time = time.time()
        
        for sig in self.signatures:
            if sig.get('source') == 'log_auth':
                pattern = sig.get('pattern')
                if pattern and pattern in line:
                    self.register_event(sig, current_time)

    def check_system_signatures(self):
        current_time = time.time()
        
        # Recolectar métricas una vez
        cpu_pct = psutil.cpu_percent(interval=None)
        mem_pct = psutil.virtual_memory().percent
        
        # Contar conexiones SYN_SENT para DDoS
        syn_sent = 0
        try:
            connections = psutil.net_connections()
            for c in connections:
                if c.status == 'SYN_SENT':
                    syn_sent += 1
        except:
            pass

        metrics = {
            'cpu_percent': cpu_pct,
            'memory_percent': mem_pct,
            'syn_sent_count': syn_sent
        }

        for sig in self.signatures:
            source = sig.get('source')
            if source in ['system_stats', 'net_stats']:
                metric_name = sig.get('metric')
                threshold = sig.get('threshold')
                
                val = metrics.get(metric_name, 0)
                if val >= threshold:
                    # Para métricas, "evento" es que supere el umbral en este chequeo
                    # Podríamos querer que se mantenga X tiempo, pero simplificamos:
                    # Si supera, cuenta como 1 hit. Si la ventana es corta, saltará rápido.
                    self.register_event(sig, current_time)

    def register_event(self, sig, timestamp):
        sig_id = sig['id']
        window = sig.get('window_seconds', 60)
        threshold = sig.get('threshold', 1)
        
        if sig_id not in self.state:
            self.state[sig_id] = deque()
        
        # Añadir evento actual
        self.state[sig_id].append(timestamp)
        
        # Limpiar eventos viejos fuera de la ventana
        while self.state[sig_id] and self.state[sig_id][0] < (timestamp - window):
            self.state[sig_id].popleft()
            
        # Verificar umbral
        if len(self.state[sig_id]) >= threshold:
            self.trigger_alert(sig)
            # Limpiar para no repetir alerta inmediatamente (Cooldown simple)
            self.state[sig_id].clear()

    def trigger_alert(self, sig):
        msg = f"Alerta de Seguridad: {sig['name']} detectado."
        logger.warning(msg)
        
        # Enviar a NeoCore para que hable
        # Usamos prioridad alta si es crítico
        self.event_queue.put({
            'type': 'speak', 
            'text': msg,
            'priority': 'high'
        })
    
    def scan_recent_downloads(self):
        """Escanea archivos recién descargados por virus."""
        if not self.virus_scanner.clamav_available:
            return
        
        downloads_dir = os.path.expanduser("~/Downloads")
        if not os.path.exists(downloads_dir):
            return
        
        now = time.time()
        
        try:
            for filename in os.listdir(downloads_dir):
                filepath = os.path.join(downloads_dir, filename)
                
                # Solo archivos
                if not os.path.isfile(filepath):
                    continue
                
                # Omitir si ya fue escaneado
                if filepath in self.scanned_files:
                    continue
                
                # Solo archivos recientes (últimos 10 minutos)
                mtime = os.path.getmtime(filepath)
                if now - mtime > 600:
                    continue
                
                # Escanear archivo
                is_infected, virus_name = self.virus_scanner.scan_file(filepath)
                
                # Marcar como escaneado
                self.scanned_files.add(filepath)
                
                if is_infected:
                    self.trigger_virus_alert(filepath, virus_name)
                    
        except Exception as e:
            logger.error(f"Error escaneando descargas: {e}")
    
    def trigger_virus_alert(self, filepath, virus_name):
        """Alerta cuando se detecta un virus."""
        filename = os.path.basename(filepath)
        msg = f"ALERTA DE VIRUS: {virus_name} detectado en {filename}"
        logger.error(msg)
        
        # Mover a cuarentena
        if self.virus_scanner.quarantine_file(filepath):
            msg += ". Archivo movido a cuarentena."
        else:
            msg += ". No se pudo mover a cuarentena."
        
        # Alerta de voz urgente
        self.event_queue.put({
            'type': 'speak',
            'text': msg,
            'priority': 'critical'
        })
