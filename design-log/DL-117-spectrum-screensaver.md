# DL-117 — Winamp-style audio spectrum screensaver widget

## Intent

The screensaver (DL-003, DL-013) is the deck's idle face — clock, weather,
markets, headlines. FEATURE-RESEARCH §2b calls for the missing classic: a
live audio spectrum analyzer in the Winamp mold, fed by whatever the PC is
actually playing. WASAPI loopback gives us the mixed output stream without
microphones, drivers, or config — capture it, FFT it into ~20 log-spaced
bands, and drive thin green→red bars with peak-hold caps on the panel.

## Frictions

- **No capture machinery exists.** The only audio code is the Core Audio
  volume path (DL-058), which lives on a dedicated COM-apartment worker —
  the spectrum capture must NOT join it (its own thread, its own COM).
- **Optional deps.** `soundcard` + `numpy` are orchestrator-installed during
  integration, so the module must lazy-import inside the worker and idle
  silently when they're absent (never raise at import or start).
- **Emit discipline.** Flask-SocketIO drops emits from threads it didn't
  spawn (DL-052) → `socketio.start_background_task` via the `set_spawner`
  seam, same contract as `volume_monitor`. At ~23 chunks/s raw, emits must
  be throttled to ~14 Hz and only fire on meaningful change; silence gets a
  ~2 s `live:false` heartbeat so the widget can relax instead of freezing
  on the last frame.
- **Honest states.** Widget must distinguish "backend never sent anything"
  (unavailable) from "capture alive but silent" (idle flat baseline).

## Mechanical Translation

### Backend — `services/audio_spectrum.py`

- Same lifecycle as `volume_monitor`: module-level `set_emitter` /
  `set_spawner` / `start()` (spawn-once guard), plus `set_enabled(bool)`
  gating the capture loop (orchestrator enables on Windows).
- Worker thread: lazy `import numpy` / `import soundcard`; missing → one
  log line, thread exits (module stays inert). Loop resolves the default
  speaker's loopback (`sc.get_microphone(id=str(sc.default_speaker().name),
  include_loopback=True)`, `all_microphones` fallback), opens
  `mic.recorder(samplerate=48000)`, and reads `record(numframes=2048)`
  chunks (~23/s). Capture errors → close, sleep, re-resolve (device churn).
- DSP kept as pure, numpy-free functions so tests need no audio deps:
  `band_bin_ranges` / `bands_from_magnitudes` (20 log-spaced bands,
  30 Hz–16 kHz, max-per-band), `amp_to_value` (fixed −60 dBFS floor →
  int 0–100), `bands_envelope` (per-band rise-instantly/fall-decay
  smoothing), `level_from_peak` / `LIVE_LEVEL_THRESHOLD`, and
  `decide_emit(bands, level, live, now, state)` implementing the emit
  contract: ≤14 Hz, emit only when any band moved ≥2 or `live` flipped,
  heartbeat `{bands:[0]*20, level:0, live:false, ts}` every ~2 s while
  silent (including one at startup so the widget learns capture is alive).
- The worker maps `np.rfft` magnitudes (Hann-windowed, coherent-gain
  corrected) through those functions and emits `audio_spectrum`
  `{bands:[int×20], level, live, ts}` per `contracts/socket-events.md`.

### Frontend

- `services/audioSpectrum.ts`: reactive singleton subscribing
  `audio_spectrum` → `{bands, level, live, lastSeenAt}`; `useAudioSpectrum()`
  lazily attaches the socket listener (pattern per `agentState.ts`).
- `components/screensaver/SpectrumWidget.vue`: `<script setup lang="ts">`,
  optional ignored `layoutEdit` prop. Canvas ~252×96 inside `.ss-section`
  chrome (small-caps "SPECTRUM" head + hairline). ~15 fps rAF loop: per-bar
  fall smoothing on top of the backend's envelope, per-bar peak-hold cap
  that lingers then drops slower than the bars, 2–4 px gaps, one shared
  bottom-anchored green→yellow→red gradient (short bars read green, tall
  bars tip red — the Winamp look). `live:false` → bars relax to a dim flat
  baseline; `lastSeenAt === null` → `.ss-empty`-style "audio capture
  unavailable". rAF cancelled in `onUnmounted`.

## Core Loop

App plays audio → WASAPI loopback streams the mix → 2048-frame chunks →
rfft → 20 log bands → dB-normalize + decay → `audio_spectrum` emit (≤14 Hz,
on change) → widget bars breathe; silence → `live:false` heartbeat → bars
settle to the baseline.

## Design Proof

- `pytest tests/test_audio_spectrum.py` — band edges/bin mapping on
  synthetic magnitude spectra (sine-equivalent spike lands in the right
  band, neighbors empty), dB→value curve, decay envelope, and the full
  emit-throttle matrix (rate cap, ≥2 delta, live flip, silent heartbeat)
  with an injected clock — no soundcard/numpy required.
- Module import + `start()` on a deps-missing host idles instead of
  raising (asserted via fake spawner + `_import_deps()` seam).
- Live look verified post-integration by orchestrator (deps + widget
  mount are theirs).

## Implementation Results

Implemented and verified — including a live end-to-end capture on the dev
machine's real WASAPI loopback.

**Built**

- `backend/services/audio_spectrum.py` — `set_emitter` / `set_spawner` /
  `start` (spawn-once) / `set_enabled` contract mirroring `volume_monitor`.
  Capture runs on its own spawned thread, resolving the default speaker's
  loopback (`get_microphone(id=str(default_speaker().name),
  include_loopback=True)` with an `all_microphones` fallback) and reading
  2048-frame chunks @ 48 kHz. Capture failures close, log-once-per-change,
  and re-resolve the device — headset/default-device churn self-heals.
  Deps lazy-import in the worker only; absent deps → one info line, module
  inert.
- DSP is pure numpy-free list math (testable seam): `band_edges` /
  `band_bin_ranges` (20 log-spaced bands 30 Hz–16 kHz),
  `bands_from_magnitudes` (per-band peak), `amp_to_value` (−60 dBFS floor →
  0–100), `bands_envelope` (rise-instantly / fall ×0.78 per chunk),
  `update_live` (0.8 s hold-over so `live` doesn't flap on quiet
  passages), `decide_emit` (≤14 Hz, ≥2 band delta or live flip, ~2 s
  silent heartbeat — incl. one at startup). Worker-side `chunk_band_amps`
  does the numpy-only part (mono mix, Hann + coherent-gain correction,
  rfft) then hands lists to the pure layer.
- `frontend/src/services/audioSpectrum.ts` — lazy reactive singleton,
  `useAudioSpectrum()` → readonly `{bands, level, live, lastSeenAt}`,
  values clamped on ingest.
- `frontend/src/components/screensaver/SpectrumWidget.vue` — canvas at
  ~15 fps rAF: 20 thin bars, single bottom-anchored
  green→yellow→orange→red gradient (color = height, the Winamp read),
  segmented bars (1 px carve every 4 px), pale peak caps that hold 350 ms
  then fall slower than bars, `live:false` → bars relax to a dim 2 px
  baseline, never-arrived → grace 3 s "Waiting for audio…" → "Audio
  capture unavailable" `.ss-empty` state. Payloads older than 4 s count as
  stale (a dead backend can't leave bars frozen). Own `.ss-section`
  chrome copy, ResizeObserver + DPR-aware canvas, rAF cancelled on
  unmount.
- `backend/tests/test_audio_spectrum.py` — 21 tests, all green; numpy is
  `importorskip`-gated for the two end-to-end DSP checks.

**Deviation / found bug (important):** `soundcard` 0.4.6 hard-crashes the
*process* on this machine — `0xc0000374` heap corruption, exit 127, no
traceback — inside `record()` whenever the stream is silent, and
intermittently elsewhere. Root cause found: `mediafoundation.py.h`
declares `PROPVARIANT` as 16 bytes; the real x64 size is 24 (union holds
DECIMAL). `_PropVariant` `CoTaskMemAlloc`s 16 and every
`IPropertyStore::GetValue` (`.name`/`.channels` — unavoidable when picking
the loopback) overruns the heap by 8 bytes; the next allocation pays for
it. Fix shipped inside the service: `_patch_soundcard_propvariant()`
replaces `_PropVariant` with a 64-byte zeroed allocation before any device
access — field-offset reads unaffected, verified stable. Without this,
enabling the feature would intermittently kill the whole backend.

**Verified live** (dev machine, Realtek loopback, real sine through
`speaker.player`):

- Silent PC → startup `live:false` heartbeat, then ~2 s cadence, correct
  `{bands:[0]*20, level:0, live:false, ts}` shape.
- 2200 Hz tone → `live:true`, `level` 84–86, band 13 (1783–2442 Hz) at
  ~73–75 with decay tail — band mapping correct; ~11 emits over ~2 s of
  steady tone (emit-on-change working under the cap); clean return to
  heartbeats after the tone.
- `pytest tests/test_audio_spectrum.py`: 21/21 pass; full backend suite
  1058/1058; `vue-tsc --noEmit` clean.

**Integration notes for orchestrator**

- Wire in `app.py` under `__main__` like `volume_monitor`:
  `audio_spectrum.set_emitter(socketio.emit)`,
  `set_spawner(socketio.start_background_task)`, `set_enabled(True)` on
  Windows, `start()`. `set_enabled(False)` pauses capture if a screensaver
  toggle warrants it later.
- `soundcard` + `numpy` were already installed in `backend/venv`
  (soundcard 0.4.6, numpy 2.5.3); add both to `requirements.txt`.
- Mount `SpectrumWidget` under widget id `spectrum`, title "Spectrum".
- Non-Windows: loopback enumeration likely finds nothing → module idles
  with one log line (retries quietly); widget shows unavailable. Sound.

## Follow-up: numpy requirement relaxed to a range

`numpy==2.5.3` (the version found in the dev venv) broke `setup.bat` option 1
on Python 3.11: numpy 2.5 requires Python 3.12+, while setup promises 3.9+.
Now `numpy>=1.26,<3` (Windows-only, as before), so pip resolves the newest
release the installed Python supports — 2.0.x on 3.9, 2.2.x on 3.10, 2.4.x on
3.11, 2.5.x on 3.12+. The capture path only uses `asarray`, `hanning`,
`fft.rfft`, `abs`, `max`, which are stable across that range.
