"""Layout-independent typing (DL-064 follow-up)."""
import sys
from unittest.mock import MagicMock, patch

import pytest

from actions.macro_action import MacroAction
from utils import text_input
from utils.text_input import KeyEvent, TextInputError, VK_RETURN, VK_TAB, plan_keystrokes


def _typed_units(keystroke_groups):
    return [
        event.unicode_unit
        for group in keystroke_groups
        for event in group
        if not event.virtual_key and not event.is_key_up
    ]


def test_letters_are_sent_as_unicode_so_the_layout_cannot_rewrite_them():
    keystroke_groups = plan_keystrokes('reply')

    assert len(keystroke_groups) == 5
    assert all(event.virtual_key == 0 for group in keystroke_groups for event in group)
    assert _typed_units(keystroke_groups) == [ord(character) for character in 'reply']


def test_each_character_is_a_key_down_then_key_up():
    assert plan_keystrokes('a') == [[
        KeyEvent(unicode_unit=ord('a')),
        KeyEvent(unicode_unit=ord('a'), is_key_up=True),
    ]]


def test_hebrew_text_is_typed_instead_of_dropped():
    assert _typed_units(plan_keystrokes('שלום')) == [ord(character) for character in 'שלום']


def test_emoji_is_sent_as_a_surrogate_pair():
    keystroke_groups = plan_keystrokes('🙂')

    assert len(keystroke_groups) == 1
    assert _typed_units(keystroke_groups) == [0xD83D, 0xDE42]


def test_newline_and_tab_are_real_keys_and_carriage_return_is_dropped():
    keystroke_groups = plan_keystrokes('a\r\nb\tc\r')

    virtual_keys = [group[0].virtual_key for group in keystroke_groups]
    assert virtual_keys == [0, VK_RETURN, 0, VK_TAB, 0]


def test_windows_path_sends_every_group(monkeypatch):
    sent_groups = []
    monkeypatch.setattr(text_input.platform, 'system', lambda: 'Windows')
    monkeypatch.setattr(text_input, '_send_key_events', sent_groups.append)

    text_input.type_text('hi', interval_seconds=0)

    assert sent_groups == plan_keystrokes('hi')


def test_partially_accepted_send_raises(monkeypatch):
    class _RefusingUser32:
        @staticmethod
        def SendInput(count, inputs, size):
            return 0

    class _FakeWindll:
        user32 = _RefusingUser32()

    monkeypatch.setattr(text_input.ctypes, 'windll', _FakeWindll(), raising=False)

    with pytest.raises(TextInputError):
        text_input._send_key_events(plan_keystrokes('a')[0])


def test_non_windows_falls_back_to_pyautogui(monkeypatch):
    fake_pyautogui = MagicMock()
    monkeypatch.setitem(sys.modules, 'pyautogui', fake_pyautogui)
    monkeypatch.setattr(text_input.platform, 'system', lambda: 'Linux')

    text_input.type_text('hello', interval_seconds=0)

    fake_pyautogui.typewrite.assert_called_once_with('hello', interval=0)


def test_macro_text_step_uses_layout_independent_typing():
    with patch('actions.macro_action.type_text') as typing_function:
        result = MacroAction({'steps': [{'type': 'text', 'text': 'continue'}]}).execute()

    assert result.success
    typing_function.assert_called_once_with('continue')


def test_macro_reports_a_refused_send_as_failure():
    with patch('actions.macro_action.type_text', side_effect=TextInputError('blocked')):
        result = MacroAction({'steps': [{'type': 'text', 'text': 'continue'}]}).execute()

    assert not result.success
