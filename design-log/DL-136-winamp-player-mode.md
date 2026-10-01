# DL-136 — Winamp player mode

**Status:** Complete

## Request

Replace the VDock dashboard with a Winamp-classic player UI (reference
imgs 6–8: the 2.x main window + playlist, the Linamp hardware unit, and
a mobile portrait layout). The panel should *be* the player — titlebar,
green LCD, spectrum analyzer, transport row — with working mobile
portrait and landscape layouts.

## Design

### Mode switch

New persisted setting `playerMode: 'deck' | 'winamp'` (default `'deck'`)
— server-synced like every other setting, so the panel and desktop stay
in lockstep. `DashboardView` renders `WinampPlayer` instead of the deck
chrome (header/chrome/grid/footer/FAB) when set; the screensaver,
modals, and rotate gate stay shared overlays. The Winamp titlebar close
button returns to deck mode. Settings gets an "Interface" panel on the
Appearance → Buttons tab with a Deck/Winamp selector.

### `components/WinampPlayer.vue`

Faithful Winamp 2.x main window, tuned for the touch panel:

- **Titlebar** — "WINAMP" wordmark + shade/close glyphs; close returns
  to deck mode.
- **Display block** — black LCD panel: green LCD elapsed-time digits
  (`position_s` anchored + local tick, same pattern as the spectrum
  media bar), a mini spectrum analyzer canvas (segmented green→yellow→
  red bars + peak caps, fed by `useAudioSpectrum`, EQ-masked), and the
  scrolling `N. Artist – Title (m:ss)` marquee. kbps/kHz slots show the
  track's source label and the pipeline's real 48 kHz capture rate —
  SMTC reports no bitrate, so we display what we know rather than
  invent a number. mono/stereo LEDs.
- **Slider row** — volume (functional: `volume_get` on mount, throttled
  `volume_set` on drag, `system_volume` socket sync like
  SliderButtonFace) + balance (decorative, springs to center — no
  backend balance action exists).
- **Transport row** — prev / play / pause / stop / next / eject mapped
  to `cross_platform` `media_*` actions; play/pause face mirrors live
  SMTC state. SHUFFLE/REPEAT render as local LED toggles (SMTC cannot
  report or set them — they visibly toggle, dispatch nothing).
- **EQ / PL buttons** — classic window toggles for the equalizer and
  playlist panels.

### Equalizer window

Preamp + 10 band sliders, ON toggle. The EQ is real in the only sense
this UI can offer: it masks the **displayed** analyzer spectrum —
20 display bands fold onto the 10 sliders, each slider a ±12 dB gain
applied before rendering. Honest functionality, zero audio claims.

### Playlist window

SMTC exposes no queue, so the playlist is a **session recent-tracks
list**: `nowPlaying.ts` accumulates played tracks (deduped by
title+artist, capped ~30), numbered green rows, current track
highlighted with the classic `***` marker and elapsed/total time.

### Layouts

- **Desktop / landscape:** centered player column (main window), the
  playlist beside it when width allows (≥~820 px), EQ window toggled in
  the same column.
- **Mobile portrait:** portrait allowed (`RotateToLandscape` exemption
  added for winamp mode) — main window on top, playlist fills the rest,
  EQ as a toggleable section; matches reference img 8.
- **Mobile landscape:** main + playlist side-by-side; EQ below main.

## Implementation Results

**Status: Complete.**

- `playerMode: 'deck' | 'winamp'` persisted setting (default `deck`),
  allowlisted server-side in `user_settings.py` so it survives the
  payload filter; the Settings panel got an "Interface" selector on
  Appearance → Buttons.
- `WinampPlayer.vue` (~740 lines): titlebar with EQ/PL/close, LCD
  time + marquee + segmented analyzer canvas (EQ-masked), volume
  slider wired to real `volume_get`/`volume_set`/`system_volume`,
  balance cosmetic, transport row dispatching `media_*` actions,
  SHUFFLE/REPEAT local LEDs, 10-band EQ window masking the displayed
  analyzer only, playlist fed by a new session recent-tracks list in
  `nowPlaying.ts` (deduped, cap 30).
- `DashboardView` swaps the entire deck chrome for `WinampPlayer`
  when the mode is set; close button exits back to deck.
  `RotateToLandscape` exempts winamp mode so portrait works.
- Layouts verified by headless CDP screenshots on the built bundle:
  - **Desktop 1024×600** — main window + playlist side-by-side, real
    SMTC track data in LCD + playlist.
  - **Portrait 390×844** — stacked main-over-playlist, no rotate gate.
  - **Landscape 844×390** — full-width main window, playlist below.
- Verification note: settings sync races a connected second client —
  the live panel rebroadcasts its own `deck` setting over the test
  value mid-run, so visual verification drove the socket relay
  (`user_settings_changed`) after load rather than racing REST.
- Fixes during verification: `ResizeObserver` guarded for jsdom;
  `nowPlayingSourceLabel` regained the app-name capitalization the
  old widget had (`spotify.exe` → `Spotify`); all `font-size` values
  converted to `clamp()` per Property 8.

**Tests:** `winamp-mode.test.ts` 9/9; full frontend suite 552/552
(after the two fixes above); backend `test_user_settings_payload_keys`
green. `npm run build` clean → `frontend/dist` rebuilt and served.

## Follow-up — mode thumbnails + stale-peer revert guard

**Request.** Show small thumbnails of the dashboard vs the player in
the picker ("so the user can understand how it looks"), and fix: the
switch to Winamp "didn't take any effect".

**Thumbnails.** The `Player mode` segmented control is now two
`.mode-card` picks, each with a real screenshot (`/guide/guide-deck.png`,
new `/guide/guide-player-winamp.png` captured headless on the built
bundle), 16:10 crop, accent border + shadow on the selected card, and a
live note under the picker — "The main screen is now the player — open
it" — so the destination of the switch is unambiguous.

**The revert.** `playerMode` is synced last-writer-wins; a peer window
holding an older blob rebroadcasts it whenever *its* unrelated settings
save fires (migration markers, touch-mode detection…), and
`applySettingsFromRemote` obediently flips the just-picked mode back.
Reproduced headless: click Winamp → localStorage `winamp` → reload →
deck rendered because a remote `deck` payload arrived during load.

Fix: `playerModeLocalAt` timestamps user-initiated picks only
(`settingsSettled` so the boot-time applies don't stamp;
`isApplyingRemoteSettings` still true at watcher flush so remote
applies don't stamp). `applySettingsFromRemote` strips `playerMode`
from remote payloads for 15 s after a local pick — the local PUT is
already on the wire, so last-writer is the user's click, not a stale
peer echo. Outside the window remote picks apply normally.

Verified: cards render + images load + selected state + note in a
headless settings screenshot; 37/37 targeted tests green; `npm run
build` clean → dist rebuilt.

## Follow-up 2 — solo player, collapsible EQ, lightbox thumbs, no saver

**Request.** (1) Clickable full-size mode thumbnails; (2) drop the
playlist window — player only; (3) match the classic 2.x reference shot
more closely and give the EQ a collapse toggle; (4) keep the analyzer
live; (5) screensaver must never fire in Winamp mode.

- **Settings thumbnails** — each `.mode-card` now has a `.mode-zoom`
  corner button (magnifier, fades in on hover/focus, always visible on
  touch) that opens a `.mode-lightbox` fixed overlay showing the full
  screenshot; click anywhere closes. The Winamp thumb was recaptured
  with the new solo-player look.
- **Playlist removed** — the `winamp-playlist` window, `playlistOpen`,
  `playlistRows`, the `.pl-open` grid rules and the PL titlebar button
  are gone. Session-recent history still feeds only the marquee's "N."
  track counter. Frame is a single column everywhere.
- **Classic fidelity** — EQ collapses/expands via the titlebar `EQ`
  button (lit while open) into a docked second window under the main
  one, like the reference. Its header gets an ON/PRESETS switch row —
  ON masks/unmasks the analyzer, PRESETS resets all bands to flat —
  and the sliders got the gold/yellow thumbs of the classic skin.
- **Analyzer** — unchanged path (WASAPI → `useAudioSpectrum` → canvas);
  re-verified live in the rebuilt bundle — real Spotify bands render.
- **Screensaver disabled in Winamp mode** — `ScreenSaver` mounts only
  when `!winampMode`, `resetIdleTimer()` early-returns so no new idle
  countdown starts, entering Winamp mode dismisses a visible saver, and
  the `show_screensaver`/`screensaver_layout_edit` ui_commands are
  ignored while the mode is active. Settings → Screensaver "Test" is a
  deck-side preview; users still see the deck saver's settings normally
  when back in deck mode.

Tests: `winamp-mode.test.ts` repinned (EQ toggle contract, marquee
numbers instead of playlist rows) — 18/18 with the guide suite green;
`npm run build` clean → dist rebuilt; headless CDP shot confirms the
two-window classic look with a live analyzer.
