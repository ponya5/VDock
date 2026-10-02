# DL-141 — Spectrum & System Stats leave the widget roster; StatsStage gets an ambient backdrop

## Problem

The Widgets section in Settings lists "Spectrum" (mini audio analyzer)
and "System Stats" (CPU/mem meters) as widgets — but both are already
full screensaver *types* (`screensaverStyle: 'spectrum' | 'stats'`).
Listing them as widgets is conceptually wrong and duplicates the type
picker. The user also finds the System Stats screensaver's flat
`#04060c` backdrop boring — it should get an animated ambient
background.

## Design

### Demote the two pseudo-widgets

Remove `'spectrum'` and `'systemstats'` from:

- `screensaverWidgetOptions` (SettingsView) — the toggle rows disappear.
- `ScreensaverWidgetId` / `SCREENSAVER_WIDGET_IDS` /
  `SCREENSAVER_WIDGET_LABELS` / `DEFAULT_SCREENSAVER_LAYOUT`
  (`utils/screensaverLayout.ts`) — persisted layouts carrying those keys
  are silently dropped by `normalizeScreensaverLayout` (it only iterates
  known ids), so no migration code is needed.
- `ScreenSaver.vue` — the two widget template blocks,
  `showSpectrumWidget`/`showSystemStatsWidget`, their `mountedWidgets`
  and `usesWidgetScale` entries, the `SpectrumWidget`/`SystemStatsWidget`
  imports, and the now-dead `.ss-wrap-spectrum` mobile CSS.
- `stores/settings.ts` — `applySettingsObject` filters the two ids out
  of any persisted `screensaverWidgets` array, so an existing user's
  saved list stops rendering them (the fullscreen types remain reachable
  via the style picker / Shuffle pool).
- `components/screensaver/SpectrumWidget.vue` and
  `SystemStatsWidget.vue` are deleted — nothing else imports them
  (`useAudioSpectrum`/`useSystemStats` composables stay; SpectrumStage
  and StatsStage use them directly).
- `system-stats-widget.test.ts` loses its `SystemStatsWidget contract`
  describe; the `useSystemStats` composable coverage stays.

### StatsStage ambient background

A pure-CSS layer (GPU-cheap, no rAF): an absolutely-positioned `.st-bg`
behind the content carrying

- three slow-drifting radial glow blobs on independent keyframe paths
  (cool cyan/indigo, monitoring-console palette),
- a warm "load" glow whose opacity tracks `--load` (CPU %) — the room
  warms when the machine runs hot,
- a faint vertical scan sweep (~9 s) for the CRT-console feel.

`prefers-reduced-motion` disables the animation; the tint still applies.

## Implementation Results

Implemented as designed, with one refinement pass after first live
verification — the initial glows were too subtle to register on the
panel, so the ambient layer gained:

- a faint **blueprint mesh** (`46px` grid at ~5% blue) as static texture
  beneath the glows,
- a **vignette** (`.st-bg::after` radial) that deepens the edges,
- stronger glow alphas (0.20→0.34 / 0.18→0.30 / 0.10→0.16, warm glow
  peak 0.26→0.37), larger blobs and wider drift paths so motion is
  perceivable across the room.

Verified:

- Settings → Screen saver → Widgets now lists exactly 7 rows (Clock,
  Weather, News, Sports News, Stocks/Crypto, World Clock, Now
  Playing) — no Spectrum/System Stats.
- `screensaverStyle: 'stats'` selected via the UI + Test shows the
  full-screen board over the animated backdrop — ref
  `design-log/refs/saver-stats-wow-2026-10-02T01-05-18-461Z.png`.
- Targeted suite 52/52 green (screensaver layout, shuffle, settings
  sync/malformed, system-stats composable, spectrum stage);
  `vue-tsc` clean; `npm run build` clean — `dist` rebuilt.
- Both deleted components removed; no remaining imports.

## Follow-up 2 — Sensor-panel rework: animated gauges

Reference: AIDA64-style hardware monitor — radial dials whose arcs are
graded green→amber→red. The flat hero-numbers-plus-bars layout read as
static; the ask is an animated dashboard where every indicator visibly
tracks live stats.

### Design

- New `GaugeDial.vue` (screensaver components): a 270° SVG dial built
  from ~33 ticks. Unlit ticks form a dim track; lit ticks take a
  position-graded hue (green→yellow→orange→red for `load`, cyan for
  `cool`/network). A white needle sweeps with
  `transition: transform .7s` (overshoot bezier) on every poll. Tick
  light-up is staggered (`transition-delay: i·9ms`) so a value jump
  cascades around the dial instead of snapping.
- Center readout: rAF-tweened number (ease-out cubic, ~650ms) so the
  digits count between polls; `display` prop override for string values
  (network rates) which crossfade-pop via `:key` remount. First sample
  sets instantly — no 0→N fly-up on mount (also keeps
  `stats-stage.test.ts`'s `'43%'` assertion deterministic).
- `prefers-reduced-motion` → tween/needle/tick transitions disabled.
- StatsStage becomes a 3×2 gauge board:
  `CPU LOAD` (dial + sparkline + per-core strip), `CPU TEMP`
  (dial, °C normalized /105; falls back to a CLOCK/freq card when the
  platform has no thermal sensor), `MEMORY` (dial + GB detail),
  `DISK` (dial on system-mount fullness + kept `.st-part` rows),
  `NET DOWN` + `NET UP` (cyan dials self-scaled to `netPeakBps`,
  center shows `fmtRate`).
- Background gets a slow-rotating conic aurora layer on top of the
  mesh/glows/scan/vignette.

### Results

- `GaugeDial.vue` created; StatsStage rebuilt as the 3×2 sensor board.
  The CPU card keeps the sparkline + 16-bar per-core strip under the
  dial; DISK keeps the partition meter rows beneath its fullness dial.
- This machine has no thermal sensor on Windows/psutil, so the live
  build exercised the designed `Clock` fallback card (GHz + process
  count) — verified rendering in place of `CPU Temp`.
- Breakpoint fix during live verification: the 2-column layout kicked
  in at ≤940px, producing ~136px-tall cards that crushed the dials in
  squat windows (800×580). Moved to ≤700px; the 1024×600 panel and
  narrow windows both keep readable gauges.
- Live-verified on the built bundle at 1024×600 —
  `design-log/refs/saver-stats-gauges-1024-2026-10-02T01-16-34-781Z.png`:
  graded tick arcs, needles mid-sweep, aurora/mesh/scan/vignette
  backdrop, rates updating between polls.
- `stats-stage.test.ts` assertions still green unchanged (`43%`,
  `61°C` chip, `Charging 88%`, 2 `.st-part`, 4 `.st-core`) — the first
  sample renders instantly as designed. Full suite 566/566,
  `vue-tsc` clean, `dist` rebuilt.
