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

Codex (``~/.codex/hooks.json``) sends the same event names as Claude Code,
plus ``Interrupt`` (the user stopped the turn -> ready); older installs used
its single ``notify`` command, which still works.

Usage: python vdock_agent_hook.py [--port 5000] [--source claude|cursor]

Stdlib only, silent by design: a hook must never block or break the agent,
so every failure exits 0 — and Cursor's beforeSubmitPrompt always gets its
required ``{"continue": true}`` reply.
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from typing import Any, Dict, Optional, Tuple

POST_TIMEOUT_SECONDS = 1.5

#: Every hook is its own process, so two events fired a few ms apart can
#: reach the backend in the wrong order. The start time of *this* process
#: orders them (DL-012).
STARTED_AT = time.time()

CLAUDE_STATE_BY_EVENT = {
    'SessionStart': 'ready',
    'Stop': 'ready',
    # A turn ended by an API error never fires Stop (DL-009).
    'StopFailure': 'ready',
    # Fires the moment a permission decision is needed; the permission
    # Notification only follows after a delay, mostly when you're away.
    'PermissionRequest': 'permission',
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

# Antigravity's stdin payload doesn't name the event — the installed
# command pins it via --event. PostInvocation is still mid-loop (tool
# calls follow), so only Stop means the agent went quiet.
AGY_STATE_BY_EVENT = {
    'PreInvocation': 'working',
    'PreToolUse': 'working',
    'PostToolUse': 'working',
    'PostInvocation': 'working',
    'Stop': 'ready',
}

# Codex hooks (``~/.codex/hooks.json``, DL-012) mirror Claude Code's events and
# pipe the payload on stdin. Compaction and subagent events say nothing
# about the main turn. The legacy ``notify`` command (older installs) passes
# its JSON as the last argv entry instead, with ``type`` naming the event;
# only the turn-complete event means "waiting for you".
CODEX_STATE_BY_EVENT = {
    'SessionStart': 'ready',
    'UserPromptSubmit': 'working',
    'PreToolUse': 'working',
    'PostToolUse': 'working',
    'PermissionRequest': 'permission',
    'Stop': 'ready',
    'Interrupt': 'ready',
    'SessionEnd': 'ended',
    'agent-turn-complete': 'ready',
}

#: Cursor events whose hooks must answer on stdout.
CURSOR_REPLY_BY_EVENT = {
    'beforeSubmitPrompt': {'continue': True},
}

#: Payload fields carrying the conversation, per (source, event).
PROMPT_EVENTS = {('claude', 'UserPromptSubmit'), ('cursor', 'beforeSubmitPrompt'),
                 ('codex', 'UserPromptSubmit'), ('codex', 'agent-turn-complete')}
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


#: Claude Code notification types (hooks reference) that need the user, or
#: that mean the session is idle. Anything else (auth_success, quota_*...)
#: says nothing about the session's state and must not flip it.
CLAUDE_NEEDS_YOU_NOTIFICATIONS = frozenset({
    'permission_prompt', 'elicitation_dialog', 'elicitation_url_dialog',
    'agent_needs_input',
})
CLAUDE_IDLE_NOTIFICATIONS = frozenset({'idle_prompt', 'agent_completed'})


def _claude_notification_state(payload: Dict[str, Any]) -> Optional[str]:
    notification_type = str(payload.get('notification_type') or '')
    if notification_type:
        if notification_type in CLAUDE_NEEDS_YOU_NOTIFICATIONS:
            return 'permission'
        return 'ready' if notification_type in CLAUDE_IDLE_NOTIFICATIONS else None
    message = str(payload.get('message') or '').lower()
    return 'permission' if 'permission' in message else 'ready'


def map_event(source: str, payload: Dict[str, Any]) -> Optional[str]:
    """The agent state an event implies, or None for unrelated events."""
    event_name = str(payload.get('hook_event_name') or payload.get('event') or '')
    if source == 'cursor':
        return CURSOR_STATE_BY_EVENT.get(event_name)
    if source == 'antigravity':
        # A Stop that is not "fully idle" still has background work that can
        # re-enter the loop - the agent is not waiting for the user yet.
        if event_name == 'Stop' and payload.get('fullyIdle') is False:
            return 'working'
        return AGY_STATE_BY_EVENT.get(event_name)
    if source == 'codex':
        return CODEX_STATE_BY_EVENT.get(event_name)
    if event_name == 'Notification':
        return _claude_notification_state(payload)
    return CLAUDE_STATE_BY_EVENT.get(event_name)


def _session_cwd(payload: Dict[str, Any]) -> str:
    cwd = payload.get('cwd')
    if cwd:
        return str(cwd)
    # Cursor: workspace_roots; Antigravity: workspacePaths (camelCase).
    workspace_roots = payload.get('workspace_roots') or payload.get('workspacePaths') or []
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
    if event_name not in (CLAUDE_REPLY_EVENT, 'agent-turn-complete'):
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


def _short(text: Any, limit: int = 160) -> str:
    flat = ' '.join(str(text or '').split())
    return flat if len(flat) <= limit else flat[:limit - 1] + '\u2026'


def permission_detail(payload: Dict[str, Any]) -> str:
    """What a PermissionRequest is about, in words a phone user can judge
    before tapping Approve (DL-011): "Run: git push", "Edit app.py"..."""
    tool = str(payload.get('tool_name') or '')
    tool_input = payload.get('tool_input')
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    path = str(tool_input.get('file_path') or tool_input.get('notebook_path') or '')
    name = path.replace('\\', '/').rstrip('/').rsplit('/', 1)[-1]
    if tool == 'Bash' and tool_input.get('command'):
        return 'Run: ' + _short(tool_input['command'])
    if tool in ('Edit', 'MultiEdit', 'NotebookEdit') and name:
        return f'Edit {name}'
    if tool == 'Write' and name:
        return f'Write {name}'
    if tool == 'apply_patch':  # Codex: tool_input.command is the whole patch
        return 'Edit files'
    if tool == 'WebFetch' and tool_input.get('url'):
        return 'Open ' + _short(tool_input['url'], 120)
    if tool == 'WebSearch' and tool_input.get('query'):
        return 'Search the web: ' + _short(tool_input['query'], 120)
    return f'Use {tool}' if tool else ''


def build_body(source: str, state: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    cwd = _session_cwd(payload)
    event_name = str(payload.get('hook_event_name') or payload.get('event') or '')
    detail = permission_detail(payload) if event_name == 'PermissionRequest' else ''
    return {
        **conversation_fields(source, payload),
        'source': source,
        'state': state,
        # Ordering + identity for the backend (DL-012): when this hook began,
        # which turn it belongs to, and the process that launched it - the
        # backend walks up from there to the agent's own pid.
        'event_ts': STARTED_AT,
        'turn_id': str(payload.get('generation_id') or payload.get('turn_id') or ''),
        'hook_pid': os.getppid(),
        # Cursor reports each assistant message mid-run; after the turn's
        # `stop` it carries a reply only and must not reopen the turn.
        'passive': event_name == CURSOR_REPLY_EVENT,
        # Every event except SessionStart/Notification implies the user
        # already prompted this session (tool calls, submits, a finished
        # turn) — Cursor and Antigravity events only exist mid-run at
        # all. Waiting alerts fire only for prompted sessions (DL-105).
        'prompted': event_name not in ('SessionStart', 'Notification'),
        # Only a notification means "come back to the agent" — a normal
        # Stop is ready too, but shouldn't pop the alert every turn.
        'attention': event_name in ('Notification', 'PermissionRequest'),
        # The later permission Notification only says "...to use Bash"; the
        # backend keeps this specific text for the same pending request.
        'detailed': bool(detail),
        # Claude Code / Codex: session_id; Cursor: conversation_id;
        # Antigravity: conversationId.
        'session_id': (payload.get('session_id') or payload.get('conversation_id')
                       or payload.get('conversationId') or ''),
        'message': detail or payload.get('message') or DEFAULT_MESSAGES[state],
        'cwd': cwd,
        'project': cwd.replace('\\', '/').rstrip('/').rsplit('/', 1)[-1],
    }


def _read_payload() -> Dict[str, Any]:
    try:
        if sys.stdin is None or sys.stdin.isatty():
            return {}  # run by hand / no piped payload: never wait on a keyboard
        raw = sys.stdin.read()
        loaded = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _normalise_codex(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Map Codex's notify payload onto the fields the other agents use."""
    messages = payload.get('input-messages') or []
    return {
        **payload,
        'hook_event_name': str(payload.get('type') or ''),
        'session_id': payload.get('thread-id') or payload.get('session_id') or '',
        'prompt': str(messages[-1]) if messages else '',
        'last_assistant_message': payload.get('last-assistant-message') or '',
    }


def _codex_payload(unknown_args: list) -> Dict[str, Any]:
    for candidate in reversed(unknown_args):
        try:
            loaded = json.loads(candidate)
        except (ValueError, TypeError):
            continue
        if isinstance(loaded, dict):
            return _normalise_codex(loaded)
    return {}


def _post(port: int, body: Dict[str, Any]) -> None:
    request = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/agent-events',
        data=json.dumps(body).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        urllib.request.urlopen(request, timeout=POST_TIMEOUT_SECONDS)
        return
    except (OSError, ValueError):
        pass  # VDock not running or busy — the agent must not notice.
    # With HTTPS on, VDock's one port speaks only TLS (DL-009). Its own
    # self-signed certificate, on this machine - nothing to verify.
    import ssl
    secure = urllib.request.Request(
        request.full_url.replace('http://', 'https://', 1), data=request.data,
        headers=dict(request.header_items()), method='POST')
    try:
        urllib.request.urlopen(secure, timeout=POST_TIMEOUT_SECONDS,
                               context=ssl._create_unverified_context())
    except (OSError, ValueError):
        pass


def _parse_args() -> Tuple[int, str, str, list]:
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--source', default='claude')
    # Agents whose stdin payload doesn't name the event (Antigravity) pin
    # it in the installed command instead.
    parser.add_argument('--event', default='')
    args, _unknown = parser.parse_known_args()
    return args.port, args.source, args.event, _unknown


def main() -> int:
    port, source, pinned_event, extra_args = _parse_args()
    # Legacy Codex ``notify`` passes its payload as the last argv entry;
    # Codex hooks and every other agent pipe it on stdin.
    payload = (_codex_payload(extra_args) if source == 'codex' else {}) or _read_payload()
    if pinned_event:
        payload.setdefault('hook_event_name', pinned_event)
        payload['event'] = pinned_event
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
