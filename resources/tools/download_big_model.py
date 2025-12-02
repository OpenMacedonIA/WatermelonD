import os
import requests
import zipfile
import json
import shutil

# Configuration
MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-es-0.42.zip"
MODEL_ZIP = "vosk-model-es-0.42.zip"
MODEL_DIR_NAME = "vosk-model-es-0.42"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "vosk-models")

def download_file(url, dest_path):
    print(f"Downloading {url}...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_length = int(r.headers.get('content-length', 0))
        dl = 0
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    dl += len(chunk)
                    f.write(chunk)
                    done = int(50 * dl / total_length)
                    print(f"\r[{'=' * done}{' ' * (50-done)}] {dl/1024/1024:.2f} MB", end='', flush=True)
    print("\nDownload complete.")

def install_model():
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
    
    zip_path = os.path.join(MODELS_DIR, MODEL_ZIP)
    extract_path = os.path.join(MODELS_DIR, "es-big") # Rename for clarity
    
    # Check if already installed
    if os.path.exists(extract_path):
        print(f"Model already exists at {extract_path}")
        return extract_path

    # Download
    download_file(MODEL_URL, zip_path)
    
    # Extract
    print("Extracting model (this may take a while)...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(MODELS_DIR)
    
    # Rename/Move
    original_extracted_path = os.path.join(MODELS_DIR, MODEL_DIR_NAME)
    if os.path.exists(original_extracted_path):
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)
        os.rename(original_extracted_path, extract_path)
    
    # Cleanup
    os.remove(zip_path)
    
    return extract_path

def update_config(model_path):
    config_path = os.path.join(BASE_DIR, "config.json")
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except:
        config = {}

    if 'stt' not in config:
        config['stt'] = {}

    config['stt']['model_path'] = model_path
    config['stt']['use_grammar'] = True # Default to True, user can change manually
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    print("Config updated successfully.")

if __name__ == "__main__":
    try:
        final_path = install_model()
        update_config(final_path)
        print("\nInstallation Complete!")
        print(f"Big Model Path: {final_path}")
    except Exception as e:
        print(f"Error during installation: {e}")
