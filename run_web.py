#!/usr/bin/env python3
"""Launcher for the ExcelIntel Web Application & Browser Preview."""
from __future__ import annotations

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main():
    print("=" * 60)
    print("  ExcelIntel Advanced Data Analysis & Duplicate Detection Studio")
    print("=" * 60)

    # 1. Check/Start Python FastAPI Backend Server
    import urllib.request
    backend_running = False
    try:
        urllib.request.urlopen("http://127.0.0.1:8000/api/", timeout=1)
        backend_running = True
        print("\n[1/3] Python FastAPI Backend is already active on http://127.0.0.1:8000")
    except Exception:
        pass

    backend_proc = None
    if not backend_running:
        print("\n[1/3] Starting Python FastAPI Backend Engine on http://127.0.0.1:8000 ...")
        cmd_backend = [sys.executable, "-m", "uvicorn", "backend.server:app", "--host", "127.0.0.1", "--port", "8000"]
        backend_proc = subprocess.Popen(
            cmd_backend,
            cwd=ROOT,
            env=os.environ.copy(),
        )
        time.sleep(2)

    # 2. Check Frontend directory
    frontend_dir = ROOT / "frontend"
    if frontend_dir.exists():
        print("[2/3] Starting React Web Dashboard on http://localhost:3000 ...")
        cmd = ["npx.cmd", "react-scripts", "start"] if os.name == "nt" else ["npx", "react-scripts", "start"]
        frontend_proc = subprocess.Popen(
            cmd,
            cwd=frontend_dir,
            env={**os.environ, "REACT_APP_BACKEND_URL": "http://127.0.0.1:8000"},
        )
        time.sleep(4)

    # 3. Open Browser
    print("[3/3] Opening ExcelIntel Web Application in your browser...")
    webbrowser.open("http://localhost:3000")

    print("\n[OK] Web application is live!")
    print("   - Web App UI: http://localhost:3000")
    print("   - API Server: http://127.0.0.1:8000/api")
    print("\nPress Ctrl+C to stop servers.\n")

    try:
        if backend_proc:
            backend_proc.wait()
        elif 'frontend_proc' in locals() and frontend_proc:
            frontend_proc.wait()
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        if backend_proc:
            backend_proc.terminate()

if __name__ == "__main__":
    main()
