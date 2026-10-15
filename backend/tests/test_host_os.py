"""DL-006: shortcuts follow the host OS."""
import json
import os
from unittest import mock

import pytest

from utils import host_os

TEMPLATES = os.path.join(os.path.dirname(__file__), '..', 'data', 'templates')


def as_os(name):
    return mock.patch('utils.host_os.platform',
                      mock.Mock(system=lambda: name))


def template(tid):
    for f in os.listdir(TEMPLATES):
        data = json.load(open(os.path.join(TEMPLATES, f), encoding='utf-8'))
        if data['id'] == tid:
            return data
    raise KeyError(tid)


def buttons(t):
    return {b['label']: b for p in t['pages'] for b in p['buttons']}


@pytest.mark.parametrize('system,expected,mod', [
    ('Darwin', 'macos', 'cmd'), ('Windows', 'windows', 'ctrl'),
    ('Linux', 'linux', 'ctrl')])
def test_host_os_and_modifier(system, expected, mod):
    with as_os(system):
        assert host_os.host_os() == expected
        assert host_os.primary_modifier() == mod


def test_localize_keys_rules():
    with as_os('Darwin'):
        assert host_os.localize_keys(('ctrl', 's')) == ('cmd', 's')
        assert host_os.localize_keys(('ctrl', '`')) == ('ctrl', '`')
        assert host_os.localize_keys(('ctrl', 'alt', 'down')) == ('ctrl', 'alt', 'down')
        assert host_os.localize_keys(('f12',)) == ('f12',)
    with as_os('Windows'):
        assert host_os.localize_keys(('ctrl', 's')) == ('ctrl', 's')


def test_cursor_template_on_macos_uses_cmd_and_glyph_labels():
    with as_os('Darwin'):
        b = buttons(host_os.localize_template(template('template-ide-cursor')))
    assert b['Command']['action']['config']['keys'] == ['cmd', 'shift', 'p']
    assert b['Command']['secondary_label'] == '⌘+⇧+P'
    assert b['Terminal']['action']['config']['keys'] == ['ctrl', '`']
    assert b['Terminal']['secondary_label'] == '⌃+`'
    assert b['Format']['secondary_label'] == '⇧+⌥+F'
    assert b['Definition']['secondary_label'] == 'F12'


def test_macro_steps_inside_a_button_are_localized():
    with as_os('Darwin'):
        b = buttons(host_os.localize_template(template('template-ide-cursor')))
    steps = json.dumps(b['Save All']['action'])
    assert '"cmd", "k"' in steps and '"ctrl", "k"' not in steps


def test_windows_and_linux_templates_are_untouched():
    for system in ('Windows', 'Linux'):
        with as_os(system):
            t = template('template-ide-cursor')
            assert host_os.localize_template(t) is t


def test_jetbrains_is_never_remapped():
    with as_os('Darwin'):
        t = template('template-ide-jetbrains')
        assert host_os.localize_template(t) is t


def test_localize_does_not_mutate_the_source():
    t = template('template-ide-cursor')
    before = json.dumps(t)
    with as_os('Darwin'):
        host_os.localize_template(t)
    assert json.dumps(t) == before


def test_mod_token_resolves_per_os():
    from actions.hotkey_action import HotkeyAction
    action = HotkeyAction({'keys': ['mod', 's']})
    with as_os('Darwin'):
        assert action._parse_key('mod') == action._parse_key('cmd')
    with as_os('Windows'):
        assert action._parse_key('mod') == action._parse_key('ctrl')


def test_host_endpoint_and_template_apply_route(client=None):
    from app import app
    c = app.test_client()
    with as_os('Darwin'):
        assert c.get('/api/system/host').get_json() == {
            'os': 'macos', 'primary_modifier': 'cmd'}
        scene = c.post('/api/templates/template-ide-cursor/apply').get_json()['scene']
    keys = [b['action']['config']['keys'] for p in scene['pages']
            for b in p['buttons'] if b['label'] == 'Save']
    assert keys == [['cmd', 's']]


def test_app_profiles_api_emits_host_native_keys():
    from app import app
    c = app.test_client()
    def cursor_keys():
        profiles = c.get('/api/app-profiles').get_json()['profiles']
        cursor = next(p for p in profiles if p['id'] == 'cursor')
        return [cmd['keys'] for cmd in cursor['commands'] if cmd['keys']]
    with as_os('Darwin'), mock.patch('integrations.keymaps.base.platform',
                                     mock.Mock(system=lambda: 'Darwin')):
        mac = cursor_keys()
    with as_os('Windows'):
        win = cursor_keys()
    assert any('cmd' in k for k in mac) and not any('cmd' in k for k in win)
