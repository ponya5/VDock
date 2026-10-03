"""Which dev servers are listening, and open / restart / stop / start them (DL-145).

Powers the ``dev_servers`` button. Servers are found from listening sockets
owned by a known dev runtime (node, python, ...) and attributed to a repo by
the process's working directory. The first sighting of a repo's server is
remembered in memory (port -> command line + cwd) so one that dies shows as
*down* with a Start item instead of silently vanishing.

Every operation addresses a server by port and is resolved against a fresh
``scan``; a pid or command line never comes from the caller.
"""
import logging
import os
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import psutil

from integrations.live_pack_base import live_result
from utils import subprocess_runner as sr

logger = logging.getLogger('vdock')

MIN_PORT = 1024
MAX_SERVERS = 8
STOP_GRACE_SECONDS = 3
_RUNTIMES = frozenset({'node', 'python', 'pythonw', 'bun', 'deno', 'java',
                       'dotnet', 'ruby', 'php', 'uvicorn', 'gunicorn'})
DEV_RUNTIMES = frozenset(_RUNTIMES | {f'{n}.exe' for n in _RUNTIMES})
EMPTY_MESSAGE = 'No dev servers running'
_OPS = frozenset({'open', 'restart', 'stop', 'start'})


@dataclass(frozen=True)
class DevServer:
    port: int
    pid: Optional[int]
    name: str
    cmdline: Tuple[str, ...]
    cwd: str
    up: bool


_lock = threading.Lock()
# repo key -> port -> (cmdline, cwd, name)
_known: Dict[str, Dict[int, Tuple[Tuple[str, ...], str, str]]] = {}


def reset() -> None:
    with _lock:
        _known.clear()


def _key(path: str) -> str:
    return os.path.normcase(os.path.abspath(path))


def _inside(path: str, root: str) -> bool:
    if not path or not root:
        return False
    child, parent = _key(path), _key(root)
    return child == parent or child.startswith(parent + os.sep)


def _vdock_ports() -> frozenset:
    """The backend's own port and the panel's frontend port."""
    from config import Config
    ports = {int(Config.PORT)}
    try:
        from routes.system import _configured_frontend_port
        ports.add(_configured_frontend_port())
    except Exception as e:  # pragma: no cover - defensive
        logger.debug('Could not read the frontend port: %s', e)
    return frozenset(ports)


def _live_servers() -> List[DevServer]:
    excluded = _vdock_ports()
    own_pid = os.getpid()
    try:
        connections = psutil.net_connections('inet')
    except (psutil.Error, OSError) as e:
        logger.debug('Could not list sockets: %s', e)
        return []
    found: Dict[int, DevServer] = {}
    for conn in connections:
        if conn.status != psutil.CONN_LISTEN or not conn.laddr:
            continue
        port = conn.laddr.port
        if port < MIN_PORT or port in excluded or port in found or not conn.pid:
            continue
        if conn.pid == own_pid:
            continue
        try:
            proc = psutil.Process(conn.pid)
            name = proc.name()
            if name.lower() not in DEV_RUNTIMES:
                continue
            found[port] = DevServer(port, conn.pid, name,
                                    tuple(proc.cmdline()), proc.cwd(), True)
        except (psutil.Error, OSError):
            continue  # another user's / system process
    return list(found.values())


def scan(repo: Optional[str]) -> List[DevServer]:
    """Live listeners plus remembered-down servers, repo's own first."""
    live = _live_servers()
    repo_key = _key(repo) if repo else None
    mine = [s for s in live if repo and _inside(s.cwd, repo)]
    others = [s for s in live if s not in mine]
    down: List[DevServer] = []
    if repo_key:
        with _lock:
            known = _known.setdefault(repo_key, {})
            for server in mine:
                known[server.port] = (server.cmdline, server.cwd, server.name)
            up_ports = {s.port for s in live}
            down = [DevServer(port, None, name, cmd, cwd, False)
                    for port, (cmd, cwd, name) in sorted(known.items())
                    if port not in up_ports]
    return (sorted(mine, key=lambda s: s.port) + down + others)[:MAX_SERVERS]


def _menu(servers: List[DevServer]) -> List[Dict[str, Any]]:
    menu: List[Dict[str, Any]] = []
    for s in servers:
        if s.up:
            menu += [
                {'id': f'open:{s.port}', 'label': f'Open :{s.port}',
                 'icon': 'arrow-up-right-from-square'},
                {'id': f'restart:{s.port}', 'label': f'Restart :{s.port}',
                 'icon': 'rotate',
                 'confirm': f'Restart the {s.name} server on :{s.port}?'},
                {'id': f'stop:{s.port}', 'label': f'Stop :{s.port}',
                 'icon': 'stop', 'danger': True,
                 'confirm': f'Stop the {s.name} server on :{s.port}?'},
            ]
        else:
            menu.append({'id': f'start:{s.port}', 'label': f'Start :{s.port}',
                         'icon': 'play'})
    return menu


def status(repo: Optional[str]) -> Dict[str, Any]:
    servers = scan(repo)
    if not servers:
        return live_result(EMPTY_MESSAGE, '0', sublabel='none running', menu=[])
    running = [s for s in servers if s.up]
    down = [s for s in servers if not s.up]
    parts = [f':{s.port}' for s in running[:4]] + [f':{s.port} ↓' for s in down[:2]]
    sublabel = ' '.join(parts)
    return live_result(sublabel or EMPTY_MESSAGE, str(len(running)),
                       'warning' if down else 'normal', sublabel, _menu(servers))


def _stop(pid: int) -> None:
    """Terminate the process tree, then kill whatever survives the grace period."""
    try:
        proc = psutil.Process(pid)
        tree = proc.children(recursive=True) + [proc]
    except psutil.NoSuchProcess:
        return
    for p in tree:
        try:
            p.terminate()
        except psutil.Error:
            pass
    _, alive = psutil.wait_procs(tree, timeout=STOP_GRACE_SECONDS)
    for p in alive:
        try:
            p.kill()
        except psutil.Error:
            pass


def _start(server: DevServer) -> Dict[str, Any]:
    try:
        sr.spawn(list(server.cmdline), cwd=server.cwd or None)
    except (sr.BinaryNotFoundError, OSError, ValueError) as e:
        return {'success': False, 'message': f'Could not start :{server.port}: {e}'}
    return {'success': True, 'message': f'Starting :{server.port}'}


def run_op(repo: Optional[str], op: str) -> Dict[str, Any]:
    """open:<port> | restart:<port> | stop:<port> | start:<port>"""
    verb, _, raw_port = op.partition(':')
    if verb not in _OPS or not raw_port.isdigit():
        return {'success': False, 'message': f'Unknown dev server action: {op}'}
    port = int(raw_port)
    server = next((s for s in scan(repo) if s.port == port), None)
    if server is None:
        return {'success': False, 'message': f'Nothing is listening on :{port}'}
    if verb == 'open':
        return {'success': True, 'message': f'Opening :{port}',
                'data': {'url': f'http://localhost:{port}'}}
    if verb == 'start':
        if server.up:
            return {'success': False, 'message': f':{port} is already running'}
        return _start(server)
    if not server.up or server.pid is None:
        return {'success': False, 'message': f':{port} is not running'}
    _stop(server.pid)
    if verb == 'stop':
        return {'success': True, 'message': f'Stopped :{port}'}
    return _start(server)
