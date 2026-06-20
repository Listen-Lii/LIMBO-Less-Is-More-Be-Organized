#!/usr/bin/env python3
"""
LIMBO Launcher
同时启动后端和浏览器前端，退出时同时关闭
"""
import subprocess
import time
import signal
import sys
import os
import urllib.request
import webbrowser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_PORT = 5001

backend_process = None

def signal_handler(sig, frame):
    print("\n[Launcher] Shutting down...")
    if backend_process:
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
    sys.exit(0)

def wait_for_backend(max_attempts=30):
    for i in range(max_attempts):
        try:
            urllib.request.urlopen(f'http://127.0.0.1:5002/', timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False

def main():
    global backend_process

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("[Launcher] Starting FastAPI + SocketIO backend...")
    backend_process = subprocess.Popen(
        ['python3', '-c', f'''
import sys
sys.path.insert(0, '{SCRIPT_DIR}')
import uvicorn
from backend import app
uvicorn.run(app, host='0.0.0.0', port=5002)
'''],
        cwd=SCRIPT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    print("[Launcher] Waiting for backend to be ready...")
    if not wait_for_backend():
        print("[Launcher] ERROR: Backend failed to start")
        backend_process.terminate()
        sys.exit(1)

    print(f"[Launcher] Backend ready (PID: {backend_process.pid})")

    url = f'http://127.0.0.1:5002/'
    print(f"[Launcher] Opening browser at {url}...")
    webbrowser.open(url)

    print("[Launcher] Browser opened. Press Ctrl+C to exit...")

    try:
        while True:
            if backend_process.poll() is not None:
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    print("[Launcher] Stopping backend...")
    if backend_process:
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()

    print("[Launcher] Done")
    return 0

if __name__ == '__main__':
    sys.exit(main())