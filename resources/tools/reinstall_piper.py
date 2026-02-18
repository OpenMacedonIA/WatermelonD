import os
import shutil
import urllib.request
import tarfile
import sys
import subprocess

def install_piper():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    piper_dir = os.path.join(project_root, 'piper')
    
    print(f"Removing existing piper directory: {piper_dir}")
    if os.path.exists(piper_dir):
        shutil.rmtree(piper_dir)
        
    # URL for Linux x86_64 (Check for latest version or stable one)
    # Using 2023.11.14-2 release which is known to work
    url = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz"
    tar_path = os.path.join(project_root, "piper_linux_x86_64.tar.gz")
    
    print(f"Downloading Piper from {url}...")
    try:
        urllib.request.urlretrieve(url, tar_path)
        print("Download complete.")
    except Exception as e:
        print(f"Error downloading: {e}")
        return False

    print("Extracting...")
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=project_root)
        print("Extraction complete.")
    except Exception as e:
        print(f"Error extracting: {e}")
        return False
    finally:
        if os.path.exists(tar_path):
            os.remove(tar_path)

    # Test binary
    piper_bin = os.path.join(piper_dir, 'piper')
    print(f"Testing binary: {piper_bin}")
    try:
        subprocess.run([piper_bin, '--version'], check=True)
        print("[OK] Piper installed and working!")
        return True
    except subprocess.CalledProcessError:
        print("[ERROR] Piper binary failed to run (Segfault or other error).")
        return False
    except OSError as e:
        print(f"[ERROR] Could not run piper: {e}")
        return False

if __name__ == "__main__":
    install_piper()
