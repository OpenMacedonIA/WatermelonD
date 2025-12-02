import subprocess
import logging

logger = logging.getLogger("WifiManager")

class WifiManager:
    def __init__(self):
        pass

    def scan(self):
        """
        Scans for available WiFi networks using nmcli.
        Returns a list of dictionaries: [{'ssid': '...', 'signal': 80, 'security': 'WPA2', 'in_use': True}]
        """
        try:
            # -t: terse (script friendly)
            # -f: fields
            cmd = ["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY,BARS", "device", "wifi", "list", "--rescan", "yes"]
            # Add timeout to prevent hanging
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
            
            networks = []
            seen_ssids = set()

            for line in result.stdout.splitlines():
                if not line: continue
                # nmcli escapes colons with backslash in terse mode, but usually fields are separated by colon
                # We need to be careful. The format is IN-USE:SSID:SIGNAL:SECURITY:BARS
                # However, SSID might contain colons. 
                # A safer way is to split by the known field count or use a different separator if possible, 
                # but nmcli default is colon.
                # Let's try simple split first.
                parts = line.split(":")
                
                # If SSID has colons, parts will be > 5. 
                # IN-USE is parts[0]
                # SIGNAL is parts[-3]
                # SECURITY is parts[-2]
                # BARS is parts[-1]
                # SSID is everything in between
                
                if len(parts) < 5: continue

                in_use = parts[0] == "*"
                signal = parts[-3]
                security = parts[-2]
                bars = parts[-1]
                ssid = ":".join(parts[1:-3])

                if not ssid: continue # Skip hidden networks if empty
                if ssid in seen_ssids: continue # Dedup

                seen_ssids.add(ssid)
                networks.append({
                    "ssid": ssid,
                    "signal": int(signal) if signal.isdigit() else 0,
                    "security": security,
                    "bars": bars,
                    "in_use": in_use
                })
            
            # Sort by signal strength
            networks.sort(key=lambda x: x['signal'], reverse=True)
            return networks

        except subprocess.CalledProcessError as e:
            logger.error(f"Error scanning wifi: {e}")
            if e.stderr:
                logger.error(f"nmcli stderr: {e.stderr}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error scanning wifi: {e}")
            return []

    def connect(self, ssid, password):
        """
        Connects to a WiFi network.
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
