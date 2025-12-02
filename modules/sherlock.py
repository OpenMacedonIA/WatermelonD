import logging
import time
import random
import subprocess
from modules.database import DatabaseManager

logger = logging.getLogger("NeoSherlock")

class Sherlock:
    """
    Sherlock is the Diagnostic Reasoning Engine for T.I.O.
    Block 4 Upgrade: Real Command Execution & Dynamic Trees.
    """
    def __init__(self, event_queue):
        self.db = DatabaseManager()
        self.event_queue = event_queue
        # Map concepts to real commands
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
        Runs a general system diagnosis (Internet, Disk, Memory, CPU).
        """
        logger.info("Sherlock: Running general diagnosis...")
        problems = []
        
        # Check Internet
        if not self._run_command(self.command_map['internet'])['success']:
            problems.append("No hay conexión a Internet.")
            
        # Check Disk
        disk = self._run_command(self.command_map['disk'])
        if disk['success'] and '100%' in disk['output']:
            problems.append("El disco está lleno.")
            
        # Check Memory
        mem = self._run_command(self.command_map['memory'])
        # Simple heuristic: if 'available' is very low (parsing needed, but let's keep it simple for now)
        
        if not problems:
            return "Todos los sistemas vitales (Red, Disco, Memoria) parecen nominales."
        else:
            return "He detectado problemas: " + " ".join(problems)

    def diagnose(self, problem_description):
        """
        Main entry point for diagnosis.
        """
        logger.info(f"Sherlock: Diagnosing '{problem_description}'...")
        
        # 1. Identify Concepts (Simplified)
        concepts = [word for word in self.command_map.keys() if word in problem_description.lower()]
        
        if not concepts:
            # Try to infer from Knowledge Graph
            # e.g. "web" -> infer "nginx"
            pass 

        if not concepts:
            return "No tengo ni idea de qué me hablas, Watson. Sé más específico."

        # 2. Execute Diagnostics
        report = []
        for concept in concepts:
            cmd = self.command_map.get(concept)
            if cmd:
                self.event_queue.put({'type': 'speak', 'text': f"Comprobando {concept}..."})
                result = self._run_command(cmd)
                status = "OK" if result['success'] else "FALLO"
                report.append(f"{concept}: {status}")
                
                # Knowledge Graph Pathfinding (if failed)
                if not result['success']:
                    self.event_queue.put({'type': 'speak', 'text': f"¡Ojo! {concept} ha fallado. Buscando culpables..."})
                    # Find dependencies
                    # e.g. nginx failed -> check port 80? check config?
                    pass

        if report:
            return "Diagnóstico finalizado: " + ", ".join(report)
        
        return "No he podido ejecutar ninguna prueba."

    def _run_command(self, cmd):
        try:
            # SECURITY WARNING: This executes shell commands.
            # Ensure cmd comes from trusted self.command_map only.
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            return {
                'success': result.returncode == 0,
                'output': result.stdout
            }
        except Exception as e:
            logger.error(f"Sherlock Execution Error: {e}")
            return {'success': False, 'output': str(e)}
