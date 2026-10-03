"""Hold-to-talk dictation into an agent session (DL-145 Phase 5).

Holding the deck button opens Windows voice typing (Win+H) in the agent's
terminal or chat; letting go closes it. The spoken text lands in the
session's input box and is never submitted - the user reads it and taps
Submit. Nothing here can press Enter: the command carries no text, no
``submit`` and only the voice-typing chord.

Keystrokes go through ``integrations.editor_base.send`` like every other
agent action, so the specific session window is resolved, focused and
verified, and a dead session is refused. Release is honoured only after a
start of ours (a stray release would otherwise *open* the panel, because
Win+H toggles).
"""
import dataclasses
import logging
import platform
import threading
from typing import Any, Dict, Optional

from integrations import editor_base
from integrations.keymaps import COMMANDS_BY_ID, RISK_INPUT
from services import agent_prompt

logger = logging.getLogger('vdock')

VOICE_TYPING_KEYS = ('win', 'h')

ENABLE_HINT = ('Turn on voice typing in Settings > Time & language > Typing '
               '(or press Win+H once in any text box to set it up).')

_PRIVACY_KEY = (r'Software\Microsoft\Speech_OneCore\Settings'
                r'\OnlineSpeechPrivacy')

# Held across a whole start/stop so a release that arrives while the start is
# still focusing the window waits for it instead of racing it.
_lock = threading.Lock()
_listening: Optional[agent_prompt.Target] = None
_hint_shown = False


def _failure(message: str, details: str = '') -> Dict[str, Any]:
    return {'success': False, 'message': message, 'details': details}


def voice_typing_platform_blocker() -> Optional[str]:
    """Static reason voice typing cannot exist here (not Windows), or None."""
    if platform.system() != 'Windows':
        return 'Voice typing is only available on Windows 10 and 11'
    return None


def voice_typing_blocker() -> Optional[str]:
    """Why voice typing cannot work on this PC right now, or None."""
    platform_reason = voice_typing_platform_blocker()
    if platform_reason:
        return platform_reason
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _PRIVACY_KEY) as key:
            accepted, _ = winreg.QueryValueEx(key, 'HasAccepted')
    except OSError:
        return None  # never configured: Windows asks on first use
    if accepted == 0:
        return ('Online speech recognition is off - turn it on in Settings > '
                'Privacy & security > Speech. ' + ENABLE_HINT)
    return None


def _command(source: str, focus_input: bool):
    """The keymap-free dictate command for ``source``'s prompt target.

    Inherits the prompt command's window rules (terminal exes, title hint,
    session marker). ``focus_input`` first presses its focus chord (Cursor's
    chat box) so the text has somewhere to land.
    """
    base = COMMANDS_BY_ID.get(agent_prompt.PROMPT_SOURCES.get(source, ''))
    if base is None:
        return None
    chord = bool(focus_input and base.keys)
    return dataclasses.replace(
        base, id='dictate', label='Dictate', types_text=None, submit=False,
        repeat=1, newline_keys=(), risk=RISK_INPUT,
        keys=base.keys if chord else VOICE_TYPING_KEYS,
        after_keys=(VOICE_TYPING_KEYS,) if chord else ())


def start(agent: str = 'auto', cwd: Optional[str] = None) -> Dict[str, Any]:
    """Open voice typing in the best ready session."""
    global _listening, _hint_shown
    blocker = voice_typing_blocker()
    if blocker:
        return _failure(blocker)

    target = agent_prompt.resolve_target(agent, cwd)
    if target is None:
        return _failure('No agent session is ready',
                        'Start one, or pin a session in the action bar.')
    blocked = agent_prompt.check_typeable(target)
    if blocked:
        return _failure(blocked['message'], blocked.get('details', ''))
    command = _command(target.source, focus_input=True)
    if command is None:
        return _failure(f'{target.source} cannot receive dictation')

    with _lock:
        if _listening is not None:
            # A release was missed; the panel is already open. Releasing this
            # press closes it.
            return {'success': True, 'message': 'Already listening - '
                                                'release to stop'}
        sent = editor_base.send(
            command, cwd=target.cwd,
            editor_label=agent_prompt.editor_label(target.source))
        if not sent.get('success'):
            return _failure(sent.get('message') or 'Could not start voice typing',
                            sent.get('details') or '')
        _listening = target

    message = 'Listening - release to stop'
    if not _hint_shown:
        _hint_shown = True
        message += f'. No panel? {ENABLE_HINT}'
    return {'success': True, 'message': message}


def stop() -> Dict[str, Any]:
    """Close the voice typing panel this module opened, if any."""
    global _listening
    with _lock:
        target = _listening
        if target is None:
            return {'success': True, 'message': 'Not listening'}
        _listening = None
        command = _command(target.source, focus_input=False)
        sent = editor_base.send(
            command, cwd=target.cwd,
            editor_label=agent_prompt.editor_label(target.source))
    if not sent.get('success'):
        return _failure(
            sent.get('message') or 'Could not stop voice typing',
            'Press Win+H in the agent window to close it. '
            + (sent.get('details') or ''))
    return {'success': True, 'message': 'Stopped - tap Submit to send'}


def dictate(op: str, agent: str = 'auto',
            cwd: Optional[str] = None) -> Dict[str, Any]:
    """Dispatch a hold-button ``op``; anything but start/stop is refused."""
    if op == 'start':
        return start(agent, cwd)
    if op == 'stop':
        return stop()
    return _failure('Hold the button to talk',
                    'Press and hold, speak, then let go.')
