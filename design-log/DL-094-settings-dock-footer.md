# DL-094 — Settings dock footer bar

## Problem / ask

The settings sidebar footer (`.nav-foot` + `.nav-credit`) is cramped in
the 240px rail: two buttons squeezed side-by-side, credit line + social
icons below, and a large dead gap between the last nav item and the
footer block. Request: improve the footer — suggestion approved was a
full-width dock bar across the whole settings window (Ko-fi button stays
on the About page).

## Design

Move the footer out of the sidebar into a full-width dock bar that spans
under both the nav rail and the content column:

- `.settings-app` grid gains `grid-template-rows: minmax(0,1fr) auto`;
  `.settings-dock` is a third grid child spanning `grid-column: 1 / -1`.
- Dock layout: left = "Created by Daniel S. · v{version}" + the three
  social icon links (LinkedIn/GitHub/site); right = `Reload VDock` +
  `Back`/`Close` ghost-sm buttons (unchanged handlers:
  `refreshVdock()`, `handleSettingsBack`, `isStandaloneSettings` icon/label).
- Styling: `background: var(--bg-sunken)` + hairline `border-top`, so the
  bar reads as a continuous frame edge with the nav rail; slim padding
  (`7px var(--gutter)`), `flex-wrap` for narrow widths.
- `position: sticky; bottom: 0` on the dock: no-op in the desktop
  fixed-height shell, but keeps the bar pinned to the viewport bottom in
  the ≤880px body-scroll layout (nav already sticks top there).
- ≤880px grid rows become `auto minmax(0,1fr) auto` (nav / main / dock)
  so the dock still lands at page bottom on short pages; ≤700px-tall
  panels get reduced dock padding.
- `.nav-foot`, `.nav-foot-btn`, `.nav-credit*` markup + CSS removed;
  aside becomes pure navigation. Modals inside `.settings-app` are
  `position: fixed` so they don't enter the grid.

## Implementation Results

- `.nav-foot` block removed from the sidebar; new `.settings-dock` footer
  sits after `</main>` inside `.settings-app`: credit + three social icon
  links left (`dock-credit`/`dock-credit-link` classes, same look as the
  old `nav-credit`), `Reload VDock` + `Back`/`Close` ghost-sm buttons
  right — same handlers and standalone label/icon logic.
- `.settings-app` grid: `grid-template-rows: minmax(0,1fr) auto`, dock
  spans `grid-column: 1/-1`. ≤880px rows become
  `auto minmax(0,1fr) auto` (top-bar nav / main / dock); ≤700px-tall
  panels get 5px dock padding.
- Dock styled `background: var(--bg-sunken)` + hairline `border-top` —
  continuous frame edge with the nav rail. `position: sticky; bottom: 0;
  z-index: 30`: verified it pins to the viewport bottom on mobile while
  being a plain grid row on desktop.
- Verified live (chrome-devtools MCP): dock bottom edge == viewport
  height at 700×800 (sticky pinned over body scroll), full-width bar at
  1400×800 and 1024×600 with credit left / actions right; sidebar footer
  gone — nav rail is pure navigation.
- `vue-tsc --noEmit` clean; `npm run build` green — `dist/` rebuilt.
