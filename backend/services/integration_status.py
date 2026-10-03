"""Which integrations are usable right now -- booleans and labels only.

Shared by the boot report (``Config.report``) and ``GET /api/config/integrations``
so the log and Settings always agree. Nothing here returns or logs a secret
value, and it never spawns a process (``shutil.which`` lookups only).
"""
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from services import secrets

# (id, label, binary, help_url)
CLI_TOOLS = (
    ('gh_cli', 'GitHub CLI', 'gh', 'https://cli.github.com'),
    ('claude_cli', 'Claude Code CLI', 'claude', 'https://claude.com/product/claude-code'),
)


def secret_items() -> List[Dict[str, Any]]:
    items = []
    for spec in secrets.ALL_SECRETS:
        configured = secrets.is_configured(spec)
        # `configured` stays "you set a key"; `builtin` says the feature works
        # anyway through a free provider, so the UI should not read as missing.
        builtin = bool(spec.builtin_label) and not configured
        items.append({
            'id': spec.env_var,
            'label': spec.label,
            'kind': 'secret',
            'configured': configured,
            'builtin': builtin,
            'builtin_label': spec.builtin_label if builtin else '',
            'reason': '' if (configured or builtin) else spec.reason(),
            'help_url': spec.help_url,
            'unlocks': spec.unlocks,
        })
    return items


def cli_items() -> List[Dict[str, Any]]:
    from utils.subprocess_runner import find_binary

    items = []
    for tool_id, label, binary, help_url in CLI_TOOLS:
        found = find_binary(binary) is not None
        items.append({
            'id': tool_id,
            'label': label,
            'kind': 'cli',
            'configured': found,
            'reason': '' if found else f'{binary} was not found on PATH',
            'help_url': help_url,
        })
    return items


def _launch(path: Path) -> None:
    """Hand a file to the OS default application."""
    if sys.platform == 'win32':
        os.startfile(str(path))  # type: ignore[attr-defined]
    else:
        subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', str(path)])


def open_env_file() -> bool:
    """Open the env file in the OS default editor, creating it empty if absent.

    Local convenience for "paste your key here"; callers must gate on a
    localhost request. Returns False when the OS could not open it.
    """
    from config import env_file

    target = env_file()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch(exist_ok=True)
        _launch(target)
        return True
    except OSError:
        return False


def display_env_path() -> str:
    """The env file path for display -- never contains the user name.

    Source runs show the repo-relative ``backend/.env``; installed builds show
    ``%APPDATA%\\...`` style (or ``~/...`` elsewhere).
    """
    from config import env_file, project_root

    target = env_file()
    try:
        return target.relative_to(project_root()).as_posix()
    except ValueError:
        pass
    for var in ('APPDATA', 'LOCALAPPDATA'):
        base = os.environ.get(var)
        if base:
            try:
                return f'%{var}%\\' + str(target.relative_to(Path(base)))
            except ValueError:
                continue
    try:
        return '~/' + target.relative_to(Path.home()).as_posix()
    except ValueError:
        return target.name
