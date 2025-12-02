#!/usr/bin/env python3
import sys

try:
    from piper import PiperVoice
except ImportError:
    sys.exit(1)

MODEL_PATH = "piper/voices/es_ES-davefx-medium.onnx"
voice = PiperVoice.load(MODEL_PATH)
text = "Test"

stream = voice.synthesize(text)
chunk = next(stream)

print(f"Type: {type(chunk)}")
print(f"Dir: {dir(chunk)}")

# Try common attributes
for attr in ['audio', 'bytes', 'data', 'raw', 'wav']:
    if hasattr(chunk, attr):
        val = getattr(chunk, attr)
        print(f"Found attribute '{attr}': type={type(val)}")
