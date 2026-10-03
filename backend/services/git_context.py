"""Git state of the focused repo, and the few safe things to do about it (DL-145).

Powers the ``git_context`` button: one ``git status --porcelain=v2 --branch``
read paints branch / dirty / ahead-behind on the face; the press menu offers
pull (fast-forward only), push, stash, pop and "open pull request". No
network on polls (ahead/behind reflect the last fetch), and nothing here can
force-push, reset, clean or rewrite history.
"""
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from integrations.live_pack_base import live_result
from services import secrets
from utils import subprocess_runner as sr

logger = logging.getLogger('vdock')

READ_TIMEOUT = 15
NETWORK_TIMEOUT = 90
NOT_A_REPO = 'Not a git repository - focus a project in your editor'
_OPS = frozenset({'pull', 'push', 'stash', 'pop', 'pr'})


def parse_status_v2(text: str) -> Dict[str, Any]:
    """Summarise ``git status --porcelain=v2 --branch`` output."""
    info: Dict[str, Any] = {
        'branch': '', 'upstream': '', 'ahead': 0, 'behind': 0,
        'dirty': 0, 'conflicts': 0, 'detached': False,
    }
    oid = ''
    for line in text.splitlines():
        if line.startswith('# branch.oid '):
            oid = line[13:].strip()
        elif line.startswith('# branch.head '):
            head = line[14:].strip()
            info['detached'] = head == '(detached)'
            info['branch'] = head
        elif line.startswith('# branch.upstream '):
            info['upstream'] = line[18:].strip()
        elif line.startswith('# branch.ab '):
            parts = line[12:].split()
            try:
                info['ahead'] = int(parts[0].lstrip('+'))
                info['behind'] = abs(int(parts[1]))
            except (IndexError, ValueError):
                pass
        elif line[:2] in ('1 ', '2 ', '? '):
            info['dirty'] += 1
        elif line.startswith('u '):
            info['dirty'] += 1
            info['conflicts'] += 1
    if info['detached']:
        info['branch'] = f'detached @{oid[:7]}' if oid else 'detached'
    return info


def _git(repo: str, *args: str, timeout: int = READ_TIMEOUT) -> sr.CommandResult:
    return sr.run(['git', *args], cwd=repo, timeout=timeout)


def _root(repo: str) -> Optional[str]:
    """The repository containing ``repo``; None when it is not one."""
    try:
        result = _git(repo, 'rev-parse', '--show-toplevel')
    except sr.BinaryNotFoundError:
        return None
    return result.stdout.strip() or None if result.ok else None


def _in_progress(root: str) -> bool:
    """A merge or rebase is under way."""
    result = _git(root, 'rev-parse', '--git-path', 'MERGE_HEAD',
                  '--git-path', 'rebase-merge', '--git-path', 'rebase-apply')
    if not result.ok:
        return False
    return any((Path(root) / line).exists()
               for line in result.stdout.split() if line)


def _has_stash(root: str) -> bool:
    return _git(root, 'rev-parse', '-q', '--verify', 'refs/stash').ok


def _target(info: Dict[str, Any]) -> str:
    return info['upstream'] or 'origin'


def _menu(info: Dict[str, Any], has_stash: bool,
          has_gh: bool) -> List[Dict[str, Any]]:
    menu: List[Dict[str, Any]] = [
        {'id': 'pull', 'label': 'Pull', 'icon': 'arrow-down'},
        {'id': 'push', 'label': 'Push', 'icon': 'arrow-up',
         'confirm': f"Push {info['branch']} to {_target(info)}?"},
    ]
    if info['dirty']:
        menu.append({'id': 'stash', 'label': 'Stash changes', 'icon': 'box-archive',
                     'confirm': f"Stash {info['dirty']} changed "
                                f"file{'s' if info['dirty'] != 1 else ''}?"})
    if has_stash:
        menu.append({'id': 'pop', 'label': 'Pop stash', 'icon': 'box-open'})
    if has_gh:
        menu.append({'id': 'pr', 'label': 'Open pull request',
                     'icon': 'code-pull-request'})
    return menu


def _face(info: Dict[str, Any], in_progress: bool) -> Dict[str, str]:
    arrows = ''.join((f" ↑{info['ahead']}" if info['ahead'] else '',
                      f" ↓{info['behind']}" if info['behind'] else ''))
    if info['conflicts'] or in_progress:
        tone = 'critical'
    elif info['behind'] or (info['dirty'] and info['ahead']):
        tone = 'warning'
    else:
        tone = 'normal'
    suffix = ' · merge/rebase' if in_progress else ''
    return {'badge': str(info['dirty']) if info['dirty'] else '✓',
            'status': tone, 'sublabel': f"{info['branch']}{arrows}{suffix}"}


def status(repo: str) -> Dict[str, Any]:
    """The button face and press menu for ``repo``."""
    root = _root(repo)
    if not root:
        return live_result(NOT_A_REPO, '–', sublabel='No repository', menu=[])
    result = _git(root, 'status', '--porcelain=v2', '--branch')
    if not result.ok:
        return live_result(secrets.redact(result.summary()) or 'git status failed',
                           '–', sublabel='git error', menu=[])
    info = parse_status_v2(result.stdout)
    in_progress = _in_progress(root)
    face = _face(info, in_progress)
    menu = _menu(info, _has_stash(root), bool(sr.find_binary('gh')))
    out = live_result(face['sublabel'], face['badge'], face['status'],
                      face['sublabel'], menu)
    out['data'].update(branch=info['branch'], dirty=info['dirty'],
                       ahead=info['ahead'], behind=info['behind'])
    return out


def _outcome(result: sr.CommandResult, done: str) -> Dict[str, Any]:
    if result.ok:
        return {'success': True, 'message': done}
    return {'success': False,
            'message': secrets.redact(result.summary()) or 'git command failed'}


def _push(root: str, info: Dict[str, Any]) -> Dict[str, Any]:
    argv = ['push'] if info['upstream'] else ['push', '-u', 'origin', 'HEAD']
    return _outcome(_git(root, *argv, timeout=NETWORK_TIMEOUT),
                    f"Pushed {info['branch']}")


def _pull_request(root: str) -> Dict[str, Any]:
    if not sr.find_binary('gh'):
        return {'success': False, 'message': 'GitHub CLI (gh) is not installed'}
    view = sr.run(['gh', 'pr', 'view', '--json', 'url', '-q', '.url'],
                  cwd=root, timeout=NETWORK_TIMEOUT)
    url = view.stdout.strip()
    if view.ok and url:
        return {'success': True, 'message': 'Opening pull request',
                'data': {'url': url}}
    created = sr.run(['gh', 'pr', 'create', '--web'], cwd=root,
                     timeout=NETWORK_TIMEOUT)
    return _outcome(created, 'Opening a new pull request in your browser')


def run_op(repo: str, op: str) -> Dict[str, Any]:
    """pull | push | stash | pop | pr. Anything else is refused."""
    if op not in _OPS:
        return {'success': False, 'message': f'Unknown git action: {op}'}
    root = _root(repo)
    if not root:
        return {'success': False, 'message': NOT_A_REPO}
    if op == 'pull':
        return _outcome(_git(root, 'pull', '--ff-only', timeout=NETWORK_TIMEOUT),
                        'Pulled')
    if op == 'stash':
        label = f"VDock {time.strftime('%Y-%m-%d %H:%M')}"
        return _outcome(_git(root, 'stash', 'push', '-u', '-m', label),
                        'Stashed your changes')
    if op == 'pop':
        return _outcome(_git(root, 'stash', 'pop'), 'Popped the stash')
    if op == 'pr':
        return _pull_request(root)
    status_out = _git(root, 'status', '--porcelain=v2', '--branch')
    return _push(root, parse_status_v2(status_out.stdout))
