"""Configuration routes."""
from flask import Blueprint, request, jsonify
from config import Config
from auth import require_auth

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
            'enable_plugins': Config.ENABLE_PLUGINS
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

    # Load current config
    config = Config.load_config()

    # Update config with new values
    for key, value in data.items():
        if key in TOGGLE_KEYS:
            config[key] = value
    
    # Save updated config
    Config.save_config(config)
    
    # Update runtime config
    Config.REQUIRE_AUTH = config.get('require_auth', Config.REQUIRE_AUTH)
    Config.ALLOW_LAN = config.get('allow_lan', Config.ALLOW_LAN)
    Config.USE_SSL = config.get('use_ssl', Config.USE_SSL)
    Config.ENABLE_PLUGINS = config.get('enable_plugins', Config.ENABLE_PLUGINS)
    
    return jsonify({'success': True})
