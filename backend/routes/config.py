"""Configuration routes."""
import secrets

from flask import Blueprint, request, jsonify
from config import (
    Config, DECK_HOST_RE, lan_ip, env_file, is_weak_secret_key,
    write_env_keys, read_env_key,
)
from auth import require_auth
from services.app_paths import validate_path

config_bp = Blueprint('config', __name__)


@config_bp.route('/api/config', methods=['GET'])
@require_auth
def get_config():
    """Get current server configuration."""
    config = Config.load_config()
    return jsonify({
        'config': {
            'host': Config.HOST,
            'port': Config.PORT,
            'require_auth': Config.REQUIRE_AUTH,
            'allow_lan': Config.ALLOW_LAN,
            'use_ssl': Config.USE_SSL,
            'enable_plugins': Config.ENABLE_PLUGINS,
            'lan_ip': lan_ip(),
            # Optional 'Connect a device' address override — the QR card
            # shows this instead of lan_ip when set. None = auto-detect.
            'deck_host': Config.DECK_HOST or None,
            # Per-app executable overrides (DL-084) — { appKey: path }.
            'app_paths': dict(Config.APP_PATHS),
            # Effective bind is 0.0.0.0 whenever ALLOW_LAN is on (see app.py).
            'lan_reachable': bool(Config.ALLOW_LAN),
            # Whether a password exists — never the password itself. Lets the
            # UI offer "enable" vs "set a password first" (DL-126).
            'auth_password_set': bool(Config.AUTH_PASSWORD),
        }
    })


TOGGLE_KEYS = ('require_auth', 'allow_lan', 'use_ssl', 'enable_plugins')


@config_bp.route('/api/config', methods=['PUT'])
@require_auth
def update_config():
    """Update server configuration."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'No data provided', 'success': False}), 400

    # These keys are security switches — only literal booleans are valid.
    # A truthy string like "false" would silently invert intent on reload.
    for key, value in data.items():
        if key in TOGGLE_KEYS and not isinstance(value, bool):
            return jsonify(
                {'error': f'{key} must be a boolean', 'success': False}
            ), 400

    # deck_host — the 'Connect a device' address override. Must be a bare
    # hostname/IPv4: 'deck.local' or '192.168.1.50', never 'http://…:4444'
    # (the QR already prepends the scheme and appends the bind port).
    # Empty string or null clears it back to auto-detect.
    deck_host_set = None
    if 'deck_host' in data:
        host = data['deck_host']
        if host is None:
            host = ''
        if not isinstance(host, str):
            return jsonify(
                {'error': 'deck_host must be a string', 'success': False}
            ), 400
        host = host.strip()
        if host and not DECK_HOST_RE.fullmatch(host):
            return jsonify(
                {
                    'error': 'deck_host must be a bare hostname or IPv4 '
                             'address — no http://, port, or path',
                    'success': False,
                }
            ), 400
        deck_host_set = host

    # app_paths — { appKey: path } executable overrides (DL-084). Each path
    # must exist on the deck host (it IS the machine being launched on);
    # a '.app' bundle is a directory, so existence — not file-ness — is the
    # check. Empty string clears a key; the whole map may be omitted.
    app_paths_set = None
    if 'app_paths' in data:
        paths = data['app_paths']
        if not isinstance(paths, dict):
            return jsonify(
                {'error': 'app_paths must be an object', 'success': False}
            ), 400
        cleaned = {}
        for key, value in paths.items():
            key = str(key).strip().lower()
            if not key or len(key) > 64:
                return jsonify(
                    {'error': 'app_paths keys must be 1–64 chars', 'success': False}
                ), 400
            if value is None or (isinstance(value, str) and not value.strip()):
                continue  # empty value clears the key
            if not isinstance(value, str) or len(value) > 1024 or '\n' in value:
                return jsonify(
                    {'error': f'app_paths[{key}] must be a path string', 'success': False}
                ), 400
            ok, result = validate_path(value)
            if not ok:
                return jsonify({'error': result, 'success': False}), 400
            cleaned[key] = result
        app_paths_set = cleaned

    # auth_password — the shared deck password (DL-126). Written to
    # backend/.env (the documented secret home — load_dotenv picks it up
    # next launch) AND applied to Config live. Never persisted to
    # config.json, never returned by GET. Setting the password also
    # persists SECRET_KEY once, so issued tokens survive restarts —
    # otherwise every boot signs with a fresh random key and every device
    # has to re-unlock.
    auth_password_set = None
    if 'auth_password' in data:
        pw = data['auth_password']
        if not isinstance(pw, str):
            return jsonify(
                {'error': 'auth_password must be a string', 'success': False}
            ), 400
        pw = pw.strip()
        if not (4 <= len(pw) <= 128):
            return jsonify(
                {'error': 'Password must be 4–128 characters', 'success': False}
            ), 400
        if any(c in pw for c in '\r\n'):
            return jsonify(
                {'error': 'Password cannot contain newlines', 'success': False}
            ), 400
        auth_password_set = pw

    # Enabling auth with no password on file is a lockout — the same rule
    # Config.validate() enforces at boot, checked here at write time.
    wants_auth = data.get('require_auth')
    if wants_auth is True and not (auth_password_set or Config.AUTH_PASSWORD):
        return jsonify(
            {'error': 'Set a password before enabling authentication',
             'success': False}
        ), 400

    # Write the password to .env BEFORE touching config.json — a failed
    # write must never leave require_auth persisted with no password on
    # disk (that state refuses to boot). Also persist SECRET_KEY once so
    # issued tokens outlive a restart; without it every boot mints a fresh
    # key and every device has to re-unlock.
    if auth_password_set is not None:
        env_updates = {'AUTH_PASSWORD': auth_password_set}
        if is_weak_secret_key(read_env_key(env_file(), 'SECRET_KEY')):
            if is_weak_secret_key(Config.SECRET_KEY):
                Config.SECRET_KEY = secrets.token_hex(32)
            env_updates['SECRET_KEY'] = Config.SECRET_KEY
        try:
            write_env_keys(env_file(), env_updates)
        except OSError as e:
            return jsonify(
                {'error': f'Could not write backend/.env: {e}', 'success': False}
            ), 500

    # Load current config
    config = Config.load_config()

    # Update config with new values
    for key, value in data.items():
        if key in TOGGLE_KEYS:
            config[key] = value
    if deck_host_set is not None:
        config['deck_host'] = deck_host_set
    if app_paths_set is not None:
        config['app_paths'] = app_paths_set

    # Save updated config
    Config.save_config(config)
    
    # Update runtime config
    Config.REQUIRE_AUTH = config.get('require_auth', Config.REQUIRE_AUTH)
    Config.ALLOW_LAN = config.get('allow_lan', Config.ALLOW_LAN)
    Config.USE_SSL = config.get('use_ssl', Config.USE_SSL)
    Config.ENABLE_PLUGINS = config.get('enable_plugins', Config.ENABLE_PLUGINS)
    if deck_host_set is not None:
        Config.DECK_HOST = deck_host_set
    if app_paths_set is not None:
        Config.APP_PATHS = app_paths_set
    if auth_password_set is not None:
        Config.AUTH_PASSWORD = auth_password_set

    return jsonify({'success': True})


@config_bp.route('/api/app-paths/probe', methods=['GET'])
@require_auth
def probe_app_path():
    """Locate an app's executable/bundle — PATH first, then known install
    dirs (DL-084). Powers the path editor's Detect button."""
    from services import app_paths
    app = (request.args.get('app') or '').strip()
    if not app:
        return jsonify({'error': 'app is required', 'success': False}), 400
    found = app_paths.probe(app)
    return jsonify({'success': True, 'path': found})
