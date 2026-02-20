import subprocess
import sys
import os
import time

# Global flag for shutdown
shutdown_flag = False

def setup_env():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")

    print(" Initializing InformaTruth...")

    # Python deps check
    req_file = os.path.join(backend_dir, "requirements.txt")
    if os.path.exists(req_file):
        print(" Checking backend dependencies...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file], check=False)
        except:
            print(" Manual pip install might be needed.")

    # Frontend node_modules check
    node_modules = os.path.join(frontend_dir, "node_modules")
    if not os.path.exists(node_modules):
        print(" node_modules missing. Running npm install...")
        npm = "npm.cmd" if sys.platform == "win32" else "npm"
        try:
            subprocess.run([npm, "install"], cwd=frontend_dir, check=True, shell=(sys.platform == "win32"))
        except Exception as e:
            print(f" Failed to install frontend deps: {e}")
            sys.exit(1)

    # Quick model check
    model_path = os.path.join(backend_dir, "fine_tuned_liar_detector", "adapter_model.safetensors")
    if os.path.exists(model_path):
        if os.path.getsize(model_path) < 1000000:
            print("-" * 50)
            print("CRITICAL: adapter_model.safetensors looks like a Git LFS pointer!")
            print("Please download the actual 4.7MB file to the detector folder.")
            print("-" * 50)
            time.sleep(2)
    else:
        print(f"!! Missing model file: {model_path}")

    return backend_dir, frontend_dir

def main():
    backend_dir, frontend_dir = setup_env()

    print("\n Booting services...")
    
    # Start Backend
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=backend_dir,
        shell=False
    )

    # Start Frontend
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_process = subprocess.Popen(
        [npm, "run", "dev"],
        cwd=frontend_dir,
        shell=False
    )

    print(f"\nAPI: http://127.0.0.1:8000")
    print(f"UI:  http://localhost:5173\n")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
            if backend_process.poll() is not None or frontend_process.poll() is not None:
                print("!! One of the services stopped unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\n Shutting down...")
    finally:
        if backend_process.poll() is None:
            backend_process.terminate()
        
        if frontend_process.poll() is None:
            if sys.platform == 'win32':
                 subprocess.run(["taskkill", "/F", "/T", "/PID", str(frontend_process.pid)], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                frontend_process.terminate()
        
        print("Cleanup done.")

if __name__ == "__main__":
    main()
