import os
import sys
from huggingface_hub import hf_hub_download
import shutil

# Configuration
REPO_ID = "bartowski/gemma-2-2b-it-GGUF"
FILENAME = "gemma-2-2b-it-Q4_K_M.gguf"
MODELS_DIR = os.path.join(os.getcwd(), "models")

def download_model():
    print(f"Iniciando descarga del modelo desde {REPO_ID}...")
    
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
        print(f"Directorio creado: {MODELS_DIR}")

    try:
        print(f"Descargando {FILENAME}...")
        model_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            local_dir=MODELS_DIR,
            local_dir_use_symlinks=False
        )
        print(f"Modelo descargado exitosamente en: {model_path}")
        
    except Exception as e:
        print(f"ERROR: Falló la descarga del modelo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_model()
