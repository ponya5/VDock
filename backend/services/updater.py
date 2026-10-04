"""In-app updater (DL-150).

Checks the GitHub "latest release" of VDock, classifies how this copy was
installed, and performs a one-tap upgrade where that is safe (Windows NSIS
installer and source checkouts). Nothing runs at import time: the background
check is started explicitly via :func:`start`.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from config import project_root
from version import __version__

logger = logging.getLogger(__name__)

REPO = 'ponya5/VDock'
LATEST_URL = f'https://api.github.com/repos/{REPO}/releases/latest'
DOWNLOAD_PREFIX = f'https://github.com/{REPO}/releases/download/'
CACHE_TTL = 6 * 3600.0
FORCE_MIN_INTERVAL = 60.0
INITIAL_DELAY = 10.0
HTTP_TIMEOUT = 8.0
NOTES_MAX = 4096
EXIT_FOR_UPDATE = 75
EXIT_DELAY = 1.5

IDLE, DOWNLOADING, INSTALLING, RESTARTING, ERROR = (
    'idle', 'downloading', 'installing', 'restarting', 'error')
BUSY_STATES = (DOWNLOADING, INSTALLING, RESTARTING)

AUTO_INSTALL_KINDS = ('windows-installer', 'source')

_TAG_RE = re.compile(r'^v(\d+)\.(\d+)\.(\d+)$')
_WIN_SETUP_RE = re.compile(r'^VDock[ .-]Setup[ .-].*\.exe$', re.IGNORECASE)

_lock = threading.RLock()
_cache: Optional[Dict[str, Any]] = None   # last check result (raw release info)
_cache_at: float = 0.0                    # monotonic time of last good/failed check
_last_forced: float = 0.0
_state: Dict[str, str] = {'state': IDLE, 'message': ''}
_started = False


# --------------------------------------------------------------------------
# Version helpers
# --------------------------------------------------------------------------

def _env(name: str) -> str:
    """Process-set markers (Electron/AppImage/portable), not user config."""
    return os.environ.get(name, '')


def parse_version(tag: Optional[str]) -> Optional[Tuple[int, int, int]]:
    """``v1.2.3`` -> (1, 2, 3); anything else -> None (ignored)."""
    if not isinstance(tag, str):
        return None
    m = _TAG_RE.match(tag.strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _current_tuple() -> Tuple[int, int, int]:
    parsed = parse_version('v' + __version__.lstrip('v'))
    return parsed or (0, 0, 0)


def is_newer(tag: Optional[str], current: Optional[str] = None) -> bool:
    latest = parse_version(tag)
    if latest is None:
        return False
    cur = parse_version('v' + (current or __version__).lstrip('v')) or (0, 0, 0)
    return latest > cur


# --------------------------------------------------------------------------
# Install kind + asset choice
# --------------------------------------------------------------------------

def detect_install_kind() -> str:
    frozen = bool(getattr(sys, 'frozen', False))
    if not frozen and (project_root() / '.git').exists():
        return 'source'
    if frozen and sys.platform == 'win32':
        return 'portable' if _env('PORTABLE_EXECUTABLE_FILE') else 'windows-installer'
    if frozen and sys.platform == 'darwin':
        return 'mac'
    if frozen and sys.platform.startswith('linux'):
        return 'appimage' if _env('APPIMAGE') else 'manual'
    return 'manual'


def can_auto_install(kind: str) -> bool:
    return kind in AUTO_INSTALL_KINDS


def pick_asset(kind: str, assets: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Choose the release asset for an install kind (None -> release page)."""
    def match(pred: Callable[[str], bool]) -> Optional[Dict[str, Any]]:
        for asset in assets or []:
            name = asset.get('name') if isinstance(asset, dict) else None
            if isinstance(name, str) and pred(name):
                return asset
        return None

    if kind == 'windows-installer':
        return match(lambda n: bool(_WIN_SETUP_RE.match(n)))
    if kind == 'portable':
        return match(lambda n: n.lower() == 'vdock-portable.exe')
    if kind == 'mac':
        return match(lambda n: n.lower().endswith('.dmg'))
    if kind == 'appimage':
        return match(lambda n: n.lower().endswith('.appimage'))
    return None


# --------------------------------------------------------------------------
# Release check
# --------------------------------------------------------------------------

def _http_get_json(url: str) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={
        'User-Agent': f'VDock/{__version__}',
        'Accept': 'application/vnd.github+json',
    })
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:  # nosec B310 - fixed https URL
        return json.loads(resp.read().decode('utf-8'))


def _fetch_latest() -> Dict[str, Any]:
    """Seam for tests: returns the GitHub release JSON."""
    return _http_get_json(LATEST_URL)


def _summarize_release(release: Dict[str, Any]) -> Dict[str, Any]:
    notes = release.get('body') or ''
    if not isinstance(notes, str):
        notes = ''
    return {
        'tag': release.get('tag_name'),
        'notes': notes[:NOTES_MAX],
        'html_url': release.get('html_url') or '',
        'assets': [a for a in (release.get('assets') or []) if isinstance(a, dict)],
    }


def check(force: bool = False) -> Dict[str, Any]:
    """Run (or reuse) the release check. Never raises."""
    global _cache, _cache_at, _last_forced
    now = time.monotonic()
    with _lock:
        fresh = _cache is not None and (now - _cache_at) < CACHE_TTL
        if fresh and not force:
            return _cache  # type: ignore[return-value]
        if force and _last_forced and (now - _last_forced) < FORCE_MIN_INTERVAL and _cache is not None:
            return _cache
        if force:
            _last_forced = now
    try:
        info = _summarize_release(_fetch_latest())
        info['error'] = None
    except Exception as exc:  # network, JSON, HTTP errors: report, never raise
        logger.warning('Update check failed: %s', exc)
        info = {'tag': None, 'notes': '', 'html_url': '', 'assets': [],
                'error': _short_error(exc)}
    info['checked_at'] = int(time.time())
    with _lock:
        _cache = info
        _cache_at = time.monotonic()
    return info


def _short_error(exc: BaseException) -> str:
    text = str(exc) or exc.__class__.__name__
    return text[:160]


def get_status(force: bool = False) -> Dict[str, Any]:
    info = check(force=force)
    kind = detect_install_kind()
    tag = info.get('tag')
    available = bool(info.get('error') is None and is_newer(tag))
    release_url = info.get('html_url') or ''
    download_url = release_url
    if available:
        asset = pick_asset(kind, info.get('assets') or [])
        if asset and asset.get('browser_download_url'):
            download_url = asset['browser_download_url']
    latest = tag.lstrip('v') if isinstance(tag, str) and parse_version(tag) else None
    with _lock:
        state = dict(_state)
    return {
        'current': __version__,
        'latest': latest,
        'available': available,
        'notes': info.get('notes') or '',
        'releaseUrl': release_url,
        'downloadUrl': download_url,
        'installKind': kind,
        'canAutoInstall': can_auto_install(kind),
        'checkedAt': info.get('checked_at'),
        'error': info.get('error'),
        'state': state['state'],
        'stateMessage': state['message'],
    }


def reset_cache() -> None:
    """Test helper: forget cached check and rate-limit/state bookkeeping."""
    global _cache, _cache_at, _last_forced
    with _lock:
        _cache = None
        _cache_at = 0.0
        _last_forced = 0.0
        _state.update(state=IDLE, message='')


# --------------------------------------------------------------------------
# Background first check
# --------------------------------------------------------------------------

def _background_check(delay: float) -> None:
    time.sleep(delay)
    try:
        check()
    except Exception:  # pragma: no cover - check() never raises
        logger.exception('Background update check crashed')


def start(spawner: Optional[Callable[..., Any]] = None, delay: float = INITIAL_DELAY) -> None:
    """Kick off the first check ~10 s after boot (idempotent)."""
    global _started
    with _lock:
        if _started:
            return
        _started = True
    if spawner is not None:
        spawner(_background_check, delay)
    else:
        threading.Thread(target=_background_check, args=(delay,),
                         name='update-check', daemon=True).start()


# --------------------------------------------------------------------------
# State machine
# --------------------------------------------------------------------------

def get_state() -> Dict[str, str]:
    with _lock:
        return dict(_state)


def _set_state(state: str, message: str = '') -> None:
    with _lock:
        _state.update(state=state, message=message)


def is_busy() -> bool:
    with _lock:
        return _state['state'] in BUSY_STATES


def begin_install() -> Tuple[bool, str]:
    """Validate and start an install in a worker thread.

    Returns (started, reason). reason is 'busy' / 'no-update' when refused.
    """
    with _lock:
        if _state['state'] in BUSY_STATES:
            return False, 'busy'
        info = _cache
        kind = detect_install_kind()
        if (info is None or info.get('error') is not None or not is_newer(info.get('tag'))
                or not can_auto_install(kind)):
            return False, 'no-update'
        _state.update(state=DOWNLOADING, message='Starting update')
    threading.Thread(target=run_install, args=(info, kind),
                     name='update-install', daemon=True).start()
    return True, ''


def run_install(info: Dict[str, Any], kind: str) -> None:
    """Worker body: never raises; failures become state=error."""
    try:
        if kind == 'windows-installer':
            install_windows(info)
        elif kind == 'source':
            install_source(info)
        else:
            raise UpdateError('This install type cannot update itself')
    except UpdateError as exc:
        logger.warning('Update failed: %s', exc)
        _set_state(ERROR, str(exc))
    except Exception as exc:
        logger.exception('Update crashed')
        _set_state(ERROR, _short_error(exc))


class UpdateError(Exception):
    """A user-presentable update failure."""


# --------------------------------------------------------------------------
# Process exit seams (patched in tests)
# --------------------------------------------------------------------------

def _hard_exit(code: int) -> None:
    logging.shutdown()
    os._exit(code)


def schedule_exit(code: int, delay: float = EXIT_DELAY) -> None:
    """Exit the process after ``delay`` so the HTTP response can flush."""
    timer = threading.Timer(delay, _hard_exit, args=(code,))
    timer.daemon = True
    timer.start()


# --------------------------------------------------------------------------
# Windows installer
# --------------------------------------------------------------------------

def _update_dir() -> Path:
    return Path(tempfile.gettempdir()) / 'vdock-update'


def validate_download_url(url: Any) -> str:
    if not isinstance(url, str) or not url.startswith(DOWNLOAD_PREFIX):
        raise UpdateError('Refusing to download from an unexpected location')
    return url


def _download(url: str, dest: Path) -> int:
    """Stream ``url`` to ``dest``; returns bytes written. Seam for tests."""
    req = urllib.request.Request(url, headers={'User-Agent': f'VDock/{__version__}'})
    written = 0
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest, 'wb') as out:  # nosec B310 - prefix validated
        while True:
            chunk = resp.read(1024 * 256)
            if not chunk:
                break
            out.write(chunk)
            written += len(chunk)
    return written


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def _spawn_detached(args: Union[str, List[str]], **kwargs: Any) -> Any:
    """Popen seam. Windows-only creation flags are applied by the caller."""
    return subprocess.Popen(args, **kwargs)


def _start_cmd_script(script: Path, cwd: Optional[Path] = None) -> None:
    """Run a .cmd detached via ``start`` so it leaves VDock's process tree.

    Passed as a string, not a list: list2cmdline escapes the empty ``""``
    window title as ``\\"\\"``, which cmd misreads and the script never runs.
    """
    flags = (getattr(subprocess, 'DETACHED_PROCESS', 0x00000008)
             | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0x00000200))
    _spawn_detached(f'cmd /c start "" /min "{script}"', creationflags=flags,
                    close_fds=True, cwd=str(cwd) if cwd else None)


def build_cmd_script(installer: Path) -> str:
    return (
        '@echo off\r\n'
        'timeout /t 3 /nobreak >nul\r\n'
        f'start "" "{installer}" /S --force-run\r\n'
    )


def install_windows(info: Dict[str, Any]) -> None:
    asset = pick_asset('windows-installer', info.get('assets') or [])
    if not asset or not asset.get('browser_download_url'):
        raise UpdateError('No Windows installer found in the latest release')
    url = validate_download_url(asset['browser_download_url'])
    name = Path(str(asset.get('name'))).name  # strip any path components
    folder = _update_dir()
    folder.mkdir(parents=True, exist_ok=True)
    installer = folder / name

    _set_state(DOWNLOADING, f'Downloading {name}')
    written = _download(url, installer)

    expected = asset.get('size')
    if isinstance(expected, int) and expected > 0 and written != expected:
        _safe_unlink(installer)
        raise UpdateError('Download incomplete (size mismatch)')
    digest = asset.get('digest')
    if isinstance(digest, str) and digest.lower().startswith('sha256:'):
        if _sha256(installer).lower() != digest.split(':', 1)[1].strip().lower():
            _safe_unlink(installer)
            raise UpdateError('Download corrupted (checksum mismatch)')

    _set_state(INSTALLING, 'Installing update')
    cmd_path = folder / 'run-update.cmd'
    cmd_path.write_text(build_cmd_script(installer), encoding='utf-8', newline='')

    _start_cmd_script(cmd_path)

    _set_state(RESTARTING, 'Restarting VDock')
    schedule_exit(EXIT_FOR_UPDATE)


def _safe_unlink(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


# --------------------------------------------------------------------------
# Source checkout
# --------------------------------------------------------------------------

def _run(cmd: List[str], cwd: Path, timeout: int, label: str) -> str:
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                              timeout=timeout)
    except FileNotFoundError:
        raise UpdateError(f'{label}: command not found ({cmd[0]})')
    except subprocess.TimeoutExpired:
        raise UpdateError(f'{label}: timed out')
    if proc.returncode != 0:
        tail = ' | '.join((proc.stderr or proc.stdout or '').strip().splitlines()[-3:])
        raise UpdateError(f'{label} failed: {tail}'[:300])
    return proc.stdout or ''


def _npm() -> str:
    return 'npm.cmd' if sys.platform == 'win32' else 'npm'


def install_source(info: Dict[str, Any]) -> None:
    root = project_root()
    _set_state(DOWNLOADING, 'Checking working tree')
    status = _run(['git', 'status', '--porcelain', '--untracked-files=no'], root, 30, 'git status')
    if status.strip():
        raise UpdateError('Local changes - update manually')

    _set_state(DOWNLOADING, 'Pulling latest code')
    _run(['git', 'pull', '--ff-only'], root, 300, 'git pull')

    _set_state(INSTALLING, 'Installing Python dependencies')
    _run([sys.executable, '-m', 'pip', 'install', '-r',
          str(root / 'backend' / 'requirements.txt')], root, 900, 'pip install')

    frontend = root / 'frontend'
    _set_state(INSTALLING, 'Installing frontend dependencies')
    _run([_npm(), 'install'], frontend, 900, 'npm install')
    _set_state(INSTALLING, 'Building frontend')
    _run([_npm(), 'run', 'build'], frontend, 900, 'npm run build')

    _set_state(RESTARTING, 'Restarting VDock')
    restart_self(root)


def restart_self(root: Path) -> None:
    """Under Electron exit 0 (it restarts us); else relaunch via the launcher.

    The detached relauncher sleeps first so this process has released the
    port by the time the new one starts.
    """
    if _env('VDOCK_ELECTRON') == '1':
        schedule_exit(0)
        return
    if sys.platform == 'win32':
        folder = _update_dir()
        folder.mkdir(parents=True, exist_ok=True)
        script = folder / 'relaunch.cmd'
        script.write_text('timeout /t 5 /nobreak >nul\r\n'
                          f'cd /d "{root}"\r\n'
                          f'call "{root / "launch.bat"}"\r\n',
                          encoding='utf-8', newline='')
        _start_cmd_script(script, cwd=root)
    else:
        args = ['sh', '-c', f'sleep 5; exec sh "{root / "launch.sh"}"']
        _spawn_detached(args, start_new_session=True, close_fds=True, cwd=str(root),
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    schedule_exit(0)
