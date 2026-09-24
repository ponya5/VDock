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

#: Payload fields carrying the conversation, per (source, event).
PROMPT_EVENTS = {('claude', 'UserPromptSubmit'), ('cursor', 'beforeSubmitPrompt')}
CURSOR_REPLY_EVENT = 'afterAgentResponse'
CLAUDE_REPLY_EVENT = 'Stop'

MAX_PROMPT_CHARS = 2000
MAX_REPLY_CHARS = 6000
#: The final assistant message sits at the end of the transcript; reading
#: the tail keeps a long session's hook fast.
TRANSCRIPT_TAIL_BYTES = 512 * 1024

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


def _assistant_text(transcript_entry: Dict[str, Any]) -> str:
    if transcript_entry.get('type') != 'assistant':
        return ''
    message = transcript_entry.get('message') or {}
    content = message.get('content') if isinstance(message, dict) else None
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ''
    text_parts = [
        str(part.get('text') or '')
        for part in content
        if isinstance(part, dict) and part.get('type') == 'text'
    ]
    return '\n'.join(text_parts).strip()


def _read_transcript_tail(transcript_path: str) -> str:
    try:
        with open(transcript_path, 'rb') as transcript_file:
            transcript_file.seek(0, 2)
            file_size = transcript_file.tell()
            transcript_file.seek(max(0, file_size - TRANSCRIPT_TAIL_BYTES))
            return transcript_file.read().decode('utf-8', errors='replace')
    except OSError:
        return ''


def last_assistant_reply(transcript_path: str) -> str:
    """Text of the newest assistant message in a Claude Code transcript."""
    if not transcript_path:
        return ''
    for line in reversed(_read_transcript_tail(transcript_path).splitlines()):
        try:
            transcript_entry = json.loads(line)
        except ValueError:
            # The first line of a tail read is usually cut mid-entry.
            continue
        if not isinstance(transcript_entry, dict):
            continue
        reply_text = _assistant_text(transcript_entry)
        if reply_text:
            return reply_text
    return ''


def _reply_text(source: str, event_name: str, payload: Dict[str, Any]) -> str:
    if source == 'cursor':
        return str(payload.get('text') or '') if event_name == CURSOR_REPLY_EVENT else ''
    if event_name != CLAUDE_REPLY_EVENT:
        return ''
    reported_reply = str(payload.get('last_assistant_message') or '')
    if reported_reply:
        return reported_reply
    return last_assistant_reply(str(payload.get('transcript_path') or ''))


def conversation_fields(source: str, payload: Dict[str, Any]) -> Dict[str, str]:
    """The prompt or reply an event carries, for the mobile console."""
    event_name = str(payload.get('hook_event_name') or '')
    fields: Dict[str, str] = {}
    if (source, event_name) in PROMPT_EVENTS:
        prompt_text = str(payload.get('prompt') or '').strip()
        if prompt_text:
            fields['prompt'] = prompt_text[:MAX_PROMPT_CHARS]
    reply_text = _reply_text(source, event_name, payload).strip()
    if len(reply_text) > MAX_REPLY_CHARS:
        # A long reply ends with its summary, which is what a phone needs.
        reply_text = '…' + reply_text[-(MAX_REPLY_CHARS - 1):]
    if reply_text:
        fields['reply'] = reply_text
    return fields


def build_body(source: str, state: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    cwd = _session_cwd(payload)
    return {
        **conversation_fields(source, payload),
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
