import logging
from modules.utils import load_json_data

class SentimentManager:
    def __init__(self):
        self.data = load_json_data('resources/nlp/sentiment.json', default={})
        self.positive_words = set(self.data.get('positive', []))
        self.negative_words = set(self.data.get('negative', []))
        self.angry_words = set(self.data.get('angry', []))

    def analyze(self, text):
        """
        Analiza el texto y devuelve una tupla (sentimiento, score).
        Sentimientos: 'neutral', 'positive', 'negative', 'angry'.
        """
        if not text:
            return 'neutral', 0

        text_lower = text.lower()
        words = text_lower.split()

        score = 0
        angry_count = 0

        for word in words:
            # Limpieza básica de puntuación
            clean_word = word.strip(".,!¡?¿")
            
            if clean_word in self.angry_words:
                angry_count += 1
                score -= 2
            elif clean_word in self.negative_words:
                score -= 1
            elif clean_word in self.positive_words:
                score += 1

        # Determinación del estado
        if angry_count > 0:
            return 'angry', score
        elif score > 0:
            return 'positive', score
        elif score < 0:
            return 'negative', score
        else:
            return 'neutral', score
