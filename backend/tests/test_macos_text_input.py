"""macOS text typing: Unicode via Quartz, refused without Accessibility."""
import sys
import types
from unittest.mock import patch

import pytest

from utils import text_input


def _fake_quartz(posted):
    q = types.SimpleNamespace(kCGHIDEventTap=0)
    q.CGEventCreateKeyboardEvent = lambda src, code, down: {'code': code, 'down': down, 'text': None}
    q.CGEventKeyboardSetUnicodeString = lambda ev, n, s: ev.update(text=s, n=n)
    q.CGEventPost = lambda tap, ev: posted.append(ev)
    return q


def test_refuses_without_accessibility():
    with patch.object(text_input.platform, 'system', return_value='Darwin'), \
            patch('actions.macos_controls.is_accessibility_trusted', return_value=False):
        with pytest.raises(text_input.TextInputError):
            text_input.type_text('hi')


def test_types_unicode_and_real_return_key():
    posted = []
    with patch.object(text_input.platform, 'system', return_value='Darwin'), \
            patch('actions.macos_controls.is_accessibility_trusted', return_value=True), \
            patch.dict(sys.modules, {'Quartz': _fake_quartz(posted)}):
        text_input.type_text('שa\n😀', interval_seconds=0)
    downs = [e for e in posted if e['down']]
    assert [e['text'] for e in downs] == ['ש', 'a', None, '😀']
    assert downs[2]['code'] == 36          # Return is a real key, not "\n"
    assert downs[3]['n'] == 2              # emoji = two UTF-16 units
    assert len(posted) == 8                # every key has a down and an up


def test_macro_text_step_reports_failure_when_blocked():
    from actions.macro_action import MacroAction
    with patch.object(text_input.platform, 'system', return_value='Darwin'), \
            patch('actions.macos_controls.is_accessibility_trusted', return_value=False):
        result = MacroAction({'steps': []})._execute_text({'text': 'x'})
    assert not result.success
