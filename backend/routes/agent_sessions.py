"""Agent session targeting (DL-071) — which live CLI session the deck drives.

Terminal-agent buttons (``cc_*``, ``devin_*``) type keystrokes into the window
hosting a live agent session. When several sessions run at once the resolver
ranks them (button cwd, focused editor's project, newest first) — silently.
These routes expose that list and let the UI pin one session as the explicit
deck target.
"""
import logging
import os
from typing import Optional

from flask import Blueprint, jsonify, request

from auth import require_auth
from integrations import agent_state, context, sessions
from integrations.keymaps import ALL_COMMANDS
from utils import window_focus

logger = logging.getLogger('vdock')

agent_sessions_bp = Blueprint('agent_sessions', __name__)

#: Only markers a shipped command actually scans for are legal ``source``
#: values — otherwise the param would let a client process-scan arbitrary
#: names.
_KNOWN_MARKERS = frozenset(
    cmd.session_marker for cmd in ALL_COMMANDS if cmd.session_marker
)


def _marker_from(raw) -> Optional[str]:
    marker = str(raw or '').lower().strip()
    return marker if marker in _KNOWN_MARKERS else None


def _norm_cwd(path: Optional[str]) -> str:
    if not path:
        return ''
    try:
        return os.path.normcase(os.path.normpath(str(path)))
    except (OSError, ValueError):
        return str(path)


def _hook_state_by_cwd(marker: str) -> dict:
    """cwd -> hook-reported session entry, for labelling picker rows.

    Works only when the user installed the agent hook (DL-064); sessions the
    hook never saw simply get ``state: None``.
    """
    by_cwd = {}
    for entry in agent_state.session_entries(marker):
        key = _norm_cwd(entry.get('cwd'))
        if key:
            by_cwd[key] = entry
    return by_cwd


def _resolved_pid(marker: str, hosts: list, pinned: Optional[int]) -> Optional[int]:
    """The pid a button press would target right now.

    Mirrors ``editor_base._resolve_session_host``: pin first, then the
    focused editor's project directory, then the resolver's ranking.
    """
    prefer_cwd = None
    try:
        prefer_cwd = context.current_editor().cwd
    except Exception:
        pass
    hwnd = window_focus.find_session_host_window(
        marker, prefer_cwd=prefer_cwd, prefer_pid=pinned,
    )
    if hwnd is None:
        return None
    for host in hosts:
        if host['hwnd'] == hwnd:
            return host['pid']
    return None


@agent_sessions_bp.route('/api/agent-sessions', methods=['GET'])
@require_auth
def list_agent_sessions():
    """Live sessions for ``source`` plus the pinned and effective target."""
    marker = _marker_from(request.args.get('source'))
    if marker is None:
        return jsonify({'success': False,
                        'error': 'Unknown or missing agent source'}), 400

    hosts = window_focus.list_session_hosts(marker)
    hook_by_cwd = _hook_state_by_cwd(marker)

    rows = []
    for host in hosts:
        hook = hook_by_cwd.get(_norm_cwd(host.get('cwd')))
        cwd = host.get('cwd')
        rows.append({
            'pid': host['pid'],
            'hwnd': host['hwnd'],
            'title': host['title'],
            'cwd': cwd,
            'project': (hook or {}).get('project')
                       or (os.path.basename(cwd) if cwd else ''),
            'state': (hook or {}).get('state'),
            # What the hook last saw this session do — the current task or
            # the last prompt. Pids don't identify a window to a human;
            # "fix the login bug" does.
            'detail': (hook or {}).get('message')
                      or (hook or {}).get('prompt')
                      or '',
            'started': host.get('create_time'),
        })

    pinned = sessions.pinned_pid(marker)
    return jsonify({
        'success': True,
        'sessions': rows,
        'pinned_pid': pinned,
        'resolved_pid': _resolved_pid(marker, hosts, pinned),
    })


@agent_sessions_bp.route('/api/agent-sessions/target', methods=['POST'])
@require_auth
def set_agent_target():
    """Pin ``{source, pid}`` as the deck target; ``pid: null`` clears it."""
    data = request.get_json(silent=True) or {}
    marker = _marker_from(data.get('source'))
    if marker is None:
        return jsonify({'success': False,
                        'error': 'Unknown or missing agent source'}), 400

    pid = data.get('pid')
    if pid is None:
        sessions.unpin_session(marker)
        return jsonify({'success': True, 'pinned_pid': None})

    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'pid must be an integer'}), 400

    if not sessions.pin_session(marker, pid):
        return jsonify({'success': False,
                        'error': 'No live session with that pid'}), 404
    return jsonify({'success': True, 'pinned_pid': pid})


@agent_sessions_bp.route('/api/agent-sessions/identify', methods=['POST'])
@require_auth
def identify_agent_session():
    """Flash ``{source, pid}``'s host window — "which terminal is this row".

    A pid means nothing to a human; a blinking titlebar/taskbar button is
    unambiguous. The deck fires this when a session is picked (and from the
    picker's per-row locate button) so the chosen CLI visibly waves back.
    """
    data = request.get_json(silent=True) or {}
    marker = _marker_from(data.get('source'))
    if marker is None:
        return jsonify({'success': False,
                        'error': 'Unknown or missing agent source'}), 400

    try:
        pid = int(data.get('pid'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'pid must be an integer'}), 400

    for host in window_focus.list_session_hosts(marker):
        if host['pid'] == pid:
            window_focus.flash_window(host['hwnd'])
            return jsonify({'success': True})
    return jsonify({'success': False,
                    'error': 'No live session with that pid'}), 404
