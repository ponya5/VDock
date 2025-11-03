"""Main Flask application for VDock backend."""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pathlib import Path
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from config import Config
from auth import require_auth
from models import BUILTIN_THEMES, Theme
from actions import ActionExecutor
from plugins import PluginManager
from utils import FileManager, setup_logger

# Import route blueprints
from routes.auth import auth_bp
from routes.profiles import profiles_bp
from routes.actions import actions_bp
from routes.config import config_bp
from routes.upload import upload_bp
from routes.assets import assets_bp
from routes.system_metrics import system_metrics_bp
from routes.app_monitor import app_monitor_bp
from routes.system import system_bp
from routes.templates import templates_bp
from routes.weather import weather_bp

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Add security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' ws: wss:;"
    if Config.USE_SSL:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Initialize extensions
CORS(app, origins=Config.CORS_ORIGINS)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[Config.RATELIMIT_DEFAULT] if Config.RATELIMIT_ENABLED else [],
    storage_uri=Config.RATELIMIT_STORAGE_URL,
    enabled=Config.RATELIMIT_ENABLED
)

socketio = SocketIO(
    app,
    cors_allowed_origins=Config.CORS_ORIGINS,
    async_mode='threading'
)

# Initialize services
Config.init_app()
logger = setup_logger('vdock', log_file=Config.DATA_DIR / 'vdock.log')
action_executor = ActionExecutor()
plugin_manager = PluginManager()

# Load plugins on startup
plugin_manager.load_plugins()

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(profiles_bp)
app.register_blueprint(actions_bp)
app.register_blueprint(config_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(assets_bp)
app.register_blueprint(system_metrics_bp)
app.register_blueprint(app_monitor_bp)
app.register_blueprint(system_bp)
app.register_blueprint(templates_bp, url_prefix='/api/templates')
app.register_blueprint(weather_bp, url_prefix='/api')

# Exempt critical endpoints from rate limiting
limiter.exempt(profiles_bp)  # Profile saves are critical
limiter.exempt(actions_bp)  # Action execution (frequent button clicks)


# ============================================================================
# Root Route - Serve Frontend for Electron App
# ============================================================================

@app.route('/')
def root():
    """Serve the frontend index.html for the Electron app."""
    # Use absolute path resolution
    backend_dir = Path(__file__).resolve().parent
    project_root = backend_dir.parent
    frontend_index = project_root / 'frontend' / 'dist' / 'index.html'

    if frontend_index.exists():
        return send_file(str(frontend_index))

    logger.warning(f"Frontend index.html not found at {frontend_index}")
    return jsonify({'message': 'VDock API is running', 'success': True})


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
# WebSocket Events for Real-time Actions
# ============================================================================

@socketio.on('connect')
def handle_connect(auth):
    """Handle client connection."""
    # Check authentication if required
    if Config.REQUIRE_AUTH:
        if not auth or 'token' not in auth:
            logger.warning(
                f"Unauthenticated connection attempt: {request.sid}"
            )
            return False

        # Verify token
        from auth import AuthManager
        payload = AuthManager.verify_token(auth['token'])
        if not payload:
            logger.warning(
                f"Invalid token for connection: {request.sid}"
            )
            return False

        logger.info(
            f"Authenticated client connected: {request.sid}"
        )
    else:
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
        emit('action_result', {
            'error': 'No action provided', 'success': False
        })
        return

    action_data = data['action']
    result = action_executor.execute_action(action_data)

    emit('action_result', result.to_dict())


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
# Frontend File Serving (for Electron app)
# ============================================================================

@app.route('/<path:path>')
def serve_frontend(path):
    """Serve frontend files for the Electron app."""
    # Skip API routes
    if path.startswith('api/') or path.startswith('avatars/'):
        return jsonify({'error': 'Not found'}), 404

    # Use absolute path resolution
    backend_dir = Path(__file__).resolve().parent
    project_root = backend_dir.parent
    frontend_path = project_root / 'frontend' / 'dist' / path

    # Check if the file exists in the dist directory
    if frontend_path.exists() and frontend_path.is_file():
        return send_file(str(frontend_path))

    # If it's a frontend route (no file extension), serve index.html for SPA routing
    if '.' not in path:
        index_path = project_root / 'frontend' / 'dist' / 'index.html'
        if index_path.exists():
            return send_file(str(index_path))

    # If nothing found, return 404
    return jsonify({'error': 'File not found'}), 404

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    host = Config.HOST if Config.ALLOW_LAN else '127.0.0.1'
    port = Config.PORT

    logger.info(f"Starting VDock server on {host}:{port}")
    logger.info(f"Plugins loaded: {len(plugin_manager.plugins)}")
    
    if Config.DEBUG:
        logger.warning("Running in DEBUG mode - not suitable for production!")
        logger.info("To disable this warning, set DEBUG=False in your .env file")

    socketio.run(
        app,
        host=host,
        port=port,
        debug=Config.DEBUG,
        allow_unsafe_werkzeug=True
    )
