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
import urllib.error
import urllib.request

# Keep console output readable on Windows code pages (cp1252, etc.)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(errors="replace")
        sys.stderr.reconfigure(errors="replace")
    except Exception:
        pass

IS_WINDOWS = os.name == "nt"
# DETACHED_PROCESS only stops the child inheriting our console — it does not stop
# cmd.exe (or a .cmd wrapper like npm/npx) from allocating its own new, visible
# console when it starts without one. CREATE_NO_WINDOW is the flag that actually
# suppresses a console window for the whole child process tree.
CREATE_NO_WINDOW = 0x08000000 if IS_WINDOWS else 0
CREATE_NEW_PROCESS_GROUP = 0x00000200 if IS_WINDOWS else 0

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
LOG_DIR = APPLICATION_PATH / "backend" / "data"
BACKEND_LOG = LOG_DIR / "vdock-backend-launcher.log"
FRONTEND_LOG = LOG_DIR / "vdock-frontend-launcher.log"
ELECTRON_LOG = LOG_DIR / "vdock-electron-launcher.log"
USER_SETTINGS_FILE = LOG_DIR / "user_settings.json"
DEFAULT_BACKEND_PORT = 5000


def load_user_settings_file() -> dict:
    """Load persisted UI settings written by the VDock backend."""
    if not USER_SETTINGS_FILE.exists():
        return {}

    try:
        import json

        with open(USER_SETTINGS_FILE, "r", encoding="utf-8") as settings_file:
            stored_settings = json.load(settings_file)
            if isinstance(stored_settings, dict):
                return stored_settings
    except (OSError, ValueError):
        pass

    return {}


def should_auto_close_launcher() -> bool:
    """Return True when the launcher window should close without waiting for Enter."""
    auto_close_value = os.environ.get("VDOCK_AUTO_CLOSE_LAUNCHER", "").strip().lower()
    if auto_close_value:
        return auto_close_value in ("1", "true", "yes", "on")

    user_settings = load_user_settings_file()
    return user_settings.get("autoCloseLauncher", True) is not False


def wait_for_launcher_close(prompt: str = "Press Enter to exit...") -> None:
    """Keep the launcher open for review unless auto-close is enabled."""
    if should_auto_close_launcher():
        return
    input(prompt)


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


def ensure_log_dir():
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def open_log_file(log_path: Path):
    ensure_log_dir()
    return open(log_path, "a", encoding="utf-8", errors="replace")


def detached_popen_args():
    if not IS_WINDOWS:
        return {}

    return {
        "creationflags": CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP,
        "close_fds": True,
    }


def wait_for_url(url: str, timeout_seconds: int = 45, interval_seconds: float = 1.0) -> bool:
    """Poll until an HTTP service responds or timeout is reached."""
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return True
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(interval_seconds)

    return False


def backend_supports_user_settings(port: int = DEFAULT_BACKEND_PORT) -> bool:
    """Return True when the running backend exposes the user-settings API."""
    user_settings_url = f"http://127.0.0.1:{port}/api/user-settings"
    try:
        with urllib.request.urlopen(user_settings_url, timeout=2) as response:
            return response.status == 200
    except urllib.error.HTTPError as http_error:
        return http_error.code == 200
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return False


def backend_is_running(port: int = DEFAULT_BACKEND_PORT) -> bool:
    """Return True when something is listening on the backend port."""
    config_url = f"http://127.0.0.1:{port}/api/config"
    return wait_for_url(config_url, timeout_seconds=2, interval_seconds=0.25)


def kill_process_on_port(port: int) -> bool:
    """Stop every process listening on the given TCP port."""
    process_ids: set[int] = set()

    if IS_WINDOWS:
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

        port_suffix = f":{port}"
        for line in result.stdout.splitlines():
            if "LISTENING" not in line:
                continue

            local_address = line.split()[1] if len(line.split()) > 1 else ""
            if not local_address.endswith(port_suffix):
                continue

            process_id = line.split()[-1]
            if process_id.isdigit():
                process_ids.add(int(process_id))
    else:
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

        for process_id in result.stdout.splitlines():
            if process_id.strip().isdigit():
                process_ids.add(int(process_id.strip()))

    if not process_ids:
        return False

    for process_id in process_ids:
        if IS_WINDOWS:
            subprocess.run(
                ["taskkill", "/F", "/PID", str(process_id)],
                capture_output=True,
                check=False,
            )
        else:
            subprocess.run(["kill", "-9", str(process_id)], capture_output=True, check=False)

    return True


def count_listeners_on_port(port: int) -> int:
    """Return how many processes are listening on a TCP port."""
    if not IS_WINDOWS:
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            return len([line for line in result.stdout.splitlines() if line.strip()])
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return 0

    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 0

    port_suffix = f":{port}"
    listener_count = 0
    for line in result.stdout.splitlines():
        if "LISTENING" not in line:
            continue
        local_address = line.split()[1] if len(line.split()) > 1 else ""
        if local_address.endswith(port_suffix):
            listener_count += 1

    return listener_count


def ensure_fresh_backend(venv_path: Path, port: int = DEFAULT_BACKEND_PORT) -> bool:
    """Start backend, restarting stale or duplicate instances when needed."""
    config_url = f"http://127.0.0.1:{port}/api/config"
    listener_count = count_listeners_on_port(port)
    needs_restart = listener_count == 0

    if listener_count > 0:
        if listener_count > 1:
            print(f"[WARN] Found {listener_count} backend processes on port {port}. Restarting...")
            needs_restart = True
        elif not backend_supports_user_settings(port):
            print("[WARN] Stale backend detected (missing user-settings API). Restarting...")
            needs_restart = True
        else:
            print("[OK] Backend already running with current API")
            return True

    if needs_restart and listener_count > 0:
        if kill_process_on_port(port):
            time.sleep(2)
        else:
            print("[WARN] Could not stop existing backend processes.")
            print("       Close VDock and end python.exe tasks in Task Manager, then relaunch.")

    if not launch_backend(venv_path):
        return False

    print(f"  Waiting for backend at http://localhost:{port} ...")
    if not wait_for_url(config_url, timeout_seconds=45):
        print("[WARN] Backend did not respond in time. Check log:")
        print(f"       {BACKEND_LOG}")
        return False

    if not backend_supports_user_settings(port):
        print("[WARN] Backend started but user-settings API is unavailable.")
        print("       Settings may not persist until the backend is updated and restarted.")

    return True


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

        backend_log = open_log_file(BACKEND_LOG)
        subprocess.Popen(
            [str(venv_python), "app.py"],
            cwd=str(BACKEND_PATH),
            stdout=backend_log,
            stderr=backend_log,
            **detached_popen_args(),
        )
        print("[OK] Backend server started")
        print(f"      Log: {BACKEND_LOG}")
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

        frontend_log = open_log_file(FRONTEND_LOG)

        if IS_WINDOWS:
            cmd = f'cd /d "{FRONTEND_PATH}" && "{npm}" run dev'
            subprocess.Popen(
                cmd,
                shell=True,
                stdout=frontend_log,
                stderr=frontend_log,
                **detached_popen_args(),
            )
        else:
            subprocess.Popen(
                [npm, "run", "dev"],
                cwd=str(FRONTEND_PATH),
                stdout=frontend_log,
                stderr=frontend_log,
                **detached_popen_args(),
            )
        print("[OK] Vite dev server started")
        print(f"      Log: {FRONTEND_LOG}")
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
        electron_log = open_log_file(ELECTRON_LOG)
        electron_env = os.environ.copy()
        electron_env["VDOCK_FULLSCREEN"] = "1"
        electron_env["VDOCK_USE_SMALLEST_DISPLAY"] = "1"
        # We already started (and waited for) the backend above — tell Electron's
        # main process not to spawn its own second copy, which would just fail to
        # bind the port and loop retrying forever in the background.
        electron_env["VDOCK_SKIP_BACKEND_SPAWN"] = "1"

        subprocess.Popen(
            [npx, "electron", "."],
            cwd=str(electron_dir),
            stdout=electron_log,
            stderr=electron_log,
            env=electron_env,
            **detached_popen_args(),
        )
        print("[OK] Electron launched in full-screen mode on smallest display")
        print(f"      Log: {ELECTRON_LOG}")
        return True
    except Exception as error:
        print(f"[WARN] Electron launch failed ({error}), falling back to browser")
        return False


def open_browser():
    """Open VDock in default browser (fallback when Electron is unavailable)."""
    time.sleep(2)
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
        wait_for_launcher_close("Press Enter to exit...")
        return False

    print("[OK] Python found")
    print("[OK] Node.js found\n")

    # Check virtual environment
    print("Checking virtual environment...")
    venv = check_venv()
    if not venv:
        print("[ERROR] Virtual environment not found")
        print(f"[WARN] Please run {setup_hint()} first\n")
        wait_for_launcher_close("Press Enter to exit...")
        return False

    print(f"[OK] Virtual environment found: {venv}\n")

    # Launch services
    print("Starting services...\n")

    if not ensure_fresh_backend(venv):
        return False

    if not launch_frontend():
        return False

    print("  Waiting for frontend at http://localhost:3000 ...")
    if not wait_for_url("http://localhost:3000", timeout_seconds=60):
        print("[WARN] Frontend did not respond in time. Check log:")
        print(f"       {FRONTEND_LOG}")

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
    if electron_ok:
        print("\nElectron is running full-screen on your smallest display.")
        print("Use the 'Full Screen' button in the header to toggle window chrome.")
    else:
        print("\nOpening in browser (Electron not available)")
    print("\nServices keep running after you close this launcher window.")
    print("Logs are saved under backend\\data\\")
    print("\nTo stop VDock, close the Electron window and end python/node tasks in Task Manager.")

    if should_auto_close_launcher():
        print("\nLauncher window will close automatically.")
        return True

    input("\nPress Enter to close this launcher window...")
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
        wait_for_launcher_close("Press Enter to exit...")
        sys.exit(1)
