#!/usr/bin/env python3
"""macOS smoke test: drives a running VDock backend through its HTTP API.

Usage:  python3 scripts/macos-smoke-test.py [http://127.0.0.1:5001]

Point it at a throwaway backend (own DATA_DIR and port) rather than your real
one, e.g.:

    DATA_DIR=/tmp/vdock-e2e PORT=5099 backend/venv/bin/python backend/app.py
    python3 scripts/macos-smoke-test.py http://127.0.0.1:5099

It changes volume, mic level and the clipboard, restores them at the end, and
deliberately skips shut down / restart / sleep / lock screen.
"""
import sys

import json
import subprocess
import time
import urllib.request

BASE = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'http://127.0.0.1:5001'
results = []


def call(method, path, body=None, timeout=40):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read() or b'null')
    except urllib.error.HTTPError as error:
        raw = error.read()
        try:
            return error.code, json.loads(raw)
        except ValueError:
            return error.code, raw.decode(errors='replace')[:200]
    except Exception as error:
        return 0, str(error)


def record(name, ok, detail=''):
    results.append((name, ok, detail))
    print(('PASS ' if ok else 'FAIL ') + name + ('  -> ' + str(detail)[:150] if detail else ''))


def action(name, action_type, config, expect_ok=True):
    status, body = call('POST', '/api/actions/execute',
                        {'action': {'type': action_type, 'config': config}, 'wait': True})
    success = isinstance(body, dict) and body.get('success') is True
    message = body.get('message') if isinstance(body, dict) else body
    record(name, success == expect_ok, f'{status} {message}')
    return body


def shell(command):
    return subprocess.run(command, shell=True, capture_output=True, text=True).stdout.strip()


original_clipboard = subprocess.run(['pbpaste'], capture_output=True).stdout
original_volume = shell('osascript -e "output volume of (get volume settings)"')
original_input = shell('osascript -e "input volume of (get volume settings)"')

print('== core API ==')
status, body = call('GET', '/api/health')
record('health', status == 200 and body.get('status') == 'ok', body)
status, body = call('GET', '/api/config')
record('config GET', status == 200, f"allow_lan={body.get('allow_lan') if isinstance(body, dict) else body}")
status, body = call('GET', '/api/actions/catalog')
record('action catalog', status == 200 and len(body['actions']) > 200, len(body['actions']))
status, body = call('GET', '/api/profiles')
record('profiles list', status == 200, type(body).__name__)
status, body = call('GET', '/api/user-settings')
record('user-settings GET', status in (200, 404), status)
for metric in ['cpu', 'memory', 'disk', 'network', 'temperature']:
    status, body = call('GET', f'/api/metrics/{metric}')
    record(f'metric /api/metrics/{metric}', status == 200 and 'error' not in str(body)[:30], str(body)[:90])
status, body = call('GET', '/api/now-playing')
record('now-playing', status == 200, str(body)[:100])
status, body = call('GET', '/api/system/ports')
record('ports read', status == 200, body)
status, body = call('GET', '/api/logs')
record('logs', status == 200, status)
status, body = call('GET', '/api/triggers')
record('triggers list', status == 200, status)

print('== profile CRUD ==')
status, body = call('POST', '/api/profiles', {'name': 'sweep-test'})
profile_id = body.get('id') if isinstance(body, dict) else None
if isinstance(body, dict) and not profile_id:
    profile_id = (body.get('profile') or {}).get('id')
record('profile create', status in (200, 201) and bool(profile_id), f'{status} {profile_id}')
if profile_id:
    status, body = call('GET', f'/api/profiles/{profile_id}')
    record('profile read', status == 200, status)
    status, body = call('DELETE', f'/api/profiles/{profile_id}')
    record('profile delete', status in (200, 204), status)

print('== settings round trip (LAN stays off) ==')
status, body = call('PUT', '/api/config', {'allow_lan': False})
record('config PUT allow_lan=false', status == 200, status)

print('== volume / media / mic (the reported bugs) ==')
action('volume_up (step 2000 preset)', 'cross_platform', {'action': 'volume_up', 'step': 2000})
action('volume_down (step 2000 preset)', 'cross_platform', {'action': 'volume_down', 'step': 2000})
action('volume_up default', 'cross_platform', {'action': 'volume_up'})
action('volume_down default', 'cross_platform', {'action': 'volume_down'})
action('volume_mute', 'cross_platform', {'action': 'volume_mute'})
action('volume_unmute', 'cross_platform', {'action': 'volume_unmute'})
action('volume_set 40', 'cross_platform', {'action': 'volume_set', 'value': 40})
action('volume_get', 'cross_platform', {'action': 'volume_get'})
action('media_play_pause', 'cross_platform', {'action': 'media_play_pause'})
time.sleep(1.2)
action('media_play_pause (restore)', 'cross_platform', {'action': 'media_play_pause'})
action('media_stop', 'cross_platform', {'action': 'media_stop'})
action('microphone_mute', 'cross_platform', {'action': 'microphone_mute'})
action('microphone_unmute', 'cross_platform', {'action': 'microphone_unmute'})

print('== system / apps ==')
screenshot_body = call('POST', '/api/actions/execute', {
    'action': {'type': 'cross_platform', 'config': {'action': 'screenshot', 'path': '/tmp/vdock-smoke-shot.png'}},
    'wait': True})[1]
screenshot_message = str(screenshot_body.get('message'))
record('screenshot (saved, or says how to grant Screen Recording)',
       screenshot_body.get('success') is True or 'Screen' in screenshot_message, screenshot_message)
action('command: disabled by default (security)', 'command', {'command': 'echo vdock-ok'}, expect_ok=False)
action('http_request to self', 'http_request', {'url': BASE + '/api/health', 'method': 'GET'})
action('open_app Calculator', 'cross_platform', {'action': 'open_app', 'path': 'Calculator'})
time.sleep(2)
action('close_app Calculator', 'cross_platform', {'action': 'close_app', 'app_name': 'Calculator'})
action('open_folder /tmp', 'cross_platform', {'action': 'open_folder', 'path': '/tmp'})
action('metric cpu usage tile', 'metric_cpu_usage', {})
action('metric memory tile', 'metric_memory', {})
action('brightness_up (needs CLI)', 'cross_platform', {'action': 'brightness_up'}, expect_ok=False)

print('== clipboard (restored afterwards) ==')
action('clipboard_set', 'macro', {'steps': [{'type': 'clipboard_set', 'text': 'vdock-clip-test'}]})
clip = subprocess.run(['pbpaste'], capture_output=True).stdout.decode()
record('clipboard value written', clip == 'vdock-clip-test', repr(clip))

print('== keyboard injection (Accessibility) ==')
body = action('hotkey without Accessibility -> clear message', 'hotkey', {'keys': ['shift']}, expect_ok=False)
record('hotkey message tells user what to do', 'Accessibility' in str(body.get('message')), body.get('message'))

subprocess.run(['pbcopy'], input=original_clipboard)
shell(f'osascript -e "set volume output volume {original_volume}"')
shell(f'osascript -e "set volume input volume {original_input}"')
print()
failed = [name for name, ok, _ in results if not ok]
print(f'{len(results) - len(failed)}/{len(results)} passed')
for name in failed:
    print('  FAILED:', name)
