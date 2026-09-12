"""Editor keybindings as data.

GitHub Copilot and Cursor have no external control surface -- no CLI, no local
API. The only way to drive them from a deck is to focus the editor and send the
keystrokes a human would press. That makes these bindings the most fragile part
of the integration: they change between versions, differ per platform, and users
remap them.

So they live here as data rather than being scattered through the packs. When a
shortcut changes, this file changes and nothing else does.

Every command is a list of macro steps, which ``MacroAction`` already knows how
to run (``hotkey``, ``text``, ``delay``, ``clipboard_*``). Note that macro
hotkey steps were silently broken until recently -- they passed HotkeyAction a
config key it did not accept -- so anything built on them depends on that fix.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Process names for the editors these keymaps target.
VSCODE_EXES = ('code.exe', 'codium.exe')
CURSOR_EXES = ('cursor.exe',)
JETBRAINS_EXES = ('idea64.exe', 'pycharm64.exe', 'webstorm64.exe')


@dataclass(frozen=True)
class Command:
    """One editor command, expressed as macro steps."""
    id: str
    label: str
    description: str
    keys: Tuple[str, ...]
    icon: str = 'keyboard'
    keywords: Tuple[str, ...] = ()
    #: Process names this command expects to be focused. Empty means any.
    target_exes: Tuple[str, ...] = ()
    #: Text typed after the keystroke, e.g. a chat slash command.
    types_text: Optional[str] = None
    #: Press Enter after typing.
    submit: bool = False

    def to_macro_steps(self, text_override: Optional[str] = None) -> List[Dict[str, Any]]:
        """Build the macro step list MacroAction executes."""
        steps: List[Dict[str, Any]] = [
            {'type': 'hotkey', 'keys': list(self.keys)},
        ]

        text = text_override if text_override is not None else self.types_text
        if text:
            # The editor needs a moment to focus its input before typing.
            steps.append({'type': 'delay', 'delay': 350})
            steps.append({'type': 'text', 'text': text})

        if self.submit and text:
            steps.append({'type': 'delay', 'delay': 120})
            steps.append({'type': 'hotkey', 'keys': ['enter']})

        return steps


# --- GitHub Copilot (VS Code) ------------------------------------------------

COPILOT_COMMANDS: Tuple[Command, ...] = (
    Command(
        id='copilot_chat', label='Copilot Chat',
        description='Open the Copilot Chat panel.',
        keys=('ctrl', 'alt', 'i'), icon='comments',
        keywords=('copilot', 'chat', 'ai'), target_exes=VSCODE_EXES,
    ),
    Command(
        id='copilot_inline', label='Copilot Inline Chat',
        description='Start an inline chat at the cursor.',
        keys=('ctrl', 'i'), icon='wand-magic-sparkles',
        keywords=('copilot', 'inline', 'edit'), target_exes=VSCODE_EXES,
    ),
    Command(
        id='copilot_edits', label='Copilot Edits',
        description='Open Copilot Edits for multi-file changes.',
        keys=('ctrl', 'shift', 'i'), icon='pen-to-square',
        keywords=('copilot', 'edits', 'multi-file'), target_exes=VSCODE_EXES,
    ),
    Command(
        id='copilot_accept', label='Accept Suggestion',
        description='Accept the inline suggestion.',
        keys=('tab',), icon='check',
        keywords=('copilot', 'accept', 'tab'), target_exes=VSCODE_EXES,
    ),
    Command(
        id='copilot_dismiss', label='Dismiss Suggestion',
        description='Dismiss the inline suggestion.',
        keys=('esc',), icon='xmark',
        keywords=('copilot', 'dismiss', 'reject'), target_exes=VSCODE_EXES,
    ),
    Command(
        id='copilot_next', label='Next Suggestion',
        description='Cycle to the next inline suggestion.',
        keys=('alt', ']'), icon='arrow-right',
        keywords=('copilot', 'next', 'cycle'), target_exes=VSCODE_EXES,
    ),
    Command(
        id='copilot_prev', label='Previous Suggestion',
        description='Cycle to the previous inline suggestion.',
        keys=('alt', '['), icon='arrow-left',
        keywords=('copilot', 'previous', 'cycle'), target_exes=VSCODE_EXES,
    ),
    Command(
        id='copilot_explain', label='Copilot: Explain',
        description='Ask Copilot Chat to explain the selection.',
        keys=('ctrl', 'alt', 'i'), icon='circle-question',
        keywords=('copilot', 'explain', 'understand'),
        target_exes=VSCODE_EXES, types_text='/explain', submit=True,
    ),
    Command(
        id='copilot_fix', label='Copilot: Fix',
        description='Ask Copilot Chat to fix the selection.',
        keys=('ctrl', 'alt', 'i'), icon='screwdriver-wrench',
        keywords=('copilot', 'fix', 'repair', 'bug'),
        target_exes=VSCODE_EXES, types_text='/fix', submit=True,
    ),
    Command(
        id='copilot_tests', label='Copilot: Generate Tests',
        description='Ask Copilot Chat to write tests for the selection.',
        keys=('ctrl', 'alt', 'i'), icon='vial',
        keywords=('copilot', 'tests', 'unit', 'coverage'),
        target_exes=VSCODE_EXES, types_text='/tests', submit=True,
    ),
    Command(
        id='copilot_doc', label='Copilot: Document',
        description='Ask Copilot Chat to document the selection.',
        keys=('ctrl', 'alt', 'i'), icon='file-lines',
        keywords=('copilot', 'docs', 'comment', 'docstring'),
        target_exes=VSCODE_EXES, types_text='/doc', submit=True,
    ),
)


# --- Cursor ------------------------------------------------------------------

CURSOR_COMMANDS: Tuple[Command, ...] = (
    Command(
        id='cursor_chat', label='Cursor Chat',
        description='Open the Cursor AI chat pane.',
        keys=('ctrl', 'l'), icon='comments',
        keywords=('cursor', 'chat', 'ai', 'ask'), target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_composer', label='Cursor Composer',
        description='Open Composer for multi-file edits.',
        keys=('ctrl', 'i'), icon='wand-magic-sparkles',
        keywords=('cursor', 'composer', 'agent', 'multi-file'),
        target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_composer_full', label='Composer (Full Screen)',
        description='Open Composer in full screen.',
        keys=('ctrl', 'shift', 'i'), icon='expand',
        keywords=('cursor', 'composer', 'fullscreen'), target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_inline_edit', label='Cursor Inline Edit',
        description='Edit the selection in place with AI.',
        keys=('ctrl', 'k'), icon='pen',
        keywords=('cursor', 'edit', 'inline', 'k'), target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_new_chat', label='New Cursor Chat',
        description='Start a fresh chat session.',
        keys=('ctrl', 'shift', 'l'), icon='plus',
        keywords=('cursor', 'new', 'chat', 'reset'), target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_accept', label='Accept Diff',
        description='Accept the suggested change.',
        keys=('ctrl', 'enter'), icon='check',
        keywords=('cursor', 'accept', 'apply', 'diff'), target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_reject', label='Reject Diff',
        description='Reject the suggested change.',
        keys=('ctrl', 'backspace'), icon='xmark',
        keywords=('cursor', 'reject', 'discard', 'diff'),
        target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_command_palette', label='Command Palette',
        description='Open the command palette.',
        keys=('ctrl', 'shift', 'p'), icon='terminal',
        keywords=('cursor', 'palette', 'commands'), target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_quick_open', label='Quick Open',
        description='Jump to a file by name.',
        keys=('ctrl', 'p'), icon='magnifying-glass',
        keywords=('cursor', 'file', 'open', 'goto'), target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_toggle_terminal', label='Toggle Terminal',
        description='Show or hide the integrated terminal.',
        keys=('ctrl', '`'), icon='terminal',
        keywords=('cursor', 'terminal', 'console', 'shell'),
        target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_toggle_sidebar', label='Toggle Sidebar',
        description='Show or hide the sidebar.',
        keys=('ctrl', 'b'), icon='bars',
        keywords=('cursor', 'sidebar', 'explorer'), target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_find_in_files', label='Find in Files',
        description='Search across the whole project.',
        keys=('ctrl', 'shift', 'f'), icon='magnifying-glass',
        keywords=('cursor', 'search', 'find', 'grep'), target_exes=CURSOR_EXES,
    ),
)


ALL_COMMANDS: Tuple[Command, ...] = COPILOT_COMMANDS + CURSOR_COMMANDS

COMMANDS_BY_ID: Dict[str, Command] = {cmd.id: cmd for cmd in ALL_COMMANDS}
