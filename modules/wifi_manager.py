import subprocess
import logging
import re

logger = logging.getLogger("WifiManager")

class WifiManager:
    def __init__(self):
        self._wireless_interface_cache = None
        self._interface_check_done = False

    def scan(self):
        """
        Busca redes WiFi disponibles utilizando múltiples métodos con alternativas.
        Prioridad: nmcli → iwlist → iw
        Devuelve: lista de diccionarios O diccionario con la clave 'error'
        """
        # Método 1: Intentar con nmcli (NetworkManager) - SIN re-escaneo para evitar problemas de permisos
        networks = self._scan_nmcli()
        if networks:
            return networks
        
        # Método 2: Intentar con iwlist (wireless-tools)
        networks = self._scan_iwlist()
        if networks:
            return networks
        
        # Método 3: Intentar con iw (utilidad inalámbrica moderna)
        networks = self._scan_iw()
        if networks:
            return networks
        
        # Todos los métodos fallaron
        return {'error': 'No hay método de escaneo WiFi disponible. Instala network-manager, wireless-tools, o iw.'}

    def _scan_nmcli(self):
        """Escaneo usando nmcli SIN --rescan para evitar problemas de permisos"""
        try:
            # Eliminar --rescan yes para evitar requerimientos de sudo
            cmd = ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
            
            networks = []
            seen_ssids = set()

            for line in result.stdout.splitlines():
                if not line:
                    continue
                
                parts = line.split(":")
                if len(parts) < 3:
                    continue

                # Formato: SSID:SEÑAL:SEGURIDAD
                ssid = parts[0]
                signal = parts[1]
                security = ":".join(parts[2:])  # La seguridad puede contener ":"

                if not ssid or ssid in seen_ssids:
                    continue

                seen_ssids.add(ssid)
                networks.append({
                    "ssid": ssid,
                    "signal": int(signal) if signal.isdigit() else 0,
                    "security": security or "Abierta",
                    "in_use": False  # No comprobamos esto sin el campo IN-USE
                })
            
            networks.sort(key=lambda x: x['signal'], reverse=True)
            logger.info(f"nmcli scan found {len(networks)} networks")
            return networks

        except subprocess.TimeoutExpired:
            logger.warning("nmcli scan timed out")
            return None
        except subprocess.CalledProcessError as e:
            logger.warning(f"nmcli scan failed: {e}")
            return None
        except Exception as e:
            logger.warning(f"nmcli scan error: {e}")
            return None

    def _scan_iwlist(self):
        """Escaneo usando iwlist (requiere sudo)"""
        try:
            interface = self._get_wireless_interface()
            if not interface:
                # Solo registrar una vez, no cada vez
                return None

            cmd = ["sudo", "iwlist", interface, "scan"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
            
            networks = []
            seen_ssids = set()
            current_network = {}

            for line in result.stdout.splitlines():
                line = line.strip()
                
                # Nueva celda = nueva red
                if "Cell" in line and "Address:" in line:
                    if current_network and current_network.get('ssid'):
                        if current_network['ssid'] not in seen_ssids:
                            seen_ssids.add(current_network['ssid'])
                            networks.append(current_network)
                    current_network = {}
                
                # ESSID
                elif "ESSID:" in line:
                    match = re.search(r'ESSID:"([^"]*)"', line)
                    if match:
                        current_network['ssid'] = match.group(1)
                
                # Calidad de señal
                elif "Quality=" in line:
                    match = re.search(r'Quality=(\d+)/(\d+)', line)
                    if match:
                        quality = int(match.group(1))
                        max_quality = int(match.group(2))
                        signal_percent = int((quality / max_quality) * 100)
                        current_network['signal'] = signal_percent
                
                # Encriptación
                elif "Encryption key:" in line:
                    if "off" in line.lower():
                        current_network['security'] = "Open"
                    else:
                        current_network['security'] = "WPA/WPA2"  # Suposición predeterminada
                
                elif "WPA" in line or "WPA2" in line:
                    current_network['security'] = "WPA2"

            # Añadir última red
            if current_network and current_network.get('ssid'):
                if current_network['ssid'] not in seen_ssids:
                    networks.append(current_network)

            # Asegurar que todas tienen los campos requeridos
            for net in networks:
                net.setdefault('signal', 0)
                net.setdefault('security', 'Unknown')
                net['in_use'] = False

            networks.sort(key=lambda x: x['signal'], reverse=True)
            logger.info(f"iwlist scan found {len(networks)} networks")
            return networks

        except subprocess.TimeoutExpired:
            logger.warning("iwlist scan timed out")
            return None
        except subprocess.CalledProcessError as e:
            logger.warning(f"iwlist scan failed (may need sudo config): {e}")
            return None
        except Exception as e:
            logger.warning(f"iwlist scan error: {e}")
            return None

    def _scan_iw(self):
        """Escaneo usando iw (herramienta moderna, requiere sudo)"""
        try:
            interface = self._get_wireless_interface()
            if not interface:
                # Solo registrar una vez, no cada vez
                return None

            cmd = ["sudo", "iw", "dev", interface, "scan"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
            
            networks = []
            seen_ssids = set()
            current_network = {}

            for line in result.stdout.splitlines():
                line = line.strip()
                
                # Nuevo BSS = nueva red
                if line.startswith("BSS"):
                    if current_network and current_network.get('ssid'):
                        if current_network['ssid'] not in seen_ssids:
                            seen_ssids.add(current_network['ssid'])
                            networks.append(current_network)
                    current_network = {}
                
                # SSID
                elif line.startswith("SSID:"):
                    ssid = line.replace("SSID:", "").strip()
                    if ssid:
                        current_network['ssid'] = ssid
                
                # Fuerza de la señal
                elif "signal:" in line:
                    match = re.search(r'signal:\s*(-?\d+)', line)
                    if match:
                        dbm = int(match.group(1))
                        # Convertir dBm a porcentaje (estimación aproximada)
                        # -30 dBm = 100%, -90 dBm = 0%
                        signal_percent = max(0, min(100, (dbm + 90) * 100 // 60))
                        current_network['signal'] = signal_percent
                
                # Seguridad
                elif "WPA" in line or "RSN" in line:
                    current_network['security'] = "WPA2"

            # Añadir última red
            if current_network and current_network.get('ssid'):
                if current_network['ssid'] not in seen_ssids:
                    networks.append(current_network)

            # Asegurar que todas tienen los campos requeridos
            for net in networks:
                net.setdefault('signal', 0)
                net.setdefault('security', 'Open')
                net['in_use'] = False

            networks.sort(key=lambda x: x['signal'], reverse=True)
            logger.info(f"iw scan found {len(networks)} networks")
            return networks

        except subprocess.TimeoutExpired:
            logger.warning("iw scan timed out")
            return None
        except subprocess.CalledProcessError as e:
            logger.warning(f"iw scan failed (may need sudo config): {e}")
            return None
        except Exception as e:
            logger.warning(f"iw scan error: {e}")
            return None

    def _get_wireless_interface(self):
        """Obtener el nombre de la interfaz inalámbrica gestionada por NetworkManager - SIN caché"""
        try:
            # Primero intentar con nmcli para asegurarnos de que el dispositivo está manejado (evita 'strictly unmanaged')
            result = subprocess.run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "device"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                wifi_devices = []
                for line in result.stdout.splitlines():
                    parts = line.split(':')
                    if len(parts) >= 3 and parts[1] == 'wifi':
                        device_name, dev_type, state = parts[0], parts[1], parts[2]
                        # Ignorar explícitamente los que están 'unmanaged'
                        if state != 'unmanaged':
                            # Si está conectado o disponible, es candidato
                            wifi_devices.append(device_name)
                
                if wifi_devices:
                    # Devolver el primero que sea válido (por ej. wlo1 en lugar del wlp1s0 no gestionado)
                    selected_iface = wifi_devices[0]
                    logger.info(f"Found managed wireless interface via nmcli: {selected_iface}")
                    return selected_iface

            # Fallback a ip link si nmcli falla
            result_ip = subprocess.run(["ip", "link", "show"], capture_output=True, text=True, timeout=5)
            found_interfaces = []
            for line in result_ip.stdout.splitlines():
                match = re.search(r'^\d+:\s+(wl\w+):', line)
                if match:
                    found_interfaces.append(match.group(1))
            
            if found_interfaces:
                # Priorizar 'wlo1' o interfaces puras sin sub-bus (ej. wlan0, wlo1) sobre wlpXsY (P2P/PCI virtuales)
                for ifc in found_interfaces:
                    if ifc == "wlo1" or ifc == "wlan0":
                        logger.info(f"Found primary wireless interface via ip link: {ifc}")
                        return ifc
                logger.info(f"Found wireless interface via ip link: {found_interfaces[0]}")
                return found_interfaces[0]
            
            # Alternativa: probar nombres comunes
            for iface in ['wlo1', 'wlan0', 'wlp3s0', 'wlp2s0', 'wlan1']:
                check = subprocess.run(["ip", "link", "show", iface], capture_output=True, timeout=2)
                if check.returncode == 0:
                    logger.info(f"Found wireless interface (fallback): {iface}")
                    return iface
            
            logger.warning("No wireless interface found")
            return None

        except Exception as e:
            logger.error(f"Error finding wireless interface: {e}")
            return None

    def connect(self, ssid, password):
        """
        Conecta a una red WiFi usando nmcli.
        """
        try:
            logger.info(f"Connecting to {ssid}...")
            
            iface = self._get_wireless_interface()
            
            if iface:
                # 0. Asegurar que NetworkManager gestione la interfaz (evitar el error 'strictly unmanaged')
                manage_cmd = ["nmcli", "device", "set", iface, "managed", "yes"]
                subprocess.run(manage_cmd, capture_output=True, timeout=5)
            
            # 1. Asegurar un rescan previo para refrescar la caché de NetworkManager
            rescan_cmd = ["nmcli", "device", "wifi", "rescan"]
            if iface:
                rescan_cmd.extend(["ifname", iface])
            subprocess.run(rescan_cmd, capture_output=True, timeout=5)
            
            # 2. Intento normal
            cmd = ["nmcli", "device", "wifi", "connect", ssid, "password", password]
            if iface:
                cmd.extend(["ifname", iface])
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully connected to {ssid} on {iface or 'default'}")
                return True, "Connected successfully"
                
            err_msg = result.stderr.strip() or result.stdout.strip()
            logger.warning(f"Standard connect failed for {ssid}: {err_msg}")
            
            # 3. Fallback: creación de perfil forzado contra fallos de descubrimiento / caché / interfaz errónea
            # Ampliamos para incluir el fallo "No suitable device found" u otros de activación
            if "no se " in err_msg.lower() or "not found" in err_msg.lower() or "no network" in err_msg.lower() or "no suitable device" in err_msg.lower() or "activ" in err_msg.lower():
                logger.info(f"Fallback: Attempting manual profile creation/update for {ssid}...")
                
                check = subprocess.run(['nmcli', '-t', '-f', 'NAME', 'con', 'show'], capture_output=True, text=True)
                profiles = [p.strip() for p in check.stdout.splitlines() if p.strip()]
                
                if ssid in profiles:
                    logger.info(f"Profile {ssid} exists. Updating PSK and binding to {iface or 'default_iface'}...")
                    modify_cmd = [
                        'nmcli', 'con', 'modify', ssid, 
                        '802-11-wireless-security.key-mgmt', 'wpa-psk', 
                        '802-11-wireless-security.psk', password
                    ]
                    if iface:
                        # Asegurar que el perfil solo puede usarse en la interfaz WiFi y no en docker0
                        modify_cmd.extend(['connection.interface-name', iface])
                        
                    subprocess.run(modify_cmd, capture_output=True)
                else:
                    logger.info(f"Creating new profile for {ssid} binding to {iface or 'default'}...")
                    add_cmd = [
                        'nmcli', 'con', 'add',
                        'type', 'wifi',
                        'con-name', ssid,
                        'ssid', ssid,
                        '802-11-wireless-security.key-mgmt', 'wpa-psk',
                        '802-11-wireless-security.psk', password
                    ]
                    if iface:
                        add_cmd.extend(['ifname', iface, 'connection.interface-name', iface])
                        
                    res_add = subprocess.run(add_cmd, capture_output=True, text=True)
                    if res_add.returncode != 0:
                        logger.error(f"Failed to create profile: {res_add.stderr.strip()}")
                        return False, err_msg
                
                # Intentar levantar conexión forzada en la interfaz correcta
                up_cmd = ['nmcli', 'con', 'up', ssid]
                if iface:
                    up_cmd.extend(['ifname', iface])
                    
                res_up = subprocess.run(up_cmd, capture_output=True, text=True)
                
                if res_up.returncode == 0:
                    logger.info(f"Successfully connected to {ssid} via fallback profile")
                    return True, "Connected successfully"
                else:
                    err_msg2 = res_up.stderr.strip() or res_up.stdout.strip()
                    logger.error(f"Fallback connection failed: {err_msg2}")
                    return False, err_msg2

            return False, err_msg
            
        except subprocess.TimeoutExpired:
            return False, "Connection timed out"
        except Exception as e:
            logger.error(f"Exception connecting to {ssid}: {e}")
            return False, str(e)

