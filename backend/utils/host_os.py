"""The OS this backend runs on, and the shortcut conventions that follow from it.

The backend is the machine that presses the keys, so its OS is the only
correct answer for "which modifier does a shortcut use". Detected live, never
stored: it cannot go stale when profiles move between machines (DL-006).
"""
import copy
import platform
import re
from typing import Any, Dict, Sequence, Tuple


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


def localize_template(template: Dict[str, Any]) -> Dict[str, Any]:
    """A copy of ``template`` with shortcuts rewritten for this OS.

    Only templates that declare ``"mac_modifier": "cmd"`` are touched, and
    only on macOS: JetBrains (separate mac keymap) and terminal decks opt out.
    """
    if host_os() != 'macos' or template.get('mac_modifier') != 'cmd':
        return template
    localized = copy.deepcopy(template)
    for page in localized.get('pages', []):
        for button in page.get('buttons', []):
            _localize_button(button)
    return localized
