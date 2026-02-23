import os
import logging
import subprocess

logger = logging.getLogger("FileManager")

class FileManager:
    """
    Gestor de archivos.
    Permite listar, leer, guardar y buscar archivos.
    """
    def __init__(self):
        pass

    def list_directory(self, path):
        """Lista el contenido de un directorio."""
        if not os.path.isdir(path):
            return False, "No es un directorio válido."
        
        try:
            items = []
            for entry in os.scandir(path):
                items.append({
                    'name': entry.name,
                    'is_dir': entry.is_dir(),
                    'size': entry.stat().st_size if not entry.is_dir() else 0,
                    'path': entry.path
                })
            # Ordenar: directorios primero, luego archivos (alfabéticamente)
            items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            return True, items
        except Exception as e:
            logger.error(f"Error listando directorio {path}: {e}")
            return False, str(e)

    def read_file(self, path):
        """Lee el contenido de un archivo de texto."""
        if not os.path.isfile(path):
            return False, "No es un archivo válido."
        
        # Límite de tamaño de comprobación (ej. 1MB) para prevenir bloqueos
        if os.path.getsize(path) > 1024 * 1024:
            return False, "El archivo es demasiado grande para editarlo aquí (>1MB)."

        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            return True, content
        except Exception as e:
            logger.error(f"Error leyendo archivo {path}: {e}")
            return False, str(e)

    def save_file(self, path, content):
        """Guarda contenido en un archivo."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "Archivo guardado correctamente."
        except Exception as e:
            logger.error(f"Error guardando archivo {path}: {e}")
            return False, str(e)

    def search_files(self, query, path='/'):
        """Busca archivos usando 'find'."""
        try:
            # find /path -name "*query*" -type f 2>/dev/null | head -n 20
            cmd = ['find', path, '-name', f'*{query}*', '-type', 'f', '-print']
            
            # Usamos subprocess para capturar salida y limitar resultados
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            
            results = []
            for _ in range(20): # Límite a 20 resultados
                line = process.stdout.readline()
                if not line:
                    break
                results.append(line.strip())
            
            process.terminate()
            return True, results
        except Exception as e:
            logger.error(f"Error buscando archivos: {e}")
            return False, str(e)
