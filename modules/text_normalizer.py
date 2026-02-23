import json
import os
import logging
from modules.logger import app_logger

try:
    from rapidfuzz import process, fuzz
    FUZZ_AVAILABLE = True
except ImportError:
    FUZZ_AVAILABLE = False
    app_logger.error("rapidfuzz no instalado. Normalizer desactivado.")

class TextNormalizer:
    """
    Sistema de Normalización de Texto (Fuzzy Matching).
    Corrige errores tipográficos o fonéticos usando un diccionario JSON antes de pasar al Router.
    """
    def __init__(self, dict_path="data/terminos_normalizacion.json", threshold=85):
        self.dict_path = dict_path
        self.threshold = threshold
        self.replacements = {} # Mapa plano: "doker" -> "docker"
        self.canonical_set = set() # Conjunto de palabras correctas para omitir búsqueda rápida (fast-skip)
        
        self.load_dictionary()

    def load_dictionary(self):
        """Carga y aplana el diccionario JSON en un mapa de búsqueda eficiente."""
        self.replacements = {}
        self.canonical_set = set()
        
        if not os.path.exists(self.dict_path):
            app_logger.warning(f"Diccionario de normalización no encontrado: {self.dict_path}")
            return

        try:
            with open(self.dict_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Aplanar estructura: Categoría -> Lista -> Variantes -> Mapa
            for category, items in data.items():
                for item in items:
                    canonical = item.get("canonical", "").lower()
                    variants = item.get("variants", [])
                    
                    self.canonical_set.add(canonical)
                    
                    for variant in variants:
                        # Mapeamos la variante incorrecta a la canónica
                        self.replacements[variant.lower()] = canonical
            
            app_logger.info(f"Normalizer cargado con {len(self.replacements)} términos correctivos.")
            
        except Exception as e:
            app_logger.error(f"Error cargando diccionario de normalización: {e}")

    def normalize(self, text):
        """
        Procesa el texto y corrige palabras mal escritas basándose en el diccionario.
        Optimización: Solo busca correcciones si la palabra no es canónica.
        """
        if not FUZZ_AVAILABLE or not self.replacements:
            return text

        words = text.split()
        normalized_words = []
        
        # Obtenemos lista de variantes conocidas para coincidencia rápida
        known_errors = list(self.replacements.keys())
        
        for word in words:
            word_lower = word.lower()
            
            # 1. Si ya es correcto, pasamos (Ruta rápida)
            if word_lower in self.canonical_set:
                normalized_words.append(word)
                continue
                
            # 2. Si está en la lista exacta de errores (Búsqueda en diccionario - O(1))
            if word_lower in self.replacements:
                corrected = self.replacements[word_lower]
                normalized_words.append(corrected)
                continue
            
            # 3. Coincidencia difusa (Solo si no hubo match exacto)
            # Buscamos si la palabra se parece a algún error conocido (ej. "dokker" -> "doker" -> "docker")
            # O mejor: mapeamos variantes a su canon. 
            # Pero la coincidencia difusa cruzando TODAS las variantes es lento.
            # ESTRATEGIA OPTIMIZADA: Scannear solo si la palabra tiene longitud > 3 (evitar corrección de 'a', 'de')
            
            if len(word_lower) > 3:
                # process.extractOne devuelve (match, score, index)
                match = process.extractOne(word_lower, known_errors, scorer=fuzz.ratio)
                
                if match:
                    best_variant, score, _ = match
                    if score >= self.threshold:
                        canonical = self.replacements[best_variant]
                        app_logger.info(f"Normalizando: '{word}' -> '{canonical}' (Score: {score})")
                        normalized_words.append(canonical)
                        continue

            # Si no hay corrección, mantenemos original
            normalized_words.append(word)

        return " ".join(normalized_words)
