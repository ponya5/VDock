# DL-142 — Per-type screensaver widget layouts

## Problem

User report: "each screensaver type should have a saved layout of widgets.
I changed the layout for spectrum and it affected the widget dashboard
layout."

`settings.screensaverLayout` is a single global map of widget positions.
The Widget dashboard saver and the Spectrum saver (when "Widgets on the
visualizer" is on, DL-135) both read it, and the layout editor always
writes it — so repositioning widgets over the spectrum rewrote the
dashboard arrangement too.

## Design

Layouts are keyed by the *visual type* being shown:

- `widgets` → existing `screensaverLayout` (unchanged key, so every saved
  layout and the allowlisted server key keep working — no migration).
- `spectrum` → new `screensaverSpectrumLayout: ScreensaverLayout | null`.
  `null` means "never customised": the spectrum overlay falls back to the
  widget layout (the exact behaviour today), and the first Save in the
  editor while spectrum is the backdrop creates the independent copy.
- `stats` has no positionable widgets (it owns the whole surface), so it
  has no layout. Editing while the type is stats edits the widgets layout,
  as the editor already renders the widget canvas in that case.
- `shuffle` resolves per displayed type (`effectiveStyle`), so each shuffled
  view uses its own layout.

`ScreenSaver.vue` derives `layoutTarget` (`spectrum` when the spectrum
backdrop is active, else `widgets`) and uses it for both reading the
persisted layout and — via `save-layout` now emitting `(layout, target)` —
writing it. Dashboard and Settings handlers call a store action
`setScreensaverLayout(target, layout)`. The editor toolbar shows which
layout is being edited.

`screensaverSpectrumLayout` joins the persisted payload, remote apply
(normalised, `null` allowed), the backend allowlist and the store return.

## Implementation Results

**Done:**

- `stores/settings.ts` — new `screensaverSpectrumLayout` ref (`null` by
  default), included in the persisted payload (deep-copied, `null` kept),
  the remote apply (object → `normalizeScreensaverLayout`, anything else →
  `null`), the load defaults, the persist watch list and the store return.
  New `setScreensaverLayout(target, layout)` action.
- `backend/routes/user_settings.py` — `screensaverSpectrumLayout` added to
  the allowlist.
- `ScreenSaver.vue` — `layoutTarget` (`spectrum` when the spectrum backdrop
  is active, else `widgets`) drives `persistedLayout` (spectrum falls back
  to the widget layout while unset) for rendering and as the editor's
  starting copy; `save-layout` now emits `(layout, target)`. The toolbar
  hint names the layout being edited, and under the Shuffle type an
  "Edit Spectrum / Edit Widgets" button picks which one (the shuffle timer
  is off in edit mode); switching reloads the edit copy.
- `DashboardView.vue` / `SettingsView.vue` — save handlers call
  `setScreensaverLayout(target, layout)`.
- Tests: `screensaver-layout.test.ts` wiring assertions updated; new
  `screensaver-per-type-layout.test.ts` (8 tests: independence both ways,
  local payload, server apply, null/garbage → null, wiring, allowlist).

**Notes:**

- Existing users see no change on upgrade: the spectrum overlay keeps
  using the widget layout until a spectrum layout is first saved.
- Layout edits made over the spectrum *before* this change already
  overwrote the widget layout; those can't be recovered automatically —
  use Reset in the Widget dashboard editor if needed.
- The running backend must be restarted to pick up the new allowlisted
  key, otherwise the spectrum layout persists locally but is dropped by
  the server on save.

Suites: 578/578 vitest, backend payload-key tests pass, `vue-tsc` clean,
`npm run build` clean — `dist` rebuilt for the panel.
