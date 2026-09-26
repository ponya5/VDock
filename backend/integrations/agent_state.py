"""Live agent state — what each coding agent is doing right now.

Fed by agent hooks (Claude Code, Cursor) through ``/api/agent-events``. The
dashboard reads it to offer the actions that fit the moment: Submit while an
agent waits for a prompt, Interrupt while it works, Approve/Deny while a
permission dialog is open.

State is tracked per session, then combined per agent source: several
sessions can run at once (an interactive CLI plus VDock's own headless
``claude -p`` jobs), and one of them ending must not wipe the others. A
pending permission prompt in any session wins — it is the one thing that
blocks until the user acts; otherwise the most recent event wins.

Pure state, no Flask: the route owns HTTP and broadcasting.
"""
import threading
import time
from typing import Any, Dict, List, Optional

STATE_READY = 'ready'
STATE_WORKING = 'working'
STATE_PERMISSION = 'permission'

ALLOWED_STATES = frozenset({STATE_READY, STATE_WORKING, STATE_PERMISSION})
ALLOWED_SOURCES = frozenset({'claude', 'cursor', 'devin', 'generic'})

#: Hooks that don't report a session id share this one.
DEFAULT_SESSION_ID = 'default'

#: A killed session never reports its end, so a state goes stale eventually.
STATE_TTL_SECONDS = 30 * 60

MAX_PROMPT_CHARS = 2000
MAX_REPLY_CHARS = 6000

_lock = threading.Lock()
_sessions_by_source: Dict[str, Dict[str, Dict[str, Any]]] = {}


def normalise_source(raw_source: Any) -> str:
    source = str(raw_source or 'generic')[:32]
    return source if source in ALLOWED_SOURCES else 'generic'


def normalise_session_id(raw_session_id: Any) -> str:
    return str(raw_session_id or DEFAULT_SESSION_ID)[:100]


def _conversation(previous_entry: Dict[str, Any], prompt: str, reply: str) -> Dict[str, str]:
    """The last prompt/reply pair after this event.

    Most events carry no text, so the pair carries over; a new prompt
    starts a new turn and clears the previous reply.
    """
    if prompt:
        return {'prompt': prompt[:MAX_PROMPT_CHARS], 'reply': reply[:MAX_REPLY_CHARS]}
    return {
        'prompt': previous_entry.get('prompt', ''),
        'reply': reply[:MAX_REPLY_CHARS] if reply else previous_entry.get('reply', ''),
    }


def record(source: str, state: str, message: str = '', cwd: str = '',
           project: str = '', session_id: str = DEFAULT_SESSION_ID,
           prompt: str = '', reply: str = '') -> Dict[str, Any]:
    """Store ``state`` for one session of ``source``; returns the entry."""
    if state not in ALLOWED_STATES:
        raise ValueError(f'Unknown agent state: {state}')
    with _lock:
        sessions = _sessions_by_source.setdefault(source, {})
        entry = {
            'source': source,
            'session_id': session_id,
            'state': state,
            'message': message[:300],
            'cwd': cwd[:300],
            'project': project[:120],
            **_conversation(sessions.get(session_id, {}), prompt, reply),
            'ts': time.time(),
        }
        sessions[session_id] = entry
    return entry


def end_session(source: str, session_id: str = DEFAULT_SESSION_ID) -> None:
    with _lock:
        sessions = _sessions_by_source.get(source)
        if not sessions:
            return
        sessions.pop(session_id, None)
        if not sessions:
            del _sessions_by_source[source]


def _is_expired(entry: Dict[str, Any], now: float) -> bool:
    return (now - entry.get('ts', 0)) > STATE_TTL_SECONDS


def _drop_expired(now: float) -> None:
    for source in list(_sessions_by_source):
        sessions = _sessions_by_source[source]
        for session_id in [sid for sid, entry in sessions.items() if _is_expired(entry, now)]:
            del sessions[session_id]
        if not sessions:
            del _sessions_by_source[source]


def _combined(sessions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    newest_first = sorted(sessions.values(), key=lambda entry: entry['ts'], reverse=True)
    waiting_on_permission = [entry for entry in newest_first if entry['state'] == STATE_PERMISSION]
    chosen = waiting_on_permission[0] if waiting_on_permission else newest_first[0]
    return {**chosen, 'session_count': len(sessions)}


def snapshot() -> Dict[str, Dict[str, Any]]:
    """One combined state per source with live sessions."""
    now = time.time()
    with _lock:
        _drop_expired(now)
        return {
            source: _combined(sessions)
            for source, sessions in _sessions_by_source.items()
        }


def get(source: str) -> Optional[Dict[str, Any]]:
    return snapshot().get(source)


def session_entries(source: str) -> List[Dict[str, Any]]:
    """The raw per-session entries for ``source`` (DL-071).

    ``snapshot()`` only exposes the combined per-source view; the session
    picker needs each session's own cwd/state to label the choices.
    """
    now = time.time()
    with _lock:
        _drop_expired(now)
        return [dict(e) for e in _sessions_by_source.get(source, {}).values()]


def reset() -> None:
    """Drop all states (tests)."""
    with _lock:
        _sessions_by_source.clear()
