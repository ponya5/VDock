"""DL-145 Phase 2: /api/agent-usage, Mission Control usage chip, compact verb."""
import pytest

from app import app
from integrations import agent_state
from services import agent_prompt, claude_usage


@pytest.fixture
def client():
    app.config['TESTING'] = True
    agent_state.reset()
    with app.test_client() as test_client:
        yield test_client
    agent_state.reset()


def _usage(session_id='a', pct=50, status='normal'):
    return {'session_id': session_id, 'model': 'claude-sonnet-5',
            'tokens': {'total': 10}, 'cost_usd': 1.5, 'estimate': True,
            'context_tokens': 100, 'context_pct': pct, 'status': status}


def _today(cost=5.0):
    return {'tokens': {'total': 10}, 'cost_usd': cost, 'estimate': True,
            'sessions': 1}


def test_usage_route_shape(client, mocker):
    agent_state.record('claude', 'ready', session_id='a')
    agent_state.record('cursor', 'ready', session_id='c')
    mocker.patch.object(claude_usage, 'today_usage', return_value=_today())
    mocker.patch.object(claude_usage, 'session_usage', return_value=_usage())

    body = client.get('/api/agent-usage').get_json()

    assert body['success'] is True
    assert body['today']['cost_usd'] == 5.0
    assert [s['session_id'] for s in body['sessions']] == ['a']  # claude only
    assert body['limit_usd'] == 0 and body['status'] == 'normal'


@pytest.mark.parametrize('limit,status', [('10', 'normal'), ('6', 'warning'),
                                          ('5', 'critical'), ('abc', 'normal')])
def test_usage_route_limit_thresholds(client, mocker, limit, status):
    mocker.patch.object(claude_usage, 'today_usage', return_value=_today(5.0))
    body = client.get(f'/api/agent-usage?limit_usd={limit}').get_json()
    assert body['status'] == status


def test_usage_route_unreadable_transcripts_is_a_clean_error(client, mocker):
    mocker.patch.object(claude_usage, 'today_usage', side_effect=OSError('x'))
    assert client.get('/api/agent-usage').status_code == 500


def test_mission_rows_carry_usage_for_claude_only(client, mocker):
    agent_state.record('claude', 'ready', session_id='a')
    agent_state.record('cursor', 'ready', session_id='c')
    mocker.patch.object(claude_usage, 'session_usage',
                        return_value=_usage(pct=82, status='warning'))

    rows = {r['source']: r for r in
            client.get('/api/agent-mission').get_json()['sessions']}

    assert rows['claude']['usage'] == {
        'cost_usd': 1.5, 'estimate': True, 'context_pct': 82, 'status': 'warning'}
    assert rows['cursor']['usage'] is None


def test_mission_usage_failure_does_not_break_the_list(client, mocker):
    agent_state.record('claude', 'ready', session_id='a')
    mocker.patch.object(claude_usage, 'session_usage', side_effect=RuntimeError('bad'))

    response = client.get('/api/agent-mission')

    assert response.status_code == 200
    assert response.get_json()['sessions'][0]['usage'] is None


def test_mission_usage_none_without_transcript(client, mocker):
    agent_state.record('claude', 'ready', session_id='a')
    mocker.patch.object(claude_usage, 'session_usage', return_value=None)
    assert client.get('/api/agent-mission').get_json()['sessions'][0]['usage'] is None


# --- compact ---------------------------------------------------------------------

def test_compact_types_only_slash_compact(client, mocker):
    agent_state.record('claude', 'ready', session_id='a', cwd='C:/x')
    send = mocker.patch.object(agent_prompt, 'send_prompt',
                               return_value={'success': True, 'status_code': 200})

    response = client.post('/api/agent-mission/compact',
                           json={'source': 'claude', 'session_id': 'a'})

    assert response.status_code == 200
    assert send.call_args.args[1] == '/compact'


def test_compact_rejects_other_agents_and_gone_sessions(client):
    agent_state.record('cursor', 'ready', session_id='c')
    assert client.post('/api/agent-mission/compact',
                       json={'source': 'cursor', 'session_id': 'c'}).status_code == 400
    assert client.post('/api/agent-mission/compact',
                       json={'source': 'claude', 'session_id': 'gone'}).status_code == 404


@pytest.mark.parametrize('state', ['permission', 'working'])
def test_compact_refuses_unsafe_states_without_typing(client, mocker, state):
    agent_state.record('claude', state, session_id='a', cwd='C:/x')
    send = mocker.patch('integrations.editor_base.send')

    response = client.post('/api/agent-mission/compact',
                           json={'source': 'claude', 'session_id': 'a'})

    assert response.status_code == 409
    send.assert_not_called()
