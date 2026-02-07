#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FixTool")

# Ensure correct working directory
if os.getcwd().endswith("tools"):
    os.chdir("../../")

# Add project root to path
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

from modules.config_manager import ConfigManager

def fix_config():
    print("\n[1/2] Fixing Configuration...")
    cm = ConfigManager()
    
    # 1. Update STT Engine to Vosk
    current_stt = cm.get("stt", {})
    if current_stt.get("engine") != "vosk":
        logger.info("Setting STT Engine to 'vosk'...")
        current_stt["engine"] = "vosk"
        current_stt["input_device_index"] = 10
        cm.set("stt", current_stt)
        print("[OK] Config updated: STT=vosk, Device=10")
    else:
        print("Config already correct.")

def download_model():
    print("\n[2/2] Checking Vosk Model...")
    model_path = "vosk-models/es"
    
    if os.path.exists(model_path):
        print("Vosk model directory found. Assuming it's valid.")
        return

    print("Model missing. Downloading now (this might take a minute)...")
    
    # Path to the downloader script
    downloader = "resources/tools/download_vosk_model.py"
    
    if not os.path.exists(downloader):
        logger.error(f"Downloader script not found at {downloader}")
        return

    # Execute using the SAME interpreter as this script (which should be the venv one)
    try:
        subprocess.check_call([sys.executable, downloader])
        print("\n[OK] Model download completed successfully!")
    except subprocess.CalledProcessError as e:
        logger.error(f"Model download failed with code {e.returncode}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    print("==========================================")
    print("   NEO AUTO-REPAIR TOOL")
    print("==========================================")
    
    try:
        fix_config()
        download_model()
        print("\nRepair finished. Please try starting the service again.")
    except Exception as e:
        logger.error(f"Critical error: {e}")
