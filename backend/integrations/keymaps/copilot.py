"""GitHub Copilot (VS Code) keybindings."""
from typing import Tuple

from .base import AppProfile, Command, VSCODE_EXES

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

COPILOT_PROFILE = AppProfile(
    id='copilot', label='GitHub Copilot', exes=VSCODE_EXES,
    commands=COPILOT_COMMANDS, kind='editor',
    default_layout=(
        ('copilot_chat', 'copilot_inline', 'copilot_accept', 'copilot_dismiss'),
        ('copilot_edits', 'copilot_explain', 'copilot_fix', 'copilot_tests'),
    ),
)
