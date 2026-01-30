import logging
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
        self.model_path = config.get('model_path', "models/microsoft/Multilingual-MiniLM-L12-H384")
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

    def predict(self, text):
        """
        Clasifica el texto de entrada usando el modelo.
        Retorna: (label, score) o (None, 0.0) si no supera el umbral.
        """
        if not self.enabled or not self.classifier:
            return None, 0.0

        try:
            # Pipeline retorna una lista de dicts [{'label': 'LABEL', 'score': 0.99}]
            # Con top_k=1 retorna lista de listas? No, default es lista de dicts para 1 input.
            results = self.classifier(text)
            
            # results es [{'label': 'malbec', 'score': 0.98}]
            if not results:
                return None, 0.0

            best_result = results[0]
            best_label = best_result['label']
            best_score = best_result['score']
            
            app_logger.info(f"Router Prediction: '{text}' -> {best_label} ({best_score:.2f})")
            
            if best_score >= self.confidence_threshold:
                return best_label, best_score
            else:
                return "null", best_score

        except Exception as e:
            app_logger.error(f"Error en Router Predict: {e}")
            return None, 0.0
