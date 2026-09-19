"""App keymaps, one module per application."""
from typing import Dict, Tuple

from .base import (
    Command,
    RISK_DESTRUCTIVE,
    RISK_INPUT,
    RISK_SAFE,
    CURSOR_EXES,
    JETBRAINS_EXES,
    VSCODE_EXES,
)
from .copilot import COPILOT_COMMANDS
from .cursor import CURSOR_COMMANDS

ALL_COMMANDS: Tuple[Command, ...] = COPILOT_COMMANDS + CURSOR_COMMANDS

COMMANDS_BY_ID: Dict[str, Command] = {cmd.id: cmd for cmd in ALL_COMMANDS}

__all__ = [
    'Command', 'RISK_SAFE', 'RISK_INPUT', 'RISK_DESTRUCTIVE',
    'VSCODE_EXES', 'CURSOR_EXES', 'JETBRAINS_EXES',
    'COPILOT_COMMANDS', 'CURSOR_COMMANDS', 'ALL_COMMANDS', 'COMMANDS_BY_ID',
]
