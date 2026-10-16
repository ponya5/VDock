"""DL-012: Codex hooks, Antigravity payload, event ordering, exact-pid targeting.

Everything OS-specific (process table, windows, keystrokes) is mocked: these
tests pin the contracts, and run the same on Windows, macOS and Linux.
"""
import json
import os
import subprocess
import sys
import time

import psutil
import pytest

from app import app
from integrations import agent_state, editor_base, sessions
from integrations.keymaps import COMMANDS_BY_ID
import routes.agent_events as agent_events
import routes.agent_mission as mission
from scripts import vdock_agent_hook as hook
from services import agent_prompt
from utils import window_focus


@pytest.fixture
def client():
    app.config['TESTING'] = True
    agent_state.reset()
    agent_events._alerts.clear()
    with app.test_client() as test_client:
        yield test_client
    agent_state.reset()
    agent_events._alerts.clear()


def _post(client, **body):
    body.setdefault('source', 'cursor')
    body.setdefault('session_id', 's1')
    return client.post('/api/agent-events', json=body)


def _entry(source='cursor', session_id='s1'):
    return next((e for e in agent_state.session_entries(source)
                 if e['session_id'] == session_id), None)


# ---------------------------------------------------------------------------
# Codex hooks: same events as Claude Code, payload on stdin
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('event_name, expected', [
    ('SessionStart', 'ready'),
    ('UserPromptSubmit', 'working'),
    ('PreToolUse', 'working'),
    ('PostToolUse', 'working'),
    ('PermissionRequest', 'permission'),
    ('Stop', 'ready'),
    ('Interrupt', 'ready'),
    ('SessionEnd', 'ended'),
    # Compaction and subagents say nothing about the main turn.
    ('PreCompact', None), ('PostCompact', None),
    ('SubagentStart', None), ('SubagentStop', None),
])
def test_codex_hook_events_map_to_states(event_name, expected):
    assert hook.map_event('codex', {'hook_event_name': event_name}) == expected


def test_codex_permission_request_names_what_is_being_approved():
    payload = {'hook_event_name': 'PermissionRequest', 'session_id': 'c1',
               'cwd': '/repo/app', 'tool_name': 'Bash',
               'tool_input': {'command': 'git push origin main'}}
    body = hook.build_body('codex', 'permission', payload)
    assert body['message'] == 'Run: git push origin main'
    assert body['attention'] is True and body['detailed'] is True
    assert body['session_id'] == 'c1' and body['project'] == 'app'
    patch_payload = {**payload, 'tool_name': 'apply_patch',
                     'tool_input': {'command': '*** Begin Patch ...'}}
    assert hook.build_body('codex', 'permission', patch_payload)['message'] == 'Edit files'


def test_codex_prompt_and_reply_reach_the_console():
    submit = hook.build_body('codex', 'working', {
        'hook_event_name': 'UserPromptSubmit', 'session_id': 'c1', 'prompt': 'fix it'})
    assert submit['prompt'] == 'fix it' and submit['prompted'] is True
    stop = hook.build_body('codex', 'ready', {
        'hook_event_name': 'Stop', 'session_id': 'c1',
        'last_assistant_message': 'Done.'})
    assert stop['reply'] == 'Done.' and stop['attention'] is False


def test_codex_hook_reads_stdin_and_the_legacy_notify_argv_still_works():
    received = []
    import http.server
    import threading

    class Recorder(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            received.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{}')

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(('127.0.0.1', 0), Recorder)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = str(server.server_address[1])
    script = str(hook.__file__)
    try:
        subprocess.run([sys.executable, script, '--port', port, '--source', 'codex'],
                       input=json.dumps({'hook_event_name': 'UserPromptSubmit',
                                         'session_id': 'c1', 'cwd': '/p/app',
                                         'prompt': 'go'}),
                       text=True, capture_output=True, timeout=15, check=True)
        subprocess.run([sys.executable, script, '--port', port, '--source', 'codex',
                        json.dumps({'type': 'agent-turn-complete', 'thread-id': 'c2',
                                    'cwd': '/p/app'})],
                       text=True, capture_output=True, timeout=15, check=True,
                       stdin=subprocess.DEVNULL)
    finally:
        server.shutdown()
    assert [(e['state'], e['session_id']) for e in received] == [
        ('working', 'c1'), ('ready', 'c2')]


# ---------------------------------------------------------------------------
# Antigravity: camelCase payload
# ---------------------------------------------------------------------------

def test_antigravity_payload_gives_a_session_and_a_project():
    payload = {'hook_event_name': 'PreToolUse', 'conversationId': 'conv-9',
               'workspacePaths': ['/Users/me/work/api', '/Users/me/other'],
               'toolCall': {'name': 'run_command', 'args': {}}}
    body = hook.build_body('antigravity', 'working', payload)
    assert body['session_id'] == 'conv-9'
    assert body['cwd'] == '/Users/me/work/api' and body['project'] == 'api'


@pytest.mark.parametrize('stop_payload, expected', [
    ({'fullyIdle': True}, 'ready'),
    ({}, 'ready'),
    # Background work can still re-enter the loop: not waiting on the user.
    ({'fullyIdle': False}, 'working'),
])
def test_antigravity_stop_is_ready_only_when_fully_idle(stop_payload, expected):
    assert hook.map_event('antigravity',
                          {'hook_event_name': 'Stop', **stop_payload}) == expected


# ---------------------------------------------------------------------------
# Hook body: ordering + identity fields
# ---------------------------------------------------------------------------

def test_body_carries_start_time_turn_and_launching_process():
    before = time.time()
    body = hook.build_body('cursor', 'working', {
        'hook_event_name': 'afterAgentResponse', 'generation_id': 'g7',
        'conversation_id': 'c1', 'text': 'hi'})
    assert body['turn_id'] == 'g7'
    assert body['passive'] is True
    assert body['hook_pid'] == os.getppid()
    assert hook.STARTED_AT <= before + 60 and body['event_ts'] == hook.STARTED_AT
    assert hook.build_body('claude', 'working', {
        'hook_event_name': 'PreToolUse'})['passive'] is False
    assert hook.build_body('codex', 'working', {
        'hook_event_name': 'PreToolUse', 'turn_id': 't3'})['turn_id'] == 't3'


def test_hook_never_waits_on_a_terminal_keyboard(monkeypatch):
    class Tty:
        def isatty(self):
            return True

        def read(self):  # pragma: no cover - would hang a real hook
            raise AssertionError('must not read from a terminal')

    monkeypatch.setattr(sys, 'stdin', Tty())
    assert hook._read_payload() == {}


# ---------------------------------------------------------------------------
# Out-of-order events (separate hook processes race to the backend)
# ---------------------------------------------------------------------------

def test_a_late_event_that_started_before_stop_is_ignored(client):
    now = time.time()
    _post(client, state='working', event_ts=now - 3)
    _post(client, state='ready', event_ts=now - 1)
    late = _post(client, state='working', event_ts=now - 2)  # PostToolUse, slow to arrive

    assert late.get_json() == {'success': True, 'ignored': 'stale'}
    assert _entry()['state'] == 'ready'


def test_events_in_order_and_events_without_a_timestamp_still_apply(client):
    now = time.time()
    _post(client, state='ready', event_ts=now - 5)
    _post(client, state='working', event_ts=now - 4)
    assert _entry()['state'] == 'working'
    _post(client, state='ready')  # an older hook copy sends no event_ts
    assert _entry()['state'] == 'ready'


def test_a_late_event_cannot_resurrect_an_ended_session(client):
    now = time.time()
    _post(client, state='working', event_ts=now - 3)
    _post(client, state='ended', event_ts=now - 1)
    assert _entry() is None
    _post(client, state='working', event_ts=now - 2)
    assert _entry() is None
    # The same session id resumed later is a real new start.
    _post(client, state='ready', event_ts=now + 1)
    assert _entry()['state'] == 'ready'


def test_an_absurd_hook_clock_does_not_poison_ordering(client):
    now = time.time()
    _post(client, state='working', event_ts=now + 10 ** 9)
    _post(client, state='ready', event_ts=now - 1)
    assert _entry()['state'] == 'ready'


def test_cursor_reply_after_stop_updates_the_reply_but_not_the_state(client):
    _post(client, state='working', turn_id='g1', prompt='do it')
    _post(client, state='ready', turn_id='g1')
    # Cursor reports the final message after `stop`.
    _post(client, state='working', turn_id='g1', passive=True, reply='All done.')
    entry = _entry()
    assert entry['state'] == 'ready'
    assert entry['reply'] == 'All done.'
    # ...while a mid-run response, or one of a new turn, is ordinary work.
    _post(client, state='working', turn_id='g2', prompt='next')
    _post(client, state='working', turn_id='g2', passive=True, reply='step')
    assert _entry()['state'] == 'working'


# ---------------------------------------------------------------------------
# The agent's own process
# ---------------------------------------------------------------------------

class _FakeProcess:
    """A tiny process table: pid -> (parent pid, name, cmdline)."""
    table = {}

    def __init__(self, pid):
        if pid not in self.table:
            raise psutil.NoSuchProcess(pid)
        self.pid = pid

    def as_dict(self, _attrs):
        _parent, name, cmdline = self.table[self.pid]
        return {'name': name, 'cmdline': cmdline, 'exe': cmdline[0]}

    def parent(self):
        parent = self.table[self.pid][0]
        return _FakeProcess(parent) if parent in self.table else None

    def create_time(self):
        return 1000.0 + self.pid


@pytest.fixture
def process_table(monkeypatch):
    _FakeProcess.table = {
        1: (0, 'launchd', ['/sbin/launchd']),
        100: (1, 'zsh', ['/bin/zsh']),
        200: (100, 'claude', ['/Users/me/.local/bin/claude']),
        300: (200, 'sh', ['/bin/sh', '-c', 'python3 hook.py']),
        400: (300, 'python3', ['python3', 'hook.py']),
        # Two terminals: a second claude with its own shell/hook.
        500: (100, 'claude', ['/Users/me/.local/bin/claude']),
        600: (500, 'python3', ['python3', 'hook.py']),
        # Cursor's built-in agent: only the IDE's helper processes.
        700: (1, 'Cursor Helper', ['/Applications/Cursor.app/Contents/Frameworks/Helper']),
        800: (700, 'node', ['node', 'hook.js']),
    }
    monkeypatch.setattr(sessions.psutil, 'Process', _FakeProcess)
    return _FakeProcess.table


def test_hook_pid_resolves_to_the_nearest_agent_ancestor(process_table):
    assert sessions.agent_pid_from_hook('claude', 400) == (200, 1200.0)
    assert sessions.agent_pid_from_hook('claude', 600) == (500, 1500.0)


def test_no_agent_process_above_the_hook_is_not_an_error(process_table):
    assert sessions.agent_pid_from_hook('cursor', 800) is None  # IDE helpers excluded
    assert sessions.agent_pid_from_hook('claude', 999) is None  # already gone
    assert sessions.agent_pid_from_hook('claude', None) is None
    assert sessions.agent_pid_from_hook('claude', 'x') is None
    assert sessions.agent_pid_from_hook('', 400) is None


def test_event_route_ties_a_session_to_its_process_once(client, process_table, mocker):
    walk = mocker.spy(sessions, 'agent_pid_from_hook')
    _post(client, source='claude', session_id='a', state='working', hook_pid=400)
    _post(client, source='claude', session_id='a', state='working', hook_pid=400)
    _post(client, source='claude', session_id='b', state='working', hook_pid=600)
    assert _entry('claude', 'a')['pid'] == 200
    assert _entry('claude', 'b')['pid'] == 500
    assert walk.call_count == 2  # not per event


def test_process_alive_knows_reused_pids():
    me = psutil.Process(os.getpid())
    assert sessions.process_alive(me.pid, me.create_time()) is True
    assert sessions.process_alive(me.pid, me.create_time() + 3600) is False  # reused
    child = subprocess.Popen([sys.executable, '-c', 'pass'])
    child.wait()
    assert sessions.process_alive(child.pid) is False


def test_a_killed_session_leaves_even_while_another_one_runs(client):
    me = psutil.Process(os.getpid())
    child = subprocess.Popen([sys.executable, '-c', 'pass'])
    child.wait()
    agent_state.record('claude', 'ready', session_id='dead', pid=child.pid, prompted=True)
    agent_state.record('claude', 'working', session_id='alive', pid=me.pid,
                       pid_started=me.create_time())
    for entry in agent_state._sessions_by_source['claude'].values():
        entry['ts'] -= 60  # quiet past the grace period

    assert [e['session_id'] for e in agent_state.session_entries('claude')] == ['alive']


def test_a_session_without_a_pid_keeps_ttl_only_expiry(client):
    agent_state.record('claude', 'ready', session_id='x')
    agent_state._sessions_by_source['claude']['x']['ts'] -= 60
    assert [e['session_id'] for e in agent_state.session_entries('claude')] == ['x']


# ---------------------------------------------------------------------------
# Targeting by pid
# ---------------------------------------------------------------------------

def _hosts(*pids):
    return [{'pid': pid, 'hwnd': 9000 + pid, 'title': f'wt {pid}', 'self_owned': False,
             'create_time': float(pid), 'cwd': '/repos/web', 'host': 'Terminal'}
            for pid in pids]


def test_host_window_for_pid_never_falls_back(mocker):
    mocker.patch.object(window_focus, 'list_session_hosts', return_value=_hosts(100, 200))
    assert window_focus.host_window_for_pid('claude', 200) == 9200
    assert window_focus.host_window_for_pid('claude', 300) is None


def test_two_sessions_in_one_directory_each_get_their_own_state(client, mocker):
    """The cwd join could not tell these apart (both /repos/web)."""
    mocker.patch.object(window_focus, 'list_session_hosts', return_value=_hosts(100, 200))
    mocker.patch.object(window_focus, 'find_session_host_window', return_value=9100)
    mocker.patch.object(sessions, 'iter_session_pids', return_value=[100, 200])
    agent_state.record('claude', 'permission', session_id='a', cwd='/repos/web',
                       message='Run: rm -rf build', pid=100, prompted=True)
    agent_state.record('claude', 'working', session_id='b', cwd='/repos/web',
                       message='Reading files', pid=200, prompted=True)
    for entry in agent_state._sessions_by_source['claude'].values():
        entry['pid_started'] = None

    rows = client.get('/api/agent-sessions?source=claude').get_json()['sessions']

    by_pid = {row['pid']: row for row in rows}
    assert by_pid[100]['state'] == 'permission' and by_pid[100]['detail'] == 'Run: rm -rf build'
    assert by_pid[200]['state'] == 'working' and by_pid[200]['detail'] == 'Reading files'


def test_send_to_a_known_session_refuses_instead_of_using_another_window(mocker):
    mocker.patch.object(window_focus, 'host_window_for_pid', return_value=None)
    find = mocker.patch.object(window_focus, 'find_session_host_window', return_value=9100)
    mocker.patch.object(editor_base.sessions, 'session_alive', return_value=True)
    mocker.patch.object(window_focus, 'interactive_desktop_blocked', return_value=False)
    macro = mocker.patch.object(editor_base, 'MacroAction')

    result = editor_base.send(COMMANDS_BY_ID['cc_accept'], session_pid=4242)

    assert result['success'] is False
    assert "session's window" in result['message']
    macro.assert_not_called()
    find.assert_not_called()  # no cwd/ranking guess behind the user's back


def test_send_to_a_known_session_types_into_that_window(mocker):
    host = mocker.patch.object(window_focus, 'host_window_for_pid', return_value=9200)
    mocker.patch.object(editor_base.sessions, 'session_alive', return_value=True)
    mocker.patch.object(window_focus, 'interactive_desktop_blocked', return_value=False)
    mocker.patch.object(window_focus, 'focus_hwnd', return_value=True)
    mocker.patch.object(window_focus, 'session_input_focused', return_value=True)
    mocker.patch.object(window_focus, 'foreground_hwnd', return_value=9200)
    mocker.patch.object(editor_base.time, 'sleep')
    macro = mocker.patch.object(editor_base, 'MacroAction')
    macro.return_value.execute.return_value = mocker.Mock(
        success=True, message='', details='', data=None)

    result = editor_base.send(COMMANDS_BY_ID['cc_accept'], session_pid=200)

    assert result['success'] is True
    host.assert_called_once_with('claude', 200)


def test_mission_decide_targets_the_sessions_own_process(client, mocker):
    sent = []
    mocker.patch.object(editor_base, 'send', side_effect=lambda cmd, **kw: (
        sent.append((cmd.id, kw)) or {'success': True}))
    agent_state.record('claude', 'permission', session_id='b', cwd='/repos/web', pid=200)

    response = client.post('/api/agent-mission/decide', json={
        'source': 'claude', 'session_id': 'b', 'decision': 'approve'})

    assert response.get_json()['success'] is True
    assert sent[0][1]['session_pid'] == 200


def test_mission_focus_uses_the_sessions_process(client, mocker):
    host = mocker.patch.object(window_focus, 'host_window_for_pid', return_value=9200)
    by_cwd = mocker.patch.object(window_focus, 'find_session_host_window')
    focus = mocker.patch.object(window_focus, 'focus_hwnd', return_value=True)
    agent_state.record('claude', 'ready', session_id='b', cwd='/repos/web', pid=200)

    assert client.post('/api/agent-mission/focus', json={
        'source': 'claude', 'session_id': 'b'}).get_json()['success'] is True
    host.assert_called_once_with('claude', 200)
    by_cwd.assert_not_called()
    focus.assert_called_once_with(9200)


def test_prompt_target_carries_the_pid_and_skips_the_pin_guard(mocker):
    agent_state.record('claude', 'ready', session_id='a', cwd='/repos/web', pid=100)
    agent_state.record('claude', 'permission', session_id='b', cwd='/repos/web', pid=200)
    mocker.patch.object(sessions, 'pinned_pid', return_value=100)

    target = agent_prompt.resolve_target(source='claude', session_id='a')

    assert target.pid == 100
    # A pin makes `send` ignore the cwd, so another session's approval could
    # be answered by typed text - unless the pid names the window exactly.
    assert agent_prompt._pinned_risk(target) is None
    legacy = agent_prompt.Target(source='claude', session_id='a', cwd=None, state='ready')
    assert agent_prompt._pinned_risk(legacy) is not None
