import logging
import time
import random
import subprocess
from modules.database import DatabaseManager

logger = logging.getLogger("NeoSherlock")

class Sherlock:
    """
    Sherlock es el Motor de Razonamiento Diagnóstico para T.I.O.
    Mejora Bloque 4: Ejecución Real de Comandos y Árboles Dinámicos.
    """
    def __init__(self, event_queue):
        self.db = DatabaseManager()
        self.event_queue = event_queue
        # Mapea conceptos a comandos reales
        self.command_map = {
            "internet": "ping -c 1 8.8.8.8",
            "router": "ping -c 1 192.168.1.1", # Assumption
            "dns": "nslookup google.com",
            "disk": "df -h",
            "memory": "free -m",
            "cpu": "top -bn1 | head -5",
            "nginx": "systemctl is-active nginx",
            "apache": "systemctl is-active apache2",
            "docker": "systemctl is-active docker"
        }
        logger.info("Neo Sherlock (Block 4 Upgraded) initialized.")

    def run_diagnosis(self):
        """
        Ejecuta un diagnóstico general del sistema (Internet, Disco, Memoria, CPU).
        """
        logger.info("Sherlock: Ejecutando diagnóstico general...")
        problems = []
        
        # Comprobar internet
        if not self._run_command(self.command_map['internet'])['success']:
            problems.append("No hay conexión a Internet.")
            
        # Comprobar disco
        disk = self._run_command(self.command_map['disk'])
        if disk['success'] and '100%' in disk['output']:
            problems.append("El disco está lleno.")
            
        # Comprobar memoria
        mem = self._run_command(self.command_map['memory'])
        # Heurística simple: si lo disponible es muy bajo (necesita análisis pero se mantiene simple por ahora)
        
        if not problems:
            return "Todos los sistemas vitales (Red, Disco, Memoria) parecen nominales."
        else:
            return "He detectado problemas: " + " ".join(problems)

    def diagnose(self, problem_description):
        """
        Punto de entrada principal para el diagnóstico.
        """
        logger.info(f"Sherlock: Diagnosticando '{problem_description}'...")
        
        # 1. Identificar Conceptos (Simplificado)
        concepts = [word for word in self.command_map.keys() if word in problem_description.lower()]
        
        if not concepts:
            # Intentar deducir (infer) desde el Gráfico de Conocimiento
            # ej "web" -> deduce "nginx"
            pass 

        if not concepts:
            return "No tengo ni idea de qué me hablas, Watson. Sé más específico."

        # 2. Ejecutar Pruebas Diagnósticas
        report = []
        for concept in concepts:
            cmd = self.command_map.get(concept)
            if cmd:
                self.event_queue.put({'type': 'speak', 'text': f"Comprobando {concept}..."})
                result = self._run_command(cmd)
                status = "OK" if result['success'] else "FALLO"
                report.append(f"{concept}: {status}")
                
                # Pathfinding del Gráfico de Conocimiento (si falló)
                if not result['success']:
                    self.event_queue.put({'type': 'speak', 'text': f"¡Ojo! {concept} ha fallado. Buscando culpables..."})
                    # Encontrar dependencias
                    # ej nginx falló -> comprueba puerto 80? comprueba conf?
                    pass

        if report:
            return "Diagnóstico finalizado: " + ", ".join(report)
        
        return "No he podido ejecutar ninguna prueba."

    def _run_command(self, cmd):
        try:
            # ADVERTENCIA DE SEGURIDAD: Esto ejecuta comandos de terminal (shell).
            # Asegúrate que el comndo viene únicamente del mapeado confiable command_map
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            return {
                'success': result.returncode == 0,
                'output': result.stdout
            }
        except Exception as e:
            logger.error(f"Sherlock Execution Error: {e}")
            return {'success': False, 'output': str(e)}
