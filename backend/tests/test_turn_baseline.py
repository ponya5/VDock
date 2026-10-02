"""DL-145: per-turn change baseline, against a real temporary git repo."""
import subprocess

import pytest

from services import turn_baseline as tb
from utils import subprocess_runner as sr


def _git(repo, *args):
    subprocess.run(['git', *args], cwd=repo, check=True,
                   capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, 'init', '-q')
    _git(tmp_path, 'config', 'user.email', 't@t')
    _git(tmp_path, 'config', 'user.name', 't')
    _git(tmp_path, 'config', 'core.autocrlf', 'false')
    (tmp_path / 'a.txt').write_text('one\ntwo\n')
    (tmp_path / 'b.txt').write_text('b\n')
    _git(tmp_path, 'add', '.')
    _git(tmp_path, 'commit', '-q', '-m', 'init')
    tb.reset()
    yield tmp_path
    tb.reset()


def _paths(result):
    return {f['path']: f for f in result['files']}


def test_clean_tree_baseline_is_head(repo):
    baseline = tb.capture('claude', 's', str(repo))
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=repo,
                          capture_output=True, text=True).stdout.strip()
    assert baseline.kind == 'turn' and baseline.sha == head


def test_preexisting_dirty_edits_are_not_reported(repo):
    (repo / 'a.txt').write_text('one\ntwo\nthree\n')       # user's own edit
    tb.capture('claude', 's', str(repo))
    (repo / 'b.txt').write_text('b\nagent\n')               # agent's edit
    result = tb.changes('claude', 's', str(repo))
    assert set(_paths(result)) == {'b.txt'}
    assert result['totals'] == {'files': 1, 'added': 1, 'removed': 0}


def test_agent_commit_is_still_reported(repo):
    tb.capture('claude', 's', str(repo))
    (repo / 'a.txt').write_text('changed\n')
    _git(repo, 'commit', '-qam', 'agent commit')
    result = tb.changes('claude', 's', str(repo))
    assert _paths(result)['a.txt']['removed'] == 2
    assert result['base']['kind'] == 'turn'


def test_new_untracked_file_reported_but_old_untracked_is_not(repo):
    (repo / 'old.txt').write_text('x\n')
    tb.capture('claude', 's', str(repo))
    (repo / 'new.txt').write_text('1\n2\n3\n')
    files = _paths(tb.changes('claude', 's', str(repo)))
    assert 'old.txt' not in files
    assert files['new.txt']['status'] == '?' and files['new.txt']['added'] == 3


def test_no_baseline_falls_back_to_head(repo):
    (repo / 'a.txt').write_text('z\n')
    result = tb.changes('claude', 'unknown', str(repo))
    assert result['base']['kind'] == 'head'
    assert 'a.txt' in _paths(result)


def test_deleted_file_status(repo):
    tb.capture('claude', 's', str(repo))
    (repo / 'b.txt').unlink()
    assert _paths(tb.changes('claude', 's', str(repo)))['b.txt']['status'] == 'D'


def test_not_a_repo(tmp_path):
    tb.reset()
    result = tb.changes('claude', 's', str(tmp_path))
    assert result == {'success': False, 'message': 'Not a git repository'}


def test_capture_async_swallows_errors(mocker):
    mocker.patch.object(tb, 'capture', side_effect=RuntimeError('boom'))
    tb.capture_async('claude', 's', 'C:/x')   # must not raise
    import time
    time.sleep(0.1)


def test_forget_drops_baseline(repo):
    tb.capture('claude', 's', str(repo))
    tb.forget('claude', 's')
    assert tb.get('claude', 's') is None


def test_open_diff_rejects_path_outside_repo(repo):
    result = tb.open_diff('claude', 's', str(repo), '../outside.txt')
    assert result['success'] is False and result['status_code'] == 400


def test_open_diff_writes_base_copy_and_spawns_diff(repo, mocker, tmp_path_factory):
    data_dir = tmp_path_factory.mktemp('data')
    mocker.patch.object(tb, '_diff_base_dir', return_value=data_dir / 'diff-base')
    real_find = sr.find_binary
    mocker.patch.object(
        sr, 'find_binary',
        side_effect=lambda n: 'code' if n == 'code'
        else None if n == 'cursor' else real_find(n))
    spawn = mocker.patch.object(sr, 'spawn')
    tb.capture('claude', 's', str(repo))
    (repo / 'a.txt').write_text('changed\n')

    result = tb.open_diff('claude', 's', str(repo), 'a.txt')

    assert result['success'] is True
    argv = spawn.call_args[0][0]
    assert argv[0] == 'code' and argv[1] == '--diff'
    assert open(argv[2]).read() == 'one\ntwo\n'
    assert argv[3].endswith('a.txt')
