#!/usr/bin/env python3
import os
import sys

try:
    from piper import PiperVoice
    print("✅ 'piper' module imported.")
except ImportError as e:
    print(f"❌ Failed to import 'piper': {e}")
    sys.exit(1)

MODEL_PATH = "piper/voices/es_ES-davefx-medium.onnx"

if not os.path.exists(MODEL_PATH):
    print(f"❌ Model not found at {MODEL_PATH}")
    sys.exit(1)

try:
    print(f"Loading model from {MODEL_PATH}...")
    voice = PiperVoice.load(MODEL_PATH)
    print("\n--- PiperVoice Instance Attributes ---")
    for attr in dir(voice):
        if not attr.startswith("__"):
            print(f"- {attr}")
            
    print("\n--- Testing 'synthesize' method signature if exists ---")
    if hasattr(voice, 'synthesize'):
        print(f"synthesize found: {voice.synthesize}")
    
except Exception as e:
    print(f"Error: {e}")
