"""Configuration routes."""
from flask import Blueprint, request, jsonify
from config import Config, DECK_HOST_RE, lan_ip
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
