"""
System Metrics API Routes
Endpoints for fetching real-time system metrics
"""
import logging
from functools import wraps
from flask import Blueprint, jsonify, request
from utils.system_metrics import SystemMetrics

logger = logging.getLogger(__name__)

def metric_route(fetch_fn):
    """Wraps a metrics fetch function in standard try/except/jsonify."""
    @wraps(fetch_fn)
    def wrapper(*args, **kwargs):
        try:
            data = fetch_fn(*args, **kwargs)
            return jsonify({'success': True, 'data': data})
        except Exception as e:
            logger.error('Metrics error: %s', e)
            return jsonify({'success': False, 'error': str(e)}), 500
    return wrapper

system_metrics_bp = Blueprint(
    'system_metrics', __name__, url_prefix='/api/metrics'
)


@system_metrics_bp.route('/cpu', methods=['GET'])
def get_cpu_metrics():
    """Get CPU metrics"""
    return metric_route(SystemMetrics.get_cpu_metrics)()


@system_metrics_bp.route('/memory', methods=['GET'])
def get_memory_metrics():
    """Get memory/RAM metrics"""
    return metric_route(SystemMetrics.get_memory_metrics)()


@system_metrics_bp.route('/disk', methods=['GET'])
def get_disk_metrics():
    """Get disk usage metrics"""
    return metric_route(SystemMetrics.get_disk_metrics)()


@system_metrics_bp.route('/network', methods=['GET'])
def get_network_metrics():
    """Get network statistics"""
    return metric_route(SystemMetrics.get_network_metrics)()


@system_metrics_bp.route('/temperature', methods=['GET'])
def get_temperature_metrics():
    """Get temperature sensors data"""
    return metric_route(SystemMetrics.get_temperature_metrics)()


@system_metrics_bp.route('/battery', methods=['GET'])
def get_battery_metrics():
    """Get battery information"""
    return metric_route(SystemMetrics.get_battery_metrics)()


@system_metrics_bp.route('/processes', methods=['GET'])
def get_process_metrics():
    """Get top processes by CPU and memory"""
    limit = request.args.get('limit', default=10, type=int)
    return metric_route(SystemMetrics.get_process_metrics)(limit=limit)


@system_metrics_bp.route('/system', methods=['GET'])
def get_system_info():
    """Get general system information"""
    return metric_route(SystemMetrics.get_system_info)()


@system_metrics_bp.route('/all', methods=['GET'])
def get_all_metrics():
    """Get all metrics at once"""
    return metric_route(SystemMetrics.get_all_metrics)()


@system_metrics_bp.route('/running-apps', methods=['GET'])
def get_running_apps():
    """Get list of currently running applications"""
    return metric_route(SystemMetrics.get_running_apps)()


@system_metrics_bp.route('/<metric_type>', methods=['GET'])
def get_metric_by_type(metric_type):
    """Get specific metric by type"""
    try:
        metrics = SystemMetrics.get_metric_by_type(metric_type)
        if 'error' in metrics:
            return jsonify({'success': False, 'error': metrics['error']}), 400
        return jsonify({'success': True, 'data': metrics})
    except Exception as e:
        logger.error('Metrics error: %s', e)
        return jsonify({'success': False, 'error': str(e)}), 500
