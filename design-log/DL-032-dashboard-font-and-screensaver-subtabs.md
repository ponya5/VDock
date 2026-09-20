# DL-032 — Dashboard font styles + Screen Saver sub-tabs

## Background
User likes the screensaver's editorial typography (Instrument Serif display
+ JetBrains Mono labels — both already loaded in index.html) and wants it
available on the dashboard. Also: the Screen Saver settings pane is one
long masonry grid — split into Widgets / Settings / Backgrounds sub-tabs.

## Design

### Dashboard font (`settings.dashboardFont`)
- Options: `default` (Heebo — status quo), `editorial` (Instrument Serif
  for display text + JetBrains Mono uppercase meta labels — the
  screensaver look), `mono` (JetBrains Mono everywhere).
- Applied via `data-ui-font` attribute on `#app` (`.theme-dark` root) —
  CSS-attribute scoping, no JS class plumbing, inherited everywhere.
- Rules target dashboard chrome only: `.button-label`, `.segment-label`,
  `.profile-title-inline`, `.weather-desc`, `.weather-loc`,
  `.dock-section-label` etc. — Settings UI stays Heebo.
- `SETTINGS_DEFAULTS.dashboardFont = 'default'` + SettingResetButton.
- Picker UI: 3-option card row in Appearance → Layout & Behavior, each
  swatch rendering sample text in the real font.

### Screen Saver sub-tabs
- `screensaverSubTab` ref: 'widgets' | 'settings' | 'backgrounds'
  (default 'widgets'), nested `.sub-tab-bar` inside the screensaver pane.
- Settings: delay slider + Test/Customize Layout.
- Backgrounds: background picker + upload card.
- Widgets: widget toggles + weather size + text size + news/sports/
  market/worldclock feeds.
- Per-section `v-if` keeps the masonry grid intact.

## Verification
- Live at 1024×600: font picker flips dashboard typography; sub-tabs show
  disjoint section sets; persisted across reload.
- vitest + vue-tsc + build.

## Implementation Results

- `settings.ts`: `dashboardFont` ref/interface/DEFAULTS/payload/apply/
  return/watch — full plumbing, `'default'` factory value.
- `App.vue`: `:data-ui-font` on the `.theme-dark` root.
- `main.css`: `[data-ui-font='editorial']` → Instrument Serif on
  `.button-label`/`.profile-title-inline`/`.weather-temp`, JetBrains Mono
  uppercase on `.segment-label`/weather meta/hints;
  `[data-ui-font='mono']` → mono across `.deck-button`, pills, sidebar,
  header. Settings UI untouched.
- `SettingsView.vue`: Dashboard Font card (3 live-sample swatches +
  reset) atop Layout & Behavior; nested Widgets/Settings/Backgrounds
  sub-tab bar inside Screen Saver; per-section `v-if` keeps the masonry
  grid.
- Verified live: `data-ui-font` flips, `.button-label` computes to
  Instrument Serif under editorial; Widgets shows 7 sections, Settings 1,
  Backgrounds 1; choice persists via autosave.
- 207/207 tests (6 new), typecheck + build clean.
