"""The keymaps package must be a drop-in replacement for keymaps.py.

Feature: ide-agent-control phase 1. This phase is a pure consolidation: if any
command's id, keys or macro steps change here, a user's existing button silently
starts doing something different. These tests are the guard against that.
"""
import pytest

from integrations import keymaps


def test_public_names_are_all_re_exported():
    for name in ('Command', 'COPILOT_COMMANDS', 'CURSOR_COMMANDS',
                 'ALL_COMMANDS', 'COMMANDS_BY_ID',
                 'VSCODE_EXES', 'CURSOR_EXES', 'JETBRAINS_EXES'):
        assert hasattr(keymaps, name), '{} is missing'.format(name)


def test_command_ids_are_unique():
    ids = [cmd.id for cmd in keymaps.ALL_COMMANDS]
    assert len(set(ids)) == len(ids)


def test_all_commands_is_the_union_of_the_per_app_tuples():
    assert set(keymaps.ALL_COMMANDS) == (
        set(keymaps.COPILOT_COMMANDS) | set(keymaps.CURSOR_COMMANDS)
    )


def test_known_commands_keep_their_keys():
    """Spot-check the bindings most likely to be depended on."""
    expected = {
        'cursor_composer': ('ctrl', 'i'),
        'cursor_chat': ('ctrl', 'l'),
        'cursor_accept': ('ctrl', 'enter'),
        'copilot_chat': ('ctrl', 'alt', 'i'),
        'copilot_accept': ('tab',),
    }
    for command_id, keys in expected.items():
        assert keymaps.COMMANDS_BY_ID[command_id].keys == keys


def test_new_fields_default_to_the_previous_behaviour():
    """risk/requires_session are declared here but only enforced in phase 2."""
    for cmd in keymaps.ALL_COMMANDS:
        assert cmd.risk in ('safe', 'input', 'destructive')
        assert cmd.requires_session is False


def test_macro_steps_are_unchanged_for_a_text_command():
    explain = keymaps.COMMANDS_BY_ID['copilot_explain']
    steps = explain.to_macro_steps()
    assert steps[0] == {'type': 'hotkey', 'keys': ['ctrl', 'alt', 'i']}
    assert {'type': 'text', 'text': '/explain'} in steps
    assert steps[-1] == {'type': 'hotkey', 'keys': ['enter']}


def test_macro_steps_honour_a_text_override():
    explain = keymaps.COMMANDS_BY_ID['copilot_explain']
    steps = explain.to_macro_steps('custom prompt')
    assert {'type': 'text', 'text': 'custom prompt'} in steps


def test_the_old_module_is_gone():
    import os
    from config import Config
    assert not os.path.exists(
        os.path.join(str(Config.BASE_DIR), 'integrations', 'keymaps.py')
    )
