"""
STT Post-Processor (Post-procesador STT)
Corrección inteligente de errores y coincidencia de comandos para mejorar la precisión del reconocimiento de voz.
"""
import logging
from typing import Optional, List, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger("STTPostProcessor")

class STTPostProcessor:
    """
    Post-procesa la salida STT para corregir errores comunes y mejorar el reconocimiento de comandos.
    """
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        
        # Errores STT comunes en español (minúsculas)
        self.error_corrections = {
            # Palabras de activación (Wake words)
            "neo": ["niño", "león", "teo", "meo", "leo"],
            "tío": ["tio", "tipo", "tito"],
            
            # Comandos comunes
            "enciende": ["en sede", "en ciega", "encienda", "en siente"],
            "apaga": ["a paga", "aparca", "aparcar"],
            "busca": ["buscar", "busco", "buscó"],
            "abre": ["habré", "habre", "abrir"],
            "cierra": ["sierra", "cierro", "cerrar"],
            "reproduce": ["reproduce ce", "reproduce se", "reproducir"],
            "pausa": ["pasar", "pasa", "pausar"],
            "para": ["parra", "para de", "parar"],
            "silencio": ["si lencio", "silenciar", "silencios"],
            
            # Comandos del sistema
            "reinicia": ["reiniciar", "reinício", "reinicia el"],
            "apaga el sistema": ["apaga sistema", "aparca sistema"],
            "suspender": ["suspende", "suspender el"],
            
            # Ubicaciones/Apps
            "spotify": ["spoti fy", "espo tify", "espotifai"],
            "youtube": ["ya tube", "yu tube", "yutú"],
            "navegador": ["navega dor", "navegar"],
            "terminal": ["terminar", "ter minal"],
            
            # Números (contexto de comando)
            "volumen": ["volúmen", "volumen al", "bullen"],
            "cinco": ["sin co", "zinco"],
            "diez": ["dies", "10"],
        }
        
        # Umbral de coincidencia difusa (fuzzy) (0-100)
        self.fuzzy_threshold = 80
        
        # Cargar correcciones personalizadas si están disponibles
        if config_manager:
            custom_corrections = config_manager.get('stt_corrections', {})
            self.error_corrections.update(custom_corrections)
    
    def process(self, text: str) -> str:
        """
        Procesa y corrige la salida STT.
        
        Argumentos:
            text: Texto de salida STT en bruto
            
        Devuelve:
            Texto corregido
        """
        if not text:
            return text
        
        original = text
        
        # 1. Normalizar
        text = self._normalize(text)
        
        # 2. Aplicar correcciones directas
        text = self._apply_corrections(text)
        
        # 3. Correcciones contextuales
        text = self._context_fixes(text)
        
        if text != original:
            logger.info(f"Corrected: '{original}' → '{text}'")
        
        return text
    
    def _normalize(self, text: str) -> str:
        """Normalización básica"""
        # Minúsculas
        text = text.lower().strip()
        
        # Eliminar espacios adicionales
        text = ' '.join(text.split())
        
        # Arreglar errores de puntuación comunes
        text = text.replace('  ', ' ')
        
        return text
    
    def _apply_corrections(self, text: str) -> str:
        """Aplicar correcciones basadas en diccionario"""
        words = text.split()
        corrected = []
        
        for word in words:
            # Comprobar si esta palabra es un error conocido
            corrected_word = word
            for correct, errors in self.error_corrections.items():
                if word in errors:
                    corrected_word = correct
                    logger.debug(f"Corrected word: '{word}' → '{correct}'")
                    break
            corrected.append(corrected_word)
        
        return ' '.join(corrected)
    
    def _context_fixes(self, text: str) -> str:
        """Aplicar correcciones contextuales"""
        # Correcciones de frases comunes
        phrase_corrections = {
            "en sede la": "enciende la",
            "en ciega la": "enciende la",
            "a paga la": "apaga la",
            "buscar internet": "busca en internet",
            "abre te": "abre",
            "cierra el": "cierra",
        }
        
        for wrong, right in phrase_corrections.items():
            if wrong in text:
                text = text.replace(wrong, right)
                logger.debug(f"Fixed phrase: '{wrong}' → '{right}'")
        
        return text
    
    def fuzzy_match_command(self, text: str, known_commands: List[str]) -> Optional[Tuple[str, int]]:
        """
        Encuentra el mejor comando coincidente usando coincidencia difusa (fuzzy).
        
        Argumentos:
            text: Texto de entrada del usuario
            known_commands: Lista de comandos válidos
            
        Devuelve:
            Tupla de (comando_coincidente, puntuacion_similitud) o None
        """
        best_match = None
        best_ratio = 0
        
        for cmd in known_commands:
            ratio = self._similarity(text, cmd)
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = cmd
        
        if best_ratio >= self.fuzzy_threshold:
            logger.info(f"Fuzzy matched: '{text}' → '{best_match}' ({best_ratio}%)")
            return (best_match, int(best_ratio))
        
        return None
    
    def _similarity(self, a: str, b: str) -> float:
        """
        Calcula la proporción de similitud entre dos cadenas (0-100).
        Utiliza SequenceMatcher para obtener resultados precisos.
        """
        return SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100
    
    def add_correction(self, correct: str, error: str):
        """
        Añade una nueva corrección al diccionario.
        
        Argumentos:
            correct: La palabra/frase correcta
            error: El error común a corregir
        """
        if correct not in self.error_corrections:
            self.error_corrections[correct] = []
        
        if error not in self.error_corrections[correct]:
            self.error_corrections[correct].append(error)
            logger.info(f"Added correction: '{error}' → '{correct}'")
    
    def remove_wake_word(self, text: str, wake_words: List[str]) -> str:
        """
        Elimina la palabra de activación del texto si está presente.
        
        Argumentos:
            text: Texto de entrada
            wake_words: Lista de palabras de activación a eliminar
            
        Devuelve:
            Texto con la palabra de activación eliminada
        """
        text_lower = text.lower()
        
        for ww in wake_words:
            ww_lower = ww.lower()
            if text_lower.startswith(ww_lower):
                # Eliminar desde el principio
                text = text[len(ww):].strip()
                logger.debug(f"Removed wake word: '{ww}'")
                break
            elif ww_lower in text_lower:
                # Eliminar desde cualquier lugar
                text = text.replace(ww, "").strip()
                logger.debug(f"Removed wake word: '{ww}' (from middle)")
                break
        
        return text


# Instancia Singleton
_processor_instance = None

def get_processor(config_manager=None):
    """Obtener instancia singleton de STTPostProcessor"""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = STTPostProcessor(config_manager)
    return _processor_instance


if __name__ == "__main__":
    # Probar el post-procesador
    logging.basicConfig(level=logging.DEBUG)
    
    proc = STTPostProcessor()
    
    test_cases = [
        "niño enciende la luz",
        "tio a paga la luz",
        "buscar internet python tutorial",
        "en sede la televisión",
        "reproduce spoti fy",
    ]
    
    print("🧪 Testing STT Post-Processor\n")
    for test in test_cases:
        result = proc.process(test)
        print(f"Input:  {test}")
        print(f"Output: {result}\n")
    
    # Probar coincidencia difusa
    commands = [
        "enciende la luz",
        "apaga la luz",
        "busca en internet",
        "reproduce música",
    ]
    
    fuzzy_tests = [
        "en siente la luz",
        "a paga luz",
        "busco internet",
    ]
    
    print("\n Testing Fuzzy Command Matching\n")
    for test in fuzzy_tests:
        match = proc.fuzzy_match_command(test, commands)
        if match:
            cmd, score = match
            print(f"'{test}' → '{cmd}' ({score}%)")
        else:
            print(f"'{test}' → No match found")
