"""
Layout-independent text typing.

Pressing the US key for each character (what ``pyautogui.typewrite`` does)
lets the target window's keyboard layout rewrite the text: under a Hebrew
layout "reply" arrives as Hebrew letters, and characters no US key produces
are dropped. On Windows each character is instead injected as a Unicode
keystroke, which arrives verbatim under any layout.
"""
import ctypes
import platform
import time
from dataclasses import dataclass
from typing import List

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
INPUT_KEYBOARD = 1
VK_RETURN = 0x0D
VK_TAB = 0x09

# Terminals and editors act on a real Enter/Tab key, not on a Unicode "\n".
VIRTUAL_KEY_BY_CHARACTER = {'\n': VK_RETURN, '\t': VK_TAB}
IGNORED_CHARACTERS = {'\r'}
DEFAULT_INTERVAL_SECONDS = 0.01


class TextInputError(RuntimeError):
    """Windows did not accept every injected keystroke."""


@dataclass(frozen=True)
class KeyEvent:
    """One keyboard event: a virtual key, or a UTF-16 code unit when
    ``virtual_key`` is 0."""
    virtual_key: int = 0
    unicode_unit: int = 0
    is_key_up: bool = False


def plan_keystrokes(text: str) -> List[List[KeyEvent]]:
    """Key events for ``text``, grouped per typed character."""
    keystroke_groups: List[List[KeyEvent]] = []
    for character in text.replace('\r\n', '\n'):
        if character in IGNORED_CHARACTERS:
            continue
        virtual_key = VIRTUAL_KEY_BY_CHARACTER.get(character)
        if virtual_key is not None:
            keystroke_groups.append([
                KeyEvent(virtual_key=virtual_key),
                KeyEvent(virtual_key=virtual_key, is_key_up=True),
            ])
            continue
        keystroke_groups.append(_unicode_events(character))
    return keystroke_groups


def _unicode_events(character: str) -> List[KeyEvent]:
    # Characters beyond the BMP (emoji) are two UTF-16 surrogate units,
    # each sent as its own down/up pair.
    encoded = character.encode('utf-16-le')
    code_units = [
        int.from_bytes(encoded[offset:offset + 2], 'little')
        for offset in range(0, len(encoded), 2)
    ]
    events: List[KeyEvent] = []
    for code_unit in code_units:
        events.append(KeyEvent(unicode_unit=code_unit))
        events.append(KeyEvent(unicode_unit=code_unit, is_key_up=True))
    return events


def type_text(text: str, interval_seconds: float = DEFAULT_INTERVAL_SECONDS) -> None:
    """Type ``text`` into the focused window exactly as written."""
    if platform.system() != 'Windows':
        import pyautogui
        pyautogui.typewrite(text, interval=interval_seconds)
        return

    for keystroke_group in plan_keystrokes(text):
        _send_key_events(keystroke_group)
        if interval_seconds:
            time.sleep(interval_seconds)


class _KeyboardInput(ctypes.Structure):
    _fields_ = [
        ('wVk', ctypes.c_uint16),
        ('wScan', ctypes.c_uint16),
        ('dwFlags', ctypes.c_uint32),
        ('time', ctypes.c_uint32),
        ('dwExtraInfo', ctypes.c_size_t),
    ]


class _MouseInput(ctypes.Structure):
    _fields_ = [
        ('dx', ctypes.c_int32),
        ('dy', ctypes.c_int32),
        ('mouseData', ctypes.c_uint32),
        ('dwFlags', ctypes.c_uint32),
        ('time', ctypes.c_uint32),
        ('dwExtraInfo', ctypes.c_size_t),
    ]


class _InputUnion(ctypes.Union):
    # SendInput validates cbSize against the full INPUT union, whose largest
    # member is MOUSEINPUT -- a keyboard-only union is rejected.
    _fields_ = [('ki', _KeyboardInput), ('mi', _MouseInput)]


class _Input(ctypes.Structure):
    _fields_ = [('type', ctypes.c_uint32), ('union', _InputUnion)]


def _to_windows_input(event: KeyEvent) -> _Input:
    flags = KEYEVENTF_KEYUP if event.is_key_up else 0
    if not event.virtual_key:
        flags |= KEYEVENTF_UNICODE
    keyboard_input = _KeyboardInput(
        wVk=event.virtual_key,
        wScan=event.unicode_unit,
        dwFlags=flags,
        time=0,
        dwExtraInfo=0,
    )
    return _Input(type=INPUT_KEYBOARD, union=_InputUnion(ki=keyboard_input))


def _send_key_events(events: List[KeyEvent]) -> None:
    input_array = (_Input * len(events))(*[_to_windows_input(event) for event in events])
    accepted_count = ctypes.windll.user32.SendInput(
        len(events), input_array, ctypes.sizeof(_Input))
    if accepted_count != len(events):
        raise TextInputError(
            f'Windows accepted {accepted_count} of {len(events)} keystrokes '
            '(the focused window may be running as administrator)')
