import os
import requests
import tarfile
import shutil

PIPER_URL = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz"
INSTALL_DIR = "piper_bin"

def download_and_extract():
    if not os.path.exists(INSTALL_DIR):
        os.makedirs(INSTALL_DIR)
    
    tar_path = os.path.join(INSTALL_DIR, "piper.tar.gz")
    
    print(f"Downloading Piper binary from {PIPER_URL}...")
    response = requests.get(PIPER_URL, stream=True)
    if response.status_code == 200:
        with open(tar_path, 'wb') as f:
            f.write(response.content)
        print("Download complete.")
        
        print("Extracting...")
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=INSTALL_DIR)
        print("Extraction complete.")
        
        # Cleanup
        os.remove(tar_path)
        
        # Verify
        piper_exe = os.path.join(INSTALL_DIR, "piper", "piper")
        if os.path.exists(piper_exe):
            print(f"Piper binary installed at: {piper_exe}")
            # Make executable
            os.chmod(piper_exe, 0o755)
            return True
        else:
            print("Error: Piper binary not found after extraction.")
            return False
    else:
        print(f"Failed to download. Status code: {response.status_code}")
        return False

if __name__ == "__main__":
    download_and_extract()
