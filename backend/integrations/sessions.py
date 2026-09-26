"""Cheap "is a session alive" checks via process scan.

This is the interim interlock for terminal-agent commands until the Phase-3
hook registry lands (DL-004): a live Claude Code session will eventually
register itself through Claude Code hooks. Until then, a running process
that looks like the agent's own binary counts as a session.

The match is deliberately stricter than a bare substring: the marker must
appear as the process name, as argv[0], or as an invocable-looking command
line token (a path or script carrying an executable extension). That keeps
the Claude *desktop app*, agent harnesses, ``cmd /c claude`` wrappers and
``python -c "... claude ..."`` blobs from counting -- all of which merely
*mention* claude without being a session. ``iter_session_pids`` is shared by
the liveness check and the window resolver so both agree on what a session
is.

A wrong guess types keystrokes into the wrong terminal, whose worst case is
a shell "command not found" -- never a silent destructive act -- so a
heuristic interlock is acceptable until the hook registry tightens it.

Not named ``*_pack`` on purpose: PluginManager only scans that suffix.
"""
import logging
import os
import threading
from typing import Dict, List, Optional

import psutil

logger = logging.getLogger('vdock')

#: Extensions a session binary or launcher script can carry. A mid-command
#: token must look like one of these to count -- bare ``claude`` arguments
#: and ``-c`` code blobs do not.
_INVOCABLE_EXTS = ('.exe', '.cmd', '.bat', '.com', '.js', '.mjs', '.cjs',
                   '.py', '.ps1', '.sh')

#: Install locations of the Claude desktop app and its helpers: they are named
#: or pathed like the CLI but are not sessions. ``packages\claude_`` is the
#: MSIX package family (``Packages\Claude_pzs8sxrjxfjjc\...``) — it also holds
#: helpers like ``chrome-native-host.exe`` whose name never mentions claude,
#: so the path check must not require the marker in the process name.
_DESKTOP_APP_DIRS = ('anthropicclaude', 'windowsapps', r'packages\claude_',
                     'chromenativehost')


def _is_desktop_app(info: dict, needle: str) -> bool:
    """True when the process lives under the desktop app's install dirs.

    Checks the exe path and argv[0] rather than the process name: helper
    processes (the Chrome native-messaging bridge, updaters) carry the
    marker only in their path, and matching those would aim keystrokes at a
    browser window.
    """
    exe = (info.get('exe') or '').lower()
    cmdline = info.get('cmdline') or []
    argv0 = str(cmdline[0]).lower() if cmdline else ''
    return any(d in exe or d in argv0 for d in _DESKTOP_APP_DIRS)


def _invocable_token(token: str, needle: str) -> bool:
    """True when a cmdline token names a marker executable or script.

    argv[0] is matched by the caller; for later tokens we require a
    script/binary-shaped element so helper processes that merely mention
    the marker in an argument do not count.
    """
    if needle not in token.lower():
        return False
    base = token.strip().strip('\'"').replace('/', os.sep)
    base = base.rsplit(os.sep, 1)[-1]
    return base.endswith(_INVOCABLE_EXTS)


def _matches(info: dict, needle: str) -> bool:
    if _is_desktop_app(info, needle):
        return False
    if needle in (info.get('name') or '').lower():
        return True
    cmdline = info.get('cmdline') or []
    for i, token in enumerate(cmdline):
        if i == 0:
            if needle in token.lower():
                return True
        elif _invocable_token(token, needle):
            return True
    return False


def iter_session_pids(marker: str) -> List[int]:
    """PIDs of processes that look like a live ``marker`` session."""
    needle = (marker or '').lower().strip()
    if not needle:
        return []
    pids: List[int] = []
    for proc in psutil.process_iter(('name', 'cmdline', 'exe')):
        try:
            if _matches(proc.info, needle):
                pids.append(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied,
                psutil.ZombieProcess):
            continue
    return pids


def session_alive(marker: str) -> bool:
    """True when some live process looks like ``marker``."""
    return bool(iter_session_pids(marker))


def find_session_process(marker: str) -> Optional[int]:
    """PID of the first matching process, or None. Diagnostic helper."""
    pids = iter_session_pids(marker)
    return pids[0] if pids else None


# ---------------------------------------------------------------------------
# Pinned target (DL-071)
#
# The deck-level "control THIS session" choice, picked from the session list
# in the agent action bar. Pinned by pid: the host window is re-resolved from
# the pid on every press, so a window handle going stale can never mistarget
# the pin. In-memory only — a pin is meaningless once the session dies or the
# backend restarts.
# ---------------------------------------------------------------------------

_pins: Dict[str, int] = {}
_pins_lock = threading.Lock()


def pin_session(marker: str, pid: int) -> bool:
    """Pin ``pid`` as ``marker``'s target session.

    Returns False when the pid is not a live session for the marker — a pin
    can only ever point at a real session, so a stale or forged pin cannot
    redirect keystrokes.
    """
    needle = (marker or '').lower().strip()
    if not needle:
        return False
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid not in iter_session_pids(needle):
        return False
    with _pins_lock:
        _pins[needle] = pid
    return True


def unpin_session(marker: str) -> None:
    """Clear ``marker``'s pin — resolution falls back to auto."""
    with _pins_lock:
        _pins.pop((marker or '').lower().strip(), None)


def pinned_pid(marker: str) -> Optional[int]:
    """``marker``'s pinned pid, or None when unpinned or the session died.

    A dead pin clears itself here so every press after the session ends falls
    back to normal resolution instead of failing forever.
    """
    needle = (marker or '').lower().strip()
    with _pins_lock:
        pid = _pins.get(needle)
    if pid is None:
        return None
    if pid not in iter_session_pids(needle):
        with _pins_lock:
            _pins.pop(needle, None)
        return None
    return pid


def reset_pins() -> None:
    """Drop all pins (tests)."""
    with _pins_lock:
        _pins.clear()
