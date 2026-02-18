import os
import sys
import json
import pyaudio
import numpy as np
import struct
import logging
import time

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AudioDebugV2")

def load_config():
    try:
        with open('config/config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return None

def debug_audio_v2():
    config = load_config()
    if not config: return

    stt_config = config.get('stt', {})
    device_index = stt_config.get('input_device_index')
    model_path = stt_config.get('model_path')
    engine = stt_config.get('engine')
    
    logger.info(f"--- Configured Settings ---")
    logger.info(f"Engine: {engine}")
    logger.info(f"Device Index: {device_index}")
    logger.info(f"Model Path: {model_path}")
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    # Verify Device
    try:
        dev_info = p.get_device_info_by_index(device_index)
        logger.info(f"Device Name: {dev_info.get('name')}")
        logger.info(f"Max Input Channels: {dev_info.get('maxInputChannels')}")
        logger.info(f"Default Sample Rate: {dev_info.get('defaultSampleRate')}")
    except Exception as e:
        logger.error(f"Error getting device info: {e}")
        return

    # Load Vosk
    logger.info("Loading Vosk...")
    try:
        import vosk
        if os.path.exists(model_path):
            model = vosk.Model(model_path)
            logger.info("Vosk loaded.")
        else:
            logger.error(f"Model path does not exist: {model_path}")
            return
    except Exception as e:
        logger.error(f"Error loading Vosk: {e}")
        return

    # Record
    CHUNK = 8192
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    logger.info(f"--- Recording from Device {device_index} ---")
    
    try:
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                        frames_per_buffer=CHUNK, input_device_index=device_index)
        
        rec = vosk.KaldiRecognizer(model, RATE)
        
        logger.info("Please speak now (Listening for 10s)...")
        start_time = time.time()
        
        while time.time() - start_time < 10:
            data = stream.read(4096, exception_on_overflow=False)
            
            # Check RMS
            shorts = struct.unpack("%dh" % (len(data) / 2), data)
            rms = np.sqrt(np.mean(np.square(shorts)))
            
            if rms > 100:
                sys.stdout.write(f"\rRMS: {int(rms)} (Signal!)")
            else:
                sys.stdout.write(f"\rRMS: {int(rms)}")
            sys.stdout.flush()
            
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                if res.get('text'):
                    print(f"\nRECOGNIZED: {res.get('text')}")
            else:
                partial = json.loads(rec.PartialResult())
                if partial.get('partial'):
                    sys.stdout.write(f" [Partial: {partial.get('partial')}]")
                    
        print("\nFinished.")
        stream.stop_stream()
        stream.close()
        p.terminate()
        
    except Exception as e:
        logger.error(f"Error during recording: {e}")

if __name__ == "__main__":
    debug_audio_v2()
