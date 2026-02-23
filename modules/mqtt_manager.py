import paho.mqtt.client as mqtt
import json
import threading
import time
import logging

logger = logging.getLogger("MQTTManager")

class MQTTManager:
    def __init__(self, event_queue, broker_address="localhost", broker_port=1883):
        self.event_queue = event_queue
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.client = mqtt.Client()
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        self.running = False
        self.connected = False
        self.thread = None

    def start(self):
        """Inicia el bucle MQTT en un hilo de fondo."""
        if self.running: return
        
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        logger.info("MQTTManager started (Background).")

    def _loop(self):
        """Bucle principal que intenta conectarse y reconectarse."""
        while self.running:
            try:
                if not self.connected:
                    logger.info(f"Connecting to MQTT Broker at {self.broker_address}...")
                    self.client.connect(self.broker_address, self.broker_port, 60)
                    self.client.loop_start() # Usa el bucle con hilos de paho
                    self.connected = True
                    
                    # Notificar a la UI del éxito del intento de conexión (opcional)
                    # self.event_queue.put({'type': 'mqtt_status', 'status': 'connected'})
                
                time.sleep(5) # Comprobar estado de conexión periódicamente
                
            except Exception as e:
                logger.warning(f"MQTT Connection failed: {e}. Retrying in 10s...")
                self.connected = False
                time.sleep(10)

    def stop(self):
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
    
    def send_command(self, agent_id, command, params=None):
        """
        Enviar un comando a un agente específico
        
        Args:
            agent_id: Hostname/ID del Agente
            command: Nombre del comando (reboot, shutdown, ping, etc.)
            params: Dict de parámetros opcionales
        Returns:
            ID del comando para seguimiento
        """
        import uuid
        import time as tm
        
        command_id = str(uuid.uuid4())[:8]
        topic = f"wamd/agents/{agent_id}/commands"
        
        payload = {
            "command": command,
            "params": params or {},
            "id": command_id,
            "timestamp": tm.time()
        }
        
        if self.client and self.connected:
            self.client.publish(topic, json.dumps(payload))
            logger.info(f"Sent command '{command}' to agent '{agent_id}' (ID: {command_id})")
            return command_id
        else:
            logger.error("Cannot send command: MQTT client not connected")
            return None

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT Broker!")
            self.connected = True
            # Suscribirse a todos los tópicos de agentes
            client.subscribe("wamd/agents/#")
        else:
            logger.error(f"Failed to connect, return code {rc}")
            self.connected = False

    def on_disconnect(self, client, userdata, rc):
        logger.warning("Disconnected from MQTT Broker.")
        self.connected = False

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            # Formato de Tópico: wamd/agents/{hostname}/{type}
            parts = topic.split('/')
            if len(parts) < 4: return
            
            agent_name = parts[2]
            msg_type = parts[3] # telemetría, alertas, o respuestas
            
            logger.debug(f"MQTT Msg from {agent_name} ({msg_type}): {payload}")
            
            if msg_type == 'alerts':
                # Alertas críticas -> Hablar o Acción
                alert_msg = payload.get('alert') or payload.get('msg')
                if alert_msg:
                    self.event_queue.put({
                        'type': 'mqtt_alert', 
                        'agent': agent_name, 
                        'msg': alert_msg
                    })
            
            elif msg_type == 'telemetry':
                # Telemetría -> Solo notificar a UI (Pop-up)
                # Asumimos que el primer mensaje de telemetría significa "Conectado" si no lo hemos visto recientemente
                # Por ahora, simplemente reenviar todo a la UI a través de event_queue
                self.event_queue.put({
                    'type': 'mqtt_telemetry',
                    'agent': agent_name,
                    'data': payload
                })
            
            elif msg_type == 'responses':
                # Respuestas a comandos -> Reenviar a UI/logs
                self.event_queue.put({
                    'type': 'mqtt_response',
                    'agent': agent_name,
                    'response': payload
                })
                logger.info(f"Command response from {agent_name}: {payload}")
                
        except Exception as e:
            logger.error(f"Error parsing MQTT message: {e}")
