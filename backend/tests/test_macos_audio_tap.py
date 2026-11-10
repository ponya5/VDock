"""macOS spectrum source: helper framing, lifecycle and the shared processor.

No audio hardware or Swift toolchain is involved: a throwaway executable
script plays the helper and speaks its wire format (4-byte little-endian
sample rate, then mono float32 samples).
"""
import math
import os
import stat
import struct
import sys
import textwrap

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

np = pytest.importorskip('numpy')

from services import audio_spectrum as spec  # noqa: E402
from services import macos_audio_tap as tap_module  # noqa: E402

pytestmark = pytest.mark.skipif(
    sys.platform == 'win32', reason='fake helper is a POSIX shebang script')

SAMPLE_RATE = 48000


def _write_helper(tmp_path, body: str):
    helper = tmp_path / 'fake-helper'
    helper.write_text('#!%s\n%s' % (sys.executable, textwrap.dedent(body)))
    helper.chmod(helper.stat().st_mode | stat.S_IXUSR)
    return helper


def _sine_helper(tmp_path, frequency_hz: float, amplitude: float = 0.5):
    return _write_helper(tmp_path, '''
        import math, struct, sys
        rate = %d
        sys.stdout.buffer.write(struct.pack('<I', rate))
        sys.stdout.buffer.flush()
        index = 0
        while True:
            block = b''.join(
                struct.pack('<f', %f * math.sin(2 * math.pi * %f * (index + i) / rate))
                for i in range(2048))
            index += 2048
            sys.stdout.buffer.write(block)
            sys.stdout.buffer.flush()
    ''' % (SAMPLE_RATE, amplitude, frequency_hz))


def test_open_reads_sample_rate_and_chunks_have_requested_length(tmp_path):
    tap = tap_module.MacAudioTap(_sine_helper(tmp_path, 440.0))
    try:
        assert tap.open() == SAMPLE_RATE
        samples = tap.read_samples(np, spec.CHUNK_FRAMES)
        assert samples.shape == (spec.CHUNK_FRAMES,)
        assert samples.dtype == np.float32
        assert float(np.max(np.abs(samples))) == pytest.approx(0.5, abs=0.01)
    finally:
        tap.close()


def test_helper_failure_surfaces_its_stderr_message(tmp_path):
    helper = _write_helper(tmp_path, '''
        import sys
        sys.stderr.write('vdock-audio-tap: cannot create system audio tap (OSStatus 1)\\n')
        sys.exit(1)
    ''')
    tap = tap_module.MacAudioTap(helper)
    with pytest.raises(tap_module.TapError, match='cannot create system audio tap'):
        tap.open()
    tap.close()


def test_stream_ending_mid_chunk_raises_instead_of_returning_short_data(tmp_path):
    helper = _write_helper(tmp_path, '''
        import struct, sys
        sys.stdout.buffer.write(struct.pack('<I', 48000) + b'\\x00' * 100)
    ''')
    tap = tap_module.MacAudioTap(helper)
    tap.open()
    with pytest.raises(tap_module.TapError):
        tap.read_samples(np, spec.CHUNK_FRAMES)
    tap.close()


def test_close_stops_the_helper_and_is_idempotent(tmp_path):
    tap = tap_module.MacAudioTap(_sine_helper(tmp_path, 440.0))
    tap.open()
    process = tap._process
    tap.close()
    tap.close()
    assert process.poll() is not None


def test_read_after_close_raises(tmp_path):
    tap = tap_module.MacAudioTap(_sine_helper(tmp_path, 440.0))
    tap.open()
    tap.close()
    with pytest.raises(tap_module.TapError):
        tap.read_samples(np, spec.CHUNK_FRAMES)


def test_missing_helper_and_compiler_gives_actionable_error(monkeypatch, tmp_path):
    monkeypatch.setattr(tap_module, 'find_helper', lambda: None)
    monkeypatch.setattr(tap_module.shutil, 'which', lambda name: None)
    with pytest.raises(tap_module.TapError, match='xcode-select --install'):
        tap_module.ensure_helper()


def test_processor_emits_frames_whose_loudest_band_matches_the_tone(monkeypatch):
    emitted = []
    monkeypatch.setattr(spec, '_emit', lambda event, payload: emitted.append(payload))
    processor = spec._ChunkProcessor(np)
    frames = np.array(
        [0.5 * math.sin(2 * math.pi * 1000.0 * i / SAMPLE_RATE)
         for i in range(spec.CHUNK_FRAMES)], dtype=np.float32)

    for _ in range(6):
        processor.process(frames, SAMPLE_RATE)

    live_frames = [payload for payload in emitted if payload['live']]
    assert live_frames, 'a 1 kHz tone must produce live frames'
    bands = live_frames[-1]['bands']
    edges = spec.band_edges()
    tone_band = next(i for i in range(spec.NUM_BANDS) if edges[i] <= 1000.0 < edges[i + 1])
    assert bands.index(max(bands)) == tone_band
