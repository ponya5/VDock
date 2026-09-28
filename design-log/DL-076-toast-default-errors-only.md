# DL-076: Default toast notification level to "errors only"

## Background

Toast notifications already had a user-facing `toastLevel` setting
(`'all' | 'errors-only' | 'off'`, in `frontend/src/stores/settings.ts`,
surfaced in `SettingsView.vue`) and the `useNotificationsStore.toasts`
computed already filtered on it correctly. The only gap: new installs
shipped with `toastLevel: 'all'`, so every success/info toast (button
press confirmations, save confirmations, etc.) appeared by default —
noisy for a control-surface app where the useful signal is "something
failed," not "something succeeded as expected."

## Design

Change the default to `'errors-only'` so a fresh install only shows
toasts for `type: 'error'` notifications, matching what most users
were expected to want to actually be interrupted for. Users who prefer
the previous behavior can still switch it back from **Settings →
Notifications**.

Two places carry the default and both must agree:
- `SETTINGS_DEFAULTS.toastLevel` in `frontend/src/stores/settings.ts`
  (used for the "reset to default" button in `SettingsView.vue` and by
  any code that maps over `SETTINGS_DEFAULTS`).
- `const toastLevel = ref<...>('errors-only')` — the actual reactive
  state's initial value, used until `loadSettings()`/server sync
  overwrite it.

Existing users with previously saved settings are unaffected: `loadSettings()`
only touches `toastLevel` when the stored blob is missing the key
entirely, and even then it consults the older `showRegularToasts`
boolean before falling back — this change only affects brand-new
installs with no persisted settings yet.

## Implementation Results

Changed both default declarations in `frontend/src/stores/settings.ts`
from `'all'` to `'errors-only'`. No other files needed changes — the
notifications store's `toasts` computed and the Settings UI already
branched on `toastLevel` correctly.

### Verification

- Frontend: 59 files / 254 tests green; `vue-tsc --noEmit` clean.
- Not yet observed live in the running app from this session.

## Follow-up — migrate existing installs (2026-09-28)

### Background

The original entry deliberately left persisted settings alone — but that is
exactly where the remaining noise lives. Every blob written between the
`toastLevel` key's introduction (Aug) and this default change (Sep 27) has
`toastLevel: 'all'` baked in — the whole payload is rewritten on every save,
so 'all' persisted whether the user ever opened the Notifications section or
not. `loadSettings()` applies it verbatim, and even a blob *missing* the key
falls back to `'all'` via the `showRegularToasts` consult. Symptom reported:
a toast on every volume-up press (`cross_platform` success →
`notificationsStore.success('Action Executed', …)` — suppressed only under
`'errors-only'`).

### Design

One-shot migration, same pattern as DL-101's screensaver widget upgrade —
a persisted marker distinguishes "inherited 'all'" from "deliberate 'all'":

- New key `toastLevelMigrated: boolean` on `PersistedUserSettings`, emitted
  by `buildSettingsPayload()` and allowlisted in
  `backend/routes/user_settings.py` so it survives the server round-trip and
  travels with socket/BroadcastChannel settings sync.
- In `applySettingsObject` — the funnel every settings source passes through
  (localStorage load, server GET, socket `user_settings_updated`,
  BroadcastChannel, storage event):
  - Incoming `toastLevelMigrated === true` → set the local marker
    (monotonic; never un-set — a `false` in a peer's payload is just "not
    migrated yet," not a revocation).
  - Incoming `toastLevel === 'all'` *without* the marker → the 'all' is
    inherited, not chosen: apply `'errors-only'` and set the marker. The
    next save persists both, healing the blob — and since the marker rides
    every settings broadcast, one migrated client immunises the whole
    fleet: a stale peer's unmarked 'all' payload gets flipped wherever it
    lands instead of re-poisoning synced devices.
  - Incoming `'all'` *with* the marker → a deliberate post-migration pick;
    respect it (the marker is what keeps Settings → "All" stickable).
- `loadSettings()` missing-key fallback: `?? SETTINGS_DEFAULTS.toastLevel`
  — a blob lacking the key provably predates the radio, so the current
  factory default applies rather than the historical `'all'`. (The
  `showRegularToasts` consult collapses into this: an unmarked 'all' it
  would have produced is caught by the migration anyway.)

### Trade-offs

A deliberately-chosen `'all'` in a blob that somehow lacks the marker gets
flipped once — indistinguishable from inherited, and correctable with one
radio click. Accepted: the radio defaulted to 'all' on open, so a real
deliberate pick was nearly impossible to distinguish from never-touched.

### Verification

- Frontend tests: migration cases in `tests/toast-level-migration.test.ts`;
  full suite + `vue-tsc --noEmit`.
- `frontend/dist` rebuilt — the touch panel loads the built bundle.

### Implementation Results (follow-up)

Implemented as designed:

- `frontend/src/stores/settings.ts` — `PersistedUserSettings.toastLevelMigrated`
  added; `toastLevelMigrated` ref (write-once true); emitted by
  `buildSettingsPayload()`; watched so a migration flips persist (and
  rebroadcast the healed payload). `applySettingsObject` applies the marker
  monotonically, then migrates an incoming unmarked `'all'` to
  `'errors-only'`; marked `'all'` and `'off'`/`'errors-only'` pass through.
  `loadSettings()` missing-key fallback is now `SETTINGS_DEFAULTS.toastLevel`
  (the `showRegularToasts` consult collapsed — an unmarked 'all' it could
  produce is caught by the same migration).
- `backend/routes/user_settings.py` — `'toastLevelMigrated'` allowlisted so
  the marker round-trips the server file and reaches every synced device.
- Tests: `frontend/src/tests/toast-level-migration.test.ts` (6 cases —
  localStorage + server sources, marker respected, missing key, 'off'
  passthrough, localStorage persistence) and
  `backend/tests/test_user_settings_toast_level.py` (marker round-trips the
  allowlist).

Verified: 70 files / 364 frontend tests green, `vue-tsc` clean; backend
user-settings tests green; `npm run build` succeeded — dist carries the fix
for the touch panel.

Deviations: none — the persistence trigger used the existing settings watch
list (marker entry) instead of an explicit save inside `applySettingsObject`;
same effect, no new save path.
