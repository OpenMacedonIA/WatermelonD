#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def check_command(cmd):
    return shutil.which(cmd) is not None

def run_test(name, cmd, ignore_fail=False):
    print(f"\n[TEST] {name}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] PASS")
            return True
        else:
            print(f"[ERROR] FAIL")
            print(f"   Error: {result.stderr.strip()}")
            print(f"   Output: {result.stdout.strip()}")
            return False
    except Exception as e:
        print(f"[ERROR] ERROR: {e}")
        return False

def main():
    print_header("NEO AUDIO DIAGNOSTIC TOOL")
    
    # 1. Check User and Environment
    print_header("1. Environment Variables")
    print(f"User: {os.environ.get('USER')}")
    print(f"Home: {os.environ.get('HOME')}")
    print(f"XDG_RUNTIME_DIR: {os.environ.get('XDG_RUNTIME_DIR', 'Not Set')}")
    print(f"PULSE_SERVER: {os.environ.get('PULSE_SERVER', 'Not Set')}")
    print(f"PULSE_COOKIE: {os.environ.get('PULSE_COOKIE', 'Not Set')}")

    # 2. Check PulseAudio
    print_header("2. PulseAudio Connection")
    if check_command('pactl'):
        run_test("PulseAudio Info", "pactl info")
    else:
        print("[WARN] 'pactl' not found. Skipping.")

    if check_command('aplay'):
        run_test("ALSA Playback Devices", "aplay -l")

    # 3. Check Piper
    print_header("3. Piper TTS")
    
    # Resolve project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    
    piper_bin = os.path.join(project_root, 'piper', 'piper')
    
    if os.path.exists(piper_bin):
        print(f"Piper binary found at: {piper_bin}")
        
        # Check permissions
        if os.access(piper_bin, os.X_OK):
            print("[OK] Piper is executable")
        else:
            print("[ERROR] Piper is NOT executable. Attempting fix...")
            try:
                os.chmod(piper_bin, 0o755)
                print("[OK] Permissions fixed.")
            except Exception as e:
                print(f"[ERROR] Failed to fix permissions: {e}")

        # Test Execution
        model_path = os.path.join(project_root, 'piper', 'voices', 'es_ES-davefx-medium.onnx')
        if os.path.exists(model_path):
            print(f"[OK] Voice model found: {model_path}")
            test_cmd = f'echo "Hola, esto es una prueba." | "{piper_bin}" --model "{model_path}" --output_file /dev/null'
            run_test("Piper Generation (Dry Run)", test_cmd)
        else:
            print(f"[ERROR] Voice model NOT found at: {model_path}")
    else:
        print(f"[ERROR] Piper binary NOT found at: {piper_bin}")

    # 4. Check Service File (User Mode)
    print_header("4. Service Configuration (User Mode)")
    user_service_file = os.path.expanduser("~/.config/systemd/user/neo.service")
    if os.path.exists(user_service_file):
        print(f"[OK] User Service file found at {user_service_file}")
        try:
            with open(user_service_file, 'r') as f:
                content = f.read()
                if "XDG_RUNTIME_DIR" in content:
                    print("ℹ️ Note: XDG_RUNTIME_DIR is not strictly needed in user service file (it's inherited), but good if present in install script logic.")
        except Exception as e:
            print(f"[WARN] Cannot read service file: {e}")
    else:
        print(f"[ERROR] User Service file NOT found at {user_service_file}")

    # 5. Interactive Audio Test
    print_header("5. Interactive Audio Test")
    print("Testing audio playback (aplay)...")
    try:
        # Generate a simple beep using sox or just use aplay with /dev/urandom (risky) or just check device
        # Better: Try to play a known file if exists, or just list devices again
        run_test("List Playback Devices", "aplay -l")
        
        print("\n--- Generating Test Audio with Piper ---")
        test_wav = "test_audio.wav"
        piper_bin = os.path.join(project_root, 'piper', 'piper')
        model_path = os.path.join(project_root, 'piper', 'voices', 'es_ES-davefx-medium.onnx')
        
        if os.path.exists(piper_bin) and os.path.exists(model_path):
            cmd = f'echo "Prueba de audio del sistema Neo." | "{piper_bin}" --model "{model_path}" --output_file "{test_wav}"'
            if run_test("Generate Test WAV", cmd):
                print(f"Playing {test_wav}...")
                run_test("Play Test WAV", f'aplay "{test_wav}"')
                if os.path.exists(test_wav): os.remove(test_wav)
        else:
            print("Skipping playback test (Piper not ready).")

    except Exception as e:
        print(f"[ERROR] Audio Test Failed: {e}")

    print_header("DIAGNOSTIC COMPLETE")

if __name__ == "__main__":
    main()
