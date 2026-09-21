# DL-051 — Screensaver widget-toggle bug; Server & About layout cleanup

**Date**: 2026-09-21
**Status**: Implemented

## Background

Three settings issues reported:

1. **Bug**: enabling/disabling a screensaver widget made the whole
   picker option list disappear.
2. Server Configuration cards render at very different heights — the
   masonry column flow leaves ragged bottoms and dead space.
3. About screen layout needed polish — the three action cards (Need
   help? / Connect / Support) had uneven heights and floating buttons.

## Analysis

The toggle bug was `toggleScreensaverWidget` setting
`openWidgetCard = id` on enable — which flips `picker-collapsed` on the
picker section and hides `.widget-toggle-list` via CSS. Worse,
disabling a widget while its config card was open left `openWidgetCard`
dangling: the picker stayed collapsed with no card open to close it.

Server tab used `settings-grid-masonry` (CSS columns): 4 cards flowed
into columns purely by source order with nothing evening their heights.

## Design

- `toggleScreensaverWidget` no longer auto-opens the config card on
  enable — the picker stays put and the new collapsed card header
  appears in the strip below. On disable, `openWidgetCard` is cleared
  if it pointed at the removed widget.
- Server tab: merged the one-toggle "Navigation" card into "Startup &
  Navigation" (3 toggles), and switched the grid from masonry to
  `settings-grid-even` — `repeat(auto-fit, minmax(280px, 1fr))` +
  `align-items: stretch`, so the 3 cards render as one equal-height
  row that collapses cleanly on narrow screens.
- About tab: `.about-grid` switched to `align-items: stretch` so the
  three side cards share a height; cards are now flex columns with
  their action area (`about-actions` wrapper on the help buttons,
  `.about-links`, `.kofi-btn`) pinned to the bottom edge via
  `margin-top: auto` — all card buttons share a baseline.

## Implementation Results

Verified live at 1568×830 and 1024×600:

- Toggling widgets on/off leaves the picker fully visible; the
  disabled widget's config card drops out of the strip.
- Server tab renders Startup & Navigation | Connection | Connect a
  device as three equal-height aligned cards; 2-up wrap at 1024.
- About tab's three action cards equalize with buttons bottom-aligned.

`vue-tsc` clean, 231/231 frontend tests pass.

## Follow-up — widget strip leaking onto Button Behaviour (2026-09-21)

The collapsed widget-config strip (`.widget-cards-grid`) sat outside the
`appearanceSubTab === 'screensaver'` container and only checked
`screensaverSubTab === 'widgets'`. Since `screensaverSubTab` is sticky,
visiting Screen Saver → Widgets then switching to Button Behaviour left
the strip rendered on the wrong page.

Fix: parent `v-if` now requires both `appearanceSubTab === 'screensaver'`
and `screensaverSubTab === 'widgets'`. Audited for duplicated settings —
none: each widget setting (weather size/location, text size, feeds,
world clock) lives in exactly one card; the leak was the only issue.

Verified live: strip absent on Button Behaviour with sticky 'widgets'
state, present with all 6 cards under Screen Saver → Widgets.
`vue-tsc` clean, 231/231 tests pass.

## Follow-up — Button Display toggle-pill alignment (2026-09-21)

The `.toggle-grid` pills on Button Behaviour → Button Display had
uneven heights and misaligned controls: the wrapped "Wiggle buttons in
edit mode" label and the Press-sound help text pushed each pill's
toggle/reset row to a different y-position (`justify-content:
flex-start` stacked content from the top).

Fix: `grid-auto-rows: 1fr` on `.toggle-grid` equalizes every pill to
the tallest content, and `margin-top: auto` on
`.toggle-grid .toggle-row-end` pins each control cluster (reset +
switch/select) to the card's bottom edge — one shared baseline across
all pills.

Verified live: all 7 pills measure 123px; row-1 controls share y=437;
the Sound-style select's bottom edge aligns with the toggles (604).
`vue-tsc` clean.
