#!/usr/bin/env python3
"""
VDock Launcher Application
Graphical launcher for the VDock Virtual Stream Deck
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path
import threading

# Check if running as frozen executable (compiled with PyInstaller)
if getattr(sys, 'frozen', False):
    APPLICATION_PATH = Path(sys.executable).parent
else:
    # Script may be run from scripts/ subdirectory or from repo root
    _script_dir = Path(__file__).parent
    _root_candidate = _script_dir.parent
    if (_root_candidate / 'backend').exists():
        APPLICATION_PATH = _root_candidate  # running from scripts/
    else:
        APPLICATION_PATH = _script_dir  # running from root (packaged)

BACKEND_PATH = APPLICATION_PATH / 'backend'
FRONTEND_PATH = APPLICATION_PATH / 'frontend'


def find_npm():
    """Find npm executable, checking PATH and common Windows install locations."""
    import shutil
    npm = shutil.which('npm')
    if npm:
        return npm
    common = [
        Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'nodejs' / 'npm.cmd',
        Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / 'nodejs' / 'npm.cmd',
        Path(os.environ.get('APPDATA', '')) / 'npm' / 'npm.cmd',
        Path('C:/Program Files/nodejs/npm.cmd'),
    ]
    for p in common:
        if p.exists():
            return str(p)
    return None


def check_requirements():
    """Check if Python and Node.js are installed."""
    try:
        subprocess.run(['python', '--version'], capture_output=True, check=True, timeout=5)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: Python not found. Please install Python 3.8+")
        return False

    npm = find_npm()
    if not npm:
        print("ERROR: Node.js/npm not found. Please install Node.js from https://nodejs.org")
        return False

    print(f"  npm found: {npm}")
    return True


def check_venv():
    """Check if virtual environment exists (backend/venv or root .venv)."""
    candidates = [
        BACKEND_PATH / 'venv' / 'Scripts' / 'activate.bat',
        APPLICATION_PATH / '.venv' / 'Scripts' / 'activate.bat',
    ]
    for c in candidates:
        if c.exists():
            return c.parent.parent  # return the venv root
    return None


def launch_backend(venv_path: Path):
    """Launch backend server."""
    try:
        activate = venv_path / 'Scripts' / 'activate.bat'
        cmd = f'cd /d "{BACKEND_PATH}" && call "{activate}" && python app.py'
        subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("\u2713 Backend server started")
        return True
    except Exception as e:
        print(f"\u2717 Failed to start backend: {e}")
        return False


def launch_frontend():
    """Launch Vite dev server."""
    try:
        npm = find_npm()
        if not npm:
            raise FileNotFoundError('npm not found')
        cmd = f'cd /d "{FRONTEND_PATH}" && "{npm}" run dev'
        subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("\u2713 Vite dev server started")
        return True
    except Exception as e:
        print(f"\u2717 Failed to start frontend: {e}")
        return False


def launch_electron():
    """Launch Electron app if dependencies are present, otherwise fall back to browser."""
    electron_dir = FRONTEND_PATH / 'electron'
    node_modules = electron_dir / 'node_modules'

    # Install electron deps if missing
    if not node_modules.exists():
        print("  Installing Electron dependencies...")
        npm = find_npm()
        if npm:
            subprocess.run([npm, 'install'], cwd=str(electron_dir), check=False)

    try:
        npx = find_npm().replace('npm.cmd', 'npx.cmd') if find_npm() else 'npx'
        subprocess.Popen(
            [npx, 'electron', '.'],
            cwd=str(electron_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("\u2713 Electron launched")
        return True
    except Exception as e:
        print(f"\u26a0 Electron launch failed ({e}), falling back to browser")
        return False


def open_browser():
    """Open VDock in default browser (fallback when Electron is unavailable)."""
    time.sleep(4)
    try:
        webbrowser.open('http://localhost:3000')
        print("✓ Opening VDock in browser at http://localhost:3000")
    except Exception as e:
        print(f"⚠ Could not open browser: {e}")
        print("  Please open http://localhost:3000 manually")


def main():
    """Main launcher function."""
    print("\n" + "="*50)
    print("  VDock Virtual Stream Deck Launcher")
    print("="*50 + "\n")

    # Check requirements
    print("Checking system requirements...")
    if not check_requirements():
        print("\n⚠ Please install missing dependencies and try again")
        input("Press Enter to exit...")
        return False

    print("✓ Python found")
    print("✓ Node.js found\n")

    # Check virtual environment
    print("Checking virtual environment...")
    venv = check_venv()
    if not venv:
        print("\u2717 Virtual environment not found")
        print("\u26a0 Please run setup.bat first\n")
        input("Press Enter to exit...")
        return False

    print(f"\u2713 Virtual environment found: {venv}\n")

    # Launch services
    print("Starting services...\n")

    if not launch_backend(venv):
        return False

    time.sleep(2)

    if not launch_frontend():
        return False

    # Try Electron first, fall back to browser
    time.sleep(3)
    electron_ok = launch_electron()
    if not electron_ok:
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()

    # Display startup information
    print("\n" + "="*50)
    print("  VDock Started Successfully!")
    print("="*50)
    print("\nBackend:  http://localhost:5000")
    print("Frontend: http://localhost:3000")
    if not electron_ok:
        print("\nOpening in browser (Electron not available)")
    print("\nBoth servers are running in the background.")
    print("Close this window to stop all services.\n")

    input("Press Enter to exit launcher...")
    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)
