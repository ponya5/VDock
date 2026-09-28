"""Per-app executable path overrides (DL-084).

Users store ``app_paths`` in config.json — ``{ appKey: absolutePath }`` —
when the launchable app isn't resolvable by name (Cursor's default
install at ``%LOCALAPPDATA%\\Programs\\cursor\\Cursor.exe`` is the case
that motivated this). Consumers:

- ``subprocess_runner.find_binary`` consults the map before PATH, so
  CLI spawns and agent session starts honor it;
- ``cross_platform open_app`` launches a configured path directly;
- ``editor_base`` launches the app and retries focus once when a keymap
  action finds no target window.

Keys normalize to lowercase stems — ``Cursor.exe``, ``cursor`` and
``CURSOR`` are the same override. A small alias table maps ids that name
the same binary differently (template id ``claude-code`` → binary
``claude``).
"""
import logging
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger('vdock')

# Ids that resolve to a differently-named binary/app.
_ALIASES = {
    'claude-code': 'claude',
    'claude_code': 'claude',
    'vscode': 'code',
    'github-copilot': 'code',
    'visualstudio': 'devenv',
}

_SYSTEM = platform.system()


def _norm(key: str) -> str:
    """Normalize an app key: lowercase, basename, strip the .exe suffix."""
    k = (key or '').strip().lower()
    k = k.replace('\\', '/').rsplit('/', 1)[-1]
    if k.endswith('.exe') or k.endswith('.app'):
        k = k.rsplit('.', 1)[0]
    return k


# Reverse direction too — the UI saves under a friendly id ('vscode',
# 'claude-code') while callers look up the binary name ('code', 'claude').
_REVERSE_ALIASES: Dict[str, list] = {}
for _a, _b in _ALIASES.items():
    _REVERSE_ALIASES.setdefault(_b, []).append(_a)


def _keys_for(name: str) -> Tuple[str, ...]:
    """Every key a caller might mean: the name, its stem, and aliases
    in both directions."""
    n = _norm(name)
    keys = [n]
    alias = _ALIASES.get(n)
    if alias:
        keys.append(alias)
    keys += _REVERSE_ALIASES.get(n, [])
    return tuple(dict.fromkeys(k for k in keys if k))


def resolve_executable(path: str) -> str:
    """A .app bundle override resolves to its inner executable — callers
    spawning argv get a real binary instead of a directory."""
    p = Path(path)
    if p.is_dir() and p.suffix.lower() == '.app':
        macos = p / 'Contents' / 'MacOS'
        if macos.is_dir():
            for child in sorted(macos.iterdir()):
                if child.is_file() and os.access(child, os.X_OK):
                    return str(child)
    return str(p)


def override_for(*names: str) -> Optional[str]:
    """First configured path for any of ``names`` (normalized), else None.

    A stale override (file deleted since it was saved) is ignored so the
    normal resolution still runs — the user re-points it rather than
    hitting a worse error.
    """
    from config import Config  # late import: config loads before services

    paths = getattr(Config, 'APP_PATHS', None) or {}
    if not paths:
        return None
    lowered = {_norm(k): v for k, v in paths.items() if isinstance(v, str)}
    for name in names:
        for key in _keys_for(name):
            path = lowered.get(key)
            if path and Path(path).exists():
                return path
    return None


def launch_app(path: str) -> bool:
    """Launch a configured app path. True when a launch was attempted."""
    p = Path(path)
    if not p.exists():
        return False
    try:
        if _SYSTEM == 'Windows':
            os.startfile(str(p))  # noqa: S606 — user-configured path
        elif _SYSTEM == 'Darwin':
            # `open` handles both .app bundles and bare executables.
            subprocess.Popen(['open', str(p)])
        else:
            subprocess.Popen(
                [str(p)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        logger.info('Launched configured app path: %s', p)
        return True
    except OSError as e:
        logger.warning('Could not launch %s: %s', p, e)
        return False


def probe(app: str) -> Optional[str]:
    """Best-effort locate for an app — PATH first, then known install dirs.

    Powers the editor's Detect button so most users never type a path.
    """
    keys = _keys_for(app)
    # Candidate executable/bundle names per key.
    names = []
    for k in keys:
        names.append(k)
        if _SYSTEM == 'Windows':
            names.append(f'{k}.exe')
    path_hit = None
    path_hit_is_shim = False
    for name in names:
        hit = shutil.which(name)
        if hit:
            path_hit = hit
            # A PATH entry that is a .cmd/.bat shim launches through a
            # console — the real .exe in the install dir is a better target
            # for focusing and relaunching, so keep looking.
            path_hit_is_shim = hit.lower().endswith(('.cmd', '.bat'))
            if not path_hit_is_shim:
                return hit
            break

    home = Path.home()
    if _SYSTEM == 'Windows':
        local = Path(os.environ.get('LOCALAPPDATA', ''))
        progfiles = [
            Path(os.environ.get('ProgramFiles', r'C:\Program Files')),
            Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')),
        ]
        # Install dirs whose name doesn't match the exe (VS Code's user
        # install lives at "Microsoft VS Code\Code.exe").
        vendor_dirs = {'code': ['Microsoft VS Code']}
        candidates = []
        for k in keys:
            pretty = k.capitalize()
            candidates += [
                local / 'Programs' / k / f'{pretty}.exe',
                local / 'Programs' / k / f'{k}.exe',
                local / 'Programs' / f'{k}-user' / f'{pretty}.exe',
                local / 'Programs' / f'{k}-user' / f'{k}.exe',
            ]
            for vd in vendor_dirs.get(k, []):
                candidates.append(local / 'Programs' / vd / f'{pretty}.exe')
                for pf in progfiles:
                    candidates.append(pf / vd / f'{pretty}.exe')
            for pf in progfiles:
                candidates += [
                    pf / pretty / f'{pretty}.exe',
                    pf / k / f'{k}.exe',
                ]
    elif _SYSTEM == 'Darwin':
        candidates = []
        for k in keys:
            pretty = k.replace('-', ' ').title().replace(' ', '')
            candidates += [
                Path('/Applications') / f'{pretty}.app',
                home / 'Applications' / f'{pretty}.app',
                Path('/usr/local/bin') / k,
            ]
    else:
        candidates = []
        for k in keys:
            candidates += [
                Path('/usr/bin') / k,
                Path('/usr/local/bin') / k,
                home / '.local' / 'bin' / k,
            ]
    for c in candidates:
        try:
            if c.exists():
                return str(c)
        except OSError:
            continue
    return path_hit


def validate_path(path: str) -> Tuple[bool, str]:
    """(ok, error) for a user-supplied override. Exists — may be a .app dir."""
    p = Path(path.strip().strip('"').strip("'")).expanduser()
    if not p.exists():
        return False, f'Not found on this machine: {p}'
    return True, str(p)
