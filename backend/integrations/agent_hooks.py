"""Install VDock's agent hook into Claude Code, Cursor and Antigravity.

All three read a user-level JSON file listing shell commands to run on
lifecycle events. VDock adds one command — ``scripts/vdock_agent_hook.py`` —
to the events that reveal the agent's state (see ``agent_state``).

Antigravity's format differs: ``hooks.json`` maps a hook *name* to its
event configs, so VDock owns one named entry (``AGY_HOOK_NAME``) covering
all events, and the command carries ``--event`` because Antigravity's
stdin payload doesn't expose ``hook_event_name``.

Rules shared by all installers:
  * merge, never replace: entries VDock doesn't own are left untouched;
  * ownership is recognised by ``HOOK_MARKER`` in the command string;
  * idempotent, and an older partial install (DL-045 only hooked
    Notification + Stop) is upgraded in place;
  * a one-shot ``.vdock-backup.json`` copy is written before any change.
"""
import json
import logging
import os
import re
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

#: Antigravity's named entry in hooks.json and its observational events.
#: Stop fires when the execution loop terminates — the closest thing to
#: "idle" Antigravity exposes. There is no permission event, so 'waiting
#: for approval' can't be distinguished — the glow shows ready instead.
AGY_HOOK_NAME = 'vdock-agent-state'
AGY_HOOK_EVENTS: Tuple[str, ...] = (
    'PreInvocation', 'PostInvocation', 'PreToolUse', 'PostToolUse', 'Stop',
)
#: Tool events take a matcher+hooks entry; loop events take bare commands.
AGY_MATCHER_EVENTS = frozenset({'PreToolUse', 'PostToolUse'})


class HookSettingsError(ValueError):
    """The agent's settings file exists but can't be parsed."""


@dataclass(frozen=True)
class HookInstallResult:
    installed: bool
    already: bool
    settings_path: Path
    added_events: Tuple[str, ...]


@dataclass(frozen=True)
class HookUninstallResult:
    removed: bool
    already: bool
    settings_path: Path
    removed_events: Tuple[str, ...]


def hook_script_path() -> Path:
    return Path(__file__).resolve().parent.parent / 'scripts' / 'vdock_agent_hook.py'


def hook_command(source: str, event: str = '') -> str:
    # Forward slashes work on Windows Python too and avoid JSON escaping pain.
    script = hook_script_path().as_posix()
    command = f'python "{script}" --port {Config.PORT} --source {source}'
    # Antigravity's stdin payload doesn't carry the event name, so the
    # command pins it instead of relying on hook_event_name.
    return f'{command} --event {event}' if event else command


def claude_settings_path() -> Path:
    return Path.home() / '.claude' / 'settings.json'


def cursor_hooks_path() -> Path:
    return Path.home() / '.cursor' / 'hooks.json'


def antigravity_hooks_path() -> Path:
    return Path.home() / '.gemini' / 'config' / 'hooks.json'


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


def _atomic_write(path: Path, data: bytes) -> None:
    """Write beside the target and swap in, so a crash never leaves half a file."""
    temp = path.with_name(path.name + '.tmp')
    temp.write_bytes(data)
    os.replace(temp, path)


def _write_with_backup(path: Path, settings: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_suffix('.vdock-backup.json')
        backup.write_text(path.read_text(encoding='utf-8'), encoding='utf-8')
    _atomic_write(path, (json.dumps(settings, indent=2) + '\n').encode('utf-8'))


def _is_vdock_hook(hook: Any) -> bool:
    return isinstance(hook, dict) and HOOK_MARKER in str(hook.get('command', ''))


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


def _remove_claude_events(settings: Dict[str, Any]) -> List[str]:
    hooks = settings.get('hooks')
    if not isinstance(hooks, dict):
        return []
    removed: List[str] = []
    for event in list(hooks):
        entries = hooks[event]
        if not _claude_event_has_hook(entries):
            continue
        kept = []
        for entry in entries:
            if isinstance(entry, dict) and isinstance(entry.get('hooks'), list):
                remaining = [hook for hook in entry['hooks'] if not _is_vdock_hook(hook)]
                if len(remaining) != len(entry['hooks']):
                    if not remaining:
                        continue
                    entry['hooks'] = remaining
            kept.append(entry)
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]
        removed.append(event)
    if removed and not hooks:
        del settings['hooks']
    return removed


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


def _remove_cursor_events(settings: Dict[str, Any]) -> List[str]:
    hooks = settings.get('hooks')
    if not isinstance(hooks, dict):
        return []
    removed: List[str] = []
    for event in list(hooks):
        entries = hooks[event]
        if not _cursor_event_has_hook(entries):
            continue
        kept = [entry for entry in entries if not _is_vdock_hook(entry)]
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]
        removed.append(event)
    if removed and not hooks:
        del settings['hooks']
    return removed


# ---------------------------------------------------------------------------
# Antigravity: {"vdock-agent-state": {"enabled": true, "<Event>": [...]}}
# Loop events (PreInvocation/PostInvocation/Stop) take bare command
# entries; tool events (Pre/PostToolUse) take {matcher, hooks[]} entries.
# ---------------------------------------------------------------------------

def _agy_entry(settings: Dict[str, Any]) -> Dict[str, Any]:
    entry = settings.get(AGY_HOOK_NAME)
    return entry if isinstance(entry, dict) else {}


def _agy_event_covered(entries: Any) -> bool:
    """Any entry in the event's list carrying our command."""
    if not isinstance(entries, list):
        return False
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if HOOK_MARKER in str(entry.get('command', '')):
            return True
        for hook in entry.get('hooks') or []:
            if isinstance(hook, dict) and HOOK_MARKER in str(hook.get('command', '')):
                return True
    return False


def antigravity_installed_events(settings: Dict[str, Any]) -> List[str]:
    entry = _agy_entry(settings)
    return [event for event in AGY_HOOK_EVENTS
            if _agy_event_covered(entry.get(event))]


def _agy_command_entry(event: str) -> Dict[str, Any]:
    command = hook_command('antigravity', event)
    if event in AGY_MATCHER_EVENTS:
        return {'matcher': '',
                'hooks': [{'type': 'command', 'command': command, 'timeout': 10}]}
    return {'type': 'command', 'command': command, 'timeout': 10}


def _add_antigravity_events(settings: Dict[str, Any]) -> List[str]:
    entry = settings.setdefault(AGY_HOOK_NAME, {})
    if not isinstance(entry, dict):  # someone else owns the name — never clobber
        return []
    entry.setdefault('enabled', True)
    added: List[str] = []
    for event in AGY_HOOK_EVENTS:
        handlers = entry.setdefault(event, [])
        if not isinstance(handlers, list) or _agy_event_covered(handlers):
            continue
        handlers.append(_agy_command_entry(event))
        added.append(event)
    return added


def _remove_antigravity_events(settings: Dict[str, Any]) -> List[str]:
    entry = _agy_entry(settings)
    removed: List[str] = []
    for event in list(entry):
        handlers = entry[event]
        if not _agy_event_covered(handlers):
            continue
        kept = []
        for handler in handlers:
            if _is_vdock_hook(handler):
                continue
            if isinstance(handler, dict) and isinstance(handler.get('hooks'), list):
                remaining = [hook for hook in handler['hooks'] if not _is_vdock_hook(hook)]
                if len(remaining) != len(handler['hooks']):
                    if not remaining:
                        continue
                    handler['hooks'] = remaining
            kept.append(handler)
        if kept:
            entry[event] = kept
        else:
            del entry[event]
        removed.append(event)
    if removed and set(entry) <= {'enabled'}:
        del settings[AGY_HOOK_NAME]
    return removed


# ---------------------------------------------------------------------------
# Codex: ~/.codex/config.toml, top-level ``notify = ["cmd", "arg", ...]``.
# Codex has one hook, fired when a turn completes, so it can report
# "ready" but never "working". TOML, so this is a small text-level merge
# instead of a JSON round-trip: comments and tables are left exactly as is.
# ---------------------------------------------------------------------------

CODEX_HOOK_EVENTS: Tuple[str, ...] = ('agent-turn-complete',)

_TOML_NOTIFY_RE = re.compile(r'^[ \t]*notify[ \t]*=', re.MULTILINE)
_TOML_FIRST_TABLE_RE = re.compile(r'^[ \t]*\[', re.MULTILINE)


def codex_config_path() -> Path:
    return Path.home() / '.codex' / 'config.toml'


def _codex_notify_line() -> str:
    script = hook_script_path().as_posix()
    # JSON strings are valid TOML basic strings.
    argv = ['python', script, '--port', str(Config.PORT), '--source', 'codex']
    return f'notify = {json.dumps(argv)}'


def _codex_top_level(text: str) -> str:
    """The part of the file before the first [table] header."""
    table = _TOML_FIRST_TABLE_RE.search(text)
    return text[:table.start()] if table else text


def _codex_installed_events(text: str) -> List[str]:
    for line in _codex_top_level(text).splitlines():
        if _TOML_NOTIFY_RE.match(line) and HOOK_MARKER in line:
            return list(CODEX_HOOK_EVENTS)
    return []


def _install_codex(path: Path) -> HookInstallResult:
    text = path.read_text(encoding='utf-8') if path.exists() else ''
    if _codex_installed_events(text):
        return HookInstallResult(True, True, path, ())
    if _TOML_NOTIFY_RE.search(_codex_top_level(text)):
        # Codex takes a single notify command; never replace the user's.
        raise HookSettingsError(
            f'{path} already defines a notify command - remove it or add '
            f'the VDock hook by hand')
    updated = _codex_notify_line() + '\n' + text
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.with_suffix('.vdock-backup.toml').write_text(text, encoding='utf-8')
    path.write_text(updated, encoding='utf-8')
    logger.info('Installed VDock codex hook into %s', path)
    return HookInstallResult(True, False, path, CODEX_HOOK_EVENTS)


def _uninstall_codex(path: Path) -> HookUninstallResult:
    if not path.exists():
        return HookUninstallResult(False, True, path, ())
    # Bytes in, bytes out: every other line keeps its exact line ending.
    text = path.read_bytes().decode('utf-8')
    top_level_length = len(_codex_top_level(text))
    kept = []
    for line in text[:top_level_length].splitlines(keepends=True):
        if not (_TOML_NOTIFY_RE.match(line) and HOOK_MARKER in line):
            kept.append(line)
    updated = ''.join(kept) + text[top_level_length:]
    if updated == text:
        return HookUninstallResult(False, True, path, ())
    path.with_suffix('.vdock-backup.toml').write_bytes(text.encode('utf-8'))
    _atomic_write(path, updated.encode('utf-8'))
    logger.info('Removed VDock codex hook from %s', path)
    return HookUninstallResult(True, False, path, CODEX_HOOK_EVENTS)


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
    'antigravity': _AgentHookTarget(
        antigravity_hooks_path, antigravity_installed_events,
        _add_antigravity_events, AGY_HOOK_EVENTS,
    ),
}



SUPPORTED_AGENTS: Tuple[str, ...] = (*_TARGETS, 'codex')

#: Strips VDock's own entries from a parsed settings dict, returning the
#: events it touched. Kept apart from ``_AgentHookTarget`` so installers
#: and their test doubles stay as they were.
_REMOVERS: Dict[str, Callable[[Dict[str, Any]], List[str]]] = {
    'claude': _remove_claude_events,
    'cursor': _remove_cursor_events,
    'antigravity': _remove_antigravity_events,
}


def _target(agent: str) -> _AgentHookTarget:
    target = _TARGETS.get(agent)
    if target is None:
        raise KeyError(f'Unsupported agent: {agent}')
    return target


def hook_status(agent: str) -> Dict[str, Any]:
    """Install state for ``agent``: fully installed, partial, or absent."""
    if agent == 'codex':
        path = codex_config_path()
        try:
            text = path.read_text(encoding='utf-8') if path.exists() else ''
        except OSError:
            text = ''
        return {'installed': bool(_codex_installed_events(text)),
                'partial': False, 'settings_path': str(path)}
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
    if agent == 'codex':
        return _install_codex(codex_config_path())
    target = _target(agent)
    path = target.path()
    settings = _load_json(path)
    added = target.add_events(settings)
    if not added:
        return HookInstallResult(True, True, path, ())
    _write_with_backup(path, settings)
    logger.info('Installed VDock %s hook into %s (%s)', agent, path, ', '.join(added))
    return HookInstallResult(True, False, path, tuple(added))


def uninstall_hook(agent: str) -> HookUninstallResult:
    """Remove only VDock's own hook entries from ``agent``'s settings file.

    Nothing to remove is success with ``already=True`` and no write. A file
    left with nothing in it stays behind as ``{}`` (JSON) rather than being
    deleted. Raises HookSettingsError when the file can't be parsed, and
    OSError when it can't be written.
    """
    if agent == 'codex':
        return _uninstall_codex(codex_config_path())
    target = _target(agent)
    path = target.path()
    settings = _load_json(path)
    removed = _REMOVERS[agent](settings)
    if not removed:
        return HookUninstallResult(False, True, path, ())
    _write_with_backup(path, settings)
    logger.info('Removed VDock %s hook from %s (%s)', agent, path, ', '.join(removed))
    return HookUninstallResult(True, False, path, tuple(removed))
