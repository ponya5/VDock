"""macOS system-audio source for the spectrum service.

macOS has no WASAPI-style loopback, so a tiny Swift helper
(``backend/native/vdock_audio_tap.swift``) taps the mixed output with a Core
Audio process tap (macOS 14.2+) and streams mono float32 samples on stdout:
a 4-byte little-endian sample rate, then raw samples forever.

This module owns the helper's lifecycle: find (or compile) the binary, spawn
it, read fixed-size chunks, and kill it on close. It imports nothing
platform-specific, so the framing logic is testable on any OS with a fake
helper executable.
"""
import logging
import os
import shutil
import struct
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, List, Optional

logger = logging.getLogger('vdock')

HELPER_NAME = 'vdock-audio-tap'
HELPER_SOURCE_NAME = 'vdock_audio_tap.swift'
HEADER_BYTES = 4
BYTES_PER_SAMPLE = 4
COMPILE_TIMEOUT_S = 180
STDERR_TAIL_BYTES = 400

_NATIVE_DIR = Path(__file__).resolve().parents[1] / 'native'
_compile_lock = threading.Lock()


class TapError(RuntimeError):
    """The helper is missing, failed to start, or stopped streaming."""


def user_helper_path() -> Path:
    """Where an on-demand build is cached (writable even when packaged)."""
    return Path.home() / '.vdock' / 'bin' / HELPER_NAME


def find_helper() -> Optional[Path]:
    """The helper binary: bundled/pre-built first, then the cached build."""
    candidates: List[Path] = [
        _NATIVE_DIR / HELPER_NAME,
        _NATIVE_DIR / 'bin' / HELPER_NAME,
        user_helper_path(),
    ]
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def _helper_is_stale(binary: Path, source: Path) -> bool:
    return source.is_file() and source.stat().st_mtime > binary.stat().st_mtime


def compile_helper() -> Path:
    """Build the helper with swiftc into the per-user cache."""
    source = _NATIVE_DIR / HELPER_SOURCE_NAME
    swiftc = shutil.which('swiftc')
    if not source.is_file() or swiftc is None:
        raise TapError(
            'audio tap helper is not built and swiftc is unavailable '
            '(install Xcode Command Line Tools: xcode-select --install)')
    target = user_helper_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [swiftc, '-O', str(source), '-o', str(target)],
        capture_output=True, text=True, timeout=COMPILE_TIMEOUT_S)
    if result.returncode != 0:
        raise TapError('swiftc failed: ' + result.stderr.strip()[-STDERR_TAIL_BYTES:])
    logger.info('Audio spectrum: built macOS tap helper at %s', target)
    return target


def ensure_helper() -> Path:
    """A runnable helper, compiling it once if only the source exists."""
    with _compile_lock:
        found = find_helper()
        source = _NATIVE_DIR / HELPER_SOURCE_NAME
        if found is not None and not (
                found == user_helper_path() and _helper_is_stale(found, source)):
            return found
        return compile_helper()


class MacAudioTap:
    """One running helper process and its chunked sample stream."""

    def __init__(self, helper: Optional[Path] = None) -> None:
        self._helper = helper
        self._process: Optional[subprocess.Popen] = None
        self.samplerate = 0

    def open(self) -> int:
        """Spawn the helper and read its sample-rate header."""
        if sys.platform == 'win32':
            raise TapError('macOS audio tap is not available on Windows')
        helper = self._helper or ensure_helper()
        self._process = subprocess.Popen(
            [str(helper)], stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        header = self._read_exactly(HEADER_BYTES)
        self.samplerate = struct.unpack('<I', header)[0]
        if self.samplerate <= 0:
            self.close()
            raise TapError('helper reported an invalid sample rate')
        return self.samplerate

    def read_samples(self, np: Any, numframes: int) -> Any:
        """Block until ``numframes`` mono float32 samples have arrived."""
        raw = self._read_exactly(numframes * BYTES_PER_SAMPLE)
        return np.frombuffer(raw, dtype='<f4').astype(np.float32)

    def _read_exactly(self, size: int) -> bytes:
        process = self._process
        if process is None or process.stdout is None:
            raise TapError('audio tap is not open')
        chunks: List[bytes] = []
        remaining = size
        while remaining > 0:
            try:
                piece = process.stdout.read(remaining)
            except ValueError:
                raise TapError('audio tap closed')
            if not piece:
                raise TapError(self._exit_reason())
            chunks.append(piece)
            remaining -= len(piece)
        return b''.join(chunks)

    def _exit_reason(self) -> str:
        process = self._process
        if process is None:
            return 'audio tap is not open'
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
        stderr_text = ''
        if process.stderr is not None:
            stderr_text = process.stderr.read(STDERR_TAIL_BYTES).decode(
                'utf-8', 'replace').strip()
        return stderr_text or 'audio tap helper exited (code %s)' % process.returncode

    def close(self) -> None:
        """Stop the helper; also unblocks a reader stuck in read_samples."""
        process, self._process = self._process, None
        if process is None:
            return
        try:
            process.terminate()
            process.wait(timeout=2)
        except Exception:
            process.kill()
        for stream in (process.stdout, process.stderr):
            if stream is not None:
                stream.close()
