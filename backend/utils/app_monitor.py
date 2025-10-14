"""
Background service to monitor running applications and detect active window.
Used for automatic scene switching based on active application.
"""

import psutil
import time
import threading
from typing import Optional, Callable, Dict, Any
import platform

# Platform-specific imports
if platform.system() == "Windows":
    try:
        import win32gui
        import win32process
        WINDOWS_AVAILABLE = True
    except ImportError:
        WINDOWS_AVAILABLE = False
        print("Warning: pywin32 not installed. Install with: pip install pywin32")
elif platform.system() == "Darwin":  # macOS
    try:
        from AppKit import NSWorkspace
        MACOS_AVAILABLE = True
    except ImportError:
        MACOS_AVAILABLE = False
        print("Warning: pyobjc not installed. Install with: pip install pyobjc")
else:  # Linux
    try:
        import subprocess
        LINUX_AVAILABLE = True
    except ImportError:
        LINUX_AVAILABLE = False


class AppMonitor:
    """Monitors active applications and triggers callbacks when apps change."""
    
    def __init__(self, poll_interval: float = 1.0):
        """
        Initialize the app monitor.
        
        Args:
            poll_interval: How often to check for active app changes (seconds)
        """
        self.poll_interval = poll_interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.current_app: Optional[Dict[str, Any]] = None
        self.callbacks: list[Callable[[Dict[str, Any]], None]] = []
        
    def get_active_window_app_windows(self) -> Optional[Dict[str, Any]]:
        """Get information about the active window application on Windows."""
        if not WINDOWS_AVAILABLE:
            return None
            
        try:
            # Get the foreground window handle
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
            
            # Get the process ID
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Get window title
            window_title = win32gui.GetWindowText(hwnd)
            
            # Get process information
            try:
                process = psutil.Process(pid)
                exe_name = process.name()
                exe_path = process.exe()
                
                return {
                    "name": process.name(),
                    "exe": exe_name,
                    "path": exe_path,
                    "pid": pid,
                    "window_title": window_title
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None
                
        except Exception as e:
            print(f"Error getting active window (Windows): {e}")
            return None
    
    def get_active_window_app_macos(self) -> Optional[Dict[str, Any]]:
        """Get information about the active window application on macOS."""
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
            
            # Extract exe name from path
            exe_name = app_path.split('/')[-1] if app_path else app_name
            
            return {
                "name": app_name,
                "exe": exe_name,
                "path": app_path,
                "pid": pid,
                "window_title": app_name
            }
            
        except Exception as e:
            print(f"Error getting active window (macOS): {e}")
            return None
    
    def get_active_window_app_linux(self) -> Optional[Dict[str, Any]]:
        """Get information about the active window application on Linux."""
        if not LINUX_AVAILABLE:
            return None
            
        try:
            # Try using xdotool
            result = subprocess.run(
                ['xdotool', 'getactivewindow', 'getwindowpid'],
                capture_output=True,
                text=True,
                timeout=1
            )
            
            if result.returncode != 0:
                return None
            
            pid = int(result.stdout.strip())
            
            # Get process information
            try:
                process = psutil.Process(pid)
                exe_name = process.name()
                exe_path = process.exe()
                
                # Try to get window title
                title_result = subprocess.run(
                    ['xdotool', 'getactivewindow', 'getwindowname'],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                window_title = title_result.stdout.strip() if title_result.returncode == 0 else ""
                
                return {
                    "name": process.name(),
                    "exe": exe_name,
                    "path": exe_path,
                    "pid": pid,
                    "window_title": window_title
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None
                
        except Exception as e:
            print(f"Error getting active window (Linux): {e}")
            return None
    
    def get_active_window_app(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently active window application."""
        system = platform.system()
        
        if system == "Windows":
            return self.get_active_window_app_windows()
        elif system == "Darwin":
            return self.get_active_window_app_macos()
        elif system == "Linux":
            return self.get_active_window_app_linux()
        else:
            print(f"Unsupported platform: {system}")
            return None
    
    def register_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Register a callback to be called when the active app changes.
        
        Args:
            callback: Function that takes app info dict as parameter
        """
        self.callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Unregister a callback.
        
        Args:
            callback: Function to remove from callbacks
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _monitor_loop(self):
        """Main monitoring loop that runs in a separate thread."""
        print("App monitor started")
        
        while self.running:
            try:
                # Get current active app
                active_app = self.get_active_window_app()
                
                # Check if app has changed
                if active_app:
                    # Compare by exe name to detect app changes
                    current_exe = self.current_app.get("exe") if self.current_app else None
                    new_exe = active_app.get("exe")
                    
                    if current_exe != new_exe:
                        # App changed, trigger callbacks
                        self.current_app = active_app
                        print(f"Active app changed to: {active_app['exe']}")
                        
                        for callback in self.callbacks:
                            try:
                                callback(active_app)
                            except Exception as e:
                                print(f"Error in callback: {e}")
                
                # Sleep until next poll
                time.sleep(self.poll_interval)
                
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(self.poll_interval)
        
        print("App monitor stopped")
    
    def start(self):
        """Start the monitoring service in a background thread."""
        if self.running:
            print("App monitor already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print("App monitor thread started")
    
    def stop(self):
        """Stop the monitoring service."""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        print("App monitor stopped")
    
    def get_current_app(self) -> Optional[Dict[str, Any]]:
        """Get the currently tracked active application."""
        return self.current_app


# Global singleton instance
_monitor_instance: Optional[AppMonitor] = None


def get_app_monitor(poll_interval: float = 1.0) -> AppMonitor:
    """Get the global AppMonitor singleton instance."""
    global _monitor_instance
    
    if _monitor_instance is None:
        _monitor_instance = AppMonitor(poll_interval)
    
    return _monitor_instance


def start_monitoring(poll_interval: float = 1.0):
    """Start the global app monitoring service."""
    monitor = get_app_monitor(poll_interval)
    monitor.start()


def stop_monitoring():
    """Stop the global app monitoring service."""
    global _monitor_instance
    
    if _monitor_instance:
        _monitor_instance.stop()


def get_current_active_app() -> Optional[Dict[str, Any]]:
    """Get the currently active application (one-time check, no monitoring)."""
    monitor = AppMonitor()
    return monitor.get_active_window_app()

