# DL-037 — Professional logo on the About screen

## Background
User supplied an engraved-style "DS" eye emblem and asked for it as the
logo on the About screen.

## Problem
The About brand block uses a generic FontAwesome `table-cells-large`
icon in a gradient tile — placeholder art, not the product logo.

## Design
- Ship the image as `frontend/public/assets/branding/vdock-logo.jpg`
  (public assets are served at `/assets/...` and precached by the PWA).
- Replace the icon inside `.about-logo-tile` with an `<img>` —
  `object-fit: cover` so the square art fills the 64px rounded tile,
  keeping the existing ring/shadow chrome.
- The artwork is black ink on white — the tile reads as a clean light
  badge on the dark card; add a thin inner ring so the edge stays crisp.

## Implementation Plan
- [x] Copy asset
- [x] Swap tile content + CSS
- [x] Verify at 1024×600

## Implementation Results
- `frontend/public/assets/branding/vdock-logo.jpg` (281KB, 1024² art).
- `.about-logo-tile` now wraps `<img class="about-logo-img">`
  (object-fit: cover); tile background switched to `#f5f3ec` light badge
  so the black-on-white artwork reads cleanly on the dark card.
- **Deviation**: used `:src` binding, not literal `src=` — the Vue
  compiler's transformAssetUrls turns literal `/assets/...` srcs into
  imports that vitest can't resolve (broke property6_settings.test.ts).
  Matches how DeckButton/appBackgrounds reference public assets.
- Verified live: img 200 + decoded, tile renders the DS emblem.
- Tests: 226/226 vitest, vue-tsc clean, dist rebuilt.

## Verification Criteria
- Logo renders inside the tile; no layout shift; tests clean. ✓
