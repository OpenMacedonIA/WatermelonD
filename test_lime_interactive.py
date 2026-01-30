import logging
import os
import sys
from unittest.mock import MagicMock
import readline # For better input handling

# --- Hack: Mock broken torchvision to prevent T5 load crash ---
# Copied from modules/BrainNut/engine.py
try:
    import torchvision
except (ImportError, RuntimeError):
    # Mocking torchvision to bypass specific environment issues
    mock_tv = MagicMock()
    from importlib.machinery import ModuleSpec
    mock_tv.__spec__ = ModuleSpec(name="torchvision", loader=None)
    sys.modules["torchvision"] = mock_tv
    sys.modules["torchvision.transforms"] = MagicMock()
    sys.modules["torchvision.ops"] = MagicMock()

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LimeTester")

class LimeTester:
    def __init__(self, model_path=None):
        # Default priority: Local > HuggingFace
        if model_path:
            self.model_path = model_path
        elif os.path.exists("models/Lime"):
            self.model_path = "models/Lime"
        else:
            self.model_path = "jrodriiguezg/lime-t5-large-770m"
            
        self.tokenizer = None
        self.model = None
        self.device = "cpu"

    def load_model(self):
        logger.info(f"Loading Lime T5 from {self.model_path}...")
        
        try:
            if torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.device = "cpu"
                torch.set_num_threads(2) # Allow slightly more threads for standalone test
                
            logger.info(f"Using device: {self.device}")

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path).to(self.device)
            
            logger.info("✅ Model loaded successfully!")
            return True
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            return False

    def get_context(self):
        try:
            raw_files = os.listdir('.')
        except:
            raw_files = []
            
        ignored = {'.git', '__pycache__', 'venv', 'env', '.config', 'node_modules', '.gemini'}
        filtered_files = [
            f for f in raw_files 
            if f not in ignored and not f.startswith('.') 
            and not f.endswith(('.pyc', '.Log'))
        ]
        
        if len(filtered_files) > 25:
            filtered_files = filtered_files[:25] + ['...']
            
        return str(filtered_files)

    def infer(self, text, context_override=None):
        if not text: return
        
        try:
            # Build prompt with context
            if context_override is not None:
                context_str = str(context_override)
            else:
                context_str = self.get_context()
                
            input_text = f"Contexto: {context_str} | Instrucción: {text.strip()}"
            
            # logger.debug(f"Full Prompt: {input_text}") # Silenced for cleaner UI

            input_ids = self.tokenizer.encode(input_text, return_tensors="pt").to(self.device)
            
            outputs = self.model.generate(
                input_ids, 
                max_length=128, 
                num_beams=5, 
                temperature=0.7,
                do_sample=True, # Enable sampling to make temperature effective
                early_stopping=True,
                return_dict_in_generate=True, 
                output_scores=True
            )
            
            command = self.tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)
            
            # Calculate confidence (heuristic)
            sequence_score = outputs.sequences_scores[0].item()
            
            # Confidence mapping
            if sequence_score > -1.5: confidence = "Very High (98%)"
            elif sequence_score > -3.0: confidence = "High (90%)"
            elif sequence_score > -5.0: confidence = "Medium (75%)"
            else: confidence = "Low (50%)"
            
            print(f"\n🌱 Result:")
            # print(f"   Context: \033[90m{context_str}\033[0m") # Removed as requested
            print(f"   Command: \033[92m{command}\033[0m") # Green text
            print(f"   Score:   {sequence_score:.4f} ({confidence})")
            print("-" * 40)
            
        except Exception as e:
            logger.error(f"Inference error: {e}")

def run_benchmark(tester):
    # ==========================================
    # CONTEXTO DIFÍCIL (NeoCore - Lleno de ruido Python)
    # ==========================================
    ctx_neocore = [
        'changelog.md', 'config', 'data', 'database', 'debug_stt_standalone.py', 
        'modules', 'public_docs', 'resources', 'run_neocore_distrobox.sh', 'source', 
        'start.sh', 'start_services.py', 'TangerineUI', 'NeoCore.py', 'README.md', 
        'install.sh', 'requirements.txt', 'setup_distrobox.sh', 'setup_repos.sh', 
        'tests', 'logs', 'priv_docs', 'models', 'tts_cache', 'test_lime_interactive.py'
    ]

    # Pruebas específicas para ver si ignora el ruido y obedece comandos de sistema
    pruebas_neocore = [
        # --- 🐳 DOCKER (¿Sabe ignorar los .py?) ---
        "Despliega un contenedor redis en el puerto 6379",
        "Listame los contenedores activos",
        "Muestra los logs del contenedor llamado 'database'",
        "Para todos los contenedores que esten corriendo",
        "Ejecuta una terminal bash dentro del contenedor 'neocore_app'",

        # --- 📂 NAVEGACIÓN Y ARCHIVOS (¿Sabe moverse?) ---
        "Entra en el directorio TangerineUI",
        "Sube un nivel de directorio",
        "Dime la ruta actual (pwd)",  # A ver si aquí no dice 'echo'
        "Busca el archivo 'settings.yaml' dentro de la carpeta config",
        "Muestrame las ultimas 10 lineas del changelog.md",
        "Cuenta cuantos archivos hay en la carpeta modules",

        # --- ⚙️ ESTADO DEL SISTEMA (¿Sabe mirar el hardware?) ---
        "Verifica el espacio libre en disco",
        "Dime cuanta memoria RAM se esta usando",
        "Muestrame los puertos que estan escuchando en el sistema",
        "Reinicia el servicio de red"
    ]

    # ==========================================
    # CONTEXTO VACÍO (SysAdmin Puro)
    # ==========================================
    # Aquí no hay archivos que le distraigan. Debería ser 100% efectivo.
    pruebas_limpias = [
        "Actualiza los repositorios del sistema", # Debería usar dnf (Fedora)
        "Busca todos los archivos .log en /var/log",
        "Crea un usuario llamado 'admin' en el sistema",
        "Comprime la carpeta /home/user en un archivo tar.gz",
        "Mata el proceso con PID 1234"
    ]

    # ==========================================
    # BUCLE DE EJECUCIÓN
    # ==========================================
    print("--- 🔥 INICIANDO BATERÍA DE PRUEBAS SYSADMIN ---")

    # 1. Ejecutar pruebas con ruido (NeoCore)
    for req in pruebas_neocore:
        print(f"📝 Contexto: NeoCore | Request > {req}")
        tester.infer(req, context_override=ctx_neocore)

    # 2. Ejecutar pruebas limpias
    for req in pruebas_limpias:
        print(f"📝 Contexto: []      | Request > {req}")
        tester.infer(req, context_override=[])

def main():
    print("\n🍈 === Lime T5 Interactive Tester === 🍈")
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", action="store_true", help="Run automated benchmark battery")
    args = parser.parse_args()

    tester = LimeTester()
    if not tester.load_model():
        print("Failed to start. Check if model is downloaded in models/Lime or internet is available.")
        return

    if args.benchmark:
        run_benchmark(tester)
        return

    print("Type 'exit' or 'quit' to stop.")
    print("Type 'benchmark' to run the test battery.")
    print("\nReady! Ask for a command (e.g., 'list all files', 'shut down the system')")
    
    while True:
        try:
            user_input = input("\n📝 Request > ")
            if user_input.lower() in ['exit', 'quit']:
                break
            
            if user_input.lower() == 'benchmark':
                run_benchmark(tester)
                continue
            
            tester.infer(user_input)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()
