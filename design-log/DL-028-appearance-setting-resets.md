# DL-028 — Per-Setting Reset Icons in Appearance Settings

## Background
Settings → Appearance has grown to ~20 user-adjustable values across four
sub-tabs (Button Behaviour, Layout & Behavior, Background, Screen Saver).
Only two controls (Button Size, Button Transparency) have reset buttons —
users who tweaked a slider/toggle can't restore the factory value without
remembering it.

## Problem
No way to reset individual appearance values to defaults. User request:
"add reset buttons icons in appearance settings pages.. (where the user is
able to change values)".

## Design

### Defaults source of truth
Export `SETTINGS_DEFAULTS` from `settings.ts` — a typed const holding every
default (buttonSize 1.0, showLabels true, editModeWiggle false,
dockedSidebarWidth 190, dockedButtonHeight 84, toastLevel 'all',
touchMode 'normal', screensaverTimeout 120, screensaverWeatherSize 100,
screensaverWidgetSize 100, newsFeeds '', sportsFeeds '',
newsRotateSeconds 8, marketTickers '', screensaverWidgets [all five],
background/screensaverBackground `DEFAULT_BACKGROUND_ID`, button defaults
animation 'none' / iconLoop 'swing' / effect 'none'). View code references
it — defaults can never drift from the store.

### `SettingResetButton.vue`
Icon-only touch-friendly button (36px, `rotate-left` icon), matching the
glass style. Prop `atDefault` dims + disables it when the current value
already equals the default — the icon doubles as a "modified" indicator.
Emits `reset`.

### Placement
- **Sliders** — inside the existing `.form-group-header` row (replaces the
  two text `.btn-reset` buttons for uniformity).
- **Toggle rows** — grouped with the switch in a new `.toggle-row-end`
  flex wrapper.
- **Radio groups / selects / text inputs** — in their label/header row.
- **Background pickers** — reset to `DEFAULT_BACKGROUND_ID` ('default').
- **Screensaver widgets** — one section-level reset restores the default
  five-widget set.
- **Button Behaviour demo controls** (animation/icon-loop/design) — reset
  restores the factory default AND updates `buttonDefault*` so new buttons
  match; applying to existing buttons stays behind the explicit "Save &
  Apply to All Buttons" button.
- **Touch Mode** — reset in the section header restores 'normal'.

## Implementation Plan
- [x] Phase 1: `SETTINGS_DEFAULTS` export + `SettingResetButton.vue`
- [x] Phase 2: wire resets into all Appearance sub-tab controls
- [x] Phase 3: typecheck, tests, build, live verify

## Implementation Results
- Phase 1: `SETTINGS_DEFAULTS` const exported from `settings.ts` (26 keys);
  `SettingResetButton.vue` — 36px icon-only `rotate-left` button, dims +
  disables via `atDefault` so it doubles as a modified indicator.
- Phase 2: wired 26 reset points — Buttons tab (size, transparency, 5
  toggles, 3 demo controls, touch mode header), Layout (sidebar toggle,
  width, height, toast level), Background (style picker), Screensaver
  (delay, background, widget-set reset, weather size, text size, news
  feeds, rotate seconds, sports feeds, market symbols, world-clock cities).
  `.toggle-row-end` / `.header-end-group` flex wrappers keep label-left /
  control-right layout. `resetButtonDefault()` restores factory value AND
  the persisted `buttonDefault*` so new buttons match.
- Phase 3: typecheck clean; 50 files / 188 tests pass; build regenerated
  dist. Live at 1024×600: 11/4/1/10 reset icons across the four sub-tabs;
  verified buttonSize 1.7 → reset → 1.0 (icon lit while dirty, dims after);
  widgets ['news'] → reset → default five.

## Trade-offs
- **Chosen:** always-visible icon that dims at default (stable layout,
  doubles as modified indicator).
- **Rejected:** v-if show-only-when-modified (layout shift); per-widget
  resets in the widget list (defaults are all-on, a section reset is the
  meaningful action); resetting scene background (per-scene data, not a
  settings default — Remove button already covers it).

## Verification Criteria
- Every adjustable control in all four Appearance sub-tabs shows a reset
  icon; clicking restores the documented default and persists via the
  store's normal save watch.
- Icon is dim/disabled when value equals default.
- 1024×600: rows don't wrap or clip.
