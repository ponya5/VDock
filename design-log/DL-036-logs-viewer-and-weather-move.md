# DL-036 — Weather location move + professional Logs viewer

## Background
User: (1) move the Weather Widget Location setting out of "Widgets &
Integration" into Screen Saver → Widgets, so the tab becomes plain
"Integrations". (2) The logs viewer is too small — make it bigger and
beautify the interface (refresh, export, clear all should look
professional).

## Problem
- Weather location lives under App Integration though it only feeds the
  screensaver/dashboard weather widget — miscategorized.
- The logs tab is two masonry cards with a 340px-max viewer and action
  buttons buried under the file list — cramped and tool-like, not
  diagnostic-console-like.

## Design

### Weather location move
- Cut the "Weather Widget Location" section from the integration pane;
  merge its controls (location-mode select + manual city input) into the
  screensaver **Weather Widget** card.
- Rename tab label "Widgets & Integration" → "Integrations"; header copy
  drops "Widget data sources".
- Search index: "Weather Widget Location" → tabId appearance, subTab
  screensaver, deepTab widgets.

### Logs viewer redesign
- `.logs-layout` — flex row sized to fill the settings viewport
  (`calc(100vh − header − page header − padding)`), replacing the masonry
  grid so the viewer gets the remaining width AND height.
- Files card → a fixed ~250px column: scrollable list, size shown as a
  chip badge; footer shows total usage.
- Viewer card → flex column filling the rest:
  - header: file icon + name + size badge
  - toolbar: tail-count select + Refresh + Export (.zip) + Clear All as
    compact grouped buttons (actions live beside the content they touch)
  - `.log-viewer` flex:1 — fills all remaining height instead of the
    340px cap
  - status bar: "N lines shown · updated HH:MM" — `logsUpdatedAt` ref set
    in refreshTail
- Keep DL-023 font clamps; no fixed px font sizes.

## Implementation Plan
- [x] Phase 1: weather-location move + tab rename + search update
- [x] Phase 2: logs layout restructure (template + CSS + status bar)

## Implementation Results
- Weather location cut from the integration pane into a standalone
  "Weather Location" card in Screen Saver → Widgets (always visible —
  it also feeds the docked weather card). Tab renamed to "Integrations",
  header copy updated, search entry re-pointed with deepTab: widgets.
- Logs tab restructured: `.logs-layout` flex row sized
  `calc(100vh - 145px)` (measured against real chrome: 72 header +
  40 padding + ~33 compact page header). Files column ~230px with
  size-badge rows + totals footer; viewer card = toolbar (file name +
  Tail select + Refresh/Export/Clear) + flex:1 `.log-viewer` + status
  bar ("N lines shown · Updated HH:MM", `logsUpdatedAt` ref).
- Toolbar polish: `.btn-sm` compact sizing (touch-mode's 64px inflation
  overridden — a diagnostic toolbar doesn't need pill-sized targets),
  labels nowrap so buttons never wrap to a second row, size badge
  yields below 1100px windows.
- Compact page header variant `.tab-page-header-compact` (title + desc
  inline) — reclaimed ~53px of dead header space.
- Live verified at 1024×600: viewer is 329px tall (was 224 at the same
  viewport; old cap was 340 but the card shared a masonry row), file
  name ellipsizes instead of pushing actions off, all three actions
  functional, Integration tab shows only Auto Switching / Recent /
  Running Apps.
- Tests: 226/226 vitest (6 new), vue-tsc clean, dist rebuilt.

## Deviations
- Location got its own always-visible card rather than living inside the
  Weather Widget card — the widget card hides when the widget is off,
  but the docked weather tile still consumes the location setting.
- Viewer target of "fills viewport" required shrinking the page header
  and overriding touch-mode button sizing; both are scoped to the logs
  tab only.

## Verification Criteria
- Integration tab shows no weather section; screensaver Widgets shows it. ✓
- Logs viewer fills the viewport; toolbar actions work. ✓
- vitest + typecheck clean. ✓
