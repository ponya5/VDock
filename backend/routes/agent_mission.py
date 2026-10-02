"""Agent Mission Control + approval inbox (DL-144).

One flat list of every live agent session the hooks know about (the existing
``/api/agent-events/states`` is one *combined* entry per agent source), plus
two per-session verbs:

* ``focus``  - raise the session's host window;
* ``decide`` - answer a blocked permission prompt (approve / deny) in THAT
  session, from anywhere on the deck.

``decide`` types ``y`` / ``n`` through the same keymap commands the Claude
Code scene buttons use, so there is one implementation of "answer a prompt".
Because a stale tap must never type into a session that has moved on, the
session is re-checked server-side to still be in ``permission`` first.
"""
import logging
import time
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request

from auth import require_auth
from integrations import agent_state, editor_base
from integrations.keymaps import COMMANDS_BY_ID
from services import agent_prompt, turn_baseline
from utils import window_focus

logger = logging.getLogger('vdock')

agent_mission_bp = Blueprint('agent_mission', __name__)

#: source -> (approve command id, deny command id). Only agents that ship
#: confirm keymaps can be answered remotely; others are listed + focusable.
DECISION_COMMANDS = {
    'claude': ('cc_approve', 'cc_deny'),
}

#: Process marker used to find a source's session window.
_MARKER_BY_SOURCE = {
    'claude': 'claude', 'cursor': 'cursor', 'devin': 'devin',
    'antigravity': 'antigravity',
}

#: Lower sorts first: blocked on you, then idle-and-prompted, then the rest.
_STATE_RANK = {
    agent_state.STATE_PERMISSION: 0,
    agent_state.STATE_READY: 1,
    agent_state.STATE_WORKING: 2,
}

REPLY_EXCERPT_CHARS = 280


def _excerpt(text: str, limit: int) -> str:
    text = ' '.join((text or '').split())
    return text if len(text) <= limit else text[:limit - 1].rstrip() + '…'


def _row(entry: Dict[str, Any], now: float) -> Dict[str, Any]:
    source = entry.get('source', 'generic')
    state = entry.get('state')
    prompted = bool(entry.get('prompted'))
    needs_you = (
        state == agent_state.STATE_PERMISSION
        or (state == agent_state.STATE_READY and prompted)
    )
    return {
        'source': source,
        'session_id': entry.get('session_id'),
        'project': entry.get('project') or '',
        'cwd': entry.get('cwd') or '',
        'state': state,
        'message': entry.get('message') or '',
        'prompt': _excerpt(entry.get('prompt', ''), 160),
        'reply': _excerpt(entry.get('reply', ''), REPLY_EXCERPT_CHARS),
        'prompted': prompted,
        'ts': entry.get('ts'),
        'idle_seconds': max(0, int(now - (entry.get('ts') or now))),
        'needs_you': needs_you,
        'can_decide': (state == agent_state.STATE_PERMISSION
                       and source in DECISION_COMMANDS),
        'can_focus': source in _MARKER_BY_SOURCE,
        'can_prompt': (source in agent_prompt.PROMPT_SOURCES
                       and state == agent_state.STATE_READY),
    }


def mission_rows() -> List[Dict[str, Any]]:
    """Every live session, most urgent first.

    Within "blocked on you" the one that has waited longest leads; the other
    groups put the most recent activity first.
    """
    now = time.time()
    rows: List[Dict[str, Any]] = []
    for source in agent_state.snapshot():
        for entry in agent_state.session_entries(source):
            rows.append(_row(entry, now))

    def sort_key(row: Dict[str, Any]):
        rank = _STATE_RANK.get(row['state'], 3)
        if not row['needs_you'] and row['state'] == agent_state.STATE_READY:
            rank = 2.5  # ready but never prompted: below "working"
        age = row['ts'] or 0
        # permission: oldest first; everything else: newest first
        return (rank, age if rank == 0 else -age)

    rows.sort(key=sort_key)
    return rows


def _find_entry(source: str, session_id: str) -> Optional[Dict[str, Any]]:
    for entry in agent_state.session_entries(source):
        if entry.get('session_id') == session_id:
            return entry
    return None


@agent_mission_bp.route('/api/agent-mission', methods=['GET'])
@require_auth
def get_mission():
    rows = mission_rows()
    return jsonify({
        'success': True,
        'sessions': rows,
        'presets': [{'id': pid, 'label': preset['label']}
                    for pid, preset in agent_prompt.PROMPT_PRESETS.items()],
        'needs_you': sum(1 for r in rows if r['needs_you']),
        'pending_approvals': sum(1 for r in rows if r['can_decide']),
    })


def _body_target():
    data = request.get_json(silent=True) or {}
    source = agent_state.normalise_source(data.get('source'))
    session_id = agent_state.normalise_session_id(data.get('session_id'))
    return data, source, session_id


@agent_mission_bp.route('/api/agent-mission/focus', methods=['POST'])
@require_auth
def focus_session():
    """Bring the session's host window to the front."""
    _, source, session_id = _body_target()
    marker = _MARKER_BY_SOURCE.get(source)
    if marker is None:
        return jsonify({'success': False,
                        'error': f'{source} sessions cannot be focused'}), 400
    entry = _find_entry(source, session_id)
    if entry is None:
        return jsonify({'success': False,
                        'error': 'Session is no longer running'}), 404

    hwnd = window_focus.find_session_host_window(
        marker, prefer_cwd=entry.get('cwd') or None)
    if hwnd is None:
        return jsonify({'success': False,
                        'error': 'Could not find that session\'s window'}), 404
    if not window_focus.focus_hwnd(hwnd):
        return jsonify({'success': False,
                        'error': 'Windows would not bring the window forward'}), 409
    return jsonify({'success': True})


@agent_mission_bp.route('/api/agent-mission/decide', methods=['POST'])
@require_auth
def decide():
    """Approve / deny the blocked permission prompt of ONE session."""
    data, source, session_id = _body_target()
    decision = str(data.get('decision') or '').lower()
    if decision not in ('approve', 'deny'):
        return jsonify({'success': False,
                        'error': 'decision must be approve or deny'}), 400

    commands = DECISION_COMMANDS.get(source)
    if commands is None:
        return jsonify({'success': False,
                        'error': f'{source} cannot be answered remotely'}), 400

    entry = _find_entry(source, session_id)
    if entry is None:
        return jsonify({'success': False,
                        'error': 'Session is no longer running'}), 404
    if entry.get('state') != agent_state.STATE_PERMISSION:
        # The prompt was answered (or timed out) since the UI last refreshed.
        return jsonify({'success': False,
                        'error': 'That session is no longer waiting for approval'}), 409

    command = COMMANDS_BY_ID[commands[0] if decision == 'approve' else commands[1]]
    result = editor_base.send(command, cwd=entry.get('cwd') or None,
                              editor_label='Claude Code')
    if not result.get('success'):
        logger.info('Mission decide failed: %s', result.get('message'))
        return jsonify({'success': False,
                        'error': result.get('message') or 'Could not answer the prompt',
                        'details': result.get('details')}), 502
    logger.info('Mission control: %s %s session %s', decision, source, session_id)
    return jsonify({'success': True, 'decision': decision})


@agent_mission_bp.route('/api/agent-mission/prompt', methods=['POST'])
@require_auth
def prompt_session():
    """Type a preset (or custom text) into ONE ready session."""
    data, source, session_id = _body_target()
    preset = str(data.get('preset') or '')
    text = str(data.get('text') or '')
    if not preset and not text.strip():
        return jsonify({'success': False,
                        'error': 'preset or text is required'}), 400
    if preset and preset != 'custom' \
            and preset not in agent_prompt.PROMPT_PRESETS:
        return jsonify({'success': False,
                        'error': f'Unknown preset: {preset}'}), 400

    target = agent_prompt.resolve_target(source=source, session_id=session_id)
    if target is None:
        return jsonify({'success': False,
                        'error': 'Session is no longer running'}), 404

    rendered, error = agent_prompt.render_text(
        preset or 'custom', text, target.cwd)
    if rendered is None:
        return jsonify({'success': False, 'error': error}), 400

    result = agent_prompt.send_prompt(target, rendered)
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('message'),
                        'details': result.get('details')}), \
            result.get('status_code', 502)
    logger.info('Mission control: prompt %s -> %s session %s',
                preset or 'custom', source, session_id)
    return jsonify({'success': True})


@agent_mission_bp.route('/api/agent-mission/changes', methods=['GET'])
@require_auth
def session_changes():
    """Files the session changed this turn (git, per-turn baseline)."""
    source = agent_state.normalise_source(request.args.get('source'))
    session_id = agent_state.normalise_session_id(request.args.get('session_id'))
    entry = _find_entry(source, session_id)
    if entry is None:
        return jsonify({'success': False,
                        'error': 'Session is no longer running'}), 404
    return jsonify(turn_baseline.changes(source, session_id,
                                         entry.get('cwd') or ''))


@agent_mission_bp.route('/api/agent-mission/open-diff', methods=['POST'])
@require_auth
def open_session_diff():
    """Open one changed file's diff in the editor on the host PC."""
    data, source, session_id = _body_target()
    path = str(data.get('path') or '').strip()
    if not path:
        return jsonify({'success': False, 'error': 'path is required'}), 400
    entry = _find_entry(source, session_id)
    if entry is None:
        return jsonify({'success': False,
                        'error': 'Session is no longer running'}), 404
    result = turn_baseline.open_diff(source, session_id,
                                     entry.get('cwd') or '', path)
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('message'),
                        'details': result.get('details')}), \
            result.get('status_code', 502)
    return jsonify({'success': True, 'message': result.get('message')})

