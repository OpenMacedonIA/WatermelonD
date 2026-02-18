import os
import sys
import subprocess
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from modules.logger import tts_logger

# Configuration
OUTPUT_DIR = "resources/sounds/fillers"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

FILLERS = [
    "A ver...",
    "Dame un segundo...",
    "Voy...",
    "Déjame ver...",
    "Un momento...",
    "Procesando...",
    "Déjame pensar...",
    "Vamos a ver..."
]

def get_piper_config():
    try:
        with open('config/config.json', 'r') as f:
            config = json.load(f)
            return config.get('tts', {})
    except:
        return {}

def generate_fillers():
    # Force absolute paths based on current directory
    cwd = os.getcwd()
    model_path = os.path.join(cwd, "piper/voices/es_ES-davefx-medium.onnx")
    piper_bin = os.path.join(cwd, "piper_bin/piper/piper")
    
    if not os.path.exists(piper_bin):
        # Fallback to local piper folder if piper_bin not found
        piper_bin = os.path.join(cwd, "piper/piper")

    if not os.path.exists(piper_bin):
        print(f"Error: Piper binary not found at {piper_bin}")
        return

    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        return

    print(f"Generating {len(FILLERS)} filler files to {OUTPUT_DIR}...")

    for i, text in enumerate(FILLERS):
        filename = f"filler_{i}.wav"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        cmd = f'echo "{text}" | "{piper_bin}" --model "{model_path}" --output_file "{filepath}"'
        
        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"Generated: {filepath} ('{text}')")
        except subprocess.CalledProcessError as e:
            print(f"Error generating {text}: {e}")

if __name__ == "__main__":
    generate_fillers()
