# DL-140 — Settings page unreachable/broken at ≤880px (clipped scrollport)

## Problem

User report: "when remove media control .. the settings screen broke." —
screenshot showed the standalone Settings window (`/settings?standalone=1`)
rendering only the middle of the Widgets panel (Sports News → System Stats),
with the nav, topbar, sub-tabs, the three panels above, the preview rail and
every row above Sports News all missing — while the footer rendered normally
below. It looked like a Vue partial-render after toggling a widget.

## Investigation

All 17 screensaver toggles (every widget row, Clock, Media controls,
Widget overlay, skins, style select) were clicked live against the built
bundle: DOM integrity held every time — zero Vue errors, all panels and the
rail present. The break was not in the toggles at all.

The pixel/DOM forensics told the real story:

- The screenshot's content column had **no rounded panel top** — the panel
  continued above the viewport → the page had *scrolled*.
- The scrollbar sat at the **window edge** → the document (or #app) was the
  scroller, not `.content`.
- Below ~880 CSS px (`@media (max-width: 880px)` in `SettingsView.vue`) the
  layout intentionally switches to a body-scroll page: `.settings-app` gets
  `height:auto`, `.main`/`.content` become `overflow:visible`, `.nav` becomes
  a sticky top strip and `.settings-dock` pins `sticky; bottom:0` (its CSS
  comment literally says "pins it in the ≤880px body-scroll layout").
- **But `#app` keeps `height:100dvh; overflow:hidden`** (global rule in
  `App.vue`). So the collapsed settings page grows to ~3400px and gets
  clipped at the viewport — content below the fold is unreachable by design.
- `overflow:hidden` boxes still scroll via wheel/keyboard/`scrollTop`, so the
  window *did* scroll — but the sticky nav failed to hold (it sticks inside
  a scrollport that fights the clip), the sticky footer glued itself to the
  bottom of the clip box, and the scrolled content painted stale/black.
  Net result: exactly the screenshot — mid-list rows, no chrome, floating
  footer.

Trigger path: the user toggled a widget/media control near the bottom of the
page; the layout change (or the follow-up scroll to see the effect) moved
#app's hidden scrollport and the page "broke". Any toggle would have done it.

## Fix

1. **Unclip #app on the settings route at the collapsed breakpoint.** The
   body-scroll design needs the document to actually scroll. App.vue adds a
   `settings-route` class on `#app` when `route.path === '/settings'` (covers
   both the in-app settings and `?standalone=1`), plus a global media query:

   ```css
   @media (max-width: 880px) {
     #app.settings-route {
       height: auto;
       min-height: 100vh;
       min-height: 100dvh;
       overflow: visible;
     }
   }
   ```

   Scoped to the settings route so the dashboard's fixed-viewport deck is
   untouched at the same width.

2. **Type-guard composite settings on apply.** `screensaverWidgets` and
   `recentActions` were assigned from remote/local payloads unchecked —
   a malformed `null`/non-array would make `.includes()`/`.length` throw
   inside the Settings template mid-patch (a genuine partial-render path).
   Same for `screensaverBackground`/`background` — `isImageBackground()`
   calls `.startsWith` on the value. All now validate before assigning.

## Implementation Results

**Done:**

- `App.vue` — `#app` gains a `settings-route` class whenever
  `route.path === '/settings'` (covers `?standalone=1`), and a global
  `@media (max-width: 880px)` rule releases the clip:
  `#app.settings-route, #app:has(> .settings-route) { height:auto;
  min-height:100dvh; overflow:visible }`. Both selectors are needed —
  index.html's mount point *and* App.vue's own root div both carry
  `id="app"` (a pre-existing duplicate id), so the outer mount element
  was still clipping even after the inner one released.
- `SettingsView.vue` — the collapsed `.nav` used `background: var(--bg-1)`,
  a variable that doesn't exist in this palette, so it silently resolved
  transparent and rows painted through the pinned rail once scrolling
  worked. Now `var(--bg)` (opaque).
- `stores/settings.ts` — `applySettingsObject` now requires
  `Array.isArray` for `screensaverWidgets`/`recentActions` and
  `typeof === 'string'` for `screensaverBackground`; `migrateBackground`
  rejects non-string values on all three inputs.
- `data/backgrounds.ts` — `isImageBackground` returns false for
  non-strings instead of throwing on `.startsWith`.
- New `settings-malformed-payload.test.ts` — 9 tests covering non-array
  widget lists, non-string backgrounds, and that valid arrays still apply.

**Verified live** (built bundle on :5000, 800×580 standalone window —
below the 880px collapse breakpoint):

- Before: `.settings-app` measured 3423px inside a 580px `#app` with
  `overflow:hidden`; `documentElement.scrollHeight` was 580 (nothing could
  scroll); scrolling `#app` moved content with stale/blank paint — the
  user's exact screenshot state.
- After: document scrolls (scrollHeight 3460), every section and row is
  reachable and paints, the nav rail pins opaque at the top, the dock
  footer pins at the bottom.
- All 17 widget/media/clock toggles clicked live — DOM integrity held in
  every snapshot; the toggles were never the bug.

Suites: 569/569 vitest (9 new), `vue-tsc` clean, `npm run build` clean —
`dist` rebuilt for the panel.
