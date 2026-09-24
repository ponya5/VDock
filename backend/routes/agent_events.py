"""Agent events — live agent state plus "agent is waiting for you" alerts.

Agent hooks (``scripts/vdock_agent_hook.py``, installed into Claude Code and
Cursor) POST here whenever the agent's state changes: ready for a prompt,
working, or blocked on a permission dialog. Two things follow:

  * the per-agent state (``integrations/agent_state``) is broadcast as
    ``agent_state`` so the dashboard can offer the actions that fit;
  * a permission/idle notification also raises the DL-045 alert popup,
    and any other state clears it.

POSTs are accepted only from localhost: this is a local webhook surface
for agent hooks, not a network API.
"""
import logging
import time
from typing import Any, Callable, Dict, Optional

from flask import Blueprint, jsonify, request

from auth import require_auth
from integrations import agent_hooks, agent_state

logger = logging.getLogger('vdock')

agent_events_bp = Blueprint('agent_events', __name__)

# ---------------------------------------------------------------------------
# State + emitter (app.py injects the socket emit fn — same pattern as
# job_runner, avoiding a circular import).
# ---------------------------------------------------------------------------

_emitter: Optional[Callable[[str, Dict[str, Any]], None]] = None
_current_alert: Optional[Dict[str, Any]] = None

# Alerts go stale — if the agent was killed mid-prompt nothing clears it.
ALERT_TTL_SECONDS = agent_state.STATE_TTL_SECONDS

#: DL-045 hooks send ``event`` instead of ``state``; keep them working.
LEGACY_STATE_BY_EVENT = {'waiting': agent_state.STATE_PERMISSION,
                         'clear': agent_state.STATE_READY}
STATE_ENDED = 'ended'


def set_emitter(fn: Callable[[str, Dict[str, Any]], None]) -> None:
    global _emitter
    _emitter = fn


def _emit(event_name: str, payload: Dict[str, Any]) -> None:
    if not _emitter:
        return
    try:
        _emitter(event_name, payload)
    except Exception as error:  # pragma: no cover - defensive
        logger.error('Failed to broadcast %s: %s', event_name, error)


def _broadcast_alert() -> None:
    _emit('agent_alert', {'alert': _current_alert})


def _broadcast_states() -> None:
    _emit('agent_state', {'states': agent_state.snapshot()})


def _is_expired(alert: Dict[str, Any]) -> bool:
    return (time.time() - alert.get('ts', 0)) > ALERT_TTL_SECONDS


def _current() -> Optional[Dict[str, Any]]:
    global _current_alert
    if _current_alert and _is_expired(_current_alert):
        _current_alert = None
    return _current_alert


def _localhost_only() -> bool:
    """Accept posts only from the machine VDock runs on."""
    return request.remote_addr in ('127.0.0.1', '::1', 'localhost')


def _requested_state(data: Dict[str, Any]) -> Optional[str]:
    state = data.get('state')
    if state:
        return str(state)
    return LEGACY_STATE_BY_EVENT.get(str(data.get('event') or 'waiting'))


def _wants_attention(data: Dict[str, Any], state: Optional[str]) -> bool:
    """Should this event raise the popup? Hooks flag notifications
    explicitly; a legacy 'waiting' event always did."""
    if 'attention' in data:
        return bool(data.get('attention'))
    return state == agent_state.STATE_PERMISSION


def _update_alert(source: str, raise_alert: bool, message: str,
                  project: str, cwd: str) -> None:
    global _current_alert
    if raise_alert:
        _current_alert = {
            'source': source,
            'message': message or 'Agent is waiting for input',
            'project': project,
            'cwd': cwd,
            'ts': time.time(),
        }
        logger.info('Agent attention: %s — %s', source, message)
    elif _current_alert and _current_alert.get('source') == source:
        combined = agent_state.get(source) or {}
        # Another session of this agent may still be blocked on a prompt.
        if combined.get('state') != agent_state.STATE_PERMISSION:
            _current_alert = None
    _broadcast_alert()


# ---------------------------------------------------------------------------
# Event intake
# ---------------------------------------------------------------------------

@agent_events_bp.route('/api/agent-events', methods=['POST'])
def post_agent_event():
    """Record + broadcast an agent state change.

    Body: {source, state: 'ready'|'working'|'permission'|'ended',
           message?, project?, cwd?}
    Legacy body: {source, event: 'waiting'|'clear', ...}.
    Deliberately unauthenticated — agent hooks run as local shell commands
    and cannot carry UI tokens; localhost-only instead.
    """
    if not _localhost_only():
        return jsonify({'success': False, 'error': 'Localhost only'}), 403

    data = request.get_json(silent=True) or {}
    source = agent_state.normalise_source(data.get('source'))
    state = _requested_state(data)
    message = str(data.get('message') or '')[:300]
    project = str(data.get('project') or '')[:120]
    cwd = str(data.get('cwd') or '')[:300]
    session_id = agent_state.normalise_session_id(data.get('session_id'))

    if state == STATE_ENDED:
        agent_state.end_session(source, session_id)
        _broadcast_states()
        _update_alert(source, False, '', project, cwd)
        return jsonify({'success': True})

    if state not in agent_state.ALLOWED_STATES:
        return jsonify({'success': False, 'error': 'Unknown state'}), 400

    agent_state.record(source, state, message=message, cwd=cwd,
                       project=project, session_id=session_id)
    _broadcast_states()
    _update_alert(source, _wants_attention(data, state), message, project, cwd)
    return jsonify({'success': True})


@agent_events_bp.route('/api/agent-events/states', methods=['GET'])
@require_auth
def get_agent_states():
    """Current state of every agent that reported recently."""
    return jsonify({'success': True, 'states': agent_state.snapshot()})


@agent_events_bp.route('/api/agent-events/current', methods=['GET'])
@require_auth
def get_current_alert():
    """Current pending alert — clients fetch on load/reconnect."""
    return jsonify({'success': True, 'alert': _current()})


@agent_events_bp.route('/api/agent-events/current', methods=['DELETE'])
@require_auth
def clear_current_alert():
    """Dismiss the current alert (user pressed Dismiss)."""
    global _current_alert
    _current_alert = None
    _broadcast_alert()
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# Hook install (Claude Code, Cursor)
# ---------------------------------------------------------------------------

def _requested_agent() -> str:
    return str(request.args.get('agent') or 'claude')


@agent_events_bp.route('/api/agent-events/hook-status', methods=['GET'])
@require_auth
def hook_status():
    """Whether VDock's hook is present in the agent's settings file."""
    agent = _requested_agent()
    if agent not in agent_hooks.SUPPORTED_AGENTS:
        return jsonify({'success': False, 'error': f'Unsupported agent: {agent}'}), 400
    return jsonify({'success': True, 'agent': agent, **agent_hooks.hook_status(agent)})


@agent_events_bp.route('/api/agent-events/install-hook', methods=['POST'])
@require_auth
def install_hook():
    """Merge the VDock hook into the agent's settings file (idempotent)."""
    agent = _requested_agent()
    if agent not in agent_hooks.SUPPORTED_AGENTS:
        return jsonify({'success': False, 'error': f'Unsupported agent: {agent}'}), 400
    try:
        result = agent_hooks.install_hook(agent)
    except agent_hooks.HookSettingsError as error:
        return jsonify({'success': False, 'error': str(error)}), 400
    except OSError as error:
        return jsonify({'success': False, 'error': f'Could not write settings: {error}'}), 500
    return jsonify({
        'success': True,
        'agent': agent,
        'installed': result.installed,
        'already': result.already,
        'added_events': list(result.added_events),
        'settings_path': str(result.settings_path),
    })
