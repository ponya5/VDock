# DL-098: Screensaver clock toggle + slimmer new-user widget defaults

## Problem

Two asks from the Appearance → Screensaver widgets panel:

1. **New-user default set should be Clock + Weather + News + Markets.**
   The fresh-install default is currently all five optional widgets
   (`weather, news, sports, market, worldclock`) — Sports and World Clock
   crowd the screen for someone who hasn't curated it yet.
2. **The Clock can't be disabled.** The row renders `checked disabled`
   with "Always drawn." copy; the widget isn't part of
   `screensaverWidgets` at all — it mounts unconditionally.

## Design

### Clock becomes toggleable via its own persisted flag

Not by folding `'clock'` into `screensaverWidgets`: every existing user's
saved list already lacks it, so gating on `includes('clock')` would
silently hide the clock for all of them — and "user turned it off" vs
"saved before the flag existed" are indistinguishable in that array.

Instead: new persisted boolean `screensaverClockEnabled` (default `true`,
the `*Enabled` convention shared by `agentAlertsEnabled` /
`pressSoundEnabled`). Existing users load without the key → stays `true`
→ clock keeps showing; turning it off persists cleanly as `false`.

`ScreenSaver.vue` gates the clock block on
`showClockWidget = isMobileViewport || screensaverClockEnabled` — the
mobile curated set keeps the clock like it forces weather + world clock
(DL-063; a phone's whole layout is built around them). `mountedWidgets`
includes `'clock'` only when shown so collision/separation never reserves
space for a hidden clock.

### Defaults for new users

`screensaverWidgets` default becomes `['weather', 'news', 'market']` —
clock on via its flag; Sports and World Clock stay available, just off.
Only new installs see this (persisted lists always win). The "Screensaver
widgets" section reset restores the same set + clock flag.

## Implementation Plan

- [ ] `settings.ts`: `screensaverClockEnabled` ref + SETTINGS_DEFAULTS +
      `PersistedUserSettings` + payload + apply + load fallback + persist
      watcher + export; `screensaverWidgets` default → three ids in all
      three places
- [ ] `user_settings.py` allowlist: `screensaverClockEnabled`
- [ ] `ScreenSaver.vue`: `showClockWidget` + `v-if` + conditional
      `mountedWidgets` entry
- [ ] `SettingsView.vue`: live Clock toggle ("Always drawn" copy dropped),
      mock preview honours the flag, section reset covers it
- [ ] Failing test first: flag wiring across store/backend/component/view

## Implementation Results

**Implemented as designed.**

- `settings.ts` — `screensaverClockEnabled` ref/persist/apply/load-fallback/
  watcher/export, typed on `PersistedUserSettings` with the rationale
  comment; `screensaverWidgets` default is `['weather','news','market']`
  in `SETTINGS_DEFAULTS`, the initial ref, and the load fallback (all
  sharing `SETTINGS_DEFAULTS` so they can't drift).
- `user_settings.py` — `screensaverClockEnabled` allowlisted with a
  comment explaining why it's not in the widgets array.
- `ScreenSaver.vue` — `showClockWidget` (`isMobileViewport ||
  screensaverClockEnabled`) gates the clock block; `mountedWidgets`
  pushes `'clock'` only when shown, so separation/snap never reserve a
  hidden clock's space.
- `SettingsView.vue` — Clock row toggle is live (`:checked`/`@change` on
  the flag), copy "Large time and date." (the "Always drawn." clause is
  gone); mock preview clock + date honour the flag; the section reset
  restores flag + trio together.

**Verified live on :5000 (built dist):**

- Settings → Screen saver: Clock row is a working toggle — flipped it off,
  `screensaverClockEnabled` became `false` and persisted (the dashboard
  tab loaded with the flag still false).
- `show_screensaver` ui_command with flag off → saver rendered weather +
  market + news + worldclock + sports, **no `.ss-time`**; the freed
  centre stays unclaimed (saved positions of the rest are untouched).
- Flag back on → clock returns centre-stage ("13:51 · MONDAY · 28
  SEPTEMBER"). Screenshots: `design-log/refs/saver-clock-off.png`,
  `saver-clock-on.png`.
- Existing-user widget list untouched: this install's saved
  `screensaverWidgets` still carries all five — only fresh installs get
  the slim default.

**Pre-existing issue observed (not this change):** news and sports
sections overlap each other in the lower band at tm=2 with all five
widgets on — identical with the clock enabled, so it's the separation
pass failing to fully resolve two tall fixed-size boxes, not a
regression. Worth its own entry if it matters on the panel.

**Tests:** `screensaver-clock-toggle.test.ts` (4 — flag wiring across
store/backend/component/view, slim defaults, live toggle in the settings
row, conditional `mountedWidgets`). `vue-tsc` clean; vitest **318/318**;
`npm run build` clean, `dist/` rebuilt.
