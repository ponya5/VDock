"""Repo hygiene contract (DL-146 Phase 1).

Answers "is X tracked?" with one command and stops junk creeping back:
scratch output, logs, env dumps, personal absolute paths, new large binaries
and stray env templates.
"""
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _tracked_files():
    if not (REPO_ROOT / '.git').exists():
        pytest.skip('not a git checkout')
    try:
        out = subprocess.run(
            ['git', 'ls-files', '-z'], cwd=REPO_ROOT, capture_output=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip('git unavailable')
    return [p for p in out.decode('utf-8', 'replace').split('\0') if p]


# design-log/ is the maintainer's private decision log (DL-148).
FORBIDDEN_PREFIXES = (
    '.devin-shots/', 'backend/test-scripts/', '.benchmarks/', 'design-log/',
)
FORBIDDEN_EXACT = {'.env', 'backend/.env', 'frontend/.env'}


def test_no_forbidden_tracked_paths():
    bad = []
    for path in _tracked_files():
        base = path.rsplit('/', 1)[-1]
        if (path.startswith(FORBIDDEN_PREFIXES) or path.endswith('.log')
                or path in FORBIDDEN_EXACT or base.lower() == 'nul'):
            bad.append(path)
    assert not bad, f'tracked files that must be ignored: {bad[:10]}'


SCANNED_ROOTS = ('backend/', 'frontend/src/', 'frontend/electron/', 'scripts/')
SKIP_DIRS = ('backend/venv/', 'frontend/electron/node_modules/')
BINARY_EXT = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.icns', '.mp4', '.mp3',
    '.wav', '.ogg', '.woff', '.woff2', '.ttf', '.otf', '.pdf', '.zip', '.bin',
    '.pyc', '.db', '.sqlite', '.glb', '.hdr', '.exe', '.dll',
}
ABS_USER_PATH = re.compile(r'[A-Za-z]:[\\/]+Users[\\/]+\w+|/Users/\w+/|/home/\w+/', re.I)
# Documentation-style placeholders, not a real person's path.
PLACEHOLDER_USERS = re.compile(r'(?:Users[\\/]+|/home/)(?:(?:you|user|username|name|someone|me|x|foo|example)\b|<[^>]+>|\{[^}]+\}|\$\{?\w+\}?)', re.I)


def test_no_absolute_user_paths_in_code():
    hits = []
    for path in _tracked_files():
        if not path.startswith(SCANNED_ROOTS) or path.startswith(SKIP_DIRS):
            continue
        if Path(path).suffix.lower() in BINARY_EXT:
            continue
        # This file spells out the pattern it hunts for.
        if path == 'backend/tests/test_repo_hygiene.py':
            continue
        full = REPO_ROOT / path
        if not full.is_file():
            continue
        try:
            text = full.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        for match in ABS_USER_PATH.finditer(text):
            snippet = text[match.start():match.end() + 12]
            if PLACEHOLDER_USERS.search(snippet):
                continue
            hits.append(f'{path}: {match.group(0)}')
            break
    assert not hits, f'absolute user paths in tracked code: {hits[:10]}'


# Tracked files > 1 MB on 2026-10-03. The test only blocks NEW large files;
# new images should stay <= 400 KB (see docs/CONTRIBUTING.md).
KNOWN_LARGE = {
    'docs/assets/screens/dashboard-live.gif',
    'docs/assets/vdock-readme.gif',
    'docs/assets/vdock-hero.mp4',
    'docs/assets/vdock-readme.mp4',
    'docs/assets/vdock2-intro.gif',
    'docs/assets/vdock2-intro.mp4',
    'docs/assets/vdock2-tour.gif',
    'docs/assets/vdock2-tour.mp4',
}
KNOWN_LARGE_PREFIXES = ('frontend/public/assets/animations/gifs/buttons/',)


def test_no_large_new_binaries():
    big = []
    for path in _tracked_files():
        full = REPO_ROOT / path
        if not full.is_file() or full.stat().st_size <= 1024 * 1024:
            continue
        if path in KNOWN_LARGE or path.startswith(KNOWN_LARGE_PREFIXES):
            continue
        big.append(path)
    assert not big, f'new tracked files over 1 MB (compress or allowlist): {big}'


ALLOWED_TEMPLATES = {'backend/.env.example', 'frontend/.env.example'}


def test_no_duplicate_env_templates():
    tracked = set(_tracked_files())
    templates = {
        p for p in tracked
        if p.rsplit('/', 1)[-1] in ('.env.example', 'env.example')
    }
    extra = templates - ALLOWED_TEMPLATES
    assert not extra, f'unexpected env templates: {extra}'
    # On disk, not "tracked": a new template is untracked until committed.
    missing = [p for p in ALLOWED_TEMPLATES if not (REPO_ROOT / p).is_file()]
    assert not missing, f'missing canonical env templates: {missing}'
