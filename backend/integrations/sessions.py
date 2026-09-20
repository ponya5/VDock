"""Cheap "is a session alive" checks via process scan.

This is the interim interlock for terminal-agent commands until the Phase-3
hook registry lands (DL-004): a live Claude Code session will eventually
register itself through Claude Code hooks. Until then, a running process
whose name or command line mentions the marker counts as a session.

Deliberately a heuristic: it can false-positive (e.g. the Claude desktop app
also shows up as a 'claude' process). Commands gated on it are typed input,
whose worst case in a wrong terminal is a shell "command not found" -- never
a silent destructive act, so a weak interlock is acceptable here and the
hook registry tightens it later.

Not named ``*_pack`` on purpose: PluginManager only scans that suffix.
"""
import logging
from typing import Optional

import psutil

logger = logging.getLogger('vdock')


def session_alive(marker: str) -> bool:
    """True when some live process looks like ``marker``.

    Matches the substring against the process name and the joined command
    line, lowercased -- so 'claude' matches claude.exe, `node .../claude`,
    and `claude --continue` alike.
    """
    needle = (marker or '').lower().strip()
    if not needle:
        return False

    for proc in psutil.process_iter(('name', 'cmdline')):
        try:
            info = proc.info
            name = (info.get('name') or '').lower()
            if needle in name:
                return True
            cmdline = info.get('cmdline')
            if cmdline and needle in ' '.join(cmdline).lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False


def find_session_process(marker: str) -> Optional[int]:
    """PID of the first matching process, or None. Diagnostic helper."""
    needle = (marker or '').lower().strip()
    if not needle:
        return None
    for proc in psutil.process_iter(('name', 'cmdline')):
        try:
            info = proc.info
            if needle in (info.get('name') or '').lower():
                return proc.pid
            cmdline = info.get('cmdline')
            if cmdline and needle in ' '.join(cmdline).lower():
                return proc.pid
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None
