"""DL-145: Agent Prompt service + Mission Control prompt route."""
import pytest

from app import app
from integrations import agent_state, context, editor_base, sessions
from services import agent_prompt as ap


@pytest.fixture
def client():
    app.config['TESTING'] = True
    agent_state.reset()
    with app.test_client() as test_client:
        yield test_client
    agent_state.reset()


@pytest.fixture
def send(mocker):
    return mocker.patch.object(editor_base, 'send',
                               return_value={'success': True, 'message': 'x'})


def _rec(source, state, sid, cwd='C:/x', **kw):
    return agent_state.record(source, state, session_id=sid, cwd=cwd,
                              project='p', **kw)


def test_prompt_sources_map_agents_to_prompt_commands():
    assert ap.PROMPT_SOURCES['claude'] == 'cc_prompt'
    assert ap.PROMPT_SOURCES['cursor'] == 'cursor_followup'
    assert ap.PROMPT_SOURCES['devin'] == 'devin_prompt'
    assert ap.PROMPT_SOURCES['antigravity'] == 'antigravity_followup'


def test_auto_target_prefers_ready_over_newer_working(client):
    _rec('claude', 'ready', 'r')
    agent_state._sessions_by_source['claude']['r']['ts'] -= 50
    _rec('claude', 'working', 'w')
    assert ap.resolve_target().session_id == 'r'


def test_agent_filter_and_cwd_filter(client):
    _rec('claude', 'ready', 'c', cwd='C:/a')
    _rec('cursor', 'ready', 'u', cwd='C:/b')
    assert ap.resolve_target(agent='cursor').session_id == 'u'
    assert ap.resolve_target(cwd='C:/a').session_id == 'c'
    assert ap.resolve_target(cwd='C:/nowhere') is None


def test_explicit_session(client):
    _rec('claude', 'ready', 'a')
    _rec('claude', 'ready', 'b')
    assert ap.resolve_target(source='claude', session_id='a').session_id == 'a'
    assert ap.resolve_target(source='claude', session_id='zzz') is None


def test_no_hooked_sessions_gives_legacy_target(client):
    target = ap.resolve_target(agent='claude', cwd='C:/x')
    assert target.session_id is None and target.source == 'claude'
    assert target.cwd == 'C:/x'


def test_explain_error_needs_clipboard(mocker):
    mocker.patch.object(context, 'clipboard_text', return_value='')
    text, error = ap.render_text('explain_error', '', None)
    assert text is None and 'clipboard is empty' in error


def test_explain_error_includes_clipboard(mocker):
    mocker.patch.object(context, 'clipboard_text', return_value='Boom at x.py')
    text, error = ap.render_text('explain_error', '', None)
    assert error is None and 'Boom at x.py' in text


def test_long_payload_is_truncated_keeping_tail(mocker):
    trace = 'line\n' * 2000 + 'THE-END'
    mocker.patch.object(context, 'clipboard_text', return_value=trace)
    text, _ = ap.render_text('explain_error', '', None)
    assert len(text) <= ap.MAX_PROMPT_CHARS
    assert text.startswith('Explain this error and fix it:')
    assert text.endswith('THE-END')


def test_fix_tests_without_failure_is_friendly(mocker):
    from services import test_runner
    mocker.patch.object(test_runner, 'last_failure', return_value='')
    text, error = ap.render_text('fix_tests', '', None)
    assert text is None and 'No failing test run yet' in error


def test_fix_tests_uses_last_failure_for_focused_repo(mocker):
    from services import test_runner
    mocker.patch.object(context, 'focused_repo', return_value='C:/repo')
    last = mocker.patch.object(test_runner, 'last_failure',
                               return_value='FAILED test_x')
    text, error = ap.render_text('fix_tests', '', None)
    last.assert_called_once_with('C:/repo')
    assert error is None and 'FAILED test_x' in text


def test_custom_blank_and_unknown_preset():
    assert ap.render_text('custom', '  ', None)[0] is None
    assert ap.render_text('nope', '', None)[0] is None


@pytest.mark.parametrize('state, code', [('permission', 409), ('working', 409)])
def test_send_refuses_blocked_or_busy_without_typing(client, send, state, code):
    _rec('claude', state, 's')
    target = ap.resolve_target(source='claude', session_id='s')
    result = ap.send_prompt(target, 'hi')
    assert result['success'] is False and result['status_code'] == code
    send.assert_not_called()


def test_send_ready_passes_cwd_and_text(client, send):
    _rec('claude', 'ready', 's', cwd='C:/proj')
    target = ap.resolve_target(source='claude', session_id='s')
    assert ap.send_prompt(target, 'go')['success'] is True
    args, kwargs = send.call_args
    assert args[0].id == 'cc_prompt' and args[0].submit in (True, False)
    assert kwargs['text_override'] == 'go' and kwargs['cwd'] == 'C:/proj'


def test_submit_false_builds_non_submitting_command(client, send):
    _rec('claude', 'ready', 's')
    target = ap.resolve_target(source='claude', session_id='s')
    ap.send_prompt(target, 'go', submit=False)
    assert send.call_args[0][0].submit is False


def test_pinned_host_with_blocked_sibling_refuses(client, send, mocker):
    _rec('claude', 'ready', 'a')
    _rec('claude', 'permission', 'b')
    mocker.patch.object(sessions, 'pinned_pid', return_value=123)
    target = ap.resolve_target(source='claude', session_id='a')
    result = ap.send_prompt(target, 'go')
    assert result['status_code'] == 409
    send.assert_not_called()


# --- route -------------------------------------------------------------------

def _post(client, **body):
    return client.post('/api/agent-mission/prompt',
                       json={'source': 'claude', 'session_id': 's', **body})


def test_route_400_when_nothing_to_send(client):
    assert _post(client).status_code == 400
    assert _post(client, preset='nope').status_code == 400


def test_route_404_when_session_gone(client, send):
    assert _post(client, preset='continue').status_code == 404


def test_route_409_on_permission(client, send):
    _rec('claude', 'permission', 's')
    resp = _post(client, preset='continue')
    assert resp.status_code == 409
    assert 'approval' in resp.get_json()['error']


def test_route_502_propagates_send_failure(client, mocker):
    mocker.patch.object(editor_base, 'send', return_value={
        'success': False, 'message': 'Window not focused', 'details': 'd'})
    _rec('claude', 'ready', 's')
    resp = _post(client, preset='continue')
    assert resp.status_code == 502
    assert resp.get_json()['error'] == 'Window not focused'


def test_route_happy_path(client, send):
    _rec('claude', 'ready', 's')
    resp = _post(client, preset='continue')
    assert resp.status_code == 200 and resp.get_json()['success'] is True
    assert send.call_args.kwargs['text_override'] == 'continue'


def test_mission_list_has_presets_and_can_prompt(client):
    _rec('claude', 'ready', 'r')
    _rec('claude', 'working', 'w')
    body = client.get('/api/agent-mission').get_json()
    assert [p['id'] for p in body['presets']][0] == 'continue'
    by_id = {s['session_id']: s for s in body['sessions']}
    assert by_id['r']['can_prompt'] is True
    assert by_id['w']['can_prompt'] is False
