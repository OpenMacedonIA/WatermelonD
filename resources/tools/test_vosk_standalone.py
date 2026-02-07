#!/usr/bin/env python3
import vosk
import wave
import sys
import os
import json

def test_vosk(model_path, audio_file):
    print(f"Testing Vosk Model at: {model_path}")
    print(f"Using Audio File: {audio_file}")
    
    if not os.path.exists(model_path):
        print("[ERROR] Model path not found.")
        return

    if not os.path.exists(audio_file):
        print("[ERROR] Audio file not found. Run the service and speak to generate it.")
        return

    try:
        print("Loading model... (this may take a few seconds)")
        model = vosk.Model(model_path)
        print("[OK] Model loaded successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to load model: {e}")
        return

    try:
        wf = wave.open(audio_file, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            print("[ERROR] Audio file must be WAV format mono PCM.")
            return
            
        rate = wf.getframerate()
        print(f"Audio Rate: {rate} Hz")
        
        rec = vosk.KaldiRecognizer(model, rate)
        
        print("Processing audio...")
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                print(f"Result: {res.get('text', '')}")
        
        res = json.loads(rec.FinalResult())
        print(f"Final Result: {res.get('text', '')}")
        
        if not res.get('text'):
            print("[WARN] No text recognized. Possible reasons:")
            print("   - Audio volume too low")
            print("   - Wrong language model")
            print("   - Audio contains only noise")
            
    except Exception as e:
        print(f"[ERROR] Error during recognition: {e}")

if __name__ == "__main__":
    test_vosk("vosk-models/es", "debug_last_audio.wav")
