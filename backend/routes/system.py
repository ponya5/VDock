"""System configuration routes."""
import os
import sys
import platform
from flask import Blueprint, request, jsonify
from pathlib import Path

system_bp = Blueprint('system', __name__)

AUTOSTART_REGISTRY_NAME = 'VDock'


@system_bp.route('/api/system/autostart', methods=['GET'])
def get_autostart_status():
    """Return whether VDock is configured to launch at OS login."""
    try:
        enabled = _is_autostart_enabled()
        return jsonify({'success': True, 'enabled': enabled})
    except Exception as error:
        return jsonify({
            'success': False,
            'enabled': False,
            'message': f'Failed to read auto-start status: {error}',
        }), 500


@system_bp.route('/api/system/autostart', methods=['POST'])
def toggle_autostart():
    """Enable or disable auto-start on system boot."""
    data = request.json
    enabled = data.get('enabled', False)

    try:
        if platform.system() == 'Windows':
            result = _windows_autostart(enabled)
        elif platform.system() == 'Darwin':  # macOS
            result = _macos_autostart(enabled)
        elif platform.system() == 'Linux':
            result = _linux_autostart(enabled)
        else:
            return jsonify({
                'success': False,
                'message': f'Auto-start not supported on {platform.system()}'
            }), 400

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to configure auto-start: {str(e)}'
        }), 500


def _project_root() -> Path:
    return Path(__file__).parent.parent.parent.absolute()


def _resolve_launch_command() -> str:
    """Build the OS launch command for VDock."""
    app_path = _project_root()

    if platform.system() == 'Windows':
        launch_bat = app_path / 'launch.bat'
        if launch_bat.exists():
            return f'"{launch_bat}"'
        launcher_script = app_path / 'scripts' / 'VDock-Launcher.py'
        if launcher_script.exists():
            return f'pythonw "{launcher_script}"'
    else:
        launch_sh = app_path / 'launch.sh'
        if launch_sh.exists():
            return f'"{launch_sh}"'

    raise FileNotFoundError('Could not find launch.bat or launch.sh for auto-start')


def _is_autostart_enabled() -> bool:
    if platform.system() == 'Windows':
        import winreg

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Run',
                0,
                winreg.KEY_QUERY_VALUE,
            )
            winreg.QueryValueEx(key, AUTOSTART_REGISTRY_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False

    if platform.system() == 'Darwin':
        plist_file = Path.home() / 'Library' / 'LaunchAgents' / 'com.vdock.launcher.plist'
        return plist_file.exists()

    if platform.system() == 'Linux':
        desktop_file = Path.home() / '.config' / 'autostart' / 'vdock.desktop'
        return desktop_file.exists()

    return False


def _windows_autostart(enabled: bool) -> dict:
    """Configure Windows auto-start using registry."""
    import winreg

    try:
        launch_command = _resolve_launch_command()
    except FileNotFoundError as error:
        return {
            'success': False,
            'message': str(error),
        }

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Run',
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
        )

        if enabled:
            winreg.SetValueEx(
                key,
                AUTOSTART_REGISTRY_NAME,
                0,
                winreg.REG_SZ,
                launch_command
            )
            message = 'VDock added to Windows startup'
        else:
            try:
                winreg.DeleteValue(key, AUTOSTART_REGISTRY_NAME)
                message = 'VDock removed from Windows startup'
            except FileNotFoundError:
                message = 'VDock was not in startup'

        winreg.CloseKey(key)

        return {
            'success': True,
            'message': message
        }

    except PermissionError:
        return {
            'success': False,
            'message': 'Permission denied. Please run VDock as administrator.'
        }
    except Exception as error:
        return {
            'success': False,
            'message': f'Failed to configure Windows autostart: {error}'
        }


def _macos_autostart(enabled: bool) -> dict:
    """Configure macOS auto-start using LaunchAgents."""
    home = Path.home()
    plist_dir = home / 'Library' / 'LaunchAgents'
    plist_file = plist_dir / 'com.vdock.launcher.plist'

    app_path = _project_root()
    launch_script = app_path / 'launch.sh'

    if enabled and not launch_script.exists():
        return {
            'success': False,
            'message': f'Launch script not found: {launch_script}',
        }

    try:
        plist_dir.mkdir(parents=True, exist_ok=True)

        if enabled:
            # Create plist file
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vdock.launcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>{launch_script}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{app_path}</string>
</dict>
</plist>"""

            with open(plist_file, 'w') as f:
                f.write(plist_content)

            # Load the launch agent
            os.system(f'launchctl load "{plist_file}"')

            message = 'VDock added to macOS startup (Login Items)'

        else:
            # Unload and remove plist file
            if plist_file.exists():
                os.system(f'launchctl unload "{plist_file}"')
                plist_file.unlink()
                message = 'VDock removed from macOS startup'
            else:
                message = 'VDock was not in startup'

        return {
            'success': True,
            'message': message
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to configure macOS autostart: {str(e)}'
        }


def _linux_autostart(enabled: bool) -> dict:
    """Configure Linux auto-start using .desktop file."""
    home = Path.home()
    autostart_dir = home / '.config' / 'autostart'
    desktop_file = autostart_dir / 'vdock.desktop'

    app_path = _project_root()
    launch_script = app_path / 'launch.sh'

    if enabled and not launch_script.exists():
        return {
            'success': False,
            'message': f'Launch script not found: {launch_script}',
        }

    try:
        autostart_dir.mkdir(parents=True, exist_ok=True)

        if enabled:
            # Create desktop file
            desktop_content = f"""[Desktop Entry]
Type=Application
Name=VDock
Comment=Virtual Stream Deck
Exec={launch_script}
Icon={app_path}/frontend/public/favicon.ico
Terminal=false
Categories=Utility;
StartupNotify=false
X-GNOME-Autostart-enabled=true
"""

            with open(desktop_file, 'w') as f:
                f.write(desktop_content)

            desktop_file.chmod(0o755)

            message = 'VDock added to Linux startup'

        else:
            # Remove desktop file
            if desktop_file.exists():
                desktop_file.unlink()
                message = 'VDock removed from Linux startup'
            else:
                message = 'VDock was not in startup'

        return {
            'success': True,
            'message': message
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to configure Linux autostart: {str(e)}'
        }
