"""DL-013: VS Code / Devin macOS chords.

Verified against the installed app bundles, not sent as keystrokes:
VS Code 1.141 workbench registers the Source Control view with
``mac: WinCtrl+Shift+G`` (physical Ctrl), ``saveAll`` with
``mac: CtrlCmd+Alt+S`` (while CtrlCmd+K S is *Save without Formatting*),
Replace as Cmd+Alt+F, Add Cursor Below as Cmd+Alt+Down. Devin CLI exits
with Ctrl+D (Ctrl+C only clears the draft / cancels the agent).
"""
import json
import os
from unittest import mock

import pytest

from utils import host_os

TEMPLATES = os.path.join(os.path.dirname(__file__), '..', 'data', 'templates')


def as_os(name):
    return mock.patch('utils.host_os.platform',
                      mock.Mock(system=lambda: name))


def template(tid):
    for f in os.listdir(TEMPLATES):
        data = json.load(open(os.path.join(TEMPLATES, f), encoding='utf-8'))
        if data['id'] == tid:
            return data
    raise KeyError(tid)


def buttons(t):
    return {b['label']: b for p in t['pages'] for b in p['buttons']}


@pytest.mark.parametrize('tid', ['template-ide-vscode', 'template-ide-cursor'])
def test_save_all_uses_the_macos_save_all_chord(tid):
    """macOS Save All is Cmd+Alt+S; CtrlCmd+K S is *Save without Formatting*."""
    with as_os('Darwin'):
        b = buttons(host_os.localize_template(template(tid)))
    action = b['Save All']['action']
    assert action['config']['steps'] == [
        {'type': 'hotkey', 'keys': ['cmd', 'alt', 's']}]
    assert 'mac_steps' not in action['config']
    assert b['Save All']['secondary_label'] == '⌘⌥S'


@pytest.mark.parametrize('tid', ['template-ide-vscode', 'template-ide-cursor'])
def test_save_all_keeps_ctrl_k_s_on_windows(tid):
    with as_os('Windows'):
        assert host_os.localize_template(template(tid))['pages'][0]['buttons']
    b = buttons(template(tid))  # Windows returns the template untouched.
    steps = b['Save All']['action']['config']['steps']
    assert [s.get('keys') for s in steps if s['type'] == 'hotkey'] == [
        ['ctrl', 'k'], ['s']]


@pytest.mark.parametrize('tid', ['template-ide-vscode', 'template-ide-cursor'])
def test_vscode_template_chords_on_macos(tid):
    """Explicit mac chords from the bundle, verified in DL-013."""
    with as_os('Darwin'):
        b = buttons(host_os.localize_template(template(tid)))
    assert b['Replace']['action']['config']['keys'] == ['cmd', 'alt', 'f']
    assert b['Replace']['secondary_label'] == '⌘⌥F'
    assert b['Multi-Cursor']['action']['config']['keys'] == ['cmd', 'alt', 'down']
    assert b['Multi-Cursor']['secondary_label'] == '⌘⌥↓'
    # Source Control stays the physical Control key on macOS.
    git = 'Git Push' if 'cursor' in tid else 'Git'
    assert b[git]['action']['config']['keys'] == ['ctrl', 'shift', 'g']
    assert b[git].get('secondary_label') in (None, '⌃⇧G')
    # Zen Mode is CtrlCmd+K Z in the bundle - the generic rule is correct.
    steps = json.dumps(b['Zen Mode']['action'])
    assert '"cmd", "k"' in steps and '"z"' in steps


@pytest.mark.parametrize('tid', ['template-ide-vscode', 'template-ide-cursor'])
def test_vscode_template_chords_unchanged_on_windows(tid):
    with as_os('Windows'):
        t = template(tid)
        assert host_os.localize_template(t) is t


def test_vscode_git_view_stays_physical_ctrl_on_macos():
    from integrations.keymaps.vscode import VSCODE_COMMANDS
    cmd = next(c for c in VSCODE_COMMANDS if c.id == 'vsc_git_view')
    with as_os('Darwin'):
        assert cmd.native_keys(cmd.keys) == ('ctrl', 'shift', 'g')
    with as_os('Windows'):
        assert cmd.native_keys(cmd.keys) == ('ctrl', 'shift', 'g')


def test_devin_exit_is_ctrl_d_after_clearing_the_draft():
    """Ctrl+C cancels/clears - it never quits; Ctrl+D exits on an empty input."""
    from integrations.keymaps.devin import DEVIN_COMMANDS
    cmd = next(c for c in DEVIN_COMMANDS if c.id == 'devin_exit')
    steps = cmd.to_macro_steps()
    hotkeys = [s['keys'] for s in steps if s['type'] == 'hotkey']
    assert hotkeys[-1] == ['ctrl', 'd']
    assert hotkeys[:2] == [['ctrl', 'c'], ['ctrl', 'c']]
    # Terminal agent: same chord on macOS and Windows.
    for system in ('Darwin', 'Windows'):
        with as_os(system):
            assert cmd.native_keys(cmd.keys) == ('ctrl', 'c')
