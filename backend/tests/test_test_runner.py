"""DL-145: test detection, output parsing and run/status caching."""
import json

import pytest

from services import test_runner as tr
from utils import subprocess_runner as sr


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.setattr(tr, '_fingerprint', lambda repo: None)
    tr.reset()
    yield
    tr.reset()


def _result(ok=True, out='', code=None):
    return sr.CommandResult(ok=ok, exit_code=0 if ok else 1, stdout=out,
                            stderr='', argv=['x'])


def _npm(path, script='vitest run'):
    path.mkdir(exist_ok=True)
    (path / 'package.json').write_text(json.dumps({'scripts': {'test': script}}))


# --- detection ---------------------------------------------------------------

def test_npm_test_script_detected(tmp_path):
    _npm(tmp_path)
    [plan] = tr.detect(str(tmp_path))
    assert plan.argv == ('npm', 'test', '--silent')
    assert plan.framework == 'vitest' and plan.env == {'CI': '1'}


def test_npm_default_placeholder_ignored(tmp_path):
    _npm(tmp_path, 'echo "Error: no test specified" && exit 1')
    assert tr.detect(str(tmp_path)) == []


@pytest.mark.parametrize('marker, content', [
    ('pytest.ini', '[pytest]\n'),
    ('pyproject.toml', '[tool.pytest.ini_options]\n'),
    ('setup.cfg', '[tool:pytest]\n'),
])
def test_pytest_markers(tmp_path, marker, content):
    (tmp_path / marker).write_text(content)
    [plan] = tr.detect(str(tmp_path))
    assert plan.framework == 'pytest' and plan.argv[1:] == ('-m', 'pytest', '-q')


def test_pytest_via_tests_folder(tmp_path):
    (tmp_path / 'tests').mkdir()
    (tmp_path / 'tests' / 'test_x.py').write_text('def test_x(): pass\n')
    assert [p.framework for p in tr.detect(str(tmp_path))] == ['pytest']


def test_venv_python_is_preferred(tmp_path):
    (tmp_path / 'pytest.ini').write_text('[pytest]\n')
    exe = tmp_path / 'venv' / 'Scripts' / 'python.exe'
    exe.parent.mkdir(parents=True)
    exe.write_text('')
    [plan] = tr.detect(str(tmp_path))
    assert plan.argv[0] == str(exe)


def test_monorepo_subdirs_in_alphabetical_order(tmp_path):
    _npm(tmp_path / 'frontend')
    (tmp_path / 'backend').mkdir()
    (tmp_path / 'backend' / 'pytest.ini').write_text('[pytest]\n')
    _npm(tmp_path / 'node_modules')                      # skipped
    assert [(p.name, p.framework) for p in tr.detect(str(tmp_path))] == [
        ('backend', 'pytest'), ('frontend', 'vitest')]


def test_go_and_cargo(tmp_path):
    (tmp_path / 'go.mod').write_text('module x\n')
    (tmp_path / 'Cargo.toml').write_text('[package]\n')
    assert [p.argv for p in tr.detect(str(tmp_path))] == [
        ('go', 'test', './...'), ('cargo', 'test')]


def test_nothing_detected(tmp_path):
    assert tr.detect(str(tmp_path)) == []


def test_plan_from_command_strips_quotes(tmp_path):
    plan = tr.plan_from_command('npx vitest run "src/a b.test.ts"', str(tmp_path))
    assert plan.argv == ('npx', 'vitest', 'run', 'src/a b.test.ts')


# --- parsing -----------------------------------------------------------------

@pytest.mark.parametrize('framework, output, expected', [
    ('pytest', '1163 passed in 28.01s', (1163, 0)),
    ('pytest', '3 failed, 1160 passed, 2 warnings in 30s', (1160, 3)),
    ('vitest', '\x1b[2m      Tests \x1b[22m 631 passed (631)', (631, 0)),
    ('vitest', 'Tests  1 failed | 630 passed (631)', (630, 1)),
    ('jest', 'Tests:       2 failed, 10 passed, 12 total', (10, 2)),
    ('go', 'ok  \tpkg/a\t0.1s\nFAIL\tpkg/b\t0.2s\n', (1, 1)),
    ('cargo', 'test result: ok. 12 passed; 0 failed; 0 ignored', (12, 0)),
    ('pytest', 'garbage', (None, None)),
])
def test_parse_counts(framework, output, expected):
    assert tr.parse_counts(framework, output) == expected


# --- run / status ------------------------------------------------------------

def _plans(tmp_path):
    return [tr.TestPlan('backend', ('py',), str(tmp_path), 'pytest'),
            tr.TestPlan('frontend', ('npm',), str(tmp_path), 'vitest')]


def test_run_aggregates_two_plans(tmp_path, mocker):
    outputs = iter([_result(out='1163 passed in 1s'),
                    _result(out='Tests  631 passed (631)')])
    mocker.patch.object(sr, 'run', side_effect=lambda *a, **k: next(outputs))
    result = tr.run(str(tmp_path), _plans(tmp_path))
    assert result['success'] is True
    assert result['data']['badge'] == '✓ 1794'
    assert result['data']['sublabel'] == 'backend 1163 · frontend 631'
    assert result['data']['status'] == 'success'


def test_failing_exit_code_is_critical_even_when_parse_fails(tmp_path, mocker):
    mocker.patch.object(sr, 'run', return_value=_result(ok=False, out='boom'))
    data = tr.run(str(tmp_path), _plans(tmp_path)[:1])['data']
    assert data['status'] == 'critical' and data['badge'] == '✕'
    assert [m['id'] for m in data['menu']] == ['run', 'failure', 'fix']


def test_failed_counts_and_last_failure_tail(tmp_path, mocker):
    out = 'FAILED tests/test_a.py::test_x\n1 failed, 5 passed in 1s'
    mocker.patch.object(sr, 'run', return_value=_result(ok=False, out=out))
    data = tr.run(str(tmp_path), _plans(tmp_path)[:1])['data']
    assert data['badge'] == '✕ 1' and data['sublabel'] == '1 failed'
    assert 'test_x' in data['panel_text']
    assert 'test_x' in tr.last_failure(str(tmp_path))


def test_last_failure_empty_when_passing_or_never_run(tmp_path, mocker):
    assert tr.last_failure(str(tmp_path)) == ''
    mocker.patch.object(sr, 'run', return_value=_result(out='2 passed'))
    tr.run(str(tmp_path), _plans(tmp_path)[:1])
    assert tr.last_failure(str(tmp_path)) == ''


def test_failure_tail_is_redacted(tmp_path, mocker):
    from services import secrets
    secrets.register_runtime_secret('s3cr3t-token-value')
    mocker.patch.object(sr, 'run', return_value=_result(
        ok=False, out='token s3cr3t-token-value leaked'))
    tr.run(str(tmp_path), _plans(tmp_path)[:1])
    assert 's3cr3t-token-value' not in tr.last_failure(str(tmp_path))


def test_status_before_any_run(tmp_path):
    assert tr.status(str(tmp_path))['badge'] == '–'


def test_concurrent_run_reports_already_running(tmp_path, mocker):
    repo = str(tmp_path)
    inner = {}

    def slow_run(*a, **k):
        inner['second'] = tr.run(repo, _plans(tmp_path)[:1])
        return _result(out='1 passed')

    mocker.patch.object(sr, 'run', side_effect=slow_run)
    tr.run(repo, _plans(tmp_path)[:1])
    assert inner['second']['success'] is False
    assert 'already running' in inner['second']['message']


def test_watch_starts_one_run_per_change(tmp_path, mocker):
    repo = str(tmp_path)
    fingerprints = iter(['a', 'a', 'b', 'b', 'b', 'b'])
    mocker.patch.object(tr, '_fingerprint', side_effect=lambda r: next(fingerprints))
    mocker.patch.object(tr, 'detect', return_value=_plans(tmp_path)[:1])
    start = mocker.patch.object(tr, '_start_background')
    clock = {'t': 1000.0}
    mocker.patch.object(tr.time, 'time', side_effect=lambda: clock['t'])

    tr.status(repo, watch=True)             # baseline 'a'
    tr.status(repo, watch=True)             # unchanged
    tr.status(repo, watch=True)             # changed to 'b': pending
    start.assert_not_called()
    clock['t'] += tr.WATCH_DEBOUNCE_SECONDS + 1
    tr.status(repo, watch=True)             # stable for the debounce: run
    assert start.call_count == 1
    tr.status(repo, watch=True)             # no further change: no new run
    tr.status(repo, watch=True)
    assert start.call_count == 1
