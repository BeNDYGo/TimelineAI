import subprocess
import sys
import os

def run():
    path = sys.executable
    base = os.path.dirname(os.path.abspath(__file__))

    services = [
        ("AI", 4003, "BaseAI/API-AI.py"),
    ]

    procs = []
    for name, port, script in services:
        p = subprocess.Popen(
            [path, os.path.join(base, script)],
            cwd=base,
        )
        procs.append((name, p))
        print(f"[{name}] запущен на порту {port} (pid {p.pid})")

    try:
        for name, p in procs:
            p.wait()
    except KeyboardInterrupt:
        for name, p in procs:
            p.terminate()

if __name__ == "__main__":
    run()
