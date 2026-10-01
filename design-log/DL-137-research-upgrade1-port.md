# DL-137 — Port the remaining `research_upgrade1` features to main

## Problem

`research_upgrade1` carried a bundle of work past main's DL-133. The
spectrum-side pieces (DL-134/135 equivalents: 6 restored skins, crossfade,
RGB bars, ambience, widget overlay) were ported earlier, but a review diff
shows the rest never landed:

1. **Spectrum dynamics expansion** — `audio_spectrum.py`: `BAND_CURVE`
   1.6 power expansion so quiet/mid content sits low and transients read
   as spikes (was linear-in-dB, parked everything at 50–80); decay
   0.78→0.70; emit cap 14→22 Hz so the frontend's per-frame interpolation
   isn't stair-stepped.
2. **Now-playing site detection** — `now_playing.py` `detect_site()`:
   SMTC only reports the app ("chrome.exe"), so for browser sources it
   scans visible window titles ("… - YouTube - Google Chrome") once per
   track change; emits `site` in the payload. `nowPlaying.ts` gains
   `nowPlayingIcon()`/`nowPlayingSourceLabel()`; NowPlayingButtonFace,
   NowPlayingWidget and the SpectrumStage media bar show the brand icon +
   "YouTube"/"Spotify" labels instead of "chrome.exe" + music note.
3. **Mobile header reveal + media-bar merge** (branch DL-134) — the
   reveal FAB is desktop-gated, so the 7" panel has *no path* to the
   header: un-gate on mobile, MobileDeckChrome yields while revealed,
   DeckHeader shows Profiles/Settings on mobile (Edit stays gated —
   mobile-blocked upstream), autohide starts on mount. FAB redesigned
   92×58→120×68 with orbiting rim + sheen. Spectrum media bar merges
   Play/Stop into one `media_play_stop` (DL-128 semantic) and scales
   text up for panel distance.
4. **Mobile landscape spectrum zoom** — radial skins size by min(w,h),
   so a 2:1 panel in landscape renders a small disc; zoom canvas draw
   by `min(1.45, sqrt(w/h))` when mobile+landscape (edges crop,
   intentional).
5. **GuideView rework** (branch DL-132 follow-ups) — fixes a real scroll
   bug (`#app` is overflow:hidden; the guide had no scrollport), adds a
   264 px side nav rail with grouped sections + scroll-spy, sticky chip
   rail ≤980 px, and reorders sections to match the rail groups.
6. **Settings tidy** — the type/activation/try-it rows merge into one
   `ss-general` panel; the About support CTA becomes sticky.
7. **Housekeeping** — numpy pinned range (each 2.x drops a Python), root
   `*.png/*.jpg` + `.devin/`/`.kilo/` ignored, test-script screenshots go
   to `design-log/refs/`.

Explicitly **not** ported: `playerMode` / the Winamp player UI — reverted
on the branch itself (97ac9b8). The branch's DL-135 (spectrum widget
overlay) is already main's DL-135; the spectrum work is DL-134 here.

## Design

Pure ports where the files are untouched since the merge-base:
`audio_spectrum.py`, `now_playing.py`, `nowPlaying.ts`,
`NowPlayingButtonFace.vue`, `NowPlayingWidget.vue`, `DeckHeader.vue`,
`GuideView.vue`, `SpectrumWidget.vue`, `audioSpectrum.ts`, both backend
test files, `requirements.txt`, `.gitignore`, `test-scripts/*`.

Hand-merges where the worktree diverged: `SpectrumStage.vue` (port the
play_stop merge, brand-icon fallback, text scale-up, mobile zoom into the
two-canvas version), `DashboardView.vue` (FAB gate + redesign +
MobileDeckChrome yield around the new screensaverState wiring),
`SettingsView.vue` (ss-general merge keeping the DL-135 overlay toggle),
`ScreenSaver.vue` (comments only — content is already equivalent), and
the affected source-contract tests.

## Implementation Results

All seven items ported; the worktree now differs from `research_upgrade1`
only where main's spectrum work (DL-134 performance pass, DL-135 overlay,
DL-136 weather glyph, `screensaverState`) goes *past* the branch.

**Pure checkouts (13 files, now byte-identical to the branch):**
`audio_spectrum.py` (BAND_CURVE 1.6, decay 0.70, 22 Hz emit),
`now_playing.py` (`detect_site` window-title scan), `nowPlaying.ts`
(`site` field, `nowPlayingIcon`/`nowPlayingSourceLabel`, brand tables),
`NowPlayingButtonFace.vue`, `NowPlayingWidget.vue`, `DeckHeader.vue`
(mobile Profiles/Settings buttons), `GuideView.vue` (side-nav rail +
own scrollport — the clip fix), `SpectrumWidget.vue`,
`audioSpectrum.ts`, `test_audio_spectrum.py`, `test_now_playing.py`,
`requirements.txt`, `.gitignore`, `test-scripts/*`.

**Hand-merges:**
- `SpectrumStage.vue` — 4-button transport → 3 (`media_play_stop`,
  state-split icon/label), `nowPlayingIcon`/`nowPlayingSourceLabel` in
  the kicker ("NOW PLAYING · SPOTIFY"), title/artist/progress scaled up
  for panel distance, mobile-landscape zoom `min(1.45, sqrt(w/h))` kept
  from DL-134. Two-canvas crossfade untouched.
- `DashboardView.vue` — reveal FAB un-gated on mobile and restyled to
  120×68 orbit-rim + sheen; MobileDeckChrome renders only while
  `isMobileViewport && !showHeader` so the real DeckHeader takes over on
  reveal. `screensaverState` background-suspend kept.
- `SettingsView.vue` — `ss-type` + `ss-activation` merged into
  `ss-general` (type, overlay toggle, shuffle interval, idle delay,
  try-it); `deepTabAnchor.settings` retargeted; `.about-support` sticky.
- `ScreenSaver.vue` — no functional diff from the branch; only comment
  phrasing differs, left as-is.
- Tests — `spectrum-stage` asserts the 3-button `media_play_stop`
  dispatch; `screensaver-shuffle`/`dashboard-font` assert `ss-general`;
  `header-timer-pill` asserts the 120×68 FAB.

**Fix applied on top of the branch:** `now-playing-button.test.ts`
expected `Artist · spotify` — the branch's title-cased source label
(`spotify.exe` → `Spotify`) was never reflected there, so the test was
red on the branch itself; updated to `Artist · Spotify`.

**Verified live on the built bundle (:5000):**
- Spectrum saver media bar: 3 buttons (prev / Play / next), brand icon +
  "Spotify" kicker, larger text — `refs/saver-media-bar-merged-transport-2026-10-01T22-53-13-730Z.png`.
- Mobile 393×852: "Header" FAB renders bottom-centre; tap → FAB swaps to
  the real DeckHeader (profiles/settings/timer pill), chrome yields —
  `refs/mobile-fab-reveal-2026-10-01T22-53-59-767Z.png`,
  `refs/mobile-header-revealed-2026-10-01T22-54-20-565Z.png`.
- `/guide`: `.guide-nav` rail lists 12 sections; `.guide-content` is its
  own scrollport (7399 px in an 852 px viewport) — the below-fold clip is
  gone — `refs/guide-side-nav-2026-10-01T22-54-43-164Z.png`.

**Suites:** `vue-tsc` clean; 555/555 vitest; 49/49 backend pytest
(audio_spectrum + now_playing); `npm run build` clean — `dist` rebuilt.

Backend on :5000 was restarted — the old process predated the checked-out
`now_playing.py`/`audio_spectrum.py` (no `site` field in the payload).
