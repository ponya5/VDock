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
