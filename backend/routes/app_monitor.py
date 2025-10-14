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

