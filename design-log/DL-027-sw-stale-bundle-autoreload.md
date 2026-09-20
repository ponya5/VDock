# DL-027 — Service-Worker Stale Bundle: Auto-Reload on Update

## Background
The production app is a PWA (`vite-plugin-pwa`, `registerType: 'autoUpdate'`).
`sw.js` precaches `index.html` plus all hashed assets and installs a
`NavigationRoute` that answers every navigation with the **precached**
`index.html`. The Electron shell loads `http://localhost:5000` (Flask serves
`frontend/dist`), so the service worker fully controls which bundle the
panel actually runs.

## Problem
User report: "still when I click delete button, it doesn't trigger anything"
— after the ConfirmDialog fix (9099c11) was merged and dist rebuilt.

Investigation:
- Dev (vite, no SW): badge click → `confirmDialog` → overlay renders →
  resolves correctly. Code path is healthy.
- `dist/` contains the fixed bundle (`Teleport to:"body"` verified in
  `index-CCZAFNbf.js`) and Flask serves it.
- But the old service worker keeps serving the **previous** precached
  bundle — the one whose `ConfirmDialog` teleported into its own ancestor
  and crashed mid-patch, hanging the `await confirmDialog(...)` forever:
  exactly "click delete, nothing happens".

Mechanics of the staleness: on launch, the old SW serves old index.html →
browser fetches sw.js → new SW installs → `skipWaiting` + `clientsClaim`
activate it → but the page already loaded old assets. Only the **next**
navigation serves the new bundle. Every deploy silently requires two
restarts, and nothing tells the user that.

## Design
Standard controllerchange auto-reload in `main.ts`:

```ts
navigator.serviceWorker.addEventListener('controllerchange', () => {
  if (reloading) return
  reloading = true
  window.location.reload()
})
```

When a new SW activates and claims the page, `controllerchange` fires →
we reload once → the new SW now serves the new precache → the fresh bundle
loads in the same session. A `reloading` guard prevents loops.

First-ever install also fires `controllerchange` (page was uncontrolled →
claimed) → one extra reload on a fresh profile — harmless one-time cost.
Mid-session reload risk is minimal: the SW update check runs at navigation
(app launch), so the reload lands seconds after startup, not mid-task.

## Trade-offs
- **Chosen:** silent auto-reload on controllerchange.
- **Rejected:** "Update available — tap to reload" toast (extra UI the user
  must discover on a kiosk panel; the app is local so reload is cheap);
  removing the SW entirely (loses offline shell + PWA install; a stale SW
  would also linger after removal anyway).

## Verification Criteria
- `controllerchange` listener present in `main.ts`, guarded against loops.
- Typecheck + build pass; `dist` regenerated.
- After deploy: one restart installs the new SW → auto-reload → new bundle
  active without a second restart.

## Implementation Plan
- [x] Phase 1: controllerchange auto-reload in `main.ts`
- [x] Phase 2: typecheck, build dist, commit/push/merge

## Implementation Results
- Phase 1: guarded `controllerchange` listener added in `main.ts` before
  `app.mount`. Reloads exactly once when a new SW claims the page.
- Phase 2: `npm run type-check` clean; `npm run build` regenerated dist
  (`index-CcG6FGAh.js`, `controllerchange` verified in bundle). dist is
  gitignored — Flask serves it directly.
- Live verification of the original report: in dev, delete-badge click →
  `confirmDialog` → `.confirm-overlay` renders and resolves (the production
  bug was the stale bundle, not the code). User needs ONE more app restart;
  this fix then makes all future deploys single-restart.
