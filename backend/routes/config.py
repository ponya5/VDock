"""Configuration routes."""
from flask import Blueprint, request, jsonify
from config import Config

config_bp = Blueprint('config', __name__)


@config_bp.route('/api/config', methods=['GET'])
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


@config_bp.route('/api/config', methods=['PUT'])
def update_config():
    """Update server configuration."""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided', 'success': False}), 400
    
    # Load current config
    config = Config.load_config()
    
    # Update config with new values
    for key, value in data.items():
        if key in ['require_auth', 'allow_lan', 'use_ssl', 'enable_plugins']:
            config[key] = value
    
    # Save updated config
    Config.save_config(config)
    
    # Update runtime config
    Config.REQUIRE_AUTH = config.get('require_auth', Config.REQUIRE_AUTH)
    Config.ALLOW_LAN = config.get('allow_lan', Config.ALLOW_LAN)
    Config.USE_SSL = config.get('use_ssl', Config.USE_SSL)
    Config.ENABLE_PLUGINS = config.get('enable_plugins', Config.ENABLE_PLUGINS)
    
    return jsonify({'success': True})
