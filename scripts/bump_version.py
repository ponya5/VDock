#!/usr/bin/env python3
"""Bump the VDock version in every place it lives, optionally commit and tag.

    python scripts/bump_version.py                 # auto: decide from commits since the last tag
    python scripts/bump_version.py minor           # force a level (major | minor | patch)
    python scripts/bump_version.py 3.0.0           # or an exact version
    python scripts/bump_version.py --dry-run       # show the decision, change nothing
    python scripts/bump_version.py --tag           # also commit "chore: release X" and create tag vX

Policy (docs/RELEASING.md): the version only moves when a release is cut, and
the level follows what shipped since the previous tag:

    major  a breaking change ("type!:" subject or a BREAKING CHANGE footer)
    minor  anything user-visible: at least one "feat" commit
    patch  only fixes / perf / refactor / docs / chore since the last tag

so day-to-day commits never bump anything, and a release with new features
moves the middle number (2.6.0 -> 2.7.0) instead of piling up patch numbers.
Pushing is never done here: `git push origin main vX.Y.Z` starts the release build.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_PY = ROOT / 'backend' / 'version.py'
PACKAGE_JSONS = [ROOT / 'frontend' / 'package.json', ROOT / 'frontend' / 'electron' / 'package.json']
LOCKFILES = [ROOT / 'frontend' / 'package-lock.json', ROOT / 'frontend' / 'electron' / 'package-lock.json']

_SEMVER = re.compile(r'^(\d+)\.(\d+)\.(\d+)$')
_SUBJECT = re.compile(r'^(?P<type>[a-zA-Z]+)(?:\([^)]*\))?(?P<bang>!)?:\s')


def bump(version: str, level: str) -> str:
    m = _SEMVER.match(version)
    if not m:
        raise ValueError(f'not a plain x.y.z version: {version!r}')
    major, minor, patch = (int(g) for g in m.groups())
    if level == 'major':
        return f'{major + 1}.0.0'
    if level == 'minor':
        return f'{major}.{minor + 1}.0'
    if level == 'patch':
        return f'{major}.{minor}.{patch + 1}'
    raise ValueError(f'unknown level {level!r}')


def decide_level(commits: list[str]) -> str:
    """`commits` are full messages (subject + body). Returns major | minor | patch."""
    level = 'patch'
    for message in commits:
        subject = message.splitlines()[0] if message.strip() else ''
        m = _SUBJECT.match(subject)
        if m and m.group('bang') or re.search(r'^BREAKING[ -]CHANGE:', message, re.M):
            return 'major'
        if m and m.group('type').lower() == 'feat':
            level = 'minor'
    return level


def current_version() -> str:
    m = re.search(r"__version__\s*=\s*'([^']+)'", VERSION_PY.read_text(encoding='utf-8'))
    if not m:
        raise SystemExit('could not read backend/version.py')
    return m.group(1)


def _git(*args: str) -> str:
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def last_tag() -> str | None:
    try:
        return _git('describe', '--tags', '--abbrev=0', '--match', 'v[0-9]*').strip() or None
    except subprocess.CalledProcessError:
        return None


def commits_since(tag: str | None) -> list[str]:
    rng = f'{tag}..HEAD' if tag else 'HEAD'
    raw = _git('log', rng, '--format=%B%x00')
    return [c.strip() for c in raw.split('\x00') if c.strip()]


def write_version(new: str) -> list[Path]:
    changed = []
    text = VERSION_PY.read_text(encoding='utf-8')
    VERSION_PY.write_text(re.sub(r"(__version__\s*=\s*')[^']+(')", rf'\g<1>{new}\g<2>', text, count=1), encoding='utf-8')
    changed.append(VERSION_PY)
    for path in PACKAGE_JSONS:
        text = path.read_text(encoding='utf-8')
        path.write_text(re.sub(r'("version"\s*:\s*")[^"]+(")', rf'\g<1>{new}\g<2>', text, count=1), encoding='utf-8')
        changed.append(path)
    for path in LOCKFILES:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding='utf-8'))
        data['version'] = new
        if isinstance(data.get('packages', {}).get(''), dict):
            data['packages']['']['version'] = new
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        changed.append(path)
    return changed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('target', nargs='?', default='auto', help='auto (default) | major | minor | patch | x.y.z')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--tag', action='store_true', help='commit the bump and create the vX.Y.Z tag (no push)')
    args = ap.parse_args(argv)

    cur = current_version()
    reason = ''
    if _SEMVER.match(args.target):
        new = args.target
        reason = 'exact version requested'
    else:
        if args.target == 'auto':
            tag = last_tag()
            commits = commits_since(tag)
            if not commits:
                print(f'Nothing to release: no commits since {tag}.', file=sys.stderr)
                return 1
            level = decide_level(commits)
            reason = f'{len(commits)} commit(s) since {tag or "the beginning"} -> {level}'
        elif args.target in ('major', 'minor', 'patch'):
            level, reason = args.target, f'{args.target} requested'
        else:
            ap.error('target must be auto, major, minor, patch or x.y.z')
        new = bump(cur, level)

    print(f'{cur} -> {new}  ({reason})')
    if args.dry_run:
        return 0
    if args.tag and _git('status', '--porcelain', '--untracked-files=no').strip():
        print('Working tree has uncommitted changes; commit them first so the tag points at the release.', file=sys.stderr)
        return 1
    files = write_version(new)
    if args.tag:
        _git('add', *[str(p.relative_to(ROOT)) for p in files])
        _git('commit', '-m', f'chore: release {new}')
        _git('tag', '-a', f'v{new}', '-m', f'VDock {new}')
        print(f'Committed and tagged v{new}. Publish with: git push origin HEAD v{new}')
    else:
        print('Updated version files. Commit them, then tag v' + new + '.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
