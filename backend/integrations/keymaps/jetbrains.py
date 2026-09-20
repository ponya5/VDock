"""JetBrains IDE keybindings — the defaults shared by IntelliJ, PyCharm,
WebStorm, Rider, CLion, GoLand, DataGrip, and RubyMine.

All commands are single keystrokes or single chords: JetBrains has many
two-stroke shortcuts (Ctrl+K Ctrl+V style) that a one-shot hotkey cannot
express, so they are deliberately absent.
"""
from typing import Tuple

from .base import AppProfile, Command, JETBRAINS_EXES

JETBRAINS_COMMANDS: Tuple[Command, ...] = (
    Command(
        id='jb_everywhere', label='Search Everywhere',
        description='Open Search Everywhere (double Shift).',
        keys=('shift',), repeat=2, icon='magnifying-glass',
        keywords=('jetbrains', 'search', 'everywhere', 'shift'),
        target_exes=JETBRAINS_EXES, category='general', priority=10,
    ),
    Command(
        id='jb_find_action', label='Find Action',
        description='Find any IDE action by name.',
        keys=('ctrl', 'shift', 'a'), icon='terminal',
        keywords=('jetbrains', 'action', 'command', 'palette'),
        target_exes=JETBRAINS_EXES, priority=10,
    ),
    Command(
        id='jb_goto_file', label='Go to File',
        description='Jump to a file by name.',
        keys=('ctrl', 'shift', 'n'), icon='file',
        keywords=('jetbrains', 'file', 'open', 'goto'),
        target_exes=JETBRAINS_EXES, priority=9,
    ),
    Command(
        id='jb_recent_files', label='Recent Files',
        description='Popup of recently opened files.',
        keys=('ctrl', 'e'), icon='clock-rotate-left',
        keywords=('jetbrains', 'recent', 'files', 'history'),
        target_exes=JETBRAINS_EXES,
    ),
    Command(
        id='jb_find_in_files', label='Find in Files',
        description='Search across the whole project.',
        keys=('ctrl', 'shift', 'f'), icon='magnifying-glass',
        keywords=('jetbrains', 'search', 'find', 'grep'),
        target_exes=JETBRAINS_EXES, priority=8,
    ),
    Command(
        id='jb_terminal', label='Terminal',
        description='Open the terminal tool window.',
        keys=('alt', 'f12'), icon='terminal',
        keywords=('jetbrains', 'terminal', 'console', 'shell'),
        target_exes=JETBRAINS_EXES, priority=9,
    ),
    Command(
        id='jb_project_view', label='Project View',
        description='Focus the project tool window.',
        keys=('alt', '1'), icon='folder-open',
        keywords=('jetbrains', 'project', 'files', 'tree'),
        target_exes=JETBRAINS_EXES,
    ),
    Command(
        id='jb_intention', label='Intention Actions',
        description='Show context actions / quick fixes (Alt+Enter).',
        keys=('alt', 'enter'), icon='wand-magic-sparkles',
        keywords=('jetbrains', 'intention', 'quickfix', 'actions', 'alt-enter'),
        target_exes=JETBRAINS_EXES, priority=9,
    ),
    Command(
        id='jb_rename', label='Rename Refactor',
        description='Rename the symbol under the cursor (Shift+F6).',
        keys=('shift', 'f6'), icon='pen',
        keywords=('jetbrains', 'rename', 'refactor', 'symbol'),
        target_exes=JETBRAINS_EXES,
    ),
    Command(
        id='jb_reformat', label='Reformat Code',
        description='Reformat the current file or selection.',
        keys=('ctrl', 'alt', 'l'), icon='align-left',
        keywords=('jetbrains', 'format', 'reformat', 'style'),
        target_exes=JETBRAINS_EXES,
    ),
    Command(
        id='jb_goto_declaration', label='Go to Declaration',
        description='Jump to the symbol declaration.',
        keys=('ctrl', 'b'), icon='arrow-right',
        keywords=('jetbrains', 'declaration', 'goto', 'symbol'),
        target_exes=JETBRAINS_EXES,
    ),
    Command(
        id='jb_settings', label='IDE Settings',
        description='Open the Settings dialog.',
        keys=('ctrl', 'alt', 's'), icon='gear',
        keywords=('jetbrains', 'settings', 'preferences'),
        target_exes=JETBRAINS_EXES,
    ),
    # Run/debug -- the F-row keeps everything one keystroke.
    Command(
        id='jb_run', label='Run',
        description='Run the active configuration (Shift+F10).',
        keys=('shift', 'f10'), icon='play',
        keywords=('jetbrains', 'run', 'execute', 'f10'),
        target_exes=JETBRAINS_EXES, category='debug', priority=9,
    ),
    Command(
        id='jb_debug', label='Debug',
        description='Debug the active configuration (Shift+F9).',
        keys=('shift', 'f9'), icon='bug',
        keywords=('jetbrains', 'debug', 'breakpoint', 'f9'),
        target_exes=JETBRAINS_EXES, category='debug', priority=9,
    ),
    Command(
        id='jb_stop', label='Stop',
        description='Stop the running process (Ctrl+F2).',
        keys=('ctrl', 'f2'), icon='stop',
        keywords=('jetbrains', 'stop', 'kill', 'process'),
        target_exes=JETBRAINS_EXES, category='debug',
    ),
    Command(
        id='jb_breakpoint', label='Toggle Breakpoint',
        description='Toggle a breakpoint on the current line (Ctrl+F8).',
        keys=('ctrl', 'f8'), icon='circle',
        keywords=('jetbrains', 'debug', 'breakpoint', 'f8'),
        target_exes=JETBRAINS_EXES, category='debug',
    ),
    Command(
        id='jb_step_over', label='Step Over',
        description='Step over the next call (F8).',
        keys=('f8',), icon='forward-step',
        keywords=('jetbrains', 'debug', 'step', 'over', 'f8'),
        target_exes=JETBRAINS_EXES, category='debug',
    ),
    Command(
        id='jb_step_into', label='Step Into',
        description='Step into the next call (F7).',
        keys=('f7',), icon='arrow-down',
        keywords=('jetbrains', 'debug', 'step', 'into', 'f7'),
        target_exes=JETBRAINS_EXES, category='debug',
    ),
    Command(
        id='jb_step_out', label='Step Out',
        description='Step out of the current call (Shift+F8).',
        keys=('shift', 'f8'), icon='arrow-up',
        keywords=('jetbrains', 'debug', 'step', 'out', 'f8'),
        target_exes=JETBRAINS_EXES, category='debug',
    ),
    Command(
        id='jb_comment', label='Comment Line',
        description='Comment or uncomment the current line.',
        keys=('ctrl', '/'), icon='comment',
        keywords=('jetbrains', 'comment', 'uncomment', 'line'),
        target_exes=JETBRAINS_EXES,
    ),
)

JETBRAINS_PROFILE = AppProfile(
    id='jetbrains', label='JetBrains IDE', exes=JETBRAINS_EXES,
    commands=JETBRAINS_COMMANDS, kind='editor',
    default_layout=(
        ('jb_everywhere', 'jb_find_action', 'jb_goto_file', 'jb_terminal'),
        ('jb_run', 'jb_debug', 'jb_intention', 'jb_find_in_files'),
    ),
)
