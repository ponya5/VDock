"""DL-144: Mission Control list + approval inbox (focus / decide).

The keystroke send and the window focus are mocked: these tests pin the
routing and the safety guards (a stale tap must never type into a session
that has moved on), not Windows input.
"""
import time

import pytest

from app import app
from integrations import agent_state, editor_base
import routes.agent_mission as mission
from utils import window_focus


@pytest.fixture
def client():
    app.config['TESTING'] = True
    agent_state.reset()
    with app.test_client() as test_client:
        yield test_client
    agent_state.reset()


def _record(source, state, session_id, project='proj', cwd='C:/x', **kw):
    return agent_state.record(source, state, session_id=session_id,
                              project=project, cwd=cwd, **kw)


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def test_lists_every_session_not_one_per_source(client):
    _record('claude', 'working', 'a', project='api')
    _record('claude', 'ready', 'b', project='web', prompt='fix it')
    _record('cursor', 'working', 'c', project='app')

    body = client.get('/api/agent-mission').get_json()

    assert body['success'] is True
    assert {(s['source'], s['session_id']) for s in body['sessions']} == {
        ('claude', 'a'), ('claude', 'b'), ('cursor', 'c')}


def test_orders_blocked_first_oldest_first_then_idle_then_working(client):
    now = time.time()
    _record('claude', 'working', 'w')
    _record('claude', 'permission', 'p-new')
    _record('cursor', 'ready', 'r', prompt='go')
    _record('claude', 'permission', 'p-old')
    sessions = agent_state._sessions_by_source
    sessions['claude']['p-old']['ts'] = now - 300   # waiting the longest
    sessions['claude']['p-new']['ts'] = now - 30

    order = [s['session_id'] for s in
             client.get('/api/agent-mission').get_json()['sessions']]

    assert order == ['p-old', 'p-new', 'r', 'w']

def test_needs_you_and_counts(client):
    _record('claude', 'permission', 'p')
    _record('cursor', 'ready', 'unprompted')            # never prompted
    _record('codex', 'ready', 'prompted', prompt='hi')  # waiting on the user

    body = client.get('/api/agent-mission').get_json()
    by_id = {s['session_id']: s for s in body['sessions']}

    assert by_id['p']['needs_you'] and by_id['p']['can_decide']
    assert not by_id['unprompted']['needs_you']
    assert by_id['prompted']['needs_you'] and not by_id['prompted']['can_decide']
    assert body['needs_you'] == 2
    assert body['pending_approvals'] == 1


def test_only_claude_can_be_decided(client):
    _record('cursor', 'permission', 'c')

    row = client.get('/api/agent-mission').get_json()['sessions'][0]

    assert row['can_decide'] is False


def test_long_reply_is_excerpted(client):
    _record('claude', 'ready', 'a', prompt='p', reply='word ' * 400)

    row = client.get('/api/agent-mission').get_json()['sessions'][0]

    assert len(row['reply']) <= mission.REPLY_EXCERPT_CHARS
    assert row['reply'].endswith('…')


# ---------------------------------------------------------------------------
# decide
# ---------------------------------------------------------------------------

@pytest.fixture
def sent(monkeypatch):
    calls = []

    def fake_send(command, **kwargs):
        calls.append((command.id, kwargs))
        return {'success': True, 'message': command.label}

    monkeypatch.setattr(editor_base, 'send', fake_send)
    return calls


def test_approve_types_into_that_sessions_window(client, sent):
    _record('claude', 'permission', 'a', cwd='C:/repos/api')
    _record('claude', 'permission', 'b', cwd='C:/repos/web')

    response = client.post('/api/agent-mission/decide', json={
        'source': 'claude', 'session_id': 'b', 'decision': 'approve'})

    assert response.get_json()['success'] is True
    assert sent == [('cc_approve', {'cwd': 'C:/repos/web',
                                    'editor_label': 'Claude Code'})]


def test_deny_uses_the_deny_command(client, sent):
    _record('claude', 'permission', 'a')

    client.post('/api/agent-mission/decide', json={
        'source': 'claude', 'session_id': 'a', 'decision': 'deny'})

    assert sent[0][0] == 'cc_deny'


@pytest.mark.parametrize('state', ['working', 'ready'])
def test_stale_decision_is_refused_and_nothing_is_typed(client, sent, state):
    _record('claude', state, 'a')

    response = client.post('/api/agent-mission/decide', json={
        'source': 'claude', 'session_id': 'a', 'decision': 'approve'})

    assert response.status_code == 409
    assert sent == []


def test_unknown_session_is_404(client, sent):
    response = client.post('/api/agent-mission/decide', json={
        'source': 'claude', 'session_id': 'ghost', 'decision': 'approve'})

    assert response.status_code == 404
    assert sent == []


def test_unsupported_source_and_bad_decision_are_rejected(client, sent):
    _record('cursor', 'permission', 'c')

    unsupported = client.post('/api/agent-mission/decide', json={
        'source': 'cursor', 'session_id': 'c', 'decision': 'approve'})
    bad = client.post('/api/agent-mission/decide', json={
        'source': 'claude', 'session_id': 'c', 'decision': 'maybe'})

    assert unsupported.status_code == 400
    assert bad.status_code == 400
    assert sent == []


def test_send_failure_is_reported_not_swallowed(client, monkeypatch):
    _record('claude', 'permission', 'a')
    monkeypatch.setattr(editor_base, 'send', lambda *a, **k: {
        'success': False, 'message': 'The session window is not focused'})

    response = client.post('/api/agent-mission/decide', json={
        'source': 'claude', 'session_id': 'a', 'decision': 'approve'})

    assert response.status_code == 502
    assert 'not focused' in response.get_json()['error']


# ---------------------------------------------------------------------------
# focus
# ---------------------------------------------------------------------------

def test_focus_raises_the_matching_window(client, monkeypatch):
    _record('claude', 'ready', 'a', cwd='C:/repos/api')
    seen = {}
    monkeypatch.setattr(window_focus, 'find_session_host_window',
                        lambda marker, **kw: seen.update(marker=marker, **kw) or 4242)
    monkeypatch.setattr(window_focus, 'focus_hwnd', lambda hwnd: hwnd == 4242)

    response = client.post('/api/agent-mission/focus', json={
        'source': 'claude', 'session_id': 'a'})

    assert response.get_json()['success'] is True
    assert seen == {'marker': 'claude', 'prefer_cwd': 'C:/repos/api'}


def test_focus_unknown_session_or_window_is_404(client, monkeypatch):
    missing = client.post('/api/agent-mission/focus', json={
        'source': 'claude', 'session_id': 'ghost'})
    _record('claude', 'ready', 'a')
    monkeypatch.setattr(window_focus, 'find_session_host_window',
                        lambda marker, **kw: None)
    no_window = client.post('/api/agent-mission/focus', json={
        'source': 'claude', 'session_id': 'a'})

    assert missing.status_code == 404
    assert no_window.status_code == 404


def test_focus_unsupported_source_is_400(client):
    _record('codex', 'ready', 'x')

    response = client.post('/api/agent-mission/focus', json={
        'source': 'codex', 'session_id': 'x'})

    assert response.status_code == 400
