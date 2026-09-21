# DL-062: Mobile dashboard layout fit

S21 landscape screenshots showed the mobile deck still misfitting:

- **Docked sidebar** held a ~190px dead strip on the left — config-bound
  dead width on an 863px screen.
- **"Show Header" pill** sat on top of the first button row: the fixed
  reveal trigger is an 84px transparent hit-strip across the top — on a
  360px screen it covered the top row both visually and for touches.
- **Revealing the header** put it back in-flow — ~150px of header crushed
  the deck into ~180px with 40px buttons.
- **Footer** spent ~56-64px on nothing but page dots.

## Design

All fixes keyed off the shared `useMobileViewport` flag (DL-061):

- **Docked sidebar hidden on mobile** — `v-if` + `with-docked-sidebar`
  class gated in DashboardView; the width goes back to the grid.
- **Header becomes an overlay on mobile** — `.deck-header-wrapper.mobile`
  is `position: absolute` (dashboard-view gets `position: relative`), so
  revealing the header floats it over the deck for its 5s autohide instead
  of shrinking the grid. Header internals slim: icons 42px (resetting the
  touch-mode `min-*` floor that silently wins over width/height), avatar
  36px, scene segments 36px via `:deep`, tighter padding — ~64px total.
- **Reveal trigger slimmed** — hit strip 84→34px, pill 40→24px; and
  `.main-content` gains `padding-top: 34px` on mobile so the pill lives in
  a reserved strip: zero visual overlap, zero touch interception of the
  first button row.
- **Footer slimmed to 44px** — the touch-target floor the page dots need
  (a 30px attempt violated property22's 44px minimum; reverted).

## Implementation Results

Verified live at 863×360 mobile landscape (stubbed touch):

- Sidebar gone; deck spans full width. Buttons 72→**83×83px**.
- Reveal pill: 24px at top:4; first button top:43 — no overlap, and the
  34px trigger strip covers only the reserved padding.
- Header revealed: 64px absolute overlay at top:0 — grid unchanged at
  282px, buttons stay 83px; autohide returns it.
- Footer 44px with compliant 44px page-dot targets.
- `vue-tsc` clean, production build clean, 239/239 frontend tests.
