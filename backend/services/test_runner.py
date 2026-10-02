"""Detect and run a repository's tests, and remember the last result (DL-145).

Powers the ``dev_run_tests`` button: one tap runs whatever test suite(s) the
focused repo has, and the button face stays green/red from the cached result
(``status``) without re-running. The exit code is the authority on pass/fail;
the passed/failed counts are best-effort parses of the framework's summary.
"""
import hashlib
import json
import logging
import os
import re
import shlex
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from services import secrets
from utils import subprocess_runner as sr

logger = logging.getLogger('vdock')

PLAN_TIMEOUT_SECONDS = 900
TAIL_CHARS = 2000
WATCH_DEBOUNCE_SECONDS = 5
SKIP_DIRS = frozenset({'node_modules', 'venv', '.venv', '.git', 'dist',
                       'build', '__pycache__', 'target'})

_ANSI = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')


@dataclass(frozen=True)
class TestPlan:
    __test__ = False  # not a pytest class, despite the name

    name: str
    argv: Tuple[str, ...]
    cwd: str
    framework: str
    env: Mapping[str, str] = field(default_factory=dict)


@dataclass
class _RepoState:
    running: bool = False
    result: Optional[Dict[str, Any]] = None
    run_fingerprint: Optional[str] = None
    pending_fingerprint: Optional[str] = None
    pending_since: float = 0.0


_lock = threading.Lock()
_states: Dict[str, _RepoState] = {}


def _key(repo_root: str) -> str:
    return os.path.normcase(os.path.abspath(repo_root))


def _state(repo_root: str) -> _RepoState:
    return _states.setdefault(_key(repo_root), _RepoState())


def reset() -> None:
    with _lock:
        _states.clear()


# --- detection ---------------------------------------------------------------

def _python_for(directory: Path) -> str:
    for rel in ('venv/Scripts/python.exe', '.venv/Scripts/python.exe',
                'venv/bin/python', '.venv/bin/python'):
        candidate = directory / rel
        if candidate.is_file():
            return str(candidate)
    return sr.find_binary('python') or 'python'


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return ''


def _npm_plan(directory: Path, name: str) -> Optional[TestPlan]:
    package = directory / 'package.json'
    if not package.is_file():
        return None
    try:
        script = (json.loads(_read(package)).get('scripts') or {}).get('test')
    except (ValueError, AttributeError):
        return None
    if not isinstance(script, str) or not script.strip() \
            or 'no test specified' in script:
        return None
    framework = 'vitest' if 'vitest' in script else (
        'jest' if 'jest' in script else 'npm')
    return TestPlan(name, ('npm', 'test', '--silent'), str(directory),
                    framework, {'CI': '1'})


def _has_pytest(directory: Path) -> bool:
    if (directory / 'pytest.ini').is_file() \
            or (directory / 'conftest.py').is_file():
        return True
    if '[tool.pytest' in _read(directory / 'pyproject.toml'):
        return True
    if '[tool:pytest]' in _read(directory / 'setup.cfg'):
        return True
    tests = directory / 'tests'
    return tests.is_dir() and any(tests.glob('test_*.py'))


def _detect_dir(directory: Path, name: str) -> List[TestPlan]:
    plans: List[TestPlan] = []
    npm = _npm_plan(directory, name)
    if npm:
        plans.append(npm)
    if _has_pytest(directory):
        plans.append(TestPlan(name, (_python_for(directory), '-m', 'pytest',
                                     '-q'), str(directory), 'pytest'))
    if (directory / 'go.mod').is_file():
        plans.append(TestPlan(name, ('go', 'test', './...'), str(directory),
                              'go'))
    if (directory / 'Cargo.toml').is_file():
        plans.append(TestPlan(name, ('cargo', 'test'), str(directory),
                              'cargo'))
    return plans


def detect(repo_root: str) -> List[TestPlan]:
    """Test plans for the repo root, else for each immediate subdirectory."""
    root = Path(repo_root)
    plans = _detect_dir(root, root.name)
    if plans:
        return plans
    try:
        children = sorted(p for p in root.iterdir() if p.is_dir()
                          and p.name not in SKIP_DIRS
                          and not p.name.startswith('.'))
    except OSError:
        return []
    for child in children:
        plans.extend(_detect_dir(child, child.name))
    return plans


def plan_from_command(command: str, cwd: str) -> TestPlan:
    argv = tuple(part.strip('"\'') for part in shlex.split(command, posix=False))
    return TestPlan(Path(cwd).name, argv, cwd, 'custom')


# --- output parsing ----------------------------------------------------------

def _last_int(pattern: str, text: str) -> Optional[int]:
    matches = re.findall(pattern, text)
    return int(matches[-1]) if matches else None


def parse_counts(framework: str, output: str) -> Tuple[Optional[int], Optional[int]]:
    """(passed, failed) from a framework's summary line; None when unknown."""
    text = _ANSI.sub('', output or '')
    if framework in ('vitest', 'npm', 'custom'):
        m = re.search(r'Tests\s+(?:(\d+) failed \| )?(\d+) passed', text)
        if m:
            return int(m.group(2)), int(m.group(1) or 0)
    if framework in ('jest', 'npm', 'custom'):
        m = re.search(r'Tests:\s+(?:(\d+) failed, )?(\d+) passed', text)
        if m:
            return int(m.group(2)), int(m.group(1) or 0)
    if framework in ('pytest', 'custom'):
        passed = _last_int(r'(\d+) passed', text)
        failed = _last_int(r'(\d+) failed', text)
        if passed is not None or failed is not None:
            return passed or 0, failed or 0
    if framework == 'go':
        passed = len(re.findall(r'^ok\s', text, re.M))
        failed = len(re.findall(r'^FAIL\t', text, re.M))
        if passed or failed:
            return passed, failed
    if framework == 'cargo':
        m = re.findall(r'test result: \w+\. (\d+) passed; (\d+) failed', text)
        if m:
            return (sum(int(p) for p, _ in m), sum(int(f) for _, f in m))
    return None, None


# --- running -----------------------------------------------------------------

def _tail(text: str) -> str:
    return secrets.redact(_ANSI.sub('', text or '').strip()[-TAIL_CHARS:])


def _run_plan(plan: TestPlan) -> Dict[str, Any]:
    try:
        result = sr.run(list(plan.argv), cwd=plan.cwd,
                        timeout=PLAN_TIMEOUT_SECONDS, env=dict(plan.env))
    except sr.BinaryNotFoundError as error:
        return {'name': plan.name, 'ok': False, 'passed': None,
                'failed': None, 'tail': str(error)}
    output = f'{result.stdout}\n{result.stderr}'
    passed, failed = parse_counts(plan.framework, output)
    return {'name': plan.name, 'ok': result.ok, 'passed': passed,
            'failed': failed, 'tail': _tail(output)}


def _fingerprint(repo_root: str) -> Optional[str]:
    """Hash of the working tree's changed files and their mtimes."""
    try:
        result = sr.run(['git', 'status', '--porcelain=v1', '-z'],
                        cwd=repo_root, timeout=10)
    except sr.BinaryNotFoundError:
        return None
    if not result.ok:
        return None
    digest = hashlib.sha1(result.stdout.encode('utf-8', 'ignore'))
    for entry in (e for e in result.stdout.split('\0') if len(e) > 3):
        try:
            digest.update(str(os.stat(Path(repo_root) / entry[3:])
                              .st_mtime_ns).encode())
        except OSError:
            continue
    return digest.hexdigest()


def run(repo_root: str, plans: Sequence[TestPlan]) -> Dict[str, Any]:
    """Run every plan (blocking), cache and return the face data."""
    with _lock:
        state = _state(repo_root)
        already = state.running
        state.running = True
    if already:
        return {'success': False, 'message': 'Tests are already running',
                'data': _face(repo_root)}
    fingerprint = _fingerprint(repo_root)
    with _lock:
        _state(repo_root).run_fingerprint = fingerprint
    try:
        runs = [_run_plan(plan) for plan in plans]
        result = {'runs': runs, 'finished_at': time.time(),
                  'ok': all(r['ok'] for r in runs)}
    finally:
        with _lock:
            _state(repo_root).running = False
    with _lock:
        _state(repo_root).result = result
    data = _face(repo_root)
    return {'success': True, 'message': _summary(result), 'data': data}


def _failed_total(result: Dict[str, Any]) -> Optional[int]:
    counts = [r['failed'] for r in result['runs'] if not r['ok']]
    known = [c for c in counts if c]
    return sum(known) if known else None


def _summary(result: Dict[str, Any]) -> str:
    if result['ok']:
        parts = [f"{r['name']} {r['passed']}" if r['passed'] is not None
                 else r['name'] for r in result['runs']]
        return 'Tests passed: ' + ' · '.join(parts)
    failed = _failed_total(result)
    return f'{failed} failed' if failed else 'Tests failed'


def _face(repo_root: str) -> Dict[str, Any]:
    with _lock:
        state = _state(repo_root)
        running, result = state.running, state.result
    if running:
        return {'badge': '…', 'status': 'running', 'sublabel': 'running',
                'menu': []}
    if result is None:
        return {'badge': '–', 'status': 'normal', 'sublabel': 'tap to run',
                'menu': [{'id': 'run', 'label': 'Run tests'}]}

    menu: List[Dict[str, str]] = [{'id': 'run', 'label': 'Run tests'}]
    if result['ok']:
        total = sum(r['passed'] or 0 for r in result['runs'])
        known = any(r['passed'] is not None for r in result['runs'])
        return {'badge': f'✓ {total}' if known else '✓', 'status': 'success',
                'sublabel': ' · '.join(
                    f"{r['name']} {r['passed']}" if r['passed'] is not None
                    else r['name'] for r in result['runs']),
                'menu': menu}

    failed = _failed_total(result)
    first = next(r for r in result['runs'] if not r['ok'])
    menu += [{'id': 'failure', 'label': 'Show last failure'},
             {'id': 'fix', 'label': 'Send failure to agent'}]
    return {'badge': f'✕ {failed}' if failed else '✕', 'status': 'critical',
            'sublabel': f'{failed} failed' if failed else 'failed',
            'panel_text': first['tail'], 'menu': menu}


def last_failure(repo_root: str) -> str:
    """Redacted tail of the first failing plan of the last run, else ''."""
    with _lock:
        result = _state(repo_root).result
    if result is None or result['ok']:
        return ''
    return next(r['tail'] for r in result['runs'] if not r['ok'])


def _start_background(repo_root: str, plans: Sequence[TestPlan]) -> None:
    threading.Thread(target=run, args=(repo_root, plans), daemon=True,
                     name='test-watch').start()


def status(repo_root: str, watch: bool = False) -> Dict[str, Any]:
    """The cached face; with ``watch``, start a run when the tree changed."""
    if watch:
        _maybe_watch_run(repo_root)
    return _face(repo_root)


def _maybe_watch_run(repo_root: str) -> None:
    fingerprint = _fingerprint(repo_root)
    if fingerprint is None:
        return
    now = time.time()
    with _lock:
        state = _state(repo_root)
        if state.run_fingerprint is None:
            state.run_fingerprint = fingerprint  # first sight: just baseline
            return
        if fingerprint != state.pending_fingerprint:
            state.pending_fingerprint, state.pending_since = fingerprint, now
            return
        due = (fingerprint != state.run_fingerprint and not state.running
               and now - state.pending_since >= WATCH_DEBOUNCE_SECONDS)
        if due:
            state.run_fingerprint = fingerprint
    if due:
        plans = detect(repo_root)
        if plans:
            _start_background(repo_root, plans)
