"""DL-003: Claude Code / Cursor interactions work on macOS as well as Windows.

Covers the pieces that were Windows-only: app identity, Cmd-vs-Ctrl shortcuts,
desktop-app false positives in session detection and agent hooks that called
a `python` interpreter macOS does not ship.
"""
import dataclasses
import json

import pytest

from actions.macro_action import MacroAction
from config import Config
from integrations import agent_hooks, sessions
from integrations.keymaps import COMMANDS_BY_ID
from integrations.keymaps.base import CURSOR_EXES, TERMINAL_EXES, VSCODE_EXES


@pytest.fixture
def operating_system(monkeypatch):
    def pretend(name):
        monkeypatch.setattr('integrations.keymaps.base.platform.system', lambda: name)
        monkeypatch.setattr('integrations.agent_hooks.platform.system', lambda: name)
        monkeypatch.setattr('actions.macro_action.platform.system', lambda: name)
    return pretend


def _hotkeys(command):
    return [step['keys'] for step in command.to_macro_steps('hi') if step['type'] == 'hotkey']


class TestAppIdentity:
    def test_cursor_bundle_matches_cursor_commands(self):
        assert 'cursor.app' in COMMANDS_BY_ID['cursor_prompt'].target_exes

    def test_vscode_and_terminal_bundles_are_known(self):
        assert 'visual studio code.app' in VSCODE_EXES
        assert {'terminal.app', 'iterm.app'} <= set(TERMINAL_EXES)

    def test_windows_exe_names_are_still_known(self):
        assert 'cursor.exe' in CURSOR_EXES
        assert 'windowsterminal.exe' in TERMINAL_EXES


class TestShortcutModifier:
    def test_cursor_uses_cmd_on_macos(self, operating_system):
        operating_system('Darwin')

        assert _hotkeys(COMMANDS_BY_ID['cursor_prompt'])[0] == ['cmd', 'shift', 'l']
        assert _hotkeys(COMMANDS_BY_ID['cursor_followup'])[0] == ['cmd', 'shift', 'y']

    def test_cursor_keeps_ctrl_on_windows(self, operating_system):
        operating_system('Windows')

        assert _hotkeys(COMMANDS_BY_ID['cursor_prompt'])[0] == ['ctrl', 'shift', 'l']

    def test_terminal_agent_never_gets_cmd(self, operating_system):
        operating_system('Darwin')
        claude_commands = [
            command for command in COMMANDS_BY_ID.values()
            if command.id.startswith('cc_')]

        pressed_keys = {
            key for command in claude_commands
            for stroke in _hotkeys(command) for key in stroke}

        assert 'cmd' not in pressed_keys

    def test_backtick_chord_stays_ctrl_on_macos(self, operating_system):
        operating_system('Darwin')
        terminal_toggle = next(
            command for command in COMMANDS_BY_ID.values()
            if '`' in command.keys and set(command.target_exes) & set(VSCODE_EXES))

        assert 'ctrl' in terminal_toggle.native_keys(terminal_toggle.keys)

    @pytest.mark.parametrize('system_name, modifier', [('Darwin', 'cmd'), ('Windows', 'ctrl')])
    def test_clipboard_steps_use_platform_modifier(
            self, operating_system, monkeypatch, system_name, modifier):
        operating_system(system_name)
        pressed = []
        action = MacroAction({'steps': []})
        monkeypatch.setattr(
            action.hotkey_action, 'execute',
            lambda: pressed.append(list(action.hotkey_action.config['keys'])))
        monkeypatch.setattr(
            'actions.macro_action.pyperclip.paste', lambda: 'x', raising=False)

        action._execute_clipboard_copy({})
        action._execute_clipboard_paste({})

        assert pressed[0] == [modifier, 'c']
        assert pressed[1] == [modifier, 'v']


class TestSessionDetectionOnMacos:
    def test_claude_desktop_app_is_not_a_session(self):
        app = {'name': 'Claude',
               'exe': '/Applications/Claude.app/Contents/MacOS/Claude',
               'cmdline': ['/Applications/Claude.app/Contents/MacOS/Claude']}

        assert not sessions._matches(app, 'claude')

    def test_claude_cli_is_a_session(self):
        cli = {'name': 'claude',
               'exe': '/Users/you/.local/share/claude/versions/2.1.0/claude',
               'cmdline': ['/Users/you/.local/bin/claude']}

        assert sessions._matches(cli, 'claude')


class TestAgentHooks:
    @pytest.fixture
    def claude_settings(self, tmp_path, monkeypatch):
        path = tmp_path / 'settings.json'
        redirected = dataclasses.replace(agent_hooks._TARGETS['claude'], path=lambda: path)
        monkeypatch.setitem(agent_hooks._TARGETS, 'claude', redirected)
        monkeypatch.setattr(agent_hooks, 'SUPPORTED_AGENTS', ('claude',))
        monkeypatch.setattr(Config, 'PORT', 5001)
        return path

    def test_macos_uses_python3_and_windows_uses_python(self, operating_system):
        operating_system('Darwin')
        assert agent_hooks.hook_command('claude').startswith('python3 "')

        operating_system('Windows')
        assert agent_hooks.hook_command('claude').startswith('python "')

    def test_install_on_macos_writes_a_runnable_interpreter(
            self, operating_system, claude_settings):
        operating_system('Darwin')

        agent_hooks.install_hook('claude')

        written = claude_settings.read_text()
        assert 'python3 \\"' in written
        assert '--port 5001' in written

    def test_old_python_and_old_port_are_repaired_in_place(
            self, operating_system, claude_settings):
        operating_system('Darwin')
        stale = 'python "/x/scripts/vdock_agent_hook.py" --port 5000 --source claude'
        claude_settings.write_text(json.dumps({'hooks': {'Stop': [{'matcher': '', 'hooks': [
            {'type': 'command', 'command': stale},
            {'type': 'command', 'command': 'echo mine'}]}]}}))

        agent_hooks.install_hook('claude')

        stop_hooks = json.loads(claude_settings.read_text())['hooks']['Stop'][0]['hooks']
        assert stop_hooks[0]['command'].startswith('python3 "')
        assert '--port 5001' in stop_hooks[0]['command']
        assert stop_hooks[1]['command'] == 'echo mine'

    def test_refresh_is_idempotent(self, operating_system, claude_settings):
        operating_system('Darwin')
        agent_hooks.install_hook('claude')

        assert agent_hooks.install_hook('claude').already

    def test_startup_repair_never_installs_a_missing_hook(
            self, operating_system, claude_settings):
        operating_system('Darwin')

        assert agent_hooks.refresh_installed_hooks() == []
        assert not claude_settings.exists()

    def test_startup_repair_fixes_an_installed_hook(self, operating_system, claude_settings):
        operating_system('Windows')
        agent_hooks.install_hook('claude')
        operating_system('Darwin')

        assert agent_hooks.refresh_installed_hooks() == ['claude']
        assert agent_hooks.refresh_installed_hooks() == []

    def test_codex_notify_line_is_refreshed(self, operating_system, tmp_path, monkeypatch):
        operating_system('Darwin')
        monkeypatch.setattr(Config, 'PORT', 5001)
        config_path = tmp_path / 'config.toml'
        config_path.write_text(
            'notify = ["python", "/x/scripts/vdock_agent_hook.py", "--port", "5000", '
            '"--source", "codex"]\nmodel = "x"\n')
        monkeypatch.setattr(agent_hooks, 'codex_config_path', lambda: config_path)

        result = agent_hooks.install_hook('codex')

        text = config_path.read_text()
        assert not result.already
        assert '"python3"' in text and '"5001"' in text
        assert 'model = "x"' in text


class TestHookScriptEndToEnd:
    """The script an installed hook runs, against a stand-in backend."""

    @pytest.fixture
    def received_events(self):
        import http.server
        import threading

        events = []

        class Recorder(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get('Content-Length', 0))
                events.append(json.loads(self.rfile.read(length)))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{}')

            def log_message(self, *args):
                pass

        server = http.server.HTTPServer(('127.0.0.1', 0), Recorder)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        events.append(server.server_address[1])
        yield events
        server.shutdown()

    @pytest.mark.parametrize('interpreter', ['/usr/bin/python3', None])
    def test_cursor_stop_reaches_the_backend_as_ready(self, received_events, interpreter):
        import os
        import subprocess
        import sys

        interpreter = interpreter or sys.executable
        if not os.path.exists(interpreter):
            pytest.skip(f'{interpreter} not present on this machine')
        port = received_events.pop(0)

        completed = subprocess.run(
            [interpreter, str(agent_hooks.hook_script_path()),
             '--port', str(port), '--source', 'cursor'],
            input=json.dumps({'hook_event_name': 'stop', 'workspace_roots': ['/tmp/proj']}),
            capture_output=True, text=True, timeout=15)

        assert completed.returncode == 0, completed.stderr
        assert received_events and received_events[0]['state'] == 'ready'
        assert received_events[0]['source'] == 'cursor'


def test_foreground_exe_macos_prefers_lsappinfo_over_stale_nsworkspace():
    """DL-005: NSWorkspace is stale without a run loop; lsappinfo is live."""
    from unittest.mock import patch, MagicMock
    from utils import window_focus

    def fake_run(argv, **_kw):
        out = ('ASN:0x0-0x970970:\n' if argv[1] == 'front' else
               'x ASN:1: (in front)\n    bundle path="/Applications/Claude.app"\n')
        return MagicMock(stdout=out)

    with patch.object(window_focus.subprocess, 'run', side_effect=fake_run):
        assert window_focus._foreground_exe_macos() == 'claude.app'


def test_foreground_exe_macos_falls_back_when_lsappinfo_missing():
    from unittest.mock import patch
    from utils import window_focus
    with patch.object(window_focus.subprocess, 'run', side_effect=OSError):
        # Must not raise; falls through to NSWorkspace (or None without AppKit).
        window_focus._foreground_exe_macos()


def test_bundle_identity_maps_mac_exe_to_keymap_identity():
    from routes.app_monitor import _bundle_identity
    assert _bundle_identity('/Applications/Cursor.app/Contents/MacOS/Cursor') == 'cursor.app'
    assert _bundle_identity('/Applications/Claude.app/Contents/Frameworks/X.app/Contents/MacOS/X') == 'claude.app'
    assert _bundle_identity('/usr/bin/python3') is None
    assert _bundle_identity(None) is None
    assert _bundle_identity(r'C:\Users\you\Cursor\Cursor.exe') is None
