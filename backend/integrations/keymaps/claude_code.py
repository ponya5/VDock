"""Claude Code keybindings — controls for a live terminal session.

Claude Code is a terminal TUI, so "commands" are keystrokes or typed slash
commands into whatever terminal hosts the session. Every command targets
TERMINAL_EXES and carries ``window_title_hint='claude'`` so window picking
prefers the tab actually running the session.

Slash commands are typed input: ``requires_session`` + ``session_marker``
gate them behind a detected claude process (the interim interlock until the
Phase-3 hook registry lands — see ``integrations/sessions.py``).
"""
from typing import Tuple

from .base import (
    AppProfile,
    Command,
    RISK_DESTRUCTIVE,
    RISK_INPUT,
    RISK_SAFE,
    TERMINAL_EXES,
)

_CLAUDE = {
    'target_exes': TERMINAL_EXES,
    'window_title_hint': 'claude',
    # Also set on the safe commands: with requires_session off it only drives
    # targeting -- the session's host window is resolved through the process
    # tree, so these work inside Devin/Cursor/any terminal, not just exes in
    # TERMINAL_EXES.
    'session_marker': 'claude',
    'category': 'general',
}

CLAUDE_CODE_COMMANDS: Tuple[Command, ...] = (
    Command(
        id='cc_interrupt', label='Interrupt Claude',
        description='Stop the current response (Esc).',
        keys=('escape',), icon='hand',
        keywords=('claude', 'stop', 'interrupt', 'cancel', 'esc'),
        risk=RISK_SAFE, **_CLAUDE,
    ),
    Command(
        id='cc_mode', label='Cycle Mode',
        description='Cycle permission mode: normal / auto-accept / plan '
                    '(Shift+Tab).',
        keys=('shift', 'tab'), icon='arrows-rotate',
        keywords=('claude', 'mode', 'plan', 'auto-accept', 'permissions'),
        risk=RISK_SAFE, **_CLAUDE,
    ),
    Command(
        id='cc_prompt', label='Send Prompt',
        description='Type a prompt into the live session and send it. '
                    'Defaults to "continue".',
        keys=(), icon='paper-plane', types_text='continue', submit=True,
        keywords=('claude', 'prompt', 'continue', 'send', 'ask', 'type'),
        risk=RISK_INPUT, requires_session=True,
        priority=10, **_CLAUDE,
    ),
    Command(
        id='cc_clear', label='New Session',
        description='Start a fresh session — clears the context (/clear).',
        keys=(), icon='plus', types_text='/clear', submit=True,
        keywords=('claude', 'new', 'clear', 'reset', 'session'),
        risk=RISK_INPUT, requires_session=True,
        priority=10, **_CLAUDE,
    ),
    Command(
        id='cc_resume', label='Resume Session',
        description='Pick up a previous session (/resume).',
        keys=(), icon='rotate-right', types_text='/resume', submit=True,
        keywords=('claude', 'resume', 'continue', 'session'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),
    Command(
        id='cc_compact', label='Compact Context',
        description='Compact the conversation to free context (/compact).',
        keys=(), icon='compress', types_text='/compact', submit=True,
        keywords=('claude', 'compact', 'context', 'summarize'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),
    Command(
        id='cc_model', label='Model Picker',
        description='Open the model picker (/model).',
        keys=(), icon='brain', types_text='/model', submit=True,
        keywords=('claude', 'model', 'opus', 'sonnet', 'haiku'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),
    Command(
        id='cc_add_file', label='Add File',
        description='Open the file-mention picker (@) — the session’s way of '
                    'attaching a file.',
        keys=(), icon='paperclip', types_text='@',
        keywords=('claude', 'file', 'attach', 'mention', 'upload'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),
    Command(
        id='cc_help', label='Claude Help',
        description='Show available commands (/help).',
        keys=(), icon='circle-question', types_text='/help', submit=True,
        keywords=('claude', 'help', 'commands'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),

    # --- Permission prompts -------------------------------------------------
    # confirm:yes/no -- the deck's killer feature: answer a permission dialog
    # without touching the keyboard.
    Command(
        id='cc_approve', label='Approve',
        description='Answer "yes" to a permission prompt (y).',
        keys=(), icon='check', types_text='y',
        keywords=('claude', 'approve', 'yes', 'allow', 'permission',
                  'confirm'),
        risk=RISK_INPUT, requires_session=True,
        priority=10, **_CLAUDE,
    ),
    Command(
        id='cc_deny', label='Deny',
        description='Answer "no" to a permission prompt (n).',
        keys=(), icon='xmark', types_text='n',
        keywords=('claude', 'deny', 'no', 'reject', 'permission',
                  'decline'),
        risk=RISK_INPUT, requires_session=True,
        priority=10, **_CLAUDE,
    ),
    Command(
        id='cc_accept', label='Accept Option',
        description='Accept the highlighted option / submit (Enter).',
        keys=('enter',), icon='circle-check',
        keywords=('claude', 'enter', 'accept', 'select', 'submit'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),

    # --- View toggles (safe: harmless if they land elsewhere) ---------------
    Command(
        id='cc_todos', label='To-do List',
        description='Toggle Claude’s to-do checklist (Ctrl+T).',
        keys=('ctrl', 't'), icon='list-check',
        keywords=('claude', 'todo', 'tasks', 'checklist', 'toggle'),
        risk=RISK_SAFE, **_CLAUDE,
    ),
    Command(
        id='cc_transcript', label='Transcript',
        description='Toggle the verbose transcript view (Ctrl+O).',
        keys=('ctrl', 'o'), icon='scroll',
        keywords=('claude', 'transcript', 'verbose', 'log'),
        risk=RISK_SAFE, **_CLAUDE,
    ),
    Command(
        id='cc_history', label='History Search',
        description='Search prompt history (Ctrl+R).',
        keys=('ctrl', 'r'), icon='clock-rotate-left',
        keywords=('claude', 'history', 'search', 'previous', 'prompt'),
        risk=RISK_SAFE, **_CLAUDE,
    ),
    Command(
        id='cc_redraw', label='Redraw Screen',
        description='Force a screen redraw / clear screen (Ctrl+L).',
        keys=('ctrl', 'l'), icon='broom',
        keywords=('claude', 'redraw', 'refresh', 'clear screen'),
        risk=RISK_SAFE, **_CLAUDE,
    ),
    Command(
        id='cc_rewind', label='Rewind',
        description='Open the rewind / message-selector dialog (Esc twice).',
        keys=('escape',), icon='backward', repeat=2,
        keywords=('claude', 'rewind', 'checkpoint', 'undo', 'back'),
        risk=RISK_SAFE, **_CLAUDE,
    ),
    Command(
        id='cc_thinking', label='Thinking Mode',
        description='Toggle extended thinking (Alt+T).',
        keys=('alt', 't'), icon='lightbulb',
        keywords=('claude', 'thinking', 'extended', 'reasoning'),
        risk=RISK_SAFE, **_CLAUDE,
    ),
    Command(
        id='cc_fast', label='Fast Mode',
        description='Toggle fast mode (Alt+O).',
        keys=('alt', 'o'), icon='bolt',
        keywords=('claude', 'fast', 'speed', 'mode'),
        risk=RISK_SAFE, **_CLAUDE,
    ),

    # --- Navigation ----------------------------------------------------------
    Command(
        id='cc_scroll_up', label='Scroll Up',
        description='Scroll up half a viewport (PageUp).',
        keys=('pageup',), icon='chevron-up',
        keywords=('claude', 'scroll', 'up', 'page'),
        risk=RISK_SAFE, **_CLAUDE,
    ),
    Command(
        id='cc_scroll_down', label='Scroll Down',
        description='Scroll down half a viewport (PageDown).',
        keys=('pagedown',), icon='chevron-down',
        keywords=('claude', 'scroll', 'down', 'page'),
        risk=RISK_SAFE, **_CLAUDE,
    ),
    Command(
        id='cc_nav_up', label='Option Up',
        description='Move up in dialogs and pickers (Up).',
        keys=('up',), icon='caret-up',
        keywords=('claude', 'arrow', 'up', 'navigate', 'option'),
        risk=RISK_SAFE, **_CLAUDE,
    ),
    Command(
        id='cc_nav_down', label='Option Down',
        description='Move down in dialogs and pickers (Down).',
        keys=('down',), icon='caret-down',
        keywords=('claude', 'arrow', 'down', 'navigate', 'option'),
        risk=RISK_SAFE, **_CLAUDE,
    ),

    # --- Draft/input controls (typed or state-changing: session-gated) ------
    Command(
        id='cc_cancel', label='Cancel Operation',
        description='Cancel the current operation (Ctrl+C). In a shell this '
                    'is SIGINT, so it stays session-gated.',
        keys=('ctrl', 'c'), icon='ban',
        keywords=('claude', 'cancel', 'interrupt', 'ctrl-c', 'abort'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),
    Command(
        id='cc_newline', label='Newline',
        description='Insert a newline in the draft without submitting '
                    '(Ctrl+J).',
        keys=('ctrl', 'j'), icon='turn-down',
        keywords=('claude', 'newline', 'line', 'multiline'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),
    Command(
        id='cc_stash', label='Stash Draft',
        description='Stash the current prompt draft (Ctrl+S).',
        keys=('ctrl', 's'), icon='box-archive',
        keywords=('claude', 'stash', 'draft', 'save'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),
    Command(
        id='cc_undo', label='Undo',
        description='Undo the last action (Ctrl+_).',
        keys=('ctrl', 'shift', '-'), icon='rotate-left',
        keywords=('claude', 'undo', 'revert'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),
    Command(
        id='cc_editor', label='External Editor',
        description='Open the draft in the external editor (Ctrl+G).',
        keys=('ctrl', 'g'), icon='pen-to-square',
        keywords=('claude', 'editor', 'external', 'compose'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),
    Command(
        id='cc_paste_image', label='Paste Image',
        description='Paste an image from the clipboard (Alt+V on Windows).',
        keys=('alt', 'v'), icon='image',
        keywords=('claude', 'paste', 'image', 'clipboard', 'attach'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),
    Command(
        id='cc_background', label='Background Task',
        description='Move the running task to the background (Ctrl+B).',
        keys=('ctrl', 'b'), icon='layer-group',
        keywords=('claude', 'background', 'task', 'detach'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),
    Command(
        id='cc_queue', label='Queue Message',
        description='Submit the draft to run after the current turn '
                    '(Ctrl+X then Enter, v2.1.247+).',
        keys=('ctrl', 'x'), after_keys=(('enter',),),
        icon='hourglass-half',
        keywords=('claude', 'queue', 'submit', 'wait', 'turn'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),

    # --- Prompt prefixes & slash commands -----------------------------------
    Command(
        id='cc_bash', label='Bash Mode',
        description='Type the bash-mode prefix (!) — run a shell command '
                    'directly.',
        keys=(), icon='terminal', types_text='!',
        keywords=('claude', 'bash', 'shell', 'command', 'bang'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),
    Command(
        id='cc_memory', label='Add Memory',
        description='Type the memory prefix (#) — save a note to memory.',
        keys=(), icon='hashtag', types_text='#',
        keywords=('claude', 'memory', 'remember', 'note'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),
    Command(
        id='cc_tasks', label='Tasks View',
        description='Open the background-tasks view (/tasks).',
        keys=(), icon='list', types_text='/tasks', submit=True,
        keywords=('claude', 'tasks', 'background', 'jobs'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),
    Command(
        id='cc_diff', label='Diff Panel',
        description='Open the diff panel (/diff, v2.1.260+ fullscreen).',
        keys=(), icon='code-compare', types_text='/diff', submit=True,
        keywords=('claude', 'diff', 'changes', 'review'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),
    Command(
        id='cc_agents', label='Agent View',
        description='Open the agent view (/agents, v2.1.257+).',
        keys=(), icon='users', types_text='/agents', submit=True,
        keywords=('claude', 'agents', 'sessions', 'view'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),
    Command(
        id='cc_effort', label='Effort Slider',
        description='Open the effort-level slider (/effort).',
        keys=(), icon='gauge', types_text='/effort', submit=True,
        keywords=('claude', 'effort', 'level', 'reasoning'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),
    Command(
        id='cc_permissions', label='Permissions',
        description='Open permission settings (/permissions).',
        keys=(), icon='shield', types_text='/permissions', submit=True,
        keywords=('claude', 'permissions', 'allow', 'rules', 'settings'),
        risk=RISK_INPUT, requires_session=True,
        **_CLAUDE,
    ),

    # --- Destructive ---------------------------------------------------------
    Command(
        id='cc_kill_agents', label='Kill Agents',
        description='Stop all running background subagents (Ctrl+X then '
                    'Ctrl+K).',
        keys=('ctrl', 'x'), after_keys=(('ctrl', 'k'),),
        icon='circle-xmark',
        keywords=('claude', 'kill', 'agents', 'subagents', 'stop all'),
        risk=RISK_DESTRUCTIVE, requires_session=True, **_CLAUDE,
    ),
    Command(
        id='cc_exit', label='Quit Claude Code',
        description='Exit the session (Ctrl+D twice).',
        keys=('ctrl', 'd'), icon='power-off', repeat=2,
        keywords=('claude', 'exit', 'quit', 'close'),
        risk=RISK_DESTRUCTIVE, requires_session=True, **_CLAUDE,
    ),
)

CLAUDE_CODE_PROFILE = AppProfile(
    id='claude-code', label='Claude Code', exes=TERMINAL_EXES,
    commands=CLAUDE_CODE_COMMANDS, kind='terminal_agent',
    # Hooks land in Phase 3; until then sessions are detected by process scan.
    status_source=None,
    # claude_pack's plugin actions — a scene built of these still votes for
    # this profile even though none of its buttons carry a cc_* command id.
    action_types=(
        'claude_prompt', 'claude_slash', 'claude_continue',
        'claude_api_prompt', 'claude_open',
    ),
    default_layout=(
        ('cc_prompt', 'cc_interrupt', 'cc_approve', 'cc_deny'),
        ('cc_clear', 'cc_mode', 'cc_rewind', 'cc_todos'),
        ('cc_resume', 'cc_compact', 'cc_add_file', 'cc_model'),
    ),
)
