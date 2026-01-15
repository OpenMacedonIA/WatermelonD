import os
import sys
import importlib.util
from modules.logger import app_logger

class PluginLoader:
    def __init__(self, core):
        self.core = core
        self.extensions_dir = os.path.join(os.path.dirname(__file__), 'extensions')
        self.loaded_plugins = {}

    def load_plugins(self):
        """Busca y carga plugins .py en la carpeta modules/extensions."""
        if not os.path.exists(self.extensions_dir):
            os.makedirs(self.extensions_dir)
            
        app_logger.info(f"💾 Buscando plugins en: {self.extensions_dir}")
        sys.path.insert(0, self.extensions_dir)

        count = 0
        for filename in os.listdir(self.extensions_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                plugin_name = filename[:-3]
                try:
                    self._load_single_plugin(plugin_name)
                    count += 1
                except Exception as e:
                    app_logger.error(f"❌ Error cargando plugin '{plugin_name}': {e}")
        
        app_logger.info(f"✅ Se han cargado {count} plugins externos.")

    def _load_single_plugin(self, name):
        """Carga un módulo dinámicamente e instancia su clase principal."""
        # 1. Importar módulo
        module_path = os.path.join(self.extensions_dir, f"{name}.py")
        spec = importlib.util.spec_from_file_location(name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 2. Buscar clase que herede de Extension/BaseSkill o tenga un setup()
        # Convención: El plugin debe tener una función 'setup(core)' o una clase 'Extension'
        if hasattr(module, 'setup'):
            app_logger.info(f"🔌 Iniciando plugin '{name}' (Method: setup())...")
            module.setup(self.core)
            self.loaded_plugins[name] = module
        else:
            # Búsqueda de clase convencional
            class_found = False
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and attr_name.endswith('Skill'):
                    app_logger.info(f"🔌 Iniciando plugin '{name}' (Class: {attr_name})...")
                    instance = attr(self.core)
                    self.loaded_plugins[name] = instance
                    class_found = True
                    break
            
            if not class_found:
                app_logger.warning(f"⚠️ El plugin '{name}' no tiene función setup() ni clase *Skill.")

