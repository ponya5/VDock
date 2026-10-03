"""DL-145 Phase 5: hold-to-talk dictation goes only through the verified path."""
import pytest

from integrations import agent_loop_pack as pack
from integrations import agent_state, editor_base
from services import agent_dictate


@pytest.fixture(autouse=True)
def clean(mocker):
    agent_state.reset()
    agent_dictate._listening = None
    agent_dictate._hint_shown = False
    mocker.patch.object(agent_dictate, 'voice_typing_blocker', return_value=None)
    yield
    agent_state.reset()
    agent_dictate._listening = None


@pytest.fixture
def send(mocker):
    return mocker.patch.object(editor_base, 'send',
                               return_value={'success': True})


def _all_keys(command):
    return [command.keys, *command.after_keys]


def test_start_sends_voice_typing_to_the_sessions_directory(send):
    agent_state.record('claude', 'ready', session_id='s', cwd='C:/work/api')
    result = agent_dictate.start()

    assert result['success'] is True and 'release to stop' in result['message']
    command = send.call_args.args[0]
    assert send.call_args.kwargs['cwd'] == 'C:/work/api'
    assert command.keys == ('win', 'h')
    assert command.session_marker == 'claude' and command.requires_session


def test_no_enter_or_text_in_any_built_command(send):
    agent_state.record('claude', 'ready', session_id='s', cwd='C:/x')
    agent_dictate.start()
    agent_dictate.stop()
    for call in send.call_args_list:
        command = call.args[0]
        assert call.kwargs.get('text_override') is None
        steps = command.to_macro_steps()
        assert not command.submit and command.types_text is None
        assert all(step['type'] == 'hotkey' for step in steps)
        assert all('enter' not in [k.lower() for k in step['keys']]
                   for step in steps)


def test_cursor_start_focuses_the_chat_box_before_voice_typing(send):
    agent_state.record('cursor', 'ready', session_id='c', cwd='C:/x')
    agent_dictate.start()
    command = send.call_args.args[0]
    assert command.after_keys == (('win', 'h'),)
    assert command.keys and command.keys != ('win', 'h')
    assert [s['keys'] for s in command.to_macro_steps()
            if s['type'] == 'hotkey'] == [list(command.keys), ['win', 'h']]


@pytest.mark.parametrize('state,fragment', [('permission', 'approval'),
                                            ('working', 'busy')])
def test_start_refuses_blocked_sessions_without_sending(send, state, fragment):
    agent_state.record('claude', state, session_id='s', cwd='C:/x')
    result = agent_dictate.start()

    assert result['success'] is False and fragment in result['message']
    send.assert_not_called()


def test_start_without_a_session_says_so(send, mocker):
    mocker.patch.object(agent_dictate.agent_prompt, 'resolve_target',
                        return_value=None)
    result = agent_dictate.start()
    assert result['success'] is False
    assert result['message'] == 'No agent session is ready'
    send.assert_not_called()


def test_send_refusal_is_reported_and_leaves_us_not_listening(mocker):
    mocker.patch.object(editor_base, 'send', return_value={
        'success': False, 'message': 'The session window is not focused',
        'details': 'Refusing'})
    agent_state.record('claude', 'ready', session_id='s', cwd='C:/x')

    assert agent_dictate.start()['message'] == 'The session window is not focused'
    assert agent_dictate.stop()['message'] == 'Not listening'


def test_stop_without_a_start_sends_nothing(send):
    result = agent_dictate.stop()
    assert result == {'success': True, 'message': 'Not listening'}
    send.assert_not_called()


def test_stop_closes_the_same_session_once(send):
    agent_state.record('claude', 'ready', session_id='s', cwd='C:/work/api')
    agent_dictate.start()
    send.reset_mock()

    first, second = agent_dictate.stop(), agent_dictate.stop()

    assert first['success'] is True and second['message'] == 'Not listening'
    assert send.call_count == 1
    assert send.call_args.args[0].keys == ('win', 'h')
    assert send.call_args.kwargs['cwd'] == 'C:/work/api'


def test_stop_failure_tells_the_user_how_to_close_the_panel(mocker):
    agent_state.record('claude', 'ready', session_id='s', cwd='C:/x')
    mocker.patch.object(editor_base, 'send', side_effect=[
        {'success': True},
        {'success': False, 'message': 'No running claude session detected'}])
    agent_dictate.start()
    result = agent_dictate.stop()

    assert result['success'] is False
    assert 'Win+H' in result['details']


def test_second_start_while_listening_does_not_toggle_the_panel_off(send):
    agent_state.record('claude', 'ready', session_id='s', cwd='C:/x')
    agent_dictate.start()
    again = agent_dictate.start()

    assert again['success'] is True and 'Already listening' in again['message']
    assert send.call_count == 1


def test_enable_hint_only_on_first_start(send):
    agent_state.record('claude', 'ready', session_id='s', cwd='C:/x')
    first = agent_dictate.start()['message']
    agent_dictate.stop()
    second = agent_dictate.start()['message']

    assert 'Settings > Time & language > Typing' in first
    assert 'Settings' not in second


def test_unavailable_voice_typing_is_explained_and_nothing_is_sent(send, mocker):
    mocker.patch.object(agent_dictate, 'voice_typing_blocker',
                        return_value='Online speech recognition is off')
    agent_state.record('claude', 'ready', session_id='s', cwd='C:/x')
    result = agent_dictate.start()

    assert result == {'success': False,
                      'message': 'Online speech recognition is off',
                      'details': ''}
    send.assert_not_called()


def test_blocker_detects_privacy_setting_off(mocker):
    mocker.stopall()
    mocker.patch.object(agent_dictate.platform, 'system', return_value='Windows')
    winreg = pytest.importorskip('winreg')
    mocker.patch.object(winreg, 'OpenKey')
    mocker.patch.object(winreg, 'QueryValueEx', return_value=(0, 4))
    reason = agent_dictate.voice_typing_blocker()
    assert 'Online speech recognition is off' in reason
    assert 'Settings > Time & language > Typing' in reason


def test_blocker_none_when_never_configured(mocker):
    mocker.stopall()
    mocker.patch.object(agent_dictate.platform, 'system', return_value='Windows')
    winreg = pytest.importorskip('winreg')
    mocker.patch.object(winreg, 'OpenKey', side_effect=FileNotFoundError)
    assert agent_dictate.voice_typing_blocker() is None


def test_blocker_on_non_windows(mocker):
    mocker.stopall()
    mocker.patch.object(agent_dictate.platform, 'system', return_value='Linux')
    assert 'Windows' in agent_dictate.voice_typing_blocker()


def test_unknown_op_is_refused(send):
    result = agent_dictate.dictate('')
    assert result['success'] is False and 'Hold' in result['message']
    send.assert_not_called()


# --- catalog entry -------------------------------------------------------------

def test_spec_is_a_hold_button_with_no_visible_field():
    spec = next(s for s in pack.Plugin().get_action_specs()
                if s.id == 'agent_dictate')
    assert spec.press == 'hold'
    assert [f.name for f in spec.config_fields if not f.advanced] == []
    assert spec.category == 'ai' and spec.label == 'Dictate to Agent'
    assert 'Hold to talk' in spec.description


def test_pack_routes_ops_to_the_service(mocker):
    dictate = mocker.patch.object(agent_dictate, 'dictate',
                                  return_value={'success': True})
    pack.Plugin().execute_action(
        'agent_dictate', {'op': 'start', 'agent': 'cursor', 'cwd': 'C:/x'})
    dictate.assert_called_once_with('start', agent='cursor', cwd='C:/x')
