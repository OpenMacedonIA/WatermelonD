import os
import shutil
from huggingface_hub import snapshot_download

import argparse

def download_mango():
    parser = argparse.ArgumentParser(description="Download AI Sysadmin Model (Lime/Mango)")
    parser.add_argument("--model", type=str, default="lime", choices=["lime", "mango"], help="Model to download: 'lime' (default) or 'mango' (legacy)")
    # Backwards compatibility for --branch if some old script calls it, though we are deprecating it for 'model' arg preference
    parser.add_argument("--branch", type=str, help="Deprecated: Use --model instead")
    
    args = parser.parse_args()
    
    # Determine model configuration
    if args.model == "lime":
        repo_id = "jrodriiguezg/lime-t5-large-770m"
        target_dir = os.path.join(os.getcwd(), "models", "Lime")
        revision = "main"
        model_name = "Lime"
    else:
        # Legacy Mango
        repo_id = "jrodriiguezg/mango-t5-770m"
        target_dir = os.path.join(os.getcwd(), "models", "MANGOt5")
        revision = "main"
        model_name = "MANGO (Legacy)"

    print(f"ℹ  Selected Model: {model_name}")
    print(f"ℹ  Repository: {repo_id}")
    
    # Check if model seems populated (simple check)
    if os.path.exists(target_dir):
        files = os.listdir(target_dir)
        # Look for critical model files
        if any(f.endswith(".bin") or f.endswith(".safetensors") for f in files) and "config.json" in files:
            print(f"[OK] {model_name} already exists in {target_dir}. Skipping download.")
            return

    print(f" Downloading {repo_id} (Branch: {revision}) to {target_dir}...")
    
    try:
        # Download the snapshot
        path = snapshot_download(
            repo_id=repo_id,
            revision=revision,
            local_dir=target_dir,
            local_dir_use_symlinks=False, # We want real files for standalone use
            resume_download=True,         # Resume if interrupted
            ignore_patterns=[".gitattributes", "README.md", "*.onnx", "*.tflite"] # Optimize size
        )
        print(f"[OK] Successfully downloaded {model_name} to {path}")
        
    except Exception as e:
        print(f"[ERROR] Error downloading model: {e}")
        print("   Please check your internet connection or install manually.")
        exit(1)

if __name__ == "__main__":
    download_mango()
