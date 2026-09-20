# DL-035 — Button Behaviour pane split into sub-tabs

## Background
User: "break button behaviour setting screen into sub tabs (button
display, live preview and touch mode) — make sure that each screen has
save and apply button to take affect." Same pattern as DL-032's
screensaver Widgets/Settings/Backgrounds split.

## Problem
The Button Behaviour pane stacks three unrelated cards (Button Display,
Live Preview + apply-all, Touch Mode) in one masonry column — a long
scroll on the 1024×600 panel. And while settings autosave via the store's
deep watch, there's no explicit "make it so" affordance per screen —
users (and settings opened in a second window) get no confirmation the
dashboard picked the change up.

## Design
- Nested `buttonsSubTab` ref: 'display' | 'preview' | 'touch', same
  `.sub-tab-bar` styling as the screensaver pane (nested directly under
  the Appearance sub-tabs when 'buttons' is active).
- Each section gets `v-if` on its sub-tab — one card visible at a time.
- Per-tab apply:
  - **Display / Touch**: `saveAndApplyButtonSettings()` —
    `settingsStore.saveSettings()` + `requestVdockRefresh()` (same
    cross-window poke `applyButtonBehaviourToAll` uses) + success toast.
    Autosave already covers same-window state; the button makes it
    explicit and covers the separate-window case.
  - **Preview**: keeps `applyButtonBehaviourToAll` ("Save & Apply to All
    Buttons") — it is the screen's save/apply action.
- Search index: the three existing 'buttons' hits get a `deepTab` field
  so a search lands on the right nested tab.

## Implementation Plan
- [x] Phase 1: nested sub-tab bar + per-section v-if + ref
- [x] Phase 2: per-tab apply buttons + search deepTab wiring
- [x] Phase 3: verify all three tabs render disjoint sections live

## Implementation Results
- Nested `.sub-tab-bar` under Appearance→Button Behaviour:
  Button Display | Live Preview | Touch Mode, one card each.
- Apply actions: Display + Touch get `saveAndApplyButtonSettings()`
  (saveSettings + requestVdockRefresh + toast); Preview keeps
  "Save & Apply to All Buttons".
- Search: `deepTab` field on `SettingsSearchEntry`; the three 'buttons'
  hits route to display/preview/touch; screensaver hits got deepTabs
  too (widgets/settings).
- Live verified at 1024×600: each tab renders exactly one section with
  its apply control; clicking Save & Apply fires the "Applied" toast.
- Tests: 220/220 vitest (4 new), vue-tsc clean, dist rebuilt.

## Verification Criteria
- Each sub-tab shows only its card; switching is instant. ✓
- Display/Touch "Save & Apply" persists + refreshes + toasts. ✓
- vitest + typecheck clean. ✓
