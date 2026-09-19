"""App keymaps, one module per application."""
from typing import Dict, Optional, Tuple

from .base import (
    AppProfile,
    Command,
    RISK_DESTRUCTIVE,
    RISK_INPUT,
    RISK_SAFE,
    CURSOR_EXES,
    DEVIN_EXES,
    JETBRAINS_EXES,
    TERMINAL_EXES,
    VISUAL_STUDIO_EXES,
    VSCODE_EXES,
)
from .claude_code import CLAUDE_CODE_COMMANDS, CLAUDE_CODE_PROFILE
from .copilot import COPILOT_COMMANDS, COPILOT_PROFILE
from .cursor import CURSOR_COMMANDS, CURSOR_PROFILE
from .devin import DEVIN_COMMANDS, DEVIN_PROFILE
from .jetbrains import JETBRAINS_COMMANDS, JETBRAINS_PROFILE
from .visualstudio import VISUAL_STUDIO_COMMANDS, VISUAL_STUDIO_PROFILE
from .vscode import VSCODE_COMMANDS, VSCODE_PROFILE

ALL_COMMANDS: Tuple[Command, ...] = (
    COPILOT_COMMANDS + CURSOR_COMMANDS + CLAUDE_CODE_COMMANDS
    + DEVIN_COMMANDS + JETBRAINS_COMMANDS + VISUAL_STUDIO_COMMANDS
    + VSCODE_COMMANDS
)

COMMANDS_BY_ID: Dict[str, Command] = {cmd.id: cmd for cmd in ALL_COMMANDS}

# Order matters for exes shared by two profiles: the LAST profile wins the
# exe mapping.
#
# - Copilot lists code.exe but VS Code comes after it, so a focused code.exe
#   resolves to 'vscode' -- whose command set already merges the Copilot
#   actions in. Copilot stays addressable by profile id for a dedicated AI
#   scene.
# - Both terminal agents list TERMINAL_EXES, which cannot disambiguate which
#   agent a terminal hosts (session_marker/process-scan does that at action
#   time). Devin is listed before Claude Code so claude-code keeps its
#   existing claim on terminal exes.
ALL_PROFILES: Tuple[AppProfile, ...] = (
    CURSOR_PROFILE, COPILOT_PROFILE, DEVIN_PROFILE, CLAUDE_CODE_PROFILE,
    JETBRAINS_PROFILE, VISUAL_STUDIO_PROFILE, VSCODE_PROFILE,
)

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
    'VSCODE_EXES', 'CURSOR_EXES', 'JETBRAINS_EXES', 'TERMINAL_EXES',
    'VISUAL_STUDIO_EXES', 'DEVIN_EXES',
    'COPILOT_COMMANDS', 'CURSOR_COMMANDS', 'CLAUDE_CODE_COMMANDS',
    'DEVIN_COMMANDS', 'JETBRAINS_COMMANDS', 'VISUAL_STUDIO_COMMANDS',
    'VSCODE_COMMANDS',
    'ALL_COMMANDS', 'COMMANDS_BY_ID',
    'ALL_PROFILES', 'PROFILES_BY_ID', 'profile_for_exe',
]
