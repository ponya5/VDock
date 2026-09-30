"""Tests for the screensaver audio spectrum service (DL-117).

Two seams keep this off real audio hardware:

- the DSP is pure list math — tests feed synthetic magnitude spectra (a
  spike at a bin stands in for a sine), no soundcard/numpy needed;
- the emit throttle is a pure function of (bands, level, live, now, state)
  — the clock is injected.

One numpy end-to-end check (sine -> band) is importorskip-guarded.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services import audio_spectrum as spec  # noqa: E402


@pytest.fixture
def spectrum(monkeypatch):
    """Fresh module state per test — the service keeps module globals."""
    monkeypatch.setattr(spec, '_emit', None)
    monkeypatch.setattr(spec, '_started', False)
    spec.set_enabled(True)
    yield spec
    spec.set_enabled(True)


def band_of(hz, samplerate=spec.SAMPLE_RATE, numframes=spec.CHUNK_FRAMES):
    edges = spec.band_edges()
    return next(i for i in range(spec.NUM_BANDS)
                if edges[i] <= hz < edges[i + 1])


# --- band geometry ---------------------------------------------------------

def test_band_edges_are_log_spaced_across_the_spec():
    edges = spec.band_edges()
    assert len(edges) == spec.NUM_BANDS + 1
    assert edges[0] == pytest.approx(spec.LOW_HZ)
    assert edges[-1] == pytest.approx(spec.HIGH_HZ)
    ratios = [edges[i + 1] / edges[i] for i in range(spec.NUM_BANDS)]
    assert max(ratios) / min(ratios) == pytest.approx(1.0)


def test_bin_ranges_stay_inside_the_rfft():
    for lo, hi in spec.band_bin_ranges(spec.SAMPLE_RATE, spec.CHUNK_FRAMES):
        assert 0 <= lo < hi <= spec.CHUNK_FRAMES // 2 + 1


def test_a_tone_lands_in_its_own_band_only():
    mags = [0.0] * (spec.CHUNK_FRAMES // 2 + 1)
    hz_per_bin = spec.SAMPLE_RATE / spec.CHUNK_FRAMES
    mags[43] = 1.0  # ~1008 Hz
    bands = spec.bands_from_magnitudes(mags)
    hit = band_of(43 * hz_per_bin)
    assert bands[hit] == pytest.approx(1.0)
    assert max(bands[:hit] + bands[hit + 1:]) == 0.0


def test_bands_tolerate_short_magnitude_lists():
    bands = spec.bands_from_magnitudes([0.5] * 4)
    assert len(bands) == spec.NUM_BANDS
    assert bands[0] == pytest.approx(0.5)


# --- normalization ---------------------------------------------------------

def test_amp_to_value_db_curve():
    assert spec.amp_to_value(1.0) == 100
    assert spec.amp_to_value(10 ** (-30 / 20)) == 50
    assert spec.amp_to_value(10 ** (-60 / 20)) == 0
    assert spec.amp_to_value(0.0) == 0
    assert spec.amp_to_value(-1.0) == 0
    assert spec.amp_to_value(2.0) == 100  # clipped, not wrapped


def test_envelope_rises_instantly_and_decays():
    prev = spec.bands_envelope([80] * spec.NUM_BANDS)
    assert prev == [80] * spec.NUM_BANDS
    fell = spec.bands_envelope([0] * spec.NUM_BANDS, prev, decay=0.5)
    assert fell == [40] * spec.NUM_BANDS
    rose = spec.bands_envelope([90] * spec.NUM_BANDS, fell, decay=0.5)
    assert rose == [90] * spec.NUM_BANDS


def test_live_flag_holds_through_quiet_gaps():
    state = {}
    assert spec.update_live(50, 10.0, state) is True
    assert spec.update_live(0, 10.4, state) is True   # inside the hold
    assert spec.update_live(0, 11.5, state) is False  # hold expired


# --- emit throttle (socket contract) ---------------------------------------

def test_first_live_frame_emits():
    state = {}
    bands = [10] * spec.NUM_BANDS
    payload = spec.decide_emit(bands, 40, True, 0.0, state)
    assert payload == {'bands': bands, 'level': 40, 'live': True, 'ts': 0.0}


def test_unchanged_bands_do_not_emit():
    state = {}
    bands = [10] * spec.NUM_BANDS
    spec.decide_emit(bands, 40, True, 0.0, state)
    assert spec.decide_emit(bands, 40, True, 1.0, state) is None


def test_sub_threshold_band_drift_does_not_emit():
    state = {}
    spec.decide_emit([10] * spec.NUM_BANDS, 40, True, 0.0, state)
    moved_one = [11] * spec.NUM_BANDS
    assert spec.decide_emit(moved_one, 40, True, 1.0, state) is None


def test_meaningful_band_move_emits_after_the_interval():
    state = {}
    spec.decide_emit([10] * spec.NUM_BANDS, 40, True, 0.0, state)
    moved = [20] + [10] * (spec.NUM_BANDS - 1)
    payload = spec.decide_emit(moved, 42, True, 0.5, state)
    assert payload['bands'] == moved


def test_emit_rate_is_capped_even_when_bands_move():
    state = {}
    spec.decide_emit([10] * spec.NUM_BANDS, 40, True, 0.0, state)
    moved = [20] * spec.NUM_BANDS
    assert spec.decide_emit(moved, 40, True, 0.02, state) is None
    # The dropped frame leaves state untouched, so the next chunk emits.
    assert spec.decide_emit(moved, 40, True, 0.08, state) is not None


def test_live_flip_to_silence_emits_a_zero_heartbeat_at_once():
    state = {}
    spec.decide_emit([50] * spec.NUM_BANDS, 60, True, 0.0, state)
    payload = spec.decide_emit([3] * spec.NUM_BANDS, 0, False, 0.01, state)
    assert payload == {'bands': [0] * spec.NUM_BANDS, 'level': 0,
                       'live': False, 'ts': 0.01}


def test_silence_heartbeats_every_two_seconds_not_every_chunk():
    state = {}
    spec.decide_emit([0] * spec.NUM_BANDS, 0, False, 0.0, state)
    assert spec.decide_emit([0] * spec.NUM_BANDS, 0, False, 0.5, state) is None
    assert spec.decide_emit([0] * spec.NUM_BANDS, 0, False, 1.9, state) is None
    payload = spec.decide_emit([0] * spec.NUM_BANDS, 0, False, 2.1, state)
    assert payload['live'] is False and payload['bands'] == [0] * spec.NUM_BANDS


def test_startup_silence_announces_itself_once():
    state = {}
    payload = spec.decide_emit([0] * spec.NUM_BANDS, 0, False, 5.0, state)
    assert payload['live'] is False
    assert spec.decide_emit([0] * spec.NUM_BANDS, 0, False, 5.5, state) is None


def test_live_recovery_emits_again():
    state = {}
    spec.decide_emit([40] * spec.NUM_BANDS, 50, True, 0.0, state)
    spec.decide_emit([0] * spec.NUM_BANDS, 0, False, 0.1, state)
    payload = spec.decide_emit([40] * spec.NUM_BANDS, 50, True, 5.0, state)
    assert payload['live'] is True


# --- lifecycle -------------------------------------------------------------

def test_start_spawns_the_worker_once(spectrum):
    spawned = []
    monkey_spawn = lambda target, *a: spawned.append(target)  # noqa: E731
    spectrum.set_spawner(monkey_spawn)
    assert spectrum.start() is True
    assert spectrum.start() is False
    assert spawned == [spectrum._capture_loop]


def test_capture_loop_idles_when_optional_deps_missing(monkeypatch, spectrum):
    monkeypatch.setitem(sys.modules, 'numpy', None)
    monkeypatch.setitem(sys.modules, 'soundcard', None)
    assert spectrum._import_deps() == (None, None)
    spectrum._capture_loop()  # logs once and returns — must not raise or block


def test_propvariant_patch_is_applied_and_idempotent():
    """soundcard<=0.4.6 allocates PROPVARIANT 8 bytes short on x64 — our
    patch over-allocates; it must mark itself and not re-wrap twice."""
    sc = pytest.importorskip('soundcard')
    spec._patch_soundcard_propvariant(sc)
    mf = getattr(sc, 'mediafoundation', None)
    if mf is None:
        pytest.skip('non-Windows soundcard backend')
    assert getattr(mf._PropVariant, '_vdock_patched', False)
    first = mf._PropVariant
    spec._patch_soundcard_propvariant(sc)
    assert mf._PropVariant is first


# --- numpy end-to-end (skipped when the optional dep is absent) ------------

def test_synthetic_sine_lights_the_right_band():
    np = pytest.importorskip('numpy')
    t = np.arange(spec.CHUNK_FRAMES) / spec.SAMPLE_RATE
    for hz in (100.0, 1000.0, 8000.0):
        mono = (0.5 * np.sin(2 * np.pi * hz * t)).astype(np.float32)
        frames = np.stack([mono, mono], axis=1)
        band_amps, peak = spec.chunk_band_amps(np, frames)
        assert band_amps.index(max(band_amps)) == band_of(hz)
        # 8 kHz at 48 kHz samples on exact 60° phase steps, so the observed
        # peak can sit well under the sine's true amplitude.
        assert peak > 0.4


def test_silence_produces_zero_bands_and_level():
    np = pytest.importorskip('numpy')
    frames = np.zeros((spec.CHUNK_FRAMES, 2), dtype=np.float32)
    band_amps, peak = spec.chunk_band_amps(np, frames)
    assert max(band_amps) < 1e-3
    assert spec.amp_to_value(peak) == 0
