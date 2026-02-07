#!/usr/bin/env python3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

try:
    from modules.chat import ChatManager
    from modules.ai_engine import GemmaEngine
except ImportError as e:
    print("\n[ERROR] Error: Missing dependencies.")
    print(f"   {e}")
    print("\n[WARN]  Please ensure you are running this script within the virtual environment:")
    print("   ./venv/bin/python3 resources/tools/test_chat_interactive.py")
    print("\nIf the venv is broken, recreate it:")
    print("   ~/.pyenv/versions/3.10.13/bin/python -m venv venv")
    print("   ./venv/bin/pip install -r requirements.txt")
    sys.exit(1)

def main():
    print("Initializing Gemma Engine (this may take a moment)...")
    engine = GemmaEngine()
    chat = ChatManager(ai_engine=engine)
    
    if not engine.is_ready:
        print("[ERROR] Error: Engine failed to load.")
        return

    print("\n[OK] TIO Chat Interactive Mode")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            
            response = chat.get_response(user_input)
            print(f"TIO: {response}\n")
            
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
