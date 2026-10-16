"""The OS this backend runs on, and the shortcut conventions that follow from it.

The backend is the machine that presses the keys, so its OS is the only
correct answer for "which modifier does a shortcut use". Detected live, never
stored: it cannot go stale when profiles move between machines (DL-006).
"""
import copy
import json
import platform
import re
from typing import Any, Dict, List, Sequence, Tuple


def host_os() -> str:
    """``macos`` | ``windows`` | ``linux``."""
    system = platform.system()
    if system == 'Darwin':
        return 'macos'
    if system == 'Windows':
        return 'windows'
    return 'linux'


def primary_modifier() -> str:
    """The modifier editors use for "command" shortcuts: ``cmd`` on macOS."""
    return 'cmd' if host_os() == 'macos' else 'ctrl'


def localize_keys(keys: Sequence[str]) -> Tuple[str, ...]:
    """A Windows-form chord as this OS expects it.

    On macOS Ctrl becomes Cmd, except backtick chords (VS Code's terminal
    toggle stays Ctrl) and Alt chords (their macOS equivalents differ per
    shortcut, so they are left as written). Anything else is untouched.
    """
    keys = tuple(keys)
    if host_os() != 'macos' or '`' in keys or 'alt' in keys:
        return keys
    return tuple('cmd' if key == 'ctrl' else key for key in keys)


_GLYPHS = {'shift': '⇧', 'alt': '⌥'}
_MODIFIER_LABELS = {'ctrl', 'shift', 'alt', 'cmd'}


def _localize_label(label: str, ctrl_became_cmd: bool) -> str:
    """"Ctrl+Shift+P" -> "⌘+⇧+P" (macOS). Non-chord text is returned as is."""
    parts = label.split('+')
    if len(parts) < 2 or parts[0].strip().lower() not in _MODIFIER_LABELS:
        return label
    out = []
    for part in parts:
        token = part.strip().lower()
        if token == 'ctrl':
            out.append('⌘' if ctrl_became_cmd else '⌃')
        elif token in _GLYPHS:
            out.append(_GLYPHS[token])
        else:
            out.append(part)
    return '+'.join(out)


def _localize_button(button: Dict[str, Any]) -> None:
    changed = False

    def walk(node: Any) -> None:
        nonlocal changed
        if isinstance(node, dict):
            keys = node.get('keys')
            if isinstance(keys, list) and all(isinstance(k, str) for k in keys):
                native = list(localize_keys(keys))
                if native != keys:
                    changed = True
                    node['keys'] = native
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(button.get('action'))
    label = button.get('secondary_label')
    if isinstance(label, str):
        button['secondary_label'] = _localize_label(label, changed)


_MAC_GLYPHS = {
    'cmd': '\u2318', 'ctrl': '\u2303', 'alt': '\u2325', 'shift': '\u21e7',
    'up': '\u2191', 'down': '\u2193', 'left': '\u2190', 'right': '\u2192',
}


def _mac_chord_label(keys: List[str]) -> str:
    return ''.join(_MAC_GLYPHS.get(k, k.upper()) for k in keys)


def _apply_explicit_mac_keys(button: Dict[str, Any]) -> bool:
    """Swap in a hotkey's ``mac_keys`` (an app's own macOS keymap, DL-009).

    JetBrains ships a separate macOS keymap (Go to File is Cmd+Shift+O, Run is
    Ctrl+R) that no Ctrl->Cmd rule can derive, so its template lists each
    macOS chord next to the Windows one. A macro can do the same per whole
    step list with ``mac_steps`` (Save All is Ctrl+K S on Windows but a single
    Cmd+Alt+S on macOS - DL-013). Returns whether anything changed.
    """
    action = button.get('action')
    config = action.get('config') if isinstance(action, dict) else None
    if not isinstance(config, dict):
        return False
    mac_steps = config.pop('mac_steps', None)
    if isinstance(mac_steps, list) and mac_steps:
        config['steps'] = mac_steps
        if isinstance(button.get('secondary_label'), str):
            button['secondary_label'] = ' '.join(
                _mac_chord_label(step['keys']) for step in mac_steps
                if isinstance(step, dict) and step.get('type') == 'hotkey'
                and isinstance(step.get('keys'), list))
        return True
    mac_keys = config.pop('mac_keys', None)
    if not (isinstance(mac_keys, list) and all(isinstance(k, str) for k in mac_keys)):
        return False
    config['keys'] = list(mac_keys)
    if isinstance(button.get('secondary_label'), str):
        button['secondary_label'] = _mac_chord_label(mac_keys)
    return True


def localize_template(template: Dict[str, Any]) -> Dict[str, Any]:
    """A copy of ``template`` with shortcuts rewritten for this OS.

    Only on macOS. A hotkey's explicit ``mac_keys`` always wins; otherwise only
    templates that declare ``"mac_modifier": "cmd"`` get the general rule
    (terminal decks opt out). Windows/Linux get the template untouched.
    """
    if host_os() != 'macos':
        return template
    general = template.get('mac_modifier') == 'cmd'
    has_explicit = '"mac_keys"' in json.dumps(template)
    if not general and not has_explicit:
        return template
    localized = copy.deepcopy(template)
    for page in localized.get('pages', []):
        for button in page.get('buttons', []):
            if not _apply_explicit_mac_keys(button) and general:
                _localize_button(button)
    return localized
