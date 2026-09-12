"""Generate the shipped developer scene templates.

These decks are data, but writing six large JSON files by hand invites the exact
drift the action catalog exists to prevent -- a typo'd action type produces a
button that fails on press. Generating them here means every action id is
checked against the catalog and the loaded packs before the file is written.

Run from backend/:

    python scripts/generate_dev_templates.py

It rewrites backend/data/templates/dev-*.json.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

BACKEND = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = BACKEND / 'data' / 'templates'

# Brand colours, reused so the decks look like one family.
CLAUDE = '#D97757'
CURSOR = '#6b7280'
GITHUB = '#24292f'
GIT = '#f05033'
DEBUG = '#7c3aed'
FOCUS = '#0ea5e9'
NEUTRAL = '#334155'
GREEN = '#16a34a'
RED = '#dc2626'


def button(
    row: int, col: int, label: str, icon: str, action_type: str,
    config: Optional[Dict[str, Any]] = None, *,
    secondary: str = '', colour: str = NEUTRAL, tooltip: str = '',
    cols: int = 1,
) -> Dict[str, Any]:
    """One deck button."""
    data: Dict[str, Any] = {
        'id': f'btn-{action_type}-{row}-{col}',
        'label': label,
        'icon': ['fas', icon],
        'icon_type': 'fontawesome',
        'position': {'row': row, 'col': col},
        'size': {'rows': 1, 'cols': cols},
        'shape': 'rounded',
        'style': {'backgroundColor': colour, 'textColor': '#ffffff'},
        'enabled': True,
        'action': {'type': action_type, 'config': config or {}},
    }
    if secondary:
        data['secondary_label'] = secondary
    if tooltip:
        data['tooltip'] = tooltip
    return data


def template(
    template_id: str, name: str, description: str, icon: str, colour: str,
    buttons: List[Dict[str, Any]], *,
    rows: int = 4, cols: int = 5, triggered_by: Optional[str] = None,
) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        'id': template_id,
        'name': name,
        'description': description,
        'icon': icon,
        'color': colour,
        'category': 'development',
        'version': '1.0',
        'author': 'VDock Team',
        'pages': [{
            'id': f'page-{template_id}',
            'name': name,
            'grid_config': {'rows': rows, 'cols': cols},
            'buttons': buttons,
        }],
    }
    if triggered_by:
        data['triggeredByApp'] = triggered_by
    return data


def claude_code_deck() -> Dict[str, Any]:
    return template(
        'dev-claude-code', 'Claude Code', 'Drive Claude Code without leaving '
        'the keyboard: prompts, reviews, commits and sessions.',
        'fa-robot', CLAUDE, triggered_by='WindowsTerminal.exe',
        buttons=[
            button(0, 0, 'Open Claude', 'window-maximize', 'claude_continue',
                   {'resume': True}, colour=CLAUDE,
                   tooltip='Resume the last Claude Code session'),
            button(0, 1, 'Review', 'magnifying-glass', 'claude_slash',
                   {'command': '/code-review', 'output': 'notify'},
                   secondary='/code-review', colour=CLAUDE),
            button(0, 2, 'Commit', 'code-commit', 'claude_slash',
                   {'command': '/commit', 'output': 'notify'},
                   secondary='/commit', colour=CLAUDE),
            button(0, 3, 'Explain', 'circle-question', 'claude_prompt',
                   {'prompt': 'Explain what this code does:\n\n{clipboard}',
                    'output': 'both'}, colour=CLAUDE,
                   tooltip='Explains whatever is on the clipboard'),
            button(0, 4, 'Write Tests', 'vial', 'claude_prompt',
                   {'prompt': 'Write tests for this code:\n\n{clipboard}',
                    'output': 'both'}, colour=CLAUDE),

            button(1, 0, 'Ask', 'comment-dots', 'claude_prompt',
                   {'prompt': 'In {project} on branch {branch}: ',
                    'output': 'both'}, colour=CLAUDE),
            button(1, 1, 'Continue', 'forward', 'claude_prompt',
                   {'prompt': 'continue', 'continue_session': True},
                   colour=CLAUDE),
            button(1, 2, 'Fix Tests', 'screwdriver-wrench', 'claude_prompt',
                   {'prompt': 'The tests are failing. Find and fix the cause.',
                    'output': 'notify'}, colour=CLAUDE),
            button(1, 3, 'Summarise Diff', 'file-lines', 'claude_prompt',
                   {'prompt': 'Summarise the staged changes in {repo}.',
                    'output': 'both'}, colour=CLAUDE),
            button(1, 4, 'claude.ai', 'up-right-from-square', 'claude_open',
                   {'target': 'new_chat'}, colour=CLAUDE),

            button(2, 0, 'Terminal', 'terminal', 'cross_platform',
                   {'action': 'open_app', 'app': 'wt'}),
            button(2, 1, 'Copy', 'copy', 'macro',
                   {'steps': [{'type': 'clipboard_copy'}]}),
            button(2, 2, 'Paste', 'paste', 'macro',
                   {'steps': [{'type': 'clipboard_paste'}]}),
            button(2, 3, 'CPU', 'microchip', 'metric_cpu_usage', {}),
            button(2, 4, 'Memory', 'memory', 'metric_memory', {}),

            button(3, 0, 'Prev Page', 'chevron-left', 'previous_page', {}),
            button(3, 1, 'Next Page', 'chevron-right', 'next_page', {}),
            button(3, 4, 'Clock', 'clock', 'time_world_clock', {}),
        ],
    )


def cursor_deck() -> Dict[str, Any]:
    return template(
        'dev-cursor-ai', 'Cursor AI', 'Composer, chat, inline edit and diff '
        'controls for Cursor.', 'fa-wand-magic-sparkles', CURSOR,
        triggered_by='Cursor.exe',
        buttons=[
            button(0, 0, 'Composer', 'wand-magic-sparkles', 'cursor_composer',
                   {}, secondary='Ctrl+I', colour='#8b5cf6'),
            button(0, 1, 'Chat', 'comments', 'cursor_chat', {},
                   secondary='Ctrl+L', colour='#8b5cf6'),
            button(0, 2, 'Inline Edit', 'pen', 'cursor_inline_edit', {},
                   secondary='Ctrl+K', colour='#8b5cf6'),
            button(0, 3, 'New Chat', 'plus', 'cursor_new_chat', {},
                   secondary='Ctrl+Shift+L', colour='#8b5cf6'),
            button(0, 4, 'Full Composer', 'expand', 'cursor_composer_full', {},
                   colour='#8b5cf6'),

            button(1, 0, 'Accept', 'check', 'cursor_accept', {}, colour=GREEN),
            button(1, 1, 'Reject', 'xmark', 'cursor_reject', {}, colour=RED),
            button(1, 2, 'Palette', 'terminal', 'cursor_command_palette', {},
                   secondary='Ctrl+Shift+P'),
            button(1, 3, 'Quick Open', 'magnifying-glass', 'cursor_quick_open',
                   {}, secondary='Ctrl+P'),
            button(1, 4, 'Find in Files', 'magnifying-glass',
                   'cursor_find_in_files', {}, secondary='Ctrl+Shift+F'),

            button(2, 0, 'Terminal', 'terminal', 'cursor_toggle_terminal', {},
                   secondary='Ctrl+`'),
            button(2, 1, 'Sidebar', 'bars', 'cursor_toggle_sidebar', {},
                   secondary='Ctrl+B'),
            button(2, 2, 'Ask Claude', 'robot', 'claude_prompt',
                   {'prompt': 'In {project}: ', 'output': 'both'},
                   colour=CLAUDE),
            button(2, 3, 'Review', 'magnifying-glass', 'claude_slash',
                   {'command': '/code-review'}, colour=CLAUDE),
            button(2, 4, 'PR Checks', 'circle-check', 'gh_pr_checks', {},
                   colour=GITHUB),

            button(3, 0, 'Prev Page', 'chevron-left', 'previous_page', {}),
            button(3, 1, 'Next Page', 'chevron-right', 'next_page', {}),
            button(3, 4, 'CPU', 'microchip', 'metric_cpu_usage', {}),
        ],
    )


def github_deck() -> Dict[str, Any]:
    return template(
        'dev-github-review', 'GitHub Review', 'Pull requests, checks and '
        'workflow runs, with live status on the button faces.',
        'fa-code-pull-request', GITHUB,
        buttons=[
            button(0, 0, 'Open PRs', 'code-pull-request', 'gh_widget_prs',
                   {'refresh_interval': 120}, colour=GITHUB,
                   tooltip='Live count (needs GITHUB_TOKEN)'),
            button(0, 1, 'CI', 'heart-pulse', 'gh_widget_ci',
                   {'refresh_interval': 120}, colour=GITHUB,
                   tooltip='Live CI status for the current branch'),
            button(0, 2, 'Inbox', 'bell', 'gh_widget_notifications',
                   {'refresh_interval': 300}, colour=GITHUB),
            button(0, 3, 'My Review', 'user-check', 'gh_widget_prs',
                   {'only_mine': True, 'refresh_interval': 120},
                   colour=GITHUB, tooltip='PRs awaiting your review'),
            button(0, 4, 'Status', 'list-check', 'gh_status', {},
                   colour=GITHUB),

            button(1, 0, 'List PRs', 'list', 'gh_pr_list', {'limit': 10}),
            button(1, 1, 'New PR', 'plus', 'gh_pr_create', {'web': True},
                   colour=GREEN, tooltip='Opens the PR form in the browser'),
            button(1, 2, 'Checkout PR', 'code-branch', 'gh_pr_checkout', {},
                   tooltip='Set the PR number in the button config'),
            button(1, 3, 'Open PR', 'up-right-from-square', 'gh_pr_view', {}),
            button(1, 4, 'Checks', 'circle-check', 'gh_pr_checks', {}),

            button(2, 0, 'Issues', 'circle-dot', 'gh_issue_list', {'limit': 10}),
            button(2, 1, 'New Issue', 'circle-plus', 'gh_issue_create',
                   {'title': '', 'web': True}),
            button(2, 2, 'Runs', 'play', 'gh_run_list', {'limit': 10}),
            button(2, 3, 'Rerun Failed', 'rotate-right', 'gh_run_rerun', {},
                   colour='#d97706'),
            button(2, 4, 'Review w/ Claude', 'robot', 'claude_slash',
                   {'command': '/code-review'}, colour=CLAUDE),

            button(3, 0, 'Prev Page', 'chevron-left', 'previous_page', {}),
            button(3, 1, 'Next Page', 'chevron-right', 'next_page', {}),
        ],
    )


def git_terminal_deck() -> Dict[str, Any]:
    def git(cmd: str) -> Dict[str, Any]:
        return {'action': 'run_command', 'command': cmd}

    return template(
        'dev-git-terminal', 'Git & Terminal', 'Everyday git operations and '
        'terminal shortcuts.', 'fa-code-branch', GIT,
        buttons=[
            button(0, 0, 'Status', 'circle-info', 'cross_platform',
                   git('git status'), colour=GIT),
            button(0, 1, 'Pull', 'arrow-down', 'cross_platform',
                   git('git pull'), colour=GIT),
            button(0, 2, 'Push', 'arrow-up', 'cross_platform',
                   git('git push'), colour=GIT),
            button(0, 3, 'Fetch', 'arrows-rotate', 'cross_platform',
                   git('git fetch --all --prune'), colour=GIT),
            button(0, 4, 'Log', 'list', 'cross_platform',
                   git('git log --oneline -20'), colour=GIT),

            button(1, 0, 'Branches', 'code-branch', 'cross_platform',
                   git('git branch -a')),
            button(1, 1, 'Stash', 'box-archive', 'cross_platform',
                   git('git stash')),
            button(1, 2, 'Stash Pop', 'box-open', 'cross_platform',
                   git('git stash pop')),
            button(1, 3, 'Diff', 'file-lines', 'cross_platform',
                   git('git diff')),
            button(1, 4, 'Staged Diff', 'file-circle-check', 'cross_platform',
                   git('git diff --staged')),

            button(2, 0, 'Terminal', 'terminal', 'cross_platform',
                   {'action': 'open_app', 'app': 'wt'}),
            button(2, 1, 'Repo Folder', 'folder-open', 'cross_platform',
                   {'action': 'open_folder', 'path': ''},
                   tooltip='Set the folder in the button config'),
            button(2, 2, 'Commit Msg', 'robot', 'claude_prompt',
                   {'prompt': 'Write a commit message for the staged changes '
                              'in {repo}.', 'output': 'both'}, colour=CLAUDE),
            button(2, 3, 'Disk', 'hdd', 'metric_harddisk', {}),
            button(2, 4, 'Network', 'network-wired', 'metric_internet_speed', {}),

            button(3, 0, 'Prev Page', 'chevron-left', 'previous_page', {}),
            button(3, 1, 'Next Page', 'chevron-right', 'next_page', {}),
        ],
    )


def debug_deck() -> Dict[str, Any]:
    def hk(*keys: str) -> Dict[str, Any]:
        return {'keys': list(keys)}

    return template(
        'dev-debug-session', 'Debug Session', 'Breakpoints and step controls '
        'for a VS Code or Cursor debugging session.', 'fa-bug', DEBUG,
        buttons=[
            button(0, 0, 'Start', 'play', 'hotkey', hk('f5'), secondary='F5',
                   colour=GREEN),
            button(0, 1, 'Stop', 'stop', 'hotkey', hk('shift', 'f5'),
                   secondary='Shift+F5', colour=RED),
            button(0, 2, 'Restart', 'rotate-right', 'hotkey',
                   hk('ctrl', 'shift', 'f5'), secondary='Ctrl+Shift+F5',
                   colour='#d97706'),
            button(0, 3, 'Breakpoint', 'circle', 'hotkey', hk('f9'),
                   secondary='F9', colour=DEBUG),
            button(0, 4, 'Continue', 'forward', 'hotkey', hk('f5'),
                   secondary='F5', colour=DEBUG),

            button(1, 0, 'Step Over', 'arrow-right', 'hotkey', hk('f10'),
                   secondary='F10'),
            button(1, 1, 'Step Into', 'arrow-down', 'hotkey', hk('f11'),
                   secondary='F11'),
            button(1, 2, 'Step Out', 'arrow-up', 'hotkey',
                   hk('shift', 'f11'), secondary='Shift+F11'),
            button(1, 3, 'Console', 'terminal', 'hotkey',
                   hk('ctrl', 'shift', 'y'), secondary='Ctrl+Shift+Y'),
            button(1, 4, 'Terminal', 'terminal', 'hotkey', hk('ctrl', '`'),
                   secondary='Ctrl+`'),

            button(2, 0, 'Explain Error', 'robot', 'claude_prompt',
                   {'prompt': 'Explain this error and how to fix it:\n\n'
                              '{clipboard}', 'output': 'both'}, colour=CLAUDE),
            button(2, 1, 'Fix It', 'screwdriver-wrench', 'claude_prompt',
                   {'prompt': 'Fix this failing test or error:\n\n{clipboard}',
                    'output': 'notify'}, colour=CLAUDE),
            button(2, 2, 'Copy', 'copy', 'macro',
                   {'steps': [{'type': 'clipboard_copy'}]}),
            button(2, 3, 'CPU', 'microchip', 'metric_cpu_usage', {}),
            button(2, 4, 'Memory', 'memory', 'metric_memory', {}),

            button(3, 0, 'Prev Page', 'chevron-left', 'previous_page', {}),
            button(3, 1, 'Next Page', 'chevron-right', 'next_page', {}),
        ],
    )


def focus_deck() -> Dict[str, Any]:
    return template(
        'dev-focus-meeting', 'Focus & Meeting', 'Mute, timers and distraction '
        'controls for calls and deep work.', 'fa-headset', FOCUS,
        buttons=[
            button(0, 0, 'Mute Mic', 'microphone-slash', 'cross_platform',
                   {'action': 'microphone_mute'}, colour=RED),
            button(0, 1, 'Unmute Mic', 'microphone', 'cross_platform',
                   {'action': 'microphone_unmute'}, colour=GREEN),
            button(0, 2, 'Mute Audio', 'volume-mute', 'cross_platform',
                   {'action': 'volume_mute'}),
            button(0, 3, 'Volume Up', 'volume-up', 'cross_platform',
                   {'action': 'volume_up'}),
            button(0, 4, 'Volume Down', 'volume-down', 'cross_platform',
                   {'action': 'volume_down'}),

            button(1, 0, 'Timer', 'stopwatch', 'time_timer',
                   {'timer_duration': 1500},
                   tooltip='25-minute focus block'),
            button(1, 1, 'Clock', 'clock', 'time_world_clock', {}),
            button(1, 2, 'Calendar', 'calendar', 'calendar', {}),
            button(1, 3, 'Weather', 'cloud-sun', 'weather', {}),
            button(1, 4, 'Screenshot', 'camera', 'cross_platform',
                   {'action': 'screenshot'}),

            button(2, 0, 'Lock', 'lock', 'cross_platform',
                   {'action': 'lock_screen'}, colour=NEUTRAL),
            button(2, 1, 'Dim Deck', 'lightbulb', 'ui_control',
                   {'action': 'ui_brightness_down', 'step': 10}),
            button(2, 2, 'Brighten', 'sun', 'ui_control',
                   {'action': 'ui_brightness_up', 'step': 10}),
            button(2, 3, 'Play/Pause', 'play', 'cross_platform',
                   {'action': 'media_play_pause'}),
            button(2, 4, 'Next Track', 'forward', 'cross_platform',
                   {'action': 'media_next'}),

            button(3, 0, 'Prev Page', 'chevron-left', 'previous_page', {}),
            button(3, 1, 'Next Page', 'chevron-right', 'next_page', {}),
        ],
    )


DECKS = [
    claude_code_deck, cursor_deck, github_deck,
    git_terminal_deck, debug_deck, focus_deck,
]


def known_action_types() -> set:
    """Every action type that can actually be dispatched right now."""
    from actions.catalog import ACTION_CATALOG
    from plugins.plugin_manager import PluginManager

    types = {spec.action_type for spec in ACTION_CATALOG}

    manager = PluginManager()
    manager.load_builtin_packs()
    types |= {spec.action_type for spec in manager.get_action_specs()}
    return types


def main() -> int:
    known = known_action_types()
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    problems = []
    written = []

    for build in DECKS:
        deck = build()
        for page in deck['pages']:
            seen = set()
            for btn in page['buttons']:
                action_type = btn['action']['type']
                if action_type not in known:
                    problems.append(f"{deck['id']}: unknown action {action_type!r}")
                cell = (btn['position']['row'], btn['position']['col'])
                if cell in seen:
                    problems.append(f"{deck['id']}: two buttons at {cell}")
                seen.add(cell)

                grid = page['grid_config']
                if not (0 <= cell[0] < grid['rows'] and 0 <= cell[1] < grid['cols']):
                    problems.append(f"{deck['id']}: {cell} is outside the grid")

        path = TEMPLATES_DIR / f"{deck['id']}.json"
        path.write_text(json.dumps(deck, indent=2) + '\n', encoding='utf-8')
        written.append((path.name, sum(len(p['buttons']) for p in deck['pages'])))

    for name, count in written:
        print(f'  wrote {name:28} {count:>3} buttons')

    if problems:
        print('\nPROBLEMS:')
        for p in problems:
            print('  -', p)
        return 1

    print(f'\n{len(written)} decks written, all action types valid.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
