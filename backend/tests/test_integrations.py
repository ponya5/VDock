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

from integrations import context, keymaps, sessions  # noqa: E402
from integrations.claude_code_pack import Plugin as ClaudeCodePlugin  # noqa: E402
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
#
# Every test mocks `window_focus.focus_app_window`: the real call would run
# EnumWindows on the dev machine and could pull an actual editor window to
# the front mid-test.

def test_cursor_command_is_refused_when_cursor_is_not_focused(mocker):
    """The guard that stops a prompt being typed into the wrong window."""
    mocker.patch(
        'integrations.editor_base.window_focus.focus_app_window',
        return_value=True)
    mocker.patch('integrations.editor_base.time.sleep')
    mocker.patch('integrations.editor_base.foreground_exe',
                 return_value='chrome.exe')
    macro = mocker.patch('integrations.editor_base.MacroAction')

    result = CursorPlugin().execute_action('cursor_composer', {})

    assert result['success'] is False
    assert 'not focused' in result['message']
    macro.assert_not_called(), 'no keystrokes may be sent'


def test_cursor_command_is_refused_when_focus_is_unknown(mocker):
    mocker.patch(
        'integrations.editor_base.window_focus.focus_app_window',
        return_value=True)
    mocker.patch('integrations.editor_base.time.sleep')
    mocker.patch('integrations.editor_base.foreground_exe', return_value=None)
    macro = mocker.patch('integrations.editor_base.MacroAction')

    result = CursorPlugin().execute_action('cursor_composer', {})

    assert result['success'] is False
    macro.assert_not_called()


def test_cursor_command_sends_keys_when_cursor_is_focused(mocker):
    mocker.patch(
        'integrations.editor_base.window_focus.focus_app_window',
        return_value=True)
    mocker.patch('integrations.editor_base.time.sleep')
    mocker.patch('integrations.editor_base.foreground_exe',
                 return_value='cursor.exe')
    macro = mocker.patch('integrations.editor_base.MacroAction')
    macro.return_value.execute.return_value = mocker.Mock(
        success=True, message='ok', details=None, data={})

    result = CursorPlugin().execute_action('cursor_composer', {})

    assert result['success'] is True
    steps = macro.call_args[0][0]['steps']
    assert steps[0] == {'type': 'hotkey', 'keys': ['ctrl', 'i']}


def test_focus_first_raises_the_target_window(mocker):
    """On a touch deck the button press steals focus -- the send must put the
    target window back in front before typing."""
    focus = mocker.patch(
        'integrations.editor_base.window_focus.focus_app_window',
        return_value=True)
    mocker.patch('integrations.editor_base.time.sleep')
    mocker.patch('integrations.editor_base.foreground_exe',
                 return_value='cursor.exe')
    macro = mocker.patch('integrations.editor_base.MacroAction')
    macro.return_value.execute.return_value = mocker.Mock(
        success=True, message='ok', details=None, data={})

    result = CursorPlugin().execute_action('cursor_composer', {})

    assert result['success'] is True
    focus.assert_called_once()
    assert set(focus.call_args[0][0]) == {'cursor.exe'}


def test_command_is_refused_when_no_target_window_exists(mocker):
    mocker.patch(
        'integrations.editor_base.window_focus.focus_app_window',
        return_value=False)
    macro = mocker.patch('integrations.editor_base.MacroAction')

    result = CursorPlugin().execute_action('cursor_composer', {})

    assert result['success'] is False
    assert 'window found' in result['message']
    macro.assert_not_called()


def test_focus_first_can_be_disabled(mocker):
    focus = mocker.patch(
        'integrations.editor_base.window_focus.focus_app_window')
    mocker.patch('integrations.editor_base.foreground_exe',
                 return_value='cursor.exe')
    macro = mocker.patch('integrations.editor_base.MacroAction')
    macro.return_value.execute.return_value = mocker.Mock(
        success=True, message='ok', details=None, data={})

    result = CursorPlugin().execute_action('cursor_composer',
                                           {'focus_first': False})

    assert result['success'] is True
    focus.assert_not_called()


def test_copilot_slash_command_types_and_submits(mocker):
    mocker.patch(
        'integrations.editor_base.window_focus.focus_app_window',
        return_value=True)
    mocker.patch('integrations.editor_base.time.sleep')
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
    for plugin in (CursorPlugin(), CopilotPlugin(), ClaudeCodePlugin()):
        for spec in plugin.get_action_specs():
            assert spec.default_config.get('enforce_focus') is True, spec.id
            assert spec.default_config.get('focus_first') is True, spec.id


# --- Claude Code live-session pack -------------------------------------------

def test_cc_clear_is_refused_without_a_live_session(mocker):
    """Typed input must not reach a terminal that is not running the agent."""
    mocker.patch('integrations.sessions.session_alive', return_value=False)
    macro = mocker.patch('integrations.editor_base.MacroAction')

    result = ClaudeCodePlugin().execute_action('cc_clear', {})

    assert result['success'] is False
    assert 'session' in result['message'].lower()
    macro.assert_not_called()


def test_cc_clear_types_clear_into_a_live_session(mocker):
    mocker.patch('integrations.sessions.session_alive', return_value=True)
    mocker.patch(
        'integrations.editor_base.window_focus.find_session_host_window',
        return_value=None)
    mocker.patch(
        'integrations.editor_base.window_focus.focus_app_window',
        return_value=True)
    mocker.patch('integrations.editor_base.time.sleep')
    mocker.patch('integrations.editor_base.foreground_exe',
                 return_value='windowsterminal.exe')
    macro = mocker.patch('integrations.editor_base.MacroAction')
    macro.return_value.execute.return_value = mocker.Mock(
        success=True, message='ok', details=None, data={})

    result = ClaudeCodePlugin().execute_action('cc_clear', {})

    assert result['success'] is True
    steps = macro.call_args[0][0]['steps']
    # Typed-only command: no empty hotkey step may be emitted.
    assert [s['type'] for s in steps] == ['delay', 'text', 'delay', 'hotkey']
    assert steps[1]['text'] == '/clear'
    assert steps[3]['keys'] == ['enter']


def test_cc_commands_resolve_the_session_host_window(mocker):
    """A session inside an IDE terminal resolves to the IDE's window -- the
    whole point of host-window targeting: exe lists can't know the host."""
    mocker.patch('integrations.sessions.session_alive', return_value=True)
    host = mocker.patch(
        'integrations.editor_base.window_focus.find_session_host_window',
        return_value=4321)
    focus = mocker.patch(
        'integrations.editor_base.window_focus.focus_hwnd',
        return_value=True)
    by_exe = mocker.patch(
        'integrations.editor_base.window_focus.focus_app_window')
    mocker.patch('integrations.editor_base.time.sleep')
    mocker.patch('integrations.editor_base.window_focus.foreground_hwnd',
                 return_value=4321)
    macro = mocker.patch('integrations.editor_base.MacroAction')
    macro.return_value.execute.return_value = mocker.Mock(
        success=True, message='ok', details=None, data={})
    mocker.patch('integrations.editor_base.context.current_editor',
                 return_value=mocker.Mock(cwd=None))

    result = ClaudeCodePlugin().execute_action('cc_clear', {})

    assert result['success'] is True
    host.assert_called_once_with('claude', prefer_title='claude',
                                 prefer_cwd=None)
    focus.assert_called_once_with(4321)
    by_exe.assert_not_called(), 'host resolution must win over the exe list'


def test_cc_host_window_refuses_when_another_window_stays_foreground(mocker):
    mocker.patch('integrations.sessions.session_alive', return_value=True)
    mocker.patch(
        'integrations.editor_base.window_focus.find_session_host_window',
        return_value=4321)
    mocker.patch('integrations.editor_base.window_focus.focus_hwnd',
                 return_value=True)
    mocker.patch('integrations.editor_base.time.sleep')
    mocker.patch('integrations.editor_base.window_focus.foreground_hwnd',
                 return_value=9999)
    macro = mocker.patch('integrations.editor_base.MacroAction')

    result = ClaudeCodePlugin().execute_action('cc_clear', {})

    assert result['success'] is False
    assert 'not focused' in result['message']
    macro.assert_not_called()


def test_cc_host_window_reports_when_focus_fails(mocker):
    mocker.patch('integrations.sessions.session_alive', return_value=True)
    mocker.patch(
        'integrations.editor_base.window_focus.find_session_host_window',
        return_value=4321)
    mocker.patch('integrations.editor_base.window_focus.focus_hwnd',
                 return_value=False)
    mocker.patch(
        'integrations.editor_base.window_focus.interactive_desktop_blocked',
        return_value=False)
    mocker.patch('integrations.editor_base.time.sleep')
    macro = mocker.patch('integrations.editor_base.MacroAction')

    result = ClaudeCodePlugin().execute_action('cc_clear', {})

    assert result['success'] is False
    assert 'focus' in result['message'].lower()
    macro.assert_not_called()


def test_cc_focus_failure_names_the_lock_screen_or_screensaver(mocker):
    mocker.patch('integrations.sessions.session_alive', return_value=True)
    mocker.patch(
        'integrations.editor_base.window_focus.find_session_host_window',
        return_value=4321)
    mocker.patch('integrations.editor_base.window_focus.focus_hwnd',
                 return_value=False)
    mocker.patch(
        'integrations.editor_base.window_focus.interactive_desktop_blocked',
        return_value=True)
    mocker.patch('integrations.editor_base.time.sleep')
    macro = mocker.patch('integrations.editor_base.MacroAction')

    result = ClaudeCodePlugin().execute_action('cc_submit', {})

    assert result['success'] is False
    assert 'screensaver' in result['message']
    macro.assert_not_called()


def test_cc_falls_back_to_terminal_exes_when_no_host_resolves(mocker):
    """No resolvable session window -> the old exe-list path still applies."""
    mocker.patch('integrations.sessions.session_alive', return_value=True)
    mocker.patch(
        'integrations.editor_base.window_focus.find_session_host_window',
        return_value=None)
    focus = mocker.patch(
        'integrations.editor_base.window_focus.focus_app_window',
        return_value=False)
    macro = mocker.patch('integrations.editor_base.MacroAction')

    result = ClaudeCodePlugin().execute_action('cc_clear', {})

    assert result['success'] is False
    focus.assert_called_once()
    macro.assert_not_called()


def test_cc_exit_is_refused_without_destructive_opt_in(mocker):
    mocker.patch('integrations.sessions.session_alive', return_value=True)
    macro = mocker.patch('integrations.editor_base.MacroAction')

    result = ClaudeCodePlugin().execute_action('cc_exit', {})

    assert result['success'] is False
    assert 'destructive' in result['message'].lower()
    macro.assert_not_called()


def test_cc_exit_sends_ctrl_d_twice_when_opted_in(mocker):
    mocker.patch('integrations.sessions.session_alive', return_value=True)
    mocker.patch(
        'integrations.editor_base.window_focus.find_session_host_window',
        return_value=None)
    mocker.patch(
        'integrations.editor_base.window_focus.focus_app_window',
        return_value=True)
    mocker.patch('integrations.editor_base.time.sleep')
    mocker.patch('integrations.editor_base.foreground_exe',
                 return_value='cmd.exe')
    macro = mocker.patch('integrations.editor_base.MacroAction')
    macro.return_value.execute.return_value = mocker.Mock(
        success=True, message='ok', details=None, data={})

    result = ClaudeCodePlugin().execute_action(
        'cc_exit', {'allow_destructive': True})

    assert result['success'] is True
    steps = macro.call_args[0][0]['steps']
    assert [s['type'] for s in steps] == ['hotkey', 'delay', 'hotkey']
    assert steps[0]['keys'] == ['ctrl', 'd'] == steps[2]['keys']


def test_cc_interrupt_needs_no_session_gate(mocker):
    """Safe commands fire on the focus guard alone."""
    mocker.patch(
        'integrations.editor_base.window_focus.find_session_host_window',
        return_value=None)
    mocker.patch(
        'integrations.editor_base.window_focus.focus_app_window',
        return_value=True)
    mocker.patch('integrations.editor_base.time.sleep')
    mocker.patch('integrations.editor_base.foreground_exe',
                 return_value='windowsterminal.exe')
    macro = mocker.patch('integrations.editor_base.MacroAction')
    macro.return_value.execute.return_value = mocker.Mock(
        success=True, message='ok', details=None, data={})

    result = ClaudeCodePlugin().execute_action('cc_interrupt', {})

    assert result['success'] is True
    steps = macro.call_args[0][0]['steps']
    assert steps[0] == {'type': 'hotkey', 'keys': ['escape']}


def test_cc_chord_commands_emit_two_hotkey_strokes(mocker):
    """Ctrl+X Ctrl+K (kill agents) is a two-stroke chord: the keymap models
    it as keys + after_keys, and the macro must send two hotkey steps."""
    mocker.patch('integrations.sessions.session_alive', return_value=True)
    mocker.patch(
        'integrations.editor_base.window_focus.find_session_host_window',
        return_value=None)
    mocker.patch(
        'integrations.editor_base.window_focus.focus_app_window',
        return_value=True)
    mocker.patch('integrations.editor_base.time.sleep')
    mocker.patch('integrations.editor_base.foreground_exe',
                 return_value='cmd.exe')
    macro = mocker.patch('integrations.editor_base.MacroAction')
    macro.return_value.execute.return_value = mocker.Mock(
        success=True, message='ok', details=None, data={})

    result = ClaudeCodePlugin().execute_action(
        'cc_kill_agents', {'allow_destructive': True})

    assert result['success'] is True
    steps = macro.call_args[0][0]['steps']
    assert [s['type'] for s in steps] == ['hotkey', 'delay', 'hotkey']
    assert steps[0]['keys'] == ['ctrl', 'x']
    assert steps[2]['keys'] == ['ctrl', 'k']


def test_destructive_commands_expose_the_opt_in_field():
    spec = next(s for s in ClaudeCodePlugin().get_action_specs()
                if s.id == 'cc_exit')
    names = [f.name for f in spec.config_fields]
    assert 'allow_destructive' in names


def test_claude_code_profile_is_registered():
    profile = keymaps.PROFILES_BY_ID['claude-code']
    assert profile.kind == 'terminal_agent'
    assert all(c.id.startswith('cc_') for c in profile.commands)


def test_session_host_window_walks_the_process_tree(mocker):
    """A session inside an IDE terminal resolves to the IDE's own window:
    claude.exe -> shell -> Cursor.exe, and the window belongs to Cursor."""
    from utils import window_focus
    mocker.patch('utils.window_focus.platform.system',
                 return_value='Windows')
    mocker.patch.object(window_focus, '_session_pids', return_value=[100])
    mocker.patch.object(
        window_focus, '_visible_windows_by_pid',
        return_value={200: [(4321, 'VDock2 - Cursor')]})
    mocker.patch('psutil.process_iter', return_value=[])

    parent = mocker.Mock()
    parent.pid = 200
    proc = mocker.Mock()
    proc.parents.return_value = [parent]
    mocker.patch('psutil.Process', return_value=proc)

    assert window_focus.find_session_host_window('claude') == 4321


def test_session_host_window_prefers_hosted_over_self_owned(mocker):
    """The Claude desktop app also matches 'claude' and owns a window, but a
    hosted CLI session is what the deck buttons mean."""
    from utils import window_focus
    mocker.patch('utils.window_focus.platform.system',
                 return_value='Windows')
    # 150 is the desktop app (owns its own window); 100 is the CLI whose
    # parent's child conhost (300) owns the console window.
    mocker.patch.object(window_focus, '_session_pids',
                        return_value=[150, 100])
    mocker.patch.object(
        window_focus, '_visible_windows_by_pid',
        return_value={150: [(9000, 'Claude')], 300: [(4321, 'claude')]})

    child = mocker.Mock()
    child.info = {'ppid': 200}
    child.pid = 300
    mocker.patch('psutil.process_iter', return_value=[child])

    def fake_process(pid):
        proc = mocker.Mock()
        proc.parents.return_value = ([mocker.Mock(pid=200)]
                                     if pid == 100 else [])
        return proc

    mocker.patch('psutil.Process', side_effect=fake_process)

    hwnd = window_focus.find_session_host_window('claude',
                                                 prefer_title='claude')
    assert hwnd == 4321


def test_session_host_window_returns_none_without_a_session(mocker):
    from utils import window_focus
    mocker.patch('utils.window_focus.platform.system',
                 return_value='Windows')
    mocker.patch.object(window_focus, '_session_pids', return_value=[])
    assert window_focus.find_session_host_window('claude') is None


def test_session_host_window_prefers_matching_cwd(mocker):
    """Two sessions enumerated in the wrong order: the one running in the
    button's project wins even though the other is listed first."""
    from utils import window_focus
    mocker.patch('utils.window_focus.platform.system',
                 return_value='Windows')
    mocker.patch.object(window_focus, '_session_pids',
                        return_value=[100, 150])
    mocker.patch.object(
        window_focus, '_visible_windows_by_pid',
        return_value={200: [(1111, 'claude A')],
                      250: [(2222, 'claude B')]})
    mocker.patch('psutil.process_iter', return_value=[])

    def fake_process(pid):
        proc = mocker.Mock()
        parent = mocker.Mock()
        parent.pid = {100: 200, 150: 250}[pid]
        proc.parents.return_value = [parent]
        proc.cwd.return_value = {100: r'C:\other',
                                 150: r'C:\proj'}[pid]
        proc.create_time.return_value = 1.0
        return proc

    mocker.patch('psutil.Process', side_effect=fake_process)

    hwnd = window_focus.find_session_host_window(
        'claude', prefer_title='claude', prefer_cwd=r'C:\proj')
    assert hwnd == 2222


def test_session_host_window_tiebreaks_to_newest_session(mocker):
    """With no cwd preference, equal candidates resolve to the most
    recently started session rather than enumeration order."""
    from utils import window_focus
    mocker.patch('utils.window_focus.platform.system',
                 return_value='Windows')
    mocker.patch.object(window_focus, '_session_pids',
                        return_value=[100, 150])
    mocker.patch.object(
        window_focus, '_visible_windows_by_pid',
        return_value={200: [(1111, 'claude A')],
                      250: [(2222, 'claude B')]})
    mocker.patch('psutil.process_iter', return_value=[])

    def fake_process(pid):
        proc = mocker.Mock()
        parent = mocker.Mock()
        parent.pid = {100: 200, 150: 250}[pid]
        proc.parents.return_value = [parent]
        proc.cwd.return_value = r'C:\proj'
        proc.create_time.return_value = {100: 1.0, 150: 2.0}[pid]
        return proc

    mocker.patch('psutil.Process', side_effect=fake_process)

    hwnd = window_focus.find_session_host_window(
        'claude', prefer_title='claude')
    assert hwnd == 2222


def test_cwd_tier_orders_exact_then_ancestor_then_nested():
    from utils import window_focus
    proj = os.path.join(os.sep, 'proj')
    sub = os.path.join(proj, 'sub')
    other = os.path.join(os.sep, 'other')
    assert window_focus._cwd_tier(proj, proj) == 0
    # Session at the repo root, button resolved a subdirectory.
    assert window_focus._cwd_tier(proj, sub) == 1
    # Session nested inside the preferred directory.
    assert window_focus._cwd_tier(sub, proj) == 2
    assert window_focus._cwd_tier(other, proj) == 3
    # A shared prefix is not nesting: project2 is not inside proj.
    assert window_focus._cwd_tier(os.path.join(os.sep, 'project2'), proj) == 3
    assert window_focus._cwd_tier(None, proj) == 3


def test_session_match_counts_real_cli_processes():
    cli = {'name': 'claude.exe', 'exe': r'C:\npm\node_modules\@anthropic-ai\claude-code\bin\claude.exe',
           'cmdline': [r'C:\npm\node_modules\@anthropic-ai\claude-code\bin\claude.exe', '--continue']}
    assert sessions._matches(cli, 'claude')

    node = {'name': 'node.exe', 'exe': r'C:\node\node.exe',
            'cmdline': ['node', r'C:\npm\claude-code\cli.js']}
    assert sessions._matches(node, 'claude')

    shim_wrap = {'name': 'cmd.exe', 'exe': r'C:\Windows\System32\cmd.exe',
                 'cmdline': ['cmd.exe', '/c', r'"C:\npm\claude.cmd"', '--continue']}
    assert sessions._matches(shim_wrap, 'claude')


def test_session_match_rejects_helpers_and_desktop_app():
    # The Claude desktop app shares the claude.exe name but is no session.
    desktop = {'name': 'claude.exe',
               'exe': r'C:\Users\x\AppData\Local\AnthropicClaude\claude.exe',
               'cmdline': [r'C:\Users\x\AppData\Local\AnthropicClaude\claude.exe']}
    assert not sessions._matches(desktop, 'claude')

    # A helper whose script blob merely mentions the marker.
    helper = {'name': 'python.exe', 'exe': r'C:\Python\python.exe',
              'cmdline': ['python', '-c', 'print("claude")']}
    assert not sessions._matches(helper, 'claude')

    # `cmd /c claude --continue` names claude as a bare argument; the real
    # session is its child claude.exe, not this wrapper.
    bare_arg = {'name': 'cmd.exe', 'exe': r'C:\Windows\System32\cmd.exe',
                'cmdline': ['cmd.exe', '/c', 'claude', '--continue']}
    assert not sessions._matches(bare_arg, 'claude')


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
