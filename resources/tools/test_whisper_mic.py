#!/usr/bin/env python3
import os
import sys
import time
import numpy as np
import pyaudio
import struct

print("--- Faster-Whisper Microphone Test ---")

# 1. Load Model
try:
    from faster_whisper import WhisperModel
    print("Loading model 'small' on cpu (int8)...")
    model = WhisperModel("small", device="cpu", compute_type="int8")
    print("✅ Model loaded.")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    sys.exit(1)

# 2. Record Audio
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5

p = pyaudio.PyAudio()

device_index = None
if len(sys.argv) > 1:
    device_index = int(sys.argv[1])
    print(f"Using Input Device Index: {device_index}")

print(f"\n🎤 Recording for {RECORD_SECONDS} seconds... SPEAK NOW!")
try:
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                    frames_per_buffer=CHUNK, input_device_index=device_index)
    
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        if i % 10 == 0: print(".", end="", flush=True)
    
    print("\n✅ Recording complete.")
    
    stream.stop_stream()
    stream.close()
    p.terminate()
except Exception as e:
    print(f"\n❌ Recording failed: {e}")
    sys.exit(1)

# 3. Transcribe
print("\nProcessing audio...")
try:
    raw_data = b''.join(frames)
    # Convert to float32 for Whisper
    audio_np = np.frombuffer(raw_data, np.int16).flatten().astype(np.float32) / 32768.0
    
    start_time = time.time()
    segments, info = model.transcribe(audio_np, beam_size=1, language="es")
    
    print(f"Detected language: {info.language} ({info.language_probability:.2f})")
    
    text = ""
    for segment in segments:
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        text += segment.text
        
    print(f"✅ Transcription time: {time.time() - start_time:.2f}s")
    print(f"RESULT: '{text.strip()}'")

except Exception as e:
    print(f"❌ Transcription failed: {e}")
