"""Install VDock's agent hook into Claude Code and Cursor.

Both agents read a user-level JSON file listing shell commands to run on
lifecycle events. VDock adds one command — ``scripts/vdock_agent_hook.py`` —
to the events that reveal the agent's state (see ``agent_state``).

Rules shared by both installers:
  * merge, never replace: entries VDock doesn't own are left untouched;
  * ownership is recognised by ``HOOK_MARKER`` in the command string;
  * idempotent, and an older partial install (DL-045 only hooked
    Notification + Stop) is upgraded in place;
  * a one-shot ``.vdock-backup.json`` copy is written before any change.
"""
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

from config import Config

logger = logging.getLogger('vdock')

HOOK_MARKER = 'vdock_agent_hook'

#: Claude Code events whose firing says something about the session's state.
CLAUDE_HOOK_EVENTS: Tuple[str, ...] = (
    'SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PostToolUse',
    'Notification', 'Stop', 'SessionEnd',
)

#: Cursor events that are purely observational. Permission-gating events
#: (beforeShellExecution, beforeMCPExecution) are deliberately absent: a
#: hook there has to answer allow/deny, which would bypass Cursor's own
#: approval dialog.
CURSOR_HOOK_EVENTS: Tuple[str, ...] = (
    'beforeSubmitPrompt', 'afterAgentResponse', 'stop',
)


class HookSettingsError(ValueError):
    """The agent's settings file exists but can't be parsed."""


@dataclass(frozen=True)
class HookInstallResult:
    installed: bool
    already: bool
    settings_path: Path
    added_events: Tuple[str, ...]


def hook_script_path() -> Path:
    return Path(__file__).resolve().parent.parent / 'scripts' / 'vdock_agent_hook.py'


def hook_command(source: str) -> str:
    # Forward slashes work on Windows Python too and avoid JSON escaping pain.
    script = hook_script_path().as_posix()
    return f'python "{script}" --port {Config.PORT} --source {source}'


def claude_settings_path() -> Path:
    return Path.home() / '.claude' / 'settings.json'


def cursor_hooks_path() -> Path:
    return Path.home() / '.cursor' / 'hooks.json'


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError) as error:
        raise HookSettingsError(f'{path} is not valid JSON: {error}') from error
    if not isinstance(loaded, dict):
        raise HookSettingsError(f'{path} does not contain a JSON object')
    return loaded


def _write_with_backup(path: Path, settings: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_suffix('.vdock-backup.json')
        backup.write_text(path.read_text(encoding='utf-8'), encoding='utf-8')
    path.write_text(json.dumps(settings, indent=2) + '\n', encoding='utf-8')


# ---------------------------------------------------------------------------
# Claude Code: {"hooks": {Event: [{"matcher": "", "hooks": [{"type", "command"}]}]}}
# ---------------------------------------------------------------------------

def _claude_event_has_hook(entries: Any) -> bool:
    if not isinstance(entries, list):
        return False
    for entry in entries:
        for hook in (entry or {}).get('hooks', []) if isinstance(entry, dict) else []:
            if HOOK_MARKER in str(hook.get('command', '')):
                return True
    return False


def claude_installed_events(settings: Dict[str, Any]) -> List[str]:
    hooks = settings.get('hooks') or {}
    return [event for event in CLAUDE_HOOK_EVENTS
            if _claude_event_has_hook(hooks.get(event))]


def _add_claude_events(settings: Dict[str, Any]) -> List[str]:
    hooks = settings.setdefault('hooks', {})
    command = hook_command('claude')
    added: List[str] = []
    for event in CLAUDE_HOOK_EVENTS:
        if _claude_event_has_hook(hooks.get(event)):
            continue
        hooks.setdefault(event, []).append({
            'matcher': '',
            'hooks': [{'type': 'command', 'command': command}],
        })
        added.append(event)
    return added


# ---------------------------------------------------------------------------
# Cursor: {"version": 1, "hooks": {event: [{"command": "..."}]}}
# ---------------------------------------------------------------------------

def _cursor_event_has_hook(entries: Any) -> bool:
    if not isinstance(entries, list):
        return False
    return any(
        isinstance(entry, dict) and HOOK_MARKER in str(entry.get('command', ''))
        for entry in entries
    )


def cursor_installed_events(settings: Dict[str, Any]) -> List[str]:
    hooks = settings.get('hooks') or {}
    return [event for event in CURSOR_HOOK_EVENTS
            if _cursor_event_has_hook(hooks.get(event))]


def _add_cursor_events(settings: Dict[str, Any]) -> List[str]:
    settings.setdefault('version', 1)
    hooks = settings.setdefault('hooks', {})
    command = hook_command('cursor')
    added: List[str] = []
    for event in CURSOR_HOOK_EVENTS:
        if _cursor_event_has_hook(hooks.get(event)):
            continue
        hooks.setdefault(event, []).append({'command': command})
        added.append(event)
    return added


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _AgentHookTarget:
    path: Callable[[], Path]
    installed_events: Callable[[Dict[str, Any]], List[str]]
    add_events: Callable[[Dict[str, Any]], List[str]]
    all_events: Tuple[str, ...]


_TARGETS: Dict[str, _AgentHookTarget] = {
    'claude': _AgentHookTarget(
        claude_settings_path, claude_installed_events, _add_claude_events,
        CLAUDE_HOOK_EVENTS,
    ),
    'cursor': _AgentHookTarget(
        cursor_hooks_path, cursor_installed_events, _add_cursor_events,
        CURSOR_HOOK_EVENTS,
    ),
}

SUPPORTED_AGENTS: Tuple[str, ...] = tuple(_TARGETS)


def _target(agent: str) -> _AgentHookTarget:
    target = _TARGETS.get(agent)
    if target is None:
        raise KeyError(f'Unsupported agent: {agent}')
    return target


def hook_status(agent: str) -> Dict[str, Any]:
    """Install state for ``agent``: fully installed, partial, or absent."""
    target = _target(agent)
    path = target.path()
    try:
        settings = _load_json(path)
    except HookSettingsError:
        return {'installed': False, 'partial': False, 'parse_error': True,
                'settings_path': str(path)}
    present = target.installed_events(settings)
    return {
        'installed': len(present) == len(target.all_events),
        'partial': 0 < len(present) < len(target.all_events),
        'settings_path': str(path),
    }


def install_hook(agent: str) -> HookInstallResult:
    """Merge VDock's hook into ``agent``'s settings file.

    Raises HookSettingsError when the existing file can't be parsed, and
    OSError when it can't be written.
    """
    target = _target(agent)
    path = target.path()
    settings = _load_json(path)
    added = target.add_events(settings)
    if not added:
        return HookInstallResult(True, True, path, ())
    _write_with_backup(path, settings)
    logger.info('Installed VDock %s hook into %s (%s)', agent, path, ', '.join(added))
    return HookInstallResult(True, False, path, tuple(added))
