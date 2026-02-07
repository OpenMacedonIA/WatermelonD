#!/usr/bin/env python3
"""
Configure WatermelonD STT Engine
Helper script to switch between STT engines and optimize settings
"""
import os
import sys
import json

# Add root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../..'))

from modules.config_manager import ConfigManager

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def show_current_config(config_manager):
    """Show current STT configuration"""
    stt_config = config_manager.get('stt', {})
    
    print_header("Current STT Configuration")
    print(f"  Engine:        {stt_config.get('engine', 'vosk')}")
    print(f"  Model Path:    {stt_config.get('model_path', 'N/A')}")
    
    if stt_config.get('engine') == 'sherpa':
        print(f"  Sherpa Model:  {stt_config.get('sherpa_model_path', 'models/sherpa')}")
        print(f"  Num Threads:   {stt_config.get('num_threads', 2)}")
    
    print()

def configure_vosk(config_manager):
    """Configure Vosk engine"""
    print_header("Configure Vosk Engine")
    print("Vosk is fast but less accurate. Good for low-end hardware.")
    print()
    
    model_path = input("Model path [vosk-models/es]: ").strip() or "vosk-models/es"
    
    if not os.path.exists(model_path):
        print(f"\n⚠️  Warning: Model not found at {model_path}")
        print("   Download with: python resources/tools/download_vosk_model.py")
    
    config_manager.set('stt.engine', 'vosk')
    config_manager.set('stt.model_path', model_path)
    
    print("\n✅ Configured Vosk engine")

def configure_sherpa(config_manager):
    """Configure Sherpa-ONNX engine"""
    print_header("Configure Sherpa-ONNX Engine")
    print("Sherpa-ONNX provides excellent accuracy with optimized speed.")
    print()
    
    print("Available models:")
    print("  1. Tiny   - ~75MB,  Very Fast,   Good accuracy")
    print("  2. Base   - ~145MB, Fast,        Better accuracy")
    print("  3. Small  - ~490MB, Medium,      Very Good accuracy")
    print("  4. Medium - ~1.5GB, Slower,      Excellent accuracy ⭐ Recommended")
    print()
    
    choice = input("Select model [1-4, default=4]: ").strip() or "4"
    
    model_map = {
        "1": ("tiny", "sherpa-onnx-whisper-tiny"),
        "2": ("base", "sherpa-onnx-whisper-base"),
        "3": ("small", "sherpa-onnx-whisper-small"),
        "4": ("medium", "sherpa-onnx-whisper-medium"),
    }
    
    if choice not in model_map:
        print("❌ Invalid choice")
        return
    
    model_name, model_dir = model_map[choice]
    model_path = f"models/sherpa/{model_dir}"
    
    # Check if model exists
    if not os.path.exists(model_path):
        print(f"\n⚠️  Model not found at {model_path}")
        download = input(f"Download {model_name} model now? (y/N): ").strip().lower()
        
        if download == 'y':
            import subprocess
            print(f"\n📥 Downloading {model_name} model...")
            result = subprocess.run([
                sys.executable,
                "resources/tools/download_sherpa_model.py",
                "--model", model_name
            ])
            
            if result.returncode != 0:
                print("❌ Download failed")
                return
        else:
            print("⚠️  Skipping download. Run manually:")
            print(f"   python resources/tools/download_sherpa_model.py --model {model_name}")
            return
    
    # CPU threads
    import multiprocessing
    cpu_count = multiprocessing.cpu_count()
    default_threads = min(2, cpu_count)
    
    threads = input(f"CPU threads [{default_threads}]: ").strip()
    threads = int(threads) if threads.isdigit() else default_threads
    
    # Save config
    config_manager.set('stt.engine', 'sherpa')
    config_manager.set('stt.sherpa_model_path', model_path)
    config_manager.set('stt.num_threads', threads)
    
    print(f"\n✅ Configured Sherpa-ONNX with {model_name} model ({threads} threads)")

def configure_whisper(config_manager):
    """Configure Faster-Whisper engine"""
    print_header("Configure Faster-Whisper Engine")
    print("⚠️  Warning: Faster-Whisper is very accurate but SLOW on CPU!")
    print("   Not recommended for real-time use on i3-7gen.")
    print("   Consider using Sherpa-ONNX instead (option 2).")
    print()
    
    proceed = input("Are you sure you want to use Faster-Whisper? (y/N): ").strip().lower()
    if proceed != 'y':
        print("Cancelled.")
        return
    
    model = input("Model size [tiny/base/small/medium, default=medium]: ").strip() or "medium"
    
    config_manager.set('stt.engine', 'whisper')
    config_manager.set('stt.whisper_model', model)
    config_manager.set('stt.whisper_device', 'cpu')
    config_manager.set('stt.whisper_compute', 'int8')
    
    print(f"\n✅ Configured Faster-Whisper with {model} model")
    print("⚠️  This may be slow! Test performance before deploying.")

def benchmark_engines():
    """Run benchmarks to compare engines"""
    print_header("STT Engine Benchmark")
    print("This will test all available engines with a sample audio file.")
    print()
    
    print("📝 TODO: Implement benchmark tool")
    print("   Will be available in: resources/tools/benchmark_stt.py")

def main():
    config_manager = ConfigManager()
    
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║          WatermelonD STT Configuration Tool           ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    show_current_config(config_manager)
    
    print("Options:")
    print("  1. Configure Vosk (Fast, Less Accurate)")
    print("  2. Configure Sherpa-ONNX (Recommended - Fast + Accurate)")
    print("  3. Configure Faster-Whisper (Slow, Very Accurate)")
    print("  4. Benchmark Engines")
    print("  5. View Current Config")
    print("  0. Exit")
    print()
    
    choice = input("Select option [1-5, 0]: ").strip()
    
    if choice == "1":
        configure_vosk(config_manager)
    elif choice == "2":
        configure_sherpa(config_manager)
    elif choice == "3":
        configure_whisper(config_manager)
    elif choice == "4":
        benchmark_engines()
    elif choice == "5":
        show_current_config(config_manager)
    elif choice == "0":
        print("Goodbye!")
        sys.exit(0)
    else:
        print("❌ Invalid option")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("🔄 Restart NeoCore for changes to take effect:")
    print("   systemctl --user restart neo.service")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
