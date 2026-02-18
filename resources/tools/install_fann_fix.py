import os
import subprocess
import sys
import shutil
import tempfile

def install_fann():
    print("Installing FANN C Library and fann2...")
    
    # Check if already installed
    try:
        import fann2
        print("fann2 is already installed. Skipping.")
        return
    except ImportError:
        print("fann2 not found. Proceeding with installation...")

    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        
        # 1. Clone FANN (C Library)
        # This is the official repo and usually public.
        print("Cloning FANN C Library...")
        subprocess.check_call(["git", "clone", "https://github.com/libfann/fann.git"])
        
        # 2. Build and Install FANN C Library
        os.chdir("fann")
        print("Building FANN C Library...")
        # Ensure cmake is installed (install.sh does this)
        subprocess.check_call(["cmake", "."])
        subprocess.check_call(["make"])
        
        print("Installing FANN C Library (requires sudo)...")
        subprocess.check_call(["sudo", "make", "install"])
        
        # Refresh shared libraries
        print("Refreshing shared libraries...")
        subprocess.check_call(["sudo", "ldconfig"])
        
        # 3. Install fann2 via pip
        # Now that headers and libs are in /usr/local, pip install fann2 should work.
        print("Installing fann2 python package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "fann2"])
        
        print("fann2 installed successfully.")
        
    except Exception as e:
        print(f"Error installing fann2: {e}")
        sys.exit(1)
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    install_fann()
