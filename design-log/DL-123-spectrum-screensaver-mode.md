# DL-123 — Spectrum as a full screensaver mode: skins, shuffle, media controls

## Background

DL-117 added the Winamp-style spectrum as one *widget* among the screensaver
sections. The user's follow-up: when enabled, the spectrum should BE the
screensaver — the idle timeout opens a fullscreen visualizer instead of the
widget dashboard — with multiple skins (references: classic Winamp bars in
fire/mono/UV palettes, a 3D rotating isometric bar field, a radial scope,
and flowing "Aurora/Ember" contour lines), a bottom media controller that
does not dismiss the saver, and an optional skin shuffle that rotates the
look every N minutes.

## Problem

- `ScreenSaver.vue` renders only the widget dashboard; there is no concept
  of a "screensaver style".
- The existing `SpectrumWidget` renderer is a 240px widget — fullscreen
  needs the same data (`audio_spectrum` bands) but different renderers,
  plus smoothing ownership moves to the stage.
- The saver dismisses on any root tap (`onRootTap` → `emit('dismiss')`), so
  a media bar needs full event containment — exactly the pattern the layout
  toolbar and headline links already use (`@click.stop`/`@touchstart.stop`).
- Skin choice + shuffle interval + media-bar visibility are user settings
  that must ride the existing settings persistence/sync machinery.

## Design

### Settings (settings.ts)

Five new persisted keys, all following the defaults → ref → payload →
`applySettingsObject` → `loadSettings` → export pattern:

- `screensaverStyle: 'widgets' | 'spectrum'` (default `'widgets'`) — what
  the idle timeout shows. `spectrum` replaces the whole surface.
- `spectrumSkin: string` (default `'winamp'`) — id into the skin registry.
- `spectrumShuffle: boolean` (default `false`).
- `spectrumShuffleMinutes: number` (default `10`).
- `spectrumMediaBar: boolean` (default `true`).

### `frontend/src/services/spectrumSkins.ts` — renderer registry

Each skin = `{ id, label, draw }`; `draw(ctx, frame)` is a pure renderer
with per-instance state held in a factory-created closure (history buffers,
smoothed arrays, phase). `frame` = `{ bands: number[20] (0-100, already
envelope-smoothed by the stage), level, live, w, h, t, dt }`. Renderers:

- **bars** (×3 skins via palette param): Winamp classic — bottom-anchored
  thin bars, segment carve lines, peak-hold caps. Palettes:
  `winamp` = green→yellow→red; `mono` = greyscale (img 1 mid); `uv` =
  violet→cyan→magenta neon (img 1 bottom).
- **iso**: isometric waterfall — a frequency × history grid of projected
  columns (top + two side faces), slow yaw drift, hue sweeping
  blue→green→yellow→red across the field (img 2).
- **scope**: radial plot — bands mapped around a circle, radius modulated
  by amplitude, mirrored inner ring + faint spokes, slow rotation, additive
  glow (img 3).
- **aurora**: concentric polar contour rings expanded by a smoothed band
  field around θ — topographic-blob look, pink/violet strokes (img 4).
- **ember**: stacked horizontal ridgelines — each line a smoothed band
  curve displaced down/back, amber→red gradient, additive (img 5).

`SPECTRUM_SKINS` is the ordered list the settings picker and the shuffle
cycle read. `pickNextSkin(current, rng)` never returns the current id.

### `frontend/src/components/screensaver/SpectrumStage.vue`

- Full-viewport `<canvas>` (DPR-aware, ResizeObserver), rAF loop capped at
  ~30 fps — fullscreen smoothness without burning the panel's GPU.
- Stage owns the shared envelope: `display[i] = max(target, display[i] *
  decay^dt)` so skins stay stateless about smoothing.
- Skin switch (settings change or shuffle tick) → CSS fade on the canvas
  (~300 ms dip) + fresh renderer instance (clears history buffers).
- Shuffle: `setInterval` at `spectrumShuffleMinutes`, picks a random
  different skin — cosmetic only, does NOT write `spectrumSkin` back to
  settings (the saved pick is the "home" skin; shuffle is ephemeral).
- **Media bar** (bottom-center glass pill, `spectrumMediaBar` on): album
  art (SMTC `artUrl` or music glyph), title/artist, thin progress from
  `position_s`/`duration_s` extrapolated like NowPlayingWidget, and
  prev / play-pause (icon tracks `nowPlaying.playing`) / stop / next.
  Buttons dispatch `{type:'cross_platform', config:{action:'media_*'}}`
  through `socketClient.executeAction`. The bar wrapper `.stop`s
  `click`/`touchstart`/`pointerdown` — taps inside never reach `onRootTap`.
- Honest idle: no `live` frames → renderers settle to baseline (bands→0);
  `lastSeenAt === null` past a grace → a dim "audio capture unavailable"
  hint instead of a black void.
- `prefers-reduced-motion`: fps cap drops and sweep/drift phases freeze.

### ScreenSaver.vue

- `spectrumMode = settingsStore.screensaverStyle === 'spectrum'`.
- When on: hide `ss-bg`/`ss-bg-component`/`ss-dim`/`ss-glow` and every
  widget block (the visualizer owns the black canvas); mount
  `<SpectrumStage />` instead. Custom backgrounds stay loaded but unseen —
  no cleanup changes.
- `layoutEdit` forces widget mode (the editor edits the widget layout —
  meaningless over the stage).
- Dismiss semantics unchanged: root tap exits; media bar and any stage
  chrome `.stop` their events.

### SettingsView.vue

New "Spectrum screensaver" panel in Appearance → Screensaver (between
Activation and Widgets):

- Mode select (`widgets`/`spectrum`) — the enable switch the user asked for.
- Skin picker — a row of labelled swatch cards, each rendering a live
  ~96×54 demo of its skin via the same renderer on synthetic bars.
- Shuffle toggle + interval select (1/5/10/30 min).
- Media bar toggle.
- Test button already in Activation shows whichever mode is selected.
- Search index entry ("Spectrum visualizer…"); reset section covers the
  new keys; widget list hint notes widgets apply to Widget-dashboard mode.

## Trade-offs

- **Renderers as plain canvas code, not components**: per-skin Vue
  components would re-create canvases on shuffle and fight the shared rAF.
  One stage + swappable draw closures is smaller and faster.
- **Shuffle is ephemeral, not persisted**: writing `spectrumSkin` every N
  minutes would churn settings sync + disk writes for a cosmetic effect.
- **Transport via `cross_platform` catalog actions**: reuses the proven
  media-key path (and therefore works for whichever app SMTC reports) —
  no new backend endpoint.
- **20-band data reused as-is**: resampling/interp inside renderers (aurora
  smooths to ~64 points) keeps the socket contract untouched.

## Verification Criteria

- `screensaverStyle='spectrum'` + idle/`show_screensaver` → fullscreen
  stage; widgets hidden; tap outside → dashboard; tap inside media bar →
  no dismiss AND the media action executes.
- Each of the 7 skins renders a distinct, non-blank frame with live bands.
- Shuffle picks a different skin each interval; disabling freezes rotation.
- Media bar icons flip play↔pause with `nowPlaying.playing`.
- vitest: registry completeness, `pickNextSkin` exclusivity, stage mount
  states, media-bar event containment, settings defaults/roundtrip.
- `npm run test` + `npm run build` green; dist ships to the panel.

## Implementation Results

All landed as designed.

**Built**

- `services/spectrumSkins.ts` — `SPECTRUM_SKINS` registry (7 skins),
  `getSpectrumSkin` fallback, `pickNextSkin` (never repeats current),
  `demoBands` synthetic driver shared by previews/tests. Renderers:
  `bars` ×3 palettes (fire/mono/uv — segmented bars + peak caps),
  `iso` (16×11 frequency-history column field, ±yaw drift, blue→red hue
  sweep, back-edge waveform rail), `scope` (rotating polar spectrum +
  per-band spokes + magenta inner echo, additive glow), `aurora`
  (16 squashed concentric contours, magenta→violet), `ember` (20 stacked
  ridgelines, sine-envelope silhouette, amber→red).
- `components/screensaver/SpectrumStage.vue` — DPR-aware fullscreen canvas,
  rAF ~30 fps, shared rise-fast/fall-slow (`exp(-dt*2.4)`) envelope so
  skins stay stateless; skin swap = 260 ms opacity dip + fresh renderer;
  shuffle via `setInterval` + `pickNextSkin` (ephemeral — never writes
  settings); `lastSeenAt===null` past 4 s grace → "Audio capture
  unavailable" hint; skin-name tag top-right with live dot.
- Media bar: glass pill bottom-center (`spectrumMediaBar`), SMTC art/title/
  artist + progress (position extrapolated from payload-arrival time —
  server `ts` is not clock-comparable), prev/play-pause/stop/next via
  `socketClient.executeAction({type:'cross_platform', config:{action}})`;
  play icon tracks `nowPlaying.playing`; all pointer events `.stop`-ed.
- `ScreenSaver.vue` — `spectrumMode` (= style==='spectrum' && !layoutEdit)
  mounts the stage instead of every bg-layer/widget block; layout edit
  still shows the widget dashboard it edits; widget feed polls skipped in
  spectrum mode.
- `settings.ts` — `screensaverStyle`, `spectrumSkin`, `spectrumShuffle`,
  `spectrumShuffleMinutes`, `spectrumMediaBar` through defaults/interface/
  payload/apply/load/export; `saveSettingsLocalOnly` exported as a test seam.
- `components/screensaver/SkinPreview.vue` — live renderer swatch for the
  picker (real skin code on `demoBands`, ~24 fps).
- `SettingsView.vue` — "Spectrum screensaver" panel (mode select, 7-card
  live skin grid, shuffle switch + 1/5/10/30 min select, media-bar
  switch), reset coverage, search entry + `spectrum` deepTab anchor,
  `.skin-*` styles (clamp() per property8).

**Verified**

- `npx vitest run src/tests/spectrum-stage.test.ts` — 13/13: registry
  shape, fallback, shuffle exclusivity over 210 draws, demo-band bounds,
  stage mount/bar toggle, media dispatch payloads, `.stop` containment
  (parent listener never fires), skin label swap, defaults + localStorage
  roundtrip.
- Full frontend suite: **446 passed** (was 433). `vue-tsc` + `npm run
  build` clean — new `dist` bundle shipped for the panel.

**Deviations**

- `screensaverStyle` is a two-value style select (`widgets`/`spectrum`)
  rather than a bare `spectrumEnabled` boolean — same enable UX, but it
  names the *alternative* and leaves room for future styles.
- Spectrum mode suppresses the custom screensaver background layers
  (visualizer owns the black canvas — matches all references); the bg
  setting is untouched for widget mode.
- Idle stubs: bar skins draw a low breathing baseline when the stream is
  silent (bands≈0 would otherwise paint a flat line — reads dead).
- Seven skins, not a skin+palette matrix — each entry self-describes its
  look so the picker stays one flat list.

## Follow-up — now-playing presented as a card

The media bar now upgrades to a compact **now-playing card** whenever a
track exists — the ask was a real presentation, "but not oversized" vs
the visualizer.

- `.spectrum-media.has-track`: same bottom-center anchor, but a
  rounded glass card (~400×170 px max) instead of the slim pill —
  album art grows to `clamp(72px, 13vh, 104px)` (was a 46 px thumb),
  a `NOW PLAYING · <source>` kicker line (`.exe` stripped), larger
  title/artist, full-width progress, and the same four transport
  controls centered beneath. Idle (no track) keeps the slim pill.
- Markup regrouped: art+text wrapped in `.spectrum-media-head`; the
  controls row is the card's second child so `flex-direction: column`
  does the switch — one template, two densities.
- 220 ms border-radius/art-size transitions + a 260 ms fade-up on the
  head when a track lands.
- Still gated on `spectrumMediaBar`; Settings copy updated
  ("Now-playing card with transport controls…").
- Tap containment unchanged — card stops all pointer events, a tap
  outside still dismisses the saver.

**Verified live** (Playwright, real SMTC): Spotify "BURN IT DOWN —
Linkin Park" renders art + kicker + progress over the Winamp skin;
card measured 400×172 px at bottom-center of a 1024×680 viewport.


## Follow-up — motion pass (DL-134 session): make the skins "eye-catching"

Feedback: the renderers read "very simple and not impressive" — they were
correct but visually static between band changes. Added a constant-motion
layer to every skin; all seven keep their identity and the shared
`SpectrumFrame` contract (no per-skin loops, silent input still goes dim).

Shared helpers added in `spectrumSkins.ts`:

- `createPulse()` — a beat-pulse tracker per renderer: spikes when the
  level jumps, decays ~0.4 s. Transients now flash, not just grow.
- `Spark`/`drawSparks()` — a small additive rising-spark pool shared by
  the bar and ember skins.
- `hexRgb()` — palette hex → `rgba()` channel string.

Per skin:

- **Bars (winamp/mono/uv)** — floor-lit radial beat glow that breathes
  with level and flashes on the pulse; a palette-tinted light beam
  sweeping left→right behind the bars (faster/brighter when louder);
  peak caps now drop under gravity (velocity accel, no more pure fade);
  sparks climb off bars running hot (>55).
- **Iso** — ripple rings radiate through the grid (per-column z lift as
  `sin(dist − t·2.8)`, amplitude level-scaled); slow hue drift; an
  elliptical under-glow pooling beneath the field; the whole field bobs
  gently and yaws a touch faster.
- **Scope** — rotation is now level-driven (`rot += dt·(0.12 + lvl·1.1)`,
  winds up when loud) instead of fixed `t·0.1`; a pulsing reactor orb at
  the core; three comets orbit inside the ring on alternating directions
  with 7-dot fading trails, brightening under loud bands; guide rings
  breathe.
- **Aurora** — every ring gets a "comet" arc sweeping it, adjacent rings
  counter-rotate; ring spacing breathes (`±5%` sine); the whole hue
  sweep drifts slowly; a violet core glow swells with level; band
  sampling rotates a little faster.
- **Ember** — a glowing hot-spot dot rides each ridgeline's crest;
  a second traveling sine adds a horizontal swell to the shimmer;
  embers lift off the hottest front crests and rise/fade.

Perf: all additions are a few dozen primitives per frame on top of the
existing paths — no new buffers, no new RAF (still the stage's ~30 fps
loop), state lives in the factory closures so skin swaps reset cleanly.

### Implementation Results

- `spectrumSkins.ts` only; registry ids/labels unchanged (test pins all
  seven). New vitest smoke test drives every skin through 90 live/idle
  frames with a mock ctx — catches runtime errors source tests can't.
  17/17 green in `spectrum-stage.test.ts`; `npm run build` clean.

## Follow-up — 60 fps render path (DL-134/135 session)

Feedback: "improve the fps… smooth animation". Three layers:

- **Render 60 fps, not 30** — `FRAME_MS` 33→16 in `SpectrumStage.tick`.
  The motion layers (sweeps, orbits, ripples) animate on `t`/`dt` so they
  were already continuous — they just looked stepped at 30 Hz.
- **Governor** — `frameCostMs` EMA of `renderer.draw` cost; sustained
  >14 ms drops the budget to `SLOW_FRAME_MS` (33) instead of janking.
  One-way downshift (no recovery timer — the panel is the weak link,
  being conservative beats oscillating). `prefers-reduced-motion` now
  gets a real ~22 fps cadence (`REDUCED_FRAME_MS`) — the old
  `lastFrame = -Infinity` only skipped the cap on frame 1, dead code.
- **Band interpolation** — the backend emits ≤~14 Hz, so at 60 fps the
  bars stair-stepped. `display[]` is now an asymmetric lerp per frame:
  attack `exp(-dt·14)` (~70 ms constant ≈ emit cadence — percussive hits
  still read instant) and release `exp(-dt·5)`. `level` gets the same
  treatment via `levelSm` (`dt·12`) — the skins' glow/pulse no longer
  snap on each emit.
- **Backend emit rate up** — `MIN_EMIT_INTERVAL` 1/14 → 1/22 ≈ one emit
  per 43 ms audio chunk when bands move (payload is ~20 ints; socket
  cost is nil). More granularity in, smoother envelope out.

Verified: `test_audio_spectrum.py` 27 passed/1 skipped; frontend
spectrum tests green; `npm run build` clean, `dist` rebuilt.

## Follow-up — landscape overscan on mobile (2026-02-20)

Radial skins (scope/aurora/iso) size by `min(w,h)`, so a wide-short
mobile landscape viewport (e.g. 844×390, or the 1024×600 touch panel)
shrunk them to a small disc. The stage now applies a centered canvas
zoom when `isMobileViewport && w > h`:

`zoom = min(1.45, sqrt(w/h))` — 1.7:1 → ~1.3×, 2:1 → ~1.4×. Visuals
fill the width; top/bottom crop is intentional ("if part of the
animation is cut due to landscape, so be it"). Each skin's own
`clearRect(0,0,w,h)` still covers the canvas under the zoomed
transform. The media bar/tag are HTML overlays — unaffected.

Verified: headless CDP shot of the aurora skin at 844×390 — rings fill
the width with edge crop instead of a small centered disc.

## Follow-up — dynamics expansion, snap-on-spike (2026-02-20)

**Problem.** The visualizer read "pretty steady" — bars hovered mid-height
and transients barely stood out.

**Backend (`audio_spectrum.py`)**

- `amp_to_value` was linear-in-dB over the -60 dBFS floor: typical music
  (-30…-10 dB) parked bands at 50-83. The normalized value now gets a
  `BAND_CURVE = 1.6` exponent — -30 dB → 33, -6 dB → 84, slams → 100;
  ~50 points of visible spread instead of ~30.
- `BAND_DECAY` 0.78 → 0.70 per ~43 ms chunk (halving ~90 ms) — hits
  release fast enough to read as separate events.

**Frontend**

- `SpectrumStage.vue`: spikes bigger than `SPIKE_SNAP` (16) skip the
  interpolation lerp entirely and land at full height on the frame they
  arrive; smaller steps keep the glide. Attack `dt·14` → `dt·18`.
- `SpectrumWidget.vue`: `BAR_FALL` 0.85 → 0.76 (same punch on the mini
  widget's ~15 fps loop).

Verified: `test_audio_spectrum.py` 29 passed (curve test repinned +
new expansion-spread test); frontend 31 green; `npm run build` clean;
backend restarted — capture live on the active endpoint.

## Follow-up — iso field painter order fix (2026-02-20)

**Bug.** The iso skin drew rows `r = ROWS-1 → 0` — front rows first —
while screen depth (`px(cy+sy) + py(cy−sy)`, both coefficients positive
for the ±0.55 rad yaw swing) makes large-r the *front*. Back bars then
painted over the side faces of bars in front of them and the field read
as a wall of colour instead of stepped columns. Latent since DL-123;
unmasked once heights got real variance.

**Fix.** Iterate `r` ascending (back → front); columns already ascend.
Nearer cells' faces now correctly overdraw farther bars' tops.

**Verified** live via headless CDP + a looped test WAV through the
loopback (bass thump + sweep): columns render as distinct 3D bars —
before the fix the identical render showed collapsed overlap.

## Follow-up — rotor skin (2026-02-20)

**Request.** Add the Winamp OpenGL "3D Rotating Spectrum Analyzer"
(McBain) as a skin: a spinning field of thin needles on a
frequency × history grid, height-mapped blue→red, ringed by a dotted
scope wave.

**`createRotor()`** (`spectrumSkins.ts`), id `rotor`, label "Rotor 3D":

- 16×14 needle field; front row samples `bands` and shifts into
  history every 55 ms (same cadence as iso).
- Continuous 360° yaw (`t·0.26` ≈ 24 s/rev) — unlike iso's bounded
  swing — so painter order can't be a fixed loop: the 224 cell indices
  are sorted by rotated depth each frame.
- Weak perspective divide (`1/(1 − ry·0.055)`): back rows converge and
  shrink, front rows loom — matches the plugin's foreshortened plane.
- Needles: thin stem + bright diamond cap, hue by height
  (blue stubs → red spikes).
- Dotted scope ring around the field: 150 dots on an ellipse, radius
  modulated by the spectrum, fast secondary wiggle fakes the
  time-domain fuzz, counter-drifts against the field's spin.
- Faint floor quad keeps the rotation readable when the field is idle.

**Verified.** Headless CDP on the built bundle: idle → clean
perspective plane of stubs + ring; with a looped test WAV through the
loopback → needles rise with correct back-to-front overlap, wavefronts
ripple through history rows. Registry test repinned to eight skins;
spectrum + screensaver suites 31/31 green; `npm run build` clean.

## Follow-up — swarm skin (2026-02-20)

**Request.** Add the Winamp-style cube-cascade visualization (reference
img 5: streams of shaded cubes flowing toward the camera, glowing orbs
on the beat) as a screensaver skin.

**`createSwarm()`** (`spectrumSkins.ts`), id `swarm`, label "Swarm":

- 460 persistent cubes, each bound to a spectrum band — lane
  (left→right) + lift (height) — so the swarm's silhouette is the
  spectrum streaming past.
- Depth `z` is the flow axis: cubes spawn converged near the horizon,
  swell as `s = 0.1 + z` approaches 1, and respawn at the back.
  Per-frame index sort (far → near) for painter order.
- Flow speed scales with level plus a beat surge from the shared
  `createPulse()` helper.
- Each cube drawn as a mini iso-cube (top rhombus + two side faces),
  hue washed by lane, depth, and a slow time drift → the reference's
  flowing rainbow.
- Beat orbs: when the pulse spikes, glowing spheres pop off a random
  loud lane and float up through the swarm via the shared additive
  `drawSparks` pool (lavender, matching the reference's orb panel).

**Verified.** Headless CDP on the built bundle over the looped test
WAV: dense cube cone streaming forward, near cubes chunky like the
reference's bottom panel, orbs popping on beats. Registry repinned to
nine skins; smoke test covers all nine; `npm run build` clean.

## Follow-up — wave / ring / mirror / psyche skins (2026-02-20)

**Request.** Offer the classic example set so the user can choose: an
FFT-driven visual, a waveform that pulses on beats, a circular waveform
whose radius changes over time — plus one unique psychedelic skin.

Four new renderers in `spectrumSkins.ts`:

- **`wave` "Waveform"** — a synthesized scope trace: the backend emits
  FFT bands, not raw PCM, so the trace is a sum of three harmonics
  weighted by the bass/mid/treble band groups. Reads like a real
  waveform while staying a pure function of the spectrum. Beat pulse
  thickens/flares the beam; two delayed ghost echoes give a phosphor
  trail; faint center graticule.
- **`ring` "Wave Ring"** — the circular-waveform example. Angle is the
  time axis; integer harmonics (3/6/11, guaranteed closed) weighted by
  band groups make the radius ripple like a wrapped scope. Base radius
  breathes on `sin(t)` and swells on beats; hard hits lob expanding
  shockwave rings; magenta main trace + cyan inner echo + orbiting
  grain; flaring core orb.
- **`mirror` "Mirror Bars"** — the FFT example, distinct from the
  bottom-anchored Winamp row: bars grow up off a lit center rail and
  reflect downward dimmer; cyan→magenta hue drift along frequency; hot
  bars get tip caps; the rail flares on beats.
- **`psyche` "Psychedelia"** — the unique one. A rotating 10-wedge
  kaleidoscope: each petal's reach is a mirrored band sample, drawn
  additively over a translucent-black trail fade (the smear IS the
  effect — ribbons of light persist and decay). Hue races the full
  wheel continuously, the center bloom uses the complement palette and
  swells on the beat, two rings of counter-rotating dust round it out.

**Verified.** Headless CDP on the built bundle over the looped test
WAV (bass thump + sweep + shimmer through the real loopback): Wave
shows a proper scope trace with echoes; Ring a morphing closed
waveform circle; Mirror a symmetric neon comb; Psyche a hue-cycling
mandala with trail arcs. Registry repinned to thirteen skins; the
90-frame smoke test covers all four; `npm run build` clean → dist.
