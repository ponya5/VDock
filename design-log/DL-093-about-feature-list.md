# DL-093 — About "What's in it" feature list

## Problem / ask

The About tab's "What's in it" section renders the ten product features as
boxed tiles in a 3-column `.grid-3` grid (`.feature` cards with
`background: var(--panel-2)` + border). The boxes look cluttered, the
description sits as a second flex column next to the title so text wraps
awkwardly, and the cards don't match the app's list idiom. Request:
improve the section as a list layout instead of boxes.

## Design

Replace the boxed grid with an unboxed two-column list, matching the
app's existing `.row`/`.kv` hairline-separator language:

- `.feature-list` — `display: grid`, two equal columns, column-gap ~28px;
  collapses to one column under the existing 880px breakpoint.
- Each feature = a row: accent `FontAwesomeIcon` left, text block right —
  bold label (`.feature-title`) with muted description (`.feature-desc`)
  stacked beneath it.
- Hairline `border-bottom: var(--line-soft)` separators per item
  (`padding: 12px 0`, same rhythm as `.row`); items in the last visual
  row drop the border (`:last-child` + `:nth-last-child(2):nth-child(odd)`,
  scoped to min-width 881px so the single-column layout keeps every
  hairline except the last item's).
- The `.row stack picker-row` + `.grid-3` wrappers and the boxed
  `.feature` styles (background, border, radius) are removed; the stray
  unused `.feature-grid-new` rule goes too.

## Implementation Results

- `SettingsView.vue`: `.row stack picker-row` + `.grid-3` wrappers removed
  from the "What's in it" panel; `.feature` items restructured to
  `icon | (title, desc)` — the icon moved out of `.feature-title` into a
  `.feature-text` flex sibling so the description stacks under the label
  instead of sitting beside it as a second flex column.
- New `.feature-list` grid (2 cols, 28px column-gap); `.feature` unboxed —
  no background/border/radius, `padding: 12px 0` + hairline
  `border-bottom`, same rhythm as `.row`/`.kv`. Last visual row drops the
  separator via `:last-child` + `:nth-last-child(2):nth-child(odd)`
  (min-width 881px); ≤880px collapses to one column with every hairline
  except the last item's. Unused `.feature-grid-new` rule deleted.
- Verified live (chrome-devtools MCP against the running dev server):
  two columns at desktop and 1024×600 panel size, single column at
  700px; computed `border-bottom` = 0px on the last row in both layouts.
- `vue-tsc --noEmit` clean; `npm run build` green — `dist/` rebuilt so
  the physical panel picks up the new layout.
