import os
import requests
import sys

MODEL_URL = "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
MODEL_DIR = "models"
MODEL_NAME = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)

def download_file(url, path):
    print(f"Downloading {url} to {path}...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_length = int(r.headers.get('content-length', 0))
        dl = 0
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    dl += len(chunk)
                    f.write(chunk)
                    done = int(50 * dl / total_length)
                    sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {dl//1024//1024}MB / {total_length//1024//1024}MB")
                    sys.stdout.flush()
    print("\nDownload complete.")

if __name__ == "__main__":
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
    
    if os.path.exists(MODEL_PATH):
        print(f"Model already exists at {MODEL_PATH}")
    else:
        try:
            download_file(MODEL_URL, MODEL_PATH)
            print(f"Successfully downloaded {MODEL_NAME}")
        except Exception as e:
            print(f"Error downloading model: {e}")
            sys.exit(1)
