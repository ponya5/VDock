"""DL-007 — macOS media: now-playing from Spotify/Music, Spotify Connect volume,
and a Mute button that toggles like Windows."""
import os
import sys
from unittest import mock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from actions import macos_controls  # noqa: E402
from services import now_playing  # noqa: E402

SEP = '\x1f'


def _osascript_result(stdout, returncode=0):
    return mock.Mock(returncode=returncode, stdout=stdout, stderr='')


# ---------------------------------------------------------------------------
# now playing
# ---------------------------------------------------------------------------

@pytest.fixture
def players(mocker):
    """name -> osascript stdout; a name missing from the dict is not running."""
    outputs = {}

    def run(argv, **kwargs):
        if argv[0] == 'pgrep':
            return mock.Mock(returncode=0 if argv[-1] in outputs else 1)
        name = 'Spotify' if '"Spotify"' in argv[2] else 'Music'
        return _osascript_result(outputs[name] + '\n')

    mocker.patch.object(now_playing.subprocess, 'run', side_effect=run)
    mocker.patch.object(now_playing, '_download_art', return_value=(b'img', 'image/jpeg'))
    return outputs


def _fields(state, title, art='https://i.scdn.co/image/abc', duration='248730', position='131,5'):
    return SEP.join([state, title, 'Peter Gabriel', 'Scratch My Back', duration, position, art])


def test_spotify_connect_track_is_reported(players):
    players['Spotify'] = _fields('playing', 'Heroes')
    key, payload, art = now_playing._fetch_macos(('', '', '', ''))
    assert key == ('Heroes', 'Peter Gabriel', 'Scratch My Back', 'Spotify', True)
    assert payload['playing'] is True
    assert payload['duration_s'] == pytest.approx(248.73)
    # The decimal comma some locales print must not zero the position.
    assert payload['position_s'] == pytest.approx(131.5)
    assert payload['has_art'] is True and art == (b'img', 'image/jpeg')
    assert 'art_url' not in payload


def test_same_track_keeps_cached_art(players):
    players['Spotify'] = _fields('paused', 'Heroes')
    key, _payload, art = now_playing._fetch_macos(
        ('Heroes', 'Peter Gabriel', 'Scratch My Back', 'Spotify'))
    assert art is now_playing.ART_UNCHANGED


def test_the_playing_player_wins(players):
    players['Spotify'] = _fields('paused', 'Heroes')
    players['Music'] = _fields('playing', 'Biko', art='', duration='300000')
    _key, payload, art = now_playing._fetch_macos(('', '', '', ''))
    assert payload['source_app'] == 'Music' and payload['title'] == 'Biko'
    assert art is None and payload['has_art'] is False


def test_art_only_from_spotify_cdn(players, mocker):
    players['Spotify'] = _fields('playing', 'Heroes', art='file:///etc/passwd')
    _key, payload, art = now_playing._fetch_macos(('', '', '', ''))
    assert art is None and payload['has_art'] is False


def test_nothing_running_or_stopped_is_the_empty_payload(players):
    key, payload, art = now_playing._fetch_macos(('', '', '', ''))
    assert payload['title'] == '' and payload['playing'] is False and art is None
    players['Spotify'] = 'stopped'
    _key, payload, _art = now_playing._fetch_macos(('', '', '', ''))
    assert payload['title'] == ''


def test_macos_is_supported(monkeypatch):
    monkeypatch.setattr(now_playing, '_available_cache', None)
    monkeypatch.setattr(now_playing.sys, 'platform', 'darwin')
    assert now_playing.available() is True


# ---------------------------------------------------------------------------
# Spotify Connect volume + mute toggle
# ---------------------------------------------------------------------------

@pytest.fixture
def osascript(mocker):
    calls = []
    state = {'remote': None, 'muted': 'false', 'output': 40}

    def run(script, javascript=False, arguments=None):
        calls.append((script, arguments))
        if script == 'get volume settings':
            return True, (f"output volume:{state['output']}, input volume:50, "
                          f"alert volume:100, output muted:{state['muted']}")
        return True, ''

    mocker.patch.object(macos_controls, '_run_osascript', side_effect=run)
    mocker.patch.object(macos_controls, 'remote_spotify_volume',
                        side_effect=lambda: state['remote'])
    macos_controls._remote_volume_before_mute = None
    return calls, state


def test_volume_goes_to_spotify_when_it_plays_on_another_device(osascript):
    calls, state = osascript
    state['remote'] = 60
    result = macos_controls.change_output_volume(-10)
    assert result.success and result.data['value'] == 50
    script, arguments = calls[-1]
    assert 'tell application "Spotify" to set sound volume' in script
    assert arguments == ['50']
    assert not any(c[0].startswith('set volume output') for c in calls)


def test_local_playback_keeps_system_volume(osascript):
    calls, _state = osascript
    result = macos_controls.change_output_volume(10)
    assert result.success
    assert calls[-1][0] == 'set volume output volume 50'


def test_slider_sets_spotify_or_system_volume(osascript):
    calls, state = osascript
    assert macos_controls.set_output_volume(30).data['value'] == 30
    assert calls[-1][0] == 'set volume output volume 30'
    state['remote'] = 80
    macos_controls.set_output_volume(30)
    assert calls[-1][1] == ['30']


def test_mute_button_toggles_like_windows(osascript):
    calls, state = osascript
    assert macos_controls.toggle_output_muted().message == 'Muted'
    state['muted'] = 'true'
    assert macos_controls.toggle_output_muted().message == 'Unmuted'
    assert calls[-1][0] == 'set volume without output muted'


def test_remote_mute_remembers_the_level(osascript):
    calls, state = osascript
    state['remote'] = 70
    macos_controls.toggle_output_muted()
    assert calls[-1][1] == ['0']
    state['remote'] = 0
    macos_controls.toggle_output_muted()
    assert calls[-1][1] == ['70']


def test_remote_detection_needs_an_idle_mac_output(mocker):
    mocker.patch.object(macos_controls, '_is_app_running', return_value=True)
    mocker.patch.object(macos_controls, '_is_player_playing', return_value=True)
    mocker.patch.object(macos_controls, '_run_osascript', return_value=(True, '64'))
    mocker.patch.object(macos_controls, '_output_device_running', return_value=False)
    assert macos_controls.remote_spotify_volume() == 64
    # Audio is coming out of the Mac: local playback, system volume applies.
    macos_controls._output_device_running.return_value = True
    assert macos_controls.remote_spotify_volume() is None
    # Unknown output state: never guess remote.
    macos_controls._output_device_running.return_value = None
    assert macos_controls.remote_spotify_volume() is None


def test_volume_mute_action_toggles_on_macos(mocker):
    from actions import cross_platform_action
    mocker.patch.object(cross_platform_action, '_SYSTEM', 'Darwin')
    toggle = mocker.patch.object(macos_controls, 'toggle_output_muted',
                                 return_value=mock.Mock(success=True))
    cross_platform_action.CrossPlatformAction({'action': 'volume_mute'}).execute()
    toggle.assert_called_once()
