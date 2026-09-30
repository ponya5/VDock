"""Polls Windows SMTC for the now-playing track and broadcasts changes.

What the Windows media flyout shows — title, artist, album, play state,
position, source app — is exposed system-wide through SMTC
(``GlobalSystemMediaTransportControlsSessionManager``). This monitor reads
it every ~1.5 s and emits ``now_playing`` so every connected client can
mirror it::

    now_playing  { playing, title, artist, album, source_app,
                   position_s?, duration_s?, has_art, ts }

Only identity changes emit — a new track, a play/pause flip, or a mid-track
seek; position ticks alone stay quiet and widgets extrapolate locally. The
first successful read always emits, and moving to "nothing playing" emits
the empty payload. Album art is fetched once per track change and cached to
``DATA_DIR/now_playing_art.bin`` for ``GET /api/now-playing/art`` — the
socket payload only carries ``has_art``.

A WinRT binding (``winsdk`` or Microsoft's ``winrt-*`` wheels) is optional:
without one (or off Windows) the module still loads and the loop idles;
:func:`available` then reports False so the REST endpoint and widget can
show their honest unsupported state. The binding's APIs are async, so the
worker thread drives them on a private thread-local asyncio loop — asyncio
objects must never cross threads.

Same spawn contract as ``volume_monitor``/``job_runner``: emits from
threads Socket.IO did not spawn are dropped in threading mode, so app.py
must drive :func:`start` via ``socketio.start_background_task``.
"""
import asyncio
import logging
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from config import Config

logger = logging.getLogger('vdock')

POLL_INTERVAL_SECONDS = 1.5
ART_FILENAME = 'now_playing_art.bin'
# A position jump larger than the poll interval plus this margin means the
# user seeked — worth an emit so widgets re-anchor their progress bar.
SEEK_TOLERANCE_SECONDS = 2.0
MAX_ART_BYTES = 16 * 1024 * 1024

#: _fetch_snapshot returns this sentinel for its art slot when the track did
#: not change: the cached art file still belongs to the current track.
ART_UNCHANGED = object()

#: Shape of the "nothing plays" payload (contract: socket-events.md).
_EMPTY_TRACK_KEY: Tuple[str, str, str, str] = ('', '', '', '')


def _default_spawn(target: Callable[..., Any], *args: Any) -> Any:
    """Plain daemon thread, used until app.py supplies the Socket.IO spawner."""
    thread = threading.Thread(target=target, args=args, daemon=True)
    thread.start()
    return thread


_emit: Optional[Callable[[str, Dict[str, Any]], None]] = None
_spawn: Callable[..., Any] = _default_spawn
_started = False
_lock = threading.Lock()

# Last emitted payload (may be the "nothing plays" one) and the cached art's
# content-type — read by the route, written only on the poll thread.
_state_lock = threading.Lock()
_latest: Optional[Dict[str, Any]] = None
_art_mime: Optional[str] = None

# None until the first probe: winsdk importable AND running on Windows.
_available_cache: Optional[bool] = None
_smtc_imports: Optional[Tuple[Any, Any, Any]] = None
_thread = threading.local()


def set_emitter(emit: Callable[[str, Dict[str, Any]], None]) -> None:
    """Provide the Socket.IO broadcast function."""
    global _emit
    _emit = emit


def set_spawner(spawn: Callable[..., Any]) -> None:
    """Provide the task spawner — socketio.start_background_task in prod."""
    global _spawn
    _spawn = spawn


def start(interval: float = POLL_INTERVAL_SECONDS) -> bool:
    """Spawn the poll loop once. Returns False if already running."""
    global _started
    with _lock:
        if _started:
            return False
        _started = True
    _spawn(_loop, interval)
    return True


# ---------------------------------------------------------------------------
# Snapshot the route reads
# ---------------------------------------------------------------------------

def available() -> bool:
    """True when SMTC can be read on this host (Windows + a WinRT binding)."""
    return _smtc_supported()


def snapshot() -> Optional[Dict[str, Any]]:
    """Last emitted payload, including the 'nothing plays' empty one."""
    with _state_lock:
        return dict(_latest) if _latest is not None else None


def latest_track() -> Optional[Dict[str, Any]]:
    """The current track payload, or None when nothing plays — the REST
    contract maps the empty payload to ``track: null``."""
    with _state_lock:
        latest = dict(_latest) if _latest is not None else None
    if not latest or not (latest.get('title') or latest.get('artist')):
        return None
    return latest


def art_path() -> Path:
    # Resolved per call: tests repoint Config.DATA_DIR, and a restart must
    # still serve the file a previous process left behind.
    return Config.DATA_DIR / ART_FILENAME


def art_mime() -> str:
    """Content-Type recorded at extraction, falling back to magic-byte
    sniffing so a backend restart still serves the cached file correctly."""
    if _art_mime:
        return _art_mime
    return _sniff_mime(art_path()) or 'image/jpeg'


# ---------------------------------------------------------------------------
# Poll loop
# ---------------------------------------------------------------------------

def _poll_state(interval: float = POLL_INTERVAL_SECONDS) -> Dict[str, Any]:
    """Mutable cursor for the poll loop: last emitted key, last track
    identity (drives once-per-track art extraction), last position (seek
    detection) and the last logged error (log throttling)."""
    return {'emit_key': None, 'track_key': _EMPTY_TRACK_KEY, 'position': None,
            'interval': interval, 'error': None}


def _loop(interval: float) -> None:
    state = _poll_state(interval)
    while True:
        try:
            if _smtc_supported():
                _poll_once(state)
        except Exception:
            # Last-resort guard: a single bad tick (e.g. an art-cache edge
            # case outside _poll_once's own try) must never kill this
            # thread silently — log and keep polling.
            logger.exception('Now-playing poll tick failed')
        time.sleep(interval)


def _poll_once(state: Dict[str, Any]) -> None:
    """One poll tick: fetch, emit on change, maintain the art cache.

    Fetch failures keep the previous state and emit nothing — matching
    volume_monitor's "failed reads emit nothing" semantics. Identical
    errors log once so a permanently failing SMTC doesn't spam the log.
    """
    global _latest
    try:
        emit_key, payload, art = _fetch_snapshot(state['track_key'])
    except Exception as e:
        if str(e) != state['error']:
            state['error'] = str(e)
            logger.error('Now-playing read failed: %s', e)
        return
    state['error'] = None

    position = payload.get('position_s')
    seeked = bool(
        payload.get('playing')
        and position is not None
        and state['position'] is not None
        and abs(position - state['position'] - state['interval'])
            > SEEK_TOLERANCE_SECONDS
    )
    if position is not None:
        state['position'] = position

    if emit_key == state['emit_key'] and not seeked:
        return
    state['emit_key'] = emit_key
    state['track_key'] = _track_key(payload)

    if art is not ART_UNCHANGED:
        _replace_art(art)
    # The payload reflects the file on disk, not the fetch's hope — a
    # thumbnail that failed extraction must not claim has_art.
    payload['has_art'] = art_path().is_file()

    with _state_lock:
        _latest = payload
    if _emit is not None:
        try:
            _emit('now_playing', payload)
        except Exception as e:  # pragma: no cover - transport
            logger.error('Could not broadcast now_playing: %s', e)


def _track_key(payload: Dict[str, Any]) -> Tuple[str, str, str, str]:
    """Track identity for the once-per-change art extraction."""
    return (payload.get('title', ''), payload.get('artist', ''),
            payload.get('album', ''), payload.get('source_app', ''))


def _replace_art(art: Optional[Tuple[bytes, Optional[str]]]) -> None:
    """Write the new track's art, or remove the file when the new track has
    none — a stale file would serve the previous album's cover while the
    payload already says has_art:false."""
    global _art_mime
    path = art_path()
    if art is None:
        _art_mime = None
        try:
            path.unlink(missing_ok=True)
        except OSError as e:
            logger.warning('Could not remove stale album art: %s', e)
        return
    data, mime = art
    try:
        if not data:
            # Extraction produced a tuple but no bytes — same as "no art":
            # drop any stale file rather than writing a zero-length cache
            # (and never let a bad blob type kill the poll loop again).
            path.unlink(missing_ok=True)
            _art_mime = None
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix('.tmp')
        tmp.write_bytes(data)
        tmp.replace(path)  # readers never see a half-written image
        _art_mime = mime
    except Exception as e:
        # Art is decorative — an unexpected blob type or disk error must
        # degrade to "no art", never propagate into the poll loop.
        logger.warning('Could not cache album art: %s', e)
        _art_mime = None


def _sniff_mime(path: Path) -> Optional[str]:
    try:
        with open(path, 'rb') as f:
            head = f.read(12)
    except OSError:
        return None
    if head.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    if head.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    if head[:6] in (b'GIF87a', b'GIF89a'):
        return 'image/gif'
    if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
        return 'image/webp'
    return None


# ---------------------------------------------------------------------------
# SMTC fetch — the replaceable seam (tests inject a fake reader here)
# ---------------------------------------------------------------------------

def _smtc_supported() -> bool:
    """Probe once, cache forever: winsdk won't appear mid-process."""
    global _available_cache
    if _available_cache is None:
        try:
            _import_smtc()
            _available_cache = sys.platform == 'win32'
        except Exception:
            _available_cache = False
    return _available_cache


def _import_smtc() -> Tuple[Any, Any, Any]:
    """Lazy SMTC binding import — the module must load without the package.

    Two Python bindings expose the identical WinRT surface: ``winsdk`` (older,
    no cp313 wheel) and Microsoft's ``winrt-*`` namespace wheels. Try winsdk
    first so an environment that has it keeps working, then fall back to
    winrt — which is what VDock ships in requirements.
    """
    global _smtc_imports
    if _smtc_imports is None:
        try:
            from winsdk.windows.media.control import (
                GlobalSystemMediaTransportControlsSessionManager,
                GlobalSystemMediaTransportControlsSessionPlaybackStatus,
            )
            from winsdk.windows.storage.streams import DataReader
        except ImportError:
            from winrt.windows.media.control import (
                GlobalSystemMediaTransportControlsSessionManager,
                GlobalSystemMediaTransportControlsSessionPlaybackStatus,
            )
            from winrt.windows.storage.streams import DataReader
        _smtc_imports = (
            GlobalSystemMediaTransportControlsSessionManager,
            GlobalSystemMediaTransportControlsSessionPlaybackStatus,
            DataReader,
        )
    return _smtc_imports


def _run_on_worker_loop(coro: Any) -> Any:
    """Drive a coroutine on this thread's private asyncio loop.

    ``asyncio.run`` per poll would create+teardown a loop every 1.5 s; one
    persistent loop per worker thread is cheaper and just as isolated —
    asyncio objects still never cross threads.
    """
    loop = getattr(_thread, 'loop', None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        _thread.loop = loop
    return loop.run_until_complete(coro)


def _fetch_snapshot(
    previous_track_key: Tuple[str, str, str, str],
) -> Tuple[Tuple[Any, ...], Dict[str, Any], Any]:
    """One SMTC read. Returns ``(emit_key, payload, art)`` where ``art`` is
    ``ART_UNCHANGED`` (same track), ``None`` (track changed, no art — caller
    deletes the cache), or ``(bytes, mime)`` from a fresh extraction.

    This is the module seam tests replace; it raises on failure and the
    caller keeps the previous state.
    """
    return _run_on_worker_loop(_fetch_async(previous_track_key))


async def _fetch_async(
    previous_track_key: Tuple[str, str, str, str],
) -> Tuple[Tuple[Any, ...], Dict[str, Any], Any]:
    session_manager_cls, playback_status_cls, _ = _import_smtc()
    manager = await session_manager_cls.request_async()
    session = manager.get_current_session()
    if session is None:
        # art=None (not ART_UNCHANGED) even when the last state was already
        # empty: the emit path then deletes any stale file a previous run
        # left behind, keeping the file in agreement with has_art:false.
        return ('', '', '', '', False), _empty_payload(), None

    props = await session.try_get_media_properties_async()
    title = str(getattr(props, 'title', '') or '')
    artist = str(getattr(props, 'artist', '') or '')
    album = str(getattr(props, 'album_title', '') or '')
    source_app = str(getattr(session, 'source_app_user_model_id', '') or '')

    # Missing playback info means "not playing" — never a fatal read.
    playing = False
    try:
        info = session.get_playback_info()
        playing = getattr(info, 'playback_status', None) == \
            playback_status_cls.PLAYING
    except Exception:
        pass

    position_s, duration_s = _timeline(session)

    track_key = (title, artist, album, source_app)
    thumbnail = getattr(props, 'thumbnail', None)
    art: Any = ART_UNCHANGED
    if track_key != previous_track_key:
        if thumbnail is not None:
            art = await _read_thumbnail(thumbnail)
        else:
            art = None

    payload: Dict[str, Any] = {
        'playing': playing,
        'title': title,
        'artist': artist,
        'album': album,
        'source_app': source_app,
        'has_art': thumbnail is not None,  # refined to disk truth on emit
        'ts': time.time(),
    }
    if duration_s > 0:
        payload['duration_s'] = duration_s
    if position_s is not None:
        payload['position_s'] = position_s
    return (title, artist, album, source_app, playing), payload, art


def _empty_payload() -> Dict[str, Any]:
    return {
        'playing': False,
        'title': '',
        'artist': '',
        'album': '',
        'source_app': '',
        'has_art': False,
        'ts': time.time(),
    }


def _timeline(session: Any) -> Tuple[Optional[float], float]:
    """(position_s|None, duration_s) — best-effort; some apps report neither."""
    try:
        timeline = session.get_timeline_properties()
        if timeline is None:
            return None, 0.0
        duration_s = _timespan_seconds(getattr(timeline, 'end_time', None))
        position = _timespan_seconds(getattr(timeline, 'position', None))
        return (position if position > 0 else None), duration_s
    except Exception:
        return None, 0.0


def _timespan_seconds(value: Any) -> float:
    """WinRT TimeSpan surfaces as timedelta; some builds hand back raw
    100-ns ticks — accept both."""
    if value is None:
        return 0.0
    total = getattr(value, 'total_seconds', None)
    if callable(total):
        return float(total())
    if isinstance(value, (int, float)):
        return float(value) / 10_000_000
    return 0.0


async def _read_thumbnail(
    thumbnail_ref: Any,
) -> Tuple[Optional[bytes], Optional[str]]:
    """thumbnail stream → (bytes, mime). Art is decorative: every failure
    path degrades to (None, None), never a raised poll."""
    try:
        stream = await thumbnail_ref.open_read_async()
        size = int(getattr(stream, 'size', 0) or 0)
        if size <= 0 or size > MAX_ART_BYTES:
            return None, None
        mime = str(getattr(stream, 'content_type', '') or '') or None
        *_, data_reader_cls = _import_smtc()
        reader = data_reader_cls(stream)
        try:
            await reader.load_async(size)
            try:
                data = bytes(reader.read_bytes(size))
            except TypeError:
                # winrt-* bindings fill a caller-provided system.Array
                # instead of returning bytes. The array must be sized up
                # front — Array('B') is empty, so read_bytes fills nothing
                # and bytes(arr) yields b'' (which then poisoned the art
                # cache write with TypeError and killed the poll loop).
                try:
                    from winsdk.system import Array
                except ImportError:
                    from winrt.system import Array
                arr = Array('B', size)
                reader.read_bytes(arr)
                data = bytes(arr)
        finally:
            for closable in (reader, stream):
                try:
                    closable.close()
                except Exception:
                    pass
        return (data or None), mime
    except Exception as e:
        logger.warning('Album art read failed: %s', e)
        return None, None
