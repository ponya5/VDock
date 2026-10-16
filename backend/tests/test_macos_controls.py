"""DL-002: macOS volume / media actions.

Regression for "Command failed: 26:36: syntax error ... (-2740)": scripts were
pasted into ``osascript -e "..."`` with shell=True, so the shell stripped the
quotes around ``"Music"``. Everything now goes through argv lists, and media
buttons drive the *running* player instead of always launching Apple Music.
"""
import re
from pathlib import Path

import pytest

from actions import macos_controls
from actions.cross_platform_action import CrossPlatformAction


@pytest.fixture(autouse=True)
def _no_players_running(monkeypatch):
    """Default: nothing is playing. pgrep does not exist on Windows, so tests
    that reach remote_spotify_playing() must not shell out for real; tests
    that want players override this via running_players (applied later)."""
    monkeypatch.setattr(macos_controls, '_is_app_running', lambda app_name: False)


@pytest.fixture
def osascript_calls(monkeypatch):
    """Record every script; 'get volume settings' answers with a fixed state."""
    calls = []

    def fake_run_osascript(script, javascript=False, arguments=None):
        calls.append({'script': script, 'javascript': javascript, 'arguments': arguments})
        if script == 'get volume settings':
            return True, 'output volume:50, input volume:30, alert volume:100, output muted:false'
        if 'player state' in script:
            return True, 'paused'
        return True, ''

    monkeypatch.setattr(macos_controls, '_run_osascript', fake_run_osascript)
    return calls


@pytest.fixture
def running_players(monkeypatch):
    running = set()
    monkeypatch.setattr(
        macos_controls, '_is_app_running', lambda app_name: app_name in running)
    return running


def _scripts(calls):
    return [call['script'] for call in calls]


class TestParseVolumeStep:
    @pytest.mark.parametrize('raw_step, expected', [
        (10, 10),
        ('15', 15),
        (-5, 5),
        (100, 100),
        (None, 10),
        ('abc', 10),
        (0, 10),
    ])
    def test_percent_steps(self, raw_step, expected):
        assert macos_controls.parse_volume_step(raw_step) == expected

    def test_nircmd_scale_step_becomes_small_percentage(self):
        # Presets ship step=2000 for Windows (0-65535 scale).
        assert macos_controls.parse_volume_step(2000) == 3

    def test_tiny_nircmd_step_never_rounds_to_zero(self):
        assert macos_controls.parse_volume_step(101) == 1


class TestVolume:
    def test_volume_up_adds_step_to_current_level(self, osascript_calls):
        result = macos_controls.change_output_volume(10)

        assert result.success
        assert 'set volume output volume 60' in _scripts(osascript_calls)

    def test_volume_clamps_at_bounds(self, osascript_calls):
        macos_controls.change_output_volume(500)
        macos_controls.change_output_volume(-500)

        scripts = _scripts(osascript_calls)
        assert 'set volume output volume 100' in scripts
        assert 'set volume output volume 0' in scripts

    def test_fixed_level_output_reports_clear_error(self, monkeypatch):
        monkeypatch.setattr(
            macos_controls, '_run_osascript',
            lambda *args, **kwargs: (True, 'output volume:missing value, input volume:30'))

        result = macos_controls.change_output_volume(10)

        assert not result.success
        assert 'no adjustable volume' in result.message

    def test_action_uses_percent_step_not_nircmd_units(self, monkeypatch, osascript_calls):
        monkeypatch.setattr('actions.cross_platform_action._SYSTEM', 'Darwin')
        CrossPlatformAction({'action': 'volume_up', 'step': 2000}).execute()

        assert 'set volume output volume 53' in _scripts(osascript_calls)


class TestMicrophone:
    def test_unmute_restores_level_from_before_mute(self, monkeypatch):
        levels = {'input': 30}
        scripts = []

        def fake_run_osascript(script, javascript=False, arguments=None):
            scripts.append(script)
            if script == 'get volume settings':
                return True, f"output volume:50, input volume:{levels['input']}"
            levels['input'] = int(script.rsplit(' ', 1)[1])
            return True, ''

        monkeypatch.setattr(macos_controls, '_run_osascript', fake_run_osascript)

        macos_controls.set_microphone_muted(True)
        macos_controls.set_microphone_muted(False)

        assert 'set volume input volume 0' in scripts
        assert levels['input'] == 30


class TestMedia:
    def test_drives_running_spotify_without_touching_music(
            self, osascript_calls, running_players):
        running_players.add('Spotify')

        result = macos_controls.control_media('next')

        assert result.success
        assert 'tell application "Spotify" to next track' in _scripts(osascript_calls)
        assert not any('"Music"' in script for script in _scripts(osascript_calls))

    def test_prefers_the_player_that_is_playing(self, monkeypatch, running_players):
        running_players.update({'Spotify', 'Music'})
        scripts = []

        def fake_run_osascript(script, javascript=False, arguments=None):
            scripts.append(script)
            if 'player state' in script:
                is_music = '"Music"' in script
                return True, 'playing' if is_music else 'paused'
            return True, ''

        monkeypatch.setattr(macos_controls, '_run_osascript', fake_run_osascript)

        macos_controls.control_media('play_pause')

        assert 'tell application "Music" to playpause' in scripts

    def test_script_keeps_quotes_around_app_name(self, osascript_calls, running_players):
        running_players.add('Music')

        macos_controls.control_media('previous')

        assert 'tell application "Music" to previous track' in _scripts(osascript_calls)

    def test_falls_back_to_system_media_key_when_no_player_runs(
            self, monkeypatch, osascript_calls, running_players):
        monkeypatch.setattr(macos_controls, 'is_accessibility_trusted', lambda: True)

        result = macos_controls.control_media('play_pause')

        key_call = osascript_calls[-1]
        assert result.success
        assert key_call['javascript'] is True
        assert key_call['arguments'] == [str(macos_controls.NX_KEYTYPE_PLAY)]

    def test_media_key_fallback_reports_missing_accessibility_instead_of_faking_success(
            self, monkeypatch, osascript_calls, running_players):
        monkeypatch.setattr(macos_controls, 'is_accessibility_trusted', lambda: False)

        result = macos_controls.control_media('next')

        assert not result.success
        assert 'Accessibility' in result.message
        assert osascript_calls == []

    def test_stop_without_a_player_fails_instead_of_launching_music(
            self, osascript_calls, running_players):
        result = macos_controls.control_media('stop')

        assert not result.success
        assert osascript_calls == []

    def test_automation_denied_gets_actionable_message(self, monkeypatch, running_players):
        running_players.add('Spotify')
        monkeypatch.setattr(
            macos_controls, '_run_osascript',
            lambda script, **kwargs: (False, 'Not authorized to send Apple events (-1743)')
            if 'to playpause' in script else (True, 'paused'))

        result = macos_controls.control_media('play_pause')

        assert not result.success
        assert 'Automation' in result.message


class TestDarwinDispatch:
    @pytest.fixture(autouse=True)
    def pretend_macos(self, monkeypatch):
        monkeypatch.setattr('actions.cross_platform_action._SYSTEM', 'Darwin')

    @pytest.mark.parametrize('action, command', [
        ('media_play_pause', 'play_pause'),
        ('media_next', 'next'),
        ('media_previous', 'previous'),
        ('media_stop', 'stop'),
    ])
    def test_media_actions_route_to_macos_controls(self, monkeypatch, action, command):
        received = []
        monkeypatch.setattr(
            macos_controls, 'control_media',
            lambda requested: received.append(requested) or macos_controls.ActionResult(True, 'ok'))

        CrossPlatformAction({'action': action}).execute()

        assert received == [command]


def test_no_osascript_shell_strings_remain():
    """The root cause: osascript scripts interpolated into shell strings."""
    action_sources = Path(__file__).resolve().parent.parent / 'actions'
    offenders = [
        path.name
        for path in action_sources.glob('*.py')
        if path.name != 'macos_controls.py'
        and re.search(r'f?[\'"]osascript -e "\{', path.read_text(encoding='utf-8'))
    ]
    assert offenders == []


class TestScreenshot:
    def test_screen_recording_denied_gets_actionable_message(self, monkeypatch):
        denied = type('Completed', (), {
            'returncode': 1, 'stdout': '',
            'stderr': 'could not create image from display 1\n',
        })()
        monkeypatch.setattr(macos_controls.subprocess, 'run', lambda *args, **kwargs: denied)

        result = macos_controls.take_screenshot('/tmp/shot.png')

        assert not result.success
        assert 'Screen' in result.message and 'Recording' in result.message

    def test_path_is_passed_as_one_argument_not_through_a_shell(self, monkeypatch):
        recorded = []
        succeeded = type('Completed', (), {'returncode': 0, 'stdout': '', 'stderr': ''})()
        monkeypatch.setattr(
            macos_controls.subprocess, 'run',
            lambda command, **kwargs: recorded.append(command) or succeeded)

        macos_controls.take_screenshot('/tmp/my "quoted" shot.png')

        assert recorded == [['screencapture', '-x', '/tmp/my "quoted" shot.png']]


class TestHotkeyAccessibilityGuard:
    def test_hotkey_reports_missing_accessibility_on_macos(self, monkeypatch):
        from actions import hotkey_action

        monkeypatch.setattr(hotkey_action.platform, 'system', lambda: 'Darwin')
        monkeypatch.setattr(macos_controls, 'is_accessibility_trusted', lambda: False)

        result = hotkey_action.HotkeyAction({'keys': ['cmd', 'd']}).execute()

        assert not result.success
        assert 'Accessibility' in result.message


class TestVolumeStepsOnEveryPlatform:
    """The step unit bug was not macOS-only: Windows (NirCmd) and Linux (amixer) mis-read it too."""

    @pytest.fixture
    def captured_commands(self, monkeypatch):
        commands = []
        monkeypatch.setattr(
            CrossPlatformAction, '_run_command',
            lambda self, command, shell=True: commands.append(command)
            or macos_controls.ActionResult(True, 'ok'))
        monkeypatch.setattr(CrossPlatformAction, '_check_nircmd', lambda self: True)
        return commands

    def test_windows_percent_step_becomes_nircmd_units(self, monkeypatch, captured_commands):
        monkeypatch.setattr('actions.cross_platform_action._SYSTEM', 'Windows')

        CrossPlatformAction({'action': 'volume_up', 'step': 10}).execute()

        assert captured_commands == ['nircmd.exe changesysvolume 6554']

    def test_windows_nircmd_preset_is_passed_through_unchanged(self, monkeypatch, captured_commands):
        monkeypatch.setattr('actions.cross_platform_action._SYSTEM', 'Windows')

        CrossPlatformAction({'action': 'volume_down', 'step': 2000}).execute()

        assert captured_commands == ['nircmd.exe changesysvolume -2000']

    def test_windows_without_a_step_keeps_its_old_default(self, monkeypatch, captured_commands):
        monkeypatch.setattr('actions.cross_platform_action._SYSTEM', 'Windows')

        CrossPlatformAction({'action': 'volume_up'}).execute()

        assert captured_commands == ['nircmd.exe changesysvolume 1966']

    def test_windows_garbage_step_is_never_pasted_into_the_command(self, monkeypatch, captured_commands):
        monkeypatch.setattr('actions.cross_platform_action._SYSTEM', 'Windows')

        CrossPlatformAction({'action': 'volume_up', 'step': 'x; calc'}).execute()

        assert captured_commands == ['nircmd.exe changesysvolume 1966']

    def test_linux_nircmd_scale_step_is_not_sent_as_2000_percent(self, monkeypatch, captured_commands):
        monkeypatch.setattr('actions.cross_platform_action._SYSTEM', 'Linux')

        CrossPlatformAction({'action': 'volume_up', 'step': 2000}).execute()

        assert captured_commands == ['amixer set Master 3%+']
