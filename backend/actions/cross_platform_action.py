"""Cross-platform system actions for shutdown, restart, sleep, lock, volume, brightness, and media control."""
import platform
import subprocess
import os
import sys
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


class CrossPlatformAction(BaseAction):
    """Cross-platform system actions with OS-specific implementations."""

    VALID_ACTIONS = [
        # System control
        'shutdown', 'restart', 'sleep', 'lock_screen',
        # Volume control
        'volume_up', 'volume_down', 'volume_mute', 'volume_unmute',
        # Brightness control
        'brightness_up', 'brightness_down', 'brightness_set',
        # Media control
        'media_play_pause', 'media_next', 'media_previous', 'media_stop',
        # Web & Apps
        'open_url', 'open_app', 'open_folder', 'open_file', 'screenshot',
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
            # Fallback to WMI using PowerShell
            ps_script = "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,100)"
            return self._run_command(f'powershell -Command "{ps_script}"')
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
            # Fallback to WMI using PowerShell
            ps_script = "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,50)"
            return self._run_command(f'powershell -Command "{ps_script}"')
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


    def get_description(self) -> str:
        """Get action description."""
        action = self.config.get('action', 'unknown')
        return f"Cross-platform: {action.replace('_', ' ').title()}"
