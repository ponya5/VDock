"""Docker / Compose state of the focused repo, with a few safe controls (DL-145).

Powers the ``docker_status`` button. A repo with a compose file reports its
compose stack; otherwise the running containers are listed. Only
``up -d``, ``stop``, ``restart <service>`` and ``logs`` can be issued -- never
``down``, ``rm``, ``prune`` or volume removal -- and a service / container
name is only ever taken from the CLI's own ``ps`` output, never from the
caller, so the argv cannot be steered.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from integrations.live_pack_base import live_result
from services import secrets
from utils import subprocess_runner as sr

logger = logging.getLogger('vdock')

COMPOSE_FILES = ('compose.yaml', 'compose.yml',
                 'docker-compose.yaml', 'docker-compose.yml')
INFO_TIMEOUT = 8
READ_TIMEOUT = 20
UP_TIMEOUT = 120
OP_TIMEOUT = 60
LOG_LINES = '80'
MAX_MENU_ITEMS = 6
NOT_RUNNING = "Docker isn't running - start Docker Desktop"
NOT_INSTALLED = 'Docker CLI not found - install Docker Desktop'


def parse_ps_json(text: str) -> List[Dict[str, Any]]:
    """Container rows from ``ps --format json``: a JSON array or one object per line."""
    text = text.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        rows = data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        rows = []
        for line in text.splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return [r for r in rows if isinstance(r, dict)]


def _compose_file(repo: str) -> bool:
    return any((Path(repo) / name).is_file() for name in COMPOSE_FILES)


def _docker(argv: List[str], cwd: str, timeout: int) -> sr.CommandResult:
    return sr.run(['docker', *argv], cwd=cwd, timeout=timeout)


def _daemon_up(repo: str) -> bool:
    return _docker(['info', '--format', '{{.ServerVersion}}'], repo,
                   INFO_TIMEOUT).ok


def _containers(repo: str, compose: bool) -> Optional[List[Dict[str, str]]]:
    """Normalised rows ({name, service, running}) or None when the read failed."""
    argv = (['compose', 'ps', '--all', '--format', 'json'] if compose
            else ['ps', '--format', 'json'])
    result = _docker(argv, repo, READ_TIMEOUT)
    if not result.ok:
        return None
    rows = []
    for row in parse_ps_json(result.stdout):
        name = str(row.get('Name') or row.get('Names') or '')
        service = str(row.get('Service') or '')
        if name or service:
            rows.append({'name': name, 'service': service,
                         'running': str(row.get('State', '')).lower() == 'running'})
    return rows


def _target(row: Dict[str, str], compose: bool) -> str:
    return (row['service'] or row['name']) if compose else row['name']


def _menu(rows: List[Dict[str, str]], compose: bool) -> List[Dict[str, Any]]:
    menu: List[Dict[str, Any]] = []
    running = any(r['running'] for r in rows)
    if compose:
        menu.append({'id': 'up', 'label': 'Start stack', 'icon': 'play'})
        if running:
            menu.append({'id': 'stop', 'label': 'Stop stack', 'icon': 'stop',
                         'danger': True, 'confirm': 'Stop all containers in this stack?'})
    for row in rows[:MAX_MENU_ITEMS]:
        target = _target(row, compose)
        if compose:
            menu.append({'id': f'restart:{target}', 'label': f'Restart {target}',
                         'icon': 'rotate'})
        menu.append({'id': f'logs:{target}', 'label': f'Logs · {target}',
                     'icon': 'file-lines'})
    return menu


def status(repo: Optional[str]) -> Dict[str, Any]:
    if not repo:
        return live_result(NOT_RUNNING, '–', sublabel='No project', menu=[])
    try:
        if not _daemon_up(repo):
            return live_result(NOT_RUNNING, '–', sublabel='Docker not running',
                               menu=[])
        compose = _compose_file(repo)
        rows = _containers(repo, compose)
    except sr.BinaryNotFoundError:
        return live_result(NOT_INSTALLED, '–', sublabel='Docker not installed',
                           menu=[])
    if rows is None:
        return live_result('Could not read Docker state', '–',
                           sublabel='Docker error', menu=[])
    running = sum(1 for r in rows if r['running'])
    if not rows and not compose:
        return live_result('No containers running', '0', sublabel='none running',
                           menu=[])
    tone = 'warning' if 0 < running < len(rows) else 'normal'
    sublabel = 'compose' if compose else 'containers'
    return live_result(f'{running}/{len(rows)} running', f'{running}/{len(rows)}',
                       tone, sublabel, _menu(rows, compose))


def _tail(result: sr.CommandResult) -> str:
    text = '\n'.join(part for part in (result.stdout, result.stderr) if part.strip())
    return secrets.redact(text.strip())


def _outcome(result: sr.CommandResult, done: str) -> Dict[str, Any]:
    if result.ok:
        return {'success': True, 'message': done}
    return {'success': False,
            'message': secrets.redact(result.summary()) or 'docker command failed'}


def run_op(repo: Optional[str], op: str) -> Dict[str, Any]:
    """up | stop | restart:<service> | logs:<service-or-container>"""
    if not repo:
        return {'success': False, 'message': 'No project to run Docker in'}
    verb, _, name = op.partition(':')
    try:
        compose = _compose_file(repo)
        if verb in ('up', 'stop') and not name:
            if not compose:
                return {'success': False,
                        'message': 'No compose file in this project'}
            if verb == 'up':
                return _outcome(_docker(['compose', 'up', '-d'], repo, UP_TIMEOUT),
                                'Stack started')
            return _outcome(_docker(['compose', 'stop'], repo, OP_TIMEOUT),
                            'Stack stopped')
        if verb not in ('restart', 'logs') or not name or (
                verb == 'restart' and not compose):
            return {'success': False, 'message': f'Unknown Docker action: {op}'}
        rows = _containers(repo, compose)
        if rows is None or name not in {_target(r, compose) for r in rows}:
            return {'success': False, 'message': f'Unknown service: {name}'}
        if verb == 'restart':
            return _outcome(_docker(['compose', 'restart', name], repo, OP_TIMEOUT),
                            f'Restarted {name}')
        argv = (['compose', 'logs', '--tail', LOG_LINES, '--no-color', name]
                if compose else ['logs', '--tail', LOG_LINES, name])
        result = _docker(argv, repo, OP_TIMEOUT)
        if not result.ok:
            return _outcome(result, '')
        return {'success': True, 'message': f'Logs for {name}',
                'data': {'panel_text': _tail(result) or 'No log output'}}
    except sr.BinaryNotFoundError:
        return {'success': False, 'message': NOT_INSTALLED}
