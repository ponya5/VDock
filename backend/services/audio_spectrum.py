"""Broadcasts a live output-audio spectrum for the screensaver widget.

The panel has a volume mirror (DL-115) but nothing that shows the machine
*sounding*. This captures the default speaker's WASAPI loopback — the mixed
output stream, no microphone involved — FFTs each chunk into 20 log-spaced
bands (30 Hz–16 kHz) and emits::

    audio_spectrum  { bands: [int x20, 0-100], level: 0-100, live: bool, ts }

Emits are capped at ~14 Hz and only fire when a band moved >=2 or ``live``
flipped; while silent, a ``live: false`` heartbeat goes out every ~2 s so
the widget relaxes to its baseline instead of freezing on the last frame.

Same lifecycle contract as ``volume_monitor``: app.py injects the Socket.IO
broadcast via :func:`set_emitter`, the task spawner via :func:`set_spawner`
(threading-mode Socket.IO drops emits from threads it didn't spawn), and
calls :func:`start` once. :func:`set_enabled` gates the capture loop —
disabling idles the worker without unhooking the module.

``soundcard`` and ``numpy`` are optional integration-time deps, so they are
imported lazily inside the worker; when absent the module logs once and
stays inert rather than raising. The capture runs on its own spawned
thread with its own COM objects — never inside the DL-058 audio worker —
and re-resolves the loopback device on failure so a default-device change
recovers on its own.

The DSP is deliberately kept numpy-free and pure (lists in, values out) so
tests can drive it with synthetic magnitude spectra — no audio device, no
optional deps.
"""
import logging
import math
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger('vdock')

NUM_BANDS = 20
LOW_HZ = 30.0
HIGH_HZ = 16000.0

SAMPLE_RATE = 48000
CHANNELS = 2
CHUNK_FRAMES = 2048

# A full-scale sine (amp 1.0) maps to 100; the -60 dBFS floor maps to 0.
DB_FLOOR = -60.0
# Bars rise instantly and fall with this per-chunk factor (~23 chunks/s):
# the backend smooths, the widget adds its own slower fall on top.
BAND_DECAY = 0.78

MIN_EMIT_INTERVAL = 1.0 / 14.0
BAND_DELTA = 2
HEARTBEAT_SECONDS = 2.0

# `level` is the chunk's peak amplitude on the same -60 dB scale. Audio
# dips below it mid-song all the time, so `live` holds a beat after the
# level drops instead of flapping between bands and heartbeat frames.
LIVE_LEVEL_THRESHOLD = 5
LIVE_HOLD_SECONDS = 0.8

DISABLED_POLL_SECONDS = 0.4
CAPTURE_RETRY_SECONDS = 2.0

# DL-133 — follow-the-audio: the tap is pinned to whichever endpoint is
# actually sounding, not just the default. While the captured stream stays
# silent for SILENCE_BEFORE_PROBE_S we scan every other loopback (one ~43 ms
# chunk each) and move to the loudest when it clears PROBE_SWITCH_PEAK.
# A chunk under PROBE_QUIET_PEAK counts as silence — the observed endpoint
# noise floor is ~0.01, a real mix clears 0.04 without trying.
SILENCE_BEFORE_PROBE_S = 4.0
PROBE_QUIET_PEAK = 0.02
PROBE_SWITCH_PEAK = 0.04


def _default_spawn(target: Callable[..., Any], *args: Any) -> Any:
    """Plain daemon thread, used until app.py supplies the Socket.IO spawner."""
    thread = threading.Thread(target=target, args=args, daemon=True)
    thread.start()
    return thread


_emit: Optional[Callable[[str, Dict[str, Any]], None]] = None
_spawn: Callable[..., Any] = _default_spawn
_enabled = threading.Event()
_enabled.set()  # a started monitor monitors; set_enabled(False) pauses it
_started = False
_lock = threading.Lock()


def set_emitter(emit: Callable[[str, Dict[str, Any]], None]) -> None:
    """Provide the Socket.IO broadcast function."""
    global _emit
    _emit = emit


def set_spawner(spawn: Callable[..., Any]) -> None:
    """Provide the task spawner — socketio.start_background_task in prod."""
    global _spawn
    _spawn = spawn


def set_enabled(flag: bool) -> None:
    """Gate the capture loop. Disabled = idle worker, no device opened."""
    if flag:
        _enabled.set()
    else:
        _enabled.clear()


def is_enabled() -> bool:
    return _enabled.is_set()


def start() -> bool:
    """Spawn the capture loop once. Returns False if already running."""
    global _started
    with _lock:
        if _started:
            return False
        _started = True
    _spawn(_capture_loop)
    return True


# --- pure DSP --------------------------------------------------------------

def band_edges() -> List[float]:
    """NUM_BANDS + 1 log-spaced edges from LOW_HZ to HIGH_HZ."""
    return [LOW_HZ * (HIGH_HZ / LOW_HZ) ** (i / NUM_BANDS)
            for i in range(NUM_BANDS + 1)]


def band_bin_ranges(samplerate: float, numframes: int) -> List[Tuple[int, int]]:
    """FFT-bin [lo, hi) range feeding each band for a given chunk size."""
    bin_hz = samplerate / numframes
    max_bin = numframes // 2 + 1
    ranges = []
    for i in range(NUM_BANDS):
        lo = int(band_edges()[i] / bin_hz)
        hi = max(int(math.ceil(band_edges()[i + 1] / bin_hz)), lo + 1)
        ranges.append((lo, min(hi, max_bin)))
    return ranges


def bands_from_magnitudes(amps: Sequence[float],
                          samplerate: float = SAMPLE_RATE,
                          numframes: int = CHUNK_FRAMES) -> List[float]:
    """Per-band peak of an rfft amplitude list (amplitudes, not power)."""
    out = []
    n = len(amps)
    for lo, hi in band_bin_ranges(samplerate, numframes):
        lo, hi = min(lo, n), min(hi, n)
        out.append(max(amps[lo:hi]) if hi > lo else 0.0)
    return out


def amp_to_value(amp: float) -> int:
    """Amplitude (0..1, sine full-scale) → 0-100 on the -60 dBFS scale."""
    if amp <= 0:
        return 0
    value = int(round((20.0 * math.log10(amp) - DB_FLOOR) / -DB_FLOOR * 100))
    return 0 if value < 0 else (100 if value > 100 else value)


def bands_envelope(values: Sequence[int],
                   prev: Optional[Sequence[int]] = None,
                   decay: float = BAND_DECAY) -> List[int]:
    """Per-band smoothing: jump up instantly, fall by `decay` per chunk."""
    if prev is None:
        prev = [0] * len(values)
    return [max(int(v), int(round(p * decay))) for v, p in zip(values, prev)]


def update_live(level: int, now: float, state: Dict[str, float]) -> bool:
    """Live flag with hold-over: stays true briefly after the level drops."""
    if level >= LIVE_LEVEL_THRESHOLD:
        state['hold_until'] = now + LIVE_HOLD_SECONDS
        return True
    return now < state.get('hold_until', 0.0)


def heartbeat_payload(now: float) -> Dict[str, Any]:
    return {'bands': [0] * NUM_BANDS, 'level': 0, 'live': False, 'ts': now}


def decide_emit(bands: Sequence[int], level: int, live: bool, now: float,
                state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Emit-decision state machine — the socket contract in one place.

    `state` carries last_ts/last_bands/last_live between calls and is only
    updated when a payload is returned, so a rate-dropped frame leaves the
    next frame free to re-qualify (a missed `live` flip self-corrects).
    """
    last_ts = state.get('last_ts')
    last_bands = state.get('last_bands')
    last_live = state.get('last_live')
    payload = None
    if live:
        moved = (last_live is not True or last_bands is None or
                 any(abs(a - b) >= BAND_DELTA
                     for a, b in zip(bands, last_bands)))
        if moved and (last_ts is None or now - last_ts >= MIN_EMIT_INTERVAL):
            payload = {'bands': list(bands), 'level': int(level),
                       'live': True, 'ts': now}
    elif last_live is not False or last_ts is None \
            or now - last_ts >= HEARTBEAT_SECONDS:
        # Silence emits once on the flip (and once at startup), then a
        # heartbeat per HEARTBEAT_SECONDS — flat zeros by contract.
        payload = heartbeat_payload(now)
    if payload is not None:
        state['last_ts'] = now
        state['last_bands'] = list(bands)
        state['last_live'] = live
    return payload


# --- capture worker ---------------------------------------------------------

def _import_deps():
    """Lazy optional deps. Returns (numpy, soundcard) or (None, None)."""
    try:
        import numpy as np
        import soundcard as sc
    except Exception:
        return None, None
    return np, sc


def _patch_soundcard_propvariant(sc: Any) -> None:
    """Work around soundcard<=0.4.6's undersized PROPVARIANT on Windows.

    Its cdef models PROPVARIANT as vt + 3 reserved WORDs + a void* (16
    bytes), but a real x64 PROPVARIANT is 24 bytes — the union must fit a
    DECIMAL. ``_PropVariant`` therefore CoTaskMemAlloc's 16 bytes and every
    ``IPropertyStore::GetValue`` (device ``name``/``channels`` reads —
    unavoidable on the loopback path) overruns the heap by 8 bytes; the
    process then dies of heap corruption at some later unrelated allocation
    (observed: crash inside GetDevicePeriod on the first silent chunk).

    Over-allocating is safe — fields are read by offset, and zeroing keeps
    PropVariantClear a no-op (vt=VT_EMPTY) if __del__ runs before GetValue.
    Same class of fix as DL-115's comtypes ``__del__`` patch.
    """
    try:
        mf = getattr(sc, 'mediafoundation', None)  # Windows backend only
        if mf is None or getattr(getattr(mf, '_PropVariant', None),
                                 '_vdock_patched', False):
            return
        ffi, ole32 = mf._ffi, mf._ole32

        class _PropVariant:
            _vdock_patched = True

            def __init__(self) -> None:
                raw = ole32.CoTaskMemAlloc(64)
                ffi.buffer(raw, 64)[:] = b'\x00' * 64
                self.ptr = ffi.cast('PROPVARIANT *', raw)

            def __del__(self) -> None:
                try:
                    ole32.PropVariantClear(self.ptr)
                except Exception:
                    pass

        mf._PropVariant = _PropVariant
    except Exception as e:
        logger.warning('Audio spectrum: PROPVARIANT patch failed: %s', e)


def chunk_band_amps(np: Any, frames: Any,
                    samplerate: float = SAMPLE_RATE) -> Tuple[List[float], float]:
    """Recorded chunk → (per-band amplitudes, mono peak amplitude).

    Hann window + coherent-gain correction so a full-scale sine reads ~1.0.
    """
    mono = np.asarray(frames, dtype=np.float32)
    if mono.ndim > 1:
        mono = mono.mean(axis=1)
    n = int(mono.shape[0])
    if n == 0:
        return [0.0] * NUM_BANDS, 0.0
    window = np.hanning(n)
    amps = np.abs(np.fft.rfft(mono * window)) / (n * float(window.mean()))
    peak = float(np.max(np.abs(mono)))
    return bands_from_magnitudes(amps.tolist(), samplerate, n), peak


def _default_loopback(sc: Any) -> Any:
    """The loopback mic mirroring the current default speaker."""
    speaker = sc.default_speaker()
    try:
        return sc.get_microphone(id=str(speaker.name), include_loopback=True)
    except Exception:
        for mic in sc.all_microphones(include_loopback=True):
            if getattr(mic, 'isloopback', False) and speaker.name in mic.name:
                return mic
        raise


def _all_loopbacks(sc: Any) -> List[Any]:
    """Every WASAPI loopback mic — one per render endpoint."""
    try:
        return [mic for mic in sc.all_microphones(include_loopback=True)
                if getattr(mic, 'isloopback', False)]
    except Exception:
        return []


def _probe_peak(np: Any, mic: Any) -> float:
    """One short loopback read → that endpoint's current peak (0 on error)."""
    try:
        with mic.recorder(samplerate=SAMPLE_RATE,
                          channels=CHANNELS) as recorder:
            frames = recorder.record(numframes=CHUNK_FRAMES)
        arr = np.asarray(frames, dtype=np.float32)
        return float(np.max(np.abs(arr))) if arr.size else 0.0
    except Exception:
        return 0.0


def _loudest_loopback(sc: Any, np: Any,
                      exclude_name: Optional[str] = None) -> Tuple[Any, float]:
    """(mic, peak) of the loudest loopback other than `exclude_name`."""
    best, best_peak = None, 0.0
    for mic in _all_loopbacks(sc):
        if exclude_name is not None \
                and getattr(mic, 'name', None) == exclude_name:
            continue
        peak = _probe_peak(np, mic)
        if peak > best_peak:
            best, best_peak = mic, peak
    return best, best_peak


def _next_capture_mic(sc: Any, np: Any, current: Any) -> Any:
    """Silent-tap follow: where the tap should live next, or None to stay.

    A clearly-sounding *other* endpoint wins (app routed off-default);
    otherwise we drop back to the current default so a device swap mid-
    session still lands on the right tap. Returns None when the current
    tap is already the best available — the caller keeps recording.
    """
    current_name = getattr(current, 'name', None)
    best, peak = _loudest_loopback(sc, np, exclude_name=current_name)
    if best is not None and peak >= PROBE_SWITCH_PEAK:
        return best
    try:
        default = _default_loopback(sc)
    except Exception:
        return None
    if getattr(default, 'name', None) != current_name:
        return default
    return None


def _emit_payload(payload: Dict[str, Any]) -> None:
    if _emit is None:
        return
    try:
        _emit('audio_spectrum', payload)
    except Exception as e:  # pragma: no cover - transport
        logger.error('Could not broadcast spectrum: %s', e)


def _capture_loop() -> None:
    np, sc = _import_deps()
    if np is None:
        logger.info('Audio spectrum idle: numpy/soundcard not installed')
        return
    _patch_soundcard_propvariant(sc)
    emit_state: Dict[str, Any] = {}
    live_state: Dict[str, float] = {}
    prev_bands = [0] * NUM_BANDS
    last_device_error: Optional[str] = None
    mic: Any = None
    while True:
        if not _enabled.is_set():
            _enabled.wait(DISABLED_POLL_SECONDS)
            continue
        if mic is None:
            try:
                mic = _default_loopback(sc)
            except Exception as e:
                # Device churn is routine (headset swap); the same failure
                # logs once, not every retry.
                if str(e) != last_device_error:
                    logger.warning('Audio spectrum: no loopback device: %s', e)
                    last_device_error = str(e)
                time.sleep(CAPTURE_RETRY_SECONDS)
                continue
        try:
            with mic.recorder(samplerate=SAMPLE_RATE,
                              channels=CHANNELS) as recorder:
                logger.info('Audio spectrum capturing on %s',
                            getattr(mic, 'name', 'loopback'))
                last_device_error = None
                last_loud_at = time.time()
                last_probe_at = 0.0
                while _enabled.is_set():
                    frames = recorder.record(numframes=CHUNK_FRAMES)
                    band_amps, peak = chunk_band_amps(np, frames)
                    values = [amp_to_value(a) for a in band_amps]
                    prev_bands = bands_envelope(values, prev_bands)
                    level = amp_to_value(peak)
                    now = time.time()
                    live = update_live(level, now, live_state)
                    payload = decide_emit(prev_bands, level, live, now,
                                          emit_state)
                    if payload is not None:
                        _emit_payload(payload)
                    if peak > PROBE_QUIET_PEAK:
                        last_loud_at = now
                    elif now - max(last_loud_at, last_probe_at) \
                            >= SILENCE_BEFORE_PROBE_S:
                        # Silent tap — maybe the sound lives on another
                        # endpoint (off-default app, device swap). Probing
                        # costs a fraction of a second of flat output and
                        # only ever runs while there's nothing to show.
                        last_probe_at = now
                        nxt = _next_capture_mic(sc, np, mic)
                        if nxt is not None:
                            logger.info('Audio spectrum following output '
                                        '%s -> %s',
                                        getattr(mic, 'name', '?'),
                                        getattr(nxt, 'name', '?'))
                            mic = nxt
                            break
        except Exception as e:
            # Recorder died (device unplugged, endpoint rebuild) — reopen on
            # the next pass; forgetting the mic re-resolves the default.
            logger.warning('Audio spectrum capture interrupted: %s', e)
            mic = None
            time.sleep(CAPTURE_RETRY_SECONDS)
