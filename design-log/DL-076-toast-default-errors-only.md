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
