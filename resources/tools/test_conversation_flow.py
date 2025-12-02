import time
import sys

def simulate_conversation_flow():
    print("=== Conversation Flow Simulation ===")
    print("This tool simulates how the active listening window works.")
    
    active_listening_end_time = 0
    
    while True:
        print(f"\n[State] Active Listening: {'YES' if time.time() < active_listening_end_time else 'NO'}")
        if time.time() < active_listening_end_time:
            remaining = int(active_listening_end_time - time.time())
            print(f"[Timer] Remaining: {remaining}s")
        
        user_input = input("You say: ").strip().lower()
        
        if not user_input:
            continue
            
        if user_input == "exit":
            break
            
        # Logic Simulation
        is_active = time.time() < active_listening_end_time
        wake_word_detected = "tio" in user_input or "tío" in user_input
        
        if is_active:
            print(f"-> [System] Processed directly (Continuous Mode).")
            # Simulate successful intent
            print("-> [System] Intent executed.")
            active_listening_end_time = time.time() + 10
            print("-> [System] Timer extended by 10s.")
            
        elif wake_word_detected:
            print(f"-> [System] Wake word detected.")
            print("-> [System] Intent executed.")
            active_listening_end_time = time.time() + 10
            print("-> [System] Timer started (10s).")
            
        else:
            print("-> [System] Ignored (Waiting for wake word).")

if __name__ == "__main__":
    simulate_conversation_flow()
