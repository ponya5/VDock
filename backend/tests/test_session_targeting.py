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
