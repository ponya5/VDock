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

## Follow-up: the same truncation resurfaced on landscape phones (2026-09-27)

### Problem

The user's Media scene rendered with truncated labels ("Volu…", "Previ…")
on a phone — the exact symptom this entry fixed, but DL-060 later made
mobile landscape-only, and this entry's own aspect trigger (`aspect < 0.7
|| aspect > 1.3`) is a heuristic over the CONTAINER's aspect ratio, not the
grid's actual cell count. A scene sized for a wide desktop grid (Media's
`3×5`) can land inside that "normal" 0.7–1.3 window on a landscape phone by
coincidence even though each *cell* is much smaller than a desktop cell —
compact mode never activates, so `effectiveButtonSize` never applies the
`cellPx / 88` downscale, and icon/label sizing meant for a ~200px+ desktop
cell overflows a ~150px phone one.

### Fix

`DeckGrid.vue`'s `cellMetrics` now forces `compact: true` whenever
`useMobileViewport().isMobileViewport` is true, in addition to the
existing aspect-ratio heuristic. Every phone — portrait or landscape —
always gets the fit-to-screen, correctly-downscaled cell sizing this entry
introduced; the aspect check still does its job for a resized desktop
window with no touch/viewport signal to key off.

### Verification

- Frontend: 59 files / 254 tests green; `vue-tsc --noEmit` clean.
- Not yet verified live on a physical phone from this session.

## Follow-up: mobile preview thumbnail on the Connect page (2026-09-27)

### Problem

The user provided a real photo (two phones side by side, Media scene on one
and Claude Code on the other) and asked for it in two places: the README's
mobile section, and as a thumbnail next to the QR code on **Settings →
Connect a device**, so someone about to scan it can see what they're about
to get before they do.

### Fix

- README: added the photo as a centered hero image (`docs/assets/screens/
  mobile-devices.jpg`) at the top of "Control it from your phone", same
  treatment as the existing `panel-on-desk.jpg` hero — image + italic
  caption, ahead of the existing side-by-side scene screenshots.
- Settings → Connect a device: added the same photo (`frontend/public/
  assets/help/mobile-preview.jpg`, the in-app static-asset convention
  already used by the Help & Guide screens) as a second column beside the
  QR canvas, with its own caption. `.qr-row` was restructured into two
  flex columns (`qr-code-col`, `qr-preview-col`) rather than reusing the
  generic `.row-control` class — the existing `.row.stack .row-control`
  rule forces `display: block` at higher CSS specificity than a bare
  `.qr-row` rule could override cleanly.
- Caught mid-edit by the existing frontend suite: a static `<img
  src="/assets/...">` attribute (rather than this file's own established
  `:src="'/assets/...'"` bound-string pattern, e.g. the nav logo two lines
  up) trips Vue's compile-time asset-URL transform and broke a test file's
  SSR-ish import resolution. Matched the existing convention instead.

### Verification

- Frontend: 59 files / 254 tests green; `vue-tsc --noEmit` clean.
- Not yet viewed live in the running Settings page from this session.

## Follow-up 3: size up and right-align the mobile preview thumbnail (2026-09-27)

### Problem

The preview thumbnail added in Follow-up 2 was too small to read at a
glance (180px, sitting immediately next to the QR code) — the user asked
for it much bigger and pushed to the right edge of the row, level with
the QR code, without touching the "CONNECT A DEVICE" instruction box above
it.

### Fix

`.qr-preview-img` grew from 180px to 380px wide (capped at `max-width:
100%` so it never overflows on narrow panels). `.qr-preview-col` got
`margin-left: auto` so it hugs the right edge of `.qr-row` instead of
sitting flush against the QR code, and `.qr-row`'s `align-items` changed
from `flex-start` to `center` so the two columns line up in the middle
now that they're very different heights. `.connect-steps` (the numbered
instruction box) is a separate element entirely and was untouched.

### Verification

- Frontend: 59 files / 254 tests green; `vue-tsc --noEmit` clean.
- Confirmed live via a browser screenshot against the running dev
  server — QR code and instruction box unchanged, preview image now
  large and right-aligned at the same vertical position as the QR.
