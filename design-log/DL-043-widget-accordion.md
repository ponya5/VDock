# DL-043: Collapsible widget cards — zero-scroll Widgets tab

## Problem

Appearance → Screen Saver → Widgets held eight detailed config cards
(~2900px of stacked content). Even a dense 3-column masonry layout
overflowed the 600px viewport to ~1450px, forcing long scrolls on the
7-inch touchscreen — the opposite of the "use free width, don't scroll"
goal in DL-041.

## Design

Accordion pattern: the tab has two states.

- **Overview** — the Screensaver Widgets picker spans full width; the
  seven config cards render as compact collapsed headers in a dedicated
  4-column `.widget-cards-grid` (title + chevron only, body hidden).
- **Editing** — tapping a card header opens that card full-width
  (`grid-column: 1 / -1`) while the collapsed strip and the picker's
  toggle list fold away (`picker-collapsed`), so the tab still fits
  one viewport. Tapping the header again (or the same card) returns to
  the overview. Only one card can be open at a time.

`openWidgetCard` ref + `toggleWidgetCard()` in SettingsView; enabling a
widget toggle auto-opens its card for immediate configuration.

## Implementation Results

- Overview fits at max-bottom **559px**; open states: News 594,
  World Clock 556, Stocks 510, Weather 510 — all inside 600px.
- Narrow (520px): grid falls to 1 column, no horizontal scroll in
  either state.
- `frontend/src/views/SettingsView.vue` only. 226/226 frontend tests,
  typecheck clean, live-verified at 1024×600 and 520×800.
