#!/usr/bin/env python3
"""VDock agent hook — called by Claude Code on Notification/Stop events.

Claude Code pipes a JSON payload to this script's stdin
(`hook_event_name`, `message`, `cwd`, ...). We map it to a VDock
agent-event and POST it to the local backend so the dashboard and
screensaver can pop an "agent needs you" alert.

  Notification -> 'waiting' (permission prompt / idle awaiting input)
  Stop         -> 'clear'   (response finished — dismiss the alert)

Usage: python vdock_agent_hook.py [--port 5000] [--source claude]

Stdlib only, silent by design: a hook must never block or break the
agent session, so every failure exits 0.
"""
import argparse
import json
import sys
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--source', default='claude')
    args = parser.parse_args()

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    event_name = payload.get('hook_event_name', '')
    if event_name == 'Stop':
        event = 'clear'
    elif event_name == 'Notification':
        event = 'waiting'
    else:
        return 0  # Unrelated hook event — nothing to report.

    body = {
        'source': args.source,
        'event': event,
        'message': payload.get('message') or 'Claude Code is waiting for input',
        'cwd': payload.get('cwd') or '',
        'project': payload.get('cwd', '').replace('\\', '/').rsplit('/', 1)[-1],
    }

    url = f'http://127.0.0.1:{args.port}/api/agent-events'
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        urllib.request.urlopen(req, timeout=3)
    except OSError:
        pass  # VDock not running — fine.

    return 0


if __name__ == '__main__':
    sys.exit(main())
