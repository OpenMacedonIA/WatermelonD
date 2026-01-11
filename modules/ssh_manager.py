import paramiko
import json
import os
import logging
import base64
from modules.config_manager import ConfigManager

logger = logging.getLogger("SSHManager")

class SSHManager:
    """
    Gestor de conexiones SSH.
    Permite conectar a servidores remotos y ejecutar comandos.
    """
    def __init__(self):
        self.config_manager = ConfigManager()
        self.servers_file = self.config_manager.get('paths', {}).get('servers', 'jsons/servers.json')
        self.servers = self._load_servers()
        self.active_connections = {} # alias -> client

    def _load_servers(self):
        if os.path.exists(self.servers_file):
            try:
                with open(self.servers_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Migrate old plain text if necessary? For now assume mixed
                    return data
            except Exception as e:
                logger.error(f"Error cargando servidores: {e}")
                return {}
        return {}
    
    def _obfuscate(self, text):
        """Simple obfuscation to avoid plain text storage."""
        if not text: return None
        # Base64 encode
        encoded = base64.b64encode(text.encode()).decode()
        # Add a simple prefix to identify
        return f"ENC:{encoded}"

    def _deobfuscate(self, text):
        """Reverses obfuscation."""
        if not text: return None
        if text.startswith("ENC:"):
            try:
                raw = text.split("ENC:")[1]
                return base64.b64decode(raw).decode()
            except:
                return text # Fallback if decode fails
        return text # Fallback for legacy plain text

    def _save_servers(self):
        try:
            with open(self.servers_file, 'w', encoding='utf-8') as f:
                json.dump(self.servers, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando servidores: {e}")

    def add_server(self, alias, host, user, port=22, key_path=None, password=None):
        self.servers[alias] = {
            "host": host,
            "user": user,
            "port": port,
            "key_path": key_path,
            "password": self._obfuscate(password) if password else None
        }
        self._save_servers()
        logger.info(f"Servidor '{alias}' añadido.")
        return True

    def remove_server(self, alias):
        if alias in self.servers:
            del self.servers[alias]
            self._save_servers()
            return True
        return False

    def connect(self, alias):
        if alias not in self.servers:
            return False, "Servidor no encontrado."
        
        if alias in self.active_connections:
            return True, "Ya conectado."

        server = self.servers[alias]
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            connect_kwargs = {
                "hostname": server['host'],
                "username": server['user'],
                "port": int(server['port']),
                "timeout": 10
            }
            
            if server.get('key_path'):
                connect_kwargs['key_filename'] = server['key_path']
            elif server.get('password'):
                connect_kwargs['password'] = self._deobfuscate(server['password'])
            
            client.connect(**connect_kwargs)
            self.active_connections[alias] = client
            logger.info(f"Conectado a {alias} ({server['host']})")
            return True, f"Conectado a {alias}."
        except Exception as e:
            logger.error(f"Error conectando a {alias}: {e}")
            return False, str(e)

    def execute(self, alias, command):
        if alias not in self.active_connections:
            # Intentar reconectar
            success, msg = self.connect(alias)
            if not success:
                return False, f"No conectado: {msg}"

        client = self.active_connections[alias]
        try:
            stdin, stdout, stderr = client.exec_command(command, timeout=30)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if error:
                return False, error
            return True, output
        except Exception as e:
            logger.error(f"Error ejecutando comando en {alias}: {e}")
            # Si falla, quizás se cayó la conexión
            if alias in self.active_connections:
                del self.active_connections[alias]
            return False, str(e)

    def disconnect(self, alias):
        if alias in self.active_connections:
            self.active_connections[alias].close()
            del self.active_connections[alias]
            return True, f"Desconectado de {alias}."
        return False, "No estaba conectado."

    def get_servers_list(self):
        return list(self.servers.keys())
