"""What did the agent change this turn? (DL-145 Phase 1)

Diffing against HEAD would count the user's own uncommitted edits as the
agent's and miss anything the agent committed. So at the start of each turn
(a hook event carrying a new prompt) we take a non-mutating snapshot of the
working tree - ``git stash create`` writes a commit object but touches no
files and creates no stash entry - plus the list of already-untracked files.
The turn's changes are then ``git diff <snapshot>`` plus untracked files that
were not there before. Baselines live in memory; after a backend restart the
HEAD fallback is used and labelled as such.
"""
import logging
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from utils import subprocess_runner as sr

logger = logging.getLogger('vdock')

MAX_UNTRACKED = 2000
MAX_COUNT_BYTES = 1_000_000
MAX_FILES = 200
GIT_TIMEOUT = 15


@dataclass
class Baseline:
    repo_root: str
    sha: str
    kind: str  # 'turn' | 'head'
    untracked: FrozenSet[str]
    ts: float


_lock = threading.Lock()
_baselines: Dict[Tuple[str, str], Baseline] = {}


def _git(args: List[str], cwd: str, timeout: int = GIT_TIMEOUT) -> sr.CommandResult:
    return sr.run(['git', *args], cwd=cwd, timeout=timeout)


def _repo_root(cwd: str) -> Optional[str]:
    if not cwd or not Path(cwd).is_dir():
        return None
    try:
        result = _git(['rev-parse', '--show-toplevel'], cwd)
    except sr.BinaryNotFoundError:
        return None
    return str(Path(result.stdout.strip())) if result.ok and result.stdout.strip() else None


def _untracked(repo_root: str) -> FrozenSet[str]:
    result = _git(['ls-files', '--others', '--exclude-standard', '-z'], repo_root)
    if not result.ok:
        return frozenset()
    names = [n for n in result.stdout.split('\0') if n]
    return frozenset(names[:MAX_UNTRACKED])


def _head(repo_root: str) -> Optional[str]:
    result = _git(['rev-parse', 'HEAD'], repo_root)
    return result.stdout.strip() if result.ok and result.stdout.strip() else None


def capture(source: str, session_id: str, cwd: str) -> Optional[Baseline]:
    repo_root = _repo_root(cwd)
    if repo_root is None:
        return None
    head = _head(repo_root)
    if head is None:  # no commits yet
        return None
    stash = _git(['stash', 'create'], repo_root)
    sha = stash.stdout.strip() if stash.ok and stash.stdout.strip() else head
    baseline = Baseline(repo_root=repo_root, sha=sha, kind='turn',
                        untracked=_untracked(repo_root), ts=time.time())
    with _lock:
        _baselines[(source, session_id)] = baseline
    return baseline


def capture_async(source: str, session_id: str, cwd: str) -> None:
    def work() -> None:
        try:
            capture(source, session_id, cwd)
        except Exception as error:
            logger.debug('Turn baseline failed: %s', error)

    try:
        threading.Thread(target=work, daemon=True,
                         name='turn-baseline').start()
    except Exception as error:  # pragma: no cover - defensive
        logger.debug('Could not start baseline thread: %s', error)


def get(source: str, session_id: str) -> Optional[Baseline]:
    with _lock:
        return _baselines.get((source, session_id))


def forget(source: str, session_id: str) -> None:
    with _lock:
        _baselines.pop((source, session_id), None)


def reset() -> None:
    with _lock:
        _baselines.clear()


def _count_lines(path: Path) -> int:
    try:
        if path.stat().st_size > MAX_COUNT_BYTES:
            return 0
        data = path.read_bytes()
    except OSError:
        return 0
    if b'\0' in data[:8000]:
        return 0
    return data.count(b'\n') + (1 if data and not data.endswith(b'\n') else 0)


def _resolve_baseline(source: str, session_id: str, cwd: str) -> Optional[Baseline]:
    baseline = get(source, session_id)
    if baseline is not None:
        return baseline
    repo_root = _repo_root(cwd)
    if repo_root is None:
        return None
    head = _head(repo_root)
    if head is None:
        return None
    return Baseline(repo_root=repo_root, sha=head, kind='head',
                    untracked=frozenset(), ts=time.time())


def changes(source: str, session_id: str, cwd: str) -> Dict[str, Any]:
    baseline = _resolve_baseline(source, session_id, cwd)
    if baseline is None:
        return {'success': False, 'message': 'Not a git repository'}
    root = baseline.repo_root

    numstat = _git(['diff', '--numstat', '-z', baseline.sha], root)
    status = _git(['diff', '--name-status', '-z', baseline.sha], root)
    if not numstat.ok:
        return {'success': False, 'message': 'Could not read the changes',
                'details': numstat.output}

    statuses: Dict[str, str] = {}
    parts = [p for p in status.stdout.split('\0') if p] if status.ok else []
    i = 0
    while i < len(parts):
        code = parts[i][:1]
        if code in ('R', 'C') and i + 2 < len(parts):
            statuses[parts[i + 2]] = 'M'
            i += 3
        elif i + 1 < len(parts):
            statuses[parts[i + 1]] = code if code in ('M', 'A', 'D') else 'M'
            i += 2
        else:
            break

    files: List[Dict[str, Any]] = []
    tokens = numstat.stdout.split('\0')
    j = 0
    while j < len(tokens):
        token = tokens[j]
        j += 1
        if not token:
            continue
        fields = token.split('\t', 2)
        if len(fields) < 3:
            continue
        added_s, removed_s, path = fields
        if path == '':  # rename: old and new path follow as separate tokens
            if j + 1 < len(tokens):
                path = tokens[j + 1]
                j += 2
            else:
                continue
        added = int(added_s) if added_s.isdigit() else 0
        removed = int(removed_s) if removed_s.isdigit() else 0
        files.append({'path': path.replace('\\', '/'), 'added': added,
                      'removed': removed,
                      'status': statuses.get(path, 'M')})

    for name in sorted(_untracked(root) - baseline.untracked):
        files.append({'path': name.replace('\\', '/'),
                      'added': _count_lines(Path(root) / name),
                      'removed': 0, 'status': '?'})

    files = files[:MAX_FILES]
    return {
        'success': True,
        'base': {'sha': baseline.sha, 'kind': baseline.kind},
        'repo': root,
        'files': files,
        'totals': {
            'files': len(files),
            'added': sum(f['added'] for f in files),
            'removed': sum(f['removed'] for f in files),
        },
    }


def _inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _diff_base_dir() -> Path:
    from config import Config
    return Path(Config.DATA_DIR) / 'diff-base'


def open_diff(source: str, session_id: str, cwd: str, path: str) -> Dict[str, Any]:
    baseline = _resolve_baseline(source, session_id, cwd)
    if baseline is None:
        return {'success': False, 'status_code': 400,
                'message': 'Not a git repository'}
    root = Path(baseline.repo_root)
    target = root / path
    if not path or not _inside(root, target):
        return {'success': False, 'status_code': 400,
                'message': 'That file is outside the repository'}

    rel = target.resolve().relative_to(root.resolve()).as_posix()
    editor = 'cursor' if source == 'cursor' else None
    if editor is None or sr.find_binary(editor) is None:
        editor = 'code' if sr.find_binary('code') else (
            'cursor' if sr.find_binary('cursor') else None)

    exists_now = target.is_file()
    base_copy: Optional[Path] = None
    shown = _git(['show', f'{baseline.sha}:{rel}'], baseline.repo_root)
    if shown.ok:
        base_copy = _diff_base_dir() / baseline.sha[:12] / rel
        try:
            base_copy.parent.mkdir(parents=True, exist_ok=True)
            # Re-run as bytes-safe: text capture may alter line endings, so
            # write what git printed; good enough for a read-only comparison.
            base_copy.write_text(shown.stdout, encoding='utf-8', newline='')
        except OSError as error:
            return {'success': False, 'status_code': 502,
                    'message': 'Could not prepare the diff',
                    'details': str(error)}

    if editor is None:
        if exists_now:
            try:
                os.startfile(str(target))  # type: ignore[attr-defined]
                return {'success': True, 'status_code': 200,
                        'message': 'Opened the file (no Cursor/VS Code CLI '
                                   'found for a diff view)'}
            except (AttributeError, OSError) as error:
                return {'success': False, 'status_code': 502,
                        'message': 'Could not open the file',
                        'details': str(error)}
        return {'success': False, 'status_code': 502,
                'message': 'No Cursor or VS Code CLI found'}

    if exists_now and base_copy is not None:
        argv = [editor, '--diff', str(base_copy), str(target)]
    elif exists_now:
        argv = [editor, str(target)]
    elif base_copy is not None:
        argv = [editor, str(base_copy)]
    else:
        return {'success': False, 'status_code': 404,
                'message': 'That file no longer exists'}
    try:
        sr.spawn(argv)
    except (sr.BinaryNotFoundError, OSError) as error:
        return {'success': False, 'status_code': 502,
                'message': 'Could not open the editor', 'details': str(error)}
    return {'success': True, 'status_code': 200, 'message': 'Opened diff'}
