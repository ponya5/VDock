"""System configuration routes."""
import re
import socket
from flask import Blueprint, request, jsonify
from pathlib import Path
from auth import require_auth
from config import project_root, env_file, write_env_keys, read_env_key

system_bp = Blueprint('system', __name__)

# Loopback origins that VDock manages in CORS_ORIGINS — refreshed on port
# changes while any other origins the user added are preserved.
_MANAGED_ORIGIN = re.compile(
    r'^https?://(localhost|127\.0\.0\.1)(:\d+)?$', re.IGNORECASE
)


# ── Port configuration ─────────────────────────────────────────────────
# Mirrors setup.bat's :configure_ports — ports live in the .env files and
# only take effect on restart, so this endpoint validates, probes for
# collisions, rewrites the env files line-preserving, and reports that a
# restart is required.

def _backend_env() -> Path:
    """The one backend .env (backend/.env from source, DATA_DIR/.env frozen)."""
    return env_file()


def _frontend_dir() -> Path:
    return project_root() / 'frontend'


def _read_env_key(env_file: Path, key: str) -> str:
    return read_env_key(env_file, key)


def _write_env_keys(env_file: Path, updates: dict) -> None:
    write_env_keys(env_file, updates)


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
    backend_env = _backend_env()
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



