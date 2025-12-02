import logging
import subprocess
import re

logger = logging.getLogger("KeywordRouter")

class KeywordRouter:
    """
    Router de Palabras Clave para ejecución directa de funciones.
    Intercepta comandos antes de que lleguen a la IA para acciones críticas o complejas.
    """
    def __init__(self, core_instance=None):
        self.core = core_instance
        self.rules = [
            {
                'keywords': ['reinicia', 'servicio'],
                'action': self.action_restart_service,
                'name': 'restart_service'
            }
        ]
        logger.info("KeywordRouter inicializado con %d reglas.", len(self.rules))

    def process(self, text):
        """
        Procesa el texto y busca coincidencias con las reglas.
        Retorna el resultado de la acción si hay match, o None.
        """
        text_lower = text.lower()
        
        for rule in self.rules:
            if all(keyword in text_lower for keyword in rule['keywords']):
                logger.info(f"Keyword Match: Regla '{rule['name']}' activada por '{text}'")
                return rule['action'](text)
        
        return None

    def action_restart_service(self, text):
        """
        Reinicia un servicio del sistema.
        Ejemplo: "reinicia el servicio de nginx" -> systemctl restart nginx
        """
        # Extraer el nombre del servicio
        # Buscamos la palabra después de "servicio" o "de"
        # Regex simple: busca la última palabra o palabras clave
        
        # Estrategia: Tokenizar y buscar palabras comunes de servicios
        common_services = ['nginx', 'apache2', 'mysql', 'postgresql', 'docker', 'bluetooth', 'ssh', 'cron']
        
        target_service = None
        for service in common_services:
            if service in text.lower():
                target_service = service
                break
        
        # Si no está en la lista común, intentamos extraerlo heurísticamente
        if not target_service:
            # Asumimos que es la última palabra si no es "servicio"
            words = text.split()
            if words:
                candidate = words[-1]
                if candidate.lower() not in ['servicio', 'de', 'el', 'la']:
                    target_service = candidate

        if not target_service:
            return "No pude identificar el nombre del servicio a reiniciar."

        logger.info(f"Ejecutando: systemctl restart {target_service}")
        
        try:
            # Ejecutar comando
            # Nota: Esto requiere permisos de sudo o ser root. 
            # Si el usuario no es root, esto fallará a menos que tenga NOPASSWD en sudoers.
            # Intentamos con sudo -n para no bloquear si pide pass.
            
            cmd = ["sudo", "-n", "systemctl", "restart", target_service]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return f"Éxito: El servicio {target_service} se ha reiniciado correctamente."
            else:
                return f"Error al reiniciar {target_service}: {result.stderr.strip() or 'Permiso denegado o servicio no encontrado.'}"
                
        except Exception as e:
            logger.error(f"Error ejecutando systemctl: {e}")
            return f"Ocurrió un error intentando reiniciar {target_service}: {str(e)}"
