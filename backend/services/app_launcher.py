"""Launch a desktop app by name or path - Windows and macOS (DL-165).

`open_app` used to run ``start "" "<name>"`` / ``open -a "<name>"`` and report success whatever happened, so a missing
app produced an OS error dialog (or nothing) and "Open Claude" could start the Claude Code CLI that happens to be on
PATH instead of the Claude desktop app. This resolves the app first and returns a clear *not installed* result the
deck can turn into a toast with a way to point VDock at the app.

Resolution order: the user's configured path (Settings -> Scene templates -> gear -> Browse / Detect, stored as
``app_paths``) -> a known desktop app (Store/Start-menu app on Windows, ``/Applications/<App>.app`` on macOS) -> an
explicit path -> a name on PATH / registered with the OS.
"""
import logging
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger('vdock')

_SYSTEM = platform.system()


@dataclass(frozen=True)
class AppLaunchResult:
    ok: bool
    message: str
    details: str = ''
    not_installed: bool = False
    app: str = ''
    download: str = ''


@dataclass(frozen=True)
class DesktopApp:
    label: str
    win_start_name: str      # exact Start-menu name, resolved to a packaged-app id
    mac_bundle: str          # /Applications/<bundle>
    download: str = ''


#: Names that must mean the desktop app, not a same-named CLI on PATH.
KNOWN_DESKTOP_APPS: Dict[str, DesktopApp] = {
    'claude desktop': DesktopApp('Claude', 'Claude', 'Claude.app', 'https://claude.com/download'),
}

_START_APP_IDS: Dict[str, Optional[str]] = {}


def start_apps_id(name: str) -> Optional[str]:
    """AppUserModelID of a packaged Start-menu app by exact name (cached). Windows only."""
    if name in _START_APP_IDS:
        return _START_APP_IDS[name]
    app_id: Optional[str] = None
    try:
        out = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             "(Get-StartApps | Where-Object { $_.Name -eq '%s' } | Select-Object -First 1).AppID" % name.replace("'", "''")],
            capture_output=True, text=True, timeout=15,
        )
        candidate = (out.stdout or '').strip()
        if '!' in candidate and os.sep not in candidate and ' ' not in candidate:
            app_id = candidate
    except Exception as e:  # pragma: no cover - powershell missing
        logger.debug('Get-StartApps failed: %s', e)
    _START_APP_IDS[name] = app_id
    return app_id


def _pretty(name: str) -> str:
    base = os.path.basename(name.replace('\\', '/')) or name
    for suffix in ('.exe', '.app', '.cmd', '.bat', '.lnk'):
        if base.lower().endswith(suffix):
            base = base[: -len(suffix)]
    return base.strip() or name


def _hint(app: str) -> str:
    where = 'Settings -> Apps & scenes -> Scene templates -> the gear on the %s card' % app
    return ('VDock could not find %s on this computer. Install it, or if it lives somewhere unusual choose its '
            'location once: %s -> Browse (or Detect).' % (app, where))


def not_installed(app: str, download: str = '', extra: str = '') -> AppLaunchResult:
    details = _hint(app) + ((' ' + extra) if extra else '')
    if download:
        details += ' Download: %s' % download
    return AppLaunchResult(False, '%s is not installed' % app, details, True, app, download)


def _windows_resolvable(name: str) -> bool:
    """True when ``start`` would find a bare app name: PATH, App Paths registry, or a Start-menu app."""
    if shutil.which(name) or shutil.which(name + '.exe'):
        return True
    try:
        import winreg  # type: ignore
        stem = name if name.lower().endswith('.exe') else name + '.exe'
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                winreg.CloseKey(winreg.OpenKey(root, r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\%s' % stem))
                return True
            except OSError:
                continue
    except ImportError:
        pass
    return bool(start_apps_id(_pretty(name)))


def _mac_app_exists(bundle: str) -> bool:
    return any((base / bundle).exists() for base in (Path('/Applications'), Path.home() / 'Applications',
                                                     Path('/System/Applications')))


def _spawn(argv, shell=False) -> AppLaunchResult:
    try:
        proc = subprocess.run(argv, shell=shell, capture_output=True, text=True, timeout=30)
        if proc.returncode == 0:
            return AppLaunchResult(True, 'Opened')
        return AppLaunchResult(False, 'Could not open the app', (proc.stderr or proc.stdout or '').strip())
    except Exception as e:
        return AppLaunchResult(False, 'Could not open the app', str(e))


def launch(name_or_path: str, label: str = '') -> AppLaunchResult:
    """Open an app. ``name_or_path`` is a name ('Cursor'), an executable / .app path, or a known alias."""
    from services import app_paths as app_paths_svc

    raw = str(name_or_path or '').strip()
    if not raw:
        return AppLaunchResult(False, 'Application path/name not specified')
    key = raw.lower()
    known = KNOWN_DESKTOP_APPS.get(key)
    display = label or (known.label if known else _pretty(raw))

    # 1. the user's configured location wins (a stale one is ignored by override_for)
    override = app_paths_svc.override_for(raw)
    if override and app_paths_svc.launch_app(override):
        return AppLaunchResult(True, 'Opened %s' % display, app=display)

    # 2. a known desktop app: resolve it the OS way instead of by a name a CLI may share
    if known:
        if _SYSTEM == 'Windows':
            app_id = start_apps_id(known.win_start_name)
            if app_id:
                r = _spawn('start "" "shell:AppsFolder%s%s"' % (chr(92), app_id), shell=True)
                return AppLaunchResult(r.ok, ('Opened %s' % display) if r.ok else r.message, r.details, app=display)
            return not_installed(display, known.download)
        if _SYSTEM == 'Darwin':
            if not _mac_app_exists(known.mac_bundle):
                return not_installed(display, known.download)
            r = _spawn(['open', '-a', known.mac_bundle[:-4]])
            return AppLaunchResult(r.ok, ('Opened %s' % display) if r.ok else r.message, r.details, app=display)

    looks_like_path = any(sep in raw for sep in ('/', '\\')) or raw.lower().endswith(('.exe', '.app'))

    # 3. an explicit path
    if looks_like_path and (':' in raw[:3] or raw.startswith(('/', '~', '\\\\'))):
        expanded = Path(raw).expanduser()
        if not expanded.exists():
            return not_installed(display, extra='It was expected at %s.' % expanded)
        if app_paths_svc.launch_app(str(expanded)):
            return AppLaunchResult(True, 'Opened %s' % display, app=display)
        return AppLaunchResult(False, 'Could not open %s' % display, 'The file exists but could not be started: %s' % expanded)

    # 4. a bare name
    if _SYSTEM == 'Windows':
        if not _windows_resolvable(raw):
            return not_installed(display)
        r = _spawn('start "" "%s"' % raw, shell=True)
    elif _SYSTEM == 'Darwin':
        r = _spawn(['open', '-a', _pretty(raw)])
        if not r.ok and 'unable to find application' in (r.details or '').lower():
            return not_installed(display)
    else:
        r = _spawn(['xdg-open', raw])
        if not r.ok and shutil.which(raw):
            r = _spawn([raw])
        if not r.ok:
            return not_installed(display)
    return AppLaunchResult(r.ok, ('Opened %s' % display) if r.ok else r.message, r.details, app=display)
