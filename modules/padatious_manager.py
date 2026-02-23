import os
import logging
from modules.utils import load_json_data

logger = logging.getLogger("PadatiousManager")

try:
    from padatious import IntentContainer
    PADATIOUS_AVAILABLE = True
except ImportError:
    PADATIOUS_AVAILABLE = False
    IntentContainer = None

class PadatiousManager:
    def __init__(self, cache_dir="models/padatious_cache"):
        self.available = PADATIOUS_AVAILABLE
        self.intents = []
        
        if self.available:
            self.container = IntentContainer(cache_dir)
            self.cache_dir = cache_dir
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
        else:
            logger.warning("Padatious no está instalado. NLU estará limitado.")

    def load_intents(self, intents_path='config/intents.json'):
        """Carga intenciones desde JSON y entrena Padatious."""
        if not self.available: return

        data = load_json_data(intents_path, 'intents')
        if not data:
            logger.error("No se cargaron intenciones.")
            return

        self.intents = data
        logger.info(f"Cargando {len(self.intents)} intenciones en Padatious...")

        for intent in self.intents:
            name = intent.get('name')
            triggers = intent.get('triggers', [])
            logger.debug(f"Añadiendo la intención '{name}' con {len(triggers)} triggers.")
            self.container.add_intent(name, triggers)

        # Cargar Itenciones Aprendidas
        learned_path = 'config/learned_intents.json'
        if os.path.exists(learned_path):
            learned_data = load_json_data(learned_path)
            if learned_data:
                logger.info(f"Cargando {len(learned_data)} muestras aprendidas...")
                for intent_name, samples in learned_data.items():
                    # Buscar la intención existente o crear una nueva?
                    # Por ahora, asumimos que estamos añadiendo muestras a intenciones EXISTENTES
                    # o nuevas intenciones que deben ser gestionadas por SkillsService.
                    
                    # Añadir a Padatious
                    self.container.add_intent(intent_name, samples)
                    
                    # También actualizar la lista self.intents para que calc_intent pueda encontrar metadatos
                    # Comprobar si la intención existe
                    existing = next((i for i in self.intents if i['name'] == intent_name), None)
                    if existing:
                        existing['triggers'].extend(samples)
                    else:
                        # Si es una intención completamente nueva, necesitamos metadatos mínimos
                        self.intents.append({
                            'name': intent_name,
                            'triggers': samples,
                            'action': 'responder_simple', # Por defecto
                            'responses': []
                        })

        logger.info("Entrenando módulo Padatious...")
        try:
            self.container.train()
            logger.info("Entrenamiento de Padatious completado.")
        except Exception as e:
            logger.error(f"Entrenamiento de Padatious FALLÓ: {e}")
            self.available = False

    def calc_intent(self, text):
        """
        Devuelve la mejor intención para el texto dado.
        Devuelve un diccionario compatible con nuestro formato NLU.
        """
        match = self.container.calc_intent(text)
        
        if match.name:
            # Encontrar el objeto intención original para obtener respuestas/acciones
            original_intent = next((i for i in self.intents if i['name'] == match.name), None)
            
            return {
                'name': match.name,
                'confidence': match.conf, # 0.0 a 1.0
                'score': int(match.conf * 100),
                'parameters': match.matches, # Entidades extraídas
                'action': original_intent.get('action') if original_intent else None,
                'responses': original_intent.get('responses', []) if original_intent else []
            }
        
        return None
