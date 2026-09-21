# DL-059: Settings polish — previews, smaller design picker, slider flex, mobile fit

Six user-reported items in one pass.

## 1. Key Design picker too large

The swatch grid is 5 fluid `aspect-ratio: 1` tiles — on a wide settings
panel each card renders ~130px and the block dominates the page.
Cap tiles at ~88px and centre the grid: same 5-up layout, ~40% less
vertical spend.

## 2. "Dashboard preview" rail broken (Layout & sidebar)

`.mock-dash`, `.mock-dash-side` and `.mock-dash-grid` are used in the
template but have **no CSS** — the mock collapses into an unstyled strip
of pills. Add the missing flex/grid rules so it reads as a miniature
dashboard: proportional sidebar column + 4-col key grid.

## 3. "Background preview" rail broken (Background)

`previewBackgroundStyle` renders `kind === 'component'` backgrounds as a
checkerboard placeholder — reads as broken. The components can't be
mounted directly (they're `position: fixed; 100vw×100vh`), but a
transformed ancestor becomes a fixed-position containing block: mount
the real component inside a `100vw×100vh` viewport div scaled down to
the stage. Checkerboard stays as the `onError` fallback.

## 4. Sliders beyond volume

Slider runtime already supports `volume` / `brightness` / `ui_brightness`
targets; the editor exposes a target select. Add a fourth scalar target —
**per-app volume** (`app_volume`): new `app_volume_get`/`app_volume_set`
cross-platform actions driven through the DL-058 COM worker
(`AudioUtilities.GetAllSessions()` → match `config.process` against
`session.Process.name()`), a `process` config field, editor option, and a
`slider_app_volume` catalog preset.

## 5. Expand a single slider (replaces merge-only UX)

Today a slider can only grow by *merging* with an adjacent slider. New
unified affordance: a widen chip on the slider's right edge in edit mode —
- next cell free → grow `size.cols` by 1,
- next cell a same-height slider → merge (existing op),
- otherwise hidden.
A shrink chip on the left edge reduces `cols` back to 1. New store ops
`expandSliderButton` / `shrinkSliderButton` are history/save wrapped like
merge. The seam-merge chip is absorbed into this mechanism.

## 6. Mobile: fit whole deck to the phone screen

DL-057 made compact cells square but width-driven + scrollable — the user
still has to scroll to see the deck. In compact mode, size cells by
`min(width-driven, height-driven)` and centre the grid: the entire deck
fits the viewport in both orientations, no scrolling.

## Implementation Results

All six items implemented and verified live (localhost + `192.168.1.173:5000`
in an emulated 412×839 / 863×360 viewport).

1. **Design picker** — swatch tiles capped at 76px (were ~130px); grid centred.
2. **Dashboard preview** — added the missing `.mock-dash` / `.mock-dash-side` /
   `.mock-dash-grid` CSS; rail renders a real miniature (≈57px sidebar +
   4-column key grid, 12 keys at ~149px tall).
3. **Background preview** — `preview-bg-clip` + scaled `preview-bg-viewport`
   mounts the real component inside the rail; scale uses *cover* (max of both
   axes) so no checkerboard strip shows. Verified: Dark Veil canvas mounts and
   renders; clip rect equals stage rect (318×240).
4. **Slider targets** — editor select now offers System volume, Screen
   brightness, VDock brightness, and **App volume (one process)** with a
   `process` field shown only for that target. `app_volume_get` /
   `app_volume_set` run through the DL-058 COM worker; verified end-to-end on
   `steam.exe` (read 100 → set 40 → read 40 → restore). Unknown process names
   return a clean error, not a crash. `slider_app_volume` catalog preset added.
5. **Slider resize** — the seam-merge chip is gone; each slider now gets a
   right-edge chip pair in edit mode. `+` widens into a free next column (or
   merges a compatible slider sibling — `expandSliderButton` delegates to
   `mergeSliderButtons` for that case), `−` frees the last column. Chips hide
   at grid bounds / when blocked. Verified live: shrink 2→1 cols then widen
   back; both ops history/save wrapped so undo and persistence work. The dead
   `button-merge` emit and `handleButtonMerge` were removed.
6. **Mobile fit** — compact mode sizes cells by the smaller of width- and
   height-driven fit and centres the grid. Portrait 412×839: 72×72px buttons,
   grid 563px, zero scroll. Landscape 863×360: header **auto-hides** (it was
   eating 164 of 360px) leaving a reveal pill; grid 248px, 72×72 buttons,
   zero scroll. Rotating back restores the header (tracked via
   `autoHidOnShort` — an explicit user hide stays hidden). Broken avatar
   images no longer leak alt text over the header (`avatars/9.png` 404 was
   rendering "My VDock" mid-header).

Deviations from the frozen plan: both resize chips sit on the slider's right
edge (not shrink-on-left) so the pair stays adjacent; item 6 needed the
header auto-hide + avatar fixes beyond pure cell sizing to actually free the
vertical space.

Verification: `vue-tsc --noEmit` clean, `npm run build` clean, 239/239
frontend tests, 787/787 backend tests.

**Follow-up:** `tiltEffectEnabled` (the 3D button tilt) is now off by
default — `ref(false)`, `SETTINGS_DEFAULTS.tiltEffectEnabled = false`,
normalization `=== true`. User-facing toggle unchanged (Appearance → 3D
tilt effect); existing users keep an explicit `true` if they opted in.

