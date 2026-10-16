"""Install VDock's agent hook into Claude Code, Cursor, Antigravity and Codex.

All four read a user-level JSON file listing shell commands to run on
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
import platform
import re
import shlex
import sys
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
    # DL-009: immediate permission signal, and the API-error end of a turn.
    'PermissionRequest', 'StopFailure',
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
    #: A one-time step the user still has to take for the hook to run.
    note: str = ''


@dataclass(frozen=True)
class HookUninstallResult:
    removed: bool
    already: bool
    settings_path: Path
    removed_events: Tuple[str, ...]


def hook_script_path() -> Path:
    """The hook script shipped with this VDock (source tree / frozen bundle)."""
    return Path(__file__).resolve().parent.parent / 'scripts' / 'vdock_agent_hook.py'


#: Release builds run the hook through the frozen backend itself; app.py
#: dispatches on this flag before importing Flask. It contains HOOK_MARKER,
#: so ownership detection keeps working for these commands too.
FROZEN_HOOK_FLAG = '--vdock_agent_hook'


def stable_hook_dir() -> Path:
    """Where the hook copy agents run lives - outside the VDock folder (DL-009).

    The agent's settings file outlives the VDock folder: moved, re-cloned or
    deleted, a hook pointing *into* it ran ``python3 <missing file>``, which
    exits 2 - and exit 2 is how Claude Code and Cursor hooks say "block this
    prompt". A copy under the user's home never disappears with the folder.
    """
    return Path.home() / '.vdock' / 'agent_hook'


def is_frozen() -> bool:
    return bool(getattr(sys, 'frozen', False))


def ensure_stable_hook_script() -> Path:
    """Copy the shipped hook script to ``stable_hook_dir()`` when it differs."""
    target = stable_hook_dir() / 'vdock_agent_hook.py'
    shipped = hook_script_path().read_bytes()
    try:
        if target.read_bytes() == shipped:
            return target
    except OSError:
        pass
    target.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(target, shipped)
    return target


def hook_interpreter() -> str:
    """Python command that exists on a stock install of this OS.

    Windows installs provide ``python``; macOS (and most Linux distros) only
    ship ``python3`` -- a ``python`` hook there fails with "command not found"
    and the agent silently never reports.
    """
    return 'python' if platform.system() == 'Windows' else 'python3'


def hook_argv(source: str, event: str = '') -> List[str]:
    """The hook as an argument list (Codex runs it without a shell).

    Release builds: the frozen backend in hook mode - no Python needed on the
    machine (a bare ``python`` is the Microsoft Store stub on many Windows
    PCs). Source installs: the system interpreter on the stable copy, exactly
    the interpreter choice that already works on both OSes.
    """
    if is_frozen():
        argv = [Path(sys.executable).as_posix(), FROZEN_HOOK_FLAG]
    else:
        # Forward slashes work on Windows Python too and avoid JSON escaping pain.
        argv = [hook_interpreter(), (stable_hook_dir() / 'vdock_agent_hook.py').as_posix()]
    argv += ['--port', str(Config.PORT), '--source', source]
    # Antigravity's stdin payload doesn't carry the event name, so the
    # command pins it instead of relying on hook_event_name.
    if event:
        argv += ['--event', event]
    return argv


def hook_command(source: str, event: str = '') -> str:
    argv = hook_argv(source, event)
    if is_frozen():
        exe = argv[0]
        # Quote only when needed: a quoted first token is a plain string to
        # PowerShell, while a path with spaces needs quotes everywhere.
        head = f'"{exe}"' if ' ' in exe else exe
        return ' '.join([head] + argv[1:])
    return ' '.join([argv[0], f'"{argv[1]}"'] + argv[2:])


def hook_target_missing(command: str) -> bool:
    """True when an installed VDock hook points at a file that is gone."""
    try:
        parts = shlex.split(command, posix=True)
    except ValueError:
        return False
    if FROZEN_HOOK_FLAG in parts:
        return not Path(parts[0]).exists()
    scripts = [part for part in parts if part.endswith('vdock_agent_hook.py')]
    return bool(scripts) and not Path(scripts[0]).exists()


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


_HOOK_SOURCE_PATTERN = re.compile(r'--source\s+(\S+)(?:\s+--event\s+(\S+))?')


def _current_command_for(existing_command: str) -> str:
    """``existing_command`` rebuilt with today's interpreter, script and port."""
    match = _HOOK_SOURCE_PATTERN.search(existing_command)
    if match is None:
        return existing_command
    return hook_command(match.group(1), match.group(2) or '')


def _refresh_stale_commands(node: Any) -> int:
    """Rewrite VDock hook commands that no longer match what we'd install now.

    An installed command bakes in the interpreter name and backend port, so it
    goes stale when the port is auto-moved (macOS: 5000 -> 5001) or the hook
    was written by a version that used ``python``. Returns how many changed.
    """
    refreshed = 0
    if isinstance(node, dict):
        command = node.get('command')
        if isinstance(command, str) and HOOK_MARKER in command:
            current = _current_command_for(command)
            if current != command:
                node['command'] = current
                refreshed += 1
        for child in node.values():
            refreshed += _refresh_stale_commands(child)
    elif isinstance(node, list):
        for child in node:
            refreshed += _refresh_stale_commands(child)
    return refreshed


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
# Codex: ~/.codex/hooks.json, the same {"hooks": {Event: [{matcher, hooks}]}}
# shape as Claude Code (DL-012). Codex used to have a single ``notify``
# command, fired when a turn completes; installs made back then keep that
# line (refreshed, never added) until the user removes the hook.
# ---------------------------------------------------------------------------

CODEX_HOOK_EVENTS: Tuple[str, ...] = (
    'SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PostToolUse',
    'PermissionRequest', 'Stop', 'Interrupt', 'SessionEnd',
)

#: Codex gives these two only 1 s unless told otherwise (3 s at most); the
#: rest default to 10 minutes - far longer than a state report may take.
_CODEX_HOOK_TIMEOUTS = {'Interrupt': 3, 'SessionEnd': 3}
_CODEX_DEFAULT_TIMEOUT = 10

CODEX_TRUST_NOTE = ('Codex runs a new hook only after you trust it: open Codex, '
                    'type /hooks and trust the VDock hook.')

_TOML_NOTIFY_RE = re.compile(r'^[ \t]*notify[ \t]*=', re.MULTILINE)
_TOML_FIRST_TABLE_RE = re.compile(r'^[ \t]*\[', re.MULTILINE)


def codex_hooks_path() -> Path:
    return Path.home() / '.codex' / 'hooks.json'


def codex_config_path() -> Path:
    return Path.home() / '.codex' / 'config.toml'


def codex_installed_events(settings: Dict[str, Any]) -> List[str]:
    hooks = settings.get('hooks') or {}
    return [event for event in CODEX_HOOK_EVENTS
            if _claude_event_has_hook(hooks.get(event))]


def _add_codex_events(settings: Dict[str, Any]) -> List[str]:
    hooks = settings.setdefault('hooks', {})
    command = hook_command('codex')
    added: List[str] = []
    for event in CODEX_HOOK_EVENTS:
        if _claude_event_has_hook(hooks.get(event)):
            continue
        hooks.setdefault(event, []).append({
            'matcher': '',
            'hooks': [{'type': 'command', 'command': command,
                       'timeout': _CODEX_HOOK_TIMEOUTS.get(event, _CODEX_DEFAULT_TIMEOUT)}],
        })
        added.append(event)
    return added


def _codex_notify_line() -> str:
    # JSON strings are valid TOML basic strings.
    argv = hook_argv('codex')
    return f'notify = {json.dumps(argv)}'


def _codex_top_level(text: str) -> str:
    """The part of the file before the first [table] header."""
    table = _TOML_FIRST_TABLE_RE.search(text)
    return text[:table.start()] if table else text


def _codex_legacy_notify(text: str) -> bool:
    """Does the config still carry VDock's own pre-hooks ``notify`` line?"""
    return any(_TOML_NOTIFY_RE.match(line) and HOOK_MARKER in line
               for line in _codex_top_level(text).splitlines())


def _codex_notify_target_missing(text: str) -> bool:
    for line in _codex_top_level(text).splitlines():
        if _TOML_NOTIFY_RE.match(line) and HOOK_MARKER in line:
            try:
                argv = json.loads(line.split('=', 1)[1].strip())
                if hook_target_missing(shlex.join(argv)):
                    return True
            except (ValueError, TypeError):
                pass
    return False


def _read_codex_config() -> str:
    path = codex_config_path()
    try:
        return path.read_text(encoding='utf-8') if path.exists() else ''
    except OSError:
        return ''


def _refresh_codex_notify(path: Path, text: str) -> bool:
    """Point a legacy VDock notify line at today's interpreter and port."""
    top_level_length = len(_codex_top_level(text))
    fresh_line = _codex_notify_line()
    rewritten = []
    for line in text[:top_level_length].splitlines(keepends=True):
        if _TOML_NOTIFY_RE.match(line) and HOOK_MARKER in line:
            line_ending = line[len(line.rstrip('\r\n')):]
            line = fresh_line + line_ending
        rewritten.append(line)
    updated = ''.join(rewritten) + text[top_level_length:]
    if updated == text:
        return False
    path.with_suffix('.vdock-backup.toml').write_bytes(text.encode('utf-8'))
    _atomic_write(path, updated.encode('utf-8'))
    logger.info('Refreshed VDock codex notify hook in %s', path)
    return True


def _remove_codex_notify(path: Path) -> bool:
    """Drop VDock's legacy notify line; every other byte stays as it was."""
    if not path.exists():
        return False
    # Bytes in, bytes out: every other line keeps its exact line ending.
    text = path.read_bytes().decode('utf-8')
    top_level_length = len(_codex_top_level(text))
    kept = []
    for line in text[:top_level_length].splitlines(keepends=True):
        if not (_TOML_NOTIFY_RE.match(line) and HOOK_MARKER in line):
            kept.append(line)
    updated = ''.join(kept) + text[top_level_length:]
    if updated == text:
        return False
    path.with_suffix('.vdock-backup.toml').write_bytes(text.encode('utf-8'))
    _atomic_write(path, updated.encode('utf-8'))
    logger.info('Removed VDock codex notify hook from %s', path)
    return True


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
    'codex': _AgentHookTarget(
        codex_hooks_path, codex_installed_events, _add_codex_events,
        CODEX_HOOK_EVENTS,
    ),
}


SUPPORTED_AGENTS: Tuple[str, ...] = tuple(_TARGETS)

#: Strips VDock's own entries from a parsed settings dict, returning the
#: events it touched. Kept apart from ``_AgentHookTarget`` so installers
#: and their test doubles stay as they were.
_REMOVERS: Dict[str, Callable[[Dict[str, Any]], List[str]]] = {
    'claude': _remove_claude_events,
    'cursor': _remove_cursor_events,
    'antigravity': _remove_antigravity_events,
    'codex': _remove_claude_events,  # same hooks.json shape as Claude Code
}


def _target(agent: str) -> _AgentHookTarget:
    target = _TARGETS.get(agent)
    if target is None:
        raise KeyError(f'Unsupported agent: {agent}')
    return target


def _vdock_commands(node: Any) -> List[str]:
    """Every VDock hook command string inside a settings structure."""
    found: List[str] = []
    if isinstance(node, dict):
        command = node.get('command')
        if isinstance(command, str) and HOOK_MARKER in command:
            found.append(command)
        for child in node.values():
            found += _vdock_commands(child)
    elif isinstance(node, list):
        for child in node:
            found += _vdock_commands(child)
    return found


def hook_status(agent: str) -> Dict[str, Any]:
    """Install state for ``agent``: fully installed, partial, or absent.

    ``broken`` flags an installed hook whose script or executable is gone
    (DL-009) - Settings offers Reinstall, startup repairs it.
    """
    target = _target(agent)
    path = target.path()
    try:
        settings = _load_json(path)
    except HookSettingsError:
        return {'installed': False, 'partial': False, 'parse_error': True,
                'settings_path': str(path)}
    present = target.installed_events(settings)
    broken = any(hook_target_missing(c) for c in _vdock_commands(settings))
    legacy = False
    if agent == 'codex':
        config_text = _read_codex_config()
        legacy = _codex_legacy_notify(config_text)
        broken = broken or _codex_notify_target_missing(config_text)
    return {
        'installed': len(present) == len(target.all_events),
        # A pre-hooks Codex install (notify only) is offered the upgrade.
        'partial': (0 < len(present) < len(target.all_events))
                   or (legacy and not present),
        'broken': broken,
        'settings_path': str(path),
    }


def install_hook(agent: str) -> HookInstallResult:
    """Merge VDock's hook into ``agent``'s settings file.

    Raises HookSettingsError when the existing file can't be parsed, and
    OSError when it can't be written.
    """
    if not is_frozen():
        ensure_stable_hook_script()
    target = _target(agent)
    path = target.path()
    settings = _load_json(path)
    refreshed = _refresh_stale_commands(settings)
    added = target.add_events(settings)
    # An install made before Codex had hooks keeps its notify line working.
    notify_refreshed = False
    if agent == 'codex':
        config = codex_config_path()
        text = _read_codex_config()
        if _codex_legacy_notify(text):
            notify_refreshed = _refresh_codex_notify(config, text)
    note = CODEX_TRUST_NOTE if agent == 'codex' and added else ''
    if not added and not refreshed:
        return HookInstallResult(True, not notify_refreshed, path, (), note)
    _write_with_backup(path, settings)
    logger.info(
        'Installed VDock %s hook into %s (added: %s, refreshed commands: %d)',
        agent, path, ', '.join(added) or 'none', refreshed,
    )
    return HookInstallResult(True, False, path, tuple(added), note)


def refresh_installed_hooks() -> List[str]:
    """Repair stale commands of hooks the user already installed.

    Never installs anything new: an agent without a VDock hook is skipped.
    Returns the agents that were rewritten.
    """
    repaired: List[str] = []
    for agent in SUPPORTED_AGENTS:
        try:
            status = hook_status(agent)
            if not (status.get('installed') or status.get('partial')):
                continue
            if not install_hook(agent).already:
                repaired.append(agent)
        except (HookSettingsError, OSError) as error:
            logger.warning('Could not refresh the %s hook: %s', agent, error)
    return repaired


def uninstall_hook(agent: str) -> HookUninstallResult:
    """Remove only VDock's own hook entries from ``agent``'s settings file.

    Nothing to remove is success with ``already=True`` and no write. A file
    left with nothing in it stays behind as ``{}`` (JSON) rather than being
    deleted. Raises HookSettingsError when the file can't be parsed, and
    OSError when it can't be written.
    """
    target = _target(agent)
    path = target.path()
    settings = _load_json(path)
    removed = _REMOVERS[agent](settings)
    notify_removed = agent == 'codex' and _remove_codex_notify(codex_config_path())
    if not removed:
        return HookUninstallResult(notify_removed, not notify_removed, path, ())
    _write_with_backup(path, settings)
    logger.info('Removed VDock %s hook from %s (%s)', agent, path, ', '.join(removed))
    return HookUninstallResult(True, False, path, tuple(removed))
