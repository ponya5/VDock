"""Send a ready-made instruction to an agent session (DL-145 Phase 1).

One implementation shared by the ``agent_prompt`` deck action and Mission
Control's per-session Prompt menu. Typing goes through
``integrations.editor_base.send`` (verified target window); this module adds
what that layer cannot know - which *session* is meant and whether it is in a
state where typed text is safe.
"""
import dataclasses
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from integrations import agent_state, context, editor_base, sessions
from integrations.keymaps import ALL_PROFILES, COMMANDS_BY_ID

logger = logging.getLogger('vdock')

PROMPT_PRESETS: Dict[str, Dict[str, str]] = {
    'continue': {'label': 'Continue', 'text': 'continue'},
    'write_tests': {
        'label': 'Write tests',
        'text': 'Write tests for the code you just changed.'},
    'explain_error': {
        'label': 'Fix this error',
        'text': 'Explain this error and fix it:\n{clipboard}'},
    'fix_tests': {
        'label': 'Fix failing tests',
        'text': 'These tests are failing. Fix them:\n{last_failure}'},
    'review': {
        'label': 'Review your change',
        'text': 'Review your last change for bugs, edge cases and missing '
                'tests.'},
    'commit': {
        'label': 'Commit',
        'text': 'Commit the current changes with a clear conventional '
                'commit message.'},
}

MAX_PROMPT_CHARS = 1500

#: agent_state source -> keymap command that types a prompt into it.
PROMPT_SOURCES: Dict[str, str] = {
    p.status_source: p.prompt_command
    for p in ALL_PROFILES if p.status_source and p.prompt_command
}

_PROFILE_LABEL = {p.status_source: p.label for p in ALL_PROFILES
                  if p.status_source}

AGENT_CHOICES = ('auto',) + tuple(PROMPT_SOURCES)


@dataclass
class Target:
    source: str
    session_id: Optional[str]
    cwd: Optional[str]
    state: Optional[str]


def has_hooked_sessions() -> bool:
    return any(agent_state.session_entries(s) for s in PROMPT_SOURCES)


def _norm(path: str) -> str:
    return os.path.normcase(os.path.normpath(path))


def cwd_matches(entry_cwd: str, wanted: str) -> bool:
    if not entry_cwd:
        return False
    a, b = _norm(entry_cwd), _norm(wanted)
    return a == b or a.startswith(b + os.sep) or b.startswith(a + os.sep)


def _entry_target(entry: Dict[str, Any]) -> Target:
    return Target(source=entry['source'], session_id=entry.get('session_id'),
                  cwd=entry.get('cwd') or None, state=entry.get('state'))


def resolve_target(agent: str = 'auto', cwd: Optional[str] = None,
                   source: Optional[str] = None,
                   session_id: Optional[str] = None) -> Optional[Target]:
    """Which session a prompt goes to.

    Explicit ``source`` + ``session_id`` -> exactly that session (None when
    it is gone). Otherwise the best hooked session: a ``ready`` one first,
    newest first. No hooked sessions at all -> a legacy target that lets
    ``send`` resolve the focused project, as ``cc_prompt`` always did.
    """
    if source and session_id:
        if source not in PROMPT_SOURCES:
            return None
        for entry in agent_state.session_entries(source):
            if entry.get('session_id') == session_id:
                return _entry_target(entry)
        return None

    wanted = [agent] if agent in PROMPT_SOURCES else list(PROMPT_SOURCES)
    hooked: List[Dict[str, Any]] = []
    for src in wanted:
        hooked.extend(agent_state.session_entries(src))
    candidates = hooked
    if cwd:
        candidates = [e for e in hooked
                      if cwd_matches(e.get('cwd') or '', cwd)]

    if candidates:
        candidates.sort(key=lambda e: (e.get('state') != agent_state.STATE_READY,
                                       -(e.get('ts') or 0)))
        return _entry_target(candidates[0])

    if hooked:
        # Sessions exist but none match the button's directory: do not fall
        # back to typing somewhere else.
        return None
    legacy_source = agent if agent in PROMPT_SOURCES else 'claude'
    return Target(source=legacy_source, session_id=None, cwd=cwd, state=None)


def _truncate_payload(text: str) -> str:
    if len(text) <= MAX_PROMPT_CHARS:
        return text
    first, sep, rest = text.partition('\n')
    if not sep:
        return '…' + text[-(MAX_PROMPT_CHARS - 1):]
    keep = MAX_PROMPT_CHARS - len(first) - 2
    return f'{first}\n…{rest[-keep:]}' if keep > 0 else first[:MAX_PROMPT_CHARS]


def render_text(preset: str, custom_text: str,
                cwd: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """The text to type for a preset / custom prompt, or ``(None, why)``."""
    if preset == 'custom':
        template = (custom_text or '').strip()
        if not template:
            return None, 'Write the custom prompt first.'
    elif preset in PROMPT_PRESETS:
        template = PROMPT_PRESETS[preset]['text']
    else:
        return None, f'Unknown prompt: {preset}'

    if '{clipboard}' in template and not context.clipboard_text().strip():
        return None, 'Copy the error first - the clipboard is empty.'

    if '{last_failure}' in template:
        failure = ''
        try:
            from services import test_runner
            failure = test_runner.last_failure(context.focused_repo(cwd))
        except Exception as error:
            logger.debug('No last failure available: %s', error)
        if not failure.strip():
            return None, ('No failing test run yet - run tests from VDock '
                          'first, or use Fix this error with a copied error.')
        template = template.replace('{last_failure}', failure)

    text = context.expand_placeholders(template, cwd=cwd)
    return _truncate_payload(text), None


def _failure(status: int, message: str, details: str = '') -> Dict[str, Any]:
    return {'success': False, 'status_code': status, 'message': message,
            'details': details}


def _pinned_risk(target: Target) -> Optional[Dict[str, Any]]:
    """A pinned host window is targeted by ``send`` whatever the cwd says, so
    with several sessions of one agent the state we checked may belong to a
    different session than the window we type into. Refuse when any of them
    is blocked on an approval - typed text would answer it."""
    marker = PROMPT_SOURCES.get(target.source) and target.source
    if not marker or sessions.pinned_pid(marker) is None:
        return None
    entries = agent_state.session_entries(target.source)
    if len(entries) > 1 and any(
            e.get('state') == agent_state.STATE_PERMISSION for e in entries):
        return _failure(
            409, 'A session is waiting for approval - answer it first',
            'Several sessions run and one is pinned; VDock cannot be sure '
            'which one would receive the text.')
    return None


def check_typeable(target: Target) -> Optional[Dict[str, Any]]:
    """A failure when typing into ``target`` now would be unsafe, else None.

    Re-reads the session's state (what the caller saw may be seconds old):
    text typed during an approval prompt would answer it, and a busy agent
    would swallow it.
    """
    if target.session_id is None:
        return None
    fresh = next((e for e in agent_state.session_entries(target.source)
                  if e.get('session_id') == target.session_id), None)
    if fresh is None:
        return _failure(404, 'That session is no longer running')
    state = fresh.get('state')
    if state == agent_state.STATE_PERMISSION:
        return _failure(409, 'That session is waiting for approval - '
                             'answer it first')
    if state == agent_state.STATE_WORKING:
        return _failure(409, "That session is busy - try again when "
                             "it's ready")
    return _pinned_risk(target)


def editor_label(source: str) -> Optional[str]:
    """Product name used in ``send`` failure messages ('Claude Code')."""
    return _PROFILE_LABEL.get(source)


def send_prompt(target: Target, text: str, submit: bool = True) -> Dict[str, Any]:
    """Type ``text`` into ``target``'s session. Never into a blocked one."""
    blocked = check_typeable(target)
    if blocked:
        return blocked

    command_id = PROMPT_SOURCES.get(target.source)
    command = COMMANDS_BY_ID.get(command_id) if command_id else None
    if command is None:
        return _failure(400, f'{target.source} cannot receive prompts')
    if not submit:
        command = dataclasses.replace(command, submit=False)

    result = editor_base.send(
        command, text_override=text, cwd=target.cwd,
        editor_label=editor_label(target.source))
    if not result.get('success'):
        return _failure(502, result.get('message') or 'Could not send the prompt',
                        result.get('details') or '')
    return {'success': True, 'status_code': 200, 'message': 'Sent'}


def prompt_preset(preset: str, custom_text: str = '', agent: str = 'auto',
                  cwd: Optional[str] = None,
                  submit: bool = True) -> Dict[str, Any]:
    """Render a preset and send it to the best session (action-result dict)."""
    target = resolve_target(agent, cwd)
    if target is None:
        return {'success': False, 'message': 'No agent session is ready',
                'details': 'Start one, or pin a session in the action bar.'}

    text, error = render_text(preset, custom_text, target.cwd or cwd)
    if text is None:
        return {'success': False, 'message': error}

    sent = send_prompt(target, text, submit)
    if not sent['success']:
        return {'success': False, 'message': sent['message'],
                'details': sent.get('details', '')}

    label = PROMPT_PRESETS.get(preset, {}).get('label', 'Custom prompt')
    project = Path(target.cwd).name if target.cwd else ''
    return {'success': True,
            'message': f'{label} → {project}' if project else label}
