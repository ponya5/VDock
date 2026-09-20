# DL-034 — Centered, legible docked sidebar info on 7"

## Background
User screenshots of the 1024×600 panel: the docked weather card is
left-aligned with small text; docked info should be centered and clearly
readable on the 7-inch screen.

## Problem
- `.sidebar-weather-card` lays out icon + temp + desc + loc in a
  left-aligned column; at the compact 168px sidebar width the text reads
  small and off-center.
- The card consumes ~150px of vertical budget but doesn't use it
  effectively — cramped left edge, lots of dead space on the right.
- Docked `DeckButton` cells should also verify their label/icon stay
  centered and legible inside the narrow column.

## Design
- Weather card: `align-items: center; text-align: center` — icon centered
  on top, temp/desc/loc centered beneath; slightly larger temp and
  secondary lines; keep the card's vertical stack (column is only ~140px
  content wide).
- Buttons: `.button-content` already centers; verify live and bump the
  compact-column label legibility if needed via existing font-size clamps
  (no fixed px — DL-023 property tests require clamp()).

## Implementation Plan
- [x] Phase 1: weather card centering + size bump
- [x] Phase 2: live-verify docked button content centering at 1024×600

## Implementation Results
- Weather card: `align-items:center` + `text-align:center` on the card
  and `.weather-info`; icon bumped 46→52px; temp 2.1rem fixed →
  `clamp(1.9rem, 4vw+1.1rem, 2.5rem)`; desc/loc now clamp-scaled.
- Verified live at 1024×600 (injected card with the component's data-v
  scope attrs — geolocation is stubbed-out in the test browser): all
  elements centered within 3px of card center; temp computes 40px,
  desc 15.2px, loc 13.6px.
- DeckButton `.button-content` already centers — confirmed visually in
  the same screenshot (Demo City label/icon centered in its cell).
- Tests: 216/216 vitest, vue-tsc clean, dist rebuilt.

## Verification Criteria
- Weather icon/temp/desc/loc centered horizontally in the card. ✓
- Text legible at arm's length on 1024×600. ✓
- vitest + typecheck clean. ✓
