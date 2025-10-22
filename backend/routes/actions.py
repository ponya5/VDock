"""Action execution routes."""
from flask import Blueprint, request, jsonify
from auth import require_auth

actions_bp = Blueprint('actions', __name__)


@actions_bp.route('/api/actions/execute', methods=['POST'])
@require_auth
def execute_action():
    """Execute an action."""
    data = request.json

    if not data or 'action' not in data:
        return jsonify({'error': 'No action provided', 'success': False}), 400
    
    action_data = data['action']
    
    # Import here to avoid circular imports
    from actions import ActionExecutor
    action_executor = ActionExecutor()
    
    result = action_executor.execute_action(action_data)
    
    return jsonify(result.to_dict())
