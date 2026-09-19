"""App profiles group a keymap with its process names and a deck layout.

Feature: ide-agent-control phase 1. The layout is what phase 4 generates a
context scene from, so a layout referencing a command that does not exist would
surface as a blank button much later. It is checked here instead.
"""
import pytest

from integrations import keymaps


def test_every_profile_has_commands_and_exes():
    assert keymaps.ALL_PROFILES
    for profile in keymaps.ALL_PROFILES:
        assert profile.commands, '{} has no commands'.format(profile.id)
        assert profile.exes, '{} has no exes'.format(profile.id)


def test_profile_ids_are_unique():
    ids = [p.id for p in keymaps.ALL_PROFILES]
    assert len(set(ids)) == len(ids)


def test_default_layout_only_references_real_commands():
    for profile in keymaps.ALL_PROFILES:
        known = {cmd.id for cmd in profile.commands}
        for row in profile.default_layout:
            for command_id in row:
                assert command_id in known, (
                    '{} layout references unknown command {}'.format(
                        profile.id, command_id)
                )


def test_kind_is_one_of_the_two_supported_values():
    for profile in keymaps.ALL_PROFILES:
        assert profile.kind in ('editor', 'terminal_agent')


def test_profile_for_exe_is_case_insensitive():
    assert keymaps.profile_for_exe('Cursor.exe').id == 'cursor'
    assert keymaps.profile_for_exe('cursor.exe').id == 'cursor'


def test_profile_for_an_unknown_exe_is_none():
    assert keymaps.profile_for_exe('notepad.exe') is None


def test_to_dict_is_json_serialisable_and_carries_risk():
    import json
    payload = keymaps.PROFILES_BY_ID['cursor'].to_dict()
    json.dumps(payload)
    assert payload['id'] == 'cursor'
    for command in payload['commands']:
        assert 'risk' in command
        assert 'keys' in command
