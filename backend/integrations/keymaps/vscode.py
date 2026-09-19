"""VS Code keybindings — the editor itself, plus Copilot merged in.

`code.exe` resolves to this profile (it is listed after Copilot in
``ALL_PROFILES``), so the context scene for a focused VS Code window shows the
full command set: navigation, panels, debugging, and the Copilot AI actions.
The standalone ``copilot`` profile still exists for a dedicated AI scene.
"""
from typing import Tuple

from .base import AppProfile, Command, VSCODE_EXES
from .copilot import COPILOT_COMMANDS

VSCODE_COMMANDS: Tuple[Command, ...] = (
    Command(
        id='vsc_palette', label='Command Palette',
        description='Open the command palette.',
        keys=('ctrl', 'shift', 'p'), icon='terminal',
        keywords=('vscode', 'palette', 'commands'), target_exes=VSCODE_EXES,
        category='general', priority=10,
    ),
    Command(
        id='vsc_quick_open', label='Quick Open',
        description='Jump to a file by name.',
        keys=('ctrl', 'p'), icon='magnifying-glass',
        keywords=('vscode', 'file', 'open', 'goto'), target_exes=VSCODE_EXES,
        priority=10,
    ),
    Command(
        id='vsc_terminal', label='Toggle Terminal',
        description='Show or hide the integrated terminal.',
        keys=('ctrl', '`'), icon='terminal',
        keywords=('vscode', 'terminal', 'console', 'shell'),
        target_exes=VSCODE_EXES, priority=9,
    ),
    Command(
        id='vsc_sidebar', label='Toggle Sidebar',
        description='Show or hide the sidebar.',
        keys=('ctrl', 'b'), icon='bars',
        keywords=('vscode', 'sidebar', 'explorer'), target_exes=VSCODE_EXES,
    ),
    Command(
        id='vsc_explorer', label='Explorer View',
        description='Focus the file explorer.',
        keys=('ctrl', 'shift', 'e'), icon='folder-open',
        keywords=('vscode', 'explorer', 'files', 'tree'),
        target_exes=VSCODE_EXES,
    ),
    Command(
        id='vsc_find_in_files', label='Find in Files',
        description='Search across the whole project.',
        keys=('ctrl', 'shift', 'f'), icon='magnifying-glass',
        keywords=('vscode', 'search', 'find', 'grep'), target_exes=VSCODE_EXES,
        priority=8,
    ),
    Command(
        id='vsc_git_view', label='Source Control',
        description='Focus the source-control view.',
        keys=('ctrl', 'shift', 'g'), icon='code-branch',
        keywords=('vscode', 'git', 'source', 'commit'),
        target_exes=VSCODE_EXES,
    ),
    Command(
        id='vsc_debug_view', label='Run and Debug View',
        description='Focus the run-and-debug view.',
        keys=('ctrl', 'shift', 'd'), icon='bug',
        keywords=('vscode', 'debug', 'run', 'view'), target_exes=VSCODE_EXES,
    ),
    Command(
        id='vsc_extensions', label='Extensions View',
        description='Focus the extensions view.',
        keys=('ctrl', 'shift', 'x'), icon='puzzle-piece',
        keywords=('vscode', 'extensions', 'plugins'), target_exes=VSCODE_EXES,
    ),
    Command(
        id='vsc_problems', label='Problems Panel',
        description='Show errors and warnings.',
        keys=('ctrl', 'shift', 'm'), icon='triangle-exclamation',
        keywords=('vscode', 'problems', 'errors', 'warnings'),
        target_exes=VSCODE_EXES,
    ),
    Command(
        id='vsc_toggle_panel', label='Toggle Panel',
        description='Show or hide the bottom panel.',
        keys=('ctrl', 'j'), icon='table-cells',
        keywords=('vscode', 'panel', 'output', 'terminal'),
        target_exes=VSCODE_EXES,
    ),
    Command(
        id='vsc_quick_fix', label='Quick Fix',
        description='Show code actions for the current line.',
        keys=('ctrl', '.'), icon='screwdriver-wrench',
        keywords=('vscode', 'quickfix', 'code', 'actions', 'refactor'),
        target_exes=VSCODE_EXES, priority=8,
    ),
    Command(
        id='vsc_rename', label='Rename Symbol',
        description='Rename the symbol under the cursor.',
        keys=('f2',), icon='pen',
        keywords=('vscode', 'rename', 'refactor', 'symbol'),
        target_exes=VSCODE_EXES,
    ),
    Command(
        id='vsc_definition', label='Go to Definition',
        description='Jump to the symbol definition.',
        keys=('f12',), icon='arrow-right',
        keywords=('vscode', 'definition', 'goto', 'symbol'),
        target_exes=VSCODE_EXES,
    ),
    Command(
        id='vsc_references', label='Find References',
        description='List every reference to the symbol.',
        keys=('shift', 'f12'), icon='list',
        keywords=('vscode', 'references', 'usages'), target_exes=VSCODE_EXES,
    ),
    Command(
        id='vsc_save', label='Save',
        description='Save the current editor.',
        keys=('ctrl', 's'), icon='floppy-disk',
        keywords=('vscode', 'save', 'file'), target_exes=VSCODE_EXES,
    ),
    # Debugging -- single-key F-row commands, no chords needed.
    Command(
        id='vsc_debug_start', label='Start Debugging',
        description='Start or continue debugging (F5).',
        keys=('f5',), icon='play',
        keywords=('vscode', 'debug', 'run', 'continue', 'f5'),
        target_exes=VSCODE_EXES, category='debug', priority=9,
    ),
    Command(
        id='vsc_debug_stop', label='Stop Debugging',
        description='Stop the debug session (Shift+F5).',
        keys=('shift', 'f5'), icon='stop',
        keywords=('vscode', 'debug', 'stop', 'f5'),
        target_exes=VSCODE_EXES, category='debug',
    ),
    Command(
        id='vsc_breakpoint', label='Toggle Breakpoint',
        description='Toggle a breakpoint on the current line (F9).',
        keys=('f9',), icon='circle',
        keywords=('vscode', 'debug', 'breakpoint', 'f9'),
        target_exes=VSCODE_EXES, category='debug',
    ),
    Command(
        id='vsc_step_over', label='Step Over',
        description='Step over the next call (F10).',
        keys=('f10',), icon='forward-step',
        keywords=('vscode', 'debug', 'step', 'over', 'f10'),
        target_exes=VSCODE_EXES, category='debug',
    ),
    Command(
        id='vsc_step_into', label='Step Into',
        description='Step into the next call (F11).',
        keys=('f11',), icon='arrow-down',
        keywords=('vscode', 'debug', 'step', 'into', 'f11'),
        target_exes=VSCODE_EXES, category='debug',
    ),
    Command(
        id='vsc_step_out', label='Step Out',
        description='Step out of the current call (Shift+F11).',
        keys=('shift', 'f11'), icon='arrow-up',
        keywords=('vscode', 'debug', 'step', 'out', 'f11'),
        target_exes=VSCODE_EXES, category='debug',
    ),
    Command(
        id='vsc_settings', label='Open Settings',
        description='Open the settings UI.',
        keys=('ctrl', ','), icon='gear',
        keywords=('vscode', 'settings', 'preferences'), target_exes=VSCODE_EXES,
    ),
    Command(
        id='vsc_close_editor', label='Close Editor',
        description='Close the current editor tab.',
        keys=('ctrl', 'w'), icon='xmark',
        keywords=('vscode', 'close', 'tab', 'editor'), target_exes=VSCODE_EXES,
    ),
)

VSCODE_PROFILE = AppProfile(
    id='vscode', label='VS Code', exes=VSCODE_EXES,
    # Copilot commands ride along: a focused VS Code window should offer the
    # AI actions in the same scene instead of needing a profile switch.
    commands=VSCODE_COMMANDS + COPILOT_COMMANDS, kind='editor',
    default_layout=(
        ('vsc_palette', 'vsc_quick_open', 'vsc_terminal', 'copilot_chat'),
        ('vsc_find_in_files', 'vsc_debug_start', 'vsc_breakpoint', 'vsc_quick_fix'),
    ),
)
