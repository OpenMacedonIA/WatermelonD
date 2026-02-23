"""
Sistema de escaneo antivirus usando ClamAV.
Integración con WatermelonGuard para protección contra malware.
"""

import subprocess
import logging
import os
from typing import Tuple, List

logger = logging.getLogger("VirusScanner")


class VirusScanner:
    """
    Escáner de virus usando ClamAV.
    Detecta y pone en cuarentena archivos infectados.
    """
    
    def __init__(self):
        self.clamav_available = self._check_clamav()
        self.quarantine_dir = os.path.expanduser("~/.watermelond/quarantine")
        
        if self.clamav_available:
            os.makedirs(self.quarantine_dir, exist_ok=True)
            logger.info("VirusScanner inicializado con ClamAV")
        else:
            logger.warning("ClamAV no disponible. Escaneo de virus deshabilitado.")
    
    def _check_clamav(self) -> bool:
        """Verifica si ClamAV está instalado y disponible."""
        try:
            result = subprocess.run(
                ["clamscan", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"ClamAV detectado: {version}")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            logger.debug(f"ClamAV no encontrado: {e}")
        
        return False
    
    def scan_file(self, filepath: str) -> Tuple[bool, str]:
        """
        Escanea un archivo individual.
        
        Devuelve:
            (is_infected, virus_name): Tupla con estado y nombre del virus si existe
        """
        if not self.clamav_available:
            return False, None
        
        if not os.path.exists(filepath):
            logger.error(f"Archivo no existe: {filepath}")
            return False, None
        
        try:
            result = subprocess.run(
                ["clamscan", "--no-summary", filepath],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Códigos de salida de ClamAV:
            # 0 = no se encontró virus
            # 1 = virus encontrado
            # 2 = error
            
            if result.returncode == 1:
                # Parsear nombre del virus
                # Formato: "filepath: Virus.Name FOUND"
                output = result.stdout.strip()
                if "FOUND" in output:
                    try:
                        virus_name = output.split(":")[1].split("FOUND")[0].strip()
                        logger.warning(f"[VIRUS DETECTADO] {filepath}: {virus_name}")
                        return True, virus_name
                    except IndexError:
                        logger.warning(f"[VIRUS DETECTADO] {filepath}: Nombre no parseado")
                        return True, "Unknown"
            
            elif result.returncode == 2:
                logger.error(f"Error escaneando {filepath}: {result.stderr}")
            
            return False, None
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout escaneando {filepath}")
            return False, None
        except Exception as e:
            logger.error(f"Error inesperado escaneando {filepath}: {e}")
            return False, None
    
    def scan_directory(self, dirpath: str, recursive: bool = True) -> Tuple[List[str], int]:
        """
        Escanea directorio completo.
        
        Devuelve:
            (infected_files, total_scanned): Lista de archivos infectados y total escaneados
        """
        if not self.clamav_available:
            return [], 0
        
        if not os.path.exists(dirpath):
            logger.error(f"Directorio no existe: {dirpath}")
            return [], 0
        
        cmd = ["clamscan", "--infected"]
        if recursive:
            cmd.append("-r")
        cmd.append(dirpath)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos max
            )
            
            infected = []
            total = 0
            
            # Parsear salida
            for line in result.stdout.split("\n"):
                if "FOUND" in line:
                    # Formato: "filepath: Virus.Name FOUND"
                    filepath = line.split(":")[0].strip()
                    if filepath:
                        infected.append(filepath)
                
                # Contar total de archivos escaneados
                if "Scanned files:" in line:
                    try:
                        total = int(line.split(":")[1].strip())
                    except (IndexError, ValueError):
                        pass
            
            if infected:
                logger.warning(f"Escaneo completo: {len(infected)} infectados de {total} archivos")
            else:
                logger.info(f"Escaneo completo: {total} archivos limpios")
            
            return infected, total
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout escaneando directorio {dirpath}")
            return [], 0
        except Exception as e:
            logger.error(f"Error escaneando directorio {dirpath}: {e}")
            return [], 0
    
    def quarantine_file(self, filepath: str) -> bool:
        """
        Mueve archivo infectado a cuarentena.
        
        Devuelve:
            True si se movió correctamente
        """
        if not os.path.exists(filepath):
            return False
        
        try:
            import shutil
            filename = os.path.basename(filepath)
            quarantine_path = os.path.join(
                self.quarantine_dir,
                f"{filename}.{int(os.path.getmtime(filepath))}.quarantine"
            )
            
            shutil.move(filepath, quarantine_path)
            logger.info(f"[CUARENTENA] {filepath} → {quarantine_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error moviendo a cuarentena {filepath}: {e}")
            return False
    
    def list_quarantine(self) -> List[dict]:
        """
        Lista archivos en cuarentena.
        
        Devuelve:
            Lista de dicts con info de archivos en cuarentena
        """
        if not os.path.exists(self.quarantine_dir):
            return []
        
        quarantined = []
        try:
            for filename in os.listdir(self.quarantine_dir):
                filepath = os.path.join(self.quarantine_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    quarantined.append({
                        'filename': filename,
                        'path': filepath,
                        'size': stat.st_size,
                        'quarantine_date': stat.st_mtime
                    })
        except Exception as e:
            logger.error(f"Error listando cuarentena: {e}")
        
        return quarantined
    
    def delete_quarantined(self, filepath: str) -> bool:
        """Elimina permanentemente archivo de cuarentena."""
        if not filepath.startswith(self.quarantine_dir):
            logger.error(f"Intento de eliminar archivo fuera de cuarentena: {filepath}")
            return False
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"[ELIMINADO] {filepath}")
                return True
        except Exception as e:
            logger.error(f"Error eliminando {filepath}: {e}")
        
        return False
    
    def update_signatures(self) -> bool:
        """
        Actualiza base de datos de firmas de ClamAV.
        Requiere permisos sudo.
        """
        if not self.clamav_available:
            return False
        
        try:
            result = subprocess.run(
                ["sudo", "freshclam"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                logger.info("Firmas de virus actualizadas correctamente")
                return True
            else:
                logger.error(f"Error actualizando firmas: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Timeout actualizando firmas de virus")
            return False
        except Exception as e:
            logger.error(f"Error inesperado actualizando firmas: {e}")
            return False
