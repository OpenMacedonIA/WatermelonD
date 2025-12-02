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
        """Starts the MQTT loop in a background thread."""
        if self.running: return
        
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        logger.info("MQTTManager started (Background).")

    def _loop(self):
        """Main loop that tries to connect and reconnect."""
        while self.running:
            try:
                if not self.connected:
                    logger.info(f"Connecting to MQTT Broker at {self.broker_address}...")
                    self.client.connect(self.broker_address, self.broker_port, 60)
                    self.client.loop_start() # Use paho's threaded loop
                    self.connected = True
                    
                    # Notify UI of connection attempt success (optional)
                    # self.event_queue.put({'type': 'mqtt_status', 'status': 'connected'})
                
                time.sleep(5) # Check connection status periodically
                
            except Exception as e:
                logger.warning(f"MQTT Connection failed: {e}. Retrying in 10s...")
                self.connected = False
                time.sleep(10)

    def stop(self):
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT Broker!")
            self.connected = True
            # Subscribe to all agent topics
            client.subscribe("tio/agents/#")
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
            
            # Topic format: tio/agents/{hostname}/{type}
            parts = topic.split('/')
            if len(parts) < 4: return
            
            agent_name = parts[2]
            msg_type = parts[3] # telemetry or alerts
            
            logger.debug(f"MQTT Msg from {agent_name} ({msg_type}): {payload}")
            
            if msg_type == 'alerts':
                # Critical alerts -> Speak or Action
                alert_msg = payload.get('alert') or payload.get('msg')
                if alert_msg:
                    self.event_queue.put({
                        'type': 'mqtt_alert', 
                        'agent': agent_name, 
                        'msg': alert_msg
                    })
            
            elif msg_type == 'telemetry':
                # Telemetry -> Just notify UI (Pop-up)
                # We assume the first telemetry message means "Connected" if we haven't seen it recently
                # For now, just forward everything to UI via event_queue
                self.event_queue.put({
                    'type': 'mqtt_telemetry',
                    'agent': agent_name,
                    'data': payload
                })
                
        except Exception as e:
            logger.error(f"Error parsing MQTT message: {e}")
