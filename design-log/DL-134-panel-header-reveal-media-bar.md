# DL-134 — Header reveal on mobile viewports + spectrum media-bar polish

## Problem

Post-`research_upgrade1` review on the touch panel surfaced five issues:

1. **No "show header" affordance on the panel.** The DL-102/104/130 reveal
   FAB (`header-reveal-fab`) is gated `v-if="!isMobileViewport && ..."` and
   `DeckHeader` never mounts on mobile viewports (`MobileDeckChrome`
   replaces it outright). A 7" touch panel (min dim ≤700 + coarse pointer)
   is exactly `isMobileViewport`, so the reveal button can never render and
   `showHeader` is meaningless there — the panel has no path to the header.
2. **Two transport buttons where one suffices.** The spectrum media bar
   carries Play/Pause *and* Stop side by side — the same dead-cell problem
   DL-128 already solved for deck buttons.
3. **Spectrum flat despite Spotify playing.** Root cause found on the live
   machine: the running backend predates the merge — `services/
   now_playing.py`/`audio_spectrum.py` landed on disk ~14:02 but the backend
   process started 12:59, so `/api/now-playing` 404s and no
   `audio_spectrum` frames exist. Restart required. (DL-133's documented
   caveat still applies after restart: Spotify Connect remote playback /
   hardware offload renders silence on every local endpoint — no loopback
   can see that stream.)
4. **"Nothing playing" while Spotify runs.** Same stale-backend cause —
   the SMTC monitor only exists in the merged code.
5. **Media-bar text too small.** The compact pill's title caps at 15 px and
   the has-track card's at 24 px — both under-read at panel distance.

## Design

### Header reveal on mobile viewports

- FAB gate drops `!isMobileViewport` → renders on any viewport while
  `!showHeader && !isEditMode`.
- `MobileDeckChrome` yields while the header is revealed on mobile:
  `v-if="isMobileViewport && !settingsStore.showHeader"`, `DeckHeader
  v-else`. Reveal mounts the real header; its existing auto-hide countdown
  (DL-130) collapses it back to the mobile chrome after 5 s unless pinned,
  and swipe-up/collapse still works — so the panel never gets *stuck* on
  the taller header.
- DeckHeader internal `!isMobileViewport` gates: **Profiles** and
  **Settings** buttons un-gated (a header on mobile can now only appear via
  deliberate reveal, so the DL-061 "no config affordances" surface-purity
  rule doesn't apply to it — and settings access is the point of summoning
  it on a panel). **Edit** stays gated: `toggleEditMode` is blocked on
  mobile upstream (`dashboard.ts`), so the button would be dead.

### Spectrum media bar

- Prev / **Play·Stop** / Next — the centre button sends
  `media_play_stop` (DL-128: backend splits playing→`media_stop`,
  else→`media_play_pause`) and swaps its icon `stop`/`play` + aria-label on
  the live `playing` feed. The standalone Stop button is removed — same
  merge the deck grid got, applied to the saver bar.
- Text scale-up: compact pill title 15→20 px cap, artist 12→15, kicker
  13→14; has-track title 24→32 px cap, artist 16→20; compact art tile
  46→56 px. Has-track card stays ≤ ~30 % of screen height (DL-133's
  visualizer-dominant budget).

## Trade-offs

- Phones gain the FAB too — `isMobileViewport` can't distinguish a wall
  panel from a phone. Acceptable: the header auto-collapses back to the
  mobile chrome, so a stray tap costs 5 s of header, not a stuck layout.
- `media_play_stop` stops rather than pauses while playing (position lost).
  Matches both the user's wording and DL-128's established semantic; the
  separate `media_play_pause` action remains for pause behaviour.

## Implementation Results

**Status: Implemented + live-verified.**

- **Stale backend was the root cause of #3/#4.** The running backend
  (started 12:59) predated the merge that landed `services/now_playing.py`
  + `services/audio_spectrum.py` (~14:02); `/api/now-playing` 404'd and no
  `audio_spectrum` frames existed. Restarted `app.py` in the venv — no code
  change needed. After restart, verified live: SMTC reads Spotify
  ("Reborn" — Tinlicker, then "Rain On Me" — DJ IP, `playing: true`,
  position advancing, art cached + served); spectrum capture opened the
  default loopback then endpoint-followed to `Speakers (usb audio)` where
  the mix actually renders. DL-133's Connect caveat still stands if
  Spotify ever renders off-device.
- **`SpectrumStage.vue`**: dropped the standalone Stop button; the centre
  transport is now one `media_play_stop` button — `fas:stop` + "Stop"
  while playing, `fas:play` + "Play" otherwise (same split the deck grid
  got in DL-128). Text scaled up: pill title 15→20 px, artist 12→15,
  kicker 13→14, art tile 46→56 px; has-track title 24→32 px, artist 16→20.
- **`DashboardView.vue`**: FAB gate is now `!showHeader && !isEditMode`
  (mobile gate dropped); `MobileDeckChrome` mounts only while
  `isMobileViewport && !showHeader` so a mobile reveal swaps in
  `DeckHeader`, and collapse/auto-hide hands the slot back.
- **`DeckHeader.vue`**: Profiles + Settings buttons un-gated on mobile
  (the header can only appear there via deliberate reveal); Edit stays
  gated — `toggleEditMode` is mobile-blocked upstream, dead button
  otherwise. Added `startAutohide()` to `onMounted` when `showHeader` is
  already true — the watcher misses mount-time transitions, so a mobile
  reveal (or desktop remount with the header open) would otherwise stick
  open with no countdown.
- Updated `spectrum-stage.test.ts`: 4→3 buttons, centre asserts
  `media_play_stop`.
- **Verified**: vitest 39/39 green across spectrum-stage,
  header-reveal-dock, header-timer-pill, edit-mode-touch-drag;
  `npm run build` (vue-tsc + vite) clean; `frontend/dist` rebuilt — the
  panel serves the new bundle (dist was missing entirely before).

Deviation: none beyond the planned scope — the mount-time autohide arm
was the only non-obvious addition, needed because the `showHeader` watcher
can't see the reveal that causes a mobile DeckHeader mount.

## Same-session follow-up: screensaver settings panels merged

User ask on the Appearance → Screen saver tab: fold the "Screensaver type"
and "Activation" panels into one and give it a generic name. Done —
single **General** panel (`#ss-general`) now holds Screensaver Type,
Rotate-every, Idle delay and Try it (Test + Customise layout); the
`ss-type`/`ss-activation` panels and the `settings → ss-activation`
deep-link anchor were retired (`settings` now anchors `ss-general`).
Logged against DL-133 too, since it owns this layout. Tests updated +
green; `dist` rebuilt.

## Follow-up — visualizer motion pass + FAB slick redesign

Same session, second round of feedback: "elements are very simple and
not impressive… more animated motion… eye-catching", and the reveal
button should be bigger + slicker + animated.

- **Spectrum**: constant-motion layer added to all seven skins —
  shared beat-pulse tracker (`createPulse`) + rising-spark pool
  (`drawSparks`); bars get floor glow, a sweeping light beam and
  gravity peak caps; iso gets radiating ripples + under-glow; scope
  spins up with level + core orb + comet trails; aurora gets
  counter-rotating comet arcs + breathing rings; ember gets crest
  hot-spots + floating embers. Detail → DL-123 follow-up.
- **FAB**: 120×68, orbiting conic rim, band sheen, dipping caret,
  periodic glass sheen sweep. Detail → DL-130 follow-up.
- Verified: 39/39 tests (incl. new 90-frame-per-skin smoke test),
  `npm run build` clean, `dist` rebuilt for the panel.
