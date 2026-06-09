import os
import sys
import subprocess

def install_bootstrap():
    """Install minimal dependencies needed for the setup script itself."""
    print("Initializing bootstrap dependencies (requests, tqdm)...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "tqdm"])
        print("✅ Bootstrap complete.\n")
    except Exception as e:
        print(f"❌ Failed to install bootstrap dependencies: {e}")
        sys.exit(1)

def setup():
    # Ensure bootstrap dependencies are present
    try:
        import requests
        from tqdm import tqdm
    except ImportError:
        install_bootstrap()
        import requests
        from tqdm import tqdm

    print("🚀 Starting SentinelX AI Automated Setup...")
    
    # 1. Install Project Dependencies
    print("📦 Installing project requirements from requirements.txt...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except Exception as e:
        print(f"❌ Failed to install project requirements: {e}")
        sys.exit(1)
    
    # 2. Download LLM Model
    model_dir = "models"
    model_name = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    model_path = os.path.join(model_dir, model_name)
    url = "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        
    if not os.path.exists(model_path):
        print(f"📥 Downloading LLM Model: {model_name} (~670MB)...")
        try:
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(model_path, 'wb') as f, tqdm(
                desc=model_name,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for data in response.iter_content(chunk_size=1024):
                    size = f.write(data)
                    bar.update(size)
            print("✅ Model downloaded successfully.")
        except Exception as e:
            print(f"❌ Failed to download model: {e}")
            print("Falling back to rule-based speech engine.")
    else:
        print("✅ LLM Model already exists.")

    print("\n✨ Setup Complete! Launching SentinelX AI...")
    
    # 3. Launch the Application
    # Using Popen so the script can finish while the app runs
    try:
        subprocess.Popen([sys.executable, "main.py"])
        print("\n🌐 Platform running at http://localhost:8000")
        print("💬 Robot Voice is active. Dashboard accessible via UI.")
        print("Keep this terminal open to see system logs.")
    except Exception as e:
        print(f"❌ Failed to launch application: {e}")

if __name__ == "__main__":
    setup()
