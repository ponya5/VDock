"""System configuration routes."""
import os
import re
import socket
import sys
import platform
from flask import Blueprint, request, jsonify
from pathlib import Path
from auth import require_auth

system_bp = Blueprint('system', __name__)

AUTOSTART_REGISTRY_NAME = 'VDock'

# Loopback origins that VDock manages in CORS_ORIGINS — refreshed on port
# changes while any other origins the user added are preserved.
_MANAGED_ORIGIN = re.compile(
    r'^https?://(localhost|127\.0\.0\.1)(:\d+)?$', re.IGNORECASE
)


@system_bp.route('/api/system/autostart', methods=['GET'])
@require_auth
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
@require_auth
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


# ── Port configuration ─────────────────────────────────────────────────
# Mirrors setup.bat's :configure_ports — ports live in the .env files and
# only take effect on restart, so this endpoint validates, probes for
# collisions, rewrites the env files line-preserving, and reports that a
# restart is required.

def _backend_dir() -> Path:
    return _project_root() / 'backend'


def _frontend_dir() -> Path:
    return _project_root() / 'frontend'


def _read_env_key(env_file: Path, key: str) -> str:
    if not env_file.exists():
        return ''
    try:
        for line in env_file.read_text().splitlines():
            stripped = line.strip()
            if stripped.upper().startswith(f'{key.upper()}='):
                return stripped.split('=', 1)[1].strip()
    except OSError:
        pass
    return ''


def _write_env_keys(env_file: Path, updates: dict) -> None:
    """Replace ``KEY=value`` lines in place; append keys that are missing.

    Unlike setup.bat's findstr strip, this preserves comments, blank lines
    and unrelated keys.
    """
    env_file.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    if env_file.exists():
        lines = env_file.read_text().splitlines()

    remaining = dict(updates)
    out = []
    for line in lines:
        replaced = False
        for key in list(remaining):
            if line.strip().upper().startswith(f'{key.upper()}='):
                out.append(f'{key}={remaining.pop(key)}')
                replaced = True
                break
        if not replaced:
            out.append(line)
    for key, value in remaining.items():
        out.append(f'{key}={value}')

    env_file.write_text('\n'.join(out) + '\n')


def _port_in_use(port: int) -> bool:
    """True if something answers on loopback — IPv4 or IPv6.

    Vite dev servers commonly bind only ::1, so an IPv4-only probe would
    report an occupied port as free and the collision check would miss it.
    """
    for family, addr in (
        (socket.AF_INET, ('127.0.0.1', port)),
        (socket.AF_INET6, ('::1', port)),
    ):
        try:
            with socket.socket(family, socket.SOCK_STREAM) as probe:
                probe.settimeout(0.5)
                if probe.connect_ex(addr) == 0:
                    return True
        except OSError:
            continue
    return False


def _configured_frontend_port() -> int:
    try:
        return int(_read_env_key(_frontend_dir() / '.env', 'VITE_PORT'))
    except ValueError:
        return 3000


def _valid_port(value) -> bool:
    try:
        port = int(value)
    except (TypeError, ValueError):
        return False
    return 1024 <= port <= 65535


@system_bp.route('/api/system/ports', methods=['GET'])
@require_auth
def get_ports():
    """Return configured ports and whether each is currently listening."""
    from config import Config

    backend_port = Config.PORT
    frontend_port = _configured_frontend_port()
    return jsonify({
        'success': True,
        'frontend_port': frontend_port,
        'backend_port': backend_port,
        'frontend_listening': _port_in_use(frontend_port),
        'backend_listening': _port_in_use(backend_port),
    })


@system_bp.route('/api/system/ports', methods=['PUT'])
@require_auth
def update_ports():
    """Validate and persist new frontend/backend ports in the .env files.

    Payload: ``{frontend_port, backend_port, check_only}``. ``check_only``
    runs the same validation and collision probes without writing — it backs
    the UI's "Check availability" button.
    """
    from config import Config

    data = request.json or {}
    current_backend = Config.PORT
    current_frontend = _configured_frontend_port()

    frontend_port = data.get('frontend_port', current_frontend)
    backend_port = data.get('backend_port', current_backend)

    errors = {}

    for field, value in (('frontend_port', frontend_port),
                         ('backend_port', backend_port)):
        if not _valid_port(value):
            errors[field] = 'Must be a port number between 1024 and 65535'

    if not errors and int(frontend_port) == int(backend_port):
        errors['frontend_port'] = 'Frontend and backend ports must differ'
        errors['backend_port'] = 'Frontend and backend ports must differ'

    if not errors:
        fp, bp = int(frontend_port), int(backend_port)
        if fp != current_frontend and _port_in_use(fp):
            errors['frontend_port'] = f'Port {fp} is already in use'
        if bp != current_backend and _port_in_use(bp):
            errors['backend_port'] = f'Port {bp} is already in use'

    if errors:
        return jsonify({'success': False, 'errors': errors}), 400

    frontend_port, backend_port = int(frontend_port), int(backend_port)

    if data.get('check_only'):
        return jsonify({
            'success': True,
            'message': 'Both ports are available.',
        })

    # backend/.env: PORT + refreshed loopback CORS origins (user-added
    # non-loopback origins survive untouched).
    backend_env = _backend_dir() / '.env'
    existing_origins = [
        o.strip() for o in
        _read_env_key(backend_env, 'CORS_ORIGINS').split(',')
        if o.strip() and not _MANAGED_ORIGIN.match(o.strip())
    ]
    origins = existing_origins + [
        f'http://localhost:{frontend_port}',
        f'http://127.0.0.1:{frontend_port}',
    ]
    _write_env_keys(backend_env, {
        'PORT': backend_port,
        'CORS_ORIGINS': ','.join(origins),
    })

    _write_env_keys(_frontend_dir() / '.env', {
        'VITE_PORT': frontend_port,
        'VITE_BACKEND_PORT': backend_port,
    })

    # Keep the persisted config mirror truthful for GET /api/config.
    config = Config.load_config()
    config['port'] = backend_port
    Config.save_config(config)

    return jsonify({
        'success': True,
        'saved': True,
        'restart_required': True,
        'url': f'http://localhost:{frontend_port}',
        'message': (
            f'Ports saved. Restart VDock (launch.bat) to apply — it will be '
            f'at http://localhost:{frontend_port}.'
        ),
    })


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
