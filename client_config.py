import json
import os
import logging


CONFIG_DIR = os.path.join(os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config')), 'org.watermelond.WatermelonDClient')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'client.json')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ClientConfig")

class ClientConfig:
    def __init__(self):
        self.config = {}
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                self.config = {}
        else:
            self.config = {}

    def save(self):
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def is_configured(self):
        return self.get('server_url') is not None
