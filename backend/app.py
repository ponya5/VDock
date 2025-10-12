"""Main Flask application for VDock backend."""
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from pathlib import Path
import uuid

from config import Config
from auth import AuthManager, require_auth
from models import Profile, Page, Theme, BUILTIN_THEMES, ProfileSettings
from actions import ActionExecutor
from plugins import PluginManager
from utils import FileManager, setup_logger

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
CORS(app, origins=Config.CORS_ORIGINS)
socketio = SocketIO(app, cors_allowed_origins=Config.CORS_ORIGINS, async_mode='threading')

# Initialize services
Config.init_app()
logger = setup_logger('vdock', log_file=Config.DATA_DIR / 'vdock.log')
action_executor = ActionExecutor()
plugin_manager = PluginManager()

# Load plugins on startup
plugin_manager.load_plugins()


# ============================================================================
# Authentication Routes
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate and get a token."""
    data = request.json
    password = data.get('password', '')
    
    token = AuthManager.authenticate(password)
    if token:
        return jsonify({'token': token, 'success': True})
    
    return jsonify({'error': 'Invalid password', 'success': False}), 401


@app.route('/api/auth/verify', methods=['GET'])
@require_auth
def verify_token():
    """Verify if the current token is valid."""
    return jsonify({'valid': True})


@app.route('/api/config', methods=['GET'])
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


@app.route('/api/config', methods=['PUT'])
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


# ============================================================================
# Profile Routes
# ============================================================================

@app.route('/api/profiles', methods=['GET'])
def get_profiles():
    """Get all profiles."""
    profile_files = FileManager.list_files(Config.PROFILES_DIR, '*.json')
    profiles = []
    
    for file_path in profile_files:
        profile_data = FileManager.load_json(file_path)
        if profile_data:
            try:
                profile = Profile.from_dict(profile_data)
                profiles.append({
                    'id': profile.id,
                    'name': profile.name,
                    'description': profile.description,
                    'icon': profile.icon,
                    'theme': profile.theme,
                    'page_count': len(profile.pages)
                })
            except Exception as e:
                logger.error(f"Error loading profile {file_path}: {e}")
    
    return jsonify({'profiles': profiles})


@app.route('/api/profiles/<profile_id>', methods=['GET'])
def get_profile(profile_id):
    """Get a specific profile."""
    file_path = Config.PROFILES_DIR / f"{profile_id}.json"
    profile_data = FileManager.load_json(file_path)
    
    if not profile_data:
        return jsonify({'error': 'Profile not found'}), 404
    
    try:
        profile = Profile.from_dict(profile_data)
        return jsonify({'profile': profile.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/profiles', methods=['POST'])
def create_profile():
    """Create a new profile."""
    data = request.json
    
    profile_id = str(uuid.uuid4())
    timestamp = FileManager.get_timestamp()
    
    # Create default page
    default_page = Page(
        id=str(uuid.uuid4()),
        name='Page 1',
        buttons=[],
        grid_config={'rows': 3, 'cols': 5}
    )
    
    profile = Profile(
        id=profile_id,
        name=data.get('name', 'New Profile'),
        description=data.get('description', ''),
        icon=data.get('icon'),
        avatar=data.get('avatar'),
        pages=[default_page],
        theme=data.get('theme', 'default'),
        settings=ProfileSettings(),
        created_at=timestamp,
        updated_at=timestamp
    )
    
    file_path = Config.PROFILES_DIR / f"{profile_id}.json"
    if FileManager.save_json(file_path, profile.to_dict()):
        return jsonify({'profile': profile.to_dict(), 'success': True}), 201
    
    return jsonify({'error': 'Failed to create profile', 'success': False}), 500


@app.route('/api/profiles/<profile_id>', methods=['PUT'])
def update_profile(profile_id):
    """Update an existing profile."""
    data = request.json
    file_path = Config.PROFILES_DIR / f"{profile_id}.json"
    
    # Load existing profile
    profile_data = FileManager.load_json(file_path)
    if not profile_data:
        return jsonify({'error': 'Profile not found'}), 404
    
    try:
        profile = Profile.from_dict(profile_data)
        
        # Update fields
        profile.name = data.get('name', profile.name)
        profile.description = data.get('description', profile.description)
        profile.icon = data.get('icon', profile.icon)
        profile.avatar = data.get('avatar', profile.avatar)
        profile.theme = data.get('theme', profile.theme)
        profile.updated_at = FileManager.get_timestamp()
        
        # Update pages if provided
        if 'pages' in data:
            profile.pages = [Page.from_dict(p) for p in data['pages']]
        
        # Save
        if FileManager.save_json(file_path, profile.to_dict()):
            return jsonify({'profile': profile.to_dict(), 'success': True})
        
        return jsonify({'error': 'Failed to save profile', 'success': False}), 500
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/profiles/<profile_id>/export', methods=['GET'])
@require_auth
def export_profile(profile_id):
    """Export a profile as JSON."""
    file_path = Config.PROFILES_DIR / f"{profile_id}.json"
    
    if not file_path.exists():
        return jsonify({'error': 'Profile not found'}), 404
    
    try:
        profile_data = FileManager.load_json(file_path)
        return jsonify({'profile': profile_data, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/profiles/import', methods=['POST'])
@require_auth
def import_profile():
    """Import a profile from JSON data."""
    data = request.json
    
    if not data or 'id' not in data:
        return jsonify({'error': 'Invalid profile data', 'success': False}), 400
    
    try:
        # Generate new ID to avoid conflicts
        new_id = str(uuid.uuid4())
        data['id'] = new_id
        data['created_at'] = FileManager.get_timestamp()
        data['updated_at'] = FileManager.get_timestamp()
        
        # Validate profile structure
        profile = Profile.from_dict(data)
        
        # Save imported profile
        file_path = Config.PROFILES_DIR / f"{new_id}.json"
        if FileManager.save_json(file_path, profile.to_dict()):
            return jsonify({'profile': profile.to_dict(), 'success': True}), 201
        
        return jsonify({'error': 'Failed to save imported profile', 'success': False}), 500
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/profiles/<profile_id>', methods=['DELETE'])
@require_auth
def delete_profile(profile_id):
    """Delete a profile."""
    file_path = Config.PROFILES_DIR / f"{profile_id}.json"
    
    if FileManager.delete_file(file_path):
        return jsonify({'success': True})
    
    return jsonify({'error': 'Failed to delete profile', 'success': False}), 500


@app.route('/api/profiles/<profile_id>/duplicate', methods=['POST'])
@require_auth
def duplicate_profile(profile_id):
    """Duplicate an existing profile."""
    src_file = Config.PROFILES_DIR / f"{profile_id}.json"
    profile_data = FileManager.load_json(src_file)
    
    if not profile_data:
        return jsonify({'error': 'Profile not found'}), 404
    
    try:
        profile = Profile.from_dict(profile_data)
        
        # Create new profile with new ID
        new_id = str(uuid.uuid4())
        profile.id = new_id
        profile.name = f"{profile.name} (Copy)"
        profile.created_at = FileManager.get_timestamp()
        profile.updated_at = profile.created_at
        
        # Generate new IDs for pages and buttons
        for page in profile.pages:
            page.id = str(uuid.uuid4())
            for button in page.buttons:
                button.id = str(uuid.uuid4())
        
        dst_file = Config.PROFILES_DIR / f"{new_id}.json"
        if FileManager.save_json(dst_file, profile.to_dict()):
            return jsonify({'profile': profile.to_dict(), 'success': True}), 201
        
        return jsonify({'error': 'Failed to duplicate profile', 'success': False}), 500
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ============================================================================
# Test Route
# ============================================================================

@app.route('/')
def root():
    """Root route."""
    return jsonify({'message': 'VDock API is running', 'success': True})

@app.route('/api/test')
def test_route():
    """Test route to verify Flask routing works."""
    return jsonify({'message': 'Test route works', 'success': True})

# ============================================================================
# Static File Serving
# ============================================================================

@app.route('/avatars/<filename>')
def serve_avatar(filename):
    """Serve avatar files from the Avatars directory."""
    try:
        avatars_dir = Path(__file__).parent / 'Avatars'
        avatar_path = avatars_dir / filename

        if not avatar_path.exists() or not avatar_path.is_file():
            return jsonify({'error': 'Avatar not found'}), 404

        return send_file(avatar_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Action Execution Routes
# ============================================================================

@app.route('/api/actions/execute', methods=['POST'])
@require_auth
def execute_action():
    """Execute an action."""
    data = request.json
    
    if 'action' not in data:
        return jsonify({'error': 'No action provided', 'success': False}), 400
    
    action_data = data['action']
    result = action_executor.execute_action(action_data)
    
    return jsonify(result.to_dict())


# ============================================================================
# WebSocket Events for Real-time Actions
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to VDock server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")


@socketio.on('execute_action')
def handle_execute_action(data):
    """Execute an action via WebSocket."""
    if 'action' not in data:
        emit('action_result', {'error': 'No action provided', 'success': False})
        return
    
    action_data = data['action']
    result = action_executor.execute_action(action_data)
    
    emit('action_result', result.to_dict())


# ============================================================================
# Theme Routes
# ============================================================================

@app.route('/api/themes', methods=['GET'])
@require_auth
def get_themes():
    """Get all available themes."""
    themes = [theme.to_dict() for theme in BUILTIN_THEMES.values()]
    
    # Load custom themes
    theme_files = FileManager.list_files(Config.DATA_DIR / 'themes', '*.json')
    for file_path in theme_files:
        theme_data = FileManager.load_json(file_path)
        if theme_data:
            try:
                theme = Theme.from_dict(theme_data)
                themes.append(theme.to_dict())
            except Exception as e:
                logger.error(f"Error loading theme {file_path}: {e}")
    
    return jsonify({'themes': themes})


# ============================================================================
# Plugin Routes
# ============================================================================

@app.route('/api/plugins', methods=['GET'])
@require_auth
def get_plugins():
    """Get all loaded plugins."""
    plugins = [info.to_dict() for info in plugin_manager.get_all_plugins()]
    return jsonify({'plugins': plugins})


@app.route('/api/plugins/<plugin_id>/actions', methods=['GET'])
@require_auth
def get_plugin_actions(plugin_id):
    """Get actions provided by a plugin."""
    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        return jsonify({'error': 'Plugin not found'}), 404
    
    info = plugin.get_info()
    actions = []
    
    for action_id in info.actions:
        schema = plugin_manager.get_action_schema(action_id)
        actions.append({
            'id': action_id,
            'schema': schema
        })
    
    return jsonify({'actions': actions})


# ============================================================================
# File Upload Routes
# ============================================================================

@app.route('/api/upload/icon', methods=['POST'])
@require_auth
def upload_icon():
    """Upload a custom icon."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided', 'success': False}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected', 'success': False}), 400
    
    # Validate file type
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.svg', '.gif'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        return jsonify({'error': 'Invalid file type', 'success': False}), 400
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}{file_ext}"
    filepath = Config.UPLOADS_DIR / filename
    
    try:
        file.save(filepath)
        return jsonify({
            'filename': filename,
            'url': f'/api/uploads/{filename}',
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/uploads/<filename>', methods=['GET'])
def serve_upload(filename):
    """Serve an uploaded file."""
    return send_from_directory(Config.UPLOADS_DIR, filename)


# ============================================================================
# Configuration Routes
# ============================================================================



# ============================================================================
# Health Check
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'plugins_loaded': len(plugin_manager.plugins)
    })


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    host = Config.HOST if Config.ALLOW_LAN else '127.0.0.1'
    port = Config.PORT
    
    logger.info(f"Starting VDock server on {host}:{port}")
    logger.info(f"Plugins loaded: {len(plugin_manager.plugins)}")
    
    socketio.run(
        app,
        host=host,
        port=port,
        debug=Config.DEBUG,
        allow_unsafe_werkzeug=True
    )

