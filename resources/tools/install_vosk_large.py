#!/usr/bin/env python3
import os
import requests
import zipfile
import shutil

# URL for the large Spanish model (~1.4 GB)
MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-es-0.42.zip"
MODEL_ZIP = "vosk-model-es-0.42.zip"
EXTRACT_DIR = "vosk-models"
FINAL_DIR = "vosk-models/es"

def download_file(url, dest_path):
    print(f"Downloading {url}...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_length = int(r.headers.get('content-length', 0))
        dl = 0
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                dl += len(chunk)
                f.write(chunk)
                done = int(50 * dl / total_length)
                print(f"\r[{'=' * done}{' ' * (50-done)}] {dl/1024/1024:.2f} MB", end='', flush=True)
    print("\nDownload complete.")

def install_model():
    if not os.path.exists(EXTRACT_DIR):
        os.makedirs(EXTRACT_DIR)

    # Check if already exists
    if os.path.exists(FINAL_DIR):
        print(f"Model already exists at {FINAL_DIR}")
        return

    # Download
    if not os.path.exists(MODEL_ZIP):
        download_file(MODEL_URL, MODEL_ZIP)

    # Extract
    print("Extracting...")
    with zipfile.ZipFile(MODEL_ZIP, 'r') as zip_ref:
        zip_ref.extractall(EXTRACT_DIR)
    
    # Rename/Move
    extracted_folder = os.path.join(EXTRACT_DIR, "vosk-model-es-0.42")
    if os.path.exists(extracted_folder):
        if os.path.exists(FINAL_DIR):
            shutil.rmtree(FINAL_DIR)
        os.rename(extracted_folder, FINAL_DIR)
        print(f"Model installed to {FINAL_DIR}")
    
    # Cleanup
    if os.path.exists(MODEL_ZIP):
        os.remove(MODEL_ZIP)
        print("Cleaned up zip file.")

if __name__ == "__main__":
    install_model()
