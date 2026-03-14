"""
Background service to monitor running applications and detect active window.
Used for automatic scene switching based on active application.
"""

import logging
import platform
import threading
import time
from typing import Any, Callable, Dict, Optional

import psutil

logger = logging.getLogger('vdock')

# Platform-specific imports
if platform.system() == "Windows":
    try:
        import win32gui
        import win32process
        WINDOWS_AVAILABLE = True
    except ImportError:
        WINDOWS_AVAILABLE = False
        logger.warning(
            "pywin32 not installed. Install with: pip install pywin32"
        )
elif platform.system() == "Darwin":
    try:
        from AppKit import NSWorkspace
        MACOS_AVAILABLE = True
    except ImportError:
        MACOS_AVAILABLE = False
        logger.warning(
            "pyobjc not installed. Install with: pip install pyobjc"
        )
else:
    try:
        import subprocess
        LINUX_AVAILABLE = True
    except ImportError:
        LINUX_AVAILABLE = False


class AppMonitor:
    """Monitors active applications and triggers callbacks when apps change."""

    def __init__(self, poll_interval: float = 1.0):
        self.poll_interval = poll_interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.current_app: Optional[Dict[str, Any]] = None
        self.callbacks: list[Callable[[Dict[str, Any]], None]] = []

    def get_active_window_app_windows(self) -> Optional[Dict[str, Any]]:
        """Get active window app info on Windows."""
        if not WINDOWS_AVAILABLE:
            return None
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            window_title = win32gui.GetWindowText(hwnd)
            try:
                process = psutil.Process(pid)
                return {
                    "name": process.name(),
                    "exe": process.name(),
                    "path": process.exe(),
                    "pid": pid,
                    "window_title": window_title,
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None
        except Exception as e:
            logger.error("Error getting active window (Windows): %s", e)
            return None

    def get_active_window_app_macos(self) -> Optional[Dict[str, Any]]:
        """Get active window app info on macOS."""
        if not MACOS_AVAILABLE:
            return None
        try:
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.activeApplication()
            if not active_app:
                return None
            app_name = active_app.get('NSApplicationName', '')
            app_path = active_app.get('NSApplicationPath', '')
            pid = active_app.get('NSApplicationProcessIdentifier', 0)
            exe_name = app_path.split('/')[-1] if app_path else app_name
            return {
                "name": app_name,
                "exe": exe_name,
                "path": app_path,
                "pid": pid,
                "window_title": app_name,
            }
        except Exception as e:
            logger.error("Error getting active window (macOS): %s", e)
            return None

    def get_active_window_app_linux(self) -> Optional[Dict[str, Any]]:
        """Get active window app info on Linux."""
        if not LINUX_AVAILABLE:
            return None
        try:
            result = subprocess.run(
                ['xdotool', 'getactivewindow', 'getwindowpid'],
                capture_output=True, text=True, timeout=1, check=False,
            )
            if result.returncode != 0:
                return None
            pid = int(result.stdout.strip())
            try:
                process = psutil.Process(pid)
                title_result = subprocess.run(
                    ['xdotool', 'getactivewindow', 'getwindowname'],
                    capture_output=True, text=True, timeout=1, check=False,
                )
                window_title = (
                    title_result.stdout.strip()
                    if title_result.returncode == 0 else ""
                )
                return {
                    "name": process.name(),
                    "exe": process.name(),
                    "path": process.exe(),
                    "pid": pid,
                    "window_title": window_title,
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None
        except Exception as e:
            logger.error("Error getting active window (Linux): %s", e)
            return None

    def get_active_window_app(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently active window application."""
        system = platform.system()
        if system == "Windows":
            return self.get_active_window_app_windows()
        if system == "Darwin":
            return self.get_active_window_app_macos()
        if system == "Linux":
            return self.get_active_window_app_linux()
        logger.warning("Unsupported platform: %s", system)
        return None

    def register_callback(
        self, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        self.callbacks.append(callback)

    def unregister_callback(
        self, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def _notify_callbacks(self, active_app: Dict[str, Any]) -> None:
        for callback in self.callbacks:
            try:
                callback(active_app)
            except Exception as e:
                logger.error("Error in app monitor callback: %s", e)

    def _monitor_loop(self) -> None:
        """Main monitoring loop that runs in a separate thread."""
        logger.info("App monitor started")
        while self.running:
            try:
                active_app = self.get_active_window_app()
                if active_app:
                    current_exe = (
                        self.current_app.get("exe") if self.current_app
                        else None
                    )
                    new_exe = active_app.get("exe")
                    if current_exe != new_exe:
                        self.current_app = active_app
                        logger.info(
                            "Active app changed to: %s", active_app['exe']
                        )
                        self._notify_callbacks(active_app)
                time.sleep(self.poll_interval)
            except Exception as e:
                logger.error("Error in monitor loop: %s", e)
                time.sleep(self.poll_interval)
        logger.info("App monitor stopped")

    def start(self) -> None:
        """Start the monitoring service in a background thread."""
        if self.running:
            logger.warning("App monitor already running")
            return
        self.running = True
        self.thread = threading.Thread(
            target=self._monitor_loop, daemon=True
        )
        self.thread.start()
        logger.info("App monitor thread started")

    def stop(self) -> None:
        """Stop the monitoring service."""
        if not self.running:
            return
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("App monitor stopped")

    def get_current_app(self) -> Optional[Dict[str, Any]]:
        """Get the currently tracked active application."""
        return self.current_app


_monitor_instance: Optional[AppMonitor] = None


def get_app_monitor(poll_interval: float = 5.0) -> AppMonitor:
    """Get the global AppMonitor singleton instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = AppMonitor(poll_interval)
    return _monitor_instance


def start_monitoring(poll_interval: float = 5.0) -> None:
    """Start the global app monitoring service."""
    get_app_monitor(poll_interval).start()


def stop_monitoring() -> None:
    """Stop the global app monitoring service."""
    if _monitor_instance:
        _monitor_instance.stop()


def get_current_active_app() -> Optional[Dict[str, Any]]:
    """Get the currently active application (one-time check)."""
    return AppMonitor().get_active_window_app()
