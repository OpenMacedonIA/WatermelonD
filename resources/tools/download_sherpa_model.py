#!/usr/bin/env python3
"""
Download Sherpa-ONNX Whisper models (Tiny, Base, Small, Medium)
Optimized ONNX models for faster CPU inference
"""
import os
import sys
import requests
import argparse

# Available Sherpa-ONNX Whisper models
MODELS = {
    "tiny": {
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-tiny.tar.bz2",
        "dir_name": "sherpa-onnx-whisper-tiny",
        "size": "~75MB",
        "speed": "Very Fast",
        "accuracy": "Good"
    },
    "base": {
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-base.tar.bz2",
        "dir_name": "sherpa-onnx-whisper-base",
        "size": "~145MB",
        "speed": "Fast",
        "accuracy": "Better"
    },
    "small": {
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2",
        "dir_name": "sherpa-onnx-whisper-small",
        "size": "~490MB",
        "speed": "Medium",
        "accuracy": "Very Good"
    },
    "medium": {
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-medium.tar.bz2",
        "dir_name": "sherpa-onnx-whisper-medium",
        "size": "~1.5GB",
        "speed": "Slower (but optimized)",
        "accuracy": "Excellent"
    }
}

DEST_BASE_DIR = "models/sherpa"

def download_and_extract(model_name):
    """Download and extract Sherpa-ONNX model"""
    import tarfile
    
    if model_name not in MODELS:
        print(f" Error: Model '{model_name}' not found.")
        print(f"Available models: {', '.join(MODELS.keys())}")
        return False
    
    model_info = MODELS[model_name]
    model_url = model_info["url"]
    
    # Create destination directory
    dest_dir = os.path.join(DEST_BASE_DIR, model_info["dir_name"])
    if not os.path.exists(DEST_BASE_DIR):
        os.makedirs(DEST_BASE_DIR)
    
    tar_path = os.path.join(DEST_BASE_DIR, f"{model_name}.tar.bz2")
    
    # Check if already downloaded
    if os.path.exists(dest_dir):
        print(f"Model '{model_name}' already exists at {dest_dir}")
        response = input("Do you want to re-download? (y/N): ")
        if response.lower() != 'y':
            return True
    
    print(f"\n Downloading Sherpa-ONNX Whisper {model_name.upper()} model...")
    print(f"   URL: {model_url}")
    print(f"   Size: {model_info['size']}")
    print(f"   Speed: {model_info['speed']}, Accuracy: {model_info['accuracy']}")
    
    try:
        # Download with progress
        r = requests.get(model_url, stream=True)
        r.raise_for_status()
        
        total_size = int(r.headers.get('content-length', 0))
        downloaded = 0
        
        with open(tar_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r   Progress: {percent:.1f}%", end='', flush=True)
        
        print(f"\n Downloaded to {tar_path}")
        
        # Extract
        print(" Extracting...")
        with tarfile.open(tar_path, "r:bz2") as tar:
            tar.extractall(path=DEST_BASE_DIR)
        
        print(" Extracted successfully")
        
        # Clean up tar file
        os.remove(tar_path)
        print(f"  Removed temporary file {tar_path}")
        
        # Verify extraction
        extracted_dir = os.path.join(DEST_BASE_DIR, model_info["dir_name"])
        if os.path.exists(extracted_dir):
            # List files
            files = os.listdir(extracted_dir)
            print(f"\n Model files in {extracted_dir}:")
            for f in files:
                print(f"   - {f}")
            
            # Check for required files
            required_files = ["encoder.onnx", "decoder.onnx", "tokens.txt"]
            missing = [f for f in required_files if f not in files and not any(f.startswith(rf.split('.')[0]) for rf in files)]
            
            if missing:
                print(f"\n Warning: Some expected files might be missing: {missing}")
            else:
                print("\n All required model files present")
            
            return True
        else:
            print(f" Error: Extraction failed, directory not found: {extracted_dir}")
            return False
            
    except Exception as e:
        print(f"\n Error during download/extraction: {e}")
        return False

def list_models():
    """List available models"""
    print("\n Available Sherpa-ONNX Whisper Models:\n")
    for name, info in MODELS.items():
        status = " Installed" if os.path.exists(os.path.join(DEST_BASE_DIR, info["dir_name"])) else " Not installed"
        print(f"  {name.upper():<10} | Size: {info['size']:<10} | Speed: {info['speed']:<20} | Accuracy: {info['accuracy']:<15} | {status}")
    print()

def main():
    parser = argparse.ArgumentParser(description="Download Sherpa-ONNX Whisper models")
    parser.add_argument('--model', '-m', 
                       choices=list(MODELS.keys()), 
                       default='medium',
                       help='Model to download (default: medium)')
    parser.add_argument('--list', '-l', 
                       action='store_true',
                       help='List available models')
    
    args = parser.parse_args()
    
    if args.list:
        list_models()
        return
    
    print(f"\n Sherpa-ONNX Whisper Model Downloader")
    print(f"=" * 50)
    
    success = download_and_extract(args.model)
    
    if success:
        print(f"\n SUCCESS! Model '{args.model}' is ready to use")
        print(f"\n To use this model, update your config:")
        print(f"   {{\n      \"stt\": {{\n         \"engine\": \"sherpa\",")
        print(f"         \"sherpa_model_path\": \"models/sherpa/{MODELS[args.model]['dir_name']}\"\n      }}\n   }}")
    else:
        print(f"\n FAILED to download model '{args.model}'")
        sys.exit(1)

if __name__ == "__main__":
    main()
