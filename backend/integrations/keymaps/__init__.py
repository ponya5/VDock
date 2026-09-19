"""App keymaps, one module per application."""
from typing import Dict, Optional, Tuple

from .base import (
    AppProfile,
    Command,
    RISK_DESTRUCTIVE,
    RISK_INPUT,
    RISK_SAFE,
    CURSOR_EXES,
    JETBRAINS_EXES,
    VSCODE_EXES,
)
from .copilot import COPILOT_COMMANDS, COPILOT_PROFILE
from .cursor import CURSOR_COMMANDS, CURSOR_PROFILE

ALL_COMMANDS: Tuple[Command, ...] = COPILOT_COMMANDS + CURSOR_COMMANDS

COMMANDS_BY_ID: Dict[str, Command] = {cmd.id: cmd for cmd in ALL_COMMANDS}

ALL_PROFILES: Tuple[AppProfile, ...] = (CURSOR_PROFILE, COPILOT_PROFILE)

PROFILES_BY_ID: Dict[str, AppProfile] = {p.id: p for p in ALL_PROFILES}

_PROFILE_BY_EXE: Dict[str, AppProfile] = {
    exe.lower(): profile
    for profile in ALL_PROFILES
    for exe in profile.exes
}


def profile_for_exe(exe: str) -> Optional[AppProfile]:
    """The profile matching a process name, or None.

    Window titles and process listings disagree about case (`Cursor.exe` vs
    `cursor.exe`), so matching is always lowercased.
    """
    if not exe:
        return None
    return _PROFILE_BY_EXE.get(exe.lower())


__all__ = [
    'Command', 'AppProfile', 'RISK_SAFE', 'RISK_INPUT', 'RISK_DESTRUCTIVE',
    'VSCODE_EXES', 'CURSOR_EXES', 'JETBRAINS_EXES',
    'COPILOT_COMMANDS', 'CURSOR_COMMANDS', 'ALL_COMMANDS', 'COMMANDS_BY_ID',
    'ALL_PROFILES', 'PROFILES_BY_ID', 'profile_for_exe',
]
