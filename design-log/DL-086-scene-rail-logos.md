# DL-086 — Scene rail: app logos, taller pills, full-pill highlight

## Problem

Three issues in the scene selector (screenshot: the "Claude Code" pill
shows the green waiting ring wrapping the whole segment while the blue
glider fill only covers ~70% of it):

1. **Partial highlight** — `GlassPillSceneSelector`'s glider sizes itself
   `100/N %` per segment, but segments carry `min-width`, padding, and
   the edit-mode badge lane, so real widths diverge from equal shares.
   The mobile rail (`MobileDeckChrome`) already solved this with a
   measured glider; the desktop rail never got the port.
2. **No app identity** — segments show a generic FA icon. The template
   gallery has real logos (`claudecode-color.png`, …) which scenes
   should inherit: `scene.appId` is stamped with the template id on
   apply (`SettingsView` line ~2184) and `appIdForExe` stamps the same
   ids on auto-created scenes.
3. **Slim rail** — 48px pills leave no room for a legible logo.

## Changes

- `services/appDetection.ts`: `sceneLogo(scene, integrations)` —
  stamped `appId` → template `logo` (map built once from
  `templateCategories`); fallback through `resolveSceneProfileId` with
  a profile→template alias table (`copilot`→`github-copilot`). No logo
  asset ⇒ `null` ⇒ caller keeps the FA icon.
- `GlassPillSceneSelector.vue`: measured glider ported from
  `MobileDeckChrome` (offsetLeft/offsetWidth + ResizeObserver +
  re-measure on index/scenes/edit-mode/fonts-ready); `.segment-logo`
  `<img>` precedes the FA-icon fallback; `min-height` 48→56px, logo
  26px, label max-width bumped.
- `MobileDeckChrome.vue`: same `segment-logo` (20px), `min-height`
  44→48px — mobile stays compact but the logo reads.
- The waiting/live dots and the `agent-waiting` ring already size from
  the segment box — measuring the glider to the same box is what makes
  the active highlight cover icon+label fully.

## Implementation Results

Implemented as designed:

- `sceneLogo()` in `services/appDetection.ts` — raw `appId` first
  (gallery ids `'claude'`/`'claude-code'` differ deliberately), then
  canonical profile id via `PROFILE_TO_TEMPLATE_ID` aliases; `null`
  falls back to the FA icon.
- Desktop rail: glider now measured (`offsetLeft`/`offsetWidth` +
  ResizeObserver + `document.fonts.ready` + watches on index/scenes/
  edit-mode) — verified: active 159px "Claude Code" segment gets a
  159px glider exactly aligned; Media 107→108px. `scrollIntoView`
  guarded for jsdom.
- Logos render in both rails: Claude Code shows
  `claudecode-color.png`; Cursor/Websites keep FA icons (no bundled
  logos). Pill heights 48→56px desktop, 44→48px mobile; logos 26px /
  20px.
- Verified: desktop 1280px (screenshot
  `design-log/refs/scene-rail-logos-*.png`) and a real iPhone 13
  landscape WebKit context — logos render, glider covers the active
  pill, `scrollWidth` overflow = 0.
- `agent-waiting-glow.test.ts` mock updated with `sceneLogo`; 303/303
  frontend green, `vue-tsc` clean, `dist` rebuilt.
