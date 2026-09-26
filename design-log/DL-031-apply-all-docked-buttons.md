# DL-031 — "Save & Apply to All" misses docked sidebar buttons

## Background
User report: Settings → Appearance → Button design → Save & Apply to All
produces no visible change on the dashboard.

## Problem
`dashboardStore.applyGlobalButtonStyle` iterates
`currentProfile.scenes[].pages[].buttons` only. Buttons docked in the
always-visible sidebar live on `profile.dockedButtons` — a separate array
the loop never touches. Grid buttons DO update (verified live: store
`layers.effect` flips to 'deckkey', DOM classes flip to
`deck-button-deckkey`), but the docked sidebar — which is on screen at all
times — keeps its old design, so the apply looks broken.

## Design
Extend `applyGlobalButtonStyle` to run the same mutation over
`currentProfile.dockedButtons` (same `Button` type, same `layers.effect`
precedence). Extract the per-button mutation into a local helper so the
two collections can't drift.

## Verification
- Live: apply 'deckkey' → docked button class flips gem→deckkey, grid
  unchanged-count matches, saveProfile persists.
- vitest suite + typecheck.

## Implementation Results

### Fixed
- `dashboard.ts applyGlobalButtonStyle` — per-button mutation extracted to
  `applyToButton()` helper; now runs over `currentProfile.dockedButtons`
  as well as every scene/page button. Verified live: docked Weather
  flipped gem→statuskey in store AND DOM (`deck-button-statuskey` on the
  sidebar card), all 54 grid buttons flipped, screenshot shows the LED
  design everywhere.

### Adjacent fixes found during verification
- **Rate limiter vs static assets**: `.env` runs `RATELIMIT_ENABLED=True`
  at 50/hour — the static catch-all wasn't exempt, so one page load
  (63 precache files) exhausted the quota and assets 429'd as text/html,
  leaving the app unmounted. `@limiter.exempt` added to `root` +
  `serve_frontend` — file reads aren't API abuse surface.
- **Build failure on vite-plugin-pwa 0.21**: the 2.8MB bundle exceeds
  workbox's 2MiB `maximumFileSizeToCacheInBytes` → build errored.
  Raised to 4MiB in `vite.config.ts` (Electron-local bundle, safe to
  precache).

### Verified
- 201/201 frontend tests (2 new: docked coverage + shared helper).
- `vue-tsc` clean, `vite build` clean with SW precache (63 entries).
- Live: index/css/sw all 200, apply-all hits docked + grid.

## Follow-up — "Save & Apply" stopped rewriting existing keys

Same user report resurfaced ("change key design, nothing applies no matter
what I select") with a different cause. The savebar redesign (DL-054) split
the Buttons page into two paths:

- Savebar **"Save & Apply"** → `saveAndApplyButtonSettings()` — committed
  the draft only as the *new-key default* (`settingsStore.buttonDefault*`);
  existing keys untouched.
- The actual mass-rewrite hid inside a warning note ("Apply to every
  existing key" → `applyButtonBehaviourToAll`).

So the primary action's label lied: "applied" toast, unchanged dashboard.

**Fix (user chose apply-to-all semantics):**

- Savebar button on the Buttons page now runs `applyButtonBehaviourToAll`
  directly, labelled "Save & Apply to all keys"; the warn-note button is
  removed and the note is a pure warning ("rewrites every existing key —
  including per-key customisation"). `saveAndApplyButtonSettings` deleted.
- `applyButtonBehaviourToAll` awaits `ensureProfileLoaded()` first — a
  standalone Settings window/tab has no `currentProfile`, and
  `applyGlobalButtonStyle` silently returned while the toast claimed
  success. No profile now produces an error toast instead.
- `applyGlobalButtonStyle` returns the `saveProfile()` result; a failed
  PUT surfaces "The profile could not be saved" instead of a false
  "applied" toast.

Tests: `button-behaviour-subtabs.test.ts` updated for the single apply
action. 254 frontend tests + vue-tsc green.

## Follow-up — apply must refresh the current window itself

`applyButtonBehaviourToAll` called `requestVdockRefresh()` to update the
dashboard — but BroadcastChannel (and the `storage` event fallback) by
spec never delivers to the sender's own context. A dashboard running in
the same window/route saw nothing until the next manual refresh, since it
can render a different profile object than the one
`applyGlobalButtonStyle` mutated.

**Fix:** `await refreshVdock()` (re-fetch settings + profiles + setProfile)
runs in the current window after a successful apply, before
`requestVdockRefresh()` notifies other tabs. Same canonical path the
header Refresh button uses; the awaited save means no read-stale race.

Tests: same-file assertion for `await refreshVdock()` in the apply path.
4 subtab tests + vue-tsc green.

## Follow-up — surface the real save error; verified end-to-end

User report: "Failed to apply — the profile could not be saved" toasts.

Diagnosed live: the apply path itself is correct — driving the real app
(vite dev :4444) through Playwright, "Glass" → "Save & Apply to all keys"
PUT 200'd and every button persisted `layers.effect.type: 'glass'`.
The user's failures coincided with backend restarts mid-session — the PUT
died at the proxy, `saveProfile()` returned false, and the toast was
right. (Wrapped `{profile}` PUTs seen in vdock.log were backend tests
writing to the same log file — a red herring; no frontend caller wraps.)

Change: `saveProfile()` now records the real failure in a
`lastProfileSaveError` ref (HTTP status + server error / network detail);
the apply toast shows it instead of a generic "could not be saved".

Tests: 6 apply/subtab tests + vue-tsc green; live verified — every button
in the profile now carries the applied effect and the dashboard refresh
re-fetches it.

## Follow-up — In-context grid control on the Buttons rail

User request: "add the ability to change the grid (in context)" — the
IN CONTEXT preview card was a hardcoded 4×3 mock (`v-for="i in 12"`).

- The mock grid now renders the real current page dims:
  `repeat(previewGridCols, 1fr)` × `cols*rows` keys.
- Cols/rows steppers in the card foot edit `dashboardStore.currentPage
  .grid_config` — the same field the deck footer edits — clamped to
  2–10 cols / 1–6 rows; each step debounce-persists via `saveProfile()`
  (500 ms) then `requestVdockRefresh()` for other windows.
- `watch(appearanceSubTab, { immediate: true })` runs
  `ensureProfileLoaded()` on the Buttons tab so the steppers work even
  in a standalone Settings window; disabled with a hint when no profile
  is loaded.

Verified live via Playwright: Cols+ resized `Media / Page 1` 5×3 → 6×3,
PUT 200, persisted to the profile file. 254 tests + vue-tsc green.
