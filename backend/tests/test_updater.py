"""DL-150 in-app updater: release check, install kinds, install endpoint.

All network, subprocess and process-exit paths are mocked.
"""
import hashlib
import sys
from pathlib import Path

import pytest
from flask import Flask

from auth import AuthManager
from config import Config
from routes.update import update_bp
from services import updater
from version import __version__


def _release(tag='v99.0.0', assets=None, body='notes'):
    return {
        'tag_name': tag,
        'body': body,
        'html_url': 'https://github.com/ponya5/VDock/releases/tag/' + tag,
        'assets': assets if assets is not None else [],
    }


def _asset(name, size=3, digest=None):
    a = {
        'name': name,
        'size': size,
        'browser_download_url': f'https://github.com/ponya5/VDock/releases/download/v99.0.0/{name}',
    }
    if digest:
        a['digest'] = digest
    return a


@pytest.fixture(autouse=True)
def clean_state(monkeypatch):
    updater.reset_cache()
    monkeypatch.setattr(updater, '_started', False)
    yield
    updater.reset_cache()


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(update_bp)
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def _mock_release(monkeypatch, release, calls=None):
    def fake():
        if calls is not None:
            calls.append(1)
        if isinstance(release, Exception):
            raise release
        return release
    monkeypatch.setattr(updater, '_fetch_latest', fake)


# ---- compare ----------------------------------------------------------------

def test_parse_version():
    assert updater.parse_version('v2.4.0') == (2, 4, 0)
    assert updater.parse_version('2.4.0') is None
    assert updater.parse_version('v2.4.0-beta') is None
    assert updater.parse_version(None) is None


def test_compare_is_numeric_not_lexical():
    assert updater.is_newer('v2.10.0', '2.9.0')
    assert updater.is_newer('v99.0.0')
    assert not updater.is_newer('v2.3.0', '2.3.0')
    assert not updater.is_newer('v2.2.9', '2.3.0')
    assert not updater.is_newer('nightly', '2.3.0')


# ---- status endpoint --------------------------------------------------------

def test_status_newer(client, monkeypatch):
    _mock_release(monkeypatch, _release('v99.0.0', body='x' * 10000))
    data = client.get('/api/update/status').get_json()
    assert set(data) == {'current', 'latest', 'available', 'notes', 'releaseUrl', 'downloadUrl',
                         'installKind', 'canAutoInstall', 'checkedAt', 'error', 'state',
                         'stateMessage'}
    assert data['available'] is True
    assert data['latest'] == '99.0.0'
    assert data['current'] == __version__
    assert len(data['notes']) == 4096
    assert data['error'] is None
    assert data['state'] == 'idle'


def test_status_equal_and_older(client, monkeypatch):
    _mock_release(monkeypatch, _release('v' + __version__))
    assert client.get('/api/update/status').get_json()['available'] is False
    updater.reset_cache()
    _mock_release(monkeypatch, _release('v0.0.1'))
    assert client.get('/api/update/status').get_json()['available'] is False


def test_status_offline_is_graceful(client, monkeypatch):
    _mock_release(monkeypatch, OSError('network down'))
    resp = client.get('/api/update/status')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['available'] is False
    assert 'network down' in data['error']


def test_cache_and_force_rate_limit(client, monkeypatch):
    calls = []
    _mock_release(monkeypatch, _release(), calls)
    client.get('/api/update/status')
    client.get('/api/update/status')
    assert len(calls) == 1
    client.get('/api/update/status?force=1')
    assert len(calls) == 2
    client.get('/api/update/status?force=1')  # within 60 s: served from cache
    assert len(calls) == 2


def test_cache_expires(client, monkeypatch):
    calls = []
    _mock_release(monkeypatch, _release(), calls)
    client.get('/api/update/status')
    monkeypatch.setattr(updater, '_cache_at', updater._cache_at - updater.CACHE_TTL - 1)
    client.get('/api/update/status')
    assert len(calls) == 2


def test_background_start_is_idempotent():
    spawned = []
    updater.start(lambda fn, *a: spawned.append((fn, a)), delay=0)
    updater.start(lambda fn, *a: spawned.append((fn, a)), delay=0)
    assert len(spawned) == 1


# ---- install kind + assets --------------------------------------------------

def _patch_platform(monkeypatch, frozen, platform, env=None, git=False):
    monkeypatch.setattr(sys, 'frozen', frozen, raising=False)
    monkeypatch.setattr(sys, 'platform', platform)
    for key in ('PORTABLE_EXECUTABLE_FILE', 'APPIMAGE'):
        monkeypatch.delenv(key, raising=False)
    for k, v in (env or {}).items():
        monkeypatch.setenv(k, v)

    class FakeRoot:
        def __truediv__(self, other):
            return type('P', (), {'exists': lambda self: git})()
    monkeypatch.setattr(updater, 'project_root', lambda: FakeRoot())


@pytest.mark.parametrize('frozen,platform,env,git,kind', [
    (False, 'win32', {}, True, 'source'),
    (True, 'win32', {'PORTABLE_EXECUTABLE_FILE': 'x'}, False, 'portable'),
    (True, 'win32', {}, False, 'windows-installer'),
    (True, 'darwin', {}, False, 'mac'),
    (True, 'linux', {'APPIMAGE': '/a.AppImage'}, False, 'appimage'),
    (True, 'linux', {}, False, 'manual'),
    (False, 'linux', {}, False, 'manual'),
])
def test_detect_install_kind(monkeypatch, frozen, platform, env, git, kind):
    _patch_platform(monkeypatch, frozen, platform, env, git)
    assert updater.detect_install_kind() == kind
    assert updater.can_auto_install(kind) == (kind in ('source', 'windows-installer'))


@pytest.mark.parametrize('name', [
    'VDock Setup 2.4.0.exe', 'VDock.Setup.2.4.0.exe', 'VDock-Setup-2.4.0.exe'])
def test_windows_asset_matching(name):
    assets = [_asset('VDock-Portable.exe'), _asset(name), _asset('x.dmg')]
    assert updater.pick_asset('windows-installer', assets)['name'] == name


def test_asset_per_kind():
    assets = [_asset('VDock-Portable.exe'), _asset('VDock-2.4.0.dmg'),
              _asset('VDock-2.4.0.AppImage'), _asset('VDock Setup 2.4.0.exe')]
    assert updater.pick_asset('portable', assets)['name'] == 'VDock-Portable.exe'
    assert updater.pick_asset('mac', assets)['name'].endswith('.dmg')
    assert updater.pick_asset('appimage', assets)['name'].endswith('.AppImage')
    assert updater.pick_asset('manual', assets) is None
    assert updater.pick_asset('source', assets) is None


def test_download_url_falls_back_to_release_page(client, monkeypatch):
    _patch_platform(monkeypatch, True, 'darwin')
    _mock_release(monkeypatch, _release(assets=[]))
    data = client.get('/api/update/status').get_json()
    assert data['installKind'] == 'mac'
    assert data['canAutoInstall'] is False
    assert data['downloadUrl'] == data['releaseUrl']


def test_download_url_is_asset_when_matching(client, monkeypatch):
    _patch_platform(monkeypatch, True, 'win32')
    _mock_release(monkeypatch, _release(assets=[_asset('VDock Setup 99.0.0.exe')]))
    data = client.get('/api/update/status').get_json()
    assert data['downloadUrl'].endswith('VDock%20Setup%2099.0.0.exe') or \
        data['downloadUrl'].endswith('VDock Setup 99.0.0.exe')


# ---- install endpoint -------------------------------------------------------

@pytest.fixture
def stub_worker(monkeypatch):
    started = []
    monkeypatch.setattr(updater, 'run_install', lambda info, kind: started.append(kind))
    return started


def _prime(monkeypatch, kind='windows-installer', tag='v99.0.0'):
    _patch_platform(monkeypatch, kind != 'source', 'win32',
                    git=(kind == 'source'))
    _mock_release(monkeypatch, _release(tag, assets=[_asset('VDock Setup 99.0.0.exe')]))
    updater.check(force=True)


def test_install_403_for_non_loopback(client, monkeypatch, stub_worker):
    _prime(monkeypatch)
    resp = client.post('/api/update/install', environ_overrides={'REMOTE_ADDR': '192.168.1.50'})
    assert resp.status_code == 403
    assert stub_worker == []


def test_install_403_for_lan_when_auth_on_but_no_token(client, monkeypatch, stub_worker):
    _prime(monkeypatch)
    Config.REQUIRE_AUTH = True
    resp = client.post('/api/update/install', environ_overrides={'REMOTE_ADDR': '192.168.1.50'})
    assert resp.status_code == 403


def test_install_lan_with_valid_token(client, monkeypatch, stub_worker):
    _prime(monkeypatch)
    Config.REQUIRE_AUTH = True
    token = AuthManager.generate_token({'authenticated': True})
    resp = client.post('/api/update/install',
                       headers={'Authorization': f'Bearer {token}'},
                       environ_overrides={'REMOTE_ADDR': '192.168.1.50'})
    assert resp.status_code == 202


def test_install_202_loopback(client, monkeypatch, stub_worker):
    _prime(monkeypatch)
    resp = client.post('/api/update/install', environ_overrides={'REMOTE_ADDR': '127.0.0.1'})
    assert resp.status_code == 202
    assert resp.get_json() == {'state': 'downloading'}


def test_install_409_no_update(client, monkeypatch, stub_worker):
    _prime(monkeypatch, tag='v' + __version__)
    resp = client.post('/api/update/install', environ_overrides={'REMOTE_ADDR': '127.0.0.1'})
    assert resp.status_code == 409


def test_install_409_when_kind_cannot_auto_install(client, monkeypatch, stub_worker):
    _patch_platform(monkeypatch, True, 'darwin')
    _mock_release(monkeypatch, _release())
    updater.check(force=True)
    resp = client.post('/api/update/install', environ_overrides={'REMOTE_ADDR': '127.0.0.1'})
    assert resp.status_code == 409


def test_install_409_when_busy(client, monkeypatch, stub_worker):
    _prime(monkeypatch)
    assert client.post('/api/update/install',
                       environ_overrides={'REMOTE_ADDR': '127.0.0.1'}).status_code == 202
    resp = client.post('/api/update/install', environ_overrides={'REMOTE_ADDR': '127.0.0.1'})
    assert resp.status_code == 409


# ---- Windows install path ---------------------------------------------------

def test_download_url_prefix_validation():
    with pytest.raises(updater.UpdateError):
        updater.validate_download_url('https://evil.example/VDock Setup 9.exe')
    with pytest.raises(updater.UpdateError):
        updater.validate_download_url('https://github.com/other/repo/releases/download/x/a.exe')
    assert updater.validate_download_url(
        'https://github.com/ponya5/VDock/releases/download/v1/a.exe')


def _fake_download(payload: bytes):
    def fake(url, dest):
        Path(dest).write_bytes(payload)
        return len(payload)
    return fake


def test_windows_install_writes_cmd_launches_detached_and_exits_75(monkeypatch, tmp_path):
    payload = b'abc'
    info = updater._summarize_release(_release(assets=[
        _asset('VDock Setup 99.0.0.exe', size=3,
               digest='sha256:' + hashlib.sha256(payload).hexdigest())]))
    monkeypatch.setattr(updater, '_update_dir', lambda: tmp_path)
    monkeypatch.setattr(updater, '_download', _fake_download(payload))
    popen_calls, exits = [], []
    monkeypatch.setattr(updater, '_spawn_detached',
                        lambda args, **kw: popen_calls.append((args, kw)))
    monkeypatch.setattr(updater, 'schedule_exit', lambda code, delay=1.5: exits.append(code))

    updater.run_install(info, 'windows-installer')

    cmd = (tmp_path / 'run-update.cmd').read_text(encoding='utf-8')
    assert 'timeout /t 3 /nobreak >nul' in cmd
    assert '/S --force-run' in cmd
    assert 'VDock Setup 99.0.0.exe' in cmd
    assert len(popen_calls) == 1
    args, kw = popen_calls[0]
    # A string, not a list: list2cmdline would mangle start's "" title.
    assert isinstance(args, str)
    assert args.startswith('cmd /c start "" /min "')
    assert args.endswith('run-update.cmd"')
    assert kw['creationflags'] & 0x00000008  # DETACHED_PROCESS
    assert kw['close_fds'] is True
    assert exits == [75]
    assert updater.get_state()['state'] == 'restarting'


def test_windows_install_size_mismatch(monkeypatch, tmp_path):
    info = updater._summarize_release(_release(assets=[_asset('VDock Setup 99.0.0.exe', size=10)]))
    monkeypatch.setattr(updater, '_update_dir', lambda: tmp_path)
    monkeypatch.setattr(updater, '_download', _fake_download(b'abc'))
    monkeypatch.setattr(updater, '_spawn_detached', lambda *a, **k: pytest.fail('launched'))
    monkeypatch.setattr(updater, 'schedule_exit', lambda *a, **k: pytest.fail('exited'))
    updater.run_install(info, 'windows-installer')
    assert updater.get_state()['state'] == 'error'
    assert not (tmp_path / 'run-update.cmd').exists()


def test_windows_install_digest_mismatch(monkeypatch, tmp_path):
    info = updater._summarize_release(_release(assets=[
        _asset('VDock Setup 99.0.0.exe', size=3, digest='sha256:' + '0' * 64)]))
    monkeypatch.setattr(updater, '_update_dir', lambda: tmp_path)
    monkeypatch.setattr(updater, '_download', _fake_download(b'abc'))
    monkeypatch.setattr(updater, '_spawn_detached', lambda *a, **k: pytest.fail('launched'))
    updater.run_install(info, 'windows-installer')
    state = updater.get_state()
    assert state['state'] == 'error'
    assert 'checksum' in state['message']


def test_windows_install_rejects_foreign_url(monkeypatch, tmp_path):
    asset = _asset('VDock Setup 99.0.0.exe')
    asset['browser_download_url'] = 'https://evil.example/VDock Setup 99.0.0.exe'
    info = updater._summarize_release(_release(assets=[asset]))
    monkeypatch.setattr(updater, '_update_dir', lambda: tmp_path)
    monkeypatch.setattr(updater, '_download', lambda *a: pytest.fail('downloaded'))
    updater.run_install(info, 'windows-installer')
    assert updater.get_state()['state'] == 'error'


# ---- source install path ----------------------------------------------------

class _Proc:
    def __init__(self, stdout='', stderr='', returncode=0):
        self.stdout, self.stderr, self.returncode = stdout, stderr, returncode


def test_source_refuses_dirty_tree(monkeypatch):
    runs = []

    def fake_run(cmd, **kw):
        runs.append(cmd)
        return _Proc(stdout=' M backend/app.py\n')
    monkeypatch.setattr(updater.subprocess, 'run', fake_run)
    monkeypatch.setattr(updater, 'schedule_exit', lambda *a, **k: pytest.fail('exited'))
    updater.run_install({}, 'source')
    state = updater.get_state()
    assert state['state'] == 'error'
    assert 'Local changes' in state['message']
    assert len(runs) == 1 and runs[0][:2] == ['git', 'status']


def test_source_happy_path_under_electron_exits_0(monkeypatch):
    runs = []

    def fake_run(cmd, **kw):
        runs.append((cmd, kw.get('cwd')))
        return _Proc()
    monkeypatch.setattr(updater.subprocess, 'run', fake_run)
    monkeypatch.setenv('VDOCK_ELECTRON', '1')
    monkeypatch.setattr(updater, '_npm', lambda: 'npm.cmd')
    exits = []
    monkeypatch.setattr(updater, 'schedule_exit', lambda code, delay=1.5: exits.append(code))
    monkeypatch.setattr(updater, '_spawn_detached', lambda *a, **k: pytest.fail('relaunched'))

    updater.run_install({}, 'source')

    cmds = [c for c, _ in runs]
    assert cmds[1] == ['git', 'pull', '--ff-only']
    assert cmds[2][:4] == [sys.executable, '-m', 'pip', 'install']
    assert cmds[3] == ['npm.cmd', 'install']
    assert cmds[4] == ['npm.cmd', 'run', 'build']
    assert exits == [0]
    assert updater.get_state()['state'] == 'restarting'


def test_source_without_electron_spawns_relaunch(monkeypatch, tmp_path):
    monkeypatch.setattr(updater.subprocess, 'run', lambda *a, **k: _Proc())
    monkeypatch.setattr(updater, '_update_dir', lambda: tmp_path)
    monkeypatch.delenv('VDOCK_ELECTRON', raising=False)
    spawned, exits = [], []
    monkeypatch.setattr(updater, '_spawn_detached',
                        lambda args, **kw: spawned.append((args, kw)))
    monkeypatch.setattr(updater, 'schedule_exit', lambda code, delay=1.5: exits.append(code))
    updater.run_install({}, 'source')
    assert len(spawned) == 1
    args = spawned[0][0]
    if updater.sys.platform == 'win32':
        assert isinstance(args, str) and args.endswith('relaunch.cmd"')
        script = (tmp_path / 'relaunch.cmd').read_text(encoding='utf-8')
        assert 'launch.bat' in script
        # The open window reloads itself; the launcher must not open another.
        assert 'set "VDOCK_UPDATE_RELAUNCH=1"' in script
        assert script.index('VDOCK_UPDATE_RELAUNCH') < script.index('launch.bat')
    else:
        assert 'launch.sh' in ' '.join(args)
        assert 'VDOCK_UPDATE_RELAUNCH=1' in ' '.join(args)
    assert exits == [0]


def test_source_command_failure_sets_error(monkeypatch):
    def fake_run(cmd, **kw):
        if cmd[:2] == ['git', 'pull']:
            return _Proc(stderr='fatal: Not possible to fast-forward', returncode=1)
        return _Proc()
    monkeypatch.setattr(updater.subprocess, 'run', fake_run)
    monkeypatch.setattr(updater, 'schedule_exit', lambda *a, **k: pytest.fail('exited'))
    updater.run_install({}, 'source')
    state = updater.get_state()
    assert state['state'] == 'error'
    assert 'fast-forward' in state['message']
