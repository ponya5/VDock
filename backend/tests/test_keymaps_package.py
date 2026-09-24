"""The keymaps package must be a drop-in replacement for keymaps.py.

Feature: ide-agent-control phase 1. This phase is a pure consolidation: if any
command's id, keys or macro steps change here, a user's existing button silently
starts doing something different. These tests are the guard against that.
"""
import pytest

from integrations import keymaps


def test_public_names_are_all_re_exported():
    for name in ('Command', 'COPILOT_COMMANDS', 'CURSOR_COMMANDS',
                 'CLAUDE_CODE_COMMANDS', 'ALL_COMMANDS', 'COMMANDS_BY_ID',
                 'VSCODE_EXES', 'CURSOR_EXES', 'JETBRAINS_EXES',
                 'TERMINAL_EXES'):
        assert hasattr(keymaps, name), '{} is missing'.format(name)


def test_command_ids_are_unique():
    ids = [cmd.id for cmd in keymaps.ALL_COMMANDS]
    assert len(set(ids)) == len(ids)


def test_all_commands_is_the_union_of_the_per_app_tuples():
    assert set(keymaps.ALL_COMMANDS) == (
        set(keymaps.COPILOT_COMMANDS) | set(keymaps.CURSOR_COMMANDS)
        | set(keymaps.CLAUDE_CODE_COMMANDS) | set(keymaps.DEVIN_COMMANDS)
        | set(keymaps.JETBRAINS_COMMANDS)
        | set(keymaps.VISUAL_STUDIO_COMMANDS) | set(keymaps.VSCODE_COMMANDS)
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
    """risk/requires_session were declared in phase 1 and are enforced from
    phase 2 -- pre-existing editor commands must keep the old defaults so a
    saved button behaves exactly as before."""
    for cmd in keymaps.COPILOT_COMMANDS + keymaps.CURSOR_COMMANDS:
        assert cmd.risk in ('safe', 'input', 'destructive')
        assert cmd.requires_session is False

    # Phase-2 commands are allowed to declare the new fields.
    for cmd in keymaps.ALL_COMMANDS:
        assert cmd.risk in ('safe', 'input', 'destructive')
        if cmd.requires_session:
            assert cmd.session_marker, cmd.id


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


def test_cursor_prompt_opens_a_new_agent_chat_and_types_into_it():
    """Regression guard for DL-066: Ctrl+Shift+L opens and focuses a new
    agent chat (unlike the Ctrl+L / Ctrl+I toggles), so it is the only safe
    lead-in key for a scene prompt button."""
    prompt = keymaps.COMMANDS_BY_ID['cursor_prompt']
    steps = prompt.to_macro_steps('Explain:\n\nclipboard text')
    assert steps[0] == {'type': 'hotkey', 'keys': ['ctrl', 'shift', 'l']}
    assert {'type': 'text', 'text': 'Explain:'} in steps
    assert {'type': 'hotkey', 'keys': ['shift', 'enter']} in steps
    assert {'type': 'text', 'text': 'clipboard text'} in steps
    assert steps[-1] == {'type': 'hotkey', 'keys': ['enter']}


def test_cursor_followup_focuses_the_current_chat_before_typing():
    followup = keymaps.COMMANDS_BY_ID['cursor_followup']
    steps = followup.to_macro_steps()
    assert steps[0] == {'type': 'hotkey', 'keys': ['ctrl', 'shift', 'y']}
    assert {'type': 'text', 'text': 'continue'} in steps
    assert steps[-1] == {'type': 'hotkey', 'keys': ['enter']}


def test_cursor_submit_focuses_the_chat_before_pressing_enter():
    """cursor_submit must never be a bare Enter: with focus anywhere else
    (e.g. a file) that would insert a newline instead of sending a chat
    message."""
    submit = keymaps.COMMANDS_BY_ID['cursor_submit']
    steps = submit.to_macro_steps()
    assert steps == [
        {'type': 'hotkey', 'keys': ['ctrl', 'shift', 'y']},
        {'type': 'delay', 'delay': 150},
        {'type': 'hotkey', 'keys': ['enter']},
    ]


def test_the_old_module_is_gone():
    import os
    from config import Config
    assert not os.path.exists(
        os.path.join(str(Config.BASE_DIR), 'integrations', 'keymaps.py')
    )
