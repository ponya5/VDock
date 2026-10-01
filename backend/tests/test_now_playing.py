"""Now Playing (DL-116): emit-on-change monitor logic and the REST surface.

The SMTC read itself is a module seam (``now_playing._fetch_snapshot``) —
these tests inject a scripted fake so no Windows media session or winsdk
install is needed.
"""
import time

import pytest
from flask import Flask

from config import Config
import services.now_playing as now_playing
from routes.now_playing import now_playing_bp


@pytest.fixture(autouse=True)
def clean_state(monkeypatch, tmp_path):
    """Isolate module state: art cache, snapshot, availability probe."""
    monkeypatch.setattr(Config, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(now_playing, '_available_cache', None)
    monkeypatch.setattr(now_playing, '_art_mime', None)
    monkeypatch.setattr(now_playing, '_emit', None)
    monkeypatch.setattr(now_playing, '_latest', None)
    yield


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(now_playing_bp)
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def emitted(monkeypatch):
    events = []
    monkeypatch.setattr(now_playing, '_emit',
                        lambda name, payload: events.append((name, payload)))
    return events


# ---------------------------------------------------------------------------
# Fake SMTC reader helpers
# ---------------------------------------------------------------------------

def _track_payload(**overrides):
    payload = {
        'playing': True,
        'title': 'Song',
        'artist': 'Artist',
        'album': 'Album',
        'source_app': 'spotify.exe',
        'has_art': False,
        'duration_s': 200.0,
        'position_s': 10.0,
        'ts': time.time(),
    }
    payload.update(overrides)
    return payload


def _empty_payload():
    return {'playing': False, 'title': '', 'artist': '', 'album': '',
            'source_app': '', 'site': '', 'has_art': False,
            'ts': time.time()}


def _emit_key(payload):
    return (payload['title'], payload['artist'], payload['album'],
            payload['source_app'], payload['playing'])


def _fake_reader(results):
    """Scripted _fetch_snapshot replacement: list items may be
    ``(emit_key, payload, art)`` tuples or an Exception to raise."""
    reads = iter(results)

    def read(_previous_track_key):
        item = next(reads)
        if isinstance(item, Exception):
            raise item
        return item
    return read


# ---------------------------------------------------------------------------
# Monitor emit-on-change
# ---------------------------------------------------------------------------

def test_first_read_emits_then_identical_reads_stay_quiet(monkeypatch, emitted):
    payload = _track_payload()
    monkeypatch.setattr(now_playing, '_fetch_snapshot', _fake_reader([
        (_emit_key(payload), dict(payload), now_playing.ART_UNCHANGED),
        (_emit_key(payload), dict(payload), now_playing.ART_UNCHANGED),
    ]))
    state = now_playing._poll_state()
    now_playing._poll_once(state)
    now_playing._poll_once(state)

    assert [name for name, _ in emitted] == ['now_playing']
    assert emitted[0][1]['title'] == 'Song'
    assert emitted[0][1]['playing'] is True


def test_track_change_and_play_flip_each_emit(monkeypatch, emitted, tmp_path):
    p1 = _track_payload()
    p2 = _track_payload(title='Next Song', position_s=0.0)
    p3 = _track_payload(title='Next Song', playing=False, position_s=0.0)
    monkeypatch.setattr(now_playing, '_fetch_snapshot', _fake_reader([
        (_emit_key(p1), dict(p1), (b'\xff\xd8\xffjpeg', 'image/jpeg')),
        (_emit_key(p2), dict(p2), (b'\x89PNG\r\n\x1a\npng', 'image/png')),
        (_emit_key(p3), dict(p3), now_playing.ART_UNCHANGED),
    ]))
    state = now_playing._poll_state()
    for _ in range(3):
        now_playing._poll_once(state)

    assert [p['title'] for _, p in emitted] == ['Song', 'Next Song', 'Next Song']
    assert emitted[2][1]['playing'] is False

    # Art follows the track: jpeg replaced by png, kept across the pause flip.
    art = tmp_path / now_playing.ART_FILENAME
    assert art.read_bytes().startswith(b'\x89PNG')
    assert emitted[2][1]['has_art'] is True


def test_nothing_playing_emits_empty_payload_and_clears_art(
        monkeypatch, emitted, tmp_path):
    payload = _track_payload()
    empty = _empty_payload()
    monkeypatch.setattr(now_playing, '_fetch_snapshot', _fake_reader([
        (_emit_key(payload), dict(payload), (b'\xff\xd8\xffjpeg', 'image/jpeg')),
        (('', '', '', '', False), dict(empty), None),
    ]))
    state = now_playing._poll_state()
    now_playing._poll_once(state)
    now_playing._poll_once(state)

    assert emitted[1][1] == empty
    assert not (tmp_path / now_playing.ART_FILENAME).exists()
    assert now_playing.latest_track() is None
    assert now_playing.snapshot()['playing'] is False


def test_position_jump_emits_even_when_track_is_same(monkeypatch, emitted):
    p1 = _track_payload(position_s=10.0)
    p2 = _track_payload(position_s=80.0)  # a seek, not normal playback drift
    key = _emit_key(p1)
    monkeypatch.setattr(now_playing, '_fetch_snapshot', _fake_reader([
        (key, dict(p1), now_playing.ART_UNCHANGED),
        (key, dict(p2), now_playing.ART_UNCHANGED),
    ]))
    state = now_playing._poll_state()
    now_playing._poll_once(state)
    now_playing._poll_once(state)

    assert [p['position_s'] for _, p in emitted] == [10.0, 80.0]


def test_normal_playback_drift_does_not_emit(monkeypatch, emitted):
    p1 = _track_payload(position_s=10.0)
    p2 = _track_payload(position_s=11.5)  # ≈ one poll interval forward
    key = _emit_key(p1)
    monkeypatch.setattr(now_playing, '_fetch_snapshot', _fake_reader([
        (key, dict(p1), now_playing.ART_UNCHANGED),
        (key, dict(p2), now_playing.ART_UNCHANGED),
    ]))
    state = now_playing._poll_state()
    now_playing._poll_once(state)
    now_playing._poll_once(state)

    assert len(emitted) == 1


def test_failed_read_keeps_last_state_and_emits_nothing(monkeypatch, emitted):
    payload = _track_payload()
    key = _emit_key(payload)
    monkeypatch.setattr(now_playing, '_fetch_snapshot', _fake_reader([
        (key, dict(payload), now_playing.ART_UNCHANGED),
        RuntimeError('SMTC gone'),
        (key, dict(payload), now_playing.ART_UNCHANGED),
    ]))
    state = now_playing._poll_state()
    now_playing._poll_once(state)
    now_playing._poll_once(state)   # raises inside, swallowed like the loop does
    now_playing._poll_once(state)

    assert len(emitted) == 1
    assert now_playing.snapshot()['title'] == 'Song'


def test_available_reflects_cached_probe(monkeypatch):
    monkeypatch.setattr(now_playing, '_available_cache', False)
    assert now_playing.available() is False
    monkeypatch.setattr(now_playing, '_available_cache', True)
    assert now_playing.available() is True


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

def test_route_reports_available_track(client, monkeypatch):
    monkeypatch.setattr(now_playing, '_available_cache', True)
    monkeypatch.setattr(now_playing, '_latest', _track_payload())

    data = client.get('/api/now-playing').get_json()
    assert data['success'] is True
    assert data['available'] is True
    assert data['track']['title'] == 'Song'
    assert data['track']['source_app'] == 'spotify.exe'


def test_route_track_null_when_nothing_plays(client, monkeypatch):
    monkeypatch.setattr(now_playing, '_available_cache', True)
    monkeypatch.setattr(now_playing, '_latest', _empty_payload())

    data = client.get('/api/now-playing').get_json()
    assert data == {'success': True, 'available': True, 'track': None}


def test_route_unavailable_without_smtc(client, monkeypatch):
    monkeypatch.setattr(now_playing, '_available_cache', False)
    monkeypatch.setattr(now_playing, '_latest', None)

    data = client.get('/api/now-playing').get_json()
    assert data == {'success': True, 'available': False, 'track': None}


def test_art_route_404_then_serves_cached_file(client, tmp_path):
    assert client.get('/api/now-playing/art').status_code == 404

    png = b'\x89PNG\r\n\x1a\nfakepngdata'
    (tmp_path / now_playing.ART_FILENAME).write_bytes(png)
    response = client.get('/api/now-playing/art')
    assert response.status_code == 200
    assert response.mimetype == 'image/png'  # sniffed — _art_mime unset
    assert response.data == png


def test_art_route_uses_remembered_mimetype(client, tmp_path, monkeypatch):
    (tmp_path / now_playing.ART_FILENAME).write_bytes(b'opaque-bytes')
    monkeypatch.setattr(now_playing, '_art_mime', 'image/webp')

    response = client.get('/api/now-playing/art')
    assert response.status_code == 200
    assert response.mimetype == 'image/webp'


# ---------------------------------------------------------------------------
# Art-cache hardening (regression: poll thread died on (None, mime) art tuple)
# ---------------------------------------------------------------------------

def test_poll_survives_empty_art_tuple(monkeypatch, emitted):
    """Thumbnail streams that open but yield no bytes used to surface as
    ``art=(None, mime)`` → ``_replace_art`` called ``write_bytes(None)`` →
    TypeError escaped ``_poll_once`` and killed the whole poll thread."""
    stale = now_playing.art_path()
    stale.write_bytes(b'old-cover')
    payload = _track_payload()
    monkeypatch.setattr(now_playing, '_fetch_snapshot', _fake_reader([
        (_emit_key(payload), dict(payload), (None, 'image/png')),
    ]))
    state = now_playing._poll_state()
    now_playing._poll_once(state)  # must not raise
    assert not stale.exists()      # stale cover dropped, not kept
    assert emitted and emitted[-1][1]['has_art'] is False


def test_loop_survives_unexpected_tick_error(monkeypatch, emitted):
    """Anything escaping ``_poll_once`` must be logged and the thread must
    keep polling — the loop is the last line of defence."""
    payload = _track_payload()
    monkeypatch.setattr(now_playing, '_smtc_supported', lambda: True)
    monkeypatch.setattr(now_playing, '_fetch_snapshot', _fake_reader([
        (_emit_key(payload), dict(payload), now_playing.ART_UNCHANGED),
    ]))
    calls = {'n': 0}
    real_poll = now_playing._poll_once

    def flaky(state):
        calls['n'] += 1
        if calls['n'] == 1:
            raise TypeError('simulated tick crash')
        real_poll(state)

    monkeypatch.setattr(now_playing, '_poll_once', flaky)

    def stop_after_two(_interval):
        if calls['n'] >= 2:
            raise KeyboardInterrupt  # BaseException — exits _loop cleanly
    monkeypatch.setattr(now_playing.time, 'sleep', stop_after_two)

    with pytest.raises(KeyboardInterrupt):
        now_playing._loop(0)
    assert calls['n'] == 2                 # crashed tick did not end the loop
    assert emitted and emitted[-1][1]['title'] == 'Song'


# ---------------------------------------------------------------------------
# Site detection — browser sessions attributed to a site via window titles
# ---------------------------------------------------------------------------

def test_detect_site_known_app_skips_window_scan(monkeypatch):
    monkeypatch.setattr(now_playing, '_visible_window_titles',
                        lambda: pytest.fail('should not scan'))
    assert now_playing.detect_site('Spotify.exe', 'Song') == 'spotify'
    assert now_playing.detect_site('com.google.YouTubeMusic', 'V') == 'youtube'


def test_detect_site_browser_matches_title_window(monkeypatch):
    monkeypatch.setattr(now_playing, '_visible_window_titles', lambda: [
        'Some Video Title - YouTube - Google Chrome',
        'Inbox - Gmail',
    ])
    assert now_playing.detect_site('chrome.exe', 'Some Video Title') \
        == 'youtube'


def test_detect_site_browser_weak_match_on_known_site(monkeypatch):
    # SMTC title doesn't appear in any window title (e.g. reformatted) —
    # a known-site window still attributes the browser's session.
    monkeypatch.setattr(now_playing, '_visible_window_titles', lambda: [
        'Live: cat cam 24/7 - Twitch',
        'VS Code - main.py',
    ])
    assert now_playing.detect_site('msedge.exe', 'stream title x') == 'twitch'


def test_detect_site_browser_no_known_site_returns_empty(monkeypatch):
    monkeypatch.setattr(now_playing, '_visible_window_titles', lambda: [
        'Inbox - Gmail - Google Chrome',
    ])
    assert now_playing.detect_site('chrome.exe', 'A video') == ''


def test_detect_site_non_browser_app_returns_empty(monkeypatch):
    monkeypatch.setattr(now_playing, '_visible_window_titles',
                        lambda: ['Something - YouTube - Google Chrome'])
    assert now_playing.detect_site('SomePlayer.exe', 'A video') == ''


def test_site_is_stamped_once_per_track(monkeypatch, emitted):
    calls = {'n': 0}

    def fake_detect(app, title):
        calls['n'] += 1
        return 'youtube' if 'chrome' in app else ''
    monkeypatch.setattr(now_playing, 'detect_site', fake_detect)

    p1 = _track_payload(source_app='chrome.exe', title='Video A')
    p2 = _track_payload(source_app='chrome.exe', title='Video B',
                        position_s=0.0)
    monkeypatch.setattr(now_playing, '_fetch_snapshot', _fake_reader([
        (_emit_key(p1), dict(p1), now_playing.ART_UNCHANGED),
        (_emit_key(p1), dict(p1), now_playing.ART_UNCHANGED),
        (_emit_key(p2), dict(p2), now_playing.ART_UNCHANGED),
    ]))
    state = now_playing._poll_state()
    for _ in range(3):
        now_playing._poll_once(state)

    assert calls['n'] == 2          # once per track, not per emit
    assert emitted[0][1]['site'] == 'youtube'
    assert emitted[1][1]['site'] == 'youtube'
