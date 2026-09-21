# DL-057 — Mobile deck fit + dedicated Connect page

## Problem

Opened VDock on a phone (`http://<lan-ip>:5000`) — the deck rendered, but
was unusable:

- The grid fills `height:100%` with `grid-template-rows: repeat(N, 1fr)`,
  so on a tall, narrow phone viewport every cell becomes a tall sliver:
  icons/labels clip ("Vol…", "Mute" wrapped mid-word) and `min-width/height:
  60px` on `.deck-button` overflows narrow cells.
- App scanning (the live-dot feature from DL-033) defaulted off, so new
  installs never see scene activity dots.
- "Connect a device" was a section buried at the bottom of the Server tab;
  a first-time mobile user has no obvious path to the QR flow.

## Design

### 1. Adaptive grid cells (`DeckGrid.vue`)

Measure the grid's host (parent element) with a `ResizeObserver`.
`compactCells` activates when the natural cell height exceeds ~1.3× the
cell width (i.e. the 1fr rows would stretch cells vertically) — true for
portrait phones and any tall narrow window, false for desktop and
landscape phones.

In compact mode the grid switches to square cells sized by column width:
`grid-template-rows: repeat(rows, <cellPx>px)`, `align-content: start`,
`overflow-y: auto` — the grid scrolls vertically inside itself instead of
stretching cells, and no parent layout changes are needed. Gap/padding
tighten to 8px.

Icons and labels scale via the existing `buttonSize` pipeline: an
effective size of `min(buttonSize, cellPx / 88)` keeps glyphs proportional
to the cell (≤88px cells shrink, larger cells unaffected). Compact mode
also drops the 60px min-size on `.deck-button` via a scoped `:deep` rule.

### 2. App scanning on by default (`settings.ts`)

`appScanningEnabled` default `ref(true)` + normalization `!== false`, same
pattern as `openSettingsInNewTab`. Users keep an opt-out in Settings.

### 3. Dedicated Connect page (`SettingsView.vue`)

New top-level nav item **Connect a device** between Integrations and Logs
(icon `mobile-screen-button`) hosting the QR flow, previously `#device`
inside Server:

- Steps panel in plain language: 1) phone and PC on the same Wi-Fi,
  2) enable "Allow LAN access" and relaunch once, 3) scan the QR or type
  the deck address — no app to install.
- The existing LAN toggle, deck address + copy, QR canvas, and offline
  warning move over unchanged.
- Entering the tab auto-loads server config and renders the QR
  (`watch(activeTab)` → `nextTick(renderQr)`), so the code is on screen
  without further clicks.
- Server tab keeps Startup/Connection panels; the `device` nav-sub link is
  removed.

## Implementation Results

Verified live against `localhost:5000` (Playwright device emulation):

- **Pixel 7 portrait (412×839):** compact mode activates (aspect 2.2:1),
  cells render as 73×72px squares with icons + full labels readable;
  content scrolls vertically inside the grid. Icon tile's 64px minimum
  initially pushed labels out of the cell — overridden to wrap the scaled
  glyph in compact mode.
- **Pixel 7 landscape (863×360):** cells were squashed to ~30px tall and
  buttons overlapped — the aspect trigger now covers `aspect < 0.7` too;
  129px square cells scroll inside the deck strip.
- **Connect a device page:** new nav item between Integrations and Logs;
  steps card (same Wi-Fi → allow LAN → scan), LAN toggle, deck address +
  copy, QR auto-drawn on tab entry (`watch(activeTab)` → loadServerConfig
  → nextTick(renderQr)). PAGE_META + tabs array + search index updated.
- **App scanning:** default flipped to disabled (`ref(false)`, `=== true`
  normalization, defaults object) — user-requested default.
- vue-tsc clean, 239/239 vitest, production build passes.
