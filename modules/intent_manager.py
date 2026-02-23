import logging
from modules.utils import load_json_data
from modules.logger import app_logger

try:
    from rapidfuzz import process, fuzz
    RAPIDFUZZ_DISPONIBLE = True
except ImportError:
    RAPIDFUZZ_DISPONIBLE = False

class IntentManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.intents = []
        self.intent_map = {}
        self.load_intents()

    def load_intents(self):
        """Carga intents desde los ficheros configurados."""
        intents_path = self.config_manager.get('paths', {}).get('intents', 'config/intents.json')
        self.intents = load_json_data(intents_path, 'intents')
        
        # Cargar intents de red y fusionarlos
        network_intents_path = self.config_manager.get('paths', {}).get('network_intents', 'config/network_intents.json')
        network_intents = load_json_data(network_intents_path, 'intents')
        if network_intents:
            self.intents.extend(network_intents)
            app_logger.info(f"Cargados {len(network_intents)} intents de red.")

        # Pre-procesar intenciones para búsqueda rápida
        self.intent_map = {}
        if self.intents:
            for intent in self.intents:
                for trigger in intent.get('triggers', []):
                    self.intent_map[trigger] = intent
        
        # Optimización: Pre-calcular lista de triggers
        self.triggers_list = list(self.intent_map.keys())
        app_logger.info(f"Pre-procesadas {len(self.intent_map)} intenciones para búsqueda rápida.")

    from functools import lru_cache

    @lru_cache(maxsize=128)
    def find_best_intent(self, command_text):
        """Busca la mejor intención usando RapidFuzz y Caché."""
        if not RAPIDFUZZ_DISPONIBLE:
            # Alternativa a búsqueda exacta
            for trigger in self.triggers_list:
                if trigger in command_text:
                    return self.intent_map[trigger]
            return None

        # RapidFuzz Optimizado
        # Usamos token_sort_ratio porque es más robusto al orden y menos permisivo con diferencias de longitud que WRatio
        
        best_intent = None
        best_score = 0
        
        # 1. Intento exacto o muy cercano (Token Sort)
        match = process.extractOne(command_text, self.triggers_list, scorer=fuzz.token_sort_ratio)
        
        if match:
            w_trigger, w_score, _ = match
            
            # Umbral ajustado para mayor flexibilidad
            if w_score >= 80:
                app_logger.info(f"Match Rápido (TokenSort): '{command_text}' vs '{w_trigger}' ({w_score})")
                best_intent = self.intent_map[w_trigger]
                best_score = w_score
            
            # 2. Si falla, probamos PartialRatio pero con penalización por longitud
            # Esto evita que "ip" haga match con "qué día es hoy" solo porque "ip" está dentro (si estuviera)
            elif w_score >= 60:
                 match_partial = process.extractOne(command_text, self.triggers_list, scorer=fuzz.partial_ratio)
                 if match_partial:
                     p_trigger, p_score, _ = match_partial
                     
                     # Penalización por diferencia de longitud
                     len_diff = abs(len(command_text) - len(p_trigger))
                     length_penalty = 0
                     if len_diff > 5:
                         length_penalty = 15 # Penalizar fuertemente si las longitudes son muy distintas
                     
                     final_score = p_score - length_penalty
                     
                     if final_score >= 75:
                         app_logger.info(f"Match Refinado (Partial+Len): '{command_text}' vs '{p_trigger}' ({final_score})")
                         best_intent = self.intent_map[p_trigger]
                         best_score = final_score
        
        # 3. Evaluar resultados
        if best_intent:
            # Copiar intent para no modificar el original en caché
            result_intent = best_intent.copy()
            result_intent['score'] = best_score
            
            if best_score > 80:
                result_intent['confidence'] = 'high'
                return result_intent
            elif best_score > 65:
                result_intent['confidence'] = 'low'
                return result_intent
        
        return None
