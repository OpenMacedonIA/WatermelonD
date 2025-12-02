import os
import requests
import zipfile
import json
import shutil
import sys
import psutil

# Configuration
MODELS = {
    "small": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip",
        "zip": "vosk-model-small-es-0.42.zip",
        "dir": "vosk-model-small-es-0.42",
        "desc": "Small (~40MB) - Recommended for < 3GB RAM"
    },
    "large": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-es-0.42.zip",
        "zip": "vosk-model-es-0.42.zip",
        "dir": "vosk-model-es-0.42",
        "desc": "Large (~1.5GB) - Recommended for >= 3GB RAM"
    }
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "vosk-models")

def get_system_resources():
    try:
        mem = psutil.virtual_memory()
        ram_gb = mem.total / (1024 ** 3)
        cpu_count = psutil.cpu_count(logical=True)
        return ram_gb, cpu_count
    except Exception as e:
        print(f"Error detecting resources: {e}")
        return 0, 1

def recommend_model(ram_gb):
    if ram_gb >= 3:
        return "large"
    else:
        return "small"

def download_file(url, dest_path):
    print(f"Downloading {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_length = int(r.headers.get('content-length', 0))
            dl = 0
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        dl += len(chunk)
                        f.write(chunk)
                        if total_length > 0:
                            done = int(50 * dl / total_length)
                            print(f"\r[{'=' * done}{' ' * (50-done)}] {dl/1024/1024:.2f} MB", end='', flush=True)
                        else:
                            print(f"\r{dl/1024/1024:.2f} MB", end='', flush=True)
        print("\nDownload complete.")
        return True
    except Exception as e:
        print(f"\nError downloading file: {e}")
        return False

def install_model(model_key):
    model_info = MODELS[model_key]
    
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
    
    zip_path = os.path.join(MODELS_DIR, model_info["zip"])
    extract_target = os.path.join(MODELS_DIR, "es") # Standardize to 'es'
    
    # Check if already installed (simple check)
    if os.path.exists(extract_target):
        print(f"A model is already installed at {extract_target}.")
        choice = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if choice != 'y':
            print("Aborting installation.")
            return extract_target

        shutil.rmtree(extract_target)

    # Download
    if not download_file(model_info["url"], zip_path):
        return None
    
    # Extract
    print("Extracting model (this may take a while)...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(MODELS_DIR)
        
        # Rename/Move
        extracted_folder = os.path.join(MODELS_DIR, model_info["dir"])
        if os.path.exists(extracted_folder):
            os.rename(extracted_folder, extract_target)
        else:
            print(f"Error: Expected extracted folder {extracted_folder} not found.")
            return None
            
        print("Model extracted successfully.")
    except Exception as e:
        print(f"Error extracting model: {e}")
        return None
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)
    
    return extract_target

def update_config(model_path):
    config_path = os.path.join(BASE_DIR, "config.json")
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except:
        config = {}

    if 'stt' not in config:
        config['stt'] = {}

    # We use a relative path for portability if possible, or absolute if needed.
    # Here we stick to the standard 'vosk-models/es' which the code likely expects.
    # But let's update it just in case.
    rel_path = os.path.relpath(model_path, BASE_DIR)
    config['stt']['model_path'] = rel_path
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    print(f"Config updated: model_path set to '{rel_path}'")

def main():
    print("=== Vosk Model Downloader ===")
    ram_gb, cpu_count = get_system_resources()
    print(f"Detected System: {ram_gb:.2f} GB RAM, {cpu_count} CPU cores")
    
    rec = recommend_model(ram_gb)
    print(f"Recommended Model: {MODELS[rec]['desc']}")
    
    print("\nAvailable Models:")
    print(f"1) {MODELS['small']['desc']}")
    print(f"2) {MODELS['large']['desc']}")
    
    choice = input(f"\nSelect model (1/2) [default: {1 if rec == 'small' else 2}]: ").strip()
    
    if not choice:
        selected = rec
    elif choice == '1':
        selected = 'small'
    elif choice == '2':
        selected = 'large'
    else:
        print("Invalid choice.")
        return

    print(f"\nSelected: {selected.upper()}")
    final_path = install_model(selected)
    
    if final_path:
        update_config(final_path)
        print("\nInstallation Complete!")
    else:
        print("\nInstallation Failed.")

if __name__ == "__main__":
    # Install psutil if missing (it might be missing in a fresh env, but it's useful)
    # If we can't rely on psutil, we can use os-specific commands, but psutil is cleaner.
    # Let's assume psutil is available or we fall back to basic checks if import fails.
    # Actually, let's add a try-except block for import at the top or just assume it's there 
    # since we are in a python env. If not, we can use 'free -m' via subprocess.
    # For now, I'll stick to psutil and if it fails, the user can install it or I'll add it to requirements.
    # Wait, 'psutil' is not in the standard library. I should probably use subprocess for 'free -m' to avoid dependency issues 
    # if I don't want to force an install right now.
    # Let's switch to subprocess for better portability without extra pip install if possible, 
    # OR just add psutil to requirements. The user has 'requirements.txt'.
    # I'll check requirements.txt first.
    main()
