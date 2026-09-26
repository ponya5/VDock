"""
API routes for application monitoring and auto scene switching.
"""

from flask import Blueprint, jsonify, request
from auth import require_auth
from utils.app_monitor import get_app_monitor, start_monitoring, stop_monitoring, get_current_active_app

app_monitor_bp = Blueprint('app_monitor', __name__, url_prefix='/api/app-monitor')


@app_monitor_bp.route('/status', methods=['GET'])
@require_auth
def monitor_status():
    """Get the current status of the app monitoring service."""
    monitor = get_app_monitor()
    
    return jsonify({
        "running": monitor.running,
        "current_app": monitor.get_current_app(),
        "poll_interval": monitor.poll_interval
    })


@app_monitor_bp.route('/start', methods=['POST'])
@require_auth
def start_monitor():
    """Start the app monitoring service."""
    data = request.get_json() or {}
    poll_interval = data.get('poll_interval', 1.0)
    
    try:
        monitor = get_app_monitor(poll_interval)
        monitor.start()
        
        return jsonify({
            "success": True,
            "message": "App monitoring started",
            "running": monitor.running
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app_monitor_bp.route('/stop', methods=['POST'])
@require_auth
def stop_monitor():
    """Stop the app monitoring service."""
    try:
        stop_monitoring()
        
        return jsonify({
            "success": True,
            "message": "App monitoring stopped"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app_monitor_bp.route('/current-app', methods=['GET'])
@require_auth
def current_app():
    """Get the currently active application (one-time check)."""
    try:
        app_info = get_current_active_app()
        
        if app_info:
            return jsonify(app_info)
        else:
            return jsonify({
                "error": "Could not detect active application"
            }), 404
            
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@app_monitor_bp.route('/active-app', methods=['GET'])
@require_auth
def active_app():
    """Get the currently monitored active application."""
    monitor = get_app_monitor()
    current = monitor.get_current_app()
    
    if current:
        return jsonify(current)
    else:
        return jsonify({
            "message": "No active application tracked"
        }), 404


@app_monitor_bp.route('/detected-profiles', methods=['GET'])
@require_auth
def detected_profiles():
    """App profiles whose process is currently running.

    Terminal agents (claude-code, devin) claim host exes like cmd.exe — a
    running terminal is not a running agent — so those are detected via
    their commands' ``session_marker`` against process names and command
    lines. Editor apps match on their real exes. ``running_exes`` is
    included so custom integrations (user maps any exe to a scene) can
    check membership client-side without a second process scan.
    """
    import logging
    import psutil
    from integrations import sessions
    from integrations.keymaps import ALL_PROFILES

    logger = logging.getLogger('vdock')
    try:
        names = set()
        for proc in psutil.process_iter(['name']):
            try:
                name = (proc.info.get('name') or '').lower()
                if name:
                    names.add(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied,
                    psutil.ZombieProcess):
                continue

        detected = []
        for profile in ALL_PROFILES:
            markers = {c.session_marker for c in profile.commands
                       if c.session_marker}
            if profile.kind == 'terminal_agent':
                # Same matcher the liveness gate and window resolver use —
                # a substring scan here reported desktop-app helpers like
                # chrome-native-host.exe as live sessions.
                if any(sessions.iter_session_pids(m) for m in markers):
                    detected.append(profile.id)
            elif any(exe.lower() in names for exe in profile.exes):
                detected.append(profile.id)

        return jsonify({
            'detected_profiles': detected,
            'running_exes': sorted(names),
        })
    except Exception as e:
        logger.error('Failed to detect app profiles: %s', e)
        return jsonify({'error': 'Detection failed'}), 500


@app_monitor_bp.route('/running-apps', methods=['GET'])
@require_auth
def running_apps():
    """Get a list of all currently running applications."""
    import logging
    import psutil
    logger = logging.getLogger('vdock')
    try:
        seen = set()
        apps = []
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                info = proc.info
                exe = info.get('name') or ''
                if not exe or exe in seen:
                    continue
                seen.add(exe)
                apps.append({
                    'name': exe.replace('.exe', '').replace('_', ' ').title(),
                    'exe': exe,
                    'pid': info.get('pid', 0),
                    'path': info.get('exe') or ''
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        apps.sort(key=lambda a: a['name'].lower())
        return jsonify(apps)
    except Exception as e:
        logger.error('Failed to get running apps: %s', e)
        return jsonify({'error': str(e)}), 500

