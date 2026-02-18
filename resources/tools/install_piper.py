import os
import requests
import tarfile
import json
import shutil

# Configuration
PIPER_URL = "https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz"
VOICE_MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx"
VOICE_JSON_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PIPER_DIR = os.path.join(BASE_DIR, "piper")
VOICES_DIR = os.path.join(PIPER_DIR, "voices")

def download_file(url, dest_path):
    print(f"Downloading {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Saved to {dest_path}")

def install_piper():
    if not os.path.exists(PIPER_DIR):
        os.makedirs(PIPER_DIR)
    
    # Download Piper Binary - SKIPPED (Using pip package)
    print("Skipping Piper binary download (using python package).")

    # Download Voice Model
    if not os.path.exists(VOICES_DIR):
        os.makedirs(VOICES_DIR)
    
    model_path = os.path.join(VOICES_DIR, "es_ES-davefx-medium.onnx")
    json_path = os.path.join(VOICES_DIR, "es_ES-davefx-medium.onnx.json")
    
    if not os.path.exists(model_path):
        download_file(VOICE_MODEL_URL, model_path)
    if not os.path.exists(json_path):
        download_file(VOICE_JSON_URL, json_path)

    return None, model_path

def update_config(piper_bin, piper_model):
    config_path = os.path.join(BASE_DIR, "config.json")
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except:
        config = {}

    if 'tts' not in config:
        config['tts'] = {}

    config['tts']['engine'] = 'piper'
    # config['tts']['piper_bin'] = piper_bin # Not needed for python package
    config['tts']['piper_model'] = piper_model
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    print("Config updated successfully.")

if __name__ == "__main__":
    try:
        bin_path, model_path = install_piper()
        update_config(bin_path, model_path)
        print("\nInstallation Complete!")
        print(f"Piper Bin: {bin_path}")
        print(f"Voice Model: {model_path}")
    except Exception as e:
        print(f"Error during installation: {e}")
