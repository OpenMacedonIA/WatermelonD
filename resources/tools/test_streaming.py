import sys
import os
import logging
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Mocking modules to isolate logic
from unittest.mock import MagicMock

# Mock dependencies before importing NeoCore
sys.modules['modules.speaker'] = MagicMock()
sys.modules['modules.voice_manager'] = MagicMock()
sys.modules['modules.intent_manager'] = MagicMock()
sys.modules['modules.ai_engine'] = MagicMock()
sys.modules['modules.chat'] = MagicMock()
# sys.modules['modules.keyword_router'] = MagicMock() # Already exists

from modules.chat import ChatManager
from modules.ai_engine import GemmaEngine

# We need to test the logic inside NeoCore.handle_unrecognized_command
# But NeoCore is complex to instantiate. Let's extract the logic or mock everything heavily.
# Actually, let's just test the logic I wrote by subclassing or monkeypatching.

class MockChatManager:
    def get_response_stream(self, text):
        chunks = ["Hola ", "tío. ", "¿Cómo ", "estás? ", "Espero ", "que ", "bien."]
        for c in chunks:
            yield c
            time.sleep(0.1)

class MockNeoCore:
    def __init__(self):
        self.chat_manager = MockChatManager()
        self.spoken_sentences = []
        self.consecutive_failures = 0

    def speak(self, text):
        print(f"SPEAKING: {text}")
        self.spoken_sentences.append(text)

    def handle_unrecognized_command(self, command_text):
        # PASTE LOGIC HERE FOR TESTING
        try:
            stream = self.chat_manager.get_response_stream(command_text)
            
            buffer = ""
            self.consecutive_failures = 0
            
            for chunk in stream:
                buffer += chunk
                
                import re
                parts = re.split(r'([.!?\n])', buffer)
                
                if len(parts) > 1:
                    while len(parts) >= 2:
                        sentence = parts.pop(0) + parts.pop(0)
                        sentence = sentence.strip()
                        if sentence:
                            self.speak(sentence)
                    buffer = "".join(parts)
            
            if buffer.strip():
                self.speak(buffer)
                
        except Exception as e:
            print(f"Error: {e}")

def test_streaming_logic():
    print("--- Testing Streaming Logic ---")
    neo = MockNeoCore()
    neo.handle_unrecognized_command("Hola")
    
    expected = ["Hola tío.", "¿Cómo estás?", "Espero que bien."]
    
    if neo.spoken_sentences == expected:
        print("PASS: Sentences spoken correctly in order.")
    else:
        print(f"FAIL: Expected {expected}, got {neo.spoken_sentences}")

if __name__ == "__main__":
    test_streaming_logic()
