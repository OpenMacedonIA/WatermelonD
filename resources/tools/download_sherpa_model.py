import os
import requests

MODEL_REPO = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-tiny.tar.bz2"
DEST_DIR = "models/sherpa"

def download_and_extract():
    import tarfile
    
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
        
    tar_path = os.path.join(DEST_DIR, "model.tar.bz2")
    
    print(f"Downloading {MODEL_REPO}...")
    try:
        r = requests.get(MODEL_REPO, stream=True)
        r.raise_for_status()
        with open(tar_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Saved to {tar_path}")
        
        print("Extracting...")
        with tarfile.open(tar_path, "r:bz2") as tar:
            tar.extractall(path="models/sherpa")
        print("Extracted successfully.")
        
        # Move files to root of models/sherpa if nested
        base_name = "sherpa-onnx-whisper-tiny"
        nested_dir = os.path.join(DEST_DIR, base_name)
        if os.path.exists(nested_dir):
            import shutil
            for item in os.listdir(nested_dir):
                s = os.path.join(nested_dir, item)
                d = os.path.join(DEST_DIR, item)
                if os.path.exists(d):
                    if os.path.isdir(d): shutil.rmtree(d)
                    else: os.remove(d)
                shutil.move(s, d)
            os.rmdir(nested_dir)
            print("Flattened directory structure.")
            
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    download_and_extract()

if __name__ == "__main__":
    main()
