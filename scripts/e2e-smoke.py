#!/usr/bin/env python3
"""VDock end-to-end smoke test: checks what a user would observe, not code paths.

Starts a throwaway backend - its own port, DATA_DIR, .env and HOME - so it can
turn on phone access, set a deck password and feed agent hooks without touching
your real deck, your backend/.env or your installed agent hooks. Then it checks:

  * phone over Wi-Fi: the deck page, the live connection and the reachability
    probe answer on the LAN address (a foreign web origin is refused);
  * deck password: another device is locked out, this computer is not, a
    sign-in renews, and changing the password signs devices out;
  * agent hooks: the real hook script, fed Claude Code / Cursor / Codex /
    Antigravity events, drives the deck state working -> permission -> ready;
  * this machine: the OS permissions keystroke buttons need, now-playing, and
    which catalog actions are unavailable here and why.

Runs on Windows, macOS and Linux with the backend venv; stdlib only.
    python scripts/e2e-smoke.py          # exit code 1 if anything failed
    python scripts/e2e-smoke.py --keep   # leave the throwaway files for a look
See AGENTS.md "Definition of done". Phone-viewport UI checks are separate
(Playwright), this script stays dependency-free.
"""
import argparse
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / 'backend'
HOOK_SCRIPT = BACKEND / 'scripts' / 'vdock_agent_hook.py'
IS_WINDOWS = os.name == 'nt'

results: List[Tuple[str, bool, str]] = []


def venv_python() -> Path:
    candidate = BACKEND / 'venv' / ('Scripts/python.exe' if IS_WINDOWS else 'bin/python')
    return candidate if candidate.exists() else Path(sys.executable)


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


def http(method: str, url: str, body: Any = None, headers: Optional[Dict[str, str]] = None,
         timeout: float = 8.0) -> Tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers=dict(headers or {}))
    if data is not None:
        request.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as error:
        raw, status = error.read(), error.code
    try:
        return status, json.loads(raw)
    except ValueError:
        return status, raw.decode('utf-8', 'replace')


def check(name: str, fn: Callable[[], str]) -> None:
    """Run one check; ``fn`` returns the observed evidence or raises."""
    try:
        evidence = fn()
        results.append((name, True, evidence))
        print(f'  PASS  {name}  ({evidence})')
    except Exception as error:  # noqa: BLE001 - every failure is a finding
        results.append((name, False, str(error)))
        print(f'  FAIL  {name}  ({error})')


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class ThrowawayBackend:
    def __init__(self, workdir: Path):
        self.workdir = workdir
        self.port = free_port()
        self.base = f'http://127.0.0.1:{self.port}'
        self.process: Optional[subprocess.Popen] = None
        self.lan_ip: Optional[str] = None

    def start(self) -> None:
        home = self.workdir / 'home'
        home.mkdir(parents=True, exist_ok=True)
        env_file = self.workdir / '.env'
        env_file.write_text(f'SECRET_KEY={secrets.token_hex(32)}\nREQUIRE_AUTH=False\nAUTH_PASSWORD=\n',
                            encoding='utf-8')
        env = {
            **os.environ,
            'DATA_DIR': str(self.workdir / 'data'),
            'PORT': str(self.port),
            'ALLOW_LAN': 'True',
            'VDOCK_ENV_FILE': str(env_file),
            # Startup "repairs" installed agent hooks to point at this port;
            # a private HOME keeps the real ~/.claude, ~/.cursor... untouched.
            'HOME': str(home), 'USERPROFILE': str(home),
            'PYTHONUNBUFFERED': '1',
        }
        env.pop('VDOCK_ELECTRON', None)
        log = open(self.workdir / 'backend.log', 'w', encoding='utf-8')
        self.process = subprocess.Popen([str(venv_python()), 'app.py'], cwd=str(BACKEND),
                                        env=env, stdout=log, stderr=subprocess.STDOUT)
        deadline = time.time() + 60
        while time.time() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError(f'backend exited, see {self.workdir / "backend.log"}')
            try:
                if http('GET', f'{self.base}/api/health', timeout=2)[0] == 200:
                    status, body = http('GET', f'{self.base}/api/config')
                    self.lan_ip = (body.get('config') or {}).get('lan_ip') if status == 200 else None
                    return
            except OSError:
                pass
            time.sleep(0.5)
        raise RuntimeError('backend did not answer within 60 s')

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()

    @property
    def lan(self) -> str:
        expect(bool(self.lan_ip), 'no LAN address detected on this machine')
        return f'http://{self.lan_ip}:{self.port}'


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def phone_checks(deck: ThrowawayBackend) -> None:
    def page() -> str:
        status, body = http('GET', f'{deck.lan}/')
        expect(status == 200, f'GET {deck.lan}/ -> {status}')
        expect('id="app"' in str(body), 'response is not the VDock page (frontend/dist built?)')
        return f'{deck.lan}/ -> 200'

    def live_connection() -> str:
        url = f'{deck.lan}/socket.io/?EIO=4&transport=polling'
        ok = http('GET', url, headers={'Origin': deck.lan})[0]
        foreign = http('GET', url, headers={'Origin': 'http://evil.example'})[0]
        expect(ok == 200, f'phone origin handshake -> {ok}')
        expect(foreign != 200, 'a foreign web origin was allowed to connect')
        return f'phone origin 200, foreign origin {foreign}'

    def probe() -> str:
        status, body = http('GET', f'{deck.base}/api/system/lan-probe')
        expect(status == 200 and body.get('reachable') is True, f'lan-probe -> {status} {body}')
        return f"{body.get('host')} reachable"

    check('phone: deck page loads over Wi-Fi', page)
    check('phone: live connection accepted, foreign origin refused', live_connection)
    check('phone: Connect card reachability probe', probe)


def password_checks(deck: ThrowawayBackend) -> None:
    state: Dict[str, str] = {}

    def enable() -> str:
        status, body = http('PUT', f'{deck.base}/api/config',
                            {'require_auth': True, 'auth_password': 'smoke-pass-1'})
        expect(status == 200 and body.get('success'), f'enable password -> {status} {body}')
        return 'password set'

    def phone_locked_out() -> str:
        status = http('GET', f'{deck.lan}/api/config')[0]
        expect(status == 401, f'phone without sign-in -> {status}, expected 401')
        return 'phone without sign-in -> 401'

    def this_computer_trusted() -> str:
        status = http('GET', f'{deck.base}/api/config')[0]
        expect(status == 200, f'this computer -> {status}, expected 200 (DL-008)')
        return 'localhost -> 200, no password'

    def sign_in_and_renew() -> str:
        status, body = http('POST', f'{deck.lan}/api/auth/login', {'password': 'smoke-pass-1'})
        expect(status == 200 and body.get('token'), f'login -> {status}')
        token = body['token']
        expect(http('GET', f'{deck.lan}/api/config',
                    headers={'Authorization': f'Bearer {token}'})[0] == 200, 'signed-in phone refused')
        status, body = http('POST', f'{deck.lan}/api/auth/refresh',
                            headers={'Authorization': f'Bearer {token}'})
        expect(status == 200 and body.get('token'), f'refresh -> {status}')
        state['token'] = body['token']
        return 'login, use and renewal work from the phone address'

    def password_change_signs_out() -> str:
        status, _ = http('PUT', f'{deck.base}/api/config', {'auth_password': 'smoke-pass-2'})
        expect(status == 200, f'change password -> {status}')
        status = http('GET', f'{deck.lan}/api/config',
                      headers={'Authorization': f"Bearer {state.get('token', '')}"})[0]
        expect(status == 401, f'old sign-in after password change -> {status}, expected 401')
        return 'old sign-in rejected after the change'

    def disable() -> str:
        status, _ = http('PUT', f'{deck.base}/api/config', {'require_auth': False})
        expect(status == 200, f'disable -> {status}')
        return 'password off again'

    check('password: turn on', enable)
    check('password: another device is locked out', phone_locked_out)
    check('password: this computer stays signed in', this_computer_trusted)
    check('password: phone signs in and renews', sign_in_and_renew)
    check('password: changing it signs devices out', password_change_signs_out)
    check('password: turn off', disable)


def run_hook(deck: ThrowawayBackend, source: str, payload: Dict[str, Any],
             event: Optional[str] = None) -> None:
    command = [str(venv_python()), str(HOOK_SCRIPT), '--port', str(deck.port), '--source', source]
    if event:
        command += ['--event', event]
    stdin = json.dumps(payload)
    if source == 'codex':
        # Codex passes its notification as the last argv element.
        command.append(stdin)
        stdin = ''
    completed = subprocess.run(command, input=stdin, capture_output=True, text=True, timeout=20)
    expect(completed.returncode == 0, f'hook exited {completed.returncode}: {completed.stderr.strip()[:200]}')


def agent_state(deck: ThrowawayBackend, source: str) -> Optional[str]:
    status, body = http('GET', f'{deck.base}/api/agent-events/states')
    expect(status == 200, f'states -> {status}')
    return ((body.get('states') or {}).get(source) or {}).get('state')


def hook_checks(deck: ThrowawayBackend) -> None:
    cwd = str(ROOT)
    flows = {
        'claude': [
            ({'hook_event_name': 'UserPromptSubmit', 'prompt': 'smoke', 'cwd': cwd, 'session_id': 's1'}, None, 'working'),
            ({'hook_event_name': 'Notification', 'notification_type': 'permission_prompt',
              'message': 'Claude needs your permission to use Bash', 'cwd': cwd, 'session_id': 's1'}, None, 'permission'),
            ({'hook_event_name': 'Stop', 'cwd': cwd, 'session_id': 's1'}, None, 'ready'),
        ],
        'cursor': [
            ({'hook_event_name': 'beforeSubmitPrompt', 'prompt': 'smoke', 'workspace_roots': [cwd],
              'conversation_id': 'c1'}, None, 'working'),
            ({'hook_event_name': 'stop', 'workspace_roots': [cwd], 'conversation_id': 'c1'}, None, 'ready'),
        ],
        'antigravity': [
            ({'cwd': cwd}, 'PreInvocation', 'working'),
            ({'cwd': cwd}, 'Stop', 'ready'),
        ],
        'codex': [
            ({'type': 'agent-turn-complete', 'cwd': cwd, 'last-assistant-message': 'done'}, None, 'ready'),
        ],
    }
    for source, steps in flows.items():
        def flow(source=source, steps=steps) -> str:
            seen = []
            for payload, event, wanted in steps:
                run_hook(deck, source, payload, event)
                deadline = time.time() + 5
                state = None
                while time.time() < deadline:
                    state = agent_state(deck, source)
                    if state == wanted:
                        break
                    time.sleep(0.2)
                expect(state == wanted, f'after {event or payload.get("hook_event_name") or payload.get("type")}: '
                                        f'deck shows {state!r}, expected {wanted!r}')
                seen.append(state)
            return ' -> '.join(seen)
        check(f'agent hooks: {source} drives the deck state', flow)


def machine_checks(deck: ThrowawayBackend) -> None:
    def permissions() -> str:
        status, body = http('GET', f'{deck.base}/api/system/permissions')
        expect(status == 200, f'permissions -> {status}')
        if body.get('os') != 'macos':
            return f"{body.get('os')}: no keystroke permission to grant"
        app = (body.get('accessibility_app') or {}).get('name')
        expect(body.get('accessibility') is True,
               f'macOS Accessibility is OFF for "{app}" (this run) - keystroke buttons will fail. '
               'Launched from the real app, check Settings > Agent alerts')
        return f'Accessibility on for "{app}"'

    def now_playing() -> str:
        status, body = http('GET', f'{deck.base}/api/now-playing')
        expect(status == 200 and body.get('available') is True, f'now-playing -> {status} {body}')
        track = body.get('track') or {}
        return f"available; {track.get('title') or 'nothing playing'}"

    def catalog() -> str:
        status, body = http('GET', f'{deck.base}/api/actions/catalog')
        expect(status == 200, f'catalog -> {status}')
        actions = body.get('actions') if isinstance(body, dict) else body
        unavailable = [a for a in actions or [] if isinstance(a, dict) and a.get('unavailable_reason')]
        for action in unavailable:
            print(f"        unavailable here: {action.get('id')} - {action['unavailable_reason']}")
        return f'{len(actions or [])} actions, {len(unavailable)} unavailable here (listed above)'

    check('machine: keystroke permission', permissions)
    check('machine: now playing readable', now_playing)
    check('machine: action catalog', catalog)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--keep', action='store_true', help='keep the throwaway files')
    args = parser.parse_args()

    workdir = Path(tempfile.mkdtemp(prefix='vdock-smoke-'))
    deck = ThrowawayBackend(workdir)
    print(f'VDock e2e smoke - throwaway backend on port {deck.port} ({workdir})')
    try:
        check('backend starts with phone access on', lambda: (deck.start(), f'up, LAN {deck.lan_ip}')[1])
        if deck.process and deck.process.poll() is None:
            phone_checks(deck)
            password_checks(deck)
            hook_checks(deck)
            machine_checks(deck)
    finally:
        deck.stop()
        if not args.keep:
            shutil.rmtree(workdir, ignore_errors=True)

    failed = [name for name, ok, _ in results if not ok]
    print(f'\n{len(results) - len(failed)} passed, {len(failed)} failed')
    for name in failed:
        print(f'  FAIL  {name}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
