"""DL-145: dev_run_tests catalog action."""
import pytest

from integrations import context
from integrations import dev_tools_pack as pack
from services import agent_prompt, test_runner


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
