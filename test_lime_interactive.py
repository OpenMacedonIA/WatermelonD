import logging
import os
import sys
from unittest.mock import MagicMock
import readline # Para un mejor manejo de la entrada

# --- Hack: Simular torchvision roto para prevenir cuelgue de T5 ---
# Copiado de modules/BrainNut/engine.py
try:
    import torchvision
except (ImportError, RuntimeError):
    # Simulando torchvision para evitar problemas específicos del entorno
    mock_tv = MagicMock()
    from importlib.machinery import ModuleSpec
    mock_tv.__spec__ = ModuleSpec(name="torchvision", loader=None)
    sys.modules["torchvision"] = mock_tv
    sys.modules["torchvision.transforms"] = MagicMock()
    sys.modules["torchvision.ops"] = MagicMock()

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LimeTester")

class LimeTester:
    def __init__(self, model_path=None):
        # Prioridad predeterminada: Local > HuggingFace
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
        logger.info(f"Cargando Lime T5 desde {self.model_path}...")
        
        try:
            if torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.device = "cpu"
                torch.set_num_threads(2) # Permitir un poco más de hilos para prueba independiente
                
            logger.info(f"Usando dispositivo: {self.device}")

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path).to(self.device)
            
            logger.info("[OK] ¡Modelo cargado exitosamente!")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Error cargando modelo: {e}")
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
            # Construir prompt con contexto
            if context_override is not None:
                context_str = str(context_override)
            else:
                context_str = self.get_context()
                
            input_text = f"Contexto: {context_str} | Instrucción: {text.strip()}"
            
            # logger.debug(f"Prompt Completo: {input_text}") # Silenciado para una interfaz más limpia

            input_ids = self.tokenizer.encode(input_text, return_tensors="pt").to(self.device)
            
            outputs = self.model.generate(
                input_ids, 
                max_length=128, 
                num_beams=5, 
                temperature=0.7,
                do_sample=True, # Habilitar muestreo para que la temperatura sea efectiva
                early_stopping=True,
                return_dict_in_generate=True, 
                output_scores=True
            )
            
            command = self.tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)
            
            # Calcular confianza (heurística)
            sequence_score = outputs.sequences_scores[0].item()
            
            # Mapeo de confianza
            if sequence_score > -1.5: confidence = "Muy Alta (98%)"
            elif sequence_score > -3.0: confidence = "Alta (90%)"
            elif sequence_score > -5.0: confidence = "Media (75%)"
            else: confidence = "Baja (50%)"
            
            print(f"\n Resultado:")
            # print(f"   Context: \033[90m{context_str}\033[0m") # Eliminado según lo solicitado
            print(f"   Comando: \033[92m{command}\033[0m") # Texto verde
            print(f"   Puntuación: {sequence_score:.4f} ({confidence})")
            print("-" * 40)
            
        except Exception as e:
            logger.error(f"Error de inferencia: {e}")

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
        # ---  DOCKER (¿Sabe ignorar los .py?) ---
        "Despliega un contenedor redis en el puerto 6379",
        "Listame los contenedores activos",
        "Muestra los logs del contenedor llamado 'database'",
        "Para todos los contenedores que esten corriendo",
        "Ejecuta una terminal bash dentro del contenedor 'neocore_app'",

        # ---  NAVEGACIÓN Y ARCHIVOS (¿Sabe moverse?) ---
        "Entra en el directorio TangerineUI",
        "Sube un nivel de directorio",
        "Dime la ruta actual (pwd)",  # A ver si aquí no dice 'echo'
        "Busca el archivo 'settings.yaml' dentro de la carpeta config",
        "Muestrame las ultimas 10 lineas del changelog.md",
        "Cuenta cuantos archivos hay en la carpeta modules",

        # ---  ESTADO DEL SISTEMA (¿Sabe mirar el hardware?) ---
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
    print("---  INICIANDO BATERÍA DE PRUEBAS SYSADMIN ---")

    # 1. Ejecutar pruebas con ruido (NeoCore)
    for req in pruebas_neocore:
        print(f" Contexto: NeoCore | Request > {req}")
        tester.infer(req, context_override=ctx_neocore)

    # 2. Ejecutar pruebas limpias
    for req in pruebas_limpias:
        print(f" Contexto: []      | Request > {req}")
        tester.infer(req, context_override=[])

def main():
    print("\n[LIME] === Lime T5 Interactive Tester === [LIME]")
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", action="store_true", help="Ejecutar la batería de pruebas automatizada")
    args = parser.parse_args()

    tester = LimeTester()
    if not tester.load_model():
        print("Error al iniciar. Compruebe si el modelo está descargado en models/Lime o si hay internet.")
        return

    if args.benchmark:
        run_benchmark(tester)
        return

    print("Escribe 'exit' o 'quit' para detener.")
    print("Escribe 'benchmark' para ejecutar la batería de pruebas.")
    print("\n¡Listo! Pide un comando (ej., 'lista todos los archivos', 'apaga el sistema')")
    
    while True:
        try:
            user_input = input("\n[INFO] Request > ")
            if user_input.lower() in ['exit', 'quit']:
                break
            
            if user_input.lower() == 'benchmark':
                run_benchmark(tester)
                continue
            
            tester.infer(user_input)
            
        except KeyboardInterrupt:
            print("\nSaliendo...")
            break

if __name__ == "__main__":
    main()
