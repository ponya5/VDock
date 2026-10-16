"""DL-009 - agent hooks can never block an agent, and work in release builds.

Exit code 2 from a hook means "block this prompt" to Claude Code and Cursor;
``python3 <missing script>`` exits 2. The hook therefore runs from a stable
copy outside the VDock folder (source installs) or from the frozen backend
itself (release builds, no Python needed).
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from integrations import agent_hooks  # noqa: E402

BACKEND = Path(__file__).resolve().parents[1]


def test_source_hook_runs_the_stable_copy_with_the_os_interpreter(mocker, tmp_path):
    mocker.patch.object(agent_hooks, 'stable_hook_dir', return_value=tmp_path / 'hookdir')
    mocker.patch.object(agent_hooks.platform, 'system', return_value='Darwin')
    command = agent_hooks.hook_command('claude')
    assert command.startswith('python3 "')
    assert f'{(tmp_path / "hookdir").as_posix()}/vdock_agent_hook.py' in command
    assert agent_hooks.HOOK_MARKER in command


def test_windows_source_hook_keeps_python(mocker, tmp_path):
    mocker.patch.object(agent_hooks, 'stable_hook_dir', return_value=tmp_path)
    mocker.patch.object(agent_hooks.platform, 'system', return_value='Windows')
    assert agent_hooks.hook_command('cursor').startswith('python "')


def test_install_writes_and_refreshes_the_stable_copy(mocker, tmp_path):
    hookdir = tmp_path / 'hookdir'
    mocker.patch.object(agent_hooks, 'stable_hook_dir', return_value=hookdir)
    copy = agent_hooks.ensure_stable_hook_script()
    assert copy.read_bytes() == agent_hooks.hook_script_path().read_bytes()
    copy.write_text('stale')
    agent_hooks.ensure_stable_hook_script()
    assert copy.read_bytes() == agent_hooks.hook_script_path().read_bytes()


@pytest.mark.parametrize('exe,expected_head', [
    ('/Applications/VDock.app/Contents/Resources/backend/vdock-backend',
     '/Applications/VDock.app/Contents/Resources/backend/vdock-backend --vdock_agent_hook'),
    ('C:/Program Files/VDock/resources/backend/vdock-backend.exe',
     '"C:/Program Files/VDock/resources/backend/vdock-backend.exe" --vdock_agent_hook'),
])
def test_release_build_hook_is_the_frozen_backend(mocker, exe, expected_head):
    mocker.patch.object(agent_hooks, 'is_frozen', return_value=True)
    mocker.patch.object(agent_hooks.sys, 'executable', exe)
    command = agent_hooks.hook_command('antigravity', 'Stop')
    assert command.startswith(expected_head)
    assert command.endswith('--source antigravity --event Stop')
    assert agent_hooks.HOOK_MARKER in command  # ownership detection still works


def test_codex_notify_uses_the_same_argv(mocker, tmp_path):
    mocker.patch.object(agent_hooks, 'stable_hook_dir', return_value=tmp_path)
    line = agent_hooks._codex_notify_line()
    argv = json.loads(line.split('=', 1)[1])
    assert argv[1] == (tmp_path / 'vdock_agent_hook.py').as_posix()


def test_status_flags_a_hook_whose_target_is_gone(tmp_path):
    gone = f'python3 "{tmp_path}/nope/vdock_agent_hook.py" --port 5001 --source claude'
    there_file = tmp_path / 'vdock_agent_hook.py'
    there_file.write_text('')
    there = f'python3 "{there_file}" --port 5001 --source claude'
    assert agent_hooks.hook_target_missing(gone) is True
    assert agent_hooks.hook_target_missing(there) is False
    frozen_gone = f'"{tmp_path}/VDock gone/vdock-backend" --vdock_agent_hook --port 1 --source x'
    assert agent_hooks.hook_target_missing(frozen_gone) is True


def test_frozen_entry_point_runs_the_hook_without_flask(tmp_path):
    """`app.py --vdock_agent_hook` (what release builds run) exits 0 at once,
    even with nothing listening, and never imports the web app."""
    started = time.time()
    completed = subprocess.run(
        [sys.executable, '-X', 'importtime', 'app.py', '--vdock_agent_hook',
         '--port', '9', '--source', 'claude'],
        input=json.dumps({'hook_event_name': 'Stop', 'cwd': str(tmp_path)}),
        cwd=str(BACKEND), capture_output=True, text=True, timeout=60,
    )
    assert completed.returncode == 0
    assert '| flask' not in completed.stderr  # importtime lists every import
    assert time.time() - started < 15


def test_hook_falls_back_to_https(mocker):
    sys.path.insert(0, str(BACKEND / 'scripts'))
    import vdock_agent_hook as hook
    calls = []

    def urlopen(request, timeout=None, context=None):
        calls.append((request.full_url, context))
        if request.full_url.startswith('http://'):
            raise OSError('connection reset (TLS-only port)')
        return mock.Mock()

    mocker.patch.object(hook.urllib.request, 'urlopen', side_effect=urlopen)
    hook._post(5001, {'source': 'claude', 'state': 'ready'})
    assert [url for url, _ in calls] == ['http://127.0.0.1:5001/api/agent-events',
                                         'https://127.0.0.1:5001/api/agent-events']
    assert calls[1][1] is not None  # self-signed localhost certificate accepted


# ---------------------------------------------------------------------------
# Focus safety on macOS: never type into the wrong pane / window
# ---------------------------------------------------------------------------

def test_editor_terminal_not_focused_refuses_to_type(mocker):
    from integrations import editor_base
    from integrations.keymaps.claude_code import CLAUDE_CODE_COMMANDS
    command = next(c for c in CLAUDE_CODE_COMMANDS if c.id == 'cc_prompt')
    mocker.patch.object(editor_base.sessions, 'session_alive', return_value=True)
    mocker.patch.object(editor_base, '_resolve_session_host', return_value=4268)
    mocker.patch.object(editor_base.window_focus, 'focus_hwnd', return_value=True)
    mocker.patch.object(editor_base.window_focus, 'session_input_focused', return_value=False)
    mocker.patch.object(editor_base.time, 'sleep')
    macro = mocker.patch.object(editor_base, 'MacroAction')

    result = editor_base.send(command, text_override='continue')
    assert result['success'] is False
    assert 'terminal' in result['message'].lower()
    macro.assert_not_called()


def test_terminal_focus_detected_from_the_accessibility_tree(mocker):
    from utils import window_focus
    focused = object()
    attrs = {('app', 'AXFocusedUIElement'): focused,
             (focused, 'AXDOMClassList'): ['xterm-helper-textarea'],
             (focused, 'AXDescription'): 'Terminal 2, claude'}
    fake = mock.Mock(
        AXIsProcessTrusted=lambda: True,
        AXUIElementCreateApplication=lambda pid: 'app',
        AXUIElementSetAttributeValue=lambda *a: 0,
        AXUIElementCopyAttributeValue=lambda el, name, _: (0, attrs.get((el, name))),
    )
    mocker.patch.dict(sys.modules, {'ApplicationServices': fake})
    assert window_focus._ax_terminal_focused(3486) is True
    attrs[(focused, 'AXDOMClassList')] = ['monaco-editor']
    attrs[(focused, 'AXDescription')] = 'Editor content'
    assert window_focus._ax_terminal_focused(3486) is False


def test_many_terminal_windows_without_tab_selection_refuses(mocker):
    from utils import window_focus
    import psutil
    proc = mock.Mock(terminal=lambda: '/dev/ttys003', cwd=lambda: '/repo')
    mocker.patch.object(window_focus, '_macos_regular_app_pids', return_value={})
    mocker.patch('psutil.Process', return_value=proc)
    mocker.patch.object(window_focus, '_macos_host_app',
                        return_value=(400, '/System/Applications/Utilities/Terminal.app'))
    mocker.patch.object(window_focus, '_select_tty_tab', return_value=False)
    mocker.patch.object(window_focus, '_visible_window_count', return_value=2)
    run = mocker.patch.object(window_focus.subprocess, 'run')
    assert window_focus._focus_session_macos(20) is False
    assert 'Automation' in window_focus.last_focus_problem()
    run.assert_not_called()  # never activated the app on a guess
