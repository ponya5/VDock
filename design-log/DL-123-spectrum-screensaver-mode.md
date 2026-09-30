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

