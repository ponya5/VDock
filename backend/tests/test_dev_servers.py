"""DL-145 Phase 3: dev server scanner."""
import os
from collections import namedtuple
from types import SimpleNamespace

import psutil
import pytest

from services import dev_servers
from utils import subprocess_runner as sr

REPO = os.path.abspath('proj')
Conn = namedtuple('Conn', 'status laddr pid')


def conn(port, pid, status=psutil.CONN_LISTEN):
    return Conn(status, SimpleNamespace(port=port), pid)


class Procs:
    """Fake process table + sockets patched into psutil."""

    def __init__(self, mocker):
        self.sockets = []
        self.table = {}
        mocker.patch.object(psutil, 'net_connections', side_effect=lambda _k: self.sockets)
        mocker.patch.object(psutil, 'Process', side_effect=self.process)
        mocker.patch.object(dev_servers, '_vdock_ports',
                            return_value=frozenset({5000, 4444}))

    def add(self, port, pid, name='node.exe', cwd=REPO, cmdline=None,
            status=psutil.CONN_LISTEN, denied=False):
        self.sockets.append(conn(port, pid, status))
        self.table[pid] = (name, cwd, cmdline or (name, 'dev'), denied)

    def process(self, pid):
        name, cwd, cmdline, denied = self.table[pid]

        def boom():
            raise psutil.AccessDenied(pid)
        return SimpleNamespace(pid=pid, name=lambda: name,
                               cwd=boom if denied else (lambda: cwd),
                               cmdline=lambda: list(cmdline))


@pytest.fixture
def procs(mocker):
    dev_servers.reset()
    yield Procs(mocker)
    dev_servers.reset()


def ports(servers):
    return [s.port for s in servers]


def test_filters_non_listen_low_ports_other_runtimes_and_vdock_ports(procs):
    procs.add(5173, 10)
    procs.add(5174, 11, status='ESTABLISHED')
    procs.add(80, 12)
    procs.add(8080, 13, name='chrome.exe')
    procs.add(5000, 14, name='python.exe')
    procs.add(4444, 15)
    assert ports(dev_servers.scan(REPO)) == [5173]


def test_repo_servers_first_then_others(procs):
    procs.add(9000, 10, cwd=os.path.abspath('elsewhere'))
    procs.add(5173, 11)
    assert ports(dev_servers.scan(REPO)) == [5173, 9000]


def test_access_denied_is_skipped(procs):
    procs.add(5173, 10, denied=True)
    procs.add(5174, 11)
    assert ports(dev_servers.scan(REPO)) == [5174]


def test_cap_at_eight(procs):
    for i in range(12):
        procs.add(6000 + i, 100 + i)
    assert len(dev_servers.scan(REPO)) == dev_servers.MAX_SERVERS


def test_duplicate_ipv4_ipv6_listeners_counted_once(procs):
    procs.add(5173, 10)
    procs.sockets.append(conn(5173, 10))
    assert ports(dev_servers.scan(REPO)) == [5173]


def test_vanished_server_reported_down(procs):
    procs.add(5173, 10)
    dev_servers.scan(REPO)
    procs.sockets.clear()
    (server,) = dev_servers.scan(REPO)
    assert (server.port, server.up) == (5173, False)
    out = dev_servers.status(REPO)
    assert out['data']['status'] == 'warning'
    assert out['data']['badge'] == '0'
    assert [i['id'] for i in out['data']['menu']] == ['start:5173']


def test_empty_state(procs):
    out = dev_servers.status(REPO)
    assert out['message'] == 'No dev servers running'
    assert out['data']['badge'] == '0' and out['data']['menu'] == []


def test_status_face_and_confirmed_menu(procs):
    procs.add(5173, 10)
    procs.add(8000, 11, name='python.exe')
    out = dev_servers.status(REPO)
    assert out['data']['badge'] == '2'
    assert out['data']['sublabel'] == ':5173 :8000'
    items = {i['id']: i for i in out['data']['menu']}
    assert 'confirm' in items['restart:5173'] and 'confirm' in items['stop:5173']
    assert 'confirm' not in items['open:5173']


def test_open_returns_url(procs):
    procs.add(5173, 10)
    out = dev_servers.run_op(REPO, 'open:5173')
    assert out['data']['url'] == 'http://localhost:5173'


def test_stop_terminates_pid_tree(procs, mocker):
    procs.add(5173, 10)
    stop = mocker.patch.object(dev_servers, '_stop')
    assert dev_servers.run_op(REPO, 'stop:5173')['success'] is True
    stop.assert_called_once_with(10)


def test_restart_stops_then_spawns_remembered_command(procs, mocker):
    procs.add(5173, 10, cmdline=('node.exe', 'vite.js'))
    order = []
    mocker.patch.object(dev_servers, '_stop', side_effect=lambda pid: order.append('stop'))
    mocker.patch.object(sr, 'spawn', side_effect=lambda argv, cwd=None: order.append((argv, cwd)))
    assert dev_servers.run_op(REPO, 'restart:5173')['success'] is True
    assert order == ['stop', (['node.exe', 'vite.js'], REPO)]


def test_start_spawns_a_down_server_only(procs, mocker):
    procs.add(5173, 10, cmdline=('node.exe', 'vite.js'))
    dev_servers.scan(REPO)
    spawn = mocker.patch.object(sr, 'spawn')
    assert dev_servers.run_op(REPO, 'start:5173')['success'] is False
    spawn.assert_not_called()
    procs.sockets.clear()
    assert dev_servers.run_op(REPO, 'start:5173')['success'] is True
    spawn.assert_called_once_with(['node.exe', 'vite.js'], cwd=REPO)


def test_unknown_port_or_op_refused(procs, mocker):
    stop = mocker.patch.object(dev_servers, '_stop')
    assert dev_servers.run_op(REPO, 'stop:9999')['success'] is False
    assert dev_servers.run_op(REPO, 'stop:abc')['success'] is False
    assert dev_servers.run_op(REPO, 'kill:5173')['success'] is False
    stop.assert_not_called()


def test_stop_kills_survivors_after_grace(mocker):
    child, parent = mocker.Mock(), mocker.Mock()
    parent.children.return_value = [child]
    mocker.patch.object(psutil, 'Process', return_value=parent)
    mocker.patch.object(psutil, 'wait_procs', return_value=([], [parent]))
    dev_servers._stop(10)
    child.terminate.assert_called_once()
    parent.terminate.assert_called_once()
    parent.kill.assert_called_once()
    child.kill.assert_not_called()
