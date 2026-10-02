"""DL-145: turn-baseline hooks into agent events + the changes routes."""
import pytest

from app import app
from integrations import agent_state
from services import turn_baseline


@pytest.fixture
def client():
    app.config['TESTING'] = True
    agent_state.reset()
    with app.test_client() as c:
        yield c
    agent_state.reset()


def _event(client, **body):
    base = {'source': 'claude', 'state': 'working', 'session_id': 's',
            'cwd': 'C:/x'}
    return client.post('/api/agent-events', json={**base, **body},
                       environ_base={'REMOTE_ADDR': '127.0.0.1'})


def test_prompt_event_captures_baseline(client, mocker):
    cap = mocker.patch.object(turn_baseline, 'capture_async')
    _event(client, prompt='do the thing')
    cap.assert_called_once_with('claude', 's', 'C:/x')


def test_event_without_prompt_does_not_capture(client, mocker):
    cap = mocker.patch.object(turn_baseline, 'capture_async')
    _event(client)
    cap.assert_not_called()


def test_ended_forgets_baseline(client, mocker):
    forget = mocker.patch.object(turn_baseline, 'forget')
    _event(client, state='ended')
    forget.assert_called_once_with('claude', 's')


def test_changes_route_404_for_unknown_session(client):
    resp = client.get('/api/agent-mission/changes?source=claude&session_id=nope')
    assert resp.status_code == 404


def test_changes_route_returns_service_result(client, mocker):
    agent_state.record('claude', 'ready', session_id='s', cwd='C:/x')
    mocker.patch.object(turn_baseline, 'changes', return_value={
        'success': True, 'files': [], 'totals': {'files': 0, 'added': 0,
                                                 'removed': 0}})
    body = client.get('/api/agent-mission/changes?source=claude&session_id=s'
                      ).get_json()
    assert body['success'] is True and body['totals']['files'] == 0


def test_open_diff_route_400_on_outside_path(client):
    agent_state.record('claude', 'ready', session_id='s', cwd='C:/x')
    resp = client.post('/api/agent-mission/open-diff',
                       json={'source': 'claude', 'session_id': 's',
                             'path': '../../etc/passwd'})
    assert resp.status_code == 400


def test_open_diff_route_requires_path(client):
    resp = client.post('/api/agent-mission/open-diff',
                       json={'source': 'claude', 'session_id': 's'})
    assert resp.status_code == 400
