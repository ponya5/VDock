"""DL-005: interactive CLI buttons need a visible terminal off Windows."""
import os
import shlex
from unittest.mock import patch

import pytest

from utils import subprocess_runner as sr


@pytest.fixture
def fake_binary(tmp_path):
    exe = tmp_path / 'claude'
    exe.write_text('#!/bin/sh\n')
    exe.chmod(0o755)
    with patch.object(sr, 'find_binary', return_value=str(exe)):
        yield str(exe)


def test_macos_opens_terminal_with_command_file(fake_binary, tmp_path):
    with patch.object(sr.sys, 'platform', 'darwin'), \
            patch.object(sr.os, 'name', 'posix'), \
            patch.object(sr.subprocess, 'Popen') as popen:
        sr.spawn_in_terminal(['claude', '--continue'], cwd=str(tmp_path),
                             fallback=['claude'])
    argv = popen.call_args[0][0]
    assert argv[:3] == ['open', '-a', 'Terminal']
    script = open(argv[3]).read()
    os.unlink(argv[3])
    # Paths are shlex-quoted in the script; Windows paths get wrapped in
    # single quotes, POSIX paths without spaces come back unchanged.
    assert f"cd {shlex.quote(str(tmp_path))}" in script
    quoted = shlex.quote(fake_binary)
    assert f"{quoted} --continue || {quoted}" in script
    assert popen.call_args[1]['shell'] is False


def test_macos_quotes_hostile_cwd(fake_binary, tmp_path):
    cwd = str(tmp_path / "a b; rm -rf ~")
    with patch.object(sr.sys, 'platform', 'darwin'), \
            patch.object(sr.os, 'name', 'posix'), \
            patch.object(sr.subprocess, 'Popen') as popen:
        sr.spawn_in_terminal(['claude'], cwd=cwd)
    path = popen.call_args[0][0][3]
    script = open(path).read()
    os.unlink(path)
    assert "'" + cwd + "'" in script


def test_linux_uses_first_available_terminal(fake_binary):
    def which(name):
        return '/usr/bin/xterm' if name == 'xterm' else None
    with patch.object(sr.sys, 'platform', 'linux'), \
            patch.object(sr.os, 'name', 'posix'), \
            patch.object(sr.shutil, 'which', side_effect=which), \
            patch.object(sr.subprocess, 'Popen') as popen:
        sr.spawn_in_terminal(['claude'], cwd='/tmp')
    argv = popen.call_args[0][0]
    assert argv[:2] == ['/usr/bin/xterm', '-e'] and argv[2:4] == ['sh', '-c']


def test_linux_without_terminal_raises(fake_binary):
    with patch.object(sr.sys, 'platform', 'linux'), \
            patch.object(sr.os, 'name', 'posix'), \
            patch.object(sr.shutil, 'which', return_value=None):
        with pytest.raises(OSError):
            sr.spawn_in_terminal(['claude'])


def test_windows_keeps_plain_spawn():
    with patch.object(sr.os, 'name', 'nt'), \
            patch.object(sr, 'spawn') as spawn:
        sr.spawn_in_terminal(['cmd.exe', '/c', 'claude'], cwd='C:\\x',
                             fallback=['claude'])
    spawn.assert_called_once_with(['cmd.exe', '/c', 'claude'], cwd='C:\\x')


def test_missing_binary():
    with patch.object(sr.os, 'name', 'posix'), \
            patch.object(sr, 'find_binary', return_value=None):
        with pytest.raises(sr.BinaryNotFoundError):
            sr.spawn_in_terminal(['claude'])


class _R:
    def __init__(self, ok, msg='m'):
        self.success, self.message, self.data = ok, msg, {}


def _plugin():
    from integrations.claude_pack import Plugin
    return Plugin()


def _capture(results):
    calls = []

    class Fake:
        def __init__(self, cfg):
            calls.append(cfg)

        def execute(self):
            return results.pop(0)
    return calls, Fake


@pytest.mark.parametrize('osname,expected', [('posix', 'Claude'),
                                             ('nt', 'claude://')])
def test_claude_open_desktop_uses_name_key(osname, expected):
    calls, fake = _capture([_R(True)])
    with patch('actions.cross_platform_action.CrossPlatformAction', fake), \
            patch('integrations.claude_pack.os.name', osname):
        out = _plugin().execute_action('claude_open', {'target': 'desktop'})
    assert out['success']
    assert calls == [{'action': 'open_app', 'name': expected}]


def test_claude_open_desktop_falls_back_to_web():
    calls, fake = _capture([_R(False), _R(True)])
    with patch('actions.cross_platform_action.CrossPlatformAction', fake):
        out = _plugin().execute_action('claude_open', {'target': 'desktop'})
    assert out['success'] and 'claude.ai' in out['message']
    assert calls[1] == {'action': 'open_url', 'url': 'https://claude.ai'}
