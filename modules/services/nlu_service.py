import logging
import os
import sys
import json

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from modules.bus_client import BusClient
from modules.config_manager import ConfigManager
from modules.intent_manager import IntentManager
from modules.padatious_manager import PadatiousManager

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [NLU] - %(levelname)s - %(message)s')
logger = logging.getLogger("NLUService")

class NLUService:
    def __init__(self):
        self.bus = BusClient(name="NLUService")
        self.config_manager = ConfigManager()
        
        # Initialize Engines
        self.intent_manager = IntentManager(self.config_manager) # Legacy / Fallback
        self.padatious_manager = PadatiousManager()
        
        # Train Padatious
        self.padatious_manager.load_intents()
        
        self.bus.connect()
        self.bus.on('recognizer_loop:utterance', self.handle_utterance)

    def handle_utterance(self, message):
        """
        Handle utterance from Voice Service.
        Message data: {"utterances": ["text"]}
        """
        data = message.get('data', {})
        utterances = data.get('utterances', [])
        
        if not utterances:
            return

        text = utterances[0]
        logger.info(f"Processing: {text}")
        
        best_intent = None
        
        # 1. Try Padatious (Primary)
        if self.padatious_manager.available:
            pad_result = self.padatious_manager.calc_intent(text)
            if pad_result and pad_result['confidence'] > 0.5:
                logger.info(f"Padatious Match: {pad_result['name']} ({pad_result['score']}%)")
                best_intent = pad_result
        
        # 2. Fallback to RapidFuzz (Legacy) if Padatious failed or low confidence
        if not best_intent:
            legacy_result = self.intent_manager.find_best_intent(text)
            if legacy_result:
                logger.info(f"Legacy Match: {legacy_result['name']} ({legacy_result['score']}%)")
                best_intent = legacy_result

        # 3. Emit Result
        if best_intent:
            intent_name = best_intent.get('name')
            confidence = best_intent.get('confidence', 'high')
            score = best_intent.get('score', 0)
            
            # Emit Intent Event
            payload = {
                "utterance": text,
                "intent_type": intent_name,
                "confidence": confidence,
                "score": score,
                "parameters": best_intent.get('parameters', {})
            }
            
            self.bus.emit(intent_name, payload)
            
        else:
            logger.info("No intent found.")
            self.bus.emit("recognizer_loop:unknown_intent", {"utterance": text})
            self.log_to_inbox(text)

    def log_to_inbox(self, text):
        """Saves unknown utterance to inbox for review."""
        inbox_path = 'data/nlu_inbox.json'
        try:
            data = []
            if os.path.exists(inbox_path):
                with open(inbox_path, 'r') as f:
                    data = json.load(f)
            
            # Avoid duplicates
            if text not in [i['text'] for i in data]:
                data.append({
                    'text': text,
                    'timestamp': os.popen('date -Iseconds').read().strip(),
                    'status': 'new'
                })
                
                # Keep last 50
                if len(data) > 50:
                    data = data[-50:]
                    
                with open(inbox_path, 'w') as f:
                    json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Error logging to inbox: {e}")

    def run(self):
        logger.info("NLU Service Started")
        self.bus.run_forever()

if __name__ == "__main__":
    service = NLUService()
    service.run()
