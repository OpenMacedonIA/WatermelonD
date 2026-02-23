import logging
from functools import lru_cache
from modules.logger import app_logger

# Fallback si no está transformers
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    app_logger.error("transformers not installed. DecisionRouter disabled.")

class DecisionRouter:
    """
    Router Semántico Discriminador usando Transformers (Classification Pipeline).
    Clasifica la intención del usuario directamente usando las etiquetas del modelo.
    """
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.enabled = False
        self.classifier = None
        
        self._load_config()
        if self.enabled and TRANSFORMERS_AVAILABLE:
            self._load_model()
            
    def _load_config(self):
        config = self.config_manager.get('decision_router', {})
        self.enabled = config.get('enabled', True)
        self.model_path = config.get('model_path', "models/grape-route")
        self.confidence_threshold = config.get('confidence_threshold', 0.4)

    def _load_model(self):
        """Carga el Pipeline de Clasificación de Texto."""
        try:
            app_logger.info(f"Cargando Router Model (Pipeline) desde: {self.model_path}...")
            # Usamos pipeline para inferencia directa. Asume que el modelo tiene id2label configurado.
            self.classifier = pipeline("text-classification", model=self.model_path, top_k=1)
            app_logger.info("Router Model cargado exitosamente.")
        except Exception as e:
            app_logger.error(f"Error cargando Router Model: {e}")
            self.enabled = False

    @lru_cache(maxsize=128)
    def _predict_cached(self, text):
        """
        Predicción en caché para consultas repetidas.
        Devuelve: tupla (etiqueta, puntuación)
        """
        if not self.enabled or not self.classifier:
            return None, 0.0

        try:
            results = self.classifier(text)
            
            if not results or not results[0]:
                return None, 0.0

            best_result = results[0][0]
            best_label = best_result['label']
            best_score = best_result['score']
            
            return best_label, best_score

        except Exception as e:
            app_logger.error(f"Error en Router Predict: {e}")
            return None, 0.0

    def predict(self, text):
        """
        Clasifica el texto de entrada usando el modelo.
        Retorna: (label, score) o (None, 0.0) si no supera el umbral.
        """
        best_label, best_score = self._predict_cached(text)
        
        if best_label and best_score >= self.confidence_threshold:
            app_logger.info(f"Router Prediction: '{text}' -> {best_label} ({best_score:.2f})")
            return best_label, best_score
        else:
            return "null", best_score

    def clear_cache(self):
        """Limpia la caché de predicción para liberar memoria."""
        self._predict_cached.cache_clear()
        app_logger.info("Router prediction cache cleared")
