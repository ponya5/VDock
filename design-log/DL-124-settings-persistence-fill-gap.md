# DL-124 — Settings persistence allowlist + white under-fill fix

## Context

Follow-up bugfix for the DL-116..123 feature set. Two defects surfaced while
verifying the new Settings configurability:

1. **Server-side settings sync silently dropped the new keys.**
   `routes/user_settings.py` sanitizes every `PUT /api/user-settings` payload
   through `ALLOWED_USER_SETTING_KEYS`, and none of the DL-119..123 keys were
   in it — `screensaverStyle`, `spectrumSkin`, `spectrumShuffle`,
   `spectrumShuffleMinutes`, `spectrumMediaBar`, `agentWaitingGlowEnabled`,
   `agentWaitingGlowStyle`, `agentWaitingDockEnabled`, `mcpEnabled`, and
   `dashboardFont` all vanished on save, so a reload/second device fell back
   to defaults.

2. **White region below the Settings screen** (user-reported). Root cause
   chain confirmed live in the built bundle:
   - `main.css` sets `body { background: var(--color-background) }`, but
     `--color-background` is defined on `#app.theme-dark` — a *descendant* of
     `body`, so the var is undefined there. An invalid `var()` reference at
     computed-value time resets the property to its *initial* value
     (transparent) — it does not fall back to App.vue's earlier
     `background: #0a0a0a` declaration, which loses the cascade anyway.
     Computed `body` background in the production bundle: `rgba(0,0,0,0)`.
   - `.settings-app { height: 100vh }` sits inside
     `#app { height: 100vh; height: 100dvh; overflow: hidden }`. Anywhere the
     two viewport units disagree (kiosk webviews, dynamic toolbars,
     `interactive-widget=resizes-content`, stale dvh) `#app` can resolve
     shorter than `100vh`, leaving the transparent canvas exposed below the
     app — rendered white.

## Design

- Keep the theme token definition where it is (`.theme-dark` on `#app` is the
  deliberate themed boundary for teleports); instead give `body` a concrete
  fallback so it can never compute transparent:
  `background: var(--color-background, #0f1726)`.
- `.settings-app` tracks `#app`'s *resolved* height (`height: 100%`) instead
  of independently re-resolving `vh` — the child can never under-fill its
  container regardless of which viewport unit a browser miscalculates.
  `min-height: 100vh/100dvh` stays as a guard if the `%` chain ever breaks.
- Add every missing frontend payload key to `ALLOWED_USER_SETTING_KEYS` and
  pin the whole payload key set with a regression test so future settings
  can't silently rot again.

## Implementation Results

- `routes/user_settings.py`: added the 10 dropped keys
  (`screensaverStyle`, `spectrumSkin`, `spectrumShuffle`,
  `spectrumShuffleMinutes`, `spectrumMediaBar`, `dashboardFont`,
  `agentWaitingGlowEnabled`, `agentWaitingGlowStyle`,
  `agentWaitingDockEnabled`, `mcpEnabled`) to
  `ALLOWED_USER_SETTING_KEYS`. Diffed against `buildSettingsPayload()` in
  `stores/settings.ts` — every payload key now round-trips; `marketCoins`
  remains allowlisted as a legacy read.
- `tests/test_user_settings_payload_keys.py` (new): PUTs the full
  57-key `PersistedUserSettings` mirror and asserts every key survives
  PUT *and* GET — future un-allowlisted settings fail loudly.
- `main.css` `body`: replaced `background: var(--color-background)` +
  `background-image: var(--app-backdrop)` with literal
  `background: #0f1726` (the dark theme's own `--color-background` value).
  The vars only resolve on `.theme-dark`/`#app` — on `body` the backdrop
  var was invalid at computed-value time and reset the image layer to
  `none`, leaving the canvas transparent. Verified live in the built
  bundle: computed `body` background went from `rgba(0,0,0,0)` to
  `rgb(15,23,38)`.
- `SettingsView.vue` `.settings-app`: `height: 100%` (tracks `#app`'s
  resolved `100dvh` instead of re-resolving `100vh`) with
  `min-height: 100vh/100dvh` guards — the view can never paint shorter
  than its container regardless of vh/dvh disagreement.
- Verified: 89 backend tests (user-settings + mcp + triggers), 446
  frontend tests, `vue-tsc` + `npm run build` clean, `dist` rebuilt.
- User note: browsers with the app already open may need a hard refresh
  once — the PWA service worker can serve a stale shell.

## Follow-up — persistence watcher missed the DL-123 spectrum keys

**Found while live-verifying the now-playing card:** changing the
screensaver style in Settings never reached `localStorage` — the store's
`saveSettings` `watch()` list (the only trigger that persists drafts)
omitted all five spectrum keys: `screensaverStyle`, `spectrumSkin`,
`spectrumShuffle`, `spectrumShuffleMinutes`, `spectrumMediaBar`. Every
payload/apply seam was correct (DL-124), but nothing *fired* the save —
a reload silently reverted to the widget dashboard.

**Fix:** the five refs added to the watch list. Audited the full set —
`buildSettingsPayload()` emits 56 keys, the watcher now covers all 56
(zero missing).

**Regression test:** `spectrum-stage.test.ts` → mutating
`screensaverStyle`/`spectrumSkin` on the store asserts the saved
`vdock_settings` blob reflects them — exercises the watcher, not just
the payload builders.

