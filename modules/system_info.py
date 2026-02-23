import platform
import flask
import requests
import sys
import os
import subprocess
try:
    import psutil
except ImportError:
    psutil = None

def get_system_info():
    info = {
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
        },
        "python": {
            "version": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "compiler": platform.python_compiler()
        },
        "app": {
            "name": "Neo Core",
            "version": "2.5.0",
            "type": "Modular AI Assistant"
        },
        "libraries": {
            "flask": flask.__version__,
            "requests": requests.__version__,
        }
    }
    
    # Intentar obtener info de git
    try:
        commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], stderr=subprocess.DEVNULL).decode().strip()
        info['app']['commit'] = commit
    except:
        info['app']['commit'] = "Unknown"

    if psutil:
        info['libraries']['psutil'] = psutil.__version__

    return info
