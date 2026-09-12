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
        
    result = action_executor.execute_action(action_data)
    
    return jsonify(result.to_dict())
