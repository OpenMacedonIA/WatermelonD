import os
import shutil
from huggingface_hub import snapshot_download

import argparse

def download_mango():
    parser = argparse.ArgumentParser(description="Download MANGO T5 model")
    parser.add_argument("--branch", type=str, default="main", help="Model branch to download (default: main)")
    args = parser.parse_args()
    
    repo_id = "jrodriiguezg/mango-t5-770m"
    target_dir = os.path.join(os.getcwd(), "models", "MANGOt5")
    revision = args.branch
    
    print(f"ℹ️  Selected Branch: {revision}")
    
    # Check if model seems populated (simple check)
    if os.path.exists(target_dir):
        files = os.listdir(target_dir)
        # Look for critical model files
        if any(f.endswith(".bin") or f.endswith(".safetensors") for f in files) and "config.json" in files:
            print(f"✅ MANGO T5 already exists in {target_dir}. Skipping download.")
            return

    print(f"⬇️ Downloading {repo_id} (Branch: {revision}) to {target_dir}...")
    
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
        print(f"✅ Successfully downloaded MANGO T5 to {path}")
        
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        print("   Please check your internet connection or install manually.")
        # Don't exit(1) to allow installation to proceed? 
        # No, if the user wants it 'ready to work', we should probably fail or warn loudly.
        # But 'set -e' in install.sh will stop everything.
        # Let's fail so they know something went wrong.
        exit(1)

if __name__ == "__main__":
    download_mango()
