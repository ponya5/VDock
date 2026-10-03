"""Claude Code usage + context fill (DL-145 Phase 2)."""
import logging
from datetime import date

from flask import Blueprint, jsonify, request

from auth import require_auth
from integrations import agent_state
from services import claude_usage

logger = logging.getLogger('vdock')

agent_usage_bp = Blueprint('agent_usage', __name__)


def _limit_arg() -> float:
    try:
        return max(0.0, float(request.args.get('limit_usd', 0) or 0))
    except ValueError:
        return 0.0


@agent_usage_bp.route('/api/agent-usage', methods=['GET'])
@require_auth
def get_usage():
    """Today's spend plus usage of every live Claude Code session."""
    today = date.today()
    limit = _limit_arg()
    try:
        spend = claude_usage.today_usage(today)
        sessions = [
            usage for entry in agent_state.session_entries('claude')
            if (usage := claude_usage.session_usage(entry.get('session_id') or '', today))
        ]
    except OSError as error:
        logger.warning('Could not read Claude transcripts: %s', error)
        return jsonify({'success': False,
                        'error': 'Could not read Claude Code transcripts'}), 500
    return jsonify({
        'success': True, 'today': spend, 'sessions': sessions,
        'limit_usd': limit,
        'status': claude_usage.limit_status(spend['cost_usd'], limit),
    })
