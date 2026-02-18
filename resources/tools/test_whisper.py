#!/usr/bin/env python3
import os
import sys
import time
import numpy as np

print("--- Faster-Whisper Test ---")

try:
    from faster_whisper import WhisperModel
    print("[OK] 'faster_whisper' module imported.")
except ImportError as e:
    print(f"[ERROR] Failed to import 'faster_whisper': {e}")
    sys.exit(1)

MODEL_SIZE = "medium"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"

print(f"Loading model '{MODEL_SIZE}' on {DEVICE} ({COMPUTE_TYPE})...")
try:
    start_time = time.time()
    model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
    print(f"[OK] Model loaded in {time.time() - start_time:.2f}s")
except Exception as e:
    print(f"[ERROR] Failed to load model: {e}")
    sys.exit(1)

# Generate dummy audio (1 second of silence + some noise)
print("Generating dummy audio...")
sample_rate = 16000
duration = 2 # seconds
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
# Simple sine wave (440Hz) to simulate speech-like signal
audio = 0.5 * np.sin(2 * np.pi * 440 * t)
audio = audio.astype(np.float32)

print("Transcribing dummy audio...")
try:
    start_time = time.time()
    segments, info = model.transcribe(audio, beam_size=5, language="es")
    
    print(f"Detected language: {info.language} with probability {info.language_probability}")
    
    text = ""
    for segment in segments:
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        text += segment.text
        
    print(f"[OK] Transcription complete in {time.time() - start_time:.2f}s")
    print(f"Result: '{text}'")
except Exception as e:
    print(f"[ERROR] Transcription failed: {e}")
    sys.exit(1)

print("\n🎉 Faster-Whisper seems operational.")
