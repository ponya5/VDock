"""DL-145: live-action metadata on the catalog + status ops skip the job runner."""
from actions.base_action import ActionResult
from actions.catalog import ActionSpec, ConfigField


def test_config_field_advanced_and_show_when_serialised():
    d = ConfigField('text', 'Text', 'textarea', advanced=True,
                    show_when={'preset': 'custom'}).to_dict()
    assert d['advanced'] is True
    assert d['show_when'] == {'preset': 'custom'}


def test_config_field_defaults_not_serialised():
    d = ConfigField('text', 'Text').to_dict()
    assert 'advanced' not in d
    assert 'show_when' not in d


def test_action_spec_live_fields_serialised():
    live = ActionSpec(id='x', label='X', category='dev', icon=('fas', 'a'),
                      action_type='x', poll_seconds=15,
                      poll_config={'op': 'status'}, press='menu').to_dict()
    assert live['poll_seconds'] == 15
    assert live['poll_config'] == {'op': 'status'}
    assert live['press'] == 'menu'

    plain = ActionSpec(id='x', label='X', category='dev', icon=('fas', 'a'),
                       action_type='x').to_dict()
    for key in ('poll_seconds', 'poll_config', 'press'):
        assert key not in plain


def _post(mocker, config):
    import app as app_module
    mocker.patch.object(app_module.action_executor, 'is_long_running',
                        return_value=True)
    execute = mocker.patch.object(app_module.action_executor,
                                  'execute_action',
                                  return_value=ActionResult(True, 'ok'))
    client = app_module.app.test_client()
    response = client.post('/api/actions/execute', json={
        'action': {'type': 'dev_run_tests', 'config': config}})
    return response, execute


def test_status_op_runs_synchronously_even_for_long_running_type(mocker):
    response, execute = _post(mocker, {'op': 'status'})
    assert response.status_code == 200
    assert execute.call_count == 1


def test_non_status_op_still_goes_to_job_runner(mocker):
    response, _ = _post(mocker, {'op': 'run'})
    assert response.status_code == 202
    assert response.get_json()['pending'] is True
