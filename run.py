import os
import sys
import subprocess
import time
import webbrowser
import threading


def stream(proc, prefix):
    for line in iter(proc.stdout.readline, b""):
        print(f"[{prefix}] {line.decode(errors='replace').rstrip()}", flush=True)


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    backend = os.path.join(root, "backend")
    frontend = os.path.join(root, "frontend")
    venv = os.path.join(root, ".venv")

    win = os.name == "nt"
    py = os.path.join(venv, "Scripts", "python.exe") if win else os.path.join(venv, "bin", "python")
    pip = os.path.join(venv, "Scripts", "pip.exe") if win else os.path.join(venv, "bin", "pip")
    npm = "npm.cmd" if win else "npm"

    print("=" * 54)
    print("  AutoDocThinker - Initializing...")
    print("=" * 54)

    if not os.path.exists(venv):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", venv], check=True)

    print("Installing backend dependencies...")
    subprocess.run([pip, "install", "-r", os.path.join(backend, "requirements.txt")], check=True)

    if not os.path.exists(os.path.join(frontend, "node_modules")):
        print("Installing frontend dependencies...")
        subprocess.run([npm, "install"], cwd=frontend, check=True)

    print("\nStarting services...")

    env = {**os.environ, "PYTHONPATH": backend}
    be = subprocess.Popen(
        [py, "run.py"],
        cwd=backend,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    fe = subprocess.Popen(
        [npm, "run", "dev"],
        cwd=frontend,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    threading.Thread(target=stream, args=(be, "backend"), daemon=True).start()
    threading.Thread(target=stream, args=(fe, "frontend"), daemon=True).start()

    print("\n  Backend  ->  http://localhost:8000")
    print("  Frontend ->  http://localhost:5173")
    print("\n  Press Ctrl+C to stop.\n")

    opened = threading.Event()

    def delayed_open():
        opened.wait(timeout=4)
        if not opened.is_set():
            webbrowser.open("http://localhost:5173")

    threading.Thread(target=delayed_open, daemon=True).start()

    try:
        while be.poll() is None and fe.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        opened.set()
    finally:
        print("\nShutting down...")
        for p in (be, fe):
            try:
                p.terminate()
            except Exception:
                pass
        print("Stopped.")


if __name__ == "__main__":
    main()
