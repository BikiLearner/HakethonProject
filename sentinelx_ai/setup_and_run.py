import os
import sys
import subprocess
import zipfile
import io

def install_bootstrap():
    """Install minimal dependencies needed for the setup script itself."""
    print("Initializing bootstrap dependencies (requests, tqdm)...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "tqdm"])
        print("✅ Bootstrap complete.\n")
    except Exception as e:
        print(f"❌ Failed to install bootstrap dependencies: {e}")
        sys.exit(1)

def download_and_extract(url, destination_dir, name):
    import requests
    from tqdm import tqdm
    
    zip_path = os.path.join(destination_dir, f"{name}.zip")
    
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
        
    print(f"📥 Downloading {name}...")
    try:
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(zip_path, 'wb') as f, tqdm(
            desc=name,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                size = f.write(data)
                bar.update(size)
        
        print(f"📦 Extracting {name}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(destination_dir)
        
        os.remove(zip_path)
        print(f"✅ {name} ready.")
    except Exception as e:
        print(f"❌ Failed to setup {name}: {e}")

def setup():
    # Ensure bootstrap dependencies are present
    try:
        import requests
        from tqdm import tqdm
    except ImportError:
        install_bootstrap()
        import requests
        from tqdm import tqdm

    print("🚀 Starting SentinelX AI V5 Automated Setup...")
    
    # 1. Install Project Dependencies
    print("📦 Installing project requirements from requirements.txt...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except Exception as e:
        print(f"❌ Failed to install project requirements: {e}")
        sys.exit(1)
    
    # 2. Download Vosk STT Model (Essential for V5 Voice)
    vosk_model_dir = "models"
    vosk_model_name = "vosk-model-small-en-us-0.15"
    vosk_path = os.path.join(vosk_model_dir, vosk_model_name)
    vosk_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    
    if not os.path.exists(vosk_path):
        download_and_extract(vosk_url, vosk_model_dir, vosk_model_name)
    else:
        print("✅ Vosk STT Model already exists.")

    # 3. Check for Ollama (The Brain of V5)
    print("🧠 Checking for local Ollama server...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            print("✅ Ollama is running.")
        else:
            print("⚠️ Ollama is installed but not running. Please start Ollama for advanced reasoning.")
    except:
        print("❌ Ollama not detected. Please install Ollama from https://ollama.com for full V5 features.")

    print("\n✨ Setup Complete! Launching SentinelX AI...")
    
    # 4. Launch the Application
    try:
        # On Windows, we use start to open a new terminal
        if os.name == 'nt':
            subprocess.Popen(["start", "cmd", "/k", sys.executable, "main.py"], shell=True)
        else:
            subprocess.Popen([sys.executable, "main.py"])
            
        print("\n🌐 Platform running at http://localhost:8000")
        print("🤖 Industrial Robot Face: http://localhost:8000/robot.html")
        print("📊 Dashboard: http://localhost:8000/index.html")
        print("⚙️ Config: http://localhost:8000/upload.html")
        print("\nKeep the new terminal window open to see system logs.")
    except Exception as e:
        print(f"❌ Failed to launch application: {e}")

if __name__ == "__main__":
    setup()
