#!/usr/bin/env python3
"""
VDock Launcher Application
Cross-platform launcher for the VDock Virtual Stream Deck
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path
import threading
import shutil

# Keep console output readable on Windows code pages (cp1252, etc.)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(errors="replace")
        sys.stderr.reconfigure(errors="replace")
    except Exception:
        pass

IS_WINDOWS = os.name == "nt"

# Check if running as frozen executable (compiled with PyInstaller)
if getattr(sys, "frozen", False):
    APPLICATION_PATH = Path(sys.executable).parent
else:
    # Script may be run from scripts/ subdirectory or from repo root
    _script_dir = Path(__file__).parent
    _root_candidate = _script_dir.parent
    if (_root_candidate / "backend").exists():
        APPLICATION_PATH = _root_candidate  # running from scripts/
    else:
        APPLICATION_PATH = _script_dir  # running from root (packaged)

BACKEND_PATH = APPLICATION_PATH / "backend"
FRONTEND_PATH = APPLICATION_PATH / "frontend"


def find_python():
    """Find a usable Python executable (prefer python3 on macOS/Linux)."""
    candidates = []
    if IS_WINDOWS:
        candidates.extend(["python", "python3", sys.executable])
    else:
        candidates.extend(["python3", "python", sys.executable])

    for candidate in candidates:
        if not candidate:
            continue
        resolved = shutil.which(candidate) if candidate != sys.executable else candidate
        if not resolved:
            continue
        try:
            subprocess.run(
                [resolved, "--version"],
                capture_output=True,
                check=True,
                timeout=5,
            )
            return resolved
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def find_npm():
    """Find npm executable, checking PATH and common install locations."""
    npm = shutil.which("npm")
    if npm:
        return npm

    common = [
        Path("/opt/homebrew/bin/npm"),
        Path("/usr/local/bin/npm"),
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "nodejs" / "npm.cmd",
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "nodejs" / "npm.cmd",
        Path(os.environ.get("APPDATA", "")) / "npm" / "npm.cmd",
        Path("C:/Program Files/nodejs/npm.cmd"),
    ]
    for candidate_path in common:
        if candidate_path.exists():
            return str(candidate_path)
    return None


def find_npx():
    """Resolve npx next to the discovered npm executable."""
    npm_path = find_npm()
    if not npm_path:
        return shutil.which("npx") or "npx"

    npm_name = Path(npm_path).name
    if npm_name.lower() == "npm.cmd":
        return str(Path(npm_path).with_name("npx.cmd"))
    if npm_name.lower() == "npm":
        sibling = Path(npm_path).with_name("npx")
        if sibling.exists():
            return str(sibling)
        return shutil.which("npx") or "npx"
    return shutil.which("npx") or "npx"


def check_requirements():
    """Check if Python and Node.js are installed."""
    python_bin = find_python()
    if not python_bin:
        print("ERROR: Python not found. Please install Python 3.9+")
        return False

    npm = find_npm()
    if not npm:
        print("ERROR: Node.js/npm not found. Please install Node.js from https://nodejs.org")
        return False

    print(f"  python found: {python_bin}")
    print(f"  npm found: {npm}")
    return True


def check_venv():
    """Check if virtual environment exists (Windows Scripts/ or Unix bin/)."""
    candidates = [
        BACKEND_PATH / "venv" / "Scripts" / "activate.bat",
        BACKEND_PATH / "venv" / "bin" / "activate",
        APPLICATION_PATH / ".venv" / "Scripts" / "activate.bat",
        APPLICATION_PATH / ".venv" / "bin" / "activate",
    ]
    for activate_script in candidates:
        if activate_script.exists():
            return activate_script.parent.parent  # return the venv root
    return None


def resolve_venv_python(venv_path: Path):
    """Return the interpreter inside the virtual environment."""
    if IS_WINDOWS:
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def launch_backend(venv_path: Path):
    """Launch backend server."""
    try:
        venv_python = resolve_venv_python(venv_path)
        if not venv_python.exists():
            raise FileNotFoundError(f"venv python not found: {venv_python}")

        subprocess.Popen(
            [str(venv_python), "app.py"],
            cwd=str(BACKEND_PATH),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("[OK] Backend server started")
        return True
    except Exception as error:
        print(f"[ERROR] Failed to start backend: {error}")
        return False


def launch_frontend():
    """Launch Vite dev server."""
    try:
        npm = find_npm()
        if not npm:
            raise FileNotFoundError("npm not found")

        if IS_WINDOWS:
            cmd = f'cd /d "{FRONTEND_PATH}" && "{npm}" run dev'
            subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.Popen(
                [npm, "run", "dev"],
                cwd=str(FRONTEND_PATH),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        print("[OK] Vite dev server started")
        return True
    except Exception as error:
        print(f"[ERROR] Failed to start frontend: {error}")
        return False


def launch_electron():
    """Launch Electron app if dependencies are present, otherwise fall back to browser."""
    electron_dir = FRONTEND_PATH / "electron"
    node_modules = electron_dir / "node_modules"

    # Install electron deps if missing
    if not node_modules.exists():
        print("  Installing Electron dependencies...")
        npm = find_npm()
        if npm:
            subprocess.run([npm, "install"], cwd=str(electron_dir), check=False)

    try:
        npx = find_npx()
        subprocess.Popen(
            [npx, "electron", "."],
            cwd=str(electron_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("[OK] Electron launched")
        return True
    except Exception as error:
        print(f"[WARN] Electron launch failed ({error}), falling back to browser")
        return False


def open_browser():
    """Open VDock in default browser (fallback when Electron is unavailable)."""
    time.sleep(4)
    try:
        webbrowser.open("http://localhost:3000")
        print("[OK] Opening VDock in browser at http://localhost:3000")
    except Exception as error:
        print(f"[WARN] Could not open browser: {error}")
        print("  Please open http://localhost:3000 manually")


def setup_hint():
    """Platform-appropriate setup command for error messages."""
    if IS_WINDOWS:
        return "setup.bat"
    return "./setup.sh"


def main():
    """Main launcher function."""
    print("\n" + "=" * 50)
    print("  VDock Virtual Stream Deck Launcher")
    print("=" * 50 + "\n")

    # Check requirements
    print("Checking system requirements...")
    if not check_requirements():
        print("\n[WARN] Please install missing dependencies and try again")
        input("Press Enter to exit...")
        return False

    print("[OK] Python found")
    print("[OK] Node.js found\n")

    # Check virtual environment
    print("Checking virtual environment...")
    venv = check_venv()
    if not venv:
        print("[ERROR] Virtual environment not found")
        print(f"[WARN] Please run {setup_hint()} first\n")
        input("Press Enter to exit...")
        return False

    print(f"[OK] Virtual environment found: {venv}\n")

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
    print("\n" + "=" * 50)
    print("  VDock Started Successfully!")
    print("=" * 50)
    print("\nBackend:  http://localhost:5000")
    print("Frontend: http://localhost:3000")
    if not electron_ok:
        print("\nOpening in browser (Electron not available)")
    print("\nBoth servers are running in the background.")
    print("Close this window to stop all services.\n")

    input("Press Enter to exit launcher...")
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nShutdown requested by user")
        sys.exit(0)
    except Exception as error:
        print(f"\nUnexpected error: {error}")
        input("Press Enter to exit...")
        sys.exit(1)
