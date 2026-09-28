"""DL-071 — session picker + pinned target.

Pins are the deck-level "control THIS session" choice: the host window is
re-resolved from the pid on every press, so prefer_pid must beat every other
ranking signal, and a dead pin must fall back instead of dead-ending.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app  # noqa: E402
from integrations import agent_state, sessions  # noqa: E402
from utils import window_focus  # noqa: E402

pytestmark = pytest.mark.skipif(sys.platform != 'win32', reason='Win32 window APIs')


@pytest.fixture(autouse=True)
def clean_pins():
    sessions.reset_pins()
    yield
    sessions.reset_pins()


# ---------------------------------------------------------------------------
# Pin lifecycle (integrations/sessions)
# ---------------------------------------------------------------------------

def test_pin_requires_a_live_session(mocker):
    mocker.patch.object(sessions, 'iter_session_pids', return_value=[10, 20])

    assert sessions.pin_session('claude', 999) is False
    assert sessions.pinned_pid('claude') is None

    assert sessions.pin_session('claude', 20) is True
    assert sessions.pinned_pid('claude') == 20


def test_dead_pin_clears_itself(mocker):
    live = mocker.patch.object(sessions, 'iter_session_pids', return_value=[10])
    assert sessions.pin_session('claude', 10) is True

    live.return_value = []
    assert sessions.pinned_pid('claude') is None
    # Cleared for good — a second call must not resurrect it.
    live.return_value = [10]
    assert sessions.pinned_pid('claude') is None


def test_unpin_and_marker_isolation(mocker):
    mocker.patch.object(sessions, 'iter_session_pids', return_value=[10])
    assert sessions.pin_session('claude', 10) is True
    assert sessions.pinned_pid('devin') is None

    sessions.unpin_session('claude')
    assert sessions.pinned_pid('claude') is None


# ---------------------------------------------------------------------------
# prefer_pid ranking (utils/window_focus)
# ---------------------------------------------------------------------------

# (pid, hwnd, title, self_owned, cwd_tier, create_time)
TWO_SESSIONS = [
    (100, 9001, 'claude — projA', False, 3, 100.0),
    (200, 9002, 'claude — projB', False, 3, 200.0),
]


def _stub_candidates(mocker, rows):
    return mocker.patch.object(
        window_focus, '_session_host_candidates', return_value=list(rows))


def test_prefer_pid_beats_newest(mocker):
    _stub_candidates(mocker, TWO_SESSIONS)
    # Without a pin the newer session (pid 200) wins the tiebreak.
    assert window_focus.find_session_host_window('claude') == 9002
    # The pin overrides the tiebreak.
    assert window_focus.find_session_host_window('claude', prefer_pid=100) == 9001


def test_prefer_pid_without_window_falls_back(mocker):
    _stub_candidates(mocker, TWO_SESSIONS)
    # Pinned pid no longer owns a window -> normal ranking decides.
    assert window_focus.find_session_host_window('claude', prefer_pid=999) == 9002


def test_prefer_pid_beats_cwd_match(mocker):
    rows = [
        (100, 9001, 'claude — projA', False, 0, 100.0),
        (200, 9002, 'claude — projB', False, 3, 200.0),
    ]
    _stub_candidates(mocker, rows)
    # cwd tier 0 would normally win; the pin still prevails.
    assert window_focus.find_session_host_window('claude', prefer_pid=200) == 9002


# ---------------------------------------------------------------------------
# Delegated-terminal fallback (DL-111)
#
# "Default terminal" mode hands a session's console to Windows Terminal (or
# another registered host): the visible window lives on a disconnected
# process tree, so the ancestor walk can never reach it. The fallback pairs
# unresolved sessions with marker-titled windows owned by terminal hosts.
# ---------------------------------------------------------------------------

def _proc_factory(table):
    """psutil.Process stand-in keyed by pid.

    ``table``: pid -> {name, parents: [pid...], cwd, created}
    """
    class _Proc:
        def __init__(self, pid):
            self.pid = pid

        def name(self):
            return self._table[self.pid]['name']

        def parents(self):
            return [_Proc(p) for p in self._table[self.pid].get('parents', [])]

        def cwd(self):
            return self._table[self.pid].get('cwd')

        def create_time(self):
            return self._table[self.pid].get('created', 0.0)

    _Proc._table = table
    return _Proc


def _ppid_proc(child_pid, ppid):
    """psutil process_iter stand-in: the caller reads .info['ppid'] and
    .pid, so carry both."""
    import types
    return types.SimpleNamespace(pid=child_pid, info={'ppid': ppid})


def _delegated_topology(mocker, session_pids, proc_table, windows_by_owner,
                        child_ppid_map):
    """Wire the mocks _session_host_candidates reads.

    proc_table: pid -> {name, parents, cwd, created}
    windows_by_owner: pid -> [(hwnd, title)]
    child_ppid_map: ppid -> [child pid] (drives children_of)
    """
    import psutil

    children = [
        _ppid_proc(child, ppid)
        for ppid, kids in child_ppid_map.items()
        for child in kids
    ]
    mocker.patch.object(
        sessions, 'iter_session_pids', return_value=list(session_pids))
    mocker.patch.object(
        window_focus, '_visible_windows_by_pid',
        return_value=dict(windows_by_owner))
    mocker.patch.object(psutil, 'process_iter', return_value=children)
    mocker.patch.object(psutil, 'Process', _proc_factory(proc_table))


def test_delegated_session_pairs_marker_titled_terminal_window(mocker):
    """claude.exe under cmd under python, no windows in-tree; the WT window
    titled '✳ Claude Code' is the session's real host."""
    _delegated_topology(
        mocker,
        session_pids=[100],
        proc_table={
            100: {'name': 'claude.exe', 'parents': [50, 60],
                  'cwd': r'C:\repos\projA', 'created': 100.0},
            50: {'name': 'cmd.exe', 'parents': [60]},
            60: {'name': 'python.exe'},
            500: {'name': 'windowsterminal.exe'},
        },
        windows_by_owner={500: [(9001, '✳ Claude Code')]},
        child_ppid_map={50: [300]},   # conhost child — owns nothing
    )
    hosts = window_focus.list_session_hosts('claude')
    assert hosts == [{
        'pid': 100, 'hwnd': 9001, 'title': '✳ Claude Code',
        'self_owned': False, 'create_time': 100.0, 'cwd': r'C:\repos\projA',
        'host': 'Windows Terminal',
    }]


def test_delegated_fallback_ignores_nonterminal_windows(mocker):
    """A browser window titled 'claude tutorial' must not be claimed."""
    _delegated_topology(
        mocker,
        session_pids=[100],
        proc_table={
            100: {'name': 'claude.exe', 'parents': [50]},
            50: {'name': 'cmd.exe'},
            600: {'name': 'chrome.exe'},
        },
        windows_by_owner={600: [(9002, 'claude tutorial — Chrome')]},
        child_ppid_map={},
    )
    assert window_focus.list_session_hosts('claude') == []


def test_delegated_fallback_pairs_each_session_its_own_window(mocker):
    """Two unresolved sessions claim the two matching terminal windows —
    newest session takes the topmost."""
    _delegated_topology(
        mocker,
        session_pids=[100, 200],
        proc_table={
            100: {'name': 'claude.exe', 'parents': [50],
                  'cwd': r'C:\repos\projA', 'created': 100.0},
            200: {'name': 'claude.exe', 'parents': [70],
                  'cwd': r'C:\repos\projB', 'created': 200.0},
            50: {'name': 'cmd.exe'},
            70: {'name': 'cmd.exe'},
            500: {'name': 'windowsterminal.exe'},
        },
        windows_by_owner={
            500: [(9001, '✳ Claude Code'), (9002, '✳ Claude Code')],
        },
        child_ppid_map={},
    )
    hosts = window_focus.list_session_hosts('claude')
    # list_session_hosts returns newest first; newest session (200) pairs
    # with the topmost enumerated window.
    assert [(h['pid'], h['hwnd']) for h in hosts] == [(200, 9001), (100, 9002)]


def test_delegated_fallback_yields_to_intree_windows(mocker):
    """A session that resolves via the ancestor walk keeps its real window;
    the terminal window only serves the unresolved one."""
    _delegated_topology(
        mocker,
        session_pids=[100, 200],
        proc_table={
            # session 100's chain: conpty child of cursor.exe owns a window
            100: {'name': 'claude.exe', 'parents': [50],
                  'cwd': r'C:\repos\projA', 'created': 100.0},
            200: {'name': 'claude.exe', 'parents': [70],
                  'cwd': r'C:\repos\projB', 'created': 200.0},
            50: {'name': 'cmd.exe'},
            70: {'name': 'cmd.exe'},
            400: {'name': 'cursor.exe'},
            500: {'name': 'windowsterminal.exe'},
        },
        windows_by_owner={
            400: [(8001, 'projA — Cursor')],
            500: [(9001, '✳ Claude Code')],
        },
        # pid 400 (cursor.exe) is a child of cmd 50 — session 100's host.
        child_ppid_map={50: [400]},
    )
    hosts = window_focus.list_session_hosts('claude')
    by_pid = {h['pid']: h for h in hosts}
    assert by_pid[100]['hwnd'] == 8001      # real in-tree host
    assert by_pid[200]['hwnd'] == 9001      # delegated-terminal fallback


def test_delegated_rows_carry_friendly_host_name(mocker):
    """DL-071 follow-up 11 — the row names which app owns the session's
    window so the picker can say 'backend · Windows Terminal'."""
    _delegated_topology(
        mocker,
        session_pids=[100],
        proc_table={
            100: {'name': 'claude.exe', 'parents': [50],
                  'cwd': r'C:\repos\projA', 'created': 100.0},
            50: {'name': 'cmd.exe'},
            500: {'name': 'windowsterminal.exe'},
        },
        windows_by_owner={500: [(9001, '✳ Claude Code')]},
        child_ppid_map={},
    )
    (host,) = window_focus.list_session_hosts('claude')
    assert host['host'] == 'Windows Terminal'


def test_host_names_ide_and_self_owned_windows(mocker):
    """A Cursor-integrated terminal reports 'Cursor'; a session owning its
    own window reports its own friendly process name."""
    _delegated_topology(
        mocker,
        session_pids=[100, 200],
        proc_table={
            100: {'name': 'claude.exe', 'parents': [50],
                  'cwd': r'C:\repos\projA', 'created': 100.0},
            200: {'name': 'claude.exe', 'parents': [70],
                  'cwd': r'C:\repos\projB', 'created': 200.0},
            50: {'name': 'cmd.exe'},
            70: {'name': 'cmd.exe'},
            400: {'name': 'cursor.exe'},
        },
        windows_by_owner={
            400: [(8001, 'projA — Cursor')],   # cursor is cmd-50's child
            200: [(9002, 'Claude Code — projB')],  # self-owned
        },
        child_ppid_map={50: [400]},
    )
    hosts = {h['pid']: h for h in window_focus.list_session_hosts('claude')}
    assert hosts[100]['host'] == 'Cursor'
    assert hosts[200]['host'] == 'Claude'


def test_host_name_unknown_exe_uses_titlecased_stem(mocker):
    """An in-tree window owned by an app we don't know still names the
    owner — exe stem, title-cased."""
    _delegated_topology(
        mocker,
        session_pids=[100],
        proc_table={
            100: {'name': 'claude.exe', 'parents': [50],
                  'cwd': r'C:\repos\projA', 'created': 100.0},
            50: {'name': 'cmd.exe'},
            900: {'name': 'myterm.exe'},
        },
        # myterm.exe is a child of the session's cmd — in-tree host.
        windows_by_owner={900: [(7001, '✳ Claude Code')]},
        child_ppid_map={50: [900]},
    )
    (host,) = window_focus.list_session_hosts('claude')
    assert host['host'] == 'Myterm'


def test_list_session_hosts_one_row_per_session(mocker):
    import psutil

    rows = [
        (100, 9001, 'wt — claude A', False, 3, 100.0),
        (100, 9003, 'claudeA self-window', True, 3, 100.0),
        (200, 9002, 'wt — claude B', False, 3, 200.0),
    ]
    _stub_candidates(mocker, rows)

    class _Proc:
        def __init__(self, pid):
            self._pid = pid

        def cwd(self):
            return {100: r'C:\repos\projA', 200: r'C:\repos\projB'}[self._pid]

    mocker.patch.object(psutil, 'Process', _Proc)

    hosts = window_focus.list_session_hosts('claude')
    assert [h['pid'] for h in hosts] == [200, 100]  # newest first
    by_pid = {h['pid']: h for h in hosts}
    # pid 100 keeps its hosted window, not the self-owned duplicate.
    assert by_pid[100]['hwnd'] == 9001
    assert by_pid[100]['cwd'] == r'C:\repos\projA'


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


def test_list_sessions_rejects_unknown_source(client):
    resp = client.get('/api/agent-sessions?source=not-an-agent')
    assert resp.status_code == 400


def test_list_sessions_reports_pin_and_resolved(client, mocker):
    mocker.patch.object(sessions, 'iter_session_pids', return_value=[100, 200])
    mocker.patch.object(
        window_focus, 'list_session_hosts', return_value=[
            {'pid': 200, 'hwnd': 9002, 'title': 'wt B', 'self_owned': False,
             'create_time': 200.0, 'cwd': r'C:\repos\projB'},
            {'pid': 100, 'hwnd': 9001, 'title': 'wt A', 'self_owned': False,
             'create_time': 100.0, 'cwd': r'C:\repos\projA'},
        ])
    mocker.patch.object(
        window_focus, 'find_session_host_window', return_value=9001)

    assert sessions.pin_session('claude', 100) is True

    resp = client.get('/api/agent-sessions?source=claude')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    assert body['pinned_pid'] == 100
    assert body['resolved_pid'] == 100
    assert [s['pid'] for s in body['sessions']] == [200, 100]
    assert body['sessions'][1]['project'] == 'projA'


def test_target_route_pin_and_clear(client, mocker):
    mocker.patch.object(sessions, 'iter_session_pids', return_value=[100])

    resp = client.post('/api/agent-sessions/target',
                       json={'source': 'claude', 'pid': 100})
    assert resp.status_code == 200
    assert resp.get_json()['pinned_pid'] == 100

    resp = client.post('/api/agent-sessions/target',
                       json={'source': 'claude', 'pid': 999})
    assert resp.status_code == 404

    resp = client.post('/api/agent-sessions/target',
                       json={'source': 'claude', 'pid': None})
    assert resp.status_code == 200
    assert resp.get_json()['pinned_pid'] is None


def test_identify_flashes_the_matching_host(client, mocker):
    mocker.patch.object(
        window_focus, 'list_session_hosts', return_value=[
            {'pid': 200, 'hwnd': 9002, 'title': 'wt B', 'self_owned': False,
             'create_time': 200.0, 'cwd': r'C:\repos\projB'},
            {'pid': 100, 'hwnd': 9001, 'title': 'wt A', 'self_owned': False,
             'create_time': 100.0, 'cwd': r'C:\repos\projA'},
        ])
    flash = mocker.patch.object(window_focus, 'flash_window')

    resp = client.post('/api/agent-sessions/identify',
                       json={'source': 'claude', 'pid': 100})
    assert resp.status_code == 200
    flash.assert_called_once_with(9001)


def test_identify_rejects_dead_pid_and_bad_source(client, mocker):
    mocker.patch.object(window_focus, 'list_session_hosts', return_value=[])

    resp = client.post('/api/agent-sessions/identify',
                       json={'source': 'claude', 'pid': 999})
    assert resp.status_code == 404

    resp = client.post('/api/agent-sessions/identify',
                       json={'source': 'not-an-agent', 'pid': 100})
    assert resp.status_code == 400


def test_list_sessions_exposes_detail_and_started(client, mocker):
    mocker.patch.object(sessions, 'iter_session_pids', return_value=[100])
    mocker.patch.object(
        window_focus, 'list_session_hosts', return_value=[
            {'pid': 100, 'hwnd': 9001, 'title': 'wt A', 'self_owned': False,
             'create_time': 1234.0, 'cwd': r'C:\repos\projA'},
        ])
    mocker.patch.object(
        window_focus, 'find_session_host_window', return_value=9001)
    mocker.patch.object(
        agent_state, 'session_entries', return_value=[
            {'cwd': r'C:\repos\projA', 'state': 'working',
             'message': 'Running the test suite', 'prompt': 'fix tests',
             'project': 'projA'},
        ])

    resp = client.get('/api/agent-sessions?source=claude')
    row = resp.get_json()['sessions'][0]
    assert row['detail'] == 'Running the test suite'
    assert row['started'] == 1234.0
    assert row['state'] == 'working'


def test_list_sessions_single_host_pairs_on_cwd_mismatch(client, mocker):
    """One live window + one hook entry can't be ambiguous — the pair
    survives a stale/moved hook cwd (DL-071 follow-up 10)."""
    mocker.patch.object(sessions, 'iter_session_pids', return_value=[100])
    mocker.patch.object(
        window_focus, 'list_session_hosts', return_value=[
            {'pid': 100, 'hwnd': 9001, 'title': 'wt A', 'self_owned': False,
             'create_time': 1234.0, 'cwd': r'C:\repos\projA'},
        ])
    mocker.patch.object(
        window_focus, 'find_session_host_window', return_value=9001)
    mocker.patch.object(
        agent_state, 'session_entries', return_value=[
            {'cwd': r'C:\other\moved', 'state': 'ready',
             'message': 'Ready for your prompt', 'project': 'projA'},
        ])

    resp = client.get('/api/agent-sessions?source=claude')
    row = resp.get_json()['sessions'][0]
    assert row['state'] == 'ready'
    assert row['detail'] == 'Ready for your prompt'


def test_list_sessions_no_fallback_with_multiple_hosts(client, mocker):
    """Ambiguity stays strict: two hosts can't share one hook entry."""
    mocker.patch.object(sessions, 'iter_session_pids', return_value=[100, 200])
    mocker.patch.object(
        window_focus, 'list_session_hosts', return_value=[
            {'pid': 200, 'hwnd': 9002, 'title': 'wt B', 'self_owned': False,
             'create_time': 200.0, 'cwd': r'C:\repos\projB'},
            {'pid': 100, 'hwnd': 9001, 'title': 'wt A', 'self_owned': False,
             'create_time': 100.0, 'cwd': r'C:\repos\projA'},
        ])
    mocker.patch.object(
        window_focus, 'find_session_host_window', return_value=9001)
    mocker.patch.object(
        agent_state, 'session_entries', return_value=[
            {'cwd': r'C:\other\moved', 'state': 'ready',
             'message': 'Ready for your prompt', 'project': 'projX'},
        ])

    resp = client.get('/api/agent-sessions?source=claude')
    rows = resp.get_json()['sessions']
    assert all(r['state'] is None for r in rows)
