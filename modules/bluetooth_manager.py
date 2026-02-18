import socket
import threading
import time
import json
import logging
import select

logger = logging.getLogger("BluetoothManager")

class BluetoothManager:
    def __init__(self, event_queue, port=1):
        self.event_queue = event_queue
        self.port = port
        self.server_sock = None
        self.running = False
        self.thread = None
        self.clients = []

    def start(self):
        """Starts the Bluetooth RFCOMM server in a background thread."""
        if self.running: return

        try:
            self.server_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self.server_sock.bind((socket.BDADDR_ANY, self.port)) # Retaining original BDADDR_ANY as self.host is not defined in __init__
            self.server_sock.listen(1)
            self.server_sock.settimeout(1.0) # Timeout para aceptar conexiones y no bloquear
            
            # Get port info
            # port = self.server_sock.getsockname()[1] # This line was removed in the diff
            logger.info(f"Bluetooth Server listening on RFCOMM channel {self.port}") # Modified log message

            self.running = True
            self.thread = threading.Thread(target=self._accept_loop, daemon=True)
            self.thread.start()
            
        except AttributeError:
            logger.info("Bluetooth not supported: socket.AF_BLUETOOTH missing. (Bluetooth disabled)")
            self.server_sock = None
            return
        except Exception as e:
            logger.error(f"Failed to start Bluetooth Server: {e}")
            self.server_sock = None
            self.running = False # Keep original running = False
            return

    def _accept_loop(self):
        """Accepts incoming Bluetooth connections."""
        while self.running:
            try:
                # Use select to make accept non-blocking-ish or handle timeout
                readable, _, _ = select.select([self.server_sock], [], [], 2.0)
                if self.server_sock in readable:
                    client_sock, client_info = self.server_sock.accept()
                    logger.info(f"Accepted Bluetooth connection from {client_info}")
                    
                    client_thread = threading.Thread(target=self._client_handler, args=(client_sock, client_info), daemon=True)
                    client_thread.start()
                    self.clients.append(client_sock)
                    
            except Exception as e:
                if self.running:
                    logger.error(f"Error in Bluetooth accept loop: {e}")
                time.sleep(1)

    def _client_handler(self, client_sock, client_info):
        """Handles data from a connected client."""
        buffer = ""
        try:
            while self.running:
                data = client_sock.recv(1024)
                if not data:
                    break
                
                buffer += data.decode('utf-8')
                
                # Process complete lines (JSONs)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        self._process_message(line.strip(), client_info)
                        
        except Exception as e:
            logger.warning(f"Bluetooth client {client_info} disconnected or error: {e}")
        finally:
            client_sock.close()
            if client_sock in self.clients:
                self.clients.remove(client_sock)
            logger.info(f"Bluetooth connection closed: {client_info}")

    def _process_message(self, raw_msg, client_info):
        """Parses JSON and injects into event queue."""
        try:
            payload = json.loads(raw_msg)
            # Normalize to match MQTT structure
            # Expected payload from agent: {"agent": "name", "type": "telemetry|alert", "data": {...}}
            
            agent = payload.get('agent', f"BT_{client_info[0]}")
            msg_type = payload.get('type', 'telemetry')
            data = payload.get('data', {})
            
            logger.debug(f"BT Msg from {agent}: {payload}")

            if msg_type == 'alert':
                self.event_queue.put({
                    'type': 'mqtt_alert', # Reuse MQTT alert type for compatibility
                    'agent': agent,
                    'msg': data.get('msg', 'Alert received via Bluetooth')
                })
            elif msg_type == 'telemetry':
                self.event_queue.put({
                    'type': 'mqtt_telemetry', # Reuse MQTT telemetry type
                    'agent': agent,
                    'data': data
                })
                
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from Bluetooth: {raw_msg}")

    def stop(self):
        self.running = False
        if self.server_sock:
            self.server_sock.close()
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        logger.info("BluetoothManager stopped.")
