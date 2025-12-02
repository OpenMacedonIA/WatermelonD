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
            logger.warning("Padatious not installed. NLU will be limited.")

    def load_intents(self, intents_path='config/intents.json'):
        """Loads intents from JSON and trains Padatious."""
        if not self.available: return

        data = load_json_data(intents_path, 'intents')
        if not data:
            logger.error("No intents loaded.")
            return

        self.intents = data
        logger.info(f"Loading {len(self.intents)} intents into Padatious...")

        for intent in self.intents:
            name = intent.get('name')
            triggers = intent.get('triggers', [])
            logger.debug(f"Adding intent '{name}' with {len(triggers)} triggers.")
            self.container.add_intent(name, triggers)

        # Load Learned Intents
        learned_path = 'config/learned_intents.json'
        if os.path.exists(learned_path):
            learned_data = load_json_data(learned_path)
            if learned_data:
                logger.info(f"Loading {len(learned_data)} learned samples...")
                for intent_name, samples in learned_data.items():
                    # Find existing intent to merge or create new?
                    # For now, we assume we are adding samples to EXISTING intents
                    # or new intents that must be handled by SkillsService.
                    
                    # Add to Padatious
                    self.container.add_intent(intent_name, samples)
                    
                    # Also update self.intents list so calc_intent can find metadata
                    # Check if intent exists
                    existing = next((i for i in self.intents if i['name'] == intent_name), None)
                    if existing:
                        existing['triggers'].extend(samples)
                    else:
                        # If it's a new intent entirely, we need minimal metadata
                        self.intents.append({
                            'name': intent_name,
                            'triggers': samples,
                            'action': 'responder_simple', # Default
                            'responses': []
                        })

        logger.info("Training Padatious model...")
        try:
            self.container.train()
            logger.info("Padatious training complete.")
        except Exception as e:
            logger.error(f"Padatious training FAILED: {e}")
            self.available = False

    def calc_intent(self, text):
        """
        Returns the best intent for the given text.
        Returns a dict compatible with our NLU format.
        """
        match = self.container.calc_intent(text)
        
        if match.name:
            # Find the original intent object to get responses/actions
            original_intent = next((i for i in self.intents if i['name'] == match.name), None)
            
            return {
                'name': match.name,
                'confidence': match.conf, # 0.0 to 1.0
                'score': int(match.conf * 100),
                'parameters': match.matches, # Extracted entities
                'action': original_intent.get('action') if original_intent else None,
                'responses': original_intent.get('responses', []) if original_intent else []
            }
        
        return None
