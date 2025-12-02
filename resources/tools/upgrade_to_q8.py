import os
import requests
import sys
import time

# URL for Gemma 2B Q8 (High Quality)
# Using bartowski's GGUF repo which is reliable
MODEL_URL = "https://huggingface.co/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q8_0.gguf"
MODEL_DIR = "models"
MODEL_NAME = "gemma-2-2b-it-Q8_0.gguf"
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)

def download_file(url, filename):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        print(f"Downloading {filename}...")
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(block_size):
                file.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = int(50 * downloaded / total_size)
                    sys.stdout.write(f"\r[{'=' * percent}{' ' * (50 - percent)}] {downloaded/1024/1024:.1f} MB")
                    sys.stdout.flush()
        print("\nDownload complete!")
        return True
    except Exception as e:
        print(f"\nError downloading: {e}")
        return False

if __name__ == "__main__":
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        print(f"Created directory {MODEL_DIR}")

    print(f"Downloading {MODEL_NAME} (approx 2.7 GB)...")
    print("This will improve intelligence significantly.")
    
    if download_file(MODEL_URL, MODEL_PATH):
        print("\nDownload complete!")
        print(f"Model saved to {MODEL_PATH}")
    else:
        print("\nDownload failed.")
