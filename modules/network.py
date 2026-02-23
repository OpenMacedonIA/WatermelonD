import subprocess
import logging
import re
import socket
import shutil

logger = logging.getLogger("NeoNetSec")

class NetworkManager:
    def __init__(self):
        self.check_dependencies()

    def check_dependencies(self):
        """Verifica si las herramientas necesarias están instaladas."""
        tools = ["nmap", "ping", "whois", "nslookup"]
        missing = []
        for tool in tools:
            if not shutil.which(tool):
                missing.append(tool)
        
        if missing:
            logger.warning(f"Faltan herramientas de red: {', '.join(missing)}. Algunas funciones no estarán disponibles.")
        else:
            logger.info("Módulo de Red inicializado. Todas las herramientas encontradas.")

    def run_command(self, command):
        """Ejecuta un comando de sistema y devuelve la salida."""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                logger.error(f"Error ejecutando '{command}': {result.stderr}")
                return None
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ejecutando '{command}'")
            return None
        except Exception as e:
            logger.error(f"Excepción ejecutando '{command}': {e}")
            return None

    def get_local_ip(self):
        """Obtiene la IP local para saber qué red escanear."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def scan_network(self):
        """Escanea la red local en busca de dispositivos."""
        local_ip = self.get_local_ip()
        if local_ip == "127.0.0.1":
            return "No estoy conectado a ninguna red externa."
            
        # Asumimos máscara /24 para redes domésticas
        subnet = ".".join(local_ip.split(".")[:3]) + ".0/24"
        logger.info(f"Escaneando subred: {subnet}")
        
        # Escaneo rápido (-F) y detección de SO (-O requiere root, mejor no usarlo por defecto)
        # Usamos -sn (ping scan) para descubrir hosts primero, o -F para puertos rápidos
        output = self.run_command(f"nmap -F {subnet}")
        
        if output:
            return self.analyze_security(output)
        return "Hubo un error al escanear la red."

    def check_host(self, host):
        """Hace un ping a un host."""
        # Limpieza básica de input para evitar inyección
        host = re.sub(r'[;&|]', '', host).strip()
        logger.info(f"Haciendo ping a: {host}")
        
        output = self.run_command(f"ping -c 3 {host}")
        if output:
            # Extraer latencia media
            match = re.search(r'time=(\d+\.?\d*) ms', output)
            if match:
                latency = match.group(1)
                return f"El host {host} responde con una latencia de {latency} milisegundos."
            return f"El host {host} está activo."
        return f"No he podido contactar con {host}."

    def whois_lookup(self, domain):
        """Consulta WHOIS de un dominio."""
        domain = re.sub(r'[;&|]', '', domain).strip()
        logger.info(f"WHOIS para: {domain}")
        
        output = self.run_command(f"whois {domain}")
        if output:
            # Filtrar salida para no leer todo el texto
            lines = output.split('\n')
            relevant = [line for line in lines if "Registrar:" in line or "Creation Date:" in line or "Registry Expiry Date:" in line]
            if relevant:
                return "Información encontrada:\n" + "\n".join(relevant[:5])
            return "He obtenido los datos de WHOIS, pero son muy extensos para leerlos todos."
        return "No he podido obtener información WHOIS."

    def analyze_security(self, nmap_output):
        """Analiza la salida de Nmap buscando vulnerabilidades obvias."""
        report = []
        lines = nmap_output.split('\n')
        
        hosts_found = 0
        current_ip = None
        
        risky_ports = {
            "21/tcp": "FTP (Transferencia de archivos insegura)",
            "23/tcp": "Telnet (Texto plano, muy inseguro)",
            "3389/tcp": "RDP (Escritorio Remoto expuesto)"
        }
        
        for line in lines:
            if "Nmap scan report for" in line:
                hosts_found += 1
                current_ip = line.split("for")[-1].strip()
            
            for port, desc in risky_ports.items():
                if f"{port} open" in line:
                    report.append(f"ALERTA: El dispositivo {current_ip} tiene abierto el puerto {port} ({desc}).")

        summary = f"Escaneo finalizado. He encontrado {hosts_found} dispositivos conectados."
        
        if report:
            summary += " He detectado algunas vulnerabilidades potenciales: " + " ".join(report)
        else:
            summary += " No he detectado puertos de alto riesgo abiertos en el escaneo rápido."
            
        return summary
