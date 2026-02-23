import json
import os
import logging

logger = logging.getLogger("ConfigManager")

class ConfigManager:
    _instance = None
    _config = {}
    CONFIG_FILE = 'config/config.json'

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.load()
        return cls._instance

    def load(self):
        """Carga la configuración desde el archivo JSON."""
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self._config = loaded if loaded is not None else {}
            else:
                logger.warning(f"Config file {self.CONFIG_FILE} not found. Using defaults.")
                self._config = {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self._config = {}

    def save(self):
        """Guarda la configuración actual en el archivo JSON."""
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get(self, key, default=None):
        """Recupera un valor de configuración."""
        return self._config.get(key, default)

    def set(self, key, value):
        """Establece un valor de configuración y guarda."""
        self._config[key] = value
        self.save()

    def get_all(self):
        """Devuelve el diccionario de configuración completo."""
        return self._config
