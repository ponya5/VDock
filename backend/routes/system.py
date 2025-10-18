"""System configuration routes."""
import os
import sys
import platform
from flask import Blueprint, request, jsonify
from pathlib import Path

system_bp = Blueprint('system', __name__)


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


def _windows_autostart(enabled: bool) -> dict:
    """Configure Windows auto-start using registry."""
    import winreg

    app_path = Path(__file__).parent.parent.parent.absolute()
    launcher_path = app_path / "VDock-Launcher.vbs"

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Run',
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
        )

        if enabled:
            # Add to startup
            winreg.SetValueEx(
                key,
                'VDock',
                0,
                winreg.REG_SZ,
                str(launcher_path)
            )
            message = 'VDock added to Windows startup'
        else:
            # Remove from startup
            try:
                winreg.DeleteValue(key, 'VDock')
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
    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to configure Windows autostart: {str(e)}'
        }


def _macos_autostart(enabled: bool) -> dict:
    """Configure macOS auto-start using LaunchAgents."""
    home = Path.home()
    plist_dir = home / 'Library' / 'LaunchAgents'
    plist_file = plist_dir / 'com.vdock.launcher.plist'

    app_path = Path(__file__).parent.parent.parent.absolute()
    launch_script = app_path / 'launch.sh'

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

    app_path = Path(__file__).parent.parent.parent.absolute()
    launch_script = app_path / 'launch.sh'

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
