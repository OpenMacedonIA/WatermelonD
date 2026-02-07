import os
import logging
import json
import time
import threading
from modules.logger import app_logger

# Fallback dependencies
try:
    import onnxruntime as ort
    from transformers import AutoTokenizer
    import numpy as np
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
    - TTL-based cleanup: Descarga modelos inactivos después de 5 minutos.
    """
    
    # Constants
    MAX_MODELS_IN_MEMORY = 3
    MODEL_TTL_SECONDS = 300  # 5 minutes
    CLEANUP_INTERVAL_SECONDS = 60  # Check every minute
    
    def __init__(self, models_base_path="models", stats_path="data/model_stats.json"):
        self.models_base_path = models_base_path
        self.stats_path = stats_path
        self.sessions = {} # Cache sessions: label -> InferenceSession
        self.tokenizers = {} # Cache tokenizers: label -> AutoTokenizer
        self.last_access = {} # label -> timestamp (para LRU eviction y TTL)
        self.max_models = self.MAX_MODELS_IN_MEMORY
        
        self.stats = self._load_stats()
        self._cleanup_lock = threading.Lock()
        self._stop_cleanup = False
        
        if ONNX_AVAILABLE:
            self._preload_top_models()
            # Start TTL cleanup thread
            self._cleanup_thread = threading.Thread(
                target=self._ttl_cleanup_loop, 
                daemon=True, 
                name="ONNX_TTL_Cleanup"
            )
            self._cleanup_thread.start()

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
    
    def _ttl_cleanup_loop(self):
        """Background thread to unload idle models based on TTL."""
        while not self._stop_cleanup:
            try:
                time.sleep(self.CLEANUP_INTERVAL_SECONDS)
                self._cleanup_expired_models()
            except Exception as e:
                app_logger.error(f"Error in TTL cleanup loop: {e}")
    
    def _cleanup_expired_models(self):
        """Unload models that haven't been accessed within TTL."""
        with self._cleanup_lock:
            now = time.time()
            to_remove = []
            
            for label, last_time in self.last_access.items():
                if now - last_time > self.MODEL_TTL_SECONDS:
                    to_remove.append(label)
            
            for label in to_remove:
                app_logger.info(f"TTL Cleanup: Descargando modelo '{label}' (idle {self.MODEL_TTL_SECONDS}s)")
                del self.sessions[label]
                del self.tokenizers[label]
                del self.last_access[label]


    def _load_model_into_memory(self, label):
        """Carga física del modelo. No gestiona eviction."""
        with self._cleanup_lock:
            if label in self.sessions:
                self.last_access[label] = time.time()
                return

            model_dir = os.path.join(self.models_base_path, label)
            
            # Check for encoder-decoder architecture (T5-style models)
            encoder_file = os.path.join(model_dir, "encoder_model_quantized.onnx")
            decoder_file = os.path.join(model_dir, "decoder_model_quantized.onnx")
            single_model_file = os.path.join(model_dir, "model.onnx")
            
            if not os.path.exists(model_dir):
                raise FileNotFoundError(f"Model directory not found: {model_dir}")
            
            # Determine model type
            if os.path.exists(encoder_file) and os.path.exists(decoder_file):
                app_logger.info(f"Cargando Modelo Encoder-Decoder ({label}) en RAM...")
                tokenizer = AutoTokenizer.from_pretrained(model_dir)
                encoder_session = ort.InferenceSession(encoder_file)
                decoder_session = ort.InferenceSession(decoder_file)
                
                # Store as tuple (encoder, decoder)
                self.sessions[label] = (encoder_session, decoder_session)
                self.tokenizers[label] = tokenizer
                self.last_access[label] = time.time()
                
            elif os.path.exists(single_model_file):
                app_logger.info(f"Cargando Modelo Single ({label}) en RAM...")
                tokenizer = AutoTokenizer.from_pretrained(model_dir)
                session = ort.InferenceSession(single_model_file)
                
                self.sessions[label] = session
                self.tokenizers[label] = tokenizer
                self.last_access[label] = time.time()
            else:
                raise FileNotFoundError(f"No valid ONNX model files found in {model_dir}")

    def _manage_memory(self, target_label):
        """Asegura espacio para el nuevo modelo aplicando política LRU."""
        with self._cleanup_lock:
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
            
            # Check if encoder-decoder (tuple) or single model
            if isinstance(session, tuple):
                # Encoder-Decoder T5-style model
                encoder_session, decoder_session = session
                
                # Tokenize input
                inputs = tokenizer(text, return_tensors="np", padding=True, truncation=True)
                input_ids = inputs["input_ids"].astype("int64")
                attention_mask = inputs["attention_mask"].astype("int64")
                
                # Run encoder
                encoder_outputs = encoder_session.run(
                    None,
                    {
                        "input_ids": input_ids,
                        "attention_mask": attention_mask
                    }
                )
                encoder_hidden_states = encoder_outputs[0]
                
                # Prepare decoder input (start with pad token)
                decoder_input_ids = np.array([[tokenizer.pad_token_id]], dtype=np.int64)
                
                # Simple greedy decoding (max 50 tokens)
                max_length = 50
                generated_ids = []
                for _ in range(max_length):
                    decoder_outputs = decoder_session.run(
                        None,
                        {
                            "input_ids": decoder_input_ids,
                            "encoder_hidden_states": encoder_hidden_states,
                            "encoder_attention_mask": attention_mask
                        }
                    )
                    logits = decoder_outputs[0]
                    next_token_id = logits[0, -1, :].argmax()
                    
                    if next_token_id == tokenizer.eos_token_id:
                        break
                    
                    generated_ids.append(int(next_token_id))
                    decoder_input_ids = np.concatenate([
                        decoder_input_ids,
                        np.array([[next_token_id]], dtype=np.int64)
                    ], axis=1)
                
                command = tokenizer.decode(generated_ids, skip_special_tokens=True)
            else:
                # Single model (legacy path)
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
            import traceback
            app_logger.error(traceback.format_exc())
            raise RuntimeError(f"Error ejecutando modelo {label}: {e}")
