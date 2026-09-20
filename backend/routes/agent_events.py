"""Agent attention events — "agent is waiting for you" alerts.

Claude Code (and any other local agent) can notify VDock when it is
blocked waiting for user input — permission prompts, idle waiting, or
completion. POSTs are accepted only from localhost: this is a local
webhook surface for agent hooks, not a network API.

The hook installer merges a `command` hook into ~/.claude/settings.json
for the `Notification` and `Stop` events, pointed at the bundled
`scripts/vdock_agent_hook.py` helper, which re-POSTs here.
"""
import json
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from flask import Blueprint, jsonify, request

from auth import require_auth
from config import Config

logger = logging.getLogger('vdock')

agent_events_bp = Blueprint('agent_events', __name__)

# ---------------------------------------------------------------------------
# State + emitter (app.py injects the socket emit fn — same pattern as
# job_runner, avoiding a circular import).
# ---------------------------------------------------------------------------

_emitter: Optional[Callable[[str, Dict[str, Any]], None]] = None
_current_alert: Optional[Dict[str, Any]] = None

# Alerts go stale — if the agent was killed mid-prompt nothing clears it.
ALERT_TTL_SECONDS = 30 * 60

ALLOWED_EVENTS = {'waiting', 'clear'}
ALLOWED_SOURCES = {'claude', 'cursor', 'devin', 'generic'}

# Marker the installer searches for in ~/.claude/settings.json to detect
# (and not duplicate) our hook entry.
HOOK_MARKER = 'vdock_agent_hook'


def set_emitter(fn: Callable[[str, Dict[str, Any]], None]) -> None:
    global _emitter
    _emitter = fn


def _broadcast() -> None:
    if _emitter:
        try:
            _emitter('agent_alert', {'alert': _current_alert})
        except Exception as e:  # pragma: no cover - defensive
            logger.error('Failed to broadcast agent alert: %s', e)


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


# ---------------------------------------------------------------------------
# Event intake
# ---------------------------------------------------------------------------

@agent_events_bp.route('/api/agent-events', methods=['POST'])
def post_agent_event():
    """Record + broadcast an agent attention event.

    Body: {source, event: 'waiting'|'clear', message?, project?, cwd?}
    Deliberately unauthenticated — agent hooks run as local shell commands
    and cannot carry UI tokens; localhost-only instead.
    """
    if not _localhost_only():
        return jsonify({'success': False, 'error': 'Localhost only'}), 403

    global _current_alert
    data = request.get_json(silent=True) or {}

    source = str(data.get('source') or 'generic')[:32]
    if source not in ALLOWED_SOURCES:
        source = 'generic'
    event = str(data.get('event') or 'waiting')
    if event not in ALLOWED_EVENTS:
        return jsonify({'success': False, 'error': 'Unknown event'}), 400

    if event == 'clear':
        _current_alert = None
        _broadcast()
        return jsonify({'success': True})

    message = str(data.get('message') or 'Agent is waiting for input')[:300]
    _current_alert = {
        'source': source,
        'message': message,
        'project': str(data.get('project') or '')[:120],
        'cwd': str(data.get('cwd') or '')[:300],
        'ts': time.time(),
    }
    logger.info('Agent attention: %s — %s', source, message)
    _broadcast()
    return jsonify({'success': True})


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
    _broadcast()
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# Claude Code hook install
# ---------------------------------------------------------------------------

def _hook_script() -> Path:
    return Path(__file__).resolve().parent.parent / 'scripts' / 'vdock_agent_hook.py'


def _hook_command() -> str:
    # Forward slashes work on Windows Python too and avoid JSON escaping pain.
    script = _hook_script().as_posix()
    return f'python "{script}" --port {Config.PORT}'


def _settings_path() -> Path:
    return Path.home() / '.claude' / 'settings.json'


def _load_settings() -> Dict[str, Any]:
    path = _settings_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f'~/.claude/settings.json is not valid JSON: {e}')


def _hook_installed(settings: Dict[str, Any]) -> bool:
    for entries in (settings.get('hooks') or {}).values():
        for entry in entries if isinstance(entries, list) else []:
            for hook in entry.get('hooks', []):
                if HOOK_MARKER in str(hook.get('command', '')):
                    return True
    return False


@agent_events_bp.route('/api/agent-events/hook-status', methods=['GET'])
@require_auth
def hook_status():
    """Whether our Claude Code hook is present in ~/.claude/settings.json."""
    try:
        settings = _load_settings()
    except ValueError:
        return jsonify({'success': True, 'installed': False, 'parse_error': True})
    return jsonify({
        'success': True,
        'installed': _hook_installed(settings),
        'settings_path': str(_settings_path()),
    })


@agent_events_bp.route('/api/agent-events/install-hook', methods=['POST'])
@require_auth
def install_hook():
    """Merge the VDock hook into ~/.claude/settings.json.

    Claude Code fires `Notification` when the agent needs permission or has
    been idle waiting for input, and `Stop` when it finishes a response —
    the helper script maps those to waiting/clear events here.
    """
    try:
        settings = _load_settings()
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    if _hook_installed(settings):
        return jsonify({'success': True, 'installed': True, 'already': True})

    command = _hook_command()
    hooks = settings.setdefault('hooks', {})
    for event_name in ('Notification', 'Stop'):
        entries = hooks.setdefault(event_name, [])
        entries.append({
            'matcher': '',
            'hooks': [{'type': 'command', 'command': command}],
        })

    path = _settings_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Keep a one-shot backup next to the file before rewriting it.
        if path.exists():
            backup = path.with_suffix('.vdock-backup.json')
            backup.write_text(path.read_text(encoding='utf-8'), encoding='utf-8')
        path.write_text(json.dumps(settings, indent=2) + '\n', encoding='utf-8')
    except OSError as e:
        return jsonify({'success': False, 'error': f'Could not write settings: {e}'}), 500

    logger.info('Installed VDock agent hook into %s', path)
    return jsonify({'success': True, 'installed': True, 'settings_path': str(path)})
