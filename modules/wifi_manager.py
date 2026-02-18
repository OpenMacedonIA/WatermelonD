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
        Scans for available WiFi networks using multiple methods with fallbacks.
        Priority: nmcli → iwlist → iw
        Returns: list of dicts OR dict with 'error' key
        """
        # Method 1: Try nmcli (NetworkManager) - NO rescan to avoid permission issues
        networks = self._scan_nmcli()
        if networks:
            return networks
        
        # Method 2: Try iwlist (wireless-tools)
        networks = self._scan_iwlist()
        if networks:
            return networks
        
        # Method 3: Try iw (modern wireless utility)
        networks = self._scan_iw()
        if networks:
            return networks
        
        # All methods failed
        return {'error': 'No WiFi scanning method available. Install network-manager, wireless-tools, or iw.'}

    def _scan_nmcli(self):
        """Scan using nmcli WITHOUT --rescan to avoid permission issues"""
        try:
            # Remove --rescan yes to avoid sudo requirements
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

                # Format: SSID:SIGNAL:SECURITY
                ssid = parts[0]
                signal = parts[1]
                security = ":".join(parts[2:])  # Security might contain ":"

                if not ssid or ssid in seen_ssids:
                    continue

                seen_ssids.add(ssid)
                networks.append({
                    "ssid": ssid,
                    "signal": int(signal) if signal.isdigit() else 0,
                    "security": security or "Open",
                    "in_use": False  # We don't check this without IN-USE field
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
        """Scan using iwlist (requires sudo)"""
        try:
            interface = self._get_wireless_interface()
            if not interface:
                # Only log once, not every time
                return None

            cmd = ["sudo", "iwlist", interface, "scan"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
            
            networks = []
            seen_ssids = set()
            current_network = {}

            for line in result.stdout.splitlines():
                line = line.strip()
                
                # New cell = new network
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
                
                # Signal quality
                elif "Quality=" in line:
                    match = re.search(r'Quality=(\d+)/(\d+)', line)
                    if match:
                        quality = int(match.group(1))
                        max_quality = int(match.group(2))
                        signal_percent = int((quality / max_quality) * 100)
                        current_network['signal'] = signal_percent
                
                # Encryption
                elif "Encryption key:" in line:
                    if "off" in line.lower():
                        current_network['security'] = "Open"
                    else:
                        current_network['security'] = "WPA/WPA2"  # Default assumption
                
                elif "WPA" in line or "WPA2" in line:
                    current_network['security'] = "WPA2"

            # Add last network
            if current_network and current_network.get('ssid'):
                if current_network['ssid'] not in seen_ssids:
                    networks.append(current_network)

            # Ensure all have required fields
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
        """Scan using iw (modern tool, requires sudo)"""
        try:
            interface = self._get_wireless_interface()
            if not interface:
                # Only log once, not every time
                return None

            cmd = ["sudo", "iw", "dev", interface, "scan"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
            
            networks = []
            seen_ssids = set()
            current_network = {}

            for line in result.stdout.splitlines():
                line = line.strip()
                
                # New BSS = new network
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
                
                # Signal strength
                elif "signal:" in line:
                    match = re.search(r'signal:\s*(-?\d+)', line)
                    if match:
                        dbm = int(match.group(1))
                        # Convert dBm to percentage (rough estimation)
                        # -30 dBm = 100%, -90 dBm = 0%
                        signal_percent = max(0, min(100, (dbm + 90) * 100 // 60))
                        current_network['signal'] = signal_percent
                
                # Security
                elif "WPA" in line or "RSN" in line:
                    current_network['security'] = "WPA2"

            # Add last network
            if current_network and current_network.get('ssid'):
                if current_network['ssid'] not in seen_ssids:
                    networks.append(current_network)

            # Ensure all have required fields
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
        """Get the wireless interface name (wlan0, wlp3s0, etc) - cached"""
        # Return cached result if we already checked
        if self._interface_check_done:
            return self._wireless_interface_cache
        
        try:
            # Try ip link show
            result = subprocess.run(["ip", "link", "show"], capture_output=True, text=True, timeout=5)
            for line in result.stdout.splitlines():
                # Look for interface names starting with 'wl'
                match = re.search(r'^\d+:\s+(wl\w+):', line)
                if match:
                    interface = match.group(1)
                    logger.info(f"Found wireless interface: {interface}")
                    self._wireless_interface_cache = interface
                    self._interface_check_done = True
                    return interface
            
            # Fallback: try common names
            for iface in ['wlan0', 'wlp3s0', 'wlp2s0', 'wlan1']:
                check = subprocess.run(["ip", "link", "show", iface], capture_output=True, timeout=2)
                if check.returncode == 0:
                    logger.info(f"Found wireless interface (fallback): {iface}")
                    self._wireless_interface_cache = iface
                    self._interface_check_done = True
                    return iface
            
            # No interface found - log only ONCE
            logger.warning("No wireless interface found (Ethernet-only system or VM)")
            self._interface_check_done = True
            self._wireless_interface_cache = None
            return None

        except Exception as e:
            logger.error(f"Error finding wireless interface: {e}")
            self._interface_check_done = True
            self._wireless_interface_cache = None
            return None

    def connect(self, ssid, password):
        """
        Connects to a WiFi network using nmcli.
        """
        try:
            logger.info(f"Connecting to {ssid}...")
            cmd = ["nmcli", "device", "wifi", "connect", ssid, "password", password]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Successfully connected to {ssid}")
            return True, "Connected successfully"
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.strip()
            logger.error(f"Failed to connect to {ssid}: {err_msg}")
            return False, err_msg
        except Exception as e:
            return False, str(e)
