# DL-133 — Spectrum endpoint-follow, bigger media card, Shuffle saver type

## Problem

Four user-visible issues on the screensaver:

1. **Spectrum sits flat during music.** Live probing showed Socket.IO
   frames arrive but carry all-zero bands while Spotify plays. Diagnosis
   (see below) — the capture is pinned to the *default* output endpoint's
   loopback; when an app's stream renders somewhere else (or the default
   device changes while the recorder is open), the tap reads silence.
2. **Now Playing card too small.** The bottom media card reads as a
   pill-sized accessory at panel scale — the user wants it clearly larger,
   while the visualizer stays the majority of the screen.
3. **Screensaver type selector buried + mislabeled.** The "When idle,
   show" select sits inside the second panel below "Activation"; the user
   wants it first at the top, named **Screensaver Type**.
4. **New type: Shuffle.** A `shuffle` screensaver type that rotates the
   active saver view (widgets → spectrum → stats → …) every N minutes.

## Spectrum diagnosis

Evidence gathered on the live machine (branch `research_upgrade1`):

- Socket.IO probe: `audio_spectrum` frames arrive (~14 Hz contract),
  `live: false`, all bands 0 — transport is healthy.
- `soundcard.default_speaker()` → "Speakers (Realtek(R) Audio)"; its
  loopback captured a `winsound` sine at peak ~0.98 → DSP path healthy.
- pycaw: `Spotify.exe` session **Active** on the same default endpoint,
  volume 1.0, unmuted — yet the endpoint peak meter reads ~0.01 (noise
  floor) and all five active endpoints' loopbacks read ~0.
- Conclusion: the app's stream is not entering any local shared-mode mix
  (Connect remote playback or hardware offload). No loopback can see it.

So today's flat saver is *honest* — there is no local audio to draw — but
the architecture is fragile: a pinned-default tap silently misses audio on
any other endpoint. The fix is **follow-the-audio** capture.

## Design decisions

### Backend — endpoint-following loopback (`services/audio_spectrum.py`)

- While the current stream stays silent (`chunk peak < ~0.005` sustained
  for `SILENCE_BEFORE_PROBE_S`), probe every other loopback endpoint —
  one short record each (~43 ms) — and adopt the loudest when it clears
  `PROBE_SWITCH_PEAK` (well above the ~0.01 noise floor).
- If nothing is loud, fall back to the *default* loopback — covers the
  default device changing while we were parked on a non-default tap.
- Probing costs a fraction of a second of flat output and only happens
  while silent; live streams are never interrupted.
- Emit contract unchanged: `bands/level/live/ts` — still honest zeros
  when nothing renders anywhere.

### Frontend — Shuffle saver type

- `screensaverStyle` gains `'shuffle'`; new persisted key
  `screensaverShuffleMinutes` (default 5, options 1/5/10/30).
- Rotation lives in `ScreenSaver.vue` (mounts only while the saver runs —
  the timer can never leak into the dashboard): `effectiveStyle` ref,
  random start, `pickNextSaverType` avoids immediate repeats, re-arms on
  interval/type change, cleared on unmount. Saved value stays `'shuffle'`
  — rotation is ephemeral, never rewrites settings. `layoutEdit` still
  forces widgets.
- Type metadata (`services/screensaverTypes.ts`): id list + labels +
  picker — one source for SettingsView and ScreenSaver.

### Settings layout

- New first panel `#ss-type` ("Screensaver type") above `#ss-activation`
  holds the renamed select + the shuffle interval row (visible only when
  Shuffle is picked). `#ss-spectrum` keeps spectrum-specific options.
- "Not in use" notes updated: widget-background/widgets notes fire for
  `spectrum`/`stats` only (Shuffle still shows widgets); spectrum-options
  note fires for `widgets`/`stats`.
- Factory default stays `'widgets'`; a missing/invalid persisted value
  falls back to it.

### Bigger now-playing card (`SpectrumStage.vue`)

- `.has-track` card: 400 → 560 px max width, art ~104 → ~128 px,
  title/artist/buttons scaled up ~30 %. Bottom-center anchor kept; total
  footprint stays ≲ 30 % of screen height — spectrum remains dominant.

## Files

- `backend/services/audio_spectrum.py` — probe + follow logic
- `backend/tests/test_audio_spectrum.py` — resolver/follow unit tests
- `frontend/src/services/screensaverTypes.ts` — NEW: type registry
- `frontend/src/stores/settings.ts` — `shuffle` union +
  `screensaverShuffleMinutes` persistence
- `frontend/src/components/ScreenSaver.vue` — effective-style rotation
- `frontend/src/components/screensaver/SpectrumStage.vue` — card sizing
- `frontend/src/views/SettingsView.vue` — panel reorder, labels, notes
- `frontend/src/tests/` — stage + settings coverage

## Test plan

- Unit: loopback picker chooses loudest, skips current, falls back to
  default; style picker never repeats; defaults/persistence roundtrips.
- Live: `speaker.play` sine onto a *non-default* endpoint → emitted bands
  go nonzero within one probe window; Spotify-Connect silent case still
  emits honest zeros.
- UI: Screensaver Type first in the tab; Shuffle option + interval row;
  shuffle rotation observed at short interval; card size screenshot.
- Suites: frontend vitest, backend pytest, vue-tsc, production build.

## Implementation Results

**Status: Implemented + live-verified.** `research_upgrade1`.

- **Spectrum endpoint-follow works live.** Played a 440 Hz sine through
  the *non-default* Lenovo headset endpoint while the tap sat on Realtek:
  after the 4 s silence window the service hopped (`following output
  Realtek -> Lenovo H600`), emitted `live: true` frames with real bands,
  then hopped back to the default when the tone ended. All-silent →
  honest zeros, unchanged.
- **Bug found mid-verification:** `screensaverShuffleMinutes` was missing
  from the backend `ALLOWED_USER_SETTING_KEYS` allowlist — server sync
  silently stripped it. Added + covered by the payload-keys mirror test.
- **Shuffle verified live** at a 3 s interval: `spectrum → stats →
  spectrum → widgets → spectrum → stats → …` — all three views rotating,
  never an immediate repeat. Saved value stays `'shuffle'`; rotation is
  ephemeral and the timer dies with the saver.
- **Bigger card verified:** `.has-track` now measures 560 × 207 px at
  1280 × 800 — ~30 % of screen height, visualizer dominant (screenshot
  `refs/dl133-spectrum-card-final-*.png`).
- **Settings verified live:** `ss-type` ("Screensaver type") is the first
  panel — label "Screensaver Type", options Widget dashboard / Spectrum
  visualizer / System stats / **Shuffle**; "Rotate every" row appears only
  under Shuffle. "Not in use" notes fire on the right types.
- **Spotify caveat is environmental, not a bug:** its session was Active
  while rendering silence on every endpoint (endpoint peak meter ~0.01 =
  noise floor) — Connect remote playback or hardware offload. When the
  machine genuinely emits audio anywhere, the spectrum follows it.

Suites: **541 frontend (86 files) + 1111 backend** — 7 new backend +
13 new frontend tests; vue-tsc clean; `dist` rebuilt; backend restarted
(10 integration packs loaded, zero errors).

