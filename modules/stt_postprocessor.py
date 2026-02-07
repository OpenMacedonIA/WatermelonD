"""
STT Post-Processor
Intelligent error correction and command matching for improved speech recognition accuracy.
"""
import logging
from typing import Optional, List, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger("STTPostProcessor")

class STTPostProcessor:
    """
    Post-processes STT output to correct common errors and improve command recognition.
    """
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        
        # Common Spanish STT errors (lowercase)
        self.error_corrections = {
            # Wake words
            "neo": ["niño", "león", "teo", "meo", "leo"],
            "tío": ["tio", "tipo", "tito"],
            
            # Common commands
            "enciende": ["en sede", "en ciega", "encienda", "en siente"],
            "apaga": ["a paga", "aparca", "aparcar"],
            "busca": ["buscar", "busco", "buscó"],
            "abre": ["habré", "habre", "abrir"],
            "cierra": ["sierra", "cierro", "cerrar"],
            "reproduce": ["reproduce ce", "reproduce se", "reproducir"],
            "pausa": ["pasar", "pasa", "pausar"],
            "para": ["parra", "para de", "parar"],
            "silencio": ["si lencio", "silenciar", "silencios"],
            
            # System commands
            "reinicia": ["reiniciar", "reinício", "reinicia el"],
            "apaga el sistema": ["apaga sistema", "aparca sistema"],
            "suspender": ["suspende", "suspender el"],
            
            # Locations/Apps
            "spotify": ["spoti fy", "espo tify", "espotifai"],
            "youtube": ["ya tube", "yu tube", "yutú"],
            "navegador": ["navega dor", "navegar"],
            "terminal": ["terminar", "ter minal"],
            
            # Numbers (command context)
            "volumen": ["volúmen", "volumen al", "bullen"],
            "cinco": ["sin co", "zinco"],
            "diez": ["dies", "10"],
        }
        
        # Fuzzy matching threshold (0-100)
        self.fuzzy_threshold = 80
        
        # Load custom corrections if available
        if config_manager:
            custom_corrections = config_manager.get('stt_corrections', {})
            self.error_corrections.update(custom_corrections)
    
    def process(self, text: str) -> str:
        """
        Process and correct STT output.
        
        Args:
            text: Raw STT output text
            
        Returns:
            Corrected text
        """
        if not text:
            return text
        
        original = text
        
        # 1. Normalize
        text = self._normalize(text)
        
        # 2. Apply direct corrections
        text = self._apply_corrections(text)
        
        # 3. Contextual fixes
        text = self._context_fixes(text)
        
        if text != original:
            logger.info(f"Corrected: '{original}' → '{text}'")
        
        return text
    
    def _normalize(self, text: str) -> str:
        """Basic normalization"""
        # Lowercase
        text = text.lower().strip()
        
        # Remove extra spaces
        text = ' '.join(text.split())
        
        # Fix common punctuation errors
        text = text.replace('  ', ' ')
        
        return text
    
    def _apply_corrections(self, text: str) -> str:
        """Apply dictionary-based corrections"""
        words = text.split()
        corrected = []
        
        for word in words:
            # Check if this word is a known error
            corrected_word = word
            for correct, errors in self.error_corrections.items():
                if word in errors:
                    corrected_word = correct
                    logger.debug(f"Corrected word: '{word}' → '{correct}'")
                    break
            corrected.append(corrected_word)
        
        return ' '.join(corrected)
    
    def _context_fixes(self, text: str) -> str:
        """Apply contextual corrections"""
        # Common phrase fixes
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
        Find best matching command using fuzzy matching.
        
        Args:
            text: User input text
            known_commands: List of valid commands
            
        Returns:
            Tuple of (matched_command, similarity_score) or None
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
        Calculate similarity ratio between two strings (0-100).
        Uses SequenceMatcher for accurate results.
        """
        return SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100
    
    def add_correction(self, correct: str, error: str):
        """
        Add a new correction to the dictionary.
        
        Args:
            correct: The correct word/phrase
            error: The common error to correct
        """
        if correct not in self.error_corrections:
            self.error_corrections[correct] = []
        
        if error not in self.error_corrections[correct]:
            self.error_corrections[correct].append(error)
            logger.info(f"Added correction: '{error}' → '{correct}'")
    
    def remove_wake_word(self, text: str, wake_words: List[str]) -> str:
        """
        Remove wake word from text if present.
        
        Args:
            text: Input text
            wake_words: List of wake words to remove
            
        Returns:
            Text with wake word removed
        """
        text_lower = text.lower()
        
        for ww in wake_words:
            ww_lower = ww.lower()
            if text_lower.startswith(ww_lower):
                # Remove from start
                text = text[len(ww):].strip()
                logger.debug(f"Removed wake word: '{ww}'")
                break
            elif ww_lower in text_lower:
                # Remove from anywhere
                text = text.replace(ww, "").strip()
                logger.debug(f"Removed wake word: '{ww}' (from middle)")
                break
        
        return text


# Singleton instance
_processor_instance = None

def get_processor(config_manager=None):
    """Get singleton instance of STTPostProcessor"""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = STTPostProcessor(config_manager)
    return _processor_instance


if __name__ == "__main__":
    # Test the post-processor
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
    
    # Test fuzzy matching
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
    
    print("\n🎯 Testing Fuzzy Command Matching\n")
    for test in fuzzy_tests:
        match = proc.fuzzy_match_command(test, commands)
        if match:
            cmd, score = match
            print(f"'{test}' → '{cmd}' ({score}%)")
        else:
            print(f"'{test}' → No match found")
