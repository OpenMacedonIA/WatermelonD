import psutil
import logging
import subprocess
import socket
import platform
import time

class SysAdminManager:
    """
    Gestor de administración del sistema.
    Proporciona métodos para obtener métricas (CPU, RAM, Disco),
    gestionar servicios systemd y ejecutar comandos de shell.
    """
    def __init__(self):
        pass

    def get_cpu_temp(self):
        """
        Obtiene la temperatura de la CPU de forma compatible con múltiples sistemas.
        Intenta usar psutil primero, luego fallback a ficheros de sistema (Raspberry Pi).
        """
        try:
            # Método 1: psutil.sensors_temperatures() (Linux estándar)
            temps = psutil.sensors_temperatures()
            if temps:
                # Busca sensores comunes
                for name in ['cpu_thermal', 'coretemp', 'k10temp', 'acpitz']:
                    if name in temps:
                        # Devuelve la temperatura del primer núcleo/sensor encontrado
                        return f"{temps[name][0].current:.1f}°C"
                
                # Si no coincide con nombres conocidos, devuelve el primero que encuentre
                first_key = list(temps.keys())[0]
                return f"{temps[first_key][0].current:.1f}°C"
        except Exception as e:
            logging.error(f"Error leyendo temperatura con psutil: {e}")

        # Método 2: Fallback específico para Raspberry Pi
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read()) / 1000.0
            return f"{temp:.1f}°C"
        except FileNotFoundError:
            pass

        return "N/A"

    def get_cpu_usage(self):
        """Obtiene el porcentaje de uso de la CPU."""
        try:
            return f"{psutil.cpu_percent(interval=0.1)}%"
        except Exception:
            return "N/A"

    def get_disk_usage(self):
        """Devuelve el uso de disco en porcentaje."""
        try:
            return psutil.disk_usage('/').percent
        except:
            return 0

    def get_top_processes(self, limit=10):
        """Devuelve los procesos que más recursos consumen."""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Ordenar por CPU y luego Memoria
            processes.sort(key=lambda p: p['cpu_percent'], reverse=True)
            return processes[:limit]
        except Exception as e:
            print(f"Error getting processes: {e}")
            return []

    def get_ram_usage(self):
        """Obtiene el porcentaje de uso de la memoria RAM."""
        try:
            ram = psutil.virtual_memory()
            return f"{ram.percent}%"
        except Exception:
            return "N/A"

    def get_full_status(self):
        """Devuelve un resumen textual del estado del sistema (CPU, Disco, RAM)."""
        temp = self.get_cpu_temp()
        disk = self.get_disk_usage()
        ram = self.get_ram_usage()
        return f"La temperatura de la CPU es de {temp}. El uso de disco está al {disk} y la memoria RAM al {ram}."

    # --- NUEVAS FUNCIONALIDADES (PHASE 8) ---

    def get_services(self):
        """
        Devuelve el estado de una lista predefinida de servicios clave.
        Retorna una lista de diccionarios: [{'name': 'ssh', 'status': 'active'}, ...]
        """
        services = ['ssh', 'docker', 'nginx', 'openkompai', 'cron', 'networking']
        status_list = []
        
        for srv in services:
            try:
                # systemctl is-active devuelve 0 si activo, otro si no
                cmd = subprocess.run(['systemctl', 'is-active', srv], capture_output=True, text=True)
                state = cmd.stdout.strip()
                status_list.append({'name': srv, 'status': state})
            except Exception:
                status_list.append({'name': srv, 'status': 'unknown'})
        
        return status_list

    def control_service(self, service_name, action):
        """
        Controla servicios systemd (start/stop/restart).
        Requiere que el usuario tenga permisos sudo sin contraseña para systemctl.
        """
        if action not in ['start', 'stop', 'restart']:
            return False, "Acción no válida"
        
        try:
            if service_name in ['neo', 'neo.service']:
                # Neo runs as user service
                subprocess.run(['systemctl', '--user', action, 'neo.service'], check=True)
            else:
                # System services require sudo
                subprocess.run(['sudo', 'systemctl', action, service_name], check=True)
                
            return True, f"Servicio {service_name} {action} ejecutado."
        except subprocess.CalledProcessError as e:
            return False, str(e)

    def get_network_info(self):
        """
        Obtiene información de las interfaces de red (Nombre, IP, Estado).
        Filtra la interfaz loopback.
        """
        info = []
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            for iface, addr_list in addrs.items():
                # Filtrar loopback
                if iface == 'lo':
                    continue
                    
                iface_info = {'name': iface, 'ip': 'N/A', 'is_up': False}
                
                # Estado (UP/DOWN)
                if iface in stats:
                    iface_info['is_up'] = stats[iface].isup
                
                # IP Address
                for addr in addr_list:
                    if addr.family == socket.AF_INET:
                        iface_info['ip'] = addr.address
                
                info.append(iface_info)
        except Exception as e:
            logging.error(f"Error obteniendo red: {e}")
            
        return info

    def run_command(self, command, cwd=None):
        """
        Ejecuta un comando de shell y devuelve la salida (stdout + stderr).
        Soporta timeout de 10 segundos y directorio de trabajo personalizado.
        """
        try:
            # Ejecutar comando con timeout de 10s
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=10,
                cwd=cwd
            )
            return True, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Error: El comando excedió el tiempo límite."
        except Exception as e:
            return False, str(e)

    def get_file_completions(self, partial_name, cwd):
        """
        Devuelve una lista de archivos/directorios que coinciden con el nombre parcial.
        Usado para el autocompletado con Tab.
        """
        import os
        matches = []
        try:
            # Determinar directorio base y prefijo de búsqueda
            if '/' in partial_name:
                dirname, prefix = os.path.split(partial_name)
                # Resolver ruta absoluta o relativa
                if os.path.isabs(dirname):
                    search_dir = dirname
                else:
                    search_dir = os.path.join(cwd, dirname)
            else:
                dirname = ""
                prefix = partial_name
                search_dir = cwd

            if not os.path.isdir(search_dir):
                return []

            for item in os.listdir(search_dir):
                if item.startswith(prefix):
                    full_path = os.path.join(search_dir, item)
                    suffix = "/" if os.path.isdir(full_path) else ""
                    # Devolvemos solo la parte que completa lo que el usuario escribió
                    # Si el usuario escribió "Do", y existe "Documents", devolvemos "Documents/"
                    # Pero el frontend necesita saber qué reemplazar.
                    # Simplificación: devolvemos el nombre completo del archivo/dir
                    matches.append(os.path.join(dirname, item) + suffix)
            
            return sorted(matches)
        except Exception as e:
            logging.error(f"Error en autocompletado: {e}")
            return []
            logging.error(f"Error en autocompletado: {e}")
            return []

    def get_battery_status(self):
        """Devuelve el estado de la batería (si existe)."""
        try:
            battery = psutil.sensors_battery()
            if battery:
                percent = battery.percent
                charging = "cargando" if battery.power_plugged else "descargando"
                return f"{percent}% ({charging})"
            return "No detectada"
        except Exception:
            return "Error al leer batería"

    def get_network_bytes(self):
        """Devuelve bytes enviados y recibidos."""
        try:
            net = psutil.net_io_counters()
            sent = self._sizeof_fmt(net.bytes_sent)
            recv = self._sizeof_fmt(net.bytes_recv)
            return sent, recv
        except Exception:
            return "0B", "0B"

    def get_system_info(self):
        """Devuelve información del SO y Kernel."""
        try:
            uname = platform.uname()
            # Intentar obtener distro
            distro_name = "Linux"
            try:
                with open("/etc/os-release") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            distro_name = line.split("=")[1].strip().strip('"')
                            break
            except:
                pass
            
            return {
                "system": uname.system,
                "node": uname.node,
                "release": uname.release,
                "version": uname.version,
                "machine": uname.machine,
                "distro": distro_name
            }
        except Exception as e:
            logging.error(f"Error system info: {e}")
            return {}

    def _sizeof_fmt(self, num, suffix="B"):
        for unit in ["", "Ki", "Mi", "Gi", "Ti"]:
            if abs(num) < 1024.0:
                return f"{num:3.1f}{unit}{suffix}"
            num /= 1024.0
    def _sizeof_fmt(self, num, suffix="B"):
        for unit in ["", "Ki", "Mi", "Gi", "Ti"]:
            if abs(num) < 1024.0:
                return f"{num:3.1f}{unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f}Pi{suffix}"

    def run_speedtest(self):
        """Ejecuta un test de velocidad usando speedtest-cli."""
        try:
            # Usar subprocess para llamar a speedtest-cli --simple
            # Output format:
            # Ping: 12.34 ms
            # Download: 100.00 Mbit/s
            # Upload: 50.00 Mbit/s
            cmd = ['speedtest-cli', '--simple']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return {"error": "Error ejecutando speedtest: " + result.stderr}
            
            lines = result.stdout.strip().split('\n')
            data = {}
            for line in lines:
                if 'Ping:' in line:
                    data['ping'] = line.replace('Ping:', '').strip()
                elif 'Download:' in line:
                    data['download'] = line.replace('Download:', '').strip()
                elif 'Upload:' in line:
                    data['upload'] = line.replace('Upload:', '').strip()
            
            return data
        except subprocess.TimeoutExpired:
            return {"error": "El test de velocidad tardó demasiado."}
        except Exception as e:
            return {"error": str(e)}
