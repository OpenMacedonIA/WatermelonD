import sys
import os
import queue
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from modules.speaker import Speaker

# Mock Logger
logging.basicConfig(level=logging.INFO)

def test_speaker_fillers():
    print("--- Testing Speaker Fillers ---")
    event_queue = queue.Queue()
    speaker = Speaker(event_queue)
    
    # Override engine to dummy to avoid actual audio hardware checks failing if not present
    speaker.engine = 'dummy' 
    speaker.is_available = True

    print("Calling play_random_filler()...")
    speaker.play_random_filler()
    
    if not speaker.speak_queue.empty():
        item = speaker.speak_queue.get()
        print(f"Queue Item: {item}")
        
        if isinstance(item, dict) and item.get('type') == 'wav':
            path = item.get('path')
            if os.path.exists(path) and "resources/sounds/fillers" in path:
                print(f"PASS: Queued a valid filler file: {path}")
            else:
                print(f"FAIL: Path invalid or not in fillers dir: {path}")
        else:
            print("FAIL: Item in queue is not a WAV dict.")
    else:
        print("FAIL: Queue is empty after calling play_random_filler.")

if __name__ == "__main__":
    test_speaker_fillers()
