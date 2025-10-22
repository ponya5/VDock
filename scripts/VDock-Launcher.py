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
    APPLICATION_PATH = Path(__file__).parent

BACKEND_PATH = APPLICATION_PATH / 'backend'
FRONTEND_PATH = APPLICATION_PATH / 'frontend'


def check_requirements():
    """Check if Python and Node.js are installed."""
    try:
        subprocess.run(['python', '--version'], capture_output=True, check=True, timeout=5)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: Python not found. Please install Python 3.8+")
        return False

    try:
        subprocess.run(['npm', '--version'], capture_output=True, check=True, timeout=5)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: Node.js not found. Please install Node.js")
        return False

    return True


def check_venv():
    """Check if virtual environment exists."""
    venv_path = BACKEND_PATH / 'venv' / 'Scripts' / 'activate.bat'
    return venv_path.exists()


def launch_backend():
    """Launch backend server."""
    try:
        cmd = f'cd /d "{BACKEND_PATH}" && call venv\\Scripts\\activate.bat && python app.py'
        subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("✓ Backend server started")
        return True
    except Exception as e:
        print(f"✗ Failed to start backend: {e}")
        return False


def launch_frontend():
    """Launch frontend development server."""
    try:
        cmd = f'cd /d "{FRONTEND_PATH}" && npm run dev'
        subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("✓ Frontend server started")
        return True
    except Exception as e:
        print(f"✗ Failed to start frontend: {e}")
        return False


def open_browser():
    """Open VDock in default browser."""
    time.sleep(3)  # Wait for servers to initialize
    try:
        webbrowser.open('http://localhost:3000')
        print("✓ Opening VDock in browser")
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
    if not check_venv():
        print("✗ Virtual environment not found")
        print("⚠ Please run install.bat first\n")
        input("Press Enter to exit...")
        return False

    print("✓ Virtual environment found\n")

    # Launch services
    print("Starting services...\n")

    if not launch_backend():
        return False

    time.sleep(2)

    if not launch_frontend():
        return False

    # Open browser
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Display startup information
    print("\n" + "="*50)
    print("  VDock Started Successfully!")
    print("="*50)
    print("\nBackend:  http://localhost:5000")
    print("Frontend: http://localhost:3000")
    print("\nDefault login:")
    print("  Username: admin")
    print("  Password: admin")
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
