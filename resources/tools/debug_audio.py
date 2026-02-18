import os
import sys
import pyaudio
import numpy as np
import struct
import time
import logging
import json

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AudioDebug")

def debug_audio():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    THRESHOLD = 500 # Lower threshold for debugging
    
    p = pyaudio.PyAudio()
    
    # List devices
    logger.info("--- Audio Devices ---")
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            logger.info(f"Index {i}: {dev['name']}")
    
    # Try to load Whisper or Vosk
    logger.info("\n--- Loading STT Engine ---")
    model = None
    engine_type = None
    
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("medium", device="cpu", compute_type="int8", download_root="models/whisper")
        engine_type = "whisper"
        logger.info("Whisper loaded successfully.")
    except Exception as e:
        logger.warning(f"Failed to load Whisper: {e}")
        logger.info("Trying Vosk...")
        try:
            import vosk
            if os.path.exists("vosk-models/es-large"):
                model = vosk.Model("vosk-models/es-large")
                engine_type = "vosk"
                logger.info("Vosk loaded successfully (es-large).")
            elif os.path.exists("vosk-models/es"):
                model = vosk.Model("vosk-models/es")
                engine_type = "vosk"
                logger.info("Vosk loaded successfully (es).")
            else:
                logger.error("Vosk model not found in vosk-models/es-large or vosk-models/es")
        except Exception as e:
            logger.error(f"Failed to load Vosk: {e}")

    if not model:
        logger.error("No STT engine available.")
        return

    # Candidate devices to test
    candidates = [6, 10, 9, 8, 7, 4] # Pipewire, Default, Stereo Mic, Digital Mic, etc.
    rates = [16000, 44100, 48000]
    channels_list = [1, 2]
    
    working_index = None
    working_rate = 16000
    working_channels = 1
    
    for idx in candidates:
        for rate in rates:
            for channels in channels_list:
                logger.info(f"\n--- Testing Device {idx} @ {rate}Hz, {channels} Channels ---")
                try:
                    stream = p.open(format=FORMAT, channels=channels, rate=rate, input=True, 
                                    frames_per_buffer=CHUNK, input_device_index=idx)
                    
                    frames = []
                    max_rms = 0
                    
                    # Record 1 second
                    for i in range(0, int(rate / CHUNK * 1)):
                        data = stream.read(CHUNK, exception_on_overflow=False)
                        frames.append(data)
                        
                        shorts = struct.unpack("%dh" % (len(data) / 2), data)
                        rms = np.sqrt(np.mean(np.square(shorts)))
                        if rms > max_rms:
                            max_rms = rms
                    
                    stream.stop_stream()
                    stream.close()
                    
                    logger.info(f"Device {idx} @ {rate}Hz ({channels}ch) Max RMS: {max_rms}")
                    
                    if max_rms > 100: 
                        logger.info(f"!!! Signal detected on Device {idx} @ {rate}Hz ({channels}ch) !!!")
                        working_index = idx
                        working_rate = rate
                        working_channels = channels
                        break
                    else:
                        logger.warning(f"Device {idx} @ {rate}Hz ({channels}ch) seems silent.")
                        
                except Exception as e:
                    logger.error(f"Error testing device {idx} @ {rate}Hz ({channels}ch): {e}")
            
            if working_index is not None: break
        if working_index is not None: break

    if working_index is None:
        logger.error("No working microphone found.")
        p.terminate()
        return

    # Transcribe using working index
    logger.info(f"\n--- Transcribing with Device {working_index} @ {working_rate}Hz ({working_channels}ch) ---")
    
    stream = p.open(format=FORMAT, channels=working_channels, rate=working_rate, input=True, 
                    frames_per_buffer=CHUNK, input_device_index=working_index)
    
    frames = []
    logger.info("Please speak now...")
    for i in range(0, int(working_rate / CHUNK * 5)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    logger.info(f"Transcribing with {engine_type}...")
    raw_data = b''.join(frames)
    
    # Convert to Mono if Stereo
    if working_channels == 2:
        # 16-bit stereo is L(2 bytes) R(2 bytes). We can just take L.
        # Numpy approach: reshape to (-1, 2), take column 0
        audio_int16 = np.frombuffer(raw_data, np.int16)
        audio_mono = audio_int16.reshape(-1, 2)[:, 0] # Take left channel
        raw_data = audio_mono.tobytes()
        logger.info("Converted Stereo to Mono.")
    
    # Resample logic (simplified)
    if working_rate != 16000:
         logger.warning("Resampling skipped. Transcription may fail.")

    if engine_type == "whisper":
        audio_np = np.frombuffer(raw_data, np.int16).flatten().astype(np.float32) / 32768.0
        if working_rate == 16000:
            segments, _ = model.transcribe(audio_np, beam_size=1, language="es")
            text = " ".join([segment.text for segment in segments]).strip()
        else:
            text = "SKIPPED (Rate mismatch)"
            
    elif engine_type == "vosk":
        if working_rate == 16000:
            rec = vosk.KaldiRecognizer(model, RATE)
            rec.AcceptWaveform(raw_data)
            res = json.loads(rec.FinalResult())
            text = res.get('text', '')
        else:
             text = "SKIPPED (Rate mismatch)"
    
    logger.info(f"Transcription: '{text}'")

if __name__ == "__main__":
    debug_audio()
