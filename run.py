import sys
import os
import time
import subprocess
import signal
import argparse

# Ensure current working directory is project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# Set PYTHONPATH
os.environ["PYTHONPATH"] = BASE_DIR


def print_banner():
    banner = """
    ===============================================================
       ⚡ DESIFIT — AI FITNESS COMPANION (FASTAPI + STREAMLIT) ⚡
    ===============================================================
       Backend API:       http://127.0.0.1:8000
       Swagger Docs:      http://127.0.0.1:8000/docs
       Frontend App:      http://localhost:8501
    ===============================================================
    """
    print(banner)


def run_services(mode="all"):
    processes = []
    print_banner()

    try:
        # Start Backend
        if mode in ["all", "backend"]:
            print("[INFO] Starting FastAPI Backend on http://127.0.0.1:8000 ...")
            backend_cmd = [
                sys.executable, "-m", "uvicorn", "backend.main:app",
                "--host", "127.0.0.1",
                "--port", "8000",
                "--reload"
            ]
            backend_proc = subprocess.Popen(backend_cmd, cwd=BASE_DIR)
            processes.append(backend_proc)

        # Brief pause to allow backend initialization
        if mode == "all":
            time.sleep(2)

        # Start Frontend
        if mode in ["all", "frontend"]:
            print("[INFO] Starting Streamlit Frontend on http://localhost:8501 ...")
            frontend_cmd = [
                sys.executable, "-m", "streamlit", "run", "frontend/app.py",
                "--server.port", "8501",
                "--server.address", "localhost",
                "--browser.gatherUsageStats", "false"
            ]
            frontend_proc = subprocess.Popen(frontend_cmd, cwd=BASE_DIR)
            processes.append(frontend_proc)

        print("\n[SUCCESS] DesiFit services are active! Press Ctrl+C to terminate both servers cleanly.\n")

        # Keep parent script alive
        while True:
            for p in processes:
                ret = p.poll()
                if ret is not None:
                    print(f"[WARN] Process {p.args} exited with code {ret}")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[INFO] Gracefully shutting down DesiFit services...")
    finally:
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                p.kill()
        print("[INFO] All services stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DesiFit Unified Launcher")
    parser.add_argument(
        "--mode",
        choices=["all", "backend", "frontend"],
        default="all",
        help="Choose which services to start (default: all)"
    )
    args = parser.parse_args()
    run_services(mode=args.mode)
