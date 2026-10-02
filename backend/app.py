"""Main Flask application for VDock backend."""
import sys

# `python app.py` runs this file as `__main__`. Routes that lazily
# `from app import action_executor` would otherwise execute it a second time
# as module `app` -- building a second, unserved SocketIO and re-pointing
# every broadcaster (agent state, alerts, background-job results) at it, so
# no server push would ever reach a client again.
if __name__ == '__main__':
    sys.modules.setdefault('app', sys.modules[__name__])

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
from config import env_file
# One documented .env: backend/.env from source, DATA_DIR/.env when frozen.
load_dotenv(env_file())
if getattr(sys, 'frozen', False):
    # Older installs kept .env next to the exe (cwd); still honour it.
    load_dotenv()

from config import Config
from auth import require_auth
from models import BUILTIN_THEMES, Theme
from actions import ActionExecutor
from plugins import PluginManager
from utils import FileManager, setup_logger
from services.job_runner import get_job_runner
from services import volume_monitor
from services import now_playing
from services import audio_spectrum
from services import triggers as triggers_service

# Import route blueprints
from routes.auth import auth_bp
from routes.profiles import profiles_bp
from routes.actions import actions_bp
from routes.config import config_bp
from routes.upload import upload_bp, serve_uploaded_file
from routes.assets import assets_bp
from routes.system_metrics import system_metrics_bp
from routes.app_monitor import app_monitor_bp
from routes.system import system_bp
from routes.templates import templates_bp
from routes.weather import weather_bp
from routes.news import news_bp
from routes.market import market_bp
from routes.user_settings import user_settings_bp
from routes.app_profiles import app_profiles_bp
from routes.logs import logs_bp
from routes.agent_events import agent_events_bp, set_emitter as set_agent_events_emitter
from routes.agent_sessions import agent_sessions_bp
from routes.agent_mission import agent_mission_bp
from routes.feedback import feedback_bp
from routes.now_playing import now_playing_bp
from routes.geo import geo_bp
from routes.triggers import triggers_bp
from routes.mcp import mcp_bp, set_emitter as set_mcp_emitter, \
    set_executor as set_mcp_executor
from routes.actions import set_emitter as set_actions_emitter

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
# Bound request bodies — without this Werkzeug buffers an unlimited upload
# in memory/disk before the route's own size check ever runs.
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB (upload cap is 10MB)

# Add security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # connect-src names the external APIs the widgets actually call
    # (weather geocode + forecast, market prices, reverse-geocoding);
    # style/font-src allow Google Fonts, which the UI requests at boot.
    # Everything else stays 'self'.
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' data: https://fonts.gstatic.com; "
        "connect-src 'self' ws: wss: "
        "https://api.open-meteo.com https://geocoding-api.open-meteo.com "
        "https://api.coingecko.com https://api.bigdatacloud.net;"
    )
    if Config.USE_SSL:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Initialize extensions
CORS(app, origins=Config.CORS_ORIGINS)

# Saved toggle switches (config.json, written by Settings → Server) are the
# source of truth — apply them before the socket CORS list and the __main__
# bind decision read ALLOW_LAN. init_app() re-applies them, harmlessly.
Config.apply_saved_toggles()

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
    cors_allowed_origins=Config.socket_origins(),
    async_mode='threading'
)

# Initialize services
Config.init_app()
logger = setup_logger('vdock', log_file=Config.DATA_DIR / 'vdock.log')
plugin_manager = PluginManager()
action_executor = ActionExecutor(plugin_manager)

# Load user drop-in plugins and the integration packs that ship with VDock.
plugin_manager.load_plugins()
plugin_manager.load_builtin_packs()

# Long-running actions (Claude Code prompts, gh commands) run off the request
# thread and report back over Socket.IO.
job_runner = get_job_runner()
job_runner.set_emitter(lambda event, payload: socketio.emit(event, payload))
# Threads the Socket.IO server did not spawn cannot emit to clients in
# threading mode -- their emits are dropped silently.
job_runner.set_spawner(socketio.start_background_task)
# Agent attention events (Claude Code hook POSTs) reach every client.
set_agent_events_emitter(lambda event, payload: socketio.emit(event, payload))
# Toggle side changes reach every client too — same deck, same switch state.
set_actions_emitter(lambda event, payload: socketio.emit(event, payload))
# Volume changed anywhere (keys, flyout, another surface) → every client
# follows. Same spawn contract as job_runner: a thread the server did not
# spawn cannot emit in threading mode.
volume_monitor.set_emitter(lambda event, payload: socketio.emit(event, payload))
volume_monitor.set_spawner(socketio.start_background_task)
# Now-playing (SMTC) and spectrum monitors share the same spawn contract —
# their emits must come from a thread Socket.IO spawned. Both idle quietly
# when their optional deps / platform are missing.
now_playing.set_emitter(lambda event, payload: socketio.emit(event, payload))
now_playing.set_spawner(socketio.start_background_task)
audio_spectrum.set_emitter(lambda event, payload: socketio.emit(event, payload))
audio_spectrum.set_spawner(socketio.start_background_task)
# WASAPI loopback capture is a Windows-only feature today; elsewhere the
# service stays inert and the widget shows its honest unavailable state.
audio_spectrum.set_enabled(sys.platform == 'win32')
# Triggers run headless: time/app/agent/webhook events fire deck actions,
# scene navigations and panel notifications.
triggers_service.set_emitter(lambda event, payload: socketio.emit(event, payload))
triggers_service.set_spawner(socketio.start_background_task)
triggers_service.set_executor(action_executor)
# MCP tools act on the deck through the same executor + emitter so agents
# can drive the panel (DL-121).
set_mcp_emitter(lambda event, payload: socketio.emit(event, payload))
set_mcp_executor(action_executor)

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
app.register_blueprint(news_bp)
app.register_blueprint(market_bp)
app.register_blueprint(user_settings_bp)
app.register_blueprint(app_profiles_bp)
app.register_blueprint(logs_bp)
app.register_blueprint(agent_events_bp)
app.register_blueprint(agent_sessions_bp)
app.register_blueprint(agent_mission_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(now_playing_bp)
app.register_blueprint(geo_bp, url_prefix='/api')
app.register_blueprint(triggers_bp)
app.register_blueprint(mcp_bp)

# Exempt critical endpoints from rate limiting
limiter.exempt(profiles_bp)  # Profile saves are critical
limiter.exempt(actions_bp)  # Action execution (frequent button clicks)
limiter.exempt(user_settings_bp)  # UI settings persistence
# Self-refreshing data widgets (weather/news/market/sports, metrics, config)
# poll on their own timers — a modest daily/hourly cap is exhausted by normal
# operation, after which every endpoint 429s and widgets show stale/empty
# states. These are local-network data reads, not abuse surface; auth and
# upload stay rate-limited.
limiter.exempt(news_bp)
limiter.exempt(market_bp)
limiter.exempt(weather_bp)
limiter.exempt(system_metrics_bp)
limiter.exempt(app_monitor_bp)
limiter.exempt(config_bp)
# Frontend error/event posts can burst during a failure — exempt so logging
# can't burn the daily quota and take down the data widgets again (DL-023).
limiter.exempt(logs_bp)
# Uploaded files are served through upload_bp — every <img> on the dashboard
# (avatars, backgrounds, button icons) plus picker thumbnail grids count as
# requests. Keep the upload POST write path limited, exempt the GET view and
# the remaining local-read blueprints (asset catalogs, ports/system,
# templates, app-profiles) so browsing settings can't drain the quota.
limiter.exempt(serve_uploaded_file)
limiter.exempt(assets_bp)
limiter.exempt(system_bp)
limiter.exempt(templates_bp)
limiter.exempt(app_profiles_bp)
# Agent hooks are localhost-only local calls — a 429 must never swallow an
# "agent is waiting" alert.
limiter.exempt(agent_events_bp)
# The session picker polls every 4 s (DL-071) — under a modest daily/hourly
# cap that alone exhausts the quota, after which the picker silently shows
# "No session" while real sessions run. Localhost enumeration, not abuse.
limiter.exempt(agent_sessions_bp)
# Mission Control polls every 15 s (240 req/h) -- exceeds any modest opt-in
# cap, after which the whole deck 429s. Localhost-grade read traffic.
limiter.exempt(agent_mission_bp)
# Now-playing track + art are read on widget mount/refresh — same
# self-refreshing-data class as the other widgets.
limiter.exempt(now_playing_bp)
# Trigger CRUD is low-volume settings traffic and fire/<key> is a
# localhost webhook — neither is an abuse surface.
limiter.exempt(triggers_bp)
# MCP clients may poll tools/call rapidly; the endpoint is localhost-only
# (or Bearer-authenticated) already.
limiter.exempt(mcp_bp)


# ============================================================================
# Root Route - Serve Frontend for Electron App
# ============================================================================

@app.route('/')
@limiter.exempt
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
    """Execute an action via WebSocket.

    The client's `request_id` is echoed back on `action_result` so concurrent
    actions can be told apart. Without it the client has no way to match a
    result to the action that produced it.
    """
    request_id = data.get('request_id') if isinstance(data, dict) else None

    if not isinstance(data, dict) or 'action' not in data:
        emit('action_result', {
            'request_id': request_id,
            'error': 'No action provided',
            'success': False,
            'message': 'No action provided'
        })
        return

    action_data = data['action']
    result = action_executor.execute_action(action_data)

    emit('action_result', {'request_id': request_id, **result.to_dict()})
    if result.success and isinstance(result.data, dict) and 'side' in result.data:
        socketio.emit('toggle_state', {
            'button_id': data.get('button_id'),
            'side': result.data['side'],
            'sublabel': result.data.get('sublabel'),
        })


@socketio.on('user_settings_changed')
def handle_user_settings_changed(data):
    """Relay UI setting changes to other VDock windows (Electron + browser tabs)."""
    if not isinstance(data, dict):
        return

    settings = data.get('settings')
    if not isinstance(settings, dict):
        return

    # `broadcast=True` is required for this to reach any client other than
    # the sender — without it, Flask-SocketIO's `emit()` defaults to
    # replying only to the requesting client's own session, so combined
    # with `include_self=False` the message was silently going nowhere.
    emit('user_settings_updated', {'settings': settings}, broadcast=True, include_self=False)


# This event reaches every connected client, so it is an allowlist, not a
# passthrough — a generic relay would be a remote-command channel.
ALLOWED_UI_COMMANDS = {'show_screensaver', 'screensaver_layout_edit', 'toggle_quick_deck'}


@socketio.on('ui_command')
def handle_ui_command(data):
    """Relay allowlisted UI commands (e.g. 'show_screensaver') to all windows."""
    if not isinstance(data, dict):
        return

    command = data.get('command')
    if command not in ALLOWED_UI_COMMANDS:
        return

    emit('ui_command', {'command': command}, broadcast=True, include_self=False)


# ============================================================================
# Health Check
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'version': '2.2.0',
        'plugins_loaded': len(plugin_manager.plugins),
        'features': {
            'user_settings': True
        }
    })


# ============================================================================
# Frontend File Serving (for Electron app)
# ============================================================================

@app.route('/<path:path>')
@limiter.exempt
def serve_frontend(path):
    """Serve frontend files for the Electron app."""
    # Skip API routes
    if path.startswith('api/') or path.startswith('avatars/'):
        return jsonify({'error': 'Not found'}), 404

    # Use absolute path resolution
    backend_dir = Path(__file__).resolve().parent
    project_root = backend_dir.parent
    dist_root = (project_root / 'frontend' / 'dist').resolve()
    frontend_path = (dist_root / path).resolve()

    # Path traversal guard — resolve() collapses '..', so anything escaping
    # dist_root (e.g. /..%2F..%2Fbackend%2F.env) must never be served.
    if not frontend_path.is_relative_to(dist_root):
        return jsonify({'error': 'File not found'}), 404

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
    # ALLOW_LAN asked for a LAN-visible server but HOST defaults to localhost —
    # bind broadly unless the user pinned a specific interface.
    host = Config.HOST if Config.ALLOW_LAN else '127.0.0.1'
    if Config.ALLOW_LAN and host in ('127.0.0.1', 'localhost'):
        host = '0.0.0.0'
    port = Config.PORT

    # Never sign deck tokens with a missing/published-placeholder key. Lives
    # here (not at import) so test imports never write the user's .env.
    Config.ensure_strong_secret_key()

    logger.info(f"Starting VDock server on {host}:{port}")
    logger.info(f"Plugins loaded: {len(plugin_manager.plugins)}")
    
    if Config.DEBUG:
        logger.warning("Running in DEBUG mode - not suitable for production!")
        logger.info("To disable this warning, set DEBUG=False in your .env file")

    # Follows OS-side volume changes and pushes them to every client. Started
    # here rather than at module level so test imports never spawn the loop.
    volume_monitor.start()
    # SMTC now-playing + spectrum capture idle gracefully where unsupported.
    now_playing.start()
    audio_spectrum.start()
    # Headless automation: time/app/agent/webhook triggers.
    triggers_service.start()

    socketio.run(
        app,
        host=host,
        port=port,
        debug=Config.DEBUG,
        allow_unsafe_werkzeug=True
    )
