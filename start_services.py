import subprocess
import time
import sys
import os
import signal

# Services to start
SERVICES = [
    "modules/message_bus.py",
    "modules/services/audio_service.py",
    "modules/services/stt_service.py",
    "modules/services/nlu_service.py",
    "modules/services/skills_service.py",
    "modules/services/tts_service.py",
    "modules/services/web_service.py"
]

processes = []

def main():
    print("Starting TIO AI (OVOS Architecture)...")
    
    # Ensure logs directory exists
    if not os.path.exists("logs"):
        os.makedirs("logs")
        
    # Open log file
    log_file = open("logs/app.log", "a")
    
    # Helper to start service
    def start_service(script):
        print(f"Starting {script}...")
        # Redirect stdout and stderr to log file
        p = subprocess.Popen([sys.executable, script], stdout=log_file, stderr=log_file, bufsize=0)
        processes.append(p)
        return p

    # 1. Start Bus first
    bus_p = start_service(SERVICES[0])
    time.sleep(2) # Wait for bus
    
    # 2. Start other services
    for script in SERVICES[1:]:
        start_service(script)
        time.sleep(1)
        
    print("All services started. Logs are being written to logs/app.log")
    
    try:
        bus_p.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
        for p in processes:
            p.terminate()
        print("Done.")
    finally:
        log_file.close()

if __name__ == "__main__":
    main()
