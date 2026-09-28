# DL-088 — User guide becomes a Settings tab (Guide, between Logs & About)

## Problem

The user guide lived in a 950px modal opened from About → "Help &
guide". Cramped, hidden, and its content lagged the newest features
(scene swipe, waiting glow + snooze, app-path gear, AI Coding
templates).

## Changes

- `UserGuideModal.vue` → `UserGuide.vue`: modal overlay, close
  buttons and `close` emit removed; it renders the guide chrome
  (sidebar + tabbed content) as a full-size panel.
- `SettingsView.vue`: new `guide` tab between Logs and About
  (nav item, `tabs` entry for `?tab=` routing, `PAGE_META`, content
  block). The Apply button hides on guide (same as About/Logs).
  About's "Help & guide" button now navigates to the tab.
- `App.vue`: `UserGuideModal` mount removed; `settingsStore
  .showHelpGuide` ref dropped (its only setter was the About button).
- Guide content refreshed: scene swipe gesture, scene-rail logos,
  agent waiting glow + 3-min snooze, per-template executable-path
  gear, AI Coding templates (Claude Code, Cursor, Antigravity),
  new troubleshooting items.

## Implementation Results

(pending)

- `UserGuideModal.vue` renamed to `UserGuide.vue`, overlay/close chrome
  removed, renders as a bordered panel filling the Settings → Guide
  tab (992×640 live vs the old 950px-modal cap).
- New `guide` tab sits between Logs and About — nav item, `?tab=guide`
  routing, `PAGE_META`, settings search entry. Apply button hidden
  there like About/Logs; About's "Help & guide" button navigates to it.
- `App.vue` modal mount + `settingsStore.showHelpGuide` removed.
- Content updated: scene-swipe gesture + page steppers (Interaction
  Tips), waiting glow + Snooze 3m (Agent Sessions), screensaver widget
  list + layout editor + world-clock defaults, mobile scene rail +
  swipe, template gear/Detect executable popup, two new
  troubleshooting items (missing exe, stale waiting glow).
- Mobile fix beyond the ask: the guide's sidebar used to hide at
  ≤768px leaving 4 of 5 sections unreachable — it now collapses to a
  horizontal scrollable section bar.
- Verified: nav order Logs→Guide→About live; desktop + 390px (zero
  overflow, sections switch); 306/306 tests, `vue-tsc` clean, `dist`
  rebuilt. Refs: `design-log/refs/guide-tab-*.png`.
