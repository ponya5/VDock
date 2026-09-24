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
    agent_events._current_alert = None
    with app.test_client() as test_client:
        yield test_client
    agent_state.reset()
    agent_events._current_alert = None


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
    return tmp_path


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


def test_install_refuses_unparseable_settings(agent_home):
    settings_path = agent_home / '.claude' / 'settings.json'
    settings_path.parent.mkdir()
    settings_path.write_text('{broken', encoding='utf-8')
    with pytest.raises(agent_hooks.HookSettingsError):
        agent_hooks.install_hook('claude')
    assert settings_path.read_text(encoding='utf-8') == '{broken'


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


def test_hook_body_carries_the_session_id():
    claude_body = hook.build_body('claude', 'ready', {'hook_event_name': 'Stop', 'session_id': 'abc'})
    cursor_body = hook.build_body('cursor', 'ready', {'hook_event_name': 'stop', 'conversation_id': 'xyz'})
    assert claude_body['session_id'] == 'abc'
    assert cursor_body['session_id'] == 'xyz'


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


def test_cc_submit_is_a_session_gated_enter():
    submit = COMMANDS_BY_ID['cc_submit']
    assert submit.to_macro_steps() == [{'type': 'hotkey', 'keys': ['enter']}]
    assert submit.requires_session is True
