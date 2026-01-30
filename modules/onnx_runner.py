import os
import logging
import json
import time
from modules.logger import app_logger

# Fallback dependencies
try:
    import onnxruntime as ort
    from transformers import AutoTokenizer
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    app_logger.error("onnxruntime or transformers not installed. SpecificModelRunner disabled.")

class SpecificModelRunner:
    """
    Ejecuta modelos ONNX especializados con gestión inteligente de memoria.
    - Aprende del uso (persistencia de estadísticas).
    - Pre-carga los Top 3 modelos más usados.
    - Limita la RAM a 3 modelos simultáneos (Eviction Policy: LRU).
    """
    def __init__(self, models_base_path="models", stats_path="data/model_stats.json"):
        self.models_base_path = models_base_path
        self.stats_path = stats_path
        self.sessions = {} # Cache sessions: label -> InferenceSession
        self.tokenizers = {} # Cache tokenizers: label -> AutoTokenizer
        self.last_access = {} # label -> timestamp (para LRU eviction)
        self.max_models = 3
        
        self.stats = self._load_stats()
        
        if ONNX_AVAILABLE:
            self._preload_top_models()

    def _load_stats(self):
        try:
            if os.path.exists(self.stats_path):
                with open(self.stats_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            app_logger.warning(f"No se pudieron cargar estadísticas de modelos: {e}")
        return {}

    def _save_stats(self):
        try:
            os.makedirs(os.path.dirname(self.stats_path), exist_ok=True)
            with open(self.stats_path, 'w') as f:
                json.dump(self.stats, f)
        except Exception as e:
            app_logger.error(f"Error guardando estadísticas de modelos: {e}")

    def _preload_top_models(self):
        """Pre-carga los modelos más populares según estadísticas históricas."""
        if not self.stats:
            return

        # Ordenar por uso descendente
        sorted_models = sorted(self.stats.items(), key=lambda x: x[1], reverse=True)
        top_models = [m[0] for m in sorted_models[:self.max_models]]
        
        app_logger.info(f"Pre-cargando modelos frecuentes: {top_models}")
        for label in top_models:
            try:
                self._load_model_into_memory(label)
            except Exception as e:
                app_logger.warning(f"Fallo pre-carga de {label}: {e}")

    def _load_model_into_memory(self, label):
        """Carga física del modelo. No gestiona eviction."""
        if label in self.sessions:
            self.last_access[label] = time.time()
            return

        model_dir = os.path.join(self.models_base_path, label)
        model_file = os.path.join(model_dir, "model.onnx")
        
        if not os.path.exists(model_dir) or not os.path.exists(model_file):
            raise FileNotFoundError(f"Model files not found for {label}")

        app_logger.info(f"Cargando Modelo ({label}) en RAM...")
        tokenizer = AutoTokenizer.from_pretrained(model_dir)
        session = ort.InferenceSession(model_file)
        
        self.sessions[label] = session
        self.tokenizers[label] = tokenizer
        self.last_access[label] = time.time()

    def _manage_memory(self, target_label):
        """Asegura espacio para el nuevo modelo aplicando política LRU."""
        if target_label in self.sessions:
            return

        if len(self.sessions) >= self.max_models:
            # Encontrar el menos usado recientemente (LRU)
            # Excluimos el target_label si estuviera (que no está)
            lru_label = min(self.sessions.keys(), key=lambda k: self.last_access.get(k, 0))
            
            app_logger.info(f"Liberando RAM: Descargando modelo '{lru_label}' (LRU eviction).")
            del self.sessions[lru_label]
            del self.tokenizers[lru_label]
            del self.last_access[lru_label]
            # Force GC optional here, but Python refcounting usually sufficient for classes

    def generate_command(self, text, label):
        if not ONNX_AVAILABLE:
            raise ImportError("Librerías ONNX no disponibles.")

        # 1. Update Stats (Learning)
        self.stats[label] = self.stats.get(label, 0) + 1
        self._save_stats() # Persist learning

        # 2. Manage Memory & Load
        try:
            self._manage_memory(label)
            self._load_model_into_memory(label)
        except Exception as e:
            app_logger.error(f"Error cargando modelo {label}: {e}")
            raise e

        # 3. Inference
        try:
            session = self.sessions[label]
            tokenizer = self.tokenizers[label]
            
            input_ids = tokenizer(text, return_tensors="np").input_ids.astype("int64")
            
            output_names = [output.name for output in session.get_outputs()]
            input_feed = {session.get_inputs()[0].name: input_ids}
            outputs = session.run(output_names, input_feed)
            
            logits = outputs[0] 
            predicted_ids = logits.argmax(axis=-1)
            command = tokenizer.decode(predicted_ids[0], skip_special_tokens=True)
            
            app_logger.info(f"Runner ({label}): '{text}' -> '{command}'")
            return command.strip()

        except Exception as e:
            app_logger.error(f"Error en inferencia ({label}): {e}")
            raise RuntimeError(f"Error ejecutando modelo {label}: {e}")
