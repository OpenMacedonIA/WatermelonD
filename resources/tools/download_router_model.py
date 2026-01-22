import os
import shutil
from huggingface_hub import snapshot_download

def download_router_model():
    repo_id = "jrodriiguezg/minilm-l12-lemon-route"
    target_dir = "models/lemon-route"
    
    print(f"Downloading DecisionRouter model '{repo_id}' to '{target_dir}'...")
    
    if os.path.exists(target_dir):
        print(f"Directory {target_dir} already exists. checking content...")
        if len(os.listdir(target_dir)) > 0:
             print("Model seems to be present.")
             # Optional: Force update logic? For now assume valid if present.
             return

    try:
        snapshot_download(repo_id=repo_id, local_dir=target_dir, local_dir_use_symlinks=False)
        print("Download complete.")
    except Exception as e:
        print(f"Error downloading model: {e}")

if __name__ == "__main__":
    download_router_model()
