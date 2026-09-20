# DL-014 — Touch-friendly header reveal affordances

## Background

VDock targets a 7" touch panel (see DL-009). When `showHeader` is false the
app header collapses and two reveal affordances remain:

- `DockedSidebar.vue` — a small "Docked Buttons" pill
  (`.header-toggle-button`, ~90×26 px) in the sidebar header.
- `DeckHeader.vue` — `.header-reveal-trigger`, a full-width 84 px invisible
  hit area whose only visible part is a 96×10 px grey bar (`.reveal-handle`).

## Problem

On a touchscreen both visible affordances are too small and neither says what
it does: "Docked Buttons" labels the column rather than the action, and the
centre bar is a thin line with no icon or label. Users can't tell that
tapping reveals the top header.

## Design

Follow the DL-009 pattern — consume `--touch-multiplier`,
`--min-touch-target`, `--spacing-touch-*` instead of inventing new scaling.

### DockedSidebar.vue

- `.header-toggle-button` div → real `<button type="button">` with
  `@click.stop` (parent `.sidebar-header` keeps its click handler so the
  padding strip still toggles; `.stop` prevents a double emit).
- Relabel to "Show Header" + `chevron-down` icon (the header slides down
  from the top edge). Full-width, `min-height` floored at
  `max(--min-touch-target, 44px × multiplier)` with the plain `44px`
  baseline kept for the Property-22 regex, `touch-action: manipulation`,
  font scaled by `--touch-multiplier`, text allowed to wrap on the 100 px
  compact sidebar.
- `.sidebar-header` padding → `--spacing-touch-md` fallback chain.
- `.add-btn` (edit-mode "+" in the same header) gets the same 44 px touch
  floor — it was a 24 px target.

### DeckHeader.vue

- Keep the 84 px full-width invisible hit area and swipe-down gesture.
- Replace the trigger's `.reveal-handle` bar with `.reveal-pill`: a ~40 px
  glassy pill containing `chevron-down` + "Show Header" — an obvious,
  labelled tap target. `.reveal-handle` stays as-is for the separate
  collapse handle inside the open header.

## Implementation Plan

- [x] Phase 1: DockedSidebar toggle button + add-btn touch floor
- [x] Phase 2: DeckHeader reveal pill

## Trade-offs

The sidebar pill loses the "Docked Buttons" column title while collapsed;
action clarity was judged more valuable than the label. The centre affordance
becomes more visually prominent (a labelled pill vs a barely-visible bar) —
acceptable since it only renders while the header is hidden.

## Verification Criteria

- `vue-tsc` clean, vitest suite passes.
- Toggle button and reveal pill both ≥44 px tall at normal mode and scale in
  tablet mode; both reveal the header on tap.

## Implementation Results

- Phase 1 (DockedSidebar): `.header-toggle-button` is now a real full-width
  `<button>` labelled "Show Header" with a `chevron-down` icon, 44 px →
  `max(--min-touch-target, 44px × multiplier)` min-height, touch padding and
  `touch-action: manipulation`; `@click.stop` emits `toggleHeader` while the
  surrounding `.sidebar-header` strip stays clickable. `.add-btn` floored at
  the same 44 px touch target (was 24 px). Header padding/icon/font consume
  `--spacing-touch-*` / `--touch-multiplier`.
- Phase 2 (DeckHeader): the trigger's 96×10 px `.reveal-handle` bar was
  replaced by `.reveal-pill` — a frosted pill with `chevron-down` + "Show
  Header" text (40 px → 60 px capped scale). The 84 px full-width invisible
  hit area and swipe-down gesture are unchanged; `.reveal-handle` still
  serves the collapse handle inside the open header.
- Tests: vitest 175 pass (49 files), `vue-tsc --noEmit` clean.
- Manual verification on the 7" panel outstanding.
