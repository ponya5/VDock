# DL-049 — Remove docked sidebar header; revert proportional settings zoom

**Date**: 2026-09-21
**Status**: Implemented

## Background

Two UI issues reported from the 7-inch/desktop dashboard:

1. The docked sidebar renders a "DOCKED BUTTONS" header row above the
   weather card. It wastes vertical space on a column whose whole job is
   holding buttons.
2. DL-046 added a proportional `--ui-zoom` (up to 1.9x) so the
   1024x600-designed Settings UI grew on large screens. In practice at
   100% browser scale on a desktop the settings render oversized — the
   user wants natural 1x sizing with responsive layout instead.

## Problem

- Sidebar header row (`<h3>Docked Buttons</h3>` + edit-mode "+" +
  "Show Header" fallback button) consumes ~60px of the docked column.
- `.settings-view` applies `zoom: var(--ui-zoom)` — at 1920x1080 that's
  1.8x, making every control comically large.

## Design

### Sidebar header removal

Everything inside `.sidebar-header` is redundant:

- "Docked Buttons" title — pure label, user wants it gone.
- "Show Header" fallback button — `DeckHeader` already renders a fixed
  `header-reveal-trigger` strip with a visible "Show Header" pill when
  `settingsStore.showHeader` is false, so the sidebar copy is a duplicate.
- Edit-mode "+" button — calls `handleAddButton`, which finds the first
  empty slot and emits `addButton`. `DashboardView` maps it to
  `onDockedPlaceholderClick` — the *same* handler each empty-slot
  placeholder already calls. Fully redundant.

Remove: the `.sidebar-header` div, `showHeader` prop, `toggleHeader`
emit, `handleAddButton`, and associated CSS (`.sidebar-header`,
`.header-toggle-button`, `.add-btn`, mobile display:none rule). Update
`gridStyle`'s `paddingBlock` reservation (header no longer rendered;
weather card alone ≈ 180px).

`DashboardView.vue`: drop `:show-header` and `@toggle-header` bindings.
`settingsStore.showHeader` stays — DeckHeader and the `toggle_header`
button action still use it.

### Settings zoom revert

Remove `--ui-zoom` entirely:

- `SettingsView.vue`: `.settings-view` back to `height: 100vh;
  width: 100vw`, no `zoom`.
- `UserGuideModal.vue`: drop `zoom`, `max-width: 95vw`,
  `max-height: 92vh`.
- `App.vue`: delete `updateUiZoom`, `BASE_W`/`BASE_H`, and the resize
  listener (no other `--ui-zoom` consumers remain).

Responsiveness comes from the existing layout: masonry columns
(`column-width: 340px`), `auto-fill minmax(300px,1fr)` grids, and the
900px/640px media queries already collapse the nav rail and stack
content. At 1024x600 zoom was already 1 — zero change on the panel.

## Trade-offs

- Rejected: keeping zoom with a lower cap (e.g. 1.2). Still proportional
  scaling, not responsive layout — and DL-046's "rendered miniature"
  concern is better served by reflowing columns than enlarging pixels.
- Rejected: keeping a slim edit-mode-only header for the "+" button.
  Placeholders cover the same action; a floating button would overlap
  the weather card.

## Verification Criteria

- Dashboard: no "DOCKED BUTTONS" label; weather card sits at top of the
  sidebar; edit mode still shows "+" placeholders; hidden header still
  revealable via the top pill.
- Settings at 1920x1080 @100%: natural desktop sizing, nav rail 216px,
  masonry reflows to more columns; no h/v overflow.
- Settings at 1024x600: unchanged (zoom was already 1).
- `vue-tsc` clean; vitest suite passes.

## Implementation Results

- `DockedSidebar.vue`: removed `.sidebar-header` block (title, "Show
  Header" fallback, edit-mode "+"), `showHeader` prop, `toggleHeader`
  emit, `handleAddButton`, `addButton` emit, and all associated CSS
  (~150 lines). `gridStyle` weather reservation bumped 150→180px since
  it previously also covered the header row.
- `DashboardView.vue`: dropped `:show-header`, `@toggle-header`,
  `@add-button` bindings and the `onDockedAddButton` alias.
- `SettingsView.vue`: `.settings-view` is plain `100vh`/`100vw` — no
  zoom.
- `UserGuideModal.vue`: zoom removed; `max-width: 95vw`,
  `max-height: 92vh`.
- `App.vue`: `updateUiZoom`, `BASE_W`/`BASE_H`, and the resize listener
  deleted — `--ui-zoom` has no remaining consumers.

### Verified live (dev server, Playwright)

| Viewport | Result |
|---|---|
| Dashboard 1920x1080 | No "DOCKED BUTTONS" label; `.sidebar-header` absent from DOM; sidebar = weather slot + grid |
| Settings 1920x1080 | Natural 1x scale; masonry reflows to 4 columns; no overflow |
| Settings 1024x600 | Identical to before (zoom was already 1) |
| Settings 800px | Nav rail collapses to icon-only via existing ≤900px media query |

Header show/hide unaffected: `DeckHeader` renders its own fixed
"Show Header" reveal pill when hidden, and the `toggle_header` button
action still flips `settingsStore.showHeader`.

`vue-tsc --noEmit` clean; vitest 231/231 pass. No deviations from the
plan above.

## Follow-up — wider Scene Editor modal (2026-09-21)

`SceneEditor.vue` was a fixed 500px column that scrolled ~1400px of
fields — cramped on the panel and wasteful on desktop.

- Modal widened to `min(920px, 94vw)`, `max-height: 88vh`; header and
  footer pinned (`flex` column + `overflow: hidden`), only the body
  scrolls — same pattern as `ButtonEditor.vue`.
- `.modal-body` is now a 2-column grid: name/icon/color/button-size in
  the left column, pages/background/active-scene in the right (two
  `.editor-col` wrappers — keeps tab order DOM-linear).
- Below 720px the body collapses to one column (`.scene-editor
  .modal-body` — descendant selector needed to beat the base grid rule
  on specificity, not source order).
- Short screens (max-height 700px) compress padding/margins and allow
  94vh, matching ButtonEditor's compact mode.
- Color palette switched from fixed `repeat(6, 300px-max)` swatches to
  `auto-fill minmax(36px, 1fr)` fluid swatches so it uses the wider
  column; pages list max-height 200→240px.

Verified live: 1920×1080 fits all options with zero scroll
(body 596px content = 596px visible); 1024×600 needs only ~156px of
body scroll with Save/Cancel always pinned; 640px collapses to one
column. `vue-tsc` clean, 231/231 tests pass.
