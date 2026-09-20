"""Visual Studio (devenv.exe) keybindings — default Windows scheme.

Only single-chord commands are listed: VS leans heavily on two-stroke chords
(Ctrl+K Ctrl+D and friends), which a one-shot hotkey cannot express.
"""
from typing import Tuple

from .base import AppProfile, Command, VISUAL_STUDIO_EXES

VISUAL_STUDIO_COMMANDS: Tuple[Command, ...] = (
    Command(
        id='vs_go_to_all', label='Go to All',
        description='Jump to any file, type, or member (Ctrl+,).',
        keys=('ctrl', ','), icon='magnifying-glass',
        keywords=('visualstudio', 'goto', 'search', 'navigate'),
        target_exes=VISUAL_STUDIO_EXES, category='general', priority=10,
    ),
    Command(
        id='vs_search', label='Feature Search',
        description='Search IDE features and commands (Ctrl+Q).',
        keys=('ctrl', 'q'), icon='terminal',
        keywords=('visualstudio', 'search', 'quick', 'launch'),
        target_exes=VISUAL_STUDIO_EXES, priority=10,
    ),
    Command(
        id='vs_solution_explorer', label='Solution Explorer',
        description='Focus the solution explorer.',
        keys=('ctrl', 'alt', 'l'), icon='folder-open',
        keywords=('visualstudio', 'solution', 'explorer', 'files'),
        target_exes=VISUAL_STUDIO_EXES,
    ),
    Command(
        id='vs_find_in_files', label='Find in Files',
        description='Search across the whole solution.',
        keys=('ctrl', 'shift', 'f'), icon='magnifying-glass',
        keywords=('visualstudio', 'search', 'find', 'grep'),
        target_exes=VISUAL_STUDIO_EXES, priority=8,
    ),
    Command(
        id='vs_go_to_line', label='Go to Line',
        description='Jump to a line number (Ctrl+G).',
        keys=('ctrl', 'g'), icon='arrow-right',
        keywords=('visualstudio', 'goto', 'line', 'number'),
        target_exes=VISUAL_STUDIO_EXES,
    ),
    Command(
        id='vs_definition', label='Go to Definition',
        description='Jump to the symbol definition (F12).',
        keys=('f12',), icon='arrow-right',
        keywords=('visualstudio', 'definition', 'goto', 'symbol'),
        target_exes=VISUAL_STUDIO_EXES,
    ),
    Command(
        id='vs_references', label='Find References',
        description='Find all references to the symbol (Shift+F12).',
        keys=('shift', 'f12'), icon='list',
        keywords=('visualstudio', 'references', 'usages'),
        target_exes=VISUAL_STUDIO_EXES,
    ),
    Command(
        id='vs_navigate_back', label='Navigate Backward',
        description='Go back to the previous location (Ctrl+-).',
        keys=('ctrl', '-'), icon='arrow-left',
        keywords=('visualstudio', 'navigate', 'back', 'history'),
        target_exes=VISUAL_STUDIO_EXES,
    ),
    Command(
        id='vs_navigate_forward', label='Navigate Forward',
        description='Go forward after navigating back (Ctrl+Shift+-).',
        keys=('ctrl', 'shift', '-'), icon='arrow-right',
        keywords=('visualstudio', 'navigate', 'forward', 'history'),
        target_exes=VISUAL_STUDIO_EXES,
    ),
    Command(
        id='vs_build', label='Build Solution',
        description='Build the whole solution (Ctrl+Shift+B).',
        keys=('ctrl', 'shift', 'b'), icon='hammer',
        keywords=('visualstudio', 'build', 'compile', 'solution'),
        target_exes=VISUAL_STUDIO_EXES, category='build', priority=9,
    ),
    Command(
        id='vs_output', label='Output Window',
        description='Show the Output window (Ctrl+Alt+O).',
        keys=('ctrl', 'alt', 'o'), icon='terminal',
        keywords=('visualstudio', 'output', 'build', 'log'),
        target_exes=VISUAL_STUDIO_EXES, category='build',
    ),
    # Debugging.
    Command(
        id='vs_debug_start', label='Start Debugging',
        description='Start or continue debugging (F5).',
        keys=('f5',), icon='play',
        keywords=('visualstudio', 'debug', 'run', 'continue', 'f5'),
        target_exes=VISUAL_STUDIO_EXES, category='debug', priority=9,
    ),
    Command(
        id='vs_debug_no_debug', label='Start Without Debugging',
        description='Run without attaching the debugger (Ctrl+F5).',
        keys=('ctrl', 'f5'), icon='forward',
        keywords=('visualstudio', 'run', 'no', 'debug', 'f5'),
        target_exes=VISUAL_STUDIO_EXES, category='debug',
    ),
    Command(
        id='vs_debug_stop', label='Stop Debugging',
        description='Stop the debug session (Shift+F5).',
        keys=('shift', 'f5'), icon='stop',
        keywords=('visualstudio', 'debug', 'stop', 'f5'),
        target_exes=VISUAL_STUDIO_EXES, category='debug',
    ),
    Command(
        id='vs_breakpoint', label='Toggle Breakpoint',
        description='Toggle a breakpoint on the current line (F9).',
        keys=('f9',), icon='circle',
        keywords=('visualstudio', 'debug', 'breakpoint', 'f9'),
        target_exes=VISUAL_STUDIO_EXES, category='debug',
    ),
    Command(
        id='vs_step_over', label='Step Over',
        description='Step over the next call (F10).',
        keys=('f10',), icon='forward-step',
        keywords=('visualstudio', 'debug', 'step', 'over', 'f10'),
        target_exes=VISUAL_STUDIO_EXES, category='debug',
    ),
    Command(
        id='vs_step_into', label='Step Into',
        description='Step into the next call (F11).',
        keys=('f11',), icon='arrow-down',
        keywords=('visualstudio', 'debug', 'step', 'into', 'f11'),
        target_exes=VISUAL_STUDIO_EXES, category='debug',
    ),
    Command(
        id='vs_step_out', label='Step Out',
        description='Step out of the current call (Shift+F11).',
        keys=('shift', 'f11'), icon='arrow-up',
        keywords=('visualstudio', 'debug', 'step', 'out', 'f11'),
        target_exes=VISUAL_STUDIO_EXES, category='debug',
    ),
    Command(
        id='vs_immediate', label='Immediate Window',
        description='Focus the Immediate window (Ctrl+Alt+I).',
        keys=('ctrl', 'alt', 'i'), icon='terminal',
        keywords=('visualstudio', 'immediate', 'debug', 'console'),
        target_exes=VISUAL_STUDIO_EXES, category='debug',
    ),
)

VISUAL_STUDIO_PROFILE = AppProfile(
    id='visualstudio', label='Visual Studio', exes=VISUAL_STUDIO_EXES,
    commands=VISUAL_STUDIO_COMMANDS, kind='editor',
    default_layout=(
        ('vs_go_to_all', 'vs_search', 'vs_build', 'vs_debug_start'),
        ('vs_find_in_files', 'vs_breakpoint', 'vs_step_over', 'vs_output'),
    ),
)
