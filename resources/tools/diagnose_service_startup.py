#!/usr/bin/env python3
import os
import sys
import json
import logging

try:
    import vosk
    import pyaudio
    from modules.config_manager import ConfigManager
except ImportError as e:
    print(f"CRITICAL ERROR: Missing dependency: {e}")
    print("Run this script within the virtual environment: ./venv/bin/python resources/tools/diagnose_service_startup.py")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Diagnostic")

def check_config():
    print("\n--- 1. CONFIGURATION CHECK ---")
    config = ConfigManager()
    stt_config = config.get("stt", {})
    engine = stt_config.get("engine", "UNKNOWN")
    device_index = stt_config.get("input_device_index", "DEFAULT")
    model_path = stt_config.get("model_path", "vosk-models/es")
    
    print(f"STT Engine: {engine}")
    print(f"Input Device Index: {device_index}")
    print(f"Vosk Model Path: {model_path}")
    
    if engine != "vosk":
        print("WARNING: Engine is NOT set to 'vosk'. Audio service might be trying to load Whisper.")
    
    return config, model_path, device_index

def check_model(model_path):
    print("\n--- 2. VOSK MODEL CHECK ---")
    if not os.path.exists(model_path):
        print(f"ERROR: Model directory does not exist at '{model_path}'")
        return None
    
    print(f"Loading Vosk model from {model_path}...")
    try:
        model = vosk.Model(model_path)
        print("SUCCESS: Vosk Model loaded correctly.")
        return model
    except Exception as e:
        print(f"ERROR: Failed to load Vosk model: {e}")
        return None

def check_audio_input(model, device_index):
    print("\n--- 3. AUDIO INPUT CHECK ---")
    if device_index == "DEFAULT":
        device_index = None
    
    try:
        p = pyaudio.PyAudio()
        info = p.get_device_info_by_index(device_index) if device_index is not None else "Default Device"
        print(f"Opening stream on device: {info}")
        
        recognizer = vosk.KaldiRecognizer(model, 16000)
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, 
                        frames_per_buffer=4096, input_device_index=device_index)
        stream.start_stream()
        
        print("\n✅ LISTENING... Say something (Press Ctrl+C to stop manually if it hangs)")
        for i in range(0, 50): # Listen for ~5-10 seconds
            data = stream.read(4000, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                res = json.loads(recognizer.Result())
                print(f"RECOGNIZED: {res.get('text', '')}")
            else:
                partial = json.loads(recognizer.PartialResult())
                # print(f"Partial: {partial}", end='\r')
        
        print("\nStream test finished.")
        stream.stop_stream()
        stream.close()
        p.terminate()
        
    except Exception as e:
        print(f"\nERROR: Audio stream failed: {e}")

if __name__ == "__main__":
    print("==========================================")
    print("   NEO SERVICE DIAGNOSTIC TOOL")
    print("==========================================")
    
    # Ensure we assume we are at project root if run from there
    if os.getcwd().endswith("tools"):
        os.chdir("../../")
        print(f"Changed working directory to: {os.getcwd()}")
        sys.path.append(os.getcwd())
    
    cfg, path, idx = check_config()
    model = check_model(path)
    if model:
        check_audio_input(model, idx)
    else:
        print("SKIPPING AUDIO TEST due to model failure.")
        
    print("\n==========================================")
    print("Diagnostic Complete.")
