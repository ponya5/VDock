"""Regression tests for MacroAction's hotkey and clipboard steps.

Feature: ai-dev-integration-packs, Property 0.1: macro hotkey steps reach the
keyboard.

MacroAction used to hand HotkeyAction a config of {'combo': 'ctrl+c'}, but
HotkeyAction.validate() only accepts 'keys' (list) or 'hotkey' (string). Every
hotkey, clipboard_copy and clipboard_paste step therefore failed validation --
and MacroAction.execute() reported success anyway, so the failure was silent.

These tests mock pynput's Controller, so no real keystrokes are ever sent.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from actions.hotkey_action import HotkeyAction  # noqa: E402
from actions.macro_action import MacroAction  # noqa: E402


@pytest.fixture
def keyboard(mocker):
    """Replace pynput's Controller so tests never touch the real keyboard."""
    controller_cls = mocker.patch('actions.hotkey_action.Controller')
    mocker.patch('actions.hotkey_action.PYNPUT_AVAILABLE', True)
    return controller_cls.return_value


def test_hotkey_action_accepts_the_config_macro_builds(keyboard):
    """The exact contract MacroAction relies on: 'keys' is a valid config."""
    assert HotkeyAction({'keys': ['ctrl', 'c']}).validate() is True


def test_hotkey_action_rejects_the_old_combo_config(keyboard):
    """Guards the original defect: 'combo' was never a supported key."""
    assert HotkeyAction({'combo': 'ctrl+c'}).validate() is False


def test_macro_hotkey_step_presses_and_releases_keys(keyboard):
    result = MacroAction({'steps': [{'type': 'hotkey', 'keys': ['ctrl', 'l']}]}).execute()

    assert result.success is True, result.message
    assert keyboard.press.call_count == 2
    assert keyboard.release.call_count == 2


def test_macro_clipboard_copy_sends_ctrl_c(keyboard, mocker):
    mocker.patch('actions.macro_action.pyperclip.paste', return_value='selected text')

    result = MacroAction({'steps': [{'type': 'clipboard_copy'}]}).execute()

    assert result.success is True, result.message
    assert keyboard.press.call_count == 2


def test_macro_clipboard_paste_sends_ctrl_v(keyboard, mocker):
    mocker.patch('actions.macro_action.pyperclip.paste', return_value='pasted')

    result = MacroAction({'steps': [{'type': 'clipboard_paste'}]}).execute()

    assert result.success is True, result.message
    assert keyboard.press.call_count == 2


def test_macro_reports_failure_instead_of_claiming_success(keyboard):
    """A macro whose steps failed must not report success."""
    result = MacroAction({'steps': [{'type': 'nonsense_step'}]}).execute()

    assert result.success is False
    assert 'failed' in result.message
    assert result.data['failures']


def test_macro_runs_remaining_steps_after_a_failure(keyboard):
    result = MacroAction({
        'steps': [
            {'type': 'nonsense_step'},
            {'type': 'hotkey', 'keys': ['ctrl', 'l']},
        ]
    }).execute()

    assert result.success is False
    assert result.data['steps_executed'] == 2
    assert keyboard.press.call_count == 2
