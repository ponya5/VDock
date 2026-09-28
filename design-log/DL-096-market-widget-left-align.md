# DL-096 — Screensaver market widget left alignment

## Problem / ask

The screensaver Markets widget lays its rows out right-aligned
(`.ss-market` column `align-items: flex-end`, `.ss-market-row`
`justify-content: flex-end` — originally designed as a "top-right"
block). In the layout editor the big serif prices crowd/clip the right
edge of the widget box while "MARKETS" sits left. Request: the content
should flow left-to-right starting from the left edge.

## Design

Flip the alignment to left:

- `.ss-market` — `align-items: flex-end → flex-start` so rows and the
  (stretched) section head share the left edge.
- `.ss-market-row` — `justify-content: flex-end → flex-start`; DOM order
  (symbol → price) is already the desired left-to-right reading order.
- Comments updated (the widget is no longer a right-aligned block).
- Widget position/scale untouched — this only changes alignment inside
  the box; the saved layout center stays where the user placed it.

## Implementation Results

- `.ss-market` `align-items: flex-end → flex-start`;
  `.ss-market-row` `justify-content: flex-end → flex-start`. DOM order
  (symbol → price) unchanged — rows now read `BIT $82,834` /
  `ETH $2,642.45` from the left edge under the left-aligned "MARKETS"
  head instead of hanging off the right edge of the box.
- Section head keeps `align-self: stretch` so the hairline still spans
  the widget width; stale "top-right"/"right-aligned" comments updated.
- Verified live in the Customise-layout editor (dev server, real
  prices): computed `align-items`/`justify-content` = `flex-start`,
  both rows' left edges at 0; no right-edge clipping.
- `vue-tsc` clean (no code changes outside template comments/CSS);
  `npm run build` green — `dist/` rebuilt for the panel.
