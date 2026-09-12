"""Tests for plugin action dispatch and catalog contribution.

Feature: ai-dev-integration-packs, Property 1.2: a plugin's actions are
executable and show up in the picker.

PluginManager.execute_plugin_action() was fully implemented but had no caller
anywhere in the backend, and ActionExecutor.ACTION_CLASSES had no entry for
plugin actions, so every plugin action returned "Unknown action type". The
plugin system loaded but could not run anything. ActionExecutor now falls
through to the plugin manager, which is what lets the integration packs add
actions without touching the core dispatch table.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from actions.action_executor import ActionExecutor  # noqa: E402
from actions.catalog import ActionSpec  # noqa: E402
from plugins.base_plugin import BasePlugin, PluginInfo  # noqa: E402
from plugins.plugin_manager import PluginManager  # noqa: E402


class FakePlugin(BasePlugin):
    """A minimal plugin that records the configs it was handed."""

    def __init__(self, available=True, reason=''):
        super().__init__()
        self.calls = []
        self._available = available
        self._reason = reason

    def get_info(self):
        return PluginInfo(
            id='fake', name='Fake Pack', version='1.0.0', author='tests',
            description='Test double',
            actions=['fake_do_thing', 'fake_with_config'],
        )

    def initialize(self):
        return True

    def cleanup(self):
        pass

    def is_available(self):
        return self._available, self._reason

    def execute_action(self, action_id, config):
        self.calls.append((action_id, config))
        return {'success': True, 'message': f'ran {action_id}',
                'data': {'echo': config}}

    def get_action_schema(self, action_id):
        if action_id == 'fake_with_config':
            return {
                'type': 'object',
                'properties': {
                    'target': {'type': 'string', 'title': 'Target',
                               'description': 'What to act on'},
                    'count': {'type': 'integer', 'title': 'Count',
                              'default': 3},
                    'mode': {'type': 'string', 'enum': ['fast', 'slow']},
                },
                'required': ['target'],
            }
        return {'type': 'object', 'properties': {}, 'required': []}


@pytest.fixture
def manager():
    mgr = PluginManager()
    plugin = FakePlugin()
    plugin.initialize()
    mgr.plugins['fake'] = plugin
    for action_id in plugin.get_info().actions:
        mgr.plugin_actions[action_id] = 'fake'
    plugin.enable()
    return mgr


# --- dispatch ----------------------------------------------------------------

def test_plugin_action_executes_through_the_executor(manager):
    executor = ActionExecutor(manager)

    result = executor.execute_action(
        {'type': 'fake_do_thing', 'config': {}}
    )

    assert result.success is True
    assert result.message == 'ran fake_do_thing'


def test_plugin_action_receives_its_config(manager):
    executor = ActionExecutor(manager)

    executor.execute_action(
        {'type': 'fake_with_config', 'config': {'target': 'x', 'count': 9}}
    )

    action_id, config = manager.plugins['fake'].calls[-1]
    assert action_id == 'fake_with_config'
    assert config == {'target': 'x', 'count': 9}


def test_unknown_type_still_reports_unknown(manager):
    executor = ActionExecutor(manager)

    result = executor.execute_action({'type': 'not_a_real_action', 'config': {}})

    assert result.success is False
    assert 'Unknown action type' in result.message


def test_executor_without_a_plugin_manager_does_not_crash():
    result = ActionExecutor().execute_action(
        {'type': 'fake_do_thing', 'config': {}}
    )

    assert result.success is False
    assert 'Unknown action type' in result.message


def test_builtin_action_is_not_shadowed_by_a_plugin(manager):
    """A plugin must not be able to hijack a core action type."""
    manager.plugin_actions['url'] = 'fake'
    executor = ActionExecutor(manager)

    executor.execute_action({'type': 'url', 'config': {'url': ''}})

    # URLAction handled it; the plugin was never consulted.
    assert all(call[0] != 'url' for call in manager.plugins['fake'].calls)


def test_plugin_failure_is_reported_faithfully(manager):
    manager.plugins['fake'].execute_action = lambda a, c: {
        'success': False, 'message': 'upstream is down'
    }
    executor = ActionExecutor(manager)

    result = executor.execute_action({'type': 'fake_do_thing', 'config': {}})

    assert result.success is False
    assert result.message == 'upstream is down'


def test_plugin_exception_does_not_escape(manager):
    def boom(action_id, config):
        raise RuntimeError('kaboom')

    manager.plugins['fake'].execute_action = boom
    executor = ActionExecutor(manager)

    result = executor.execute_action({'type': 'fake_do_thing', 'config': {}})

    assert result.success is False
    assert 'kaboom' in result.message


# --- catalog contribution ----------------------------------------------------

def test_plugin_actions_appear_in_the_catalog(manager):
    specs = {spec.id: spec for spec in manager.get_action_specs()}

    assert 'fake_do_thing' in specs
    assert 'fake_with_config' in specs


def test_derived_spec_is_labelled_and_categorised(manager):
    spec = next(s for s in manager.get_action_specs() if s.id == 'fake_do_thing')

    assert spec.label == 'Fake Do Thing'
    assert spec.category == 'custom'
    assert spec.action_type == 'fake_do_thing'


def test_json_schema_becomes_config_fields(manager):
    spec = next(
        s for s in manager.get_action_specs() if s.id == 'fake_with_config'
    )
    fields = {f.name: f for f in spec.config_fields}

    assert fields['target'].required is True
    assert fields['target'].label == 'Target'
    assert fields['count'].type == 'number'
    assert fields['count'].default == 3
    assert fields['mode'].type == 'select'
    assert {o['value'] for o in fields['mode'].options} == {'fast', 'slow'}


def test_unavailable_plugin_is_listed_with_a_reason():
    mgr = PluginManager()
    plugin = FakePlugin(available=False, reason='gh CLI not found on PATH')
    plugin.initialize()
    mgr.plugins['fake'] = plugin
    for action_id in plugin.get_info().actions:
        mgr.plugin_actions[action_id] = 'fake'

    specs = mgr.get_action_specs()

    assert specs
    assert all(s.unavailable_reason == 'gh CLI not found on PATH' for s in specs)


def test_declared_specs_win_over_derivation(manager):
    """A pack that describes itself fully keeps its own metadata."""
    declared = (
        ActionSpec(id='fake_do_thing', label='Do The Thing', category='ai',
                   icon=('fas', 'robot'), action_type='fake_do_thing'),
    )
    manager.plugins['fake'].get_action_specs = lambda: declared

    spec = next(s for s in manager.get_action_specs() if s.id == 'fake_do_thing')

    assert spec.label == 'Do The Thing'
    assert spec.category == 'ai'


def test_catalog_endpoint_includes_plugin_actions(manager, monkeypatch):
    import app as app_module
    from actions.catalog import catalog_to_dict

    monkeypatch.setattr(app_module, 'plugin_manager', manager)
    client = app_module.app.test_client()

    payload = client.get('/api/actions/catalog').get_json()
    ids = {a['id'] for a in payload['actions']}

    assert 'fake_do_thing' in ids
    # Built-in entries are still there.
    assert 'volume_up' in ids
    assert len(payload['actions']) == len(catalog_to_dict()['actions']) + 2
