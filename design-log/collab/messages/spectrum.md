# W2 spectrum — notes

## CRITICAL: soundcard 0.4.6 heap-corruption bug + shipped patch

Stock `soundcard` 0.4.6 crashes the Python process (0xc0000374 heap
corruption, exit 127, no traceback) during `record()` — guaranteed when
the audio stream is silent, intermittent otherwise. Root cause: its cffi
cdef declares `PROPVARIANT` 16 bytes; real x64 size is 24 (DECIMAL in the
union). `_PropVariant` allocates 16 via `CoTaskMemAlloc`, so every
`IPropertyStore::GetValue` (device `.name`/`.channels`) overruns the heap
by 8 bytes and a later allocation crashes — looks random, isn't.

`services/audio_spectrum.py` ships `_patch_soundcard_propvariant()` which
replaces `_PropVariant` with a 64-byte zeroed alloc before touching any
device (applied inside the worker, guarded + idempotent). Verified live:
full record loop ran clean, silent + tone.

**If soundcard is ever upgraded**, re-verify whether the upstream bug is
fixed — the patch is harmless either way but worth revisiting. Any other
feature touching `soundcard` (W1 does not — it uses winsdk) needs the same
patch or it will crash the backend.

## Integration wiring (orchestrator)

- `backend/venv` already contains `soundcard==0.4.6` and `numpy==2.5.3` —
  add both to `requirements.txt`.
- `app.py` under `__main__`, same as `volume_monitor`:
  ```python
  from services import audio_spectrum
  audio_spectrum.set_emitter(lambda ev, p: socketio.emit(ev, p))
  audio_spectrum.set_spawner(socketio.start_background_task)
  audio_spectrum.set_enabled(sys.platform == 'win32')
  audio_spectrum.start()
  ```
- Widget: mount `components/screensaver/SpectrumWidget.vue` under id
  `spectrum`, title "Spectrum", default-visible decision is yours. Natural
  size 240×~130 px; scales fine via `.ss-pos` transform.
- Non-Windows: no loopback enumeration → module idles (retries quietly,
  logs once per distinct failure); widget shows "Audio capture
  unavailable" after a 3 s grace. That's the honest-state contract, fine.

## Contract conformance

- Emits `audio_spectrum` exactly per `contracts/socket-events.md`:
  `{bands: int[20] 0-100, level: int, live: bool, ts}`; ≤14 Hz, ≥2 delta
  or live flip; heartbeat `{bands:[0]*20, level:0, live:false, ts}` ~2 s
  when silent AND once at startup (lets the widget distinguish silent from
  absent backend).
- `live` has 0.8 s hold-over so quiet gaps mid-song don't flap.
- `lastSeenAt`-staleness is handled widget-side (4 s) — a dead backend
  can't freeze bars in the live state.

## For W7 (conditional rules consumer)

`audio_spectrum` payloads are `{bands, level, live, ts}` as contracted;
`services/audioSpectrum.ts` exposes them as a readonly reactive
`{bands, level, live, lastSeenAt}` — import `useAudioSpectrum()` or read
the socket directly. Level is dB-scaled (−60 dBFS → 0, FS → 100).
