import logging
import os
from modules.logger import app_logger

try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    app_logger.warning("llama-cpp-python no está instalado. AIEngine no funcionará.")

class AIEngine:
    def __init__(self, model_path=None):
        # Default paths
        self.default_path = "models/gemma-2-2b-it-Q4_K_M.gguf"
        
        if model_path and os.path.exists(model_path):
            self.model_path = model_path
            app_logger.info(f"AI Engine configurado con: {self.model_path} (Lazy Loading)")
        elif os.path.exists("models/gemma-2b-tio.gguf"):
            self.model_path = "models/gemma-2b-tio.gguf"
            app_logger.info("Configurado modelo Fine-Tuned TIO (Lazy Loading).")
        elif os.path.exists("models/gemma-2-2b-it-Q8_0.gguf"):
            self.model_path = "models/gemma-2-2b-it-Q8_0.gguf"
            app_logger.info("Configurado modelo Gemma Q8 (Lazy Loading).")
        else:
            self.model_path = self.default_path
            app_logger.info(f"Configurado modelo por defecto: {self.model_path} (Lazy Loading)")

        self.llm = None
        self.is_ready = False
        
        # NOTE: Model is NOT loaded here. It will be loaded on first use.

    def _ensure_model_loaded(self):
        """Carga el modelo si aún no está en memoria."""
        if not self.llm and LLAMA_AVAILABLE:
            app_logger.info("⚠️ Disparando carga perezosa (Lazy Load) del modelo AI...")
            self.load_model()

    def load_model(self):
        """Carga el modelo GGUF."""
        if not os.path.exists(self.model_path):
            app_logger.error(f"Modelo no encontrado en {self.model_path}.")
            return

        try:
            app_logger.info(f"Cargando modelo GGUF desde {self.model_path}...")
            
            # Adjust context window based on model if needed, but 2048 is safe for most
            n_ctx = 2048
            if "llama-3" in self.model_path.lower():
                n_ctx = 4096 # Llama 3 supports 8k, but 4k is safer for Nano
            
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=n_ctx, 
                n_threads=3, # Keep 3 threads for i3 (usually 2 cores/4 threads or 4 cores)
                n_batch=512, # Optimized batch size
                use_mmap=True, # Allow OS to manage memory paging
                verbose=False
            )
            
            self.is_ready = True
            app_logger.info(f"Modelo {os.path.basename(self.model_path)} cargado correctamente.")
            
            # Optimization: Free up initialization memory
            import gc
            gc.collect()
        except Exception as e:
            app_logger.error(f"Error cargando modelo: {e}")
            self.is_ready = False

    def generate_response(self, prompt, max_tokens=150):
        """Genera una respuesta usando el modelo (Raw Completion)."""
        self._ensure_model_loaded()
        
        if not self.is_ready:
            return "Lo siento, mi cerebro de IA no está disponible en este momento."

        try:
            # Usamos raw completion
            output = self.llm(
                prompt,
                max_tokens=max_tokens,
                stop=["<end_of_turn>"], # Gemma 2 stop token
                echo=False,
                temperature=0.7,
                top_p=0.9,
                repeat_penalty=1.1
            )
            
            response = output['choices'][0]['text'].strip()
            return response
        except Exception as e:
            app_logger.error(f"Error generando respuesta: {e}")
            return "Tuve un error al pensar la respuesta."

    def generate_response_stream(self, prompt, max_tokens=150):
        """Genera una respuesta en streaming (yields chunks)."""
        self._ensure_model_loaded()

        if not self.is_ready:
            yield "Lo siento, mi cerebro de IA no está disponible."
            return

        try:
            stream = self.llm(
                prompt,
                max_tokens=max_tokens,
                stop=["<end_of_turn>"], # Gemma 2 stop token
                echo=False,
                temperature=0.7,
                top_p=0.9,
                repeat_penalty=1.1,
                stream=True
            )
            
            for output in stream:
                chunk = output['choices'][0]['text']
                yield chunk

        except Exception as e:
            app_logger.error(f"Error generando stream: {e}")
            yield " Error."

# Alias for backward compatibility if needed, but we will update imports
GemmaEngine = AIEngine
