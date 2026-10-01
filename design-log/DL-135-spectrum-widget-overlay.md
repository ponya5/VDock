# DL-135 — Widgets over the spectrum screensaver

## Problem

The `spectrum` screensaver style replaces the whole surface with the
visualizer + media bar — so the widget system (clock, weather, market,
news, sports, world clock) can never appear on it. Feedback: "add the
ability to add widgets to the spectrum — for example clock or weather."
The widget machinery already exists (positions in `screensaverLayout`,
toggles in `screensaverWidgets` + `screensaverClockEnabled`); it is
simply unreachable while a fullscreen style is on stage.

## Design

### Rendering: one widget layer, two possible backdrops

`ScreenSaver.vue` today: `SpectrumStage v-if / StatsStage v-else-if /
<template v-else>` — the v-else block holds both the widget-mode
backdrop (custom bg, scrim, dim, glow) and all nine `.ss-pos` widgets.

Split the two concerns:

- `<SpectrumStage v-if="spectrumBackdrop">` — renders whenever the
  effective style is spectrum, *including* `layoutEdit` (see below).
- The backdrop layers keep the old `v-else` conditions (widget surface
  only).
- A new `widgetLayerOn` computed gates the widget group:
  `!statsMode && (!spectrumBackdrop || spectrumOverlay || layoutEdit)`.

The three component widgets (`nowplaying`, `spectrum`, `systemstats`)
stay widget-surface-only (`&& !spectrumBackdrop`): the stage's own
media bar already covers now-playing, a mini spectrum inside the
fullscreen spectrum is nonsense, and system stats is the stats stage's
domain. The six info widgets (clock, weather, market, news, sports,
world clock) render over the spectrum — exactly the "clock/weather on
the visualizer" ask.

### Opt-in persisted flag

New key `screensaverSpectrumWidgets: boolean`, default **false** — the
factory widget list already enables weather/news/market, so defaulting
the overlay on would surprise every existing spectrum user with three
feeds over their viz. Toggled from Settings → Screensaver → General,
right under the type picker (shown when the style is spectrum or
shuffle — shuffle rotates through spectrum windows where it applies).

### Shared layout, WYSIWYG editing

Widget positions come from the same `screensaverLayout` map — the
"Customise layout" editor keeps working unchanged. When the style is
spectrum, the stage renders *behind* the editor instead of the widget
backdrop (`spectrumBackdrop` doesn't exclude `layoutEdit`), so the user
positions widgets on the real canvas they overlay. `SpectrumStage` gets
an `backdrop?: boolean` prop — in that mode its media bar is hidden so
transport buttons can't eat drags in the bottom-center band.

### Feed lifecycle

The existing `watch(spectrumMode)` sleeps widget feeds whenever the
spectrum is on stage. Re-key it to `widgetLayerOn`: feeds run whenever
the layer that can show them is mounted — widget surface, or spectrum
with the overlay enabled. Stats still sleeps them. Mount-time start
condition changes likewise.

### Behavior preserved

- Tap-to-dismiss: widgets don't stop propagation outside edit mode —
  taps bubble to the root dismiss handler exactly like widget mode.
- `onRootTap`/`startDrag` early-returns in `layoutEdit` — unchanged.
- Mobile curated set (clock/weather/worldclock forced) applies to the
  overlay too — on a 7" panel the overlay toggle is the single switch.
- `stats` style stays exclusive — no widget layer.

### Settings copy

- `ss-general` gains an "Overlay widgets" toggle row (spectrum/shuffle
  only) + the `ss-widgets` "not in use" note updates: on spectrum it
  now points at the toggle; on stats it stays exclusive.

## Trade-offs

- Overlay is all-or-nothing per widget list — no separate "which widgets
  on spectrum" picker. The list + shared layout is one mental model;
  a second matrix per style would double the settings surface.
- Editing positions happens over the live spectrum (not a mock) — a
  deliberate WYSIWYG upgrade over editing blind on the widget bg.
- Default-off flag = zero surprise for existing installs; one toggle
  turn-on for the ask.

## Implementation Results

- `stores/settings.ts`: new persisted `screensaverSpectrumWidgets`
  (default `false`) — defaults map, `PersistedUserSettings`, ref, save
  payload, `applySettingsObject`, defaults-merge, autosave watch list,
  store exports. `backend/routes/user_settings.py`: added to
  `ALLOWED_USER_SETTING_KEYS` so the key survives a server round-trip.
- `ScreenSaver.vue`: template split into backdrop vs. widget layer —
  `SpectrumStage v-if="spectrumBackdrop"` (covers layoutEdit too),
  widget-surface bg gated `!spectrumBackdrop && !statsMode`, widget
  layer gated `widgetLayerOn` (`!statsMode && (!spectrumBackdrop ||
  spectrumOverlay || layoutEdit)`). Component widgets
  (nowplaying/mini-spectrum/systemstats) wrapped in
  `v-if="!spectrumBackdrop"` — surface-only. Feed lifecycle re-keyed
  from `spectrumMode` to `widgetLayerOn` (watcher + onMounted start).
- `SpectrumStage.vue`: new `backdrop?: boolean` prop suppresses the
  media bar while it backs the layout editor (`mediaBarOn` now also
  requires `!props.backdrop`).
- `SettingsView.vue`: "Widgets on the visualizer" toggle row in the
  screensaver-type panel (spectrum/shuffle only); `ss-widgets` note now
  points at the toggle on spectrum, stays "not in use" on stats.
- Mobile: `showSpectrumWidget` no longer forced desktop-only — the
  mini-spectrum widget may ride phone layouts when explicitly enabled;
  `ss-wrap-spectrum` CSS spans the column width in portrait and becomes
  a full-width bottom strip in landscape.
- Deviation vs design: none — layoutEdit keeps the spectrum as backdrop
  as designed (`spectrumBackdrop` rather than the old `spectrumMode`),
  so positions are edited on the real canvas.

### Follow-up: ported to `main`

This entry originated on `research_upgrade1`; the design and the
implementation results above were ported onto `main` (post DL-134) with
the unrelated player-mode work from that branch deliberately excluded.
Differences while porting:

- The spectrum stage on `main` is the DL-134 two-canvas crossfade
  version; the `backdrop` prop + `mediaBarOn` gate were applied on top
  of it, no conflict.
- Tests updated: `spectrum-stage.test.ts` (backdrop/media-bar contract,
  flag default + roundtrip, `widgetLayerOn` feed contract) and
  `screensaver-shuffle.test.ts` (settings-toggle source contract).
  545/545 frontend tests green; `vue-tsc` clean; `dist` rebuilt.
- Verified live on the built bundle (Flask :5000): spectrum style +
  flag on renders clock/weather/markets/headlines over the live Winamp
  stage with the media bar intact (`refs/saver-spectrum-widget-overlay-
  live-2026-10-01T22-01-24-478Z.png`); `screensaver_layout_edit` keeps
  the spectrum mounted as backdrop with drag frames + toolbar and the
  media bar suppressed (`refs/saver-spectrum-layout-edit-2026-10-01T22
  -01-42-008Z.png`); flag off restores a clean spectrum (`0` `.ss-pos`,
  media bar back).
- Note: `screensaverSpectrumWidgets` was added to the backend
  `ALLOWED_USER_SETTING_KEYS`, so a server running an older build
  silently strips the key on PUT — the backend must be restarted to
  pick up the allowlist before the flag can persist server-side.
