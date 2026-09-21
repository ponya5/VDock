"""Cross-platform system actions for shutdown, restart, sleep, lock, volume, brightness, and media control."""
import platform
import queue
import subprocess
import os
import sys
import threading
from typing import Dict, Any, Optional
from .base_action import BaseAction, ActionResult

# Platform detection
_SYSTEM = platform.system()

# Windows API imports for media keys
if _SYSTEM == 'Windows':
    try:
        import ctypes
        from ctypes import wintypes
        KEYEVENTF_EXTENDEDKEY = 0x0001
        KEYEVENTF_KEYUP = 0x0002
        VK_VOLUME_MUTE = 0xAD
        VK_VOLUME_DOWN = 0xAE  
        VK_VOLUME_UP = 0xAF
        VK_MEDIA_NEXT_TRACK = 0xB0
        VK_MEDIA_PREV_TRACK = 0xB1
        VK_MEDIA_STOP = 0xB2
        VK_MEDIA_PLAY_PAUSE = 0xB3
        WINDOWS_API_AVAILABLE = True
    except:
        WINDOWS_API_AVAILABLE = False
else:
    WINDOWS_API_AVAILABLE = False


# Dedicated COM apartment thread for Core Audio (pycaw). IAudioEndpointVolume
# pointers must be created AND released on the same initialized thread —
# creating them on Flask workers left __del__→Release() to GC on arbitrary
# threads, which raised access violations and could kill the process silently.
_audio_worker_lock = threading.Lock()
_audio_worker_thread = None
_audio_worker_queue = None


def _audio_worker_loop(work_q):
    """Single-tenant COM thread: CoInitialize once, own the endpoint forever."""
    import comtypes
    comtypes.CoInitialize()
    endpoint_box = {'endpoint': None, 'err': None}

    def get_endpoint():
        if endpoint_box['endpoint'] is None and endpoint_box['err'] is None:
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                endpoint_box['endpoint'] = cast(
                    interface, POINTER(IAudioEndpointVolume))
            except ImportError:
                endpoint_box['err'] = 'pycaw not installed (pip install pycaw)'
            except Exception as e:
                endpoint_box['err'] = f'Audio device unavailable: {e}'
        return endpoint_box['endpoint'], endpoint_box['err']

    def app_volume(process, set_value=None):
        """Per-app session volume. set_value 0.0-1.0 or None to read.

        Returns (percent | True, None) or (None, error)."""
        try:
            from pycaw.pycaw import AudioUtilities
        except ImportError:
            return None, 'pycaw not installed (pip install pycaw)'
        proc = (process or '').strip().lower()
        if not proc:
            return None, 'No process configured'
        if not proc.endswith('.exe'):
            proc += '.exe'
        try:
            matched = None
            for session in AudioUtilities.GetAllSessions():
                name = ''
                try:
                    if session.Process:
                        name = session.Process.name().lower()
                except Exception:
                    name = ''
                if name == proc:
                    matched = session
                    break
            if matched is None:
                return None, f'No audio session for {proc}'
            vol = matched.SimpleAudioVolume
            if set_value is None:
                return round(vol.GetMasterVolume() * 100), None
            vol.SetMasterVolume(set_value, None)
            return True, None
        except Exception as e:
            return None, str(e)

    while True:
        job = work_q.get()
        if job is None:
            break
        fn, done, box = job
        try:
            box['result'] = fn({'endpoint': get_endpoint, 'app_volume': app_volume})
        except Exception as e:
            box['error'] = e
        done.set()
    comtypes.CoUninitialize()


def _run_on_audio_thread(fn, timeout=5):
    """Run fn(ctx) on the COM worker; returns fn's result."""
    global _audio_worker_thread, _audio_worker_queue
    with _audio_worker_lock:
        if _audio_worker_thread is None or not _audio_worker_thread.is_alive():
            _audio_worker_queue = queue.Queue()
            _audio_worker_thread = threading.Thread(
                target=_audio_worker_loop, args=(_audio_worker_queue,),
                name='vdock-audio', daemon=True)
            _audio_worker_thread.start()
    done = threading.Event()
    box = {}
    _audio_worker_queue.put((fn, done, box))
    if not done.wait(timeout):
        raise TimeoutError('Audio worker did not respond')
    if 'error' in box:
        raise box['error']
    return box.get('result')


class CrossPlatformAction(BaseAction):
    """Cross-platform system actions with OS-specific implementations."""

    VALID_ACTIONS = [
        # System control
        'shutdown', 'restart', 'sleep', 'lock_screen',
        # Volume control
        'volume_up', 'volume_down', 'volume_mute', 'volume_unmute',
        'volume_set', 'volume_get', 'app_volume_set', 'app_volume_get',
        # Microphone control
        'microphone_mute', 'microphone_unmute',
        # Brightness control
        'brightness_up', 'brightness_down', 'brightness_set',
        # Media control
        'media_play_pause', 'media_next', 'media_previous', 'media_stop',
        # Web & Apps
        'open_url', 'open_app', 'open_folder', 'open_file', 'screenshot',
        'run_command', 'close_app', 'empty_recycle_bin',
    ]

    def __init__(self, config: Dict[str, Any]):
        """Initialize cross-platform action."""
        super().__init__(config)

    def validate(self) -> bool:
        """Validate that action type is provided and valid."""
        action = self.config.get('action')
        return action in self.VALID_ACTIONS

    def execute(self) -> ActionResult:
        """Execute the cross-platform action."""
        if not self.validate():
            return ActionResult(
                False,
                'Invalid configuration: Valid action required'
            )

        action = self.config['action']

        try:
            if action == 'shutdown':
                return self._shutdown()
            elif action == 'restart':
                return self._restart()
            elif action == 'sleep':
                return self._sleep()
            elif action == 'lock_screen':
                return self._lock_screen()
            elif action == 'volume_up':
                return self._volume_up()
            elif action == 'volume_down':
                return self._volume_down()
            elif action == 'volume_mute':
                return self._volume_mute()
            elif action == 'volume_unmute':
                return self._volume_unmute()
            elif action == 'volume_set':
                return self._volume_set()
            elif action == 'volume_get':
                return self._volume_get()
            elif action == 'app_volume_set':
                return self._app_volume_set()
            elif action == 'app_volume_get':
                return self._app_volume_get()
            elif action == 'brightness_up':
                return self._brightness_up()
            elif action == 'brightness_down':
                return self._brightness_down()
            elif action == 'brightness_set':
                return self._brightness_set()
            elif action == 'media_play_pause':
                return self._media_play_pause()
            elif action == 'media_next':
                return self._media_next()
            elif action == 'media_previous':
                return self._media_previous()
            elif action == 'media_stop':
                return self._media_stop()
            elif action == 'open_url':
                return self._open_url()
            elif action == 'open_app':
                return self._open_app()
            elif action == 'open_folder':
                return self._open_folder()
            elif action == 'open_file':
                return self._open_file()
            elif action == 'screenshot':
                return self._screenshot()
            elif action == 'microphone_mute':
                return self._microphone_mute()
            elif action == 'microphone_unmute':
                return self._microphone_unmute()
            elif action == 'run_command':
                return self._run_custom_command()
            elif action == 'close_app':
                return self._close_app()
            elif action == 'empty_recycle_bin':
                return self._empty_recycle_bin()
            else:
                return ActionResult(False, f'Unknown action: {action}')
        except Exception as e:
            return ActionResult(False, f'Error executing {action}: {str(e)}')

    def _run_command(self, command: str, shell: bool = True) -> ActionResult:
        """Run a system command safely."""
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return ActionResult(True, f'Command executed successfully')
            else:
                return ActionResult(
                    False,
                    f'Command failed: {result.stderr or result.stdout}'
                )
        except subprocess.TimeoutExpired:
            return ActionResult(False, 'Command timed out')
        except Exception as e:
            return ActionResult(False, f'Command error: {str(e)}')

    def _check_nircmd(self) -> bool:
        """Check if NirCmd is available on Windows."""
        if _SYSTEM != 'Windows':
            return False
        try:
            result = subprocess.run(
                'nircmd.exe',
                capture_output=True,
                timeout=5
            )
            return result.returncode != 9009  # Command not found error
        except:
            return False
    
    def _send_windows_key(self, vk_code: int) -> ActionResult:
        """Send a Windows virtual key code using ctypes."""
        if not WINDOWS_API_AVAILABLE:
            return ActionResult(False, 'Windows API not available')
        
        try:
            # Press key
            ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
            # Release key
            ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
            return ActionResult(True, 'Key sent successfully')
        except Exception as e:
            return ActionResult(False, f'Failed to send key: {str(e)}')

    # System Control Actions
    def _shutdown(self) -> ActionResult:
        """Shutdown the computer."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe exitwin poweroff')
            else:
                return self._run_command('shutdown /s /t 0')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command('sudo shutdown -h now')
        elif _SYSTEM == 'Linux':
            return self._run_command('sudo shutdown now')
        else:
            return ActionResult(False, f'Shutdown not supported on {_SYSTEM}')

    def _restart(self) -> ActionResult:
        """Restart the computer."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe exitwin reboot')
            else:
                return self._run_command('shutdown /r /t 0')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command('sudo shutdown -r now')
        elif _SYSTEM == 'Linux':
            return self._run_command('sudo shutdown -r now')
        else:
            return ActionResult(False, f'Restart not supported on {_SYSTEM}')

    def _sleep(self) -> ActionResult:
        """Put the computer to sleep."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe standby')
            else:
                return self._run_command('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command('pmset sleepnow')
        elif _SYSTEM == 'Linux':
            return self._run_command('sudo systemctl suspend')
        else:
            return ActionResult(False, f'Sleep not supported on {_SYSTEM}')

    def _lock_screen(self) -> ActionResult:
        """Lock the screen."""
        if _SYSTEM == 'Windows':
            return self._run_command('rundll32.exe user32.dll,LockWorkStation')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command('/System/Library/CoreServices/Menu\\ Extras/User.menu/Contents/Resources/CGSession -suspend')
        elif _SYSTEM == 'Linux':
            # Try xdg-screensaver first
            result = self._run_command('xdg-screensaver lock')
            if result.success:
                return result
            # Fallback to dbus
            return self._run_command('dbus-send --type=method_call --dest=org.gnome.ScreenSaver /org/gnome/ScreenSaver org.gnome.ScreenSaver.Lock')
        else:
            return ActionResult(False, f'Lock screen not supported on {_SYSTEM}')

    # Volume Control Actions
    def _volume_up(self) -> ActionResult:
        """Increase system volume."""
        step = self.config.get('step', 2000)  # Default step for NirCmd
        
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command(f'nircmd.exe changesysvolume {step}')
            else:
                # Use Windows API via ctypes
                return self._send_windows_key(VK_VOLUME_UP)
        elif _SYSTEM == 'Darwin':  # macOS
            volume_step = self.config.get('step', 10)
            script = f'set volume output volume (output volume of (get volume settings) + {volume_step})'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            volume_step = self.config.get('step', 10)
            return self._run_command(f'amixer set Master {volume_step}%+')
        else:
            return ActionResult(False, f'Volume control not supported on {_SYSTEM}')

    def _volume_down(self) -> ActionResult:
        """Decrease system volume."""
        step = self.config.get('step', 2000)  # Default step for NirCmd
        
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command(f'nircmd.exe changesysvolume -{step}')
            else:
                # Use Windows API via ctypes
                return self._send_windows_key(VK_VOLUME_DOWN)
        elif _SYSTEM == 'Darwin':  # macOS
            volume_step = self.config.get('step', 10)
            script = f'set volume output volume (output volume of (get volume settings) - {volume_step})'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            volume_step = self.config.get('step', 10)
            return self._run_command(f'amixer set Master {volume_step}%-')
        else:
            return ActionResult(False, f'Volume control not supported on {_SYSTEM}')

    def _volume_mute(self) -> ActionResult:
        """Toggle mute."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe mutesysvolume 2')
            else:
                # Use Windows API via ctypes
                return self._send_windows_key(VK_VOLUME_MUTE)
        elif _SYSTEM == 'Darwin':  # macOS
            script = 'set volume with output muted'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            return self._run_command('amixer set Master mute')
        else:
            return ActionResult(False, f'Volume control not supported on {_SYSTEM}')

    def _volume_unmute(self) -> ActionResult:
        """Unmute."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe mutesysvolume 0')
            else:
                # Use Windows API via ctypes (mute is toggle)
                return self._send_windows_key(VK_VOLUME_MUTE)
        elif _SYSTEM == 'Darwin':  # macOS
            script = 'set volume without output muted'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            return self._run_command('amixer set Master unmute')
        else:
            return ActionResult(False, f'Volume control not supported on {_SYSTEM}')

    def _volume_scalar(self, set_value=None):
        """Read (set_value=None) or write (0.0-1.0) the master volume scalar.

        Runs on the dedicated COM apartment thread via _run_on_audio_thread —
        Core Audio objects must never be created or released on Flask workers.
        Returns (level_percent | True, None) or (None, error).
        """
        def job(ctx):
            endpoint, err = ctx['endpoint']()
            if endpoint is None:
                return None, err
            try:
                if set_value is None:
                    return round(endpoint.GetMasterVolumeLevelScalar() * 100), None
                endpoint.SetMasterVolumeLevelScalar(set_value, None)
                return True, None
            except Exception as e:
                return None, str(e)

        try:
            return _run_on_audio_thread(job)
        except Exception as e:
            return None, str(e)

    def _volume_set(self) -> ActionResult:
        """Set absolute output volume 0-100 — the slider action."""
        try:
            value = max(0, min(100, int(float(self.config.get('value', 50)))))
        except (TypeError, ValueError):
            return ActionResult(False, 'Invalid volume value (0-100 expected)')

        if _SYSTEM == 'Windows':
            result, err = self._volume_scalar(value / 100.0)
            if result is not None:
                return ActionResult(
                    True, f'Volume set to {value}%',
                    {'value': value, 'badge': f'{value}%'}
                )
            if self._check_nircmd():
                # NirCmd takes 0-65535.
                result = self._run_command(
                    f'nircmd.exe setsysvolume {int(value / 100 * 65535)}'
                )
                if result.success:
                    result.data = {**(result.data or {}), 'value': value, 'badge': f'{value}%'}
                return result
            return ActionResult(False, err or 'Volume set unavailable on Windows')
        elif _SYSTEM == 'Darwin':
            result = self._run_command(f'osascript -e "set volume output volume {value}"')
            if result.success:
                result.data = {**(result.data or {}), 'value': value, 'badge': f'{value}%'}
            return result
        elif _SYSTEM == 'Linux':
            result = self._run_command(f'amixer set Master {value}%')
            if result.success:
                result.data = {**(result.data or {}), 'value': value, 'badge': f'{value}%'}
            return result
        return ActionResult(False, f'Volume control not supported on {_SYSTEM}')

    def _volume_get(self) -> ActionResult:
        """Current output volume 0-100 — sliders fetch this on mount."""
        if _SYSTEM == 'Windows':
            value, err = self._volume_scalar()
            if value is not None:
                return ActionResult(True, f'Volume {value}%', {'value': value})
            return ActionResult(False, err or 'Volume read unavailable on Windows')
        elif _SYSTEM == 'Darwin':
            result = subprocess.run(
                'osascript -e "output volume of (get volume settings)"',
                shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip().isdigit():
                return ActionResult(
                    True, f"Volume {result.stdout.strip()}%",
                    {'value': int(result.stdout.strip())}
                )
            return ActionResult(False, 'Could not read volume (osascript)')
        elif _SYSTEM == 'Linux':
            result = subprocess.run(
                "amixer get Master | grep -oP '\\d+%' | head -1 | tr -d '%'",
                shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip().isdigit():
                return ActionResult(
                    True, f"Volume {result.stdout.strip()}%",
                    {'value': int(result.stdout.strip())}
                )
            return ActionResult(False, 'Could not read volume (amixer)')
        return ActionResult(False, f'Volume control not supported on {_SYSTEM}')

    def _app_volume_process(self):
        return str(self.config.get('process') or self.config.get('app') or '').strip()

    def _app_volume_set(self) -> ActionResult:
        """Set one app's session volume 0-100 — the app_volume slider."""
        if _SYSTEM != 'Windows':
            return ActionResult(False, 'Per-app volume is Windows-only')
        process = self._app_volume_process()
        if not process:
            return ActionResult(False, 'No process configured')
        try:
            value = max(0, min(100, int(float(self.config.get('value', 50)))))
        except (TypeError, ValueError):
            return ActionResult(False, 'Invalid volume value (0-100 expected)')
        result, err = _run_on_audio_thread(
            lambda ctx: ctx['app_volume'](process, value / 100.0))
        if result is not None:
            return ActionResult(
                True, f'{process} volume set to {value}%',
                {'value': value, 'badge': f'{value}%'})
        return ActionResult(False, err or f'Could not set {process} volume')

    def _app_volume_get(self) -> ActionResult:
        """Current session volume 0-100 for the configured process."""
        if _SYSTEM != 'Windows':
            return ActionResult(False, 'Per-app volume is Windows-only')
        process = self._app_volume_process()
        if not process:
            return ActionResult(False, 'No process configured')
        value, err = _run_on_audio_thread(
            lambda ctx: ctx['app_volume'](process))
        if value is not None:
            return ActionResult(True, f'{process} volume {value}%', {'value': value})
        return ActionResult(False, err or f'Could not read {process} volume')

    # Brightness Control Actions
    def _brightness_up(self) -> ActionResult:
        """Increase screen brightness."""
        step = self.config.get('step', 10)
        
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                # Get current brightness and increase
                try:
                    result = subprocess.run(
                        'nircmd.exe getbrightness',
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        current = int(result.stdout.strip())
                        new_brightness = min(100, current + step)
                        return self._run_command(f'nircmd.exe setbrightness {new_brightness}')
                except:
                    pass
            
            # Try multiple Windows brightness control methods
            methods = [
                # Method 1: WMI with error handling
                f'powershell -Command "try {{ (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,100) }} catch {{ Write-Host \\"WMI not supported\\" }}"',
                # Method 2: Windows 10+ brightness control
                f'powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\\"{{F15}}\\")"',
                # Method 3: Fallback hotkey
                'powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\\"%{{F15}}\\")"'
            ]
            
            for method in methods:
                try:
                    result = self._run_command(method)
                    if result.success:
                        return ActionResult(True, 'Brightness increased')
                except:
                    continue
            
            return ActionResult(False, 'Brightness control not available on this system')
        elif _SYSTEM == 'Darwin':  # macOS
            # Check if brightness tool is available
            try:
                result = subprocess.run(
                    'brightness',
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 127:  # Command exists
                    return self._run_command('brightness 1')  # Set to max
            except:
                pass
            return ActionResult(False, 'Brightness control requires brightness tool on macOS. Install with: brew install brightness')
        elif _SYSTEM == 'Linux':
            # Try to get current brightness and increase
            try:
                result = subprocess.run(
                    'xrandr --verbose | grep -i brightness',
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Extract current brightness and increase
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'brightness:' in line.lower():
                            current = float(line.split(':')[1].strip())
                            new_brightness = min(1.0, current + 0.1)
                            # Get display name
                            display_result = subprocess.run(
                                'xrandr | grep " connected" | head -1 | cut -d" " -f1',
                                shell=True,
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if display_result.returncode == 0:
                                display = display_result.stdout.strip()
                                return self._run_command(f'xrandr --output {display} --brightness {new_brightness}')
            except:
                pass
            return ActionResult(False, 'Brightness control not available on Linux')
        else:
            return ActionResult(False, f'Brightness control not supported on {_SYSTEM}')

    def _brightness_down(self) -> ActionResult:
        """Decrease screen brightness."""
        step = self.config.get('step', 10)
        
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                # Get current brightness and decrease
                try:
                    result = subprocess.run(
                        'nircmd.exe getbrightness',
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        current = int(result.stdout.strip())
                        new_brightness = max(0, current - step)
                        return self._run_command(f'nircmd.exe setbrightness {new_brightness}')
                except:
                    pass
            
            # Try multiple Windows brightness control methods
            methods = [
                # Method 1: WMI with error handling
                f'powershell -Command "try {{ (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,50) }} catch {{ Write-Host \\"WMI not supported\\" }}"',
                # Method 2: Windows 10+ brightness control
                f'powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\\"{{F14}}\\")"',
                # Method 3: Fallback hotkey
                'powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\\"%{{F14}}\\")"'
            ]
            
            for method in methods:
                try:
                    result = self._run_command(method)
                    if result.success:
                        return ActionResult(True, 'Brightness decreased')
                except:
                    continue
            
            return ActionResult(False, 'Brightness control not available on this system')
        elif _SYSTEM == 'Darwin':  # macOS
            # Check if brightness tool is available
            try:
                result = subprocess.run(
                    'brightness',
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 127:  # Command exists
                    return self._run_command('brightness 0.5')  # Set to 50%
            except:
                pass
            return ActionResult(False, 'Brightness control requires brightness tool on macOS')
        elif _SYSTEM == 'Linux':
            # Try to get current brightness and decrease
            try:
                result = subprocess.run(
                    'xrandr --verbose | grep -i brightness',
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Extract current brightness and decrease
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'brightness:' in line.lower():
                            current = float(line.split(':')[1].strip())
                            new_brightness = max(0.1, current - 0.1)
                            # Get display name
                            display_result = subprocess.run(
                                'xrandr | grep " connected" | head -1 | cut -d" " -f1',
                                shell=True,
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if display_result.returncode == 0:
                                display = display_result.stdout.strip()
                                return self._run_command(f'xrandr --output {display} --brightness {new_brightness}')
            except:
                pass
            return ActionResult(False, 'Brightness control not available on Linux')
        else:
            return ActionResult(False, f'Brightness control not supported on {_SYSTEM}')

    def _brightness_set(self) -> ActionResult:
        """Set screen brightness to specific value."""
        brightness = self.config.get('brightness', 50)
        
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command(f'nircmd.exe setbrightness {brightness}')
            else:
                # Fallback to WMI using PowerShell
                ps_script = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{brightness})"
                return self._run_command(f'powershell -Command "{ps_script}"')
        elif _SYSTEM == 'Darwin':  # macOS
            try:
                result = subprocess.run(
                    'brightness',
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 127:  # Command exists
                    brightness_normalized = brightness / 100.0
                    return self._run_command(f'brightness {brightness_normalized}')
            except:
                pass
            return ActionResult(False, 'Brightness control requires brightness tool on macOS')
        elif _SYSTEM == 'Linux':
            try:
                # Get display name
                display_result = subprocess.run(
                    'xrandr | grep " connected" | head -1 | cut -d" " -f1',
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if display_result.returncode == 0:
                    display = display_result.stdout.strip()
                    brightness_normalized = brightness / 100.0
                    return self._run_command(f'xrandr --output {display} --brightness {brightness_normalized}')
            except:
                pass
            return ActionResult(False, 'Brightness control not available on Linux')
        else:
            return ActionResult(False, f'Brightness control not supported on {_SYSTEM}')

    # Media Control Actions
    def _media_play_pause(self) -> ActionResult:
        """Toggle play/pause."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe sendkeypress media_play_pause')
            else:
                # Use Windows API via ctypes
                return self._send_windows_key(VK_MEDIA_PLAY_PAUSE)
        elif _SYSTEM == 'Darwin':  # macOS
            script = 'tell application "Music" to playpause'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            # Check if playerctl is available
            try:
                result = subprocess.run(
                    'playerctl',
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 127:  # Command exists
                    return self._run_command('playerctl play-pause')
            except:
                pass
            # Fallback to PowerShell SendKeys
            ps_script = "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{MEDIA_PLAY_PAUSE}')"
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return ActionResult(True, 'Media play/pause toggled')
            return ActionResult(False, 'Media control not available')
        else:
            return ActionResult(False, f'Media control not supported on {_SYSTEM}')

    def _media_next(self) -> ActionResult:
        """Skip to next track."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe sendkeypress media_next_track')
            else:
                # Use Windows API via ctypes
                return self._send_windows_key(VK_MEDIA_NEXT_TRACK)
        elif _SYSTEM == 'Darwin':  # macOS
            script = 'tell application "Music" to next track'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            # Check if playerctl is available
            try:
                result = subprocess.run(
                    'playerctl',
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 127:  # Command exists
                    return self._run_command('playerctl next')
            except:
                pass
            # Fallback to PowerShell SendKeys
            ps_script = "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{MEDIA_NEXT_TRACK}')"
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return ActionResult(True, 'Media next track')
            return ActionResult(False, 'Media control not available')
        else:
            return ActionResult(False, f'Media control not supported on {_SYSTEM}')

    def _media_previous(self) -> ActionResult:
        """Skip to previous track."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe sendkeypress media_prev_track')
            else:
                # Use Windows API via ctypes
                return self._send_windows_key(VK_MEDIA_PREV_TRACK)
        elif _SYSTEM == 'Darwin':  # macOS
            script = 'tell application "Music" to previous track'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            # Check if playerctl is available
            try:
                result = subprocess.run(
                    'playerctl',
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 127:  # Command exists
                    return self._run_command('playerctl previous')
            except:
                pass
            # Fallback to PowerShell SendKeys
            ps_script = "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{MEDIA_PREV_TRACK}')"
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return ActionResult(True, 'Media previous track')
            return ActionResult(False, 'Media control not available')
        else:
            return ActionResult(False, f'Media control not supported on {_SYSTEM}')

    def _media_stop(self) -> ActionResult:
        """Stop playback."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe sendkeypress media_stop')
            else:
                # Use Windows API via ctypes
                return self._send_windows_key(VK_MEDIA_STOP)
        elif _SYSTEM == 'Darwin':  # macOS
            script = 'tell application "Music" to stop'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            # Check if playerctl is available
            try:
                result = subprocess.run(
                    'playerctl',
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 127:  # Command exists
                    return self._run_command('playerctl stop')
            except:
                pass
            # Fallback to PowerShell SendKeys
            ps_script = "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{MEDIA_STOP}')"
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return ActionResult(True, 'Media stopped')
            return ActionResult(False, 'Media control not available')
        else:
            return ActionResult(False, f'Media control not supported on {_SYSTEM}')

    # Web & Apps Actions
    def _open_url(self) -> ActionResult:
        """Open URL in default browser."""
        url = self.config.get('url')
        if not url:
            return ActionResult(False, 'URL not specified')
        
        # Validate URL
        if not url.startswith(('http://', 'https://', 'ftp://')):
            url = 'https://' + url
        
        if _SYSTEM == 'Windows':
            return self._run_command(f'start "" "{url}"')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command(f'open "{url}"')
        elif _SYSTEM == 'Linux':
            return self._run_command(f'xdg-open "{url}"')
        else:
            return ActionResult(False, f'URL opening not supported on {_SYSTEM}')

    def _open_app(self) -> ActionResult:
        """Open application."""
        app_path = self.config.get('path') or self.config.get('name')
        if not app_path:
            return ActionResult(False, 'Application path/name not specified')
        
        if _SYSTEM == 'Windows':
            return self._run_command(f'start "" "{app_path}"')
        elif _SYSTEM == 'Darwin':  # macOS
            app_name = os.path.basename(app_path)
            return self._run_command(f'open -a "{app_name}"')
        elif _SYSTEM == 'Linux':
            # Try xdg-open first
            result = self._run_command(f'xdg-open "{app_path}"')
            if result.success:
                return result
            # Fallback to direct execution
            return self._run_command(f'"{app_path}"')
        else:
            return ActionResult(False, f'Application opening not supported on {_SYSTEM}')

    def _open_folder(self) -> ActionResult:
        """Open folder in file manager."""
        folder_path = self.config.get('path')
        if not folder_path:
            return ActionResult(False, 'Folder path not specified')
        
        if not os.path.exists(folder_path):
            return ActionResult(False, f'Folder does not exist: {folder_path}')
        
        if _SYSTEM == 'Windows':
            return self._run_command(f'explorer.exe "{folder_path}"')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command(f'open "{folder_path}"')
        elif _SYSTEM == 'Linux':
            return self._run_command(f'xdg-open "{folder_path}"')
        else:
            return ActionResult(False, f'Folder opening not supported on {_SYSTEM}')

    def _open_file(self) -> ActionResult:
        """Open file with default application."""
        file_path = self.config.get('path')
        if not file_path:
            return ActionResult(False, 'File path not specified')
        
        if not os.path.exists(file_path):
            return ActionResult(False, f'File does not exist: {file_path}')
        
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command(f'nircmd.exe shexec open "{file_path}"')
            else:
                return self._run_command(f'start "" "{file_path}"')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command(f'open "{file_path}"')
        elif _SYSTEM == 'Linux':
            return self._run_command(f'xdg-open "{file_path}"')
        else:
            return ActionResult(False, f'File opening not supported on {_SYSTEM}')

    def _screenshot(self) -> ActionResult:
        """Take a screenshot."""
        output_path = self.config.get('path', 'screenshot.png')
        
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command(f'nircmd.exe savescreenshot "{output_path}"')
            else:
                # Fallback to PowerShell with proper string escaping
                ps_script = f"Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; $Screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; $bitmap = New-Object System.Drawing.Bitmap $Screen.Width, $Screen.Height; $graphics = [System.Drawing.Graphics]::FromImage($bitmap); $graphics.CopyFromScreen($Screen.Left, $Screen.Top, 0, 0, $Screen.Size); $bitmap.Save('{output_path}'); $graphics.Dispose(); $bitmap.Dispose()"
                return self._run_command(f'powershell -Command "{ps_script}"')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command(f'screencapture -x "{output_path}"')
        elif _SYSTEM == 'Linux':
            # Try gnome-screenshot first
            result = self._run_command(f'gnome-screenshot -f "{output_path}"')
            if result.success:
                return result
            # Fallback to ImageMagick
            result = self._run_command(f'import -window root "{output_path}"')
            if result.success:
                return result
            return ActionResult(False, 'Screenshot requires gnome-screenshot or ImageMagick on Linux')
        else:
            return ActionResult(False, f'Screenshot not supported on {_SYSTEM}')


    # Microphone Control Actions
    def _microphone_mute(self) -> ActionResult:
        """Mute microphone."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe mutesysvolume 1 microphone')
            else:
                # PowerShell method to mute microphone
                ps_script = "$devices = Get-WmiObject -Class Win32_SoundDevice; foreach ($device in $devices) { if ($device.Name -like '*Microphone*') { $device.Disable() } }"
                return self._run_command(f'powershell -Command "{ps_script}"')
        elif _SYSTEM == 'Darwin':  # macOS
            script = 'set volume input volume 0'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            return self._run_command('amixer set Capture nocap')
        else:
            return ActionResult(False, f'Microphone control not supported on {_SYSTEM}')

    def _microphone_unmute(self) -> ActionResult:
        """Unmute microphone."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe mutesysvolume 0 microphone')
            else:
                # PowerShell method to unmute microphone
                ps_script = "$devices = Get-WmiObject -Class Win32_SoundDevice; foreach ($device in $devices) { if ($device.Name -like '*Microphone*') { $device.Enable() } }"
                return self._run_command(f'powershell -Command "{ps_script}"')
        elif _SYSTEM == 'Darwin':  # macOS
            script = 'set volume input volume 50'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            return self._run_command('amixer set Capture cap')
        else:
            return ActionResult(False, f'Microphone control not supported on {_SYSTEM}')

    # Additional Actions
    def _run_custom_command(self) -> ActionResult:
        """Run a custom command."""
        command = self.config.get('command')
        if not command:
            return ActionResult(False, 'Command not specified')
        
        return self._run_command(command)

    def _close_app(self) -> ActionResult:
        """Close an application by name."""
        app_name = self.config.get('app_name')
        if not app_name:
            return ActionResult(False, 'Application name not specified')
        
        if _SYSTEM == 'Windows':
            # Remove .exe extension if present for taskkill
            if app_name.endswith('.exe'):
                app_name_clean = app_name
            else:
                app_name_clean = app_name + '.exe'
            return self._run_command(f'taskkill /F /IM "{app_name_clean}"')
        elif _SYSTEM == 'Darwin':  # macOS
            # Remove .app extension if present
            app_name_clean = app_name.replace('.app', '')
            return self._run_command(f'pkill -x "{app_name_clean}"')
        elif _SYSTEM == 'Linux':
            return self._run_command(f'pkill "{app_name}"')
        else:
            return ActionResult(False, f'Close app not supported on {_SYSTEM}')

    def _empty_recycle_bin(self) -> ActionResult:
        """Empty the recycle bin."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe emptybin')
            else:
                # PowerShell method
                ps_script = "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"
                return self._run_command(f'powershell -Command "{ps_script}"')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command('rm -rf ~/.Trash/*')
        elif _SYSTEM == 'Linux':
            # Try multiple trash locations
            commands = [
                'rm -rf ~/.local/share/Trash/*',
                'rm -rf ~/.Trash/*'
            ]
            for cmd in commands:
                result = self._run_command(cmd)
                if result.success:
                    return result
            return ActionResult(False, 'Could not empty trash')
        else:
            return ActionResult(False, f'Empty recycle bin not supported on {_SYSTEM}')

    def get_description(self) -> str:
        """Get action description."""
        action = self.config.get('action', 'unknown')
        return f"Cross-platform: {action.replace('_', ' ').title()}"
