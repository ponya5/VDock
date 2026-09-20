# DL-009 — Small-panel touch scaling for chrome & sidebar

## Context

VDock targets a 7" 800×480 touch panel next to an ultrawide main monitor.
The touch-mode machinery (`touchMode` → `--touch-multiplier`,
`--spacing-touch-*`, `--min-touch-target`) existed and scaled deck buttons,
but the surrounding chrome never consumed it: header circles were a fixed
64 px, the actions sidebar used static `--spacing-*` vars and 52 px rows.

## Decision

Consume the existing CSS vars in chrome rather than inventing a second
scaling system:

- `DeckHeader` — icon circles and avatar scale with
  `min(--touch-multiplier, 1.4)` (capped so a row of them still fits an
  800 px header at tablet mode), header/content min-heights and scene-pill
  height scale fully, small tap targets floor at
  `max(--min-touch-target, 44px × multiplier)` with the plain `44px`
  declaration kept as the fallback/baseline.
- `ButtonActionsSidebar` — `--spacing-*` usages swapped for
  `--spacing-touch-*` (with fallback), row min-heights and fonts scale by
  `--touch-multiplier`, width caps at `min(92vw, 380px × multiplier)`,
  scrollbar widens for finger drag, close/search hit-targets get
  `--min-touch-target`.

Verified at 800×480 + `touchMode: tablet`: icon circles 90 px (was 64),
header min-height 154 px, no horizontal overflow.

**Tests:** vitest 138 pass (dual-declaration kept so the Property-22
44 px regex still sees the baseline), `vue-tsc` clean.

## Addendum — EditSidebar coverage (2026-09-20)

`EditSidebar.vue` — the "Button Actions" panel docked in edit mode — was
missed: DL-009 scaled `ButtonActionsSidebar.vue`, which is the action picker
inside ButtonEditor, not the edit-mode panel. Same treatment applied:

- Width `280px` → `min(92vw, 280px × min(--touch-multiplier, 1.5))` +
  `flex-shrink: 0`. Capped at 1.5 (not the full 2.0) because it shares the
  flex row with the deck grid — uncapped it would take 560 px of an 800 px
  panel.
- `--spacing-*` → `--spacing-touch-*` throughout; category headers, action
  rows, search input and `.btn-control` get the dual
  `44px` / `max(--min-touch-target, 44px × multiplier)` min-height/width
  (baseline kept for the Property-22 regex); fonts and the close button
  scale by `--touch-multiplier`; scrollbar widens to `8px × multiplier`.

`DeckFooter.vue` (page dots, Grid R×C inputs, Add/Delete/Save buttons) got
the same pass:

- Footer `min-height` 44 → `max(44px, 56px × multiplier)`; `.btn-sm` floor
  36 → `44px × multiplier` with scaled padding/font; `.grid-input` 32px →
  `44px × multiplier` tall and `56px × multiplier` wide; page dots scale
  (dot `10px × mult`, padding `17px × mult` — literal kept first so the
  Property-22 regex still reads the 17px baseline); edit section wraps so
  scaled controls can't overflow on narrow widths.

**Tests:** vitest 148 pass, `vue-tsc` clean. Manual verification at 800×480
tablet mode outstanding.
