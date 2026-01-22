import logging
import time
from modules.logger import app_logger

try:
    from sentence_transformers import SentenceTransformer, util
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    app_logger.error("sentence-transformers not installed. DecisionRouter disabled.")

class DecisionRouter:
    """
    Semantic Router based on Sentence Transformers.
    Categorizes input text into high-level domains to route to the appropriate subsystem.
    """
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.enabled = False
        self.model = None
        self.categories = {}
        self.category_embeddings = {}
        
        self._load_config()
        if self.enabled and TRANSFORMERS_AVAILABLE:
            self._load_model()
            self._init_categories()
            
    def _load_config(self):
        config = self.config_manager.get('decision_router', {})
        self.enabled = config.get('enabled', True)
        self.model_path = config.get('model_path', "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.confidence_threshold = config.get('confidence_threshold', 0.6)

    def _load_model(self):
        """Loads the Sentence Transformer model."""
        try:
            app_logger.info(f"Loading DecisionRouter Model: {self.model_path}...")
            # Use local cache if available, or download
            self.model = SentenceTransformer(self.model_path)
            app_logger.info("DecisionRouter Model loaded successfully.")
        except Exception as e:
            app_logger.error(f"Failed to load DecisionRouter model: {e}")
            self.enabled = False

    def _init_categories(self):
        """
        Defines the categories and their anchor sentences.
        These anchors define the 'center' of each semantic category.
        """
        # User defined categories
        self.categories = {
            "docker": [
                "activa mango para docker",
                "crear contenedor docker",
                "listar imagenes de docker",
                "estado de los contenedores",
                "logs del contenedor",
                "docker ps",
                "reiniciar contenedor"
            ],
            "security": [
                "activa mango seguridad",
                "escanear red nmap",
                "buscar puertos abiertos",
                "analisis de vulnerabilidades",
                "detectar intrusos",
                "ver trafico de red",
                "ciberseguridad"
            ],
            "command": [
                "activa mango consola",
                "ejecuta comando de sistema",
                "abre una terminal",
                "listar archivos del directorio",
                "uso de cpu y memoria",
                "actualizar el sistema",
                "instalar paquete"
            ],
            "time": [
                "qué hora es",
                "dime la hora actual",
                "reloj",
                "tienes hora",
                "que dia es hoy"
            ],
            "calendar": [
                "tengo reuniones hoy",
                "añadir evento al calendario",
                "que tengo en la agenda",
                "cita para mañana",
                "revisar calendario"
            ],
            "search": [
                "busca en internet",
                "búscame informacion sobre",
                "googlear algo",
                "quien es",
                "buscar online"
            ],
            "conversation": [
                "hola",
                "buenos dias",
                "quien eres",
                "como te llamas",
                "cuentame un chiste",
                "hablemos de algo",
                "que opinas de esto",
                "gracias",
                "adios"
            ],
            "entertainment": [
                "pon musica",
                "reproducir video",
                "busca en youtube",
                "pon algo de rock",
                "siguiente cancion",
                "parar musica"
            ]
        }
        
        # Pre-compute embeddings for anchors
        app_logger.info("Computing category embeddings...")
        for category, anchors in self.categories.items():
            self.category_embeddings[category] = self.model.encode(anchors, convert_to_tensor=True)
        app_logger.info(f"DecisionRouter: {len(self.categories)} categories initialized.")

    def predict(self, text):
        """
        Predicts the category of the given text.
        Returns: (category, confidence_score) or (None, 0.0)
        """
        if not self.enabled or not self.model:
            return None, 0.0

        try:
            # Encode input text
            text_embedding = self.model.encode(text, convert_to_tensor=True)
            
            best_category = None
            best_score = 0.0
            
            # Compare with each category cluster
            for category, anchor_embeddings in self.category_embeddings.items():
                # Compute cosine similarities
                cosine_scores = util.cos_sim(text_embedding, anchor_embeddings)
                
                # Take the max score (closest match to ANY anchor in the category)
                max_score = float(cosine_scores.max())
                
                if max_score > best_score:
                    best_score = max_score
                    best_category = category
            
            app_logger.info(f"DecisionRouter Prediction: '{text}' -> {best_category} ({best_score:.2f})")
            
            if best_score >= self.confidence_threshold:
                return best_category, best_score
            else:
                return None, best_score

        except Exception as e:
            app_logger.error(f"DecisionRouter Prediction Error: {e}")
            return None, 0.0
