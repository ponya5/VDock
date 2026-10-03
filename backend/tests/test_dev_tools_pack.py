"""DL-145: dev_run_tests catalog action."""
import pytest

from integrations import context
from integrations import dev_tools_pack as pack
from services import (agent_prompt, dev_servers, docker_status, git_context,
                      test_runner)


@pytest.fixture
def plugin(mocker):
    mocker.patch.object(context, 'focused_repo', return_value='C:/work/proj')
    return pack.Plugin()


def _spec(plugin):
    return plugin.get_action_specs()[0]


def test_spec_flags_and_no_visible_fields(plugin):
    spec = _spec(plugin)
    assert spec.id == 'dev_run_tests' and spec.long_running is True
    assert (spec.poll_seconds, spec.poll_config) == (15, {'op': 'status'})
    assert spec.press == 'run'
    assert [f for f in spec.config_fields if not f.advanced] == []


def test_status_never_runs_tests(plugin, mocker):
    run = mocker.patch.object(test_runner, 'run')
    detect = mocker.patch.object(test_runner, 'detect')
    mocker.patch.object(test_runner, 'status', return_value={
        'badge': '–', 'status': 'normal', 'sublabel': 'tap to run',
        'menu': []})
    result = plugin.execute_action('dev_run_tests', {'op': 'status'})
    assert result['success'] is True and result['data']['badge'] == '–'
    run.assert_not_called()
    detect.assert_not_called()


def test_status_passes_watch_flag(plugin, mocker):
    status = mocker.patch.object(test_runner, 'status', return_value={
        'badge': '–', 'sublabel': ''})
    plugin.execute_action('dev_run_tests', {'op': 'status', 'watch': True})
    status.assert_called_once_with('C:/work/proj', watch=True)


def test_run_uses_detected_plans(plugin, mocker):
    plans = [test_runner.TestPlan('proj', ('x',), 'C:/work/proj', 'pytest')]
    mocker.patch.object(test_runner, 'detect', return_value=plans)
    run = mocker.patch.object(test_runner, 'run',
                              return_value={'success': True, 'message': 'ok'})
    plugin.execute_action('dev_run_tests', {})
    run.assert_called_once_with('C:/work/proj', plans)


def test_run_prefers_configured_command(plugin, mocker):
    run = mocker.patch.object(test_runner, 'run',
                              return_value={'success': True, 'message': 'ok'})
    plugin.execute_action('dev_run_tests', {'command': 'npx vitest run'})
    plan = run.call_args[0][1][0]
    assert plan.argv == ('npx', 'vitest', 'run')


def test_nothing_detected_empty_state(plugin, mocker):
    mocker.patch.object(test_runner, 'detect', return_value=[])
    result = plugin.execute_action('dev_run_tests', {})
    assert result['success'] is False
    assert result['message'] == ('No tests found in proj - set a test '
                                 'command under Advanced')


def test_fix_op_sends_fix_tests_preset(plugin, mocker):
    send = mocker.patch.object(agent_prompt, 'prompt_preset',
                               return_value={'success': True, 'message': 'x'})
    plugin.execute_action('dev_run_tests', {'op': 'fix'})
    send.assert_called_once_with('fix_tests', cwd='C:/work/proj')


# --- Phase 3: git / dev servers / docker ------------------------------------

LIVE_IDS = ('git_context', 'dev_servers', 'docker_status')


def _live_specs(plugin):
    return {s.id: s for s in plugin.get_action_specs() if s.id in LIVE_IDS}


def test_live_specs_are_menu_buttons_with_no_visible_field(plugin):
    specs = _live_specs(plugin)
    assert set(specs) == set(LIVE_IDS)
    for spec in specs.values():
        assert spec.press == 'menu' and spec.category == 'dev'
        assert spec.poll_config == {'op': 'status'} and spec.poll_seconds > 0
        assert [f.name for f in spec.config_fields if not f.advanced] == []
    assert [specs[i].poll_seconds for i in LIVE_IDS] == [30, 10, 20]


def test_docker_unavailable_reason_without_cli(mocker):
    mocker.patch.object(pack.sr, 'find_binary', return_value=None)
    spec = _live_specs(pack.Plugin())['docker_status']
    assert spec.unavailable_reason == 'Docker CLI not found - install Docker Desktop'
    assert pack.Plugin().is_available() == (True, '')


@pytest.mark.parametrize('action_id,service', [
    ('git_context', git_context), ('dev_servers', dev_servers),
    ('docker_status', docker_status)])
def test_live_status_default_and_ops_dispatch(plugin, mocker, action_id, service):
    status = mocker.patch.object(service, 'status', return_value={'success': True})
    run_op = mocker.patch.object(service, 'run_op', return_value={'success': True})
    plugin.execute_action(action_id, {'op': 'status'})
    plugin.execute_action(action_id, {})
    status.assert_called_with('C:/work/proj')
    assert status.call_count == 2
    run_op.assert_not_called()
    plugin.execute_action(action_id, {'op': 'pull'})
    run_op.assert_called_once_with('C:/work/proj', 'pull')


def test_live_missing_binary_is_a_friendly_failure(plugin, mocker):
    mocker.patch.object(git_context, 'run_op',
                        side_effect=pack.sr.BinaryNotFoundError('git not found'))
    out = plugin.execute_action('git_context', {'op': 'pull'})
    assert out == {'success': False, 'message': 'git not found'}