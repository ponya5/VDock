"""Action execution routes."""
from flask import Blueprint, request, jsonify
from auth import require_auth
from actions.catalog import catalog_to_dict

actions_bp = Blueprint('actions', __name__)


@actions_bp.route('/api/actions/catalog', methods=['GET'])
@require_auth
def get_action_catalog():
    """Every action the picker can offer, including plugin-provided ones.

    The frontend builds the action list and the button editor's config forms
    from this, so the UI cannot offer something the backend cannot run.
    """
    from app import plugin_manager

    extra = plugin_manager.get_action_specs() if plugin_manager else []
    return jsonify(catalog_to_dict(extra))


@actions_bp.route('/api/actions/execute', methods=['POST'])
@require_auth
def execute_action():
    """Execute an action."""
    data = request.json

    if not data or 'action' not in data:
        return jsonify({'error': 'No action provided', 'success': False}), 400
    
    action_data = data['action']
    
    # Import singleton to avoid circular imports
    from app import action_executor
    
    if action_executor is None:
        return jsonify({'error': 'Action executor unavailable', 'success': False}), 503
        
    action_type = action_data.get('type', '')

    # Long actions cannot finish inside the request. Hand them to the job
    # runner and answer immediately; the result arrives over Socket.IO.
    if not data.get('wait') and action_executor.is_long_running(action_type):
        from services.job_runner import get_job_runner

        job = get_job_runner().submit(
            action_type,
            lambda: action_executor.execute_action(action_data),
            button_id=data.get('button_id'),
        )
        return jsonify({
            'success': True,
            'pending': True,
            'job_id': job.id,
            'message': 'Running...',
            'data': {'job_id': job.id, 'action_type': action_type},
        }), 202

    result = action_executor.execute_action(action_data)
    
    return jsonify(result.to_dict())


@actions_bp.route('/api/actions/jobs/<job_id>', methods=['GET'])
@require_auth
def get_action_job(job_id):
    """Poll a background action, for clients that missed the socket event."""
    from services.job_runner import get_job_runner

    job = get_job_runner().get_job(job_id)
    if job is None:
        return jsonify({'error': 'Job not found', 'success': False}), 404

    return jsonify({'success': True, **job.to_dict()})
