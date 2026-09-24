#!/usr/bin/env python3
"""VDock agent hook — reports a coding agent's state to the local backend.

Claude Code and Cursor pipe a JSON payload to this script's stdin
(``hook_event_name``, ``message``, ``cwd`` / ``workspace_roots`` ...). The
event is mapped to an agent state and POSTed to VDock, which lights up the
actions that fit: Submit while the agent waits for a prompt, Interrupt while
it works, Approve/Deny while a permission dialog is open.

  Claude Code                                    Cursor
  SessionStart, Stop           -> ready          stop                -> ready
  UserPromptSubmit, Pre/PostToolUse -> working   beforeSubmitPrompt,
  Notification (permission)    -> permission     afterAgentResponse  -> working
  Notification (idle)          -> ready
  SessionEnd                   -> ended

Usage: python vdock_agent_hook.py [--port 5000] [--source claude|cursor]

Stdlib only, silent by design: a hook must never block or break the agent,
so every failure exits 0 — and Cursor's beforeSubmitPrompt always gets its
required ``{"continue": true}`` reply.
"""
import argparse
import json
import sys
import urllib.request
from typing import Any, Dict, Optional, Tuple

POST_TIMEOUT_SECONDS = 1.5

CLAUDE_STATE_BY_EVENT = {
    'SessionStart': 'ready',
    'Stop': 'ready',
    'UserPromptSubmit': 'working',
    'PreToolUse': 'working',
    'PostToolUse': 'working',
    'SessionEnd': 'ended',
}

CURSOR_STATE_BY_EVENT = {
    'stop': 'ready',
    'beforeSubmitPrompt': 'working',
    'afterAgentResponse': 'working',
}

#: Cursor events whose hooks must answer on stdout.
CURSOR_REPLY_BY_EVENT = {
    'beforeSubmitPrompt': {'continue': True},
}

DEFAULT_MESSAGES = {
    'ready': 'Waiting for your prompt',
    'working': 'Working…',
    'permission': 'Needs your permission',
    'ended': 'Session ended',
}


def _claude_notification_state(payload: Dict[str, Any]) -> str:
    notification_type = str(payload.get('notification_type') or '')
    if notification_type:
        return 'permission' if 'permission' in notification_type else 'ready'
    message = str(payload.get('message') or '').lower()
    return 'permission' if 'permission' in message else 'ready'


def map_event(source: str, payload: Dict[str, Any]) -> Optional[str]:
    """The agent state an event implies, or None for unrelated events."""
    event_name = str(payload.get('hook_event_name') or '')
    if source == 'cursor':
        return CURSOR_STATE_BY_EVENT.get(event_name)
    if event_name == 'Notification':
        return _claude_notification_state(payload)
    return CLAUDE_STATE_BY_EVENT.get(event_name)


def _session_cwd(payload: Dict[str, Any]) -> str:
    cwd = payload.get('cwd')
    if cwd:
        return str(cwd)
    workspace_roots = payload.get('workspace_roots') or []
    return str(workspace_roots[0]) if workspace_roots else ''


def build_body(source: str, state: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    cwd = _session_cwd(payload)
    return {
        'source': source,
        'state': state,
        # Only a notification means "come back to the agent" — a normal
        # Stop is ready too, but shouldn't pop the alert every turn.
        'attention': payload.get('hook_event_name') == 'Notification',
        # Claude Code: session_id; Cursor: conversation_id.
        'session_id': payload.get('session_id') or payload.get('conversation_id') or '',
        'message': payload.get('message') or DEFAULT_MESSAGES[state],
        'cwd': cwd,
        'project': cwd.replace('\\', '/').rstrip('/').rsplit('/', 1)[-1],
    }


def _read_payload() -> Dict[str, Any]:
    try:
        raw = sys.stdin.read()
        loaded = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _post(port: int, body: Dict[str, Any]) -> None:
    request = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/agent-events',
        data=json.dumps(body).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        urllib.request.urlopen(request, timeout=POST_TIMEOUT_SECONDS)
    except (OSError, ValueError):
        pass  # VDock not running or busy — the agent must not notice.


def _parse_args() -> Tuple[int, str]:
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--source', default='claude')
    args, _unknown = parser.parse_known_args()
    return args.port, args.source


def main() -> int:
    port, source = _parse_args()
    payload = _read_payload()
    event_name = str(payload.get('hook_event_name') or '')

    if source == 'cursor' and event_name in CURSOR_REPLY_BY_EVENT:
        print(json.dumps(CURSOR_REPLY_BY_EVENT[event_name]), flush=True)

    state = map_event(source, payload)
    if state is None:
        return 0
    _post(port, build_body(source, state, payload))
    return 0


if __name__ == '__main__':
    # BaseException: argparse exits non-zero on bad flags, and a hook must
    # never fail the agent.
    try:
        main()
    except BaseException:  # noqa: BLE001
        pass
    sys.exit(0)
