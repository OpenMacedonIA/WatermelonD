import os
import sys
import pyaudio
import numpy as np
import struct
import logging
import json

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AudioDebugTargeted")

def debug_targeted():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2 # Stereo
    RATE = 48000 # HD Audio standard
    DEVICE_INDEX = 9 # Stereo Mic
    
    p = pyaudio.PyAudio()
    
    logger.info(f"--- Testing Device {DEVICE_INDEX} @ {RATE}Hz, {CHANNELS} Channels ---")
    
    try:
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, 
                        frames_per_buffer=CHUNK, input_device_index=DEVICE_INDEX)
        
        frames = []
        max_rms = 0
        
        logger.info("Recording 3 seconds...")
        for i in range(0, int(RATE / CHUNK * 3)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            
            shorts = struct.unpack("%dh" % (len(data) / 2), data)
            rms = np.sqrt(np.mean(np.square(shorts)))
            if rms > max_rms:
                max_rms = rms
            
            # Visual feedback
            if i % 10 == 0:
                bars = "#" * int(rms / 100)
                sys.stdout.write(f"\rRMS: {int(rms)} {bars}")
                sys.stdout.flush()
        
        print("\nRecording finished.")
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        logger.info(f"Max RMS: {max_rms}")
        
        if max_rms > 100:
            logger.info("Signal Detected!")
            
            # Transcribe
            logger.info("Attempting Transcription (Vosk)...")
            try:
                import vosk
                if os.path.exists("vosk-models/es-large"):
                    model = vosk.Model("vosk-models/es-large")
                else:
                    model = vosk.Model("vosk-models/es")
                
                # Convert Stereo to Mono for Vosk
                raw_data = b''.join(frames)
                audio_int16 = np.frombuffer(raw_data, np.int16)
                audio_mono = audio_int16.reshape(-1, 2)[:, 0] # Left channel
                raw_data_mono = audio_mono.tobytes()
                
                # Resample if needed (Vosk needs 16k usually, but let's see if it accepts 48k with SetSampleRate)
                # Actually Vosk Model is usually 16k. We MUST resample.
                # Simple decimation: 48000 -> 16000 is factor of 3.
                audio_mono_16k = audio_mono[::3]
                raw_data_resampled = audio_mono_16k.tobytes()
                
                rec = vosk.KaldiRecognizer(model, 16000)
                rec.AcceptWaveform(raw_data_resampled)
                res = json.loads(rec.FinalResult())
                logger.info(f"Transcription: '{res.get('text', '')}'")
                
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                
        else:
            logger.warning("Silence detected.")
            
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    debug_targeted()
