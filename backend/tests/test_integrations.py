"""Tests for the Claude, GitHub, Copilot and Cursor integration packs.

Feature: ai-dev-integration-packs, Property 2: packs build correct commands,
never reach a shell, and refuse to type into the wrong window.

The CLIs are mocked throughout -- these assert the exact argv a pack builds,
which is the part that has to be right. Nothing here runs `claude` or `gh` for
real, and nothing sends a keystroke.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from integrations import context, keymaps  # noqa: E402
from integrations.claude_pack import Plugin as ClaudePlugin  # noqa: E402
from integrations.copilot_pack import Plugin as CopilotPlugin  # noqa: E402
from integrations.cursor_pack import Plugin as CursorPlugin  # noqa: E402
from integrations.github_pack import Plugin as GitHubPlugin  # noqa: E402
from utils.subprocess_runner import CommandResult  # noqa: E402


def ok(stdout=''):
    return CommandResult(ok=True, exit_code=0, stdout=stdout, stderr='',
                         argv=['fake'])


@pytest.fixture
def claude(mocker):
    plugin = ClaudePlugin()
    mocker.patch('integrations.claude_pack.sr.find_binary',
                 return_value='C:/fake/claude.exe')
    plugin.initialize()
    return plugin


@pytest.fixture
def github(mocker):
    plugin = GitHubPlugin()
    mocker.patch('integrations.github_pack.sr.find_binary',
                 return_value='C:/fake/gh.exe')
    mocker.patch('integrations.github_pack.sr.run', return_value=ok())
    plugin.initialize()
    return plugin


# --- Claude pack -------------------------------------------------------------

def test_claude_prompt_builds_the_expected_argv(claude, mocker, tmp_path):
    run = mocker.patch('integrations.claude_pack.sr.run',
                       return_value=ok('the answer'))
    mocker.patch('integrations.claude_pack.context.resolve_cwd',
                 return_value=str(tmp_path))

    result = claude.execute_action('claude_prompt', {
        'prompt': 'explain this', 'model': 'claude-opus-5', 'output': 'notify',
    })

    assert result['success'] is True
    argv = run.call_args[0][0]
    assert argv == ['claude', '--model', 'claude-opus-5', '-p', 'explain this']


def test_claude_prompt_passes_shell_metacharacters_as_one_argument(
    claude, mocker, tmp_path
):
    """A prompt is a prompt, even when it contains shell syntax."""
    run = mocker.patch('integrations.claude_pack.sr.run', return_value=ok('ok'))
    mocker.patch('integrations.claude_pack.context.resolve_cwd',
                 return_value=str(tmp_path))

    nasty = 'fix the bug; rm -rf ~ && echo `whoami`'
    claude.execute_action('claude_prompt', {'prompt': nasty})

    argv = run.call_args[0][0]
    assert argv[-1] == nasty, 'the prompt must arrive as a single argv entry'
    assert argv[-2] == '-p'


def test_claude_prompt_can_continue_a_session(claude, mocker, tmp_path):
    run = mocker.patch('integrations.claude_pack.sr.run', return_value=ok('ok'))
    mocker.patch('integrations.claude_pack.context.resolve_cwd',
                 return_value=str(tmp_path))

    claude.execute_action('claude_prompt',
                          {'prompt': 'and now?', 'continue_session': True})

    assert '--continue' in run.call_args[0][0]


def test_claude_slash_normalises_a_missing_leading_slash(claude, mocker, tmp_path):
    run = mocker.patch('integrations.claude_pack.sr.run', return_value=ok('ok'))
    mocker.patch('integrations.claude_pack.context.resolve_cwd',
                 return_value=str(tmp_path))

    claude.execute_action('claude_slash', {'command': 'code-review'})

    assert run.call_args[0][0][-1] == '/code-review'


def test_claude_slash_appends_arguments(claude, mocker, tmp_path):
    run = mocker.patch('integrations.claude_pack.sr.run', return_value=ok('ok'))
    mocker.patch('integrations.claude_pack.context.resolve_cwd',
                 return_value=str(tmp_path))

    claude.execute_action('claude_slash',
                          {'command': '/commit', 'args': 'be terse'})

    assert run.call_args[0][0][-1] == '/commit be terse'


def test_claude_prompt_requires_a_prompt(claude):
    result = claude.execute_action('claude_prompt', {'prompt': '   '})

    assert result['success'] is False
    assert 'No prompt' in result['message']


def test_claude_reports_cli_failure_with_details(claude, mocker, tmp_path):
    mocker.patch('integrations.claude_pack.sr.run', return_value=CommandResult(
        ok=False, exit_code=1, stdout='', stderr='not logged in',
        argv=['claude']))
    mocker.patch('integrations.claude_pack.context.resolve_cwd',
                 return_value=str(tmp_path))

    result = claude.execute_action('claude_prompt', {'prompt': 'hi'})

    assert result['success'] is False
    assert 'not logged in' in result['details']


def test_claude_without_the_cli_reports_it_clearly(mocker):
    mocker.patch('integrations.claude_pack.sr.find_binary', return_value=None)
    plugin = ClaudePlugin()
    plugin.initialize()

    result = plugin.execute_action('claude_prompt', {'prompt': 'hi'})

    assert result['success'] is False
    assert 'not found' in result['message'].lower()


def test_claude_api_action_is_greyed_out_without_a_key(claude, mocker):
    mocker.patch('services.secrets.is_configured', return_value=False)

    spec = next(s for s in claude.get_action_specs() if s.id == 'claude_api_prompt')

    assert spec.unavailable_reason
    assert 'ANTHROPIC_API_KEY' in spec.unavailable_reason


def test_claude_api_action_refuses_without_a_key(claude, mocker):
    mocker.patch('services.secrets.get', return_value=None)

    result = claude.execute_action('claude_api_prompt', {'prompt': 'hi'})

    assert result['success'] is False
    assert 'ANTHROPIC_API_KEY' in result['message']


def test_claude_cli_actions_stay_available_without_an_api_key(claude, mocker):
    """The CLI uses its own login; a missing key must not disable it."""
    mocker.patch('services.secrets.is_configured', return_value=False)

    specs = {s.id: s for s in claude.get_action_specs()}

    assert specs['claude_prompt'].unavailable_reason is None
    assert claude.is_available()[0] is True


# --- GitHub pack -------------------------------------------------------------

def test_gh_pr_list_builds_the_expected_argv(github, mocker, tmp_path):
    run = mocker.patch('integrations.github_pack.sr.run', return_value=ok('#1 a'))
    mocker.patch('integrations.github_pack.context.resolve_cwd',
                 return_value=str(tmp_path))
    mocker.patch('integrations.github_pack.context.git_repo_root',
                 return_value=str(tmp_path))

    result = github.execute_action('gh_pr_list', {'limit': 5})

    assert result['success'] is True
    assert run.call_args[0][0] == ['gh', 'pr', 'list', '--limit', '5']


def test_gh_pr_create_defaults_to_the_browser(github, mocker, tmp_path):
    """One button press must not silently open a PR."""
    run = mocker.patch('integrations.github_pack.sr.run', return_value=ok())
    mocker.patch('integrations.github_pack.context.resolve_cwd',
                 return_value=str(tmp_path))
    mocker.patch('integrations.github_pack.context.git_repo_root',
                 return_value=str(tmp_path))

    github.execute_action('gh_pr_create', {})

    assert '--web' in run.call_args[0][0]


def test_gh_refuses_outside_a_git_repository(github, mocker, tmp_path):
    mocker.patch('integrations.github_pack.context.resolve_cwd',
                 return_value=str(tmp_path))
    mocker.patch('integrations.github_pack.context.git_repo_root',
                 return_value=None)

    result = github.execute_action('gh_pr_list', {})

    assert result['success'] is False
    assert 'not a git repository' in result['message'].lower()


def test_gh_pr_checkout_requires_a_number(github):
    result = github.execute_action('gh_pr_checkout', {'pr': ''})

    assert result['success'] is False
    assert 'No PR number' in result['message']


def test_gh_widgets_are_greyed_out_without_a_token(github, mocker):
    mocker.patch('services.secrets.is_configured', return_value=False)

    specs = {s.id: s for s in github.get_action_specs()}

    assert specs['gh_widget_prs'].unavailable_reason
    # ...but the CLI actions, which use gh's own login, stay usable.
    assert specs['gh_pr_list'].unavailable_reason is None


def test_gh_unauthenticated_cli_is_reported(mocker):
    mocker.patch('integrations.github_pack.sr.find_binary',
                 return_value='C:/fake/gh.exe')
    mocker.patch('integrations.github_pack.sr.run', return_value=CommandResult(
        ok=False, exit_code=1, stdout='', stderr='not logged in', argv=['gh']))
    plugin = GitHubPlugin()
    plugin.initialize()

    spec = next(s for s in plugin.get_action_specs() if s.id == 'gh_pr_list')

    assert 'gh auth login' in spec.unavailable_reason


def test_repo_slug_parses_https_and_ssh_remotes(github, mocker, tmp_path):
    mocker.patch('integrations.github_pack.context.resolve_cwd',
                 return_value=str(tmp_path))

    for url in ('https://github.com/ponya5/VDock2.git',
                'git@github.com:ponya5/VDock2.git',
                'https://github.com/ponya5/VDock2'):
        mocker.patch('integrations.github_pack.sr.run', return_value=ok(url))
        assert github._repo_slug({}) == 'ponya5/VDock2', url


# --- Copilot / Cursor keystroke packs ----------------------------------------

def test_cursor_command_is_refused_when_cursor_is_not_focused(mocker):
    """The guard that stops a prompt being typed into the wrong window."""
    mocker.patch('integrations.editor_base.foreground_exe',
                 return_value='chrome.exe')
    macro = mocker.patch('integrations.editor_base.MacroAction')

    result = CursorPlugin().execute_action('cursor_composer', {})

    assert result['success'] is False
    assert 'not focused' in result['message']
    macro.assert_not_called(), 'no keystrokes may be sent'


def test_cursor_command_is_refused_when_focus_is_unknown(mocker):
    mocker.patch('integrations.editor_base.foreground_exe', return_value=None)
    macro = mocker.patch('integrations.editor_base.MacroAction')

    result = CursorPlugin().execute_action('cursor_composer', {})

    assert result['success'] is False
    macro.assert_not_called()


def test_cursor_command_sends_keys_when_cursor_is_focused(mocker):
    mocker.patch('integrations.editor_base.foreground_exe',
                 return_value='cursor.exe')
    macro = mocker.patch('integrations.editor_base.MacroAction')
    macro.return_value.execute.return_value = mocker.Mock(
        success=True, message='ok', details=None, data={})

    result = CursorPlugin().execute_action('cursor_composer', {})

    assert result['success'] is True
    steps = macro.call_args[0][0]['steps']
    assert steps[0] == {'type': 'hotkey', 'keys': ['ctrl', 'i']}


def test_copilot_slash_command_types_and_submits(mocker):
    mocker.patch('integrations.editor_base.foreground_exe',
                 return_value='code.exe')
    macro = mocker.patch('integrations.editor_base.MacroAction')
    macro.return_value.execute.return_value = mocker.Mock(
        success=True, message='ok', details=None, data={})

    CopilotPlugin().execute_action('copilot_fix', {})

    steps = macro.call_args[0][0]['steps']
    kinds = [s['type'] for s in steps]
    assert kinds == ['hotkey', 'delay', 'text', 'delay', 'hotkey']
    assert steps[2]['text'] == '/fix'
    assert steps[4]['keys'] == ['enter']


def test_focus_guard_can_be_disabled_deliberately(mocker):
    mocker.patch('integrations.editor_base.foreground_exe',
                 return_value='chrome.exe')
    macro = mocker.patch('integrations.editor_base.MacroAction')
    macro.return_value.execute.return_value = mocker.Mock(
        success=True, message='ok', details=None, data={})

    result = CursorPlugin().execute_action('cursor_composer',
                                           {'enforce_focus': False})

    assert result['success'] is True


def test_focus_guard_defaults_to_on_in_every_spec():
    for plugin in (CursorPlugin(), CopilotPlugin()):
        for spec in plugin.get_action_specs():
            assert spec.default_config.get('enforce_focus') is True, spec.id


def test_keymap_commands_use_supported_macro_steps():
    supported = {'hotkey', 'delay', 'text', 'click',
                 'clipboard_copy', 'clipboard_paste', 'clipboard_set'}
    for command in keymaps.ALL_COMMANDS:
        for step in command.to_macro_steps():
            assert step['type'] in supported, command.id


def test_keymap_command_ids_are_unique():
    ids = [c.id for c in keymaps.ALL_COMMANDS]
    assert len(ids) == len(set(ids))


# --- shared context ----------------------------------------------------------

@pytest.mark.parametrize('title,expected', [
    ('app.py - VDock2 - Cursor', 'VDock2'),
    ('VDock2 - Visual Studio Code', 'VDock2'),
    ('\u25cf catalog.py - vdock2 - Cursor', 'vdock2'),
    ('untitled', None),
    ('', None),
])
def test_project_name_is_parsed_from_the_window_title(title, expected):
    assert context.project_name_from_title(title) == expected


def test_placeholders_expand(mocker, tmp_path):
    mocker.patch('integrations.context.resolve_cwd', return_value=str(tmp_path))
    mocker.patch('integrations.context.current_branch', return_value='main')

    out = context.expand_placeholders('{project} on {branch}')

    assert out == f'{tmp_path.name} on main'


def test_text_without_placeholders_is_untouched():
    assert context.expand_placeholders('plain text') == 'plain text'
