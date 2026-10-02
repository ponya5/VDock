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

## Follow-up — short-viewport collapse (footer mid-screen on the panel)

### Problem

User report (panel): "when toggle settings in screensaver screen settings
the footer comes up and break the ui — like clicking toggle media buttons
and toggling types of widgets." Screenshot: a 1024×547 frame where
`.settings-app` is ~92px tall — an empty sunken nav sliver at the left, the
bottom slice of the widgets card ("Now Playing" row, toggle on), the dock
footer pinned at ~y68–92, and a solid `--bg` void filling the rest.

### Investigation

Pixel forensics: left strip = `--bg-sunken` (nav column), card = `--panel`,
gutter/right zone = the settings-local `--bg #0a111f`, void below y=92 =
body's literal `#0f1726` (main.css). So `.settings-app` genuinely ended at
~92px while the window was 547px tall — `100dvh` resolved to ~92.

`index.html` carries `interactive-widget=resizes-content` in its viewport
meta: when a virtual keyboard opens (or the window is otherwise squeezed to
a sliver), the **layout** viewport shrinks — `vh`/`dvh` collapse to the
visible strip. The fixed-height grid (`min-height:100dvh; overflow:hidden`)
then squeezes the whole shell into that strip: row 1 becomes a sliver,
`.nav`'s children overflow invisibly, `.content`'s inner scroller keeps its
scrollTop (showing whatever row was being toggled), and the sticky dock
glues to the bottom of the 92px container — mid-screen. Every toggle
"breaks" the UI because the break is the collapsed viewport, not the
toggle.

DL-140's fix only covers the width axis (`max-width: 880px`). A viewport
that is wide but short — the panel with its touch keyboard up, a docked or
resized window — keeps the fixed-height clipped shell.

### Fix

1. Extend the body-scroll fallback to short viewports. The rules that turn
   `.settings-app` into a normal scrolling document (`height:auto;
   overflow:visible`, `.main`/`.content` released, `.topbar` static) now
   apply at `(max-width: 880px)` **or** `(max-height: 480px)`; the ≤880px
   block keeps its single-column/mobile-only overrides on top.
2. `App.vue` — the `#app` clip release media query gains the same
   `max-height: 480px` branch so the document can actually scroll.
3. `.settings-dock` goes `position: static` in both body-scroll modes — a
   viewport-pinned footer is the literal "footer comes up"; in a scrolling
   document it belongs at the end of the page.
4. `NotificationCenter` — `.notification-center` was `position: relative`,
   so its in-flow bell added ~37px of document height below the settings
   shell. Now `absolute` (same static position, zero flow footprint).

### Implementation Results

**Done:**

- `SettingsView.vue` — the body-scroll rules (`height:auto`,
  `min-height:100dvh`, `overflow:visible` on `.settings-app`; released
  `.main`/`.content`; static `.topbar`) moved into a shared
  `@media (max-width: 880px), (max-height: 480px)` block; the ≤880px block
  keeps only the mobile layout deltas (single column, top-strip nav,
  stacked rows). `.settings-dock` is `position: static` in both scroll
  modes.
- `App.vue` — `#app` clip release now fires at
  `(max-width: 880px), (max-height: 480px)`, still scoped to
  `.settings-route` so the fixed-viewport dashboard is untouched.
- `NotificationCenter.vue` — `.notification-center` → `position: absolute`;
  the bell keeps its spot at document end but no longer inflates
  `documentElement.scrollHeight` (+37px) below the footer.

**Verified live** (built bundle on :5000):

- `1024×92` (the screenshot's collapsed state): `.settings-app` is a
  2251px scrolling document instead of a 92px clipped sliver; dock is at
  document end, not mid-screen; the void below the shell is gone.
- `1024×400` (wide-short boundary): 2-column rail kept, page scrolls,
  dock `static` at end.
- `1024×547` & `1024×600` (panel-like desktop): unchanged fixed grid —
  `.content` remains the inner scroller, dock pinned as the bottom grid
  row, `docH` === viewport (no stray notification height).
- `800×600` (narrow): body-scroll + top-strip nav as before, but the dock
  no longer floats over content while scrolling — at mid-page scroll it is
  simply off-screen at document end.
- Toggle battery: Media controls on/off, screensaver type select, Now
  Playing and all widget switches — 20+ toggles across the three modes,
  `appH`/`docH`/scroll position stable every time, zero console errors.

Suites: 570/570 vitest, `vue-tsc` clean, `npm run build` clean — `dist`
rebuilt for the panel.

## Follow-up 2 — footer jumps to the top after toggling a screensaver switch

### Problem

User report (desktop Chrome, `/settings?standalone=1`): Appearance →
Screen saver, toggle a setting, and the whole page goes dark with only the
footer ("Created by Daniel S") at the very top and the notification bell
below it. The viewport was neither narrow (>880px) nor short (>480px), so
the earlier body-scroll fallbacks never applied.

### Investigation

Reproduced against the built bundle. Right after a toggle the mount-point
`#app` had `scrollTop: 933`, and its `scrollHeight` was 2353 vs a 720
`clientHeight`, even though the inner shell was exactly 720.

Cause: the visually-hidden inputs/labels are `position:absolute` (`.switch
input`, `.sr-only`). `.switch` — unlike `.seg label` and `.pick` — was not
`position:relative`, so those boxes were positioned against the page, not
`.content`. `.content`'s `overflow:auto` therefore did not clip them; they
inflated `#app`'s scrollable overflow. `#app` is `overflow:hidden`, which is
still a scroll container: focusing the toggled switch made the browser
scroll `#app` ~900px to reveal its hidden input, pushing the entire shell
off-screen and leaving only the dock + the bell (which is rendered after
the shell, below it) visible at the top.

### Fix

1. `.switch { position: relative }` — contains its hidden input and
   `.sr-only` label, like `.seg label` / `.pick` already did.
2. `.content { position: relative }` — backstop so any other `.sr-only`
   descendant (e.g. `TriggersPanel`) can't escape the scroller.
3. `#app { overflow: clip }` (fallback `hidden`) in `App.vue`, and
   `main.css`'s `#app { overflow-x }` switched to `clip` — `clip` crops
   identically but is not a scroll container, so nothing can scroll the app
   out of view again. `main.css` previously set `overflow-x:hidden`, which
   forces `clip` back to `hidden` on the other axis (mixed axes), so both
   rules had to change together.

## Implementation Results (follow-up 2)

- `SettingsView.vue`: `.switch` and `.content` gain `position: relative`.
- `App.vue`: `#app` gets `overflow: clip`; `main.css`: `#app` `overflow-x`
  → `clip`. Verified computed style is `clip/clip` on both `#app` nodes.

**Verified live** (built bundle on :5000, standalone settings, 1280×720):
before the fix a toggle left `#app.scrollTop = 933` and `.settings-app` at
`top: -933`. After: Screen saver (10 switches) and Buttons (6 switches),
each driven with `scrollIntoView` + `focus` + click — 0/16 displaced the
shell, `#app.scrollTop` stayed 0, `.settings-app` stayed at `top: 0`.

Suites: 570/570 vitest, `vue-tsc` clean, `npm run build` clean — `dist`
rebuilt for the panel.
