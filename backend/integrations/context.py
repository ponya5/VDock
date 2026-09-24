"""Working-directory and editor context shared by the integration packs.

A dev control deck is only useful if its buttons act on *the thing you are
looking at*. "Ask Claude about this repo" and "list PRs" both need to know which
project is in front of the user, and making them useful means not asking the
user to hardcode a path into every button.

Resolution order, most specific first:

1. an explicit path configured on the button;
2. the folder name in the focused editor's window title -- ``AppMonitor``
   already captures ``window_title`` for the foreground process, and VS Code,
   Cursor and the JetBrains IDEs all put the project name there;
3. ``VDOCK_DEFAULT_REPO_PATH`` from the environment;
4. the process working directory.

Step 2 is a heuristic and deliberately conservative: it only accepts a match
when the resolved directory actually exists under a known workspace root, so a
window title like "untitled-1" or a browser tab can never redirect a command
into an unrelated folder.
"""
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from utils import subprocess_runner as sr

logger = logging.getLogger('vdock')

# Editors that name the open project in their window title.
EDITOR_EXECUTABLES = {
    'cursor.exe': 'Cursor',
    'code.exe': 'VS Code',
    'codium.exe': 'VSCodium',
    'idea64.exe': 'IntelliJ IDEA',
    'pycharm64.exe': 'PyCharm',
    'webstorm64.exe': 'WebStorm',
    'devenv.exe': 'Visual Studio',
    'windowsterminal.exe': 'Windows Terminal',
    'wt.exe': 'Windows Terminal',
}

# "file.py - my-project - Cursor" / "my-project - Cursor"
_TITLE_SEPARATOR = re.compile(r'\s+[-–—]\s+')


@dataclass(frozen=True)
class EditorContext:
    """What VDock believes the user is looking at."""
    app_exe: Optional[str] = None
    app_name: Optional[str] = None
    window_title: Optional[str] = None
    project_name: Optional[str] = None
    cwd: Optional[str] = None

    @property
    def is_editor(self) -> bool:
        return bool(self.app_exe) and self.app_exe.lower() in EDITOR_EXECUTABLES


def _workspace_roots() -> List[Path]:
    """Directories under which a project named in a window title may live."""
    roots: List[Path] = []

    configured = os.environ.get('VDOCK_DEFAULT_REPO_PATH', '').strip()
    if configured:
        path = Path(configured).expanduser()
        roots.append(path)
        roots.append(path.parent)

    home = Path.home()
    for name in ('CursorRepo', 'Projects', 'repos', 'src', 'dev', 'code',
                 'Documents/GitHub', 'source/repos'):
        candidate = home / name
        if candidate.is_dir():
            roots.append(candidate)

    return roots


def project_name_from_title(window_title: str) -> Optional[str]:
    """Pull the project name out of an editor window title.

    Titles look like "app.py - vdock2 - Cursor" or "vdock2 - Visual Studio
    Code". The application name is the last segment and the project the one
    before it.
    """
    if not window_title:
        return None

    parts = [p.strip() for p in _TITLE_SEPARATOR.split(window_title) if p.strip()]
    if len(parts) < 2:
        return None

    # Drop the trailing application name, then take the last remaining segment.
    candidate = parts[-2]

    # Editors prefix unsaved or modified files with a bullet.
    candidate = candidate.lstrip('●•* ').strip()

    # A path segment rather than a project name.
    if not candidate or candidate.startswith(('http://', 'https://')):
        return None
    if os.sep in candidate or '/' in candidate:
        candidate = Path(candidate).name

    return candidate or None


def _resolve_project_dir(project_name: str) -> Optional[str]:
    """Find a real directory for ``project_name`` under a known root."""
    if not project_name:
        return None
    for root in _workspace_roots():
        try:
            candidate = root / project_name
            if candidate.is_dir():
                return str(candidate)
        except OSError:
            continue
    return None


def current_editor() -> EditorContext:
    """Describe the focused application, as far as VDock can tell."""
    try:
        from utils.app_monitor import get_app_monitor
        active = get_app_monitor().get_current_app()
        if not active:
            from utils.app_monitor import get_current_active_app
            active = get_current_active_app()
    except Exception as e:  # pragma: no cover - platform dependent
        logger.debug('Could not read the active window: %s', e)
        active = None

    if not active:
        return EditorContext()

    exe = (active.get('exe') or '').lower()
    title = active.get('window_title') or ''
    project = project_name_from_title(title) if exe in EDITOR_EXECUTABLES else None

    return EditorContext(
        app_exe=exe or None,
        app_name=EDITOR_EXECUTABLES.get(exe, active.get('name')),
        window_title=title or None,
        project_name=project,
        cwd=_resolve_project_dir(project) if project else None,
    )


def resolve_cwd(configured: Optional[str] = None) -> str:
    """Pick the working directory an action should run in.

    Args:
        configured: An explicit path from the button's config. Wins outright.
    """
    if configured:
        path = Path(configured).expanduser()
        if path.is_dir():
            return str(path)
        logger.warning('Configured path does not exist, ignoring: %s', configured)

    editor = current_editor()
    if editor.cwd:
        return editor.cwd

    fallback = os.environ.get('VDOCK_DEFAULT_REPO_PATH', '').strip()
    if fallback:
        path = Path(fallback).expanduser()
        if path.is_dir():
            return str(path)

    return os.getcwd()


def git_repo_root(cwd: Optional[str] = None) -> Optional[str]:
    """The git repository containing ``cwd``, or None."""
    target = resolve_cwd(cwd)
    try:
        result = sr.run(['git', 'rev-parse', '--show-toplevel'], cwd=target,
                        timeout=10)
    except sr.BinaryNotFoundError:
        return None
    return result.stdout.strip() if result.ok else None


def current_branch(cwd: Optional[str] = None) -> Optional[str]:
    """The checked-out branch name, or None."""
    target = resolve_cwd(cwd)
    try:
        result = sr.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=target,
                        timeout=10)
    except sr.BinaryNotFoundError:
        return None
    return result.stdout.strip() if result.ok else None


def clipboard_text() -> str:
    """The clipboard's text, or '' when it is empty or unreadable."""
    try:
        import pyperclip
        return pyperclip.paste() or ''
    except Exception as e:
        logger.warning('Could not read the clipboard: %s', e)
        return ''


def expand_placeholders(text: str, cwd: Optional[str] = None) -> str:
    """Substitute ``{clipboard}``, ``{repo}``, ``{branch}`` and ``{project}``.

    Lets one saved prompt be reused across projects -- "review the staged diff
    in {repo}" works wherever the user happens to be.
    """
    if not text or '{' not in text:
        return text

    replacements = {}

    if '{clipboard}' in text:
        replacements['{clipboard}'] = clipboard_text()

    if '{repo}' in text or '{project}' in text or '{branch}' in text:
        target = resolve_cwd(cwd)
        replacements['{repo}'] = target
        replacements['{project}'] = Path(target).name
        replacements['{branch}'] = current_branch(target) or ''

    for token, value in replacements.items():
        text = text.replace(token, value)
    return text
