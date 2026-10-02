# DL-131 — Manual-only tour steps + honest spotlight anchoring

## Problem

Two reported tour defects, both from the same place — the tour moved
itself:

1. **Wrong highlight on "Scenes & Pages".** The step targets
   `.enhanced-scene-nav` (desktop header pills) / `.mc-scene-rail`
   (mobile chrome). With the header hidden and no mobile chrome, the
   target is absent → the `optional` flag auto-skipped to "Your Deck",
   spotlighting `.deck-grid` — a grid-sized ring under a scene-step
   title. Even when the target resolved, the spotlight rect was a static
   snapshot: if the 5 s auto-hide slid the header away mid-step, the
   ring stayed parked over whatever slid underneath.
2. **Auto-advance.** `optional` steps skipped themselves on missing
   targets, and `advanceOnPath` advanced on navigation — the user wants
   Next/Back/Skip to be the only way the tour moves.

## Design

- **Manual only.** `advanceOnPath` deleted from the step type and the
  route watcher; the `optional` skip deleted from `prepareStep`. A step
  with no target renders as a centered card — the honest state.
- **Continuous re-anchor.** While the tour is active, a 350 ms interval
  re-measures the target's box — follows transform-driven motion (the
  header's slide-out), drops to the centered card when the target
  unmounts, re-anchors if it reappears. Transforms don't fire
  ResizeObserver and unmounts don't fire resize/scroll, so polling is
  the cheap correct tool at tour cadence.
- Pin interaction is unaffected — the countdown pill and reveal FAB work
  under the `pointer-events:none` overlay.

## Implementation Results

- `services/tutorial.ts`: `advanceOnPath` removed (type + step + route
  watcher branch); `optional` re-documented as "centered card when the
  target is absent".
- `components/TutorialTour.vue`: `prepareStep` never calls `next()`;
  `startReanchor`/`stopReanchor` interval tied to `tour.state.active`.
- **Live-verified** (Playwright, desktop viewport): step 3 stays at
  "3 / 9" with target absent (centered card, no grid highlight).
  Revealing the header mid-step → the re-anchor picks up
  `.enhanced-scene-nav` within one tick and the ring wraps it exactly
  (spotlight = nav box − 10 px pad, verified numerically + screenshot).
- Tests: 5 new (`tutorial-manual-steps.test.ts`) — no step declares an
  advance trigger, missing-target step stays put, next/back index math,
  source assertions for the re-anchor loop and the removed `next()`
  call.
- Full suite green; `dist` rebuilt.

## Implementation Results — orchestrated test campaign (follow-up)

Four parallel test agents swept the new feature surface; three bugs found
and fixed:

1. **MCP `press_button` schema gap** (`routes/mcp.py`) — the tool declared
   no `required`, but the handler needs `button_id` or `button`; added
   `anyOf` so schema-driven clients get pre-call validation. Endpoint
   itself fully verified: all 11 tools, correct JSON-RPC error taxonomy,
   batch/notification semantics, live SMTC data.
2. **`devin` session over-match** (`integrations/sessions.py`) — every
   `Devin.exe` helper of the IDE (~26 procs, one window) counted as a
   session. Two-part fix: `_DESKTOP_APP_BINS` exe-suffix exclusion for the
   install-root IDE binary (the real CLI ships under `resources\` and
   still matches), and argv0 matching tightened to the basename so helpers
   living under `Programs\Devin\` stop matching on path segments. Live:
   26 rows → 2 real CLI sessions.
3. **`ELECTRON_RUN_AS_NODE` launch poisoning** (`actions/program_action.py`,
   `actions/cross_platform_action.py`, `utils/subprocess_runner.py`) —
   the backend, started from an IDE shell, passed `ELECTRON_RUN_AS_NODE=1`
   to every spawned child; Electron targets (the Cursor `.lnk` launcher!)
   ran as bare Node and died instantly while reporting `Launched:`.
   Added `child_env()` stripping `ELECTRON_*`, applied to both launch
   paths. Live-verified: same `.lnk` → 17 `Cursor.exe` processes, and
   `detected-profiles` now reports `cursor`.

Cursor scene flow verified end-to-end: scene removed via PUT, recreated
through the real SceneEditor UI, button grid + agent bar render in both
chromes (desktop `.agent-action-bar`, mobile `MobileAgentConsole`), and
the `.lnk` launcher works post-fix. Integrations verified: app-profiles
map live detection, agent-events inject/surface/clear, triggers CRUD.
Known non-bugs: foreground-window detection needs an interactive desktop
(degrades to 404 in detached sessions); empty POST to `/api/agent-events`
creates a default alert by design (legacy hook compat).

Regression cost of the campaign: one transient module shadow
(`utils/subprocess_runner.py`) — restored and merged; full backend suite
1104 passing.

## Follow-up 2 — reveal the header for steps that point into it

Steps 3 (Scenes & Pages) and 5 (Edit Mode) spotlight elements inside
`DeckHeader`, which unmounts entirely when `showHeader` is false — its
default plus the 5 s autohide mean it's absent almost always, so both
steps rendered as dead centered cards. Step 6 (Agent Sessions) targeted
`.agent-action-bar`, which only mounts while the current scene actually
has agent actions — and its mobile counterpart was never in the
selector.

- `TutorialStep` gains `needsHeader?: boolean`; steps 3 and 5 set it.
  `prepareStep` reveals the header via the settings store (the reveal
  FAB hides in edit mode — the store path can't miss), marks
  `headerRevealedByTour`, then clicks `.autohide-pill:not(.pinned)` so
  the 5 s countdown can't unmount the target mid-step. The
  `:not(.pinned)` guard makes the click conditional — an already-pinned
  header is left alone.
- Mobile viewports skip the reveal entirely: it would swap the mobile
  chrome's `.mc-scene-rail` for the desktop pill nav (spotlighting the
  wrong thing), and the edit button doesn't exist on mobile either way.
  Step 3 highlights the real mobile rail; step 5 keeps its honest
  centered card on phones.
- The reveal is restored when the tour leaves the dashboard (a step
  whose `route` isn't `/`) or when the tour deactivates — a user who
  keeps the header hidden gets it back afterward. If the header was
  *already* visible but counting down, the pin we added is un-clicked on
  restore so the user's countdown resumes (`headerPinnedByTour` —
  tracked separately because an unpinned-then-hidden restore would leave
  the user's header stuck open). Both flags only track changes we made.
- Step 6's target is now `.agent-action-bar, .mobile-agent-console` —
  the mobile agent surface can be spotlighted on touch panels.
- `TutorialStep` also gains `needsAgentScene?: boolean` (step 6): before
  measuring, `prepareStep` switches the deck to the first scene whose
  app profile carries `state_actions` (the same eligibility check
  DashboardView uses), so the bar is real, not imagined. The switch is
  restored when the tour leaves `/` or ends — unless the user already
  tapped a different scene pill (clicks pass through the overlay), in
  which case we don't fight them. No agent scene on the deck → the
  honest centered card still stands — nothing real to point at.

### Results — follow-up 2

- `services/tutorial.ts`: `needsHeader` + `needsAgentScene` step fields;
  steps 3/5/6 updated.
- `components/TutorialTour.vue`: `restoreDashboardState()` owns both
  restorations; `prepareStep` reveals+pins the header (desktop only) and
  hops to an agent scene for step 6.
- **Live-verified** (Playwright, 1440×800, built bundle): step 3
  spotlight = `.enhanced-scene-nav` rect + 10 px pad, header revealed and
  pill auto-pinned; step 5 spotlight wraps the edit button exactly;
  step 6 switched to the "Claude Code" scene and the spotlight wrapped
  the live `.agent-action-bar`; step 7 → header re-hidden + scene
  restored; tour finished clean (`vdock_tutorial_done` written). Ref:
  `refs/tour-step6-agent-bar-*.png`.
- Tests: 4 new in `tutorial-manual-steps.test.ts` (needsHeader flags,
  reveal/pin/restore wiring, agent target union + scene-switch wiring).
  Full suite 570/570, `vue-tsc` clean, `dist` rebuilt.
