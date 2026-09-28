# DL-101: Screensaver — migrate untouched legacy defaults to the DL-098 set

## Problem

DL-098 changed the fresh-install screensaver default to Clock + Weather +
News + Markets, but "persisted lists always win": any settings file written
before that change stores the old all-five `screensaverWidgets`
(`weather, news, sports, market, worldclock`), so upgraded installs that
never customized the saver keep the crowded pre-change view forever — the
new default the user asked for never appears.

## Design

One-time migration inside `applySettingsFromRemote` (the single funnel for
server-persisted settings — broadcast/socket echoes are idempotent because
the gate below can't be re-satisfied once applied):

Apply the new defaults only when the stored settings are *provably untouched*
legacy values — all three:

1. `screensaverClockEnabled` is **absent** — the flag was introduced by
   DL-098, so any file written by a current build contains it. This is the
   one-shot gate: after any new-version save the flag exists and the
   migration can never fire again (no extra marker key needed — a user who
   later re-selects all five widgets deliberately keeps them, because their
   file carries the flag).
2. `screensaverWidgets` set-equals the legacy five (order-insensitive).
3. `screensaverLayout` is absent or deep-equals `DEFAULT_SCREENSAVER_LAYOUT`
   — a user who dragged widgets keeps their arrangement.

When all three hold, substitute before `applySettingsObject`:
`screensaverWidgets = SETTINGS_DEFAULTS.screensaverWidgets`,
`screensaverClockEnabled = true`, `screensaverLayout` untouched (it's already
default). The result persists through the normal save path.

## Implementation Plan

- [ ] `settings.ts`: legacy-signature check + substitution at the top of
      `applySettingsFromRemote`
- [ ] New test covering: untouched legacy → migrated; flag present → never
      migrated (even with all-five list); customized layout → untouched

## Implementation Results

Landed as designed:

- `settings.ts` — `LEGACY_SCREENSAVER_WIDGETS` (the verbatim pre-DL-098
  five-widget list) + `isUntouchedLegacyScreensaver()` (flag-absent check
  happens in the caller; here: set-equal widget list + layout absent or
  `normalizeScreensaverLayout`-equal to factory). At the top of
  `applySettingsFromRemote`, when `screensaverClockEnabled === undefined`
  and the untouched check passes, the payload is rewritten to the DL-098
  default (`['weather','news','market']` + `screensaverClockEnabled:
  true`) before `remoteSettingsDiffer` runs — so a local state that
  already mirrors the legacy remote still migrates.
- This machine's `user_settings.json` is the motivating case: exact
  legacy list + factory layout + no flag → migrates to Clock + Weather +
  News + Markets on next load, then `saveSettings` writes the flag so the
  swap can never re-fire.
- `screensaver-legacy-migration.test.ts` (3): untouched legacy → slim
  default (flag lands `true`); flag present → legacy list survives
  untouched even with `screensaverClockEnabled: false`; dragged layout →
  fails the untouched check, list preserved.
- `screensaver-clock-toggle.test.ts` — the "sports/worldclock off the
  defaults" source check rescoped to the `SETTINGS_DEFAULTS` block so the
  migration signature constant doesn't false-positive it.

**Tests:** vitest **325/325**, `vue-tsc` clean, `npm run build` clean.
