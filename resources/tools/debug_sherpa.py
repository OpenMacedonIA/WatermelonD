import os
import sys

# Explicitly add venv site-packages
venv_site = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../venv/lib/python3.14/site-packages"))
if os.path.exists(venv_site):
    sys.path.append(venv_site)

import time
import wave
import struct
import numpy as np
import pyaudio
import sherpa_onnx

def main():
    print("--- Sherpa-ONNX Debug Tool ---")
    
    # 1. Model Paths
    model_dir = "models/sherpa"
    encoder = os.path.join(model_dir, "tiny-encoder.onnx")
    decoder = os.path.join(model_dir, "tiny-decoder.onnx")
    tokens = os.path.join(model_dir, "tiny-tokens.txt")
    
    if not os.path.exists(encoder):
        print(f"Error: Model not found in {model_dir}")
        return

    print(f"Loading model from {model_dir}...")
    try:
        recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=encoder,
            decoder=decoder,
            tokens=tokens,
            language="es",
            task="transcribe",
            num_threads=1
        )
        print("Model loaded successfully (Offline Whisper).")
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # 2. Audio Setup
    p = pyaudio.PyAudio()
    print("\n--- Audio Devices ---")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f"Index {i}: {info['name']}")
            
    device_index = int(input("\nEnter microphone device index (default 4): ") or 4)
    
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    print(f"\nOpening stream on device {device_index}...")
    try:
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                        frames_per_buffer=CHUNK, input_device_index=device_index)
        stream.start_stream()
    except Exception as e:
        print(f"Error opening stream: {e}")
        return

    print("\nListening... (Press Ctrl+C to stop)")
    print("Note: Whisper is offline. Speak, then pause to see result.")
    
    audio_buffer = []
    silence_frames = 0
    is_recording = False
    THRESHOLD = 500 # Adjust based on mic
    SILENCE_LIMIT = 30 # ~1.5 seconds of silence
    
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            shorts = struct.unpack("%dh" % (len(data) / 2), data)
            rms = np.sqrt(np.mean(np.square(shorts)))
            
            if rms > THRESHOLD:
                is_recording = True
                silence_frames = 0
            else:
                if is_recording:
                    silence_frames += 1
            
            if is_recording:
                audio_buffer.append(data)
                
                if silence_frames > SILENCE_LIMIT:
                    # End of speech detected
                    print("\nProcessing...", end="", flush=True)
                    
                    raw_data = b''.join(audio_buffer)
                    samples = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    s = recognizer.create_stream()
                    s.accept_waveform(RATE, samples)
                    recognizer.decode_stream(s)
                    text = s.result.text
                    
                    print(f"\rRecognized: {text}")
                    
                    audio_buffer = []
                    is_recording = False
                    silence_frames = 0
                    print("Listening...", end="", flush=True)
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    main()
