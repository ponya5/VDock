"""MCP endpoint (DL-121): JSON-RPC 2.0 over POST /api/mcp.

The blueprint is exercised on a bare Flask app — app.py does not register
mcp_bp yet (the orchestrator wires it), and importing app here would drag in
the whole server. Executor/emitter arrive through the same
set_executor/set_emitter seams app.py will use.
"""
import json
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask  # noqa: E402

from actions.base_action import ActionResult  # noqa: E402
from auth import AuthManager  # noqa: E402
from config import Config  # noqa: E402
from integrations import agent_state  # noqa: E402
from routes import mcp  # noqa: E402


def _rpc(client, body, **kwargs):
    kwargs.setdefault('content_type', 'application/json')
    return client.post('/api/mcp', data=json.dumps(body), **kwargs)


def _result(resp):
    body = json.loads(resp.get_data())
    assert 'error' not in body, body
    return body['result']


def _tool_call(client, name, arguments=None, req_id=1):
    params = {'name': name}
    if arguments is not None:
        params['arguments'] = arguments
    resp = _rpc(client, {'jsonrpc': '2.0', 'id': req_id,
                         'method': 'tools/call', 'params': params})
    return _result(resp)


def _tool_payload(result):
    assert result['content'][0]['type'] == 'text'
    return result['structuredContent']


class FakeExecutor:
    """Same shape as ActionExecutor: .execute_action({type, config})."""

    def __init__(self, succeed=True):
        self.calls = []
        self.succeed = succeed

    def execute_action(self, action_data):
        self.calls.append(action_data)
        return ActionResult(self.succeed, 'ran it', {'echo': action_data})


@pytest.fixture
def deck_dir(tmp_path, monkeypatch):
    """Point Config at a temp DATA_DIR with one seeded profile."""
    profiles_dir = tmp_path / 'profiles'
    profiles_dir.mkdir()
    profile = {
        'id': 'prof-1', 'name': 'Test Deck', 'description': '',
        'pages': [],
        'scenes': [{
            'id': 'scene-1', 'name': 'Main', 'isActive': True,
            'pages': [{
                'id': 'page-1', 'name': 'Page 1',
                'buttons': [
                    {'id': 'btn-mute', 'label': 'Mute', 'enabled': True,
                     'action': {'type': 'cross_platform',
                                'config': {'action': 'volume_mute'}}},
                    {'id': 'btn-off', 'label': 'Disabled', 'enabled': False,
                     'action': {'type': 'url',
                                'config': {'url': 'http://x'}}},
                ],
            }],
        }, {
            'id': 'scene-2', 'name': 'Claude', 'isActive': False,
            'pages': [{
                'id': 'page-2', 'name': 'Page 1',
                'buttons': [
                    {'id': 'btn-submit', 'label': 'Submit', 'enabled': True,
                     'action': {'type': 'command',
                                'config': {'command': 'x'}}},
                ],
            }],
        }],
        'dockedButtons': [
            {'id': 'dock-1', 'label': 'Docked Go',
             'action': {'type': 'url', 'config': {'url': 'http://y'}}},
        ],
    }
    (profiles_dir / 'prof-1.json').write_text(json.dumps(profile),
                                            encoding='utf-8')
    monkeypatch.setattr(Config, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(Config, 'PROFILES_DIR', profiles_dir)
    return tmp_path


@pytest.fixture
def client(monkeypatch):
    """Bare app + clean seams; the executor is injected per-test."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(mcp.mcp_bp)
    monkeypatch.setattr(mcp, '_executor', None)
    monkeypatch.setattr(mcp, '_emitter', None)
    monkeypatch.setattr(mcp, '_now_playing', False)  # service absent
    agent_state.reset()
    with app.test_client() as test_client:
        yield test_client
    agent_state.reset()


@pytest.fixture
def emitted(monkeypatch):
    events = []
    monkeypatch.setattr(mcp, '_emitter',
                        lambda name, payload: events.append((name, payload)))
    return events


@pytest.fixture
def executor(monkeypatch):
    fake = FakeExecutor()
    monkeypatch.setattr(mcp, '_executor', fake)
    return fake


# ---------------------------------------------------------------------------
# Protocol lifecycle
# ---------------------------------------------------------------------------

def test_initialize(client):
    result = _result(_rpc(client, {'jsonrpc': '2.0', 'id': 1,
                                   'method': 'initialize',
                                   'params': {'protocolVersion': '2025-06-18'}}))
    assert result['protocolVersion'] == '2025-06-18'
    assert result['capabilities']['tools'] == {'listChanged': False}
    assert result['serverInfo'] == {'name': 'vdock', 'version': '2.1.0'}


def test_ping(client):
    assert _result(_rpc(client, {'jsonrpc': '2.0', 'id': 'p',
                                 'method': 'ping'})) == {}


def test_notifications_initialized_acks_null_when_sent_as_request(client):
    body = json.loads(_rpc(client, {'jsonrpc': '2.0', 'id': 7, 'method':
                                    'notifications/initialized'}).get_data())
    assert body['result'] is None and 'error' not in body


def test_notification_without_id_gets_no_response(client):
    resp = _rpc(client, {'jsonrpc': '2.0', 'method': 'notifications/initialized'})
    assert resp.status_code == 202
    assert resp.get_data() == b''


def test_get_returns_405_json(client):
    resp = client.get('/api/mcp')
    assert resp.status_code == 405
    assert 'POST' in resp.get_json()['error']
    assert resp.headers['Allow'] == 'POST'


# ---------------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------------

def test_batch_requests(client):
    resp = _rpc(client, [
        {'jsonrpc': '2.0', 'id': 1, 'method': 'ping'},
        {'jsonrpc': '2.0', 'id': 2, 'method': 'ping'},
        {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/list'},
    ])
    replies = json.loads(resp.get_data())
    assert [r['id'] for r in replies] == [1, 2, 3]
    assert replies[0]['result'] == {}
    assert 'tools' in replies[2]['result']


def test_batch_with_notifications_only_answers_202(client):
    resp = _rpc(client, [
        {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
        {'jsonrpc': '2.0', 'method': 'notifications/cancelled'},
    ])
    assert resp.status_code == 202


def test_batch_mixes_replies_and_notifications(client):
    replies = json.loads(_rpc(client, [
        {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
        {'jsonrpc': '2.0', 'id': 9, 'method': 'ping'},
    ]).get_data())
    assert replies == [{'jsonrpc': '2.0', 'id': 9, 'result': {}}]


def test_batch_collects_per_message_errors(client):
    replies = json.loads(_rpc(client, [
        {'jsonrpc': '2.0', 'id': 1, 'method': 'nope'},
        {'not': 'rpc'},
        {'jsonrpc': '2.0', 'id': 2, 'method': 'ping'},
    ]).get_data())
    assert replies[0]['error']['code'] == -32601
    assert replies[1]['error']['code'] == -32600
    assert replies[2]['result'] == {}


# ---------------------------------------------------------------------------
# JSON-RPC error codes
# ---------------------------------------------------------------------------

def test_garbage_body_is_parse_error(client):
    resp = client.post('/api/mcp', data='{not json',
                       content_type='application/json')
    assert json.loads(resp.get_data())['error']['code'] == -32700


def test_missing_envelope_fields_is_invalid_request(client):
    body = json.loads(_rpc(client, {'id': 1, 'method': 'ping'}).get_data())
    assert body['error']['code'] == -32600
    body = json.loads(_rpc(client, {'jsonrpc': '2.0', 'id': 1}).get_data())
    assert body['error']['code'] == -32600
    body = json.loads(_rpc(client, 'scalar').get_data())
    assert body['error']['code'] == -32600
    body = json.loads(_rpc(client, []).get_data())
    assert body['error']['code'] == -32600


def test_unknown_method(client):
    body = json.loads(_rpc(client, {'jsonrpc': '2.0', 'id': 1,
                                    'method': 'resources/list'}).get_data())
    assert body['error']['code'] == -32601


def test_invalid_params(client):
    for params in ({}, {'name': 42}, {'name': 'ping',
                                      'arguments': [1, 2]}):
        body = json.loads(_rpc(client, {
            'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
            'params': params}).get_data())
        assert body['error']['code'] == -32602, params


def test_unknown_tool_is_invalid_params(client):
    body = json.loads(_rpc(client, {
        'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
        'params': {'name': 'explode'}}).get_data())
    assert body['error']['code'] == -32602


# ---------------------------------------------------------------------------
# tools/list + tools/call
# ---------------------------------------------------------------------------

def test_tools_list_shape(client):
    tools = _result(_rpc(client, {'jsonrpc': '2.0', 'id': 1,
                                  'method': 'tools/list'}))['tools']
    by_name = {t['name']: t for t in tools}
    for name in ('deck_info', 'list_scenes', 'list_buttons', 'press_button',
                 'run_action', 'switch_scene', 'show_notification',
                 'get_volume', 'set_volume', 'get_now_playing',
                 'get_agent_states'):
        assert name in by_name
    for tool in tools:
        assert tool['inputSchema']['type'] == 'object'
        assert tool['description']


def test_deck_info(client, deck_dir):
    payload = _tool_payload(_tool_call(client, 'deck_info'))
    assert payload['version'] == '2.1.0'
    assert payload['profile'] == {'id': 'prof-1', 'name': 'Test Deck'}
    assert payload['scenes'] == 2
    assert payload['buttons'] == 4      # 3 scene buttons + 1 docked
    assert payload['active_scene'] == 'Main'


def test_list_scenes(client, deck_dir):
    payload = _tool_payload(_tool_call(client, 'list_scenes'))
    names = {s['name'] for s in payload['scenes']}
    assert names == {'Main', 'Claude'}
    main = next(s for s in payload['scenes'] if s['name'] == 'Main')
    assert main['active'] is True and main['page_count'] == 1


def test_list_buttons_and_scene_filter(client, deck_dir):
    payload = _tool_payload(_tool_call(client, 'list_buttons'))
    ids = {b['id'] for b in payload['buttons']}
    assert {'btn-mute', 'btn-off', 'btn-submit', 'dock-1'} <= ids
    mute = next(b for b in payload['buttons'] if b['id'] == 'btn-mute')
    assert mute['label'] == 'Mute'
    assert mute['action'] == {'type': 'cross_platform'}

    filtered = _tool_payload(
        _tool_call(client, 'list_buttons', {'scene': 'claude'}))
    assert [b['id'] for b in filtered['buttons']] == ['btn-submit']

    missing = _tool_call(client, 'list_buttons', {'scene': 'nope'})
    assert missing['isError'] is True


def test_press_button_by_id_runs_its_action(client, deck_dir, executor):
    result = _tool_call(client, 'press_button', {'button_id': 'btn-mute'})
    payload = _tool_payload(result)
    assert result['isError'] is False
    assert executor.calls == [
        {'type': 'cross_platform', 'config': {'action': 'volume_mute'}}]
    assert payload['result']['success'] is True
    assert payload['button']['label'] == 'Mute'


def test_press_button_by_scene_and_label(client, deck_dir, executor):
    result = _tool_call(client, 'press_button',
                        {'scene': 'claude', 'button': 'submit'})
    assert result['isError'] is False
    assert executor.calls[0]['type'] == 'command'


def test_press_button_by_label_alone_and_docked(client, deck_dir, executor):
    result = _tool_call(client, 'press_button', {'button': 'docked go'})
    assert result['isError'] is False
    assert executor.calls[0]['type'] == 'url'


def test_press_button_failures_are_iserror(client, deck_dir, executor):
    for args in ({'button_id': 'ghost'},
                 {'scene': 'nope', 'button': 'x'},
                 {'scene': 'Main', 'button': 'not-there'},
                 {'button_id': 'btn-off'}):   # disabled
        result = _tool_call(client, 'press_button', args)
        assert result['isError'] is True, args
    # ghost/nope/not-there resolve nothing; btn-off is disabled → no execute.
    assert executor.calls == []


def test_press_button_without_executor_is_error_not_crash(client, deck_dir):
    result = _tool_call(client, 'press_button', {'button_id': 'btn-mute'})
    assert result['isError'] is True
    assert 'executor' in _tool_payload(result)['error'].lower()


def test_run_action(client, executor):
    result = _tool_call(client, 'run_action', {
        'action': {'type': 'cross_platform',
                   'config': {'action': 'volume_get'}}})
    assert result['isError'] is False
    assert executor.calls[0]['type'] == 'cross_platform'

    bad = _tool_call(client, 'run_action', {'action': 'nope'})
    assert bad['isError'] is True


def test_run_action_failure_propagates_iserror(client, monkeypatch):
    monkeypatch.setattr(mcp, '_executor', FakeExecutor(succeed=False))
    result = _tool_call(client, 'run_action',
                        {'action': {'type': 'x', 'config': {}}})
    assert result['isError'] is True


def test_switch_scene_emits_navigate_scene(client, emitted):
    result = _tool_call(client, 'switch_scene', {'scene': 'Claude'})
    payload = _tool_payload(result)
    assert payload['delivered'] is True
    assert 'async' in payload['note'].lower()
    assert emitted == [('navigate_scene', {'scene': 'Claude'})]


def test_switch_scene_without_emitter_is_error(client):
    result = _tool_call(client, 'switch_scene', {'scene': 'Main'})
    assert result['isError'] is True


def test_show_notification_emits_panel_notification(client, emitted):
    result = _tool_call(client, 'show_notification',
                        {'title': 'Build done', 'message': 'All green'})
    assert result['isError'] is False
    name, payload = emitted[0]
    assert name == 'panel_notification'
    assert payload['source'] == 'mcp'
    assert payload['title'] == 'Build done'
    assert payload['message'] == 'All green'
    assert payload['ts'] > 0


def test_show_notification_requires_title(client, emitted):
    result = _tool_call(client, 'show_notification', {'message': 'x'})
    assert result['isError'] is True
    assert emitted == []


def test_get_volume(client, monkeypatch):
    monkeypatch.setattr(mcp, 'read_output_volume', lambda: (55, False, None))
    payload = _tool_payload(_tool_call(client, 'get_volume'))
    assert payload == {'value': 55, 'muted': False}

    monkeypatch.setattr(mcp, 'read_output_volume',
                        lambda: (None, None, 'no device'))
    result = _tool_call(client, 'get_volume')
    assert result['isError'] is True


def test_set_volume(client, monkeypatch):
    seen = []

    class FakeAction:
        def __init__(self, config):
            seen.append(config)
            self.config = config

        def execute(self):
            return ActionResult(True, 'ok', {'value': self.config['value']})

    monkeypatch.setattr(mcp, 'CrossPlatformAction', FakeAction)
    result = _tool_call(client, 'set_volume', {'value': 40})
    assert result['isError'] is False
    assert seen == [{'action': 'volume_set', 'value': 40}]

    bad = _tool_call(client, 'set_volume', {'value': 'loud'})
    assert bad['isError'] is True


def test_get_now_playing_unavailable(client):
    result = _tool_call(client, 'get_now_playing')
    assert result['isError'] is True
    assert _tool_payload(result)['available'] is False


def test_get_now_playing_reads_latest(client, monkeypatch):
    module = types.SimpleNamespace(latest=lambda: {
        'playing': True, 'title': 'Song', 'artist': 'A', 'album': 'B',
        'source_app': 'spotify.exe', 'has_art': False, 'ts': 1.0})
    monkeypatch.setattr(mcp, '_now_playing', module)
    payload = _tool_payload(_tool_call(client, 'get_now_playing'))
    assert payload['playing'] is True
    assert payload['track']['title'] == 'Song'


def test_get_now_playing_falls_back_without_latest(client, monkeypatch):
    monkeypatch.setattr(mcp, '_now_playing', types.SimpleNamespace())
    payload = _tool_payload(_tool_call(client, 'get_now_playing'))
    assert payload == {'available': True, 'track': None, 'playing': False}


def test_get_now_playing_accepts_w1_snapshot_name(client, monkeypatch):
    """W1 shipped snapshot()/latest_track()/available(), not the contract's
    latest() — the tool accepts whichever getter exists."""
    module = types.SimpleNamespace(
        snapshot=lambda: {'playing': False, 'title': '', 'artist': '',
                          'album': '', 'source_app': '', 'has_art': False,
                          'ts': 2.0},
        available=lambda: True)
    monkeypatch.setattr(mcp, '_now_playing', module)
    payload = _tool_payload(_tool_call(client, 'get_now_playing'))
    assert payload['available'] is True
    assert payload['playing'] is False
    assert payload['track']['title'] == ''


def test_get_agent_states(client):
    agent_state.record('claude', 'working', message='mid-task')
    payload = _tool_payload(_tool_call(client, 'get_agent_states'))
    assert payload['states']['claude']['state'] == 'working'


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

def test_remote_addr_rejected_without_auth(client):
    resp = _rpc(client, {'jsonrpc': '2.0', 'id': 1, 'method': 'ping'},
                environ_overrides={'REMOTE_ADDR': '10.1.2.3'})
    assert resp.status_code == 403


def test_remote_addr_rejected_with_bad_token(client, monkeypatch):
    monkeypatch.setattr(Config, 'REQUIRE_AUTH', True)
    resp = _rpc(client, {'jsonrpc': '2.0', 'id': 1, 'method': 'ping'},
                environ_overrides={'REMOTE_ADDR': '10.1.2.3'})
    assert resp.status_code == 401

    resp = _rpc(client, {'jsonrpc': '2.0', 'id': 1, 'method': 'ping'},
                environ_overrides={'REMOTE_ADDR': '10.1.2.3'},
                headers={'Authorization': 'Bearer junk'})
    assert resp.status_code == 401


def test_remote_addr_accepted_with_valid_token(client, monkeypatch):
    monkeypatch.setattr(Config, 'REQUIRE_AUTH', True)
    token = AuthManager.generate_token({'authenticated': True})
    resp = _rpc(client, {'jsonrpc': '2.0', 'id': 1, 'method': 'ping'},
                environ_overrides={'REMOTE_ADDR': '10.1.2.3'},
                headers={'Authorization': f'Bearer {token}'})
    assert json.loads(resp.get_data())['result'] == {}


def test_localhost_needs_no_token(client, monkeypatch):
    monkeypatch.setattr(Config, 'REQUIRE_AUTH', True)
    resp = _rpc(client, {'jsonrpc': '2.0', 'id': 1, 'method': 'ping'})
    assert json.loads(resp.get_data())['result'] == {}


def test_disabled_in_settings_returns_503(client, deck_dir):
    """Settings → Integrations → "Enable MCP server" off → honest 503."""
    (deck_dir / 'user_settings.json').write_text(
        json.dumps({'mcpEnabled': False}), encoding='utf-8')
    resp = _rpc(client, {'jsonrpc': '2.0', 'id': 1, 'method': 'ping'})
    assert resp.status_code == 503
    assert 'disabled' in json.loads(resp.get_data())['error']


def test_other_settings_leaves_mcp_enabled(client, deck_dir):
    """A settings file without the key means default-on."""
    (deck_dir / 'user_settings.json').write_text(
        json.dumps({'otherSetting': 1}), encoding='utf-8')
    resp = _rpc(client, {'jsonrpc': '2.0', 'id': 1, 'method': 'ping'})
    assert resp.status_code == 200
