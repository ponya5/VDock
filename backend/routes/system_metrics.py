"""
System Metrics API Routes
Endpoints for fetching real-time system metrics
"""
from flask import Blueprint, jsonify, request
from utils.system_metrics import SystemMetrics
from utils.logger import log_info, log_error

system_metrics_bp = Blueprint('system_metrics', __name__, url_prefix='/api/metrics')


@system_metrics_bp.route('/cpu', methods=['GET'])
def get_cpu_metrics():
    """Get CPU metrics"""
    try:
        metrics = SystemMetrics.get_cpu_metrics()
        return jsonify({'success': True, 'data': metrics})
    except Exception as e:
        log_error(f"Error fetching CPU metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@system_metrics_bp.route('/memory', methods=['GET'])
def get_memory_metrics():
    """Get memory/RAM metrics"""
    try:
        metrics = SystemMetrics.get_memory_metrics()
        return jsonify({'success': True, 'data': metrics})
    except Exception as e:
        log_error(f"Error fetching memory metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@system_metrics_bp.route('/disk', methods=['GET'])
def get_disk_metrics():
    """Get disk usage metrics"""
    try:
        metrics = SystemMetrics.get_disk_metrics()
        return jsonify({'success': True, 'data': metrics})
    except Exception as e:
        log_error(f"Error fetching disk metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@system_metrics_bp.route('/network', methods=['GET'])
def get_network_metrics():
    """Get network statistics"""
    try:
        metrics = SystemMetrics.get_network_metrics()
        return jsonify({'success': True, 'data': metrics})
    except Exception as e:
        log_error(f"Error fetching network metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@system_metrics_bp.route('/temperature', methods=['GET'])
def get_temperature_metrics():
    """Get temperature sensors data"""
    try:
        metrics = SystemMetrics.get_temperature_metrics()
        return jsonify({'success': True, 'data': metrics})
    except Exception as e:
        log_error(f"Error fetching temperature metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@system_metrics_bp.route('/battery', methods=['GET'])
def get_battery_metrics():
    """Get battery information"""
    try:
        metrics = SystemMetrics.get_battery_metrics()
        return jsonify({'success': True, 'data': metrics})
    except Exception as e:
        log_error(f"Error fetching battery metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@system_metrics_bp.route('/processes', methods=['GET'])
def get_process_metrics():
    """Get top processes by CPU and memory"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        metrics = SystemMetrics.get_process_metrics(limit=limit)
        return jsonify({'success': True, 'data': metrics})
    except Exception as e:
        log_error(f"Error fetching process metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@system_metrics_bp.route('/system', methods=['GET'])
def get_system_info():
    """Get general system information"""
    try:
        info = SystemMetrics.get_system_info()
        return jsonify({'success': True, 'data': info})
    except Exception as e:
        log_error(f"Error fetching system info: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@system_metrics_bp.route('/all', methods=['GET'])
def get_all_metrics():
    """Get all metrics at once"""
    try:
        metrics = SystemMetrics.get_all_metrics()
        return jsonify({'success': True, 'data': metrics})
    except Exception as e:
        log_error(f"Error fetching all metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@system_metrics_bp.route('/<metric_type>', methods=['GET'])
def get_metric_by_type(metric_type):
    """Get specific metric by type"""
    try:
        metrics = SystemMetrics.get_metric_by_type(metric_type)
        if 'error' in metrics:
            return jsonify({'success': False, 'error': metrics['error']}), 400
        return jsonify({'success': True, 'data': metrics})
    except Exception as e:
        log_error(f"Error fetching metric {metric_type}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@system_metrics_bp.route('/running-apps', methods=['GET'])
def get_running_apps():
    """Get list of currently running applications"""
    try:
        import psutil
        apps = []
        seen_names = set()
        
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'create_time']):
            try:
                info = proc.info
                name = info['name']
                
                # Skip system processes and duplicates
                if name and name not in seen_names and not name.startswith('System'):
                    apps.append({
                        'name': name,
                        'exe': name.lower(),
                        'pid': info['pid'],
                        'path': info['exe'] if info['exe'] else '',
                        'running_since': info['create_time']
                    })
                    seen_names.add(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Sort by name
        apps.sort(key=lambda x: x['name'].lower())
        
        return jsonify({'success': True, 'data': apps})
    except Exception as e:
        log_error(f"Error fetching running apps: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

