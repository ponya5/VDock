"""DL-010: the packaged app's backend runtime (frontend/electron/backend-runtime.js).

Electron now decides the backend port (never AirPlay's 5000 on macOS), backs
off instead of respawning a dying backend forever, and hands the backend the
user's login-shell PATH. The helpers are plain Node, so they are exercised
here through `node` - no Electron needed. Skipped when Node is not installed.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import textwrap
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
ELECTRON_DIR = REPO / 'frontend' / 'electron'
RUNTIME = ELECTRON_DIR / 'backend-runtime.js'
NODE = shutil.which('node')

needs_node = pytest.mark.skipif(NODE is None, reason='node is not installed')


def run_node(tmp_path, body):
    """Run an async JS body with `rt` = backend-runtime; returns its JSON result."""
    script = tmp_path / 'probe.js'
    script.write_text(
        f'const rt = require({json.dumps(str(RUNTIME))});\n'
        '(async () => {\n'
        f'{textwrap.indent(textwrap.dedent(body), "  ")}\n'
        '})().then((r) => { process.stdout.write(JSON.stringify(r)); },\n'
        '          (e) => { console.error(e); process.exit(1); });\n',
        encoding='utf-8',
    )
    out = subprocess.run([NODE, str(script)], capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


# --- .env handling ----------------------------------------------------------

@needs_node
def test_reads_port_from_env_text_like_dotenv(tmp_path):
    result = run_node(tmp_path, '''
        return [
          rt.readEnvPort('SECRET_KEY=x\\nPORT=5123\\n'),
          rt.readEnvPort('export PORT="5124" # chosen by VDock\\n'),
          rt.readEnvPort("PORT='5125'"),
          rt.readEnvPort('PORT=5000\\nPORT=5126\\n'),
          rt.readEnvPort('PORT=\\n'),
          rt.readEnvPort('PORT=80\\n'),
          rt.readEnvPort('BACKEND_PORT=5127\\n'),
          rt.readEnvPort(''),
        ]
    ''')
    assert result == [5123, 5124, 5125, 5126, None, None, None, None]


@needs_node
def test_upsert_keeps_other_lines_and_replaces_port(tmp_path):
    result = run_node(tmp_path, '''
        const text = '# VDock settings\\nSECRET_KEY=abc\\nPORT=5000\\n\\nAUTH_PASSWORD=pw\\nPORT=5001\\n'
        return [
          rt.upsertEnvText(text, { PORT: 5002 }),
          rt.upsertEnvText('', { PORT: 5003 }),
          rt.upsertEnvText('SECRET_KEY=abc', { PORT: 5004 }),
        ]
    ''')
    assert result[0] == '# VDock settings\nSECRET_KEY=abc\nPORT=5002\n\nAUTH_PASSWORD=pw\n'
    assert result[1] == 'PORT=5003\n'
    assert result[2] == 'SECRET_KEY=abc\nPORT=5004\n'


@needs_node
def test_write_env_keys_creates_the_data_dir_and_preserves_secrets(tmp_path):
    env_path = tmp_path / 'vdock-data' / '.env'
    run_node(tmp_path, f'''
        rt.writeEnvKeys({json.dumps(str(env_path))}, {{ PORT: 5001 }})
        rt.writeEnvKeys({json.dumps(str(env_path))}, {{ SECRET_KEY: 'k' }})
        rt.writeEnvKeys({json.dumps(str(env_path))}, {{ PORT: 5002 }})
        return true
    ''')
    assert env_path.read_text(encoding='utf-8') == 'PORT=5002\nSECRET_KEY=k\n'


@needs_node
def test_legacy_port_and_https_come_from_config_json(tmp_path):
    config = tmp_path / 'config.json'
    config.write_text(json.dumps({'port': 5000, 'use_ssl': True}), encoding='utf-8')
    broken = tmp_path / 'broken.json'
    broken.write_text('{not json', encoding='utf-8')
    result = run_node(tmp_path, f'''
        return [
          rt.readLegacyPort({json.dumps(str(config))}),
          rt.readUseSsl({json.dumps(str(config))}, ''),
          rt.readLegacyPort({json.dumps(str(broken))}),
          rt.readUseSsl({json.dumps(str(broken))}, 'USE_SSL=true'),
          rt.readLegacyPort({json.dumps(str(tmp_path / 'missing.json'))}),
        ]
    ''')
    assert result == [5000, True, None, True, None]


# --- port choice --------------------------------------------------------------

def choose(tmp_path, states, **kwargs):
    """choosePort with a fake probe: `states` maps port -> free|vdock|busy (default free)."""
    args = json.dumps(kwargs)
    return run_node(tmp_path, f'''
        const states = {json.dumps({str(k): v for k, v in states.items()})}
        const probe = async (port) => states[String(port)] || 'free'
        return await rt.choosePort({{ ...{args}, probe }})
    ''')


@needs_node
def test_saved_port_wins_when_free(tmp_path):
    assert choose(tmp_path, {}, savedPort=5123, legacyPort=5000) == {
        'port': 5123, 'persist': False, 'reason': 'saved'}


@needs_node
def test_saved_port_taken_by_another_app_moves_for_good(tmp_path):
    result = choose(tmp_path, {5123: 'busy', 5124: 'busy'}, savedPort=5123)
    assert result['port'] == 5125 and result['persist'] is True


@needs_node
def test_saved_port_served_by_another_vdock_is_left_to_the_user(tmp_path):
    result = choose(tmp_path, {5123: 'vdock'}, savedPort=5123)
    assert result['port'] == 5124 and result['persist'] is False


@needs_node
def test_macos_upgrade_leaves_airplay_port_5000(tmp_path):
    # Older packaged builds served on 5000 (config.json); on a Mac that is
    # AirPlay Receiver, which answers on loopback.
    result = choose(tmp_path, {5000: 'busy'}, legacyPort=5000)
    assert result == {'port': 5001, 'persist': True, 'reason': 'first-run'}


@needs_node
def test_windows_upgrade_keeps_port_5000_for_phone_bookmarks(tmp_path):
    result = choose(tmp_path, {}, legacyPort=5000)
    assert result == {'port': 5000, 'persist': True, 'reason': 'legacy'}


@needs_node
def test_fresh_install_takes_first_free_port_from_5001(tmp_path):
    result = choose(tmp_path, {5001: 'vdock', 5002: 'busy'})
    assert result == {'port': 5003, 'persist': True, 'reason': 'first-run'}


@needs_node
def test_port_that_failed_to_bind_is_avoided(tmp_path):
    # LAN on, another app on 0.0.0.0:5123 - invisible to the loopback probe.
    result = choose(tmp_path, {}, savedPort=5123, avoid=[5123])
    assert result['port'] == 5124 and result['persist'] is True


def _free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class _Health(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - http.server API
        body = json.dumps({'status': 'ok', 'uptime_s': 1.0}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class _Foreign(_Health):
    def do_GET(self):  # noqa: N802 - like AirPlay Receiver: 403 to everything
        self.send_response(403)
        self.send_header('Content-Length', '0')
        self.end_headers()


@needs_node
def test_probe_tells_free_vdock_and_foreign_listeners_apart(tmp_path):
    vdock = HTTPServer(('127.0.0.1', 0), _Health)
    foreign = HTTPServer(('127.0.0.1', 0), _Foreign)
    raw = socket.socket()
    raw.bind(('127.0.0.1', 0))
    raw.listen(1)
    threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in (vdock, foreign)]
    for thread in threads:
        thread.start()
    try:
        free_port = _free_port()
        result = run_node(tmp_path, f'''
            return [
              await rt.probePort({vdock.server_port}),
              await rt.probePort({foreign.server_port}),
              await rt.probePort({raw.getsockname()[1]}),
              await rt.probePort({free_port}),
              await rt.probePort(80000),
            ]
        ''')
    finally:
        vdock.shutdown()
        foreign.shutdown()
        vdock.server_close()
        foreign.server_close()
        raw.close()
    assert result == ['vdock', 'busy', 'busy', 'free', 'busy']


# --- respawn policy -------------------------------------------------------------

@needs_node
def test_quick_deaths_back_off_then_give_up(tmp_path):
    result = run_node(tmp_path, '''
        const policy = new rt.RespawnPolicy()
        const quick = [policy.onExit({ uptimeMs: 800 }), policy.onExit({ uptimeMs: 900 }),
                       policy.onExit({ uptimeMs: 700 })]
        policy.reset()
        const afterReset = policy.onExit({ uptimeMs: 500 })
        // A backend that ran for minutes and exits (Settings > restart) comes
        // straight back and clears the failure count.
        const restart = policy.onExit({ uptimeMs: 10 * 60 * 1000 })
        const nextQuick = policy.onExit({ uptimeMs: 100 })
        return { quick, afterReset, restart, nextQuick }
    ''')
    assert [step['giveUp'] for step in result['quick']] == [False, False, True]
    assert [step['delayMs'] for step in result['quick'][:2]] == [2000, 4000]
    assert result['afterReset'] == {'giveUp': False, 'delayMs': 2000, 'quickFailures': 1}
    assert result['restart'] == {'giveUp': False, 'delayMs': 500, 'quickFailures': 0}
    assert result['nextQuick']['quickFailures'] == 1


@needs_node
def test_address_in_use_is_recognised_on_every_os(tmp_path):
    result = run_node(tmp_path, '''
        return [
          'OSError: [Errno 48] Address already in use',
          'OSError: [Errno 98] Address already in use',
          'OSError: [WinError 10048] Only one usage of each socket address is normally permitted',
          'Traceback: ModuleNotFoundError: No module named flask',
        ].map(rt.isAddressInUse)
    ''')
    assert result == [True, True, True, False]


# --- login-shell PATH -------------------------------------------------------------

@needs_node
def test_marked_path_ignores_shell_noise(tmp_path):
    result = run_node(tmp_path, '''
        return [
          rt.extractMarkedPath('Welcome!\\n__VDOCK_PATH__/opt/homebrew/bin:/usr/bin__VDOCK_PATH__\\nbye'),
          rt.extractMarkedPath('no markers here'),
          rt.extractMarkedPath('__VDOCK_PATH____VDOCK_PATH__'),
          rt.mergePathLists(['/a:/b', '/b:/c', ['/a', '/d']], ':'),
        ]
    ''')
    assert result == ['/opt/homebrew/bin:/usr/bin', None, None, '/a:/b:/c:/d']


@needs_node
@pytest.mark.skipif(sys.platform == 'win32', reason='login-shell PATH is macOS/Linux only')
def test_login_shell_path_is_read_and_a_hanging_shell_times_out(tmp_path):
    talkative = tmp_path / 'fake-zsh'
    talkative.write_text(
        '#!/bin/sh\n'
        'echo "motd: welcome"\n'
        # The real call is `$SHELL -ilc '<printf ...>'`: run the command.
        'PATH=/opt/fake/bin:/usr/bin; export PATH\n'
        'eval "$2"\n',
        encoding='utf-8',
    )
    hanging = tmp_path / 'hanging-shell'
    hanging.write_text('#!/bin/sh\nsleep 30\n', encoding='utf-8')
    for script in (talkative, hanging):
        script.chmod(0o755)
    result = run_node(tmp_path, f'''
        const started = Date.now()
        const hung = await rt.resolveLoginShellPath({{ shell: {json.dumps(str(hanging))}, timeoutMs: 500 }})
        return {{
          path: await rt.resolveLoginShellPath({{ shell: {json.dumps(str(talkative))} }}),
          missing: await rt.resolveLoginShellPath({{ shell: {json.dumps(str(tmp_path / 'nope'))} }}),
          hung,
          hungMs: Date.now() - started,
        }}
    ''')
    assert result['path'] == '/opt/fake/bin:/usr/bin'
    assert result['missing'] is None
    assert result['hung'] is None and result['hungMs'] < 5000


# --- wiring in main.js / package.json (static: Electron is not run in CI) -------------

def test_main_passes_the_chosen_port_and_guards_single_instance():
    main = (ELECTRON_DIR / 'main.js').read_text(encoding='utf-8')
    assert "require('./backend-runtime')" in main
    assert 'PORT: String(port)' in main
    assert 'app.requestSingleInstanceLock()' in main
    assert "app.on('second-instance'" in main
    # The infinite 5 s respawn loop is gone; the policy decides.
    assert 'startBackend()\n      }, 5000)' not in main
    assert 'policy.onExit' in main
    # Login-shell PATH only off Windows.
    assert "process.platform !== 'win32'" in main and 'userShellPath()' in main


def test_package_ships_the_runtime_and_macos_automation_strings():
    package = json.loads((ELECTRON_DIR / 'package.json').read_text(encoding='utf-8'))
    build = package['build']
    assert 'backend-runtime.js' in build['files']
    mac = build['mac']
    assert mac['extendInfo']['NSAppleEventsUsageDescription'].strip()
    assert mac['hardenedRuntime'] is True
    entitlements = (ELECTRON_DIR / mac['entitlements']).read_text(encoding='utf-8')
    for key in ('com.apple.security.automation.apple-events',
                'com.apple.security.cs.disable-library-validation',
                'com.apple.security.cs.allow-unsigned-executable-memory'):
        assert key in entitlements
    # identity "-" must stay out of package.json: electron-builder would match
    # it as a substring against real certificate names.
    assert 'identity' not in mac
