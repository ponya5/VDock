"""DL-145: agent_prompt + agent_review_changes catalog actions."""
import pytest

from integrations import agent_loop_pack as pack
from integrations import agent_state
from plugins.plugin_manager import PluginManager
from services import agent_prompt, turn_baseline


@pytest.fixture(autouse=True)
def clean():
    agent_state.reset()
    yield
    agent_state.reset()


@pytest.fixture
def plugin():
    return pack.Plugin()


def _spec(plugin, action_id):
    return next(s for s in plugin.get_action_specs() if s.id == action_id)


def _visible(spec):
    return [f for f in spec.config_fields
            if not f.advanced and not f.show_when]


def test_agent_prompt_has_exactly_one_visible_field(plugin):
    spec = _spec(plugin, 'agent_prompt')
    assert [f.name for f in _visible(spec)] == ['preset']
    text = next(f for f in spec.config_fields if f.name == 'text')
    assert text.show_when == {'preset': 'custom'}


def test_review_changes_has_no_visible_fields_and_is_a_live_menu(plugin):
    spec = _spec(plugin, 'agent_review_changes')
    assert _visible(spec) == []
    assert (spec.poll_seconds, spec.press) == (20, 'menu')
    assert spec.poll_config == {'op': 'status'}


def test_prompt_dispatches_to_service(plugin, mocker):
    send = mocker.patch.object(
        agent_prompt, 'prompt_preset',
        return_value={'success': True, 'message': 'ok'})
    result = plugin.execute_action('agent_prompt', {'preset': 'review',
                                                    'agent': 'cursor'})
    assert result['success'] is True
    send.assert_called_once_with('review', custom_text='', agent='cursor',
                                 cwd=None, submit=True)


def test_prompt_no_session_message(plugin, mocker):
    mocker.patch.object(agent_prompt, 'resolve_target', return_value=None)
    result = plugin.execute_action('agent_prompt', {'preset': 'continue'})
    assert result['success'] is False
    assert result['message'] == 'No agent session is ready'


def test_prompt_custom_blank_and_unknown(plugin, mocker):
    agent_state.record('claude', 'ready', session_id='s', cwd='C:/x')
    blank = plugin.execute_action('agent_prompt', {'preset': 'custom'})
    unknown = plugin.execute_action('agent_prompt', {'preset': 'zzz'})
    assert blank['success'] is False and unknown['success'] is False


def test_prompt_success_message_names_preset_and_project(plugin, mocker):
    agent_state.record('claude', 'ready', session_id='s', cwd='C:/work/api')
    mocker.patch.object(agent_prompt.editor_base, 'send',
                        return_value={'success': True})
    result = plugin.execute_action('agent_prompt', {'preset': 'continue'})
    assert result == {'success': True, 'message': 'Continue → api'}


def test_pluginmanager_discovers_pack():
    manager = PluginManager()
    manager.load_builtin_packs()
    ids = {s.id for s in manager.get_action_specs()}
    assert {'agent_prompt', 'agent_review_changes', 'dev_run_tests'} <= ids


def _changes(files, kind='turn'):
    return {'success': True, 'base': {'sha': 'x', 'kind': kind},
            'repo': 'C:/x', 'files': files,
            'totals': {'files': len(files),
                       'added': sum(f['added'] for f in files),
                       'removed': sum(f['removed'] for f in files)}}


def test_review_status_shape(plugin, mocker):
    agent_state.record('claude', 'ready', session_id='s', cwd='C:/x')
    mocker.patch.object(turn_baseline, 'changes', return_value=_changes([
        {'path': 'a.py', 'added': 3, 'removed': 1, 'status': 'M'},
        {'path': 'b.py', 'added': 2, 'removed': 0, 'status': '?'}]))
    result = plugin.execute_action('agent_review_changes', {'op': 'status'})
    data = result['data']
    assert data['badge'] == '2' and data['status'] == 'warning'
    assert data['sublabel'] == '+5 −1'
    assert [m['id'] for m in data['menu']] == ['open:a.py', 'open:b.py']


def test_review_head_fallback_is_labelled(plugin, mocker):
    agent_state.record('claude', 'ready', session_id='s', cwd='C:/x')
    mocker.patch.object(turn_baseline, 'changes', return_value=_changes(
        [{'path': 'a.py', 'added': 1, 'removed': 0, 'status': 'M'}],
        kind='head'))
    data = plugin.execute_action('agent_review_changes', {})['data']
    assert 'since last commit' in data['sublabel']


def test_review_open_op_opens_that_path(plugin, mocker):
    agent_state.record('claude', 'ready', session_id='s', cwd='C:/x')
    opened = mocker.patch.object(turn_baseline, 'open_diff', return_value={
        'success': True, 'message': 'Opened diff'})
    result = plugin.execute_action('agent_review_changes',
                                   {'op': 'open:src/a.py'})
    opened.assert_called_once_with('claude', 's', 'C:/x', 'src/a.py')
    assert result['success'] is True


def test_review_empty_states(plugin, mocker):
    none = plugin.execute_action('agent_review_changes', {'op': 'status'})
    assert none['success'] is True and none['message'] == 'No agent session yet'

    agent_state.record('claude', 'ready', session_id='s', cwd='C:/x')
    mocker.patch.object(turn_baseline, 'changes', return_value=_changes([]))
    zero = plugin.execute_action('agent_review_changes', {'op': 'status'})
    assert zero['message'] == 'No changes this turn'
    assert zero['data']['badge'] == '0'


# --- agent_usage ---------------------------------------------------------------

def _today(cost, tokens):
    return {'tokens': {'total': tokens}, 'cost_usd': cost, 'estimate': True,
            'sessions': 1}


def test_usage_has_one_visible_field_and_polls(plugin):
    spec = _spec(plugin, 'agent_usage')
    assert [f.name for f in _visible(spec)] == ['daily_limit_usd']
    assert (spec.poll_seconds, spec.press) == (60, 'run')
    assert spec.poll_config == {'op': 'status'}


@pytest.mark.parametrize('usd,expected', [(0.42, '≈$0.42'), (4.2, '≈$4.20'),
                                          (12.4, '≈$12')])
def test_cost_badge_format(usd, expected):
    assert pack.format_cost(usd) == expected


@pytest.mark.parametrize('count,expected', [(850_000, '850k'), (1_200_000, '1.2M'),
                                            (420, '420')])
def test_token_badge_format(count, expected):
    assert pack.format_tokens(count) == expected


def test_usage_face_and_mission_control_flag(plugin, mocker):
    mocker.patch.object(pack.claude_usage, 'today_usage',
                        return_value=_today(4.2, 1_200_000))
    result = plugin.execute_action('agent_usage', {'daily_limit_usd': 0})
    assert result['success'] is True
    assert result['data']['badge'] == '≈$4.20'
    assert result['data']['sublabel'] == 'today'
    assert result['data']['status'] == 'normal'
    assert result['data']['open_mission_control'] is True


@pytest.mark.parametrize('limit,status', [(0, 'normal'), (10, 'normal'),
                                          (5, 'warning'), (4.2, 'critical')])
def test_usage_limit_thresholds(plugin, mocker, limit, status):
    mocker.patch.object(pack.claude_usage, 'today_usage',
                        return_value=_today(4.2, 10))
    result = plugin.execute_action('agent_usage', {'daily_limit_usd': limit})
    assert result['data']['status'] == status


def test_usage_tokens_metric_has_no_limit_colour(plugin, mocker):
    mocker.patch.object(pack.claude_usage, 'today_usage',
                        return_value=_today(40, 850_000))
    result = plugin.execute_action(
        'agent_usage', {'metric': 'tokens', 'daily_limit_usd': 1})
    assert result['data']['badge'] == '850k'
    assert result['data']['status'] == 'normal'


def test_usage_empty_state(plugin, mocker):
    mocker.patch.object(pack.claude_usage, 'today_usage',
                        return_value=_today(0, 0))
    result = plugin.execute_action('agent_usage', {})
    assert result['success'] is True
    assert result['message'] == 'No Claude Code usage today'
    assert result['data']['badge'] == '$0'


def test_usage_read_error_is_a_failure_not_a_crash(plugin, mocker):
    mocker.patch.object(pack.claude_usage, 'today_usage',
                        side_effect=OSError('disk'))
    assert plugin.execute_action('agent_usage', {})['success'] is False
