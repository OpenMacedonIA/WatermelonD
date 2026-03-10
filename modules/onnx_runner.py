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
    
    # Prefijos de tarea para modelos T5 (deben coincidir con el prefijo de entrenamiento)
    # Si un modelo no está en este mapa, no se añade prefijo.
    MODEL_TASK_PREFIXES = {
        "malbec":      "translate Spanish to Bash: ",
        "syrah":       "translate Spanish to Bash: ",
        "pinot":       "translate Spanish to Bash: ",
        "grape-route": "translate Spanish to Bash: ",
        "chardonnay":  "translate Spanish to Bash: ",
    }

    # Tokenizer base para modelos que no incluyen archivos de tokenizer propios.
    # Los modelos Grape están fine-tuned sobre t5-small (vocab_size=32100).
    MODEL_TOKENIZER_BASE = {
        "malbec":      "t5-small",
        "syrah":       "t5-small",
        "pinot":       "t5-small",
        "grape-route": "t5-small",
        "chardonnay":  "t5-small",
    }
    
    # Constants
    MAX_MODELS_IN_MEMORY = 3
    MODEL_TTL_SECONDS = 300  # 5 minutes
    CLEANUP_INTERVAL_SECONDS = 60  # Check every minute
    
    def __init__(self, models_base_path="models", stats_path="data/model_stats.json"):
        self.models_base_path = models_base_path
        self.stats_path = stats_path
        # Caché de sesiones: etiqueta -> InferenceSession
        self.sessions = {}   # Caché de sesiones: etiqueta -> InferenceSession ó (encoder, decoder)
        self.tokenizers = {} # Caché de tokenizadores: etiqueta -> AutoTokenizer
        self.last_access = {} # etiqueta -> marca de tiempo (para desalojo LRU y TTL)
        self.max_models = self.MAX_MODELS_IN_MEMORY
        
        self.stats = self._load_stats()
        self._cleanup_lock = threading.Lock()
        self._stop_cleanup = False
        
        if ONNX_AVAILABLE:
            self._preload_top_models()
            # Iniciar hilo de limpieza TTL
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
        """Hilo en segundo plano para descargar modelos inactivos basado en TTL."""
        while not self._stop_cleanup:
            try:
                time.sleep(self.CLEANUP_INTERVAL_SECONDS)
                self._cleanup_expired_models()
            except Exception as e:
                app_logger.error(f"Error in TTL cleanup loop: {e}")
    
    def _cleanup_expired_models(self):
        """Descarga los modelos al que no se ha accedido dentro del tiempo TTL."""
        with self._cleanup_lock:
            now = time.time()
            to_remove = []
            
            for label, last_time in self.last_access.items():
                if now - last_time > self.MODEL_TTL_SECONDS:
                    to_remove.append(label)
            
            for label in to_remove:
                app_logger.info(f"Limpieza TTL: Descargando modelo '{label}' (idle {self.MODEL_TTL_SECONDS}s)")
                # Usar pop() con default None para evitar KeyError en race conditions
                # (el hilo de inferencia pudo cargar el modelo justo antes del cleanup)
                self.sessions.pop(label, None)
                self.tokenizers.pop(label, None)
                self.last_access.pop(label, None)


    def _load_model_into_memory(self, label):
        """Carga física del modelo en memoria. No gestiona eviction."""
        with self._cleanup_lock:
            if label in self.sessions:
                self.last_access[label] = time.time()
                return

            model_dir = os.path.join(self.models_base_path, label)

            if not os.path.exists(model_dir):
                raise FileNotFoundError(f"Model directory not found: {model_dir}")

            # --- Tokenizer ---
            # Comprobar si el directorio tiene archivos de tokenizer propios
            has_local_tokenizer = any(
                os.path.exists(os.path.join(model_dir, f))
                for f in ['tokenizer.json', 'spiece.model', 'tokenizer_config.json']
            )
            if has_local_tokenizer:
                tokenizer = AutoTokenizer.from_pretrained(model_dir)
                app_logger.info(f"Tokenizer cargado desde directorio local: {model_dir}")
            else:
                # Buscar tokenizer en modelos hermanos locales antes de intentar descarga
                sibling_models = ["chardonnay", "pinot", "syrah", "malbec"]
                tok_loaded = False
                for sibling in sibling_models:
                    if sibling == label:
                        continue
                    sibling_dir = os.path.join(self.models_base_path, sibling)
                    if os.path.exists(os.path.join(sibling_dir, 'tokenizer.json')):
                        try:
                            tokenizer = AutoTokenizer.from_pretrained(sibling_dir)
                            app_logger.info(f"Tokenizer para '{label}' cargado desde hermano local: {sibling_dir}")
                            tok_loaded = True
                            break
                        except Exception:
                            continue
                if not tok_loaded:
                    tok_base = self.MODEL_TOKENIZER_BASE.get(label, 't5-small')
                    app_logger.info(f"Sin tokenizer local para '{label}', descargando base: {tok_base}")
                    tokenizer = AutoTokenizer.from_pretrained(tok_base)

            # --- Archivos ONNX ---
            encoder_file     = os.path.join(model_dir, "encoder_model_quantized.onnx")
            decoder_file     = os.path.join(model_dir, "decoder_model_quantized.onnx")
            dec_past_file    = os.path.join(model_dir, "decoder_with_past_model_quantized.onnx")
            # Fallback a no-quantized si no hay cuantizados
            if not os.path.exists(encoder_file):
                encoder_file  = os.path.join(model_dir, "encoder_model.onnx")
            if not os.path.exists(decoder_file):
                decoder_file  = os.path.join(model_dir, "decoder_model.onnx")
            if not os.path.exists(dec_past_file):
                dec_past_file = os.path.join(model_dir, "decoder_with_past_model.onnx")
            single_model_file = os.path.join(model_dir, "model.onnx")

            sess_opts = ort.SessionOptions()
            sess_opts.log_severity_level = 3  # Suprimir warnings verbosos de ONNX

            if os.path.exists(encoder_file) and os.path.exists(decoder_file):
                app_logger.info(f"Cargando Modelo Encoder-Decoder ({label}) en RAM...")
                encoder_session  = ort.InferenceSession(encoder_file,  sess_options=sess_opts)
                decoder_session  = ort.InferenceSession(decoder_file,  sess_options=sess_opts)
                dec_past_session = ort.InferenceSession(dec_past_file, sess_options=sess_opts) \
                    if os.path.exists(dec_past_file) else None

                # Tupla (encoder, decoder_init, decoder_with_past)
                self.sessions[label] = (encoder_session, decoder_session, dec_past_session)
                self.tokenizers[label] = tokenizer
                self.last_access[label] = time.time()

            elif os.path.exists(single_model_file):
                app_logger.info(f"Cargando Modelo Single ({label}) en RAM...")
                session = ort.InferenceSession(single_model_file, sess_options=sess_opts)
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
                # Forzar GC opcional aquí, pero el recuento de referencias de Python suele ser suficiente para clases

    def generate_command(self, text, label):
        if not ONNX_AVAILABLE:
            raise ImportError("Librerías ONNX no disponibles.")

        # 1. Actualizar Estadísticas (Aprendizaje)
        self.stats[label] = self.stats.get(label, 0) + 1
        self._save_stats() # Persistir aprendizaje

        # 2. Añadir prefijo de tarea si el modelo lo requiere
        # Los modelos T5 fine-tuned necesitan el prefijo con el que fueron entrenados
        task_prefix = self.MODEL_TASK_PREFIXES.get(label, "")
        if task_prefix and not text.startswith(task_prefix):
            text = task_prefix + text
            app_logger.info(f"Prefijo de tarea aplicado: '{task_prefix[:40]}...'")

        # 3. Gestionar Memoria y Carga
        try:
            self._manage_memory(label)
            self._load_model_into_memory(label)
        except Exception as e:
            app_logger.error(f"Error cargando modelo {label}: {e}")
            raise e

        # 4. Inferencia
        try:
            session = self.sessions[label]
            tokenizer = self.tokenizers[label]
            
            # Comprobar si es un encoder-decoder (tupla) o un solo modelo
            if isinstance(session, tuple):
                # Modelo Encoder-Decoder tipo T5 (exportado con optimum/ORTModelForSeq2SeqLM)
                encoder_session, decoder_session, dec_past_session = session

                # --- Tokenizar ---
                inputs = tokenizer(
                    text, return_tensors="np",
                    padding=True, truncation=True, max_length=512
                )
                input_ids      = inputs["input_ids"].astype("int64")
                attention_mask = inputs["attention_mask"].astype("int64")
                app_logger.debug(f"input_ids shape: {input_ids.shape}, tokens[:6]: {input_ids[0][:6].tolist()}")

                # --- Encoder ---
                enc_out               = encoder_session.run(None, {"input_ids": input_ids, "attention_mask": attention_mask})
                encoder_hidden_states = enc_out[0]

                # --- Paso 1: decoder_model sin past (token de inicio = 0) ---
                dec1_out = decoder_session.run(
                    None,
                    {
                        "input_ids":              np.array([[0]], dtype=np.int64),
                        "encoder_hidden_states":  encoder_hidden_states,
                        "encoder_attention_mask": attention_mask,
                    }
                )
                # Mapa nombre->tensor para todos los present.* de este paso
                dec_out_names = [o.name for o in decoder_session.get_outputs()]
                present_map   = {dec_out_names[i]: dec1_out[i] for i in range(1, len(dec_out_names))}

                logits        = dec1_out[0]
                next_token_id = int(logits[0, -1, :].argmax())
                app_logger.debug(f"Primer token: {next_token_id} ('{tokenizer.decode([next_token_id])}') eos={tokenizer.eos_token_id}")

                generated_ids = []

                # --- Loop de generación con KV-cache ---
                for step in range(128):
                    if next_token_id == tokenizer.eos_token_id:
                        break
                    generated_ids.append(next_token_id)

                    if dec_past_session is None:
                        # Fallback: re-alimentar todos los tokens acumulados
                        all_ids = [0] + generated_ids
                        dec_out = decoder_session.run(
                            None,
                            {
                                "input_ids":              np.array([all_ids], dtype=np.int64),
                                "encoder_hidden_states":  encoder_hidden_states,
                                "encoder_attention_mask": attention_mask,
                            }
                        )
                        logits = dec_out[0]
                        dec_out_names2 = [o.name for o in decoder_session.get_outputs()]
                        present_map = {dec_out_names2[i]: dec_out[i] for i in range(1, len(dec_out_names2))}
                    else:
                        # Con KV-cache: sólo el último token + past_key_values
                        past_feed = {
                            "input_ids":              np.array([[next_token_id]], dtype=np.int64),
                            "encoder_hidden_states":  encoder_hidden_states,
                            "encoder_attention_mask": attention_mask,
                        }
                        # Mapear past_key_values.N.X -> present.N.X usando present_map
                        for inp in dec_past_session.get_inputs():
                            if inp.name.startswith('past_key_values.'):
                                present_name = inp.name.replace('past_key_values.', 'present.')
                                if present_name in present_map:
                                    past_feed[inp.name] = present_map[present_name]

                        dec_past_out      = dec_past_session.run(None, past_feed)
                        logits            = dec_past_out[0]
                        # Actualizar present_map solo con decoder past (encoder past = constante)
                        dec_past_out_names = [o.name for o in dec_past_session.get_outputs()]
                        for i, name in enumerate(dec_past_out_names[1:], start=1):
                            present_map[name] = dec_past_out[i]

                    next_token_id = int(logits[0, -1, :].argmax())

                command = tokenizer.decode(generated_ids, skip_special_tokens=True)


            else:
                # Un solo modelo (ruta anterior/heredada)
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
