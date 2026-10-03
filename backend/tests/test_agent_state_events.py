"""Agent state (DL-064): hook mapping, hook installers, the events route and
state-aware keymap data.

The hook script runs inside Claude Code / Cursor, so its contract is strict:
map every lifecycle event correctly, never fail, and always answer Cursor's
beforeSubmitPrompt so a prompt is never blocked.
"""
import json
import subprocess
import sys

import pytest

from app import app
from integrations import agent_hooks, agent_state
from integrations.keymaps import COMMANDS_BY_ID, PROFILES_BY_ID
import routes.agent_events as agent_events
from scripts import vdock_agent_hook as hook


@pytest.fixture
def client():
    app.config['TESTING'] = True
    agent_state.reset()
    agent_events._alerts.clear()
    with app.test_client() as test_client:
        yield test_client
    agent_state.reset()
    agent_events._alerts.clear()


@pytest.fixture
def emitted(monkeypatch):
    events = []
    monkeypatch.setattr(agent_events, '_emitter',
                        lambda name, payload: events.append((name, payload)))
    return events


# ---------------------------------------------------------------------------
# Hook script mapping
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('event_name, expected_state', [
    ('SessionStart', 'ready'),
    ('Stop', 'ready'),
    ('UserPromptSubmit', 'working'),
    ('PreToolUse', 'working'),
    ('PostToolUse', 'working'),
    ('SessionEnd', 'ended'),
    ('SubagentStop', None),
])
def test_claude_events_map_to_states(event_name, expected_state):
    assert hook.map_event('claude', {'hook_event_name': event_name}) == expected_state


@pytest.mark.parametrize('payload, expected_state', [
    ({'notification_type': 'permission_prompt'}, 'permission'),
    ({'notification_type': 'idle_prompt'}, 'ready'),
    ({'message': 'Claude needs your permission to use Bash'}, 'permission'),
    ({'message': 'Claude is waiting for your input'}, 'ready'),
])
def test_claude_notification_splits_permission_from_idle(payload, expected_state):
    payload = {'hook_event_name': 'Notification', **payload}
    assert hook.map_event('claude', payload) == expected_state


@pytest.mark.parametrize('event_name, expected_state', [
    ('beforeSubmitPrompt', 'working'),
    ('afterAgentResponse', 'working'),
    ('stop', 'ready'),
    ('beforeShellExecution', None),
])
def test_cursor_events_map_to_states(event_name, expected_state):
    assert hook.map_event('cursor', {'hook_event_name': event_name}) == expected_state


@pytest.mark.parametrize('event_name, expected_state', [
    ('PreInvocation', 'working'),
    ('PreToolUse', 'working'),
    ('PostToolUse', 'working'),
    ('PostInvocation', 'working'),
    ('Stop', 'ready'),
    ('Whatever', None),
])
def test_antigravity_events_map_to_states(event_name, expected_state):
    # Antigravity pins the event in the installed command — the script
    # surfaces it as payload['event'] (hook_event_name stays empty).
    assert hook.map_event('antigravity', {'event': event_name}) == expected_state


def test_antigravity_event_can_also_come_from_hook_event_name():
    assert hook.map_event(
        'antigravity', {'hook_event_name': 'Stop'}) == 'ready'


def test_only_notifications_ask_for_attention():
    stop_body = hook.build_body('claude', 'ready', {'hook_event_name': 'Stop'})
    notification_body = hook.build_body(
        'claude', 'ready', {'hook_event_name': 'Notification', 'cwd': 'C:\\work\\vdock'},
    )
    assert stop_body['attention'] is False
    assert notification_body['attention'] is True
    assert notification_body['project'] == 'vdock'


def test_cursor_cwd_comes_from_workspace_roots():
    body = hook.build_body('cursor', 'working', {
        'hook_event_name': 'beforeSubmitPrompt', 'workspace_roots': ['/home/me/app/'],
    })
    assert body['cwd'] == '/home/me/app/'
    assert body['project'] == 'app'


def _run_hook(args, stdin_text):
    return subprocess.run(
        [sys.executable, str(agent_hooks.hook_script_path()), *args],
        input=stdin_text, capture_output=True, text=True, timeout=20,
    )


def test_hook_exits_zero_when_backend_is_down():
    completed = _run_hook(['--port', '1'], json.dumps({'hook_event_name': 'Stop'}))
    assert completed.returncode == 0


def test_hook_exits_zero_on_garbage_input_and_bad_flags():
    completed = _run_hook(['--port', 'not-a-number'], '{not json')
    assert completed.returncode == 0


def test_hook_always_lets_cursor_prompts_through():
    completed = _run_hook(
        ['--port', '1', '--source', 'cursor'],
        json.dumps({'hook_event_name': 'beforeSubmitPrompt'}),
    )
    assert completed.returncode == 0
    assert json.loads(completed.stdout.strip()) == {'continue': True}


# ---------------------------------------------------------------------------
# Installers
# ---------------------------------------------------------------------------

@pytest.fixture
def agent_home(tmp_path, monkeypatch):
    monkeypatch.setitem(agent_hooks._TARGETS, 'claude', agent_hooks._AgentHookTarget(
        lambda: tmp_path / '.claude' / 'settings.json',
        agent_hooks.claude_installed_events, agent_hooks._add_claude_events,
        agent_hooks.CLAUDE_HOOK_EVENTS,
    ))
    monkeypatch.setitem(agent_hooks._TARGETS, 'cursor', agent_hooks._AgentHookTarget(
        lambda: tmp_path / '.cursor' / 'hooks.json',
        agent_hooks.cursor_installed_events, agent_hooks._add_cursor_events,
        agent_hooks.CURSOR_HOOK_EVENTS,
    ))
    monkeypatch.setitem(agent_hooks._TARGETS, 'antigravity', agent_hooks._AgentHookTarget(
        lambda: tmp_path / '.gemini' / 'config' / 'hooks.json',
        agent_hooks.antigravity_installed_events, agent_hooks._add_antigravity_events,
        agent_hooks.AGY_HOOK_EVENTS,
    ))
    monkeypatch.setattr(agent_hooks, 'codex_config_path',
                        lambda: tmp_path / '.codex' / 'config.toml')
    return tmp_path


def test_codex_install_prepends_notify_and_keeps_existing_config(agent_home):
    config = agent_home / '.codex' / 'config.toml'
    config.parent.mkdir()
    config.write_text('model = "o4"\n\n[projects."x"]\ntrust = "trusted"\n', encoding='utf-8')
    result = agent_hooks.install_hook('codex')
    text = config.read_text(encoding='utf-8')
    assert result.installed and not result.already
    assert text.startswith('notify = [')
    assert '"--source", "codex"' in text
    assert 'model = "o4"' in text and '[projects."x"]' in text
    assert agent_hooks.hook_status('codex')['installed'] is True
    # Idempotent: a second install changes nothing.
    assert agent_hooks.install_hook('codex').already is True
    assert config.read_text(encoding='utf-8') == text


def test_codex_install_never_replaces_a_foreign_notify(agent_home):
    config = agent_home / '.codex' / 'config.toml'
    config.parent.mkdir()
    config.write_text('notify = ["say", "done"]\n', encoding='utf-8')
    with pytest.raises(agent_hooks.HookSettingsError):
        agent_hooks.install_hook('codex')
    assert config.read_text(encoding='utf-8') == 'notify = ["say", "done"]\n'
    assert agent_hooks.hook_status('codex')['installed'] is False


def test_codex_notify_in_a_table_is_not_a_top_level_notify(agent_home):
    config = agent_home / '.codex' / 'config.toml'
    config.parent.mkdir()
    config.write_text('[tui]\nnotify = true\n', encoding='utf-8')
    assert agent_hooks.install_hook('codex').installed is True
    assert config.read_text(encoding='utf-8').endswith('[tui]\nnotify = true\n')


def test_codex_turn_complete_means_ready_with_reply():
    payload = hook._codex_payload([json.dumps({
        'type': 'agent-turn-complete', 'thread-id': 'th1', 'cwd': 'C:/p/app',
        'input-messages': ['fix the bug'], 'last-assistant-message': 'Fixed.',
    })])
    assert hook.map_event('codex', payload) == 'ready'
    body = hook.build_body('codex', 'ready', payload)
    assert body['session_id'] == 'th1'
    assert body['project'] == 'app'
    assert body['prompt'] == 'fix the bug'
    assert body['reply'] == 'Fixed.'
    assert body['attention'] is False


def test_codex_ignores_unknown_events_and_garbage():
    assert hook.map_event('codex', hook._codex_payload(['not json'])) is None
    assert hook.map_event('codex', hook._codex_payload([json.dumps({'type': 'other'})])) is None


def test_claude_install_upgrades_a_dl045_install_and_keeps_foreign_hooks(agent_home):
    settings_path = agent_home / '.claude' / 'settings.json'
    settings_path.parent.mkdir()
    legacy_command = 'python "x/vdock_agent_hook.py" --port 5000'
    foreign_hook = {'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'lint.sh'}]}
    settings_path.write_text(json.dumps({
        'theme': 'dark',
        'hooks': {
            'Notification': [{'matcher': '', 'hooks': [{'type': 'command', 'command': legacy_command}]}],
            'Stop': [{'matcher': '', 'hooks': [{'type': 'command', 'command': legacy_command}]}],
            'PreToolUse': [foreign_hook],
        },
    }), encoding='utf-8')

    assert agent_hooks.hook_status('claude')['partial'] is True
    result = agent_hooks.install_hook('claude')

    written = json.loads(settings_path.read_text(encoding='utf-8'))
    assert set(result.added_events) == {
        'SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PostToolUse', 'SessionEnd',
    }
    assert written['theme'] == 'dark'
    assert written['hooks']['PreToolUse'][0] == foreign_hook
    assert len(written['hooks']['Notification']) == 1
    assert settings_path.with_suffix('.vdock-backup.json').exists()
    assert agent_hooks.hook_status('claude')['installed'] is True


def test_install_is_idempotent(agent_home):
    agent_hooks.install_hook('claude')
    second = agent_hooks.install_hook('claude')
    assert second.already is True
    assert second.added_events == ()


def test_cursor_install_creates_versioned_hooks_file(agent_home):
    agent_hooks.install_hook('cursor')
    written = json.loads((agent_home / '.cursor' / 'hooks.json').read_text(encoding='utf-8'))
    assert written['version'] == 1
    assert set(written['hooks']) == set(agent_hooks.CURSOR_HOOK_EVENTS)
    assert '--source cursor' in written['hooks']['stop'][0]['command']
    assert 'beforeShellExecution' not in written['hooks']


def test_antigravity_install_writes_named_entry(agent_home):
    hooks_path = agent_home / '.gemini' / 'config' / 'hooks.json'
    result = agent_hooks.install_hook('antigravity')
    assert result.installed and not result.already
    assert set(result.added_events) == set(agent_hooks.AGY_HOOK_EVENTS)

    written = json.loads(hooks_path.read_text(encoding='utf-8'))
    entry = written['vdock-agent-state']
    assert entry['enabled'] is True
    # Loop events carry a bare command entry pinning --event; tool events
    # carry the matcher+hooks shape.
    assert '--event Stop' in entry['Stop'][0]['command']
    assert '--source antigravity' in entry['Stop'][0]['command']
    pre_tool = entry['PreToolUse'][0]
    assert 'matcher' in pre_tool
    assert '--event PreToolUse' in pre_tool['hooks'][0]['command']
    assert agent_hooks.hook_status('antigravity')['installed'] is True


def test_antigravity_install_merges_and_is_idempotent(agent_home):
    hooks_path = agent_home / '.gemini' / 'config' / 'hooks.json'
    hooks_path.parent.mkdir(parents=True)
    hooks_path.write_text(json.dumps({
        'my-linter': {'PostToolUse': [{'matcher': 'run_command', 'hooks': [
            {'type': 'command', 'command': 'lint.sh'}]}]},
    }), encoding='utf-8')

    agent_hooks.install_hook('antigravity')
    written = json.loads(hooks_path.read_text(encoding='utf-8'))
    assert written['my-linter']['PostToolUse'][0]['hooks'][0]['command'] == 'lint.sh'
    assert set(written['vdock-agent-state']) >= set(agent_hooks.AGY_HOOK_EVENTS)
    assert hooks_path.with_suffix('.vdock-backup.json').exists()

    second = agent_hooks.install_hook('antigravity')
    assert second.already is True and second.added_events == ()


def test_antigravity_partial_install_is_detected(agent_home):
    hooks_path = agent_home / '.gemini' / 'config' / 'hooks.json'
    hooks_path.parent.mkdir(parents=True)
    hooks_path.write_text(json.dumps({
        'vdock-agent-state': {'enabled': True, 'Stop': [
            {'type': 'command',
             'command': 'python "x/vdock_agent_hook.py" --event Stop'}]},
    }), encoding='utf-8')
    status = agent_hooks.hook_status('antigravity')
    assert status['partial'] is True and status['installed'] is False
    agent_hooks.install_hook('antigravity')
    assert agent_hooks.hook_status('antigravity')['installed'] is True


def test_hook_status_all_reports_every_agent(client, agent_home):
    response = client.get('/api/agent-events/hook-status?agent=all')
    assert response.status_code == 200
    agents = response.get_json()['agents']
    assert set(agents) == {'claude', 'cursor', 'antigravity', 'codex'}
    agent_hooks.install_hook('antigravity')
    agents = client.get('/api/agent-events/hook-status?agent=all').get_json()['agents']
    assert agents['antigravity']['installed'] is True
    assert agents['claude']['installed'] is False


def test_install_refuses_unparseable_settings(agent_home):
    settings_path = agent_home / '.claude' / 'settings.json'
    settings_path.parent.mkdir()
    settings_path.write_text('{broken', encoding='utf-8')
    with pytest.raises(agent_hooks.HookSettingsError):
        agent_hooks.install_hook('claude')
    assert settings_path.read_text(encoding='utf-8') == '{broken'


# --- Uninstall ---------------------------------------------------------------

_FOREIGN_JSON = {
    'claude': {'theme': 'dark', 'hooks': {
        'PreToolUse': [{'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'lint.sh'}]}],
        'Stop': [{'matcher': '', 'hooks': [{'type': 'command', 'command': 'notify.sh'}]}],
    }},
    'cursor': {'version': 1, 'hooks': {
        'stop': [{'command': 'mine.sh'}],
        'beforeShellExecution': [{'command': 'gate.sh'}],
    }},
    'antigravity': {'my-linter': {'PostToolUse': [{'matcher': 'run_command', 'hooks': [
        {'type': 'command', 'command': 'lint.sh'}]}]}},
}
_JSON_PATHS = {
    'claude': ('.claude', 'settings.json'),
    'cursor': ('.cursor', 'hooks.json'),
    'antigravity': ('.gemini', 'config', 'hooks.json'),
}


@pytest.mark.parametrize('agent', sorted(_FOREIGN_JSON))
def test_uninstall_restores_the_pre_install_json(agent_home, agent):
    path = agent_home.joinpath(*_JSON_PATHS[agent])
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(_FOREIGN_JSON[agent]), encoding='utf-8')
    agent_hooks.install_hook(agent)
    assert agent_hooks.hook_status(agent)['installed'] is True

    result = agent_hooks.uninstall_hook(agent)

    assert result.removed and not result.already
    assert json.loads(path.read_text(encoding='utf-8')) == _FOREIGN_JSON[agent]
    assert agent_hooks.hook_status(agent)['installed'] is False
    assert agent_hooks.hook_status(agent)['partial'] is False


@pytest.mark.parametrize('agent', sorted(_FOREIGN_JSON))
def test_uninstall_of_a_vdock_only_file_leaves_a_valid_object(agent_home, agent):
    path = agent_home.joinpath(*_JSON_PATHS[agent])
    agent_hooks.install_hook(agent)
    agent_hooks.uninstall_hook(agent)
    left = json.loads(path.read_text(encoding='utf-8'))
    assert left in ({}, {'version': 1})
    assert path.exists()


def test_uninstall_removes_a_partial_dl045_install(agent_home):
    path = agent_home / '.claude' / 'settings.json'
    path.parent.mkdir()
    command = 'python "x/vdock_agent_hook.py" --port 5000'
    path.write_text(json.dumps({'hooks': {'Stop': [
        {'matcher': '', 'hooks': [{'type': 'command', 'command': command}]}]}}),
        encoding='utf-8')
    assert agent_hooks.uninstall_hook('claude').removed is True
    assert json.loads(path.read_text(encoding='utf-8')) == {}


def test_uninstall_keeps_a_foreign_hook_in_the_same_claude_entry(agent_home):
    path = agent_home / '.claude' / 'settings.json'
    path.parent.mkdir()
    ours = {'type': 'command', 'command': 'python "x/vdock_agent_hook.py"'}
    theirs = {'type': 'command', 'command': 'mine.sh'}
    path.write_text(json.dumps({'hooks': {'Stop': [
        {'matcher': '', 'hooks': [theirs, ours]}]}}), encoding='utf-8')
    agent_hooks.uninstall_hook('claude')
    assert json.loads(path.read_text(encoding='utf-8')) == {
        'hooks': {'Stop': [{'matcher': '', 'hooks': [theirs]}]}}


def test_codex_uninstall_restores_the_pre_install_toml_exactly(agent_home):
    config = agent_home / '.codex' / 'config.toml'
    config.parent.mkdir()
    original = '# my config\nmodel = "o4"\n\n[projects."x"]\ntrust = "trusted"\n'
    config.write_text(original, encoding='utf-8', newline='')
    agent_hooks.install_hook('codex')
    result = agent_hooks.uninstall_hook('codex')
    assert result.removed is True
    assert config.read_text(encoding='utf-8') == original
    assert agent_hooks.hook_status('codex')['installed'] is False


def test_codex_uninstall_leaves_a_foreign_notify(agent_home):
    config = agent_home / '.codex' / 'config.toml'
    config.parent.mkdir()
    config.write_text('notify = ["say", "done"]\n', encoding='utf-8')
    result = agent_hooks.uninstall_hook('codex')
    assert result.already is True and result.removed is False
    assert config.read_text(encoding='utf-8') == 'notify = ["say", "done"]\n'


@pytest.mark.parametrize('agent', ['claude', 'cursor', 'antigravity', 'codex'])
def test_uninstall_when_not_installed_writes_nothing(agent_home, agent):
    result = agent_hooks.uninstall_hook(agent)
    assert result.already is True and result.removed is False
    assert not any(agent_home.rglob('*'))  # no file, folder or backup created


@pytest.mark.parametrize('agent', sorted(_FOREIGN_JSON))
def test_second_uninstall_is_a_no_op(agent_home, agent):
    agent_hooks.install_hook(agent)
    agent_hooks.uninstall_hook(agent)
    path = agent_home.joinpath(*_JSON_PATHS[agent])
    after_first = path.read_text(encoding='utf-8')
    second = agent_hooks.uninstall_hook(agent)
    assert second.already is True and second.removed is False
    assert path.read_text(encoding='utf-8') == after_first


@pytest.mark.parametrize('agent', sorted(_FOREIGN_JSON))
def test_uninstall_refuses_unparseable_settings(agent_home, agent):
    path = agent_home.joinpath(*_JSON_PATHS[agent])
    path.parent.mkdir(parents=True)
    path.write_text('{broken', encoding='utf-8')
    with pytest.raises(agent_hooks.HookSettingsError):
        agent_hooks.uninstall_hook(agent)
    assert path.read_text(encoding='utf-8') == '{broken'


def test_uninstall_backs_up_before_modifying(agent_home):
    path = agent_home / '.claude' / 'settings.json'
    agent_hooks.install_hook('claude')
    installed_text = path.read_text(encoding='utf-8')
    agent_hooks.uninstall_hook('claude')
    assert path.with_suffix('.vdock-backup.json').read_text(encoding='utf-8') == installed_text
    assert not list(path.parent.glob('*.tmp'))


def test_uninstall_route_removes_and_reports(client, agent_home):
    agent_hooks.install_hook('cursor')
    body = client.post('/api/agent-events/uninstall-hook?agent=cursor').get_json()
    assert body['success'] is True and body['removed'] is True and body['already'] is False
    again = client.post('/api/agent-events/uninstall-hook?agent=cursor').get_json()
    assert again['already'] is True and again['removed'] is False
    statuses = client.get('/api/agent-events/hook-status?agent=all').get_json()['agents']
    assert statuses['cursor']['installed'] is False


def test_uninstall_route_refuses_unparseable_settings(client, agent_home):
    path = agent_home / '.claude' / 'settings.json'
    path.parent.mkdir()
    path.write_text('{broken', encoding='utf-8')
    response = client.post('/api/agent-events/uninstall-hook?agent=claude')
    assert response.status_code == 400
    assert path.read_text(encoding='utf-8') == '{broken'


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

def test_state_post_records_and_broadcasts(client, emitted):
    response = client.post('/api/agent-events', json={
        'source': 'claude', 'state': 'working', 'cwd': 'C:/w/app',
    })
    assert response.status_code == 200

    states = client.get('/api/agent-events/states').get_json()['states']
    assert states['claude']['state'] == 'working'
    assert ('agent_state', {'states': agent_state.snapshot()}) in emitted


def test_attention_notification_raises_alert_and_next_turn_clears_it(client, emitted):
    client.post('/api/agent-events', json={
        'source': 'claude', 'state': 'permission', 'attention': True,
        'message': 'Claude needs your permission to use Bash',
    })
    assert client.get('/api/agent-events/current').get_json()['alert']['source'] == 'claude'

    client.post('/api/agent-events', json={'source': 'claude', 'state': 'working', 'attention': False})
    assert client.get('/api/agent-events/current').get_json()['alert'] is None


def test_plain_stop_does_not_raise_alert(client, emitted):
    client.post('/api/agent-events', json={
        'source': 'claude', 'state': 'ready', 'attention': False,
        'message': 'Waiting for your prompt',
    })
    assert client.get('/api/agent-events/current').get_json()['alert'] is None


def test_idle_notification_on_never_prompted_session_stays_quiet(client, emitted):
    """DL-105: a just-launched agent is always idle — its idle
    notification is not 'waiting for you' until a prompt was sent."""
    client.post('/api/agent-events', json={
        'source': 'claude', 'state': 'ready', 'attention': True,
        'message': 'Claude Code is waiting for your input',
    })
    assert client.get('/api/agent-events/current').get_json()['alert'] is None
    assert agent_state.get('claude')['prompted'] is False


def test_idle_notification_alerts_once_the_session_was_prompted(client, emitted):
    client.post('/api/agent-events', json={
        'source': 'claude', 'state': 'working', 'prompt': 'fix the bug',
        'session_id': 's1',
    })
    client.post('/api/agent-events', json={
        'source': 'claude', 'state': 'ready', 'attention': True,
        'session_id': 's1',
    })
    assert client.get('/api/agent-events/current').get_json()['alert'] is not None
    assert agent_state.get('claude')['prompted'] is True


def test_prompted_flag_counts_without_prompt_text(client, emitted):
    """The hook flags prompted on events that imply a prompt even when
    no prompt text rides along (tool calls, a finished turn)."""
    client.post('/api/agent-events', json={
        'source': 'claude', 'state': 'ready', 'attention': True, 'prompted': True,
    })
    assert client.get('/api/agent-events/current').get_json()['alert'] is not None


def test_permission_alert_bypasses_the_prompted_gate(client, emitted):
    """Permission dialogs are real blockers (and legacy 'waiting' events
    map here) — they alert regardless of prompt history."""
    client.post('/api/agent-events', json={
        'source': 'claude', 'state': 'permission', 'attention': True,
    })
    assert client.get('/api/agent-events/current').get_json()['alert'] is not None


def test_legacy_waiting_and_clear_events_still_work(client, emitted):
    client.post('/api/agent-events', json={'source': 'claude', 'event': 'waiting'})
    assert client.get('/api/agent-events/current').get_json()['alert'] is not None
    assert agent_state.get('claude')['state'] == 'permission'

    client.post('/api/agent-events', json={'source': 'claude', 'event': 'clear'})
    assert client.get('/api/agent-events/current').get_json()['alert'] is None
    assert agent_state.get('claude')['state'] == 'ready'


def test_session_end_removes_state(client, emitted):
    client.post('/api/agent-events', json={'source': 'cursor', 'state': 'ready'})
    client.post('/api/agent-events', json={'source': 'cursor', 'state': 'ended'})
    assert 'cursor' not in client.get('/api/agent-events/states').get_json()['states']


def test_ending_one_session_keeps_the_others(client, emitted):
    client.post('/api/agent-events', json={'source': 'claude', 'state': 'ready', 'session_id': 'interactive'})
    client.post('/api/agent-events', json={'source': 'claude', 'state': 'working', 'session_id': 'headless-job'})
    client.post('/api/agent-events', json={'source': 'claude', 'state': 'ended', 'session_id': 'headless-job'})

    claude = client.get('/api/agent-events/states').get_json()['states']['claude']
    assert claude['state'] == 'ready'
    assert claude['session_id'] == 'interactive'
    assert claude['session_count'] == 1


def test_a_pending_permission_prompt_outranks_newer_activity(client, emitted):
    client.post('/api/agent-events', json={
        'source': 'claude', 'state': 'permission', 'attention': True, 'session_id': 'blocked',
    })
    client.post('/api/agent-events', json={'source': 'claude', 'state': 'working', 'session_id': 'other'})
    client.post('/api/agent-events', json={'source': 'claude', 'state': 'ended', 'session_id': 'other'})

    assert agent_state.get('claude')['state'] == 'permission'
    assert client.get('/api/agent-events/current').get_json()['alert'] is not None


# ---------------------------------------------------------------------------
# DL-119 — per-source alerts
# ---------------------------------------------------------------------------

def _raise(client, source, message='needs you', **kw):
    return client.post('/api/agent-events', json={
        'source': source, 'state': 'permission', 'attention': True,
        'message': message, **kw,
    })


def test_two_agents_keep_their_own_alerts_newest_first(client, emitted):
    _raise(client, 'claude', 'Claude blocked on Bash')
    _raise(client, 'cursor', 'Cursor blocked on Write')

    body = client.get('/api/agent-events/current').get_json()
    assert [a['source'] for a in body['alerts']] == ['cursor', 'claude']
    # Legacy field keeps pointing at the newest alert.
    assert body['alert']['source'] == 'cursor'

    broadcast = [p for n, p in emitted if n == 'agent_alert'][-1]
    assert broadcast['alert']['source'] == 'cursor'
    assert [a['source'] for a in broadcast['alerts']] == ['cursor', 'claude']


def test_a_fresh_alert_replaces_the_same_sources_old_one(client, emitted):
    _raise(client, 'claude', 'first prompt')
    _raise(client, 'claude', 'second prompt')

    body = client.get('/api/agent-events/current').get_json()
    assert len(body['alerts']) == 1
    assert body['alert']['message'] == 'second prompt'


def test_delete_with_source_clears_only_that_alert(client, emitted):
    _raise(client, 'claude')
    _raise(client, 'cursor')

    response = client.delete('/api/agent-events/current?source=claude')
    assert response.status_code == 200

    body = client.get('/api/agent-events/current').get_json()
    assert [a['source'] for a in body['alerts']] == ['cursor']
    assert body['alert']['source'] == 'cursor'


def test_delete_without_source_clears_everything(client, emitted):
    _raise(client, 'claude')
    _raise(client, 'cursor')

    client.delete('/api/agent-events/current')
    body = client.get('/api/agent-events/current').get_json()
    assert body['alert'] is None and body['alerts'] == []


def test_a_state_event_clears_only_its_own_sources_alert(client, emitted):
    _raise(client, 'claude')
    _raise(client, 'cursor')

    client.post('/api/agent-events', json={
        'source': 'claude', 'state': 'working', 'attention': False,
    })
    body = client.get('/api/agent-events/current').get_json()
    assert [a['source'] for a in body['alerts']] == ['cursor']


def test_an_alert_still_expires_on_its_own(client, emitted, monkeypatch):
    _raise(client, 'claude')
    _raise(client, 'cursor')

    real_time = agent_events.time.time
    monkeypatch.setattr(agent_events.time, 'time',
                        lambda: real_time() + agent_events.ALERT_TTL_SECONDS + 1)
    body = client.get('/api/agent-events/current').get_json()
    assert body['alert'] is None and body['alerts'] == []


def test_hook_body_flags_prompt_implying_events():
    """DL-105: every event except SessionStart/Notification means the
    session was prompted — Cursor/Antigravity events only exist mid-run."""
    promptless = hook.build_body('claude', 'ready', {'hook_event_name': 'SessionStart'})
    notify = hook.build_body('claude', 'ready', {'hook_event_name': 'Notification'})
    assert promptless['prompted'] is False
    assert notify['prompted'] is False
    for source, event in [
        ('claude', 'UserPromptSubmit'), ('claude', 'PreToolUse'),
        ('claude', 'Stop'), ('cursor', 'stop'),
        ('cursor', 'beforeSubmitPrompt'), ('antigravity', 'PreInvocation'),
    ]:
        body = hook.build_body(source, 'ready', {'hook_event_name': event})
        assert body['prompted'] is True, (source, event)


def test_hook_body_carries_the_session_id():
    claude_body = hook.build_body('claude', 'ready', {'hook_event_name': 'Stop', 'session_id': 'abc'})
    cursor_body = hook.build_body('cursor', 'ready', {'hook_event_name': 'stop', 'conversation_id': 'xyz'})
    assert claude_body['session_id'] == 'abc'
    assert cursor_body['session_id'] == 'xyz'


# ---------------------------------------------------------------------------
# Conversation (DL-065 mobile console)
# ---------------------------------------------------------------------------

def _write_transcript(path, entries):
    path.write_text('\n'.join(json.dumps(entry) for entry in entries) + '\n', encoding='utf-8')
    return str(path)


def test_hook_sends_the_submitted_prompt():
    body = hook.build_body('claude', 'working', {
        'hook_event_name': 'UserPromptSubmit', 'prompt': '  Fix the login bug  ',
    })
    assert body['prompt'] == 'Fix the login bug'
    assert 'reply' not in body


def test_hook_prefers_the_reported_last_assistant_message(tmp_path):
    transcript_path = _write_transcript(tmp_path / 't.jsonl', [
        {'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': 'from transcript'}]}},
    ])
    body = hook.build_body('claude', 'ready', {
        'hook_event_name': 'Stop', 'last_assistant_message': 'reported',
        'transcript_path': transcript_path,
    })
    assert body['reply'] == 'reported'


def test_hook_reads_the_last_assistant_text_from_the_transcript(tmp_path):
    transcript_path = _write_transcript(tmp_path / 't.jsonl', [
        {'type': 'user', 'message': {'content': 'hi'}},
        {'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': 'Older reply'}]}},
        {'type': 'assistant', 'message': {'content': [
            {'type': 'text', 'text': 'Done.'}, {'type': 'text', 'text': 'Tests pass.'},
        ]}},
        {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Bash'}]}},
    ])
    body = hook.build_body('claude', 'ready', {'hook_event_name': 'Stop', 'transcript_path': transcript_path})
    assert body['reply'] == 'Done.\nTests pass.'


def test_hook_survives_a_missing_transcript(tmp_path):
    body = hook.build_body('claude', 'ready', {
        'hook_event_name': 'Stop', 'transcript_path': str(tmp_path / 'missing.jsonl'),
    })
    assert 'reply' not in body


def test_hook_keeps_the_end_of_a_long_reply():
    long_reply = 'start ' + 'x' * hook.MAX_REPLY_CHARS + ' summary'
    body = hook.build_body('claude', 'ready', {'hook_event_name': 'Stop', 'last_assistant_message': long_reply})
    assert len(body['reply']) == hook.MAX_REPLY_CHARS
    assert body['reply'].startswith('…')
    assert body['reply'].endswith(' summary')


def test_cursor_hook_sends_prompt_and_reply():
    prompt_body = hook.build_body('cursor', 'working', {'hook_event_name': 'beforeSubmitPrompt', 'prompt': 'Refactor'})
    reply_body = hook.build_body('cursor', 'working', {'hook_event_name': 'afterAgentResponse', 'text': 'Refactored.'})
    assert prompt_body['prompt'] == 'Refactor'
    assert reply_body['reply'] == 'Refactored.'


def test_conversation_carries_over_and_a_new_prompt_clears_the_old_reply(client, emitted):
    client.post('/api/agent-events', json={'source': 'claude', 'state': 'working', 'prompt': 'First'})
    client.post('/api/agent-events', json={'source': 'claude', 'state': 'working', 'message': 'Using Bash'})
    client.post('/api/agent-events', json={'source': 'claude', 'state': 'ready', 'reply': 'Answer one'})
    claude = agent_state.get('claude')
    assert (claude['prompt'], claude['reply']) == ('First', 'Answer one')

    client.post('/api/agent-events', json={'source': 'claude', 'state': 'working', 'prompt': 'Second'})
    claude = agent_state.get('claude')
    assert (claude['prompt'], claude['reply']) == ('Second', '')


def test_conversation_is_capped():
    entry = agent_state.record('claude', 'ready', prompt='p' * 5000, reply='r' * 9000)
    assert len(entry['prompt']) == agent_state.MAX_PROMPT_CHARS
    assert len(entry['reply']) == agent_state.MAX_REPLY_CHARS


def test_agent_profiles_declare_their_prompt_command():
    assert PROFILES_BY_ID['claude-code'].to_dict()['prompt_command'] == 'cc_prompt'
    assert PROFILES_BY_ID['devin'].to_dict()['prompt_command'] == 'devin_prompt'
    assert PROFILES_BY_ID['cursor'].to_dict()['prompt_command'] == 'cursor_followup'
    for profile in PROFILES_BY_ID.values():
        if profile.prompt_command:
            assert COMMANDS_BY_ID[profile.prompt_command].types_text is not None


def test_unknown_state_is_rejected(client):
    response = client.post('/api/agent-events', json={'source': 'claude', 'state': 'dancing'})
    assert response.status_code == 400


def test_states_expire(client, monkeypatch):
    agent_state.record('claude', 'ready')
    real_time = agent_state.time.time
    monkeypatch.setattr(agent_state.time, 'time',
                        lambda: real_time() + agent_state.STATE_TTL_SECONDS + 1)
    assert agent_state.snapshot() == {}


def test_hook_routes_reject_unknown_agent(client):
    assert client.get('/api/agent-events/hook-status?agent=vim').status_code == 400
    assert client.post('/api/agent-events/install-hook?agent=vim').status_code == 400
    assert client.post('/api/agent-events/uninstall-hook?agent=vim').status_code == 400


# ---------------------------------------------------------------------------
# Keymap data
# ---------------------------------------------------------------------------

def test_every_state_action_references_a_real_command_of_its_profile():
    for profile in PROFILES_BY_ID.values():
        profile_command_ids = {command.id for command in profile.commands}
        for _state, actions in profile.state_actions:
            for action in actions:
                assert action.command_id in profile_command_ids, (profile.id, action)


def test_agent_profiles_expose_state_actions():
    serialised = PROFILES_BY_ID['claude-code'].to_dict()
    assert serialised['status_source'] == 'claude'
    assert set(serialised['state_actions']) == {'ready', 'working', 'permission', 'unknown'}
    assert serialised['state_actions']['permission'][0] == {'id': 'cc_accept', 'label': 'Approve'}


def test_multiline_prompt_uses_newline_chord_and_submits_once():
    steps = COMMANDS_BY_ID['cc_prompt'].to_macro_steps('Explain:\n\ndef f():\n  pass')
    enter_presses = [step for step in steps if step.get('keys') == ['enter']]
    newline_presses = [step for step in steps if step.get('keys') == ['ctrl', 'j']]
    typed = [step['text'] for step in steps if step['type'] == 'text']

    assert len(enter_presses) == 1
    assert steps[-1] == {'type': 'hotkey', 'keys': ['enter']}
    assert len(newline_presses) == 3
    assert typed == ['Explain:', 'def f():', '  pass']
    assert all('\n' not in text for text in typed)


def test_tab_indentation_is_typed_as_spaces_into_terminal_agents():
    steps = COMMANDS_BY_ID['cc_prompt'].to_macro_steps('def f():\n\treturn 1')
    typed = [step['text'] for step in steps if step['type'] == 'text']

    assert typed == ['def f():', '    return 1']


def test_clipboard_prompt_refuses_an_empty_clipboard(mocker):
    from integrations import context
    from integrations.claude_code_pack import Plugin as ClaudeCodePlugin
    mocker.patch.object(context, 'clipboard_text', return_value='  ')
    send = mocker.patch('integrations.editor_base.send')

    result = ClaudeCodePlugin().execute_action(
        'cc_prompt', {'text': 'Explain:\n\n{clipboard}'})

    assert result['success'] is False
    assert result['message'] == 'Copy some code first'
    send.assert_not_called()


def test_cc_submit_is_a_session_gated_enter():
    submit = COMMANDS_BY_ID['cc_submit']
    assert submit.to_macro_steps() == [{'type': 'hotkey', 'keys': ['enter']}]
    assert submit.requires_session is True


def test_install_and_uninstall_hook_are_localhost_only(client, agent_home):
    for route in ('install-hook', 'uninstall-hook'):
        resp = client.post(f'/api/agent-events/{route}?agent=claude',
                           environ_overrides={'REMOTE_ADDR': '192.168.1.50'})
        assert resp.status_code == 403
    assert agent_hooks.hook_status('claude')['installed'] is False
