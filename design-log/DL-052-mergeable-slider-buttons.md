# DL-052 — Mergeable slider buttons + Sliders action category

**Date**: 2026-09-21
**Status**: In progress

## Background

User asked for two related things:

1. Sliders should be a first-class member of Button Actions — today the
   three slider specs (`slider_volume`, `slider_brightness`,
   `slider_ui_brightness`) sit in the backend catalog's `custom`
   category, surfacing in the sidebar under "Custom Media" where they
   are easy to miss.
2. Adjacent slider buttons should be mergeable into one wide slider:
   in edit mode, when two sliders sit side by side, a merge button on
   their shared edge merges them into a single button spanning both
   cells.

## Analysis

- `Button.size = { rows, cols }` already exists and is honored
  everywhere it matters: `DeckButton` places itself with
  `gridRow/gridColumn` spans, `emptySlots` marks all covered cells
  occupied, `checkButtonCollision` treats buttons as rectangles, and
  `addButton`/`moveButton` reject overlaps. A merged slider is just a
  button with `size.cols > 1` — no model changes needed.
- `SliderButtonFace` is width-agnostic (track stretches to 100%).
- Store mutations (`addButton`, `removeButton`, `updateButton`) each
  push a history entry; merging must be a single store method so undo
  restores both buttons in one step.
- Edit-mode chrome lives in `DeckButton.edit-overlay`, but a seam
  affordance spans two buttons — `DeckGrid` is the component that knows
  both geometries, so the merge chip belongs there.

## Design

- **Catalog**: new backend category `sliders` ("Sliders",
  `fas:sliders-h`); the three slider specs move from `custom` to it.
  `catalogCategories` appends it automatically — no frontend alias
  needed.
- **Merge store method**: `mergeSliderButtons(leftId, rightId)` —
  validates both are enabled sliders on the same row with equal height
  and `right.col === left.col + left.size.cols`, then
  `left.size.cols += right.size.cols`, removes `right`, single
  `addToHistory` + `saveProfile`. Left button keeps its config
  (target/min/max/step), label, and styling; undo restores both.
- **Seam chips** in `DeckGrid` (edit mode only): for each pair of
  horizontally adjacent equal-height sliders, render a small circular
  chip centered on their shared edge — a grid item anchored to the
  right cell's first column with `justify-self: start;
  translateX(-50% - half-gap)`, vertically centered on the shared
  rows. Click emits `buttonMerge(left, right)` →
  `useButtonActions.handleButtonMerge` → store method + toast.
- Chains work naturally: a 2-wide slider adjacent to another slider
  shows the chip again and merges to 3-wide.
- **ButtonEditor**: bump the size Columns input `max` from 3 to 12 so
  merged sliders stay editable without the spinner clamping them.
- Vertical merging is out of scope (sliders are horizontal controls).

## Implementation Results

Implemented and verified live at 1280×800 in edit mode:

- **Sliders category** — backend catalog now has `sliders` ("Sliders",
  `sliders-h` icon) holding Volume Slider, Brightness Slider and UI
  Dimmer Slider; the sidebar shows them as their own group instead of
  buried under Custom Media. Backend restarted to load it.
- **Merge chips** — `DeckGrid` computes `sliderSeams` (adjacent,
  same-row, same-height sliders) and renders a circular link-icon chip
  centred on the shared edge in edit mode. Clicking merged two volume
  sliders into one 330px (2-cell) slider; the track stretched and a
  drag to ~20% applied the real OS volume. Chains generalise (the chip
  reappears beside an already-wide slider).
- **Undo** — `mergeSliderButtons` is one store mutation = one history
  entry. Wired the existing-but-unreachable history: Ctrl+Z / Ctrl+Y
  (and Ctrl+Shift+Z) now call `undo()`/`redo()` + `saveProfile` in edit
  mode. Verified: merge → Ctrl+Z splits back to two 1-cell sliders →
  Ctrl+Y re-merges.
- `ButtonEditor` Columns cap raised 3 → 12 so merged sliders stay
  editable.
- Test fix during CI: `property8` requires `clamp()`/`var()` font
  sizes — chip icon uses `calc(12px * min(var(--touch-multiplier), 1.25))`.

`vue-tsc` clean, 231/231 tests pass (1 pre-existing jsdom network
error unrelated to this change).

**Note:** the docked sidebar (`DockedSidebar`) renders `DeckButton`s in
its own column — merge chips are `DeckGrid`-only, so docked sliders
don't offer merging (vertical column, horizontal control — correct to
skip).
