import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

try:
    from faster_whisper import download_model
except ImportError:
    print("Error: faster-whisper not installed. Run 'pip install faster-whisper'")
    sys.exit(1)

def main():
    model_size = "medium" # Good balance for i3/8GB
    output_dir = "models/whisper"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Downloading Faster-Whisper model '{model_size}' to {output_dir}...")
    try:
        model_path = download_model(model_size, output_dir=output_dir)
        print(f"Model downloaded successfully to: {model_path}")
    except Exception as e:
        print(f"Error downloading model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
