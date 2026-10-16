"""DL-007 — "Allow LAN" really applies, macOS LAN address, macOS session hosts.

Runs on every OS: macOS-only paths are reached by patching platform.system and
faking the AppKit / psutil views, Windows paths stay pinned by their own tests.
"""
import importlib.util
import io
import json
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config as config_module  # noqa: E402
from app import app  # noqa: E402
from config import Config  # noqa: E402
from integrations import editor_base, sessions  # noqa: E402
from integrations.keymaps.claude_code import CLAUDE_CODE_COMMANDS  # noqa: E402
from utils import window_focus  # noqa: E402

LAUNCHER = Path(__file__).resolve().parents[2] / 'scripts' / 'VDock-Launcher.py'


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def bound(monkeypatch):
    """Pretend the server bound with LAN off / HTTP, then let tests flip switches."""
    monkeypatch.setattr(Config, 'ALLOW_LAN', False)
    monkeypatch.setattr(Config, 'USE_SSL', False)
    monkeypatch.setattr(Config, 'BOUND_LAN', None)
    monkeypatch.setattr(Config, 'BOUND_SSL', None)
    Config.record_bind()
    return Config


# ---------------------------------------------------------------------------
# Startup-only switches
# ---------------------------------------------------------------------------

def test_not_serving_never_asks_for_a_restart(monkeypatch):
    monkeypatch.setattr(Config, 'BOUND_LAN', None)
    monkeypatch.setattr(Config, 'ALLOW_LAN', True)
    assert Config.restart_required() is False
    assert Config.lan_reachable() is True


def test_lan_toggled_after_start_needs_restart(bound):
    assert Config.restart_required() is False
    Config.ALLOW_LAN = True
    assert Config.restart_required() is True
    # The switch says on, but the socket is still loopback-only.
    assert Config.lan_reachable() is False


def test_https_toggled_after_start_needs_restart(bound, monkeypatch):
    monkeypatch.setattr(Config, 'USE_SSL', True)
    assert Config.restart_required() is True


def test_bind_host(monkeypatch):
    monkeypatch.setattr(Config, 'HOST', '127.0.0.1')
    monkeypatch.setattr(Config, 'ALLOW_LAN', False)
    assert Config.bind_host() == '127.0.0.1'
    monkeypatch.setattr(Config, 'ALLOW_LAN', True)
    assert Config.bind_host() == '0.0.0.0'
    monkeypatch.setattr(Config, 'HOST', '192.168.0.14')
    assert Config.bind_host() == '192.168.0.14'


def test_health_and_config_report_the_pending_restart(bound, client):
    Config.ALLOW_LAN = True
    health = client.get('/api/health').get_json()
    assert health['restart_required'] is True
    cfg = client.get('/api/config').get_json()['config']
    assert cfg['allow_lan'] is True
    assert cfg['lan_reachable'] is False
    assert cfg['restart_required'] is True


def test_restart_route_uses_the_updater_relaunch(client, mocker):
    from services import updater
    restart = mocker.patch.object(updater, 'restart_self')
    mocker.patch.object(updater, 'is_busy', return_value=False)
    response = client.post('/api/system/restart')
    assert response.status_code == 202
    restart.assert_called_once()


def test_restart_route_refuses_other_devices(client, mocker):
    from services import updater
    restart = mocker.patch.object(updater, 'restart_self')
    response = client.post('/api/system/restart',
                           environ_base={'REMOTE_ADDR': '192.168.0.50'})
    assert response.status_code == 403
    restart.assert_not_called()


def test_restart_route_waits_for_an_update(client, mocker):
    from services import updater
    restart = mocker.patch.object(updater, 'restart_self')
    mocker.patch.object(updater, 'is_busy', return_value=True)
    assert client.post('/api/system/restart').status_code == 409
    restart.assert_not_called()


# ---------------------------------------------------------------------------
# Launcher: relaunch applies the switch instead of reusing the old backend
# ---------------------------------------------------------------------------

@pytest.fixture
def launcher(monkeypatch):
    # The launcher imports its sibling scripts (electron_branding).
    monkeypatch.syspath_prepend(str(LAUNCHER.parent))
    spec = importlib.util.spec_from_file_location('vdock_launcher_dl007', LAUNCHER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _healthy_running_backend(monkeypatch, launcher, needs_restart):
    killed = []
    monkeypatch.setattr(launcher, 'count_listeners_on_port', lambda port: 1)
    monkeypatch.setattr(launcher, 'port_serves_vdock_backend', lambda port: True)
    monkeypatch.setattr(launcher, 'backend_supports_user_settings', lambda port=0: True)
    monkeypatch.setattr(launcher, 'backend_code_is_newer', lambda port=0: False)
    monkeypatch.setattr(launcher, 'backend_needs_settings_restart', lambda port=0: needs_restart)
    monkeypatch.setattr(launcher, 'backend_env_is_newer', lambda port=0: False)
    monkeypatch.setattr(launcher, 'kill_process_on_port', lambda port: killed.append(port) or True)
    monkeypatch.setattr(launcher, 'launch_backend', lambda venv: True)
    monkeypatch.setattr(launcher, 'wait_for_url', lambda *a, **k: True)
    monkeypatch.setattr(launcher.time, 'sleep', lambda s: None)
    return killed


def test_launcher_restarts_backend_with_pending_lan_switch(monkeypatch, launcher):
    killed = _healthy_running_backend(monkeypatch, launcher, needs_restart=True)
    assert launcher.ensure_fresh_backend(Path('venv'), port=5001) is True
    assert killed == [5001]


def test_launcher_keeps_an_up_to_date_backend(monkeypatch, launcher):
    killed = _healthy_running_backend(monkeypatch, launcher, needs_restart=False)
    assert launcher.ensure_fresh_backend(Path('venv'), port=5001) is True
    assert killed == []


def test_launcher_restarts_after_env_edit(monkeypatch, launcher, tmp_path):
    env = tmp_path / '.env'
    env.write_text('PORT=5001\n')
    monkeypatch.setattr(launcher, 'BACKEND_PATH', tmp_path)
    now = launcher.time.time()
    os.utime(env, (now, now))
    monkeypatch.setattr(launcher, 'backend_started_at', lambda port=0: now - 600)
    assert launcher.backend_env_is_newer(5001) is True
    monkeypatch.setattr(launcher, 'backend_started_at', lambda port=0: now + 1)
    assert launcher.backend_env_is_newer(5001) is False


@pytest.mark.parametrize('payload,expected', [
    ({'uptime_s': 5, 'restart_required': True}, True),
    ({'uptime_s': 5, 'restart_required': False}, False),
    ({'uptime_s': 5}, False),  # older backend without the field
])
def test_launcher_reads_restart_required_from_health(launcher, payload, expected):
    body = io.BytesIO(json.dumps(payload).encode())
    body.__enter__ = lambda self=body: self
    body.__exit__ = lambda *a: False
    with mock.patch.object(launcher.urllib.request, 'urlopen', return_value=body):
        assert launcher.backend_needs_settings_restart(5001) is expected


def test_launcher_only_kills_listeners_never_connected_clients(monkeypatch, launcher):
    """A bare ``lsof -ti :PORT`` also returns clients (the deck window's
    network process, a browser) -- those were counted as duplicate backends
    and kill -9'd on every restart."""
    queries, killed = [], []

    def run(argv, **kwargs):
        if argv[0] == 'lsof':
            queries.append(argv)
            return mock.Mock(stdout='8479\n')
        killed.append(argv)
        return mock.Mock()

    monkeypatch.setattr(launcher, 'IS_WINDOWS', False)
    monkeypatch.setattr(launcher.subprocess, 'run', run)
    assert launcher.count_listeners_on_port(5001) == 1
    assert launcher.kill_process_on_port(5001) is True
    for argv in queries:
        assert '-sTCP:LISTEN' in argv and '-iTCP:5001' in argv
    assert killed == [['kill', '-9', '8479']]


# ---------------------------------------------------------------------------
# macOS LAN address
# ---------------------------------------------------------------------------

def test_macos_vpn_tunnel_is_not_the_deck_address(mocker):
    mocker.patch.object(config_module, '_probe_ip', return_value='10.8.0.5')
    mocker.patch.object(config_module, '_iface_candidates', return_value=[
        ('utun4', '10.8.0.5'), ('en0', '192.168.0.14')])
    assert config_module.lan_ip() == '192.168.0.14'


@pytest.mark.parametrize('name,virtual', [
    ('utun3', True), ('ipsec0', True), ('bridge100', True), ('ppp0', True),
    ('en0', False), ('en1', False),
    # Windows names keep their old meaning: a "Network Bridge" bridges real NICs.
    ('Network Bridge', False), ('Wi-Fi', False), ('vEthernet (WSL)', True),
])
def test_virtual_interface_names(name, virtual):
    assert config_module._is_virtual_iface(name) is virtual


# ---------------------------------------------------------------------------
# macOS session hosts
# ---------------------------------------------------------------------------

class FakeProc:
    def __init__(self, pid, exe, parents=(), cwd=None, tty=None, created=0.0):
        self.pid = pid
        self._exe = exe
        self._parents = list(parents)
        self._cwd = cwd
        self._tty = tty
        self._created = created

    def exe(self):
        return self._exe

    def parents(self):
        return self._parents

    def cwd(self):
        return self._cwd

    def terminal(self):
        return self._tty

    def create_time(self):
        return self._created


CURSOR = '/Applications/Cursor.app'
TERMINAL = '/System/Applications/Utilities/Terminal.app'
REGULAR_APPS = {
    CURSOR.lower(): (300, CURSOR),
    TERMINAL.lower(): (400, TERMINAL),
}


def _cursor_session():
    cursor = FakeProc(300, CURSOR + '/Contents/MacOS/Cursor')
    helper = FakeProc(301, CURSOR + '/Contents/Frameworks/Cursor Helper.app/Contents/MacOS/Cursor Helper')
    shell = FakeProc(302, '/bin/zsh')
    return FakeProc(10, '/Users/you/.local/share/claude/versions/2.1.0',
                    parents=[shell, helper, cursor],
                    cwd='/Users/you/code/VDock', tty='/dev/ttys001', created=100.0)


def _terminal_session():
    terminal = FakeProc(400, TERMINAL + '/Contents/MacOS/Terminal')
    login = FakeProc(401, '/usr/bin/login')
    shell = FakeProc(402, '/bin/zsh')
    return FakeProc(20, '/Users/you/.local/share/claude/versions/2.1.0',
                    parents=[shell, login, terminal],
                    cwd='/Users/you/code/other', tty='/dev/ttys003', created=200.0)


def _headless_session():
    backend = FakeProc(500, '/Users/you/VDock/backend/venv/bin/python')
    return FakeProc(30, '/Users/you/.local/bin/claude', parents=[backend], created=300.0)


@pytest.fixture
def mac(mocker):
    procs = {p.pid: p for p in (_cursor_session(), _terminal_session(), _headless_session())}
    mocker.patch.object(window_focus.platform, 'system', return_value='Darwin')
    mocker.patch.object(window_focus, '_session_pids', return_value=list(procs))
    mocker.patch.object(window_focus, '_macos_regular_app_pids', return_value=dict(REGULAR_APPS))
    mocker.patch('psutil.Process', side_effect=lambda pid: procs[int(pid)])
    return procs


@pytest.mark.parametrize('path,bundle', [
    (CURSOR + '/Contents/Frameworks/Cursor Helper.app/Contents/MacOS/Cursor Helper', CURSOR),
    (TERMINAL + '/Contents/MacOS/Terminal', TERMINAL),
    ('/Applications/iTerm.app/Contents/MacOS/iTermServer-3.5.0', '/Applications/iTerm.app'),
    ('/bin/zsh', None),
    (None, None),
])
def test_outer_app_bundle(path, bundle):
    assert window_focus._outer_app_bundle(path) == bundle


def test_sessions_resolve_to_their_host_app(mac):
    rows = window_focus.list_session_hosts('claude')
    # Headless session (no GUI ancestor) is excluded; newest first.
    assert [r['pid'] for r in rows] == [20, 10]
    assert [r['host'] for r in rows] == ['Terminal', 'Cursor']
    assert rows[1]['title'] == 'Cursor — VDock'
    # The handle is the session pid -- unique even when two sessions share an app.
    assert [r['hwnd'] for r in rows] == [20, 10]


def test_resolver_ranks_project_then_newest_and_honours_pins(mac):
    assert window_focus.find_session_host_window('claude') == 20  # newest
    assert window_focus.find_session_host_window(
        'claude', prefer_cwd='/Users/you/code/VDock') == 10
    assert window_focus.find_session_host_window('claude', prefer_pid=10) == 10


def test_terminal_session_focuses_its_exact_tab(mac, mocker):
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        return mock.Mock(returncode=0, stdout='ok\n', stderr='')

    mocker.patch.object(window_focus.subprocess, 'run', side_effect=run)
    mocker.patch.object(window_focus, '_wait_frontmost', return_value=True)
    raise_window = mocker.patch.object(window_focus, '_raise_project_window')

    assert window_focus.focus_hwnd(20) is True
    osascript, activate = calls
    assert osascript[:2] == ['osascript', '-e']
    assert 'com.apple.Terminal' in osascript[2]
    # The tty travels as argv, never inside the script text.
    assert osascript[3] == '/dev/ttys003'
    assert '/dev/ttys003' not in osascript[2]
    assert activate == ['open', '-a', TERMINAL]
    raise_window.assert_not_called()


def test_editor_session_raises_project_window_then_activates(mac, mocker):
    run = mocker.patch.object(window_focus.subprocess, 'run',
                              return_value=mock.Mock(returncode=0, stdout='', stderr=''))
    mocker.patch.object(window_focus, '_wait_frontmost', return_value=True)
    raise_window = mocker.patch.object(window_focus, '_raise_project_window', return_value=True)

    assert window_focus.focus_hwnd(10) is True
    raise_window.assert_called_once_with(300, '/Users/you/code/VDock')
    run.assert_called_once_with(['open', '-a', CURSOR], capture_output=True, timeout=5)


def test_denied_automation_falls_back_to_the_app(mac, mocker):
    calls = []

    def run(argv, **kwargs):
        calls.append(argv[0])
        if argv[0] == 'osascript':
            return mock.Mock(returncode=1, stdout='', stderr='Not authorized (-1743)')
        return mock.Mock(returncode=0, stdout='', stderr='')

    mocker.patch.object(window_focus.subprocess, 'run', side_effect=run)
    mocker.patch.object(window_focus, '_wait_frontmost', return_value=True)
    mocker.patch.object(window_focus, '_raise_project_window', return_value=False)
    # One window only: activating the app cannot land in another shell (DL-017).
    mocker.patch.object(window_focus, '_visible_window_count', return_value=1)
    assert window_focus.focus_hwnd(20) is True
    assert calls == ['osascript', 'open']


def test_headless_session_cannot_be_focused(mac, mocker):
    run = mocker.patch.object(window_focus.subprocess, 'run')
    assert window_focus.focus_hwnd(30) is False
    run.assert_not_called()


def test_identify_raises_the_window_on_macos(mac, mocker):
    focus = mocker.patch.object(window_focus, '_focus_session_macos', return_value=True)
    assert window_focus.flash_window(20) is True
    focus.assert_called_once_with(20)


def test_session_host_frontmost(mac, mocker):
    mocker.patch.object(window_focus, '_frontmost_bundle_path_lsappinfo', return_value=CURSOR)
    assert window_focus.session_host_frontmost(10) is True
    assert window_focus.session_host_frontmost(20) is False


def test_session_host_frontmost_is_unknown_off_macos(mocker):
    mocker.patch.object(window_focus.platform, 'system', return_value='Windows')
    assert window_focus.session_host_frontmost(10) is None


@pytest.mark.parametrize('title,project,match', [
    ('editor_base.py — VDock', 'VDock', True),
    ('VDock', 'VDock', True),
    ('app.py — VDock [Extension Development Host]', 'VDock', True),
    ('main.ts — webapp', 'app', False),
])
def test_title_names_project(title, project, match):
    assert window_focus._title_names_project(title, project) is match


def test_project_names_walk_up_to_home(monkeypatch):
    monkeypatch.setenv('HOME', '/Users/you')
    # Windows expanduser consults USERPROFILE before HOME.
    monkeypatch.setenv('USERPROFILE', '/Users/you')
    assert window_focus._project_names('/Users/you/code/VDock/backend') == ['backend', 'VDock', 'code']
    assert window_focus._project_names(None) == []


# ---------------------------------------------------------------------------
# Keystroke guard: never type when the session's app is not in front
# ---------------------------------------------------------------------------

def test_keystrokes_refused_when_session_app_is_not_frontmost(mocker):
    command = next(c for c in CLAUDE_CODE_COMMANDS if c.id == 'cc_interrupt')
    mocker.patch.object(sessions, 'session_alive', return_value=True)
    mocker.patch.object(editor_base, '_resolve_session_host', return_value=20)
    mocker.patch.object(window_focus, 'foreground_hwnd', return_value=None)
    mocker.patch.object(window_focus, 'session_host_frontmost', return_value=False)
    macro = mocker.patch.object(editor_base, 'MacroAction')

    result = editor_base.send(command, focus_first=False)
    assert result['success'] is False
    assert result['message'] == 'The session window is not focused'
    macro.assert_not_called()


def test_keystrokes_sent_after_macos_focus(mocker):
    command = next(c for c in CLAUDE_CODE_COMMANDS if c.id == 'cc_interrupt')
    mocker.patch.object(sessions, 'session_alive', return_value=True)
    mocker.patch.object(editor_base, '_resolve_session_host', return_value=20)
    mocker.patch.object(window_focus, 'focus_hwnd', return_value=True)
    mocker.patch.object(window_focus, 'foreground_hwnd', return_value=None)
    mocker.patch.object(window_focus, 'session_host_frontmost', return_value=True)
    mocker.patch.object(editor_base.time, 'sleep')
    macro = mocker.patch.object(editor_base, 'MacroAction')
    macro.return_value.execute.return_value = mock.Mock(success=True, message='', details='', data=None)

    result = editor_base.send(command)
    assert result['success'] is True
    macro.assert_called_once()


# ---------------------------------------------------------------------------
# LAN probe: backend-side, because the page's CSP blocks a fetch to the LAN IP
# ---------------------------------------------------------------------------

def test_lan_probe_reports_a_listening_address(client, mocker, monkeypatch):
    from routes import system
    monkeypatch.setattr(Config, 'DECK_HOST', '')
    mocker.patch('config.lan_ip', return_value='192.168.0.14')
    connect = mocker.patch.object(system.socket, 'create_connection')
    body = client.get(f'/api/system/lan-probe?port={Config.PORT}').get_json()
    assert body == {'success': True, 'reachable': True, 'host': '192.168.0.14'}
    connect.assert_called_once_with(('192.168.0.14', Config.PORT), timeout=1.5)


def test_lan_probe_reports_a_loopback_only_server(client, mocker, monkeypatch):
    from routes import system
    monkeypatch.setattr(Config, 'DECK_HOST', 'deck.local')
    mocker.patch.object(system.socket, 'create_connection', side_effect=ConnectionRefusedError)
    body = client.get('/api/system/lan-probe').get_json()
    assert body['reachable'] is False and body['host'] == 'deck.local'


def test_lan_probe_is_not_a_port_scanner(client, mocker):
    from routes import system
    connect = mocker.patch.object(system.socket, 'create_connection')
    assert client.get('/api/system/lan-probe?port=22').status_code == 400
    connect.assert_not_called()


# ---------------------------------------------------------------------------
# macOS Accessibility: report it up front, one click to the grant
# ---------------------------------------------------------------------------

def test_permissions_report_accessibility_on_macos(client, mocker):
    from actions import macos_controls
    from utils import host_os
    mocker.patch.object(host_os, 'host_os', return_value='macos')
    mocker.patch.object(macos_controls, 'is_accessibility_trusted', return_value=False)
    mocker.patch.object(macos_controls, 'accessibility_client',
                        return_value={'name': 'python3.14', 'path': '/x/python3.14'})
    body = client.get('/api/system/permissions').get_json()
    assert body == {'success': True, 'os': 'macos', 'accessibility': False,
                    'accessibility_app': {'name': 'python3.14', 'path': '/x/python3.14'}}


def test_permissions_have_nothing_to_grant_on_windows(client, mocker):
    from utils import host_os
    mocker.patch.object(host_os, 'host_os', return_value='windows')
    body = client.get('/api/system/permissions').get_json()
    assert body['accessibility'] is None
    assert client.post('/api/system/permissions/accessibility').get_json()['accessibility'] is None


def test_accessibility_request_opens_the_grant_on_this_mac_only(client, mocker):
    from actions import macos_controls
    from utils import host_os
    mocker.patch.object(host_os, 'host_os', return_value='macos')
    request = mocker.patch.object(macos_controls, 'request_accessibility', return_value=False)
    assert client.post('/api/system/permissions/accessibility',
                       environ_base={'REMOTE_ADDR': '192.168.0.50'}).status_code == 403
    request.assert_not_called()
    assert client.post('/api/system/permissions/accessibility').get_json()['accessibility'] is False
    request.assert_called_once()


LSAPPINFO_LIST = '''
 1) "loginwindow" ASN:0x0-0x2002:
    bundleID="com.apple.loginwindow"
    bundle path="/System/Library/CoreServices/loginwindow.app"
    pid = 421 token=[sess=100021] type="UIElement" flavor=3
 2) "Terminal" ASN:0x0-0x739739:
    bundleID="com.apple.Terminal"
    bundle path="/System/Applications/Utilities/Terminal.app"
    executable path="/System/Applications/Utilities/Terminal.app/Contents/MacOS/Terminal"
    pid = 11235 type="Foreground" flavor=3 Version="466"
 3) "Cursor" ASN:0x0-0x1b01b:
    bundleID="com.todesktop.230313mzl4w4u92"
    bundle path="/Applications/Cursor.app"
    pid = 3486 type="Foreground" flavor=3
'''


def test_running_apps_read_fresh_from_lsappinfo(mocker):
    """NSWorkspace never sees apps launched after the backend started (no
    run loop) -- a Terminal opened by "Open Claude" stayed invisible."""
    mocker.patch.object(window_focus.subprocess, 'run',
                        return_value=mock.Mock(stdout=LSAPPINFO_LIST))
    assert window_focus._lsappinfo_foreground_apps() == [
        (11235, '/System/Applications/Utilities/Terminal.app'),
        (3486, '/Applications/Cursor.app'),
    ]
    assert window_focus._macos_regular_apps() == [
        ('terminal.app', '/System/Applications/Utilities/Terminal.app'),
        ('cursor.app', '/Applications/Cursor.app'),
    ]
