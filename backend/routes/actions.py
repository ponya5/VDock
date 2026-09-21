"""Action execution routes."""
import logging
from typing import Any, Callable, Dict, Optional

from flask import Blueprint, request, jsonify
from auth import require_auth
from actions.catalog import catalog_to_dict

logger = logging.getLogger('vdock')

actions_bp = Blueprint('actions', __name__)

# Injected by app.py (same pattern as agent_events) — broadcasts toggle
# side changes so every window/device paints the same switch state.
_emitter: Optional[Callable[[str, Dict[str, Any]], None]] = None


def set_emitter(fn: Callable[[str, Dict[str, Any]], None]) -> None:
    global _emitter
    _emitter = fn


def _broadcast_toggle(button_id: Optional[str], result_data: Dict[str, Any]) -> None:
    if not _emitter or 'side' not in result_data:
        return
    try:
        _emitter('toggle_state', {
            'button_id': button_id,
            'side': result_data['side'],
            'sublabel': result_data.get('sublabel'),
        })
    except Exception as e:  # pragma: no cover - defensive
        logger.error('Failed to broadcast toggle state: %s', e)


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

    if not isinstance(action_data, dict):
        return jsonify({'error': 'Action must be an object', 'success': False}), 400

    # Import singleton to avoid circular imports
    from app import action_executor
    
    if action_executor is None:
        return jsonify({'error': 'Action executor unavailable', 'success': False}), 503
        
    action_type = action_data.get('type', '')

    # Long actions cannot finish inside the request. Hand them to the job
    # runner and answer immediately; the result arrives over Socket.IO.
    # A multi_action with enough configured delay also goes to the job runner —
    # axios gives up at 30s while a "launch app, wait 45s, press play" chain is
    # still sleeping.
    if not data.get('wait') and (
        action_executor.is_long_running(action_type) or _looks_long(action_data)
    ):
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

    if result.success and isinstance(result.data, dict):
        _broadcast_toggle(data.get('button_id'), result.data)

    return jsonify(result.to_dict())


@actions_bp.route('/api/actions/toggles', methods=['GET'])
@require_auth
def get_toggle_states():
    """All toggle sides — clients sync button faces on load/reconnect."""
    from actions.toggle_action import _sides
    return jsonify({'success': True, 'sides': dict(_sides)})


def _looks_long(action_data: Dict[str, Any]) -> bool:
    """Estimate a multi_action's sleep budget — over the client's timeout it
    belongs on the job runner even though every step is fast."""
    if action_data.get('type') != 'multi_action':
        return False
    cfg = action_data.get('config') or {}
    steps = cfg.get('actions') or []
    if not isinstance(steps, list):
        return False
    default_delay = float(cfg.get('delay', 0.1))
    total = 0.0
    for i, step in enumerate(steps[:-1]):
        ms = step.get('delay') if isinstance(step, dict) else None
        total += (float(ms) / 1000) if ms else default_delay
    return total > 20


@actions_bp.route('/api/actions/jobs/<job_id>', methods=['GET'])
@require_auth
def get_action_job(job_id):
    """Poll a background action, for clients that missed the socket event."""
    from services.job_runner import get_job_runner

    job = get_job_runner().get_job(job_id)
    if job is None:
        return jsonify({'error': 'Job not found', 'success': False}), 404

    return jsonify({'success': True, **job.to_dict()})
