# DL-080: Edge-glow + bar highlight when an agent session is waiting

## Background

Agent scenes already report state (`ready | working | permission | unknown`)
in the action bar, and `permission` pops the `AgentAlertOverlay` banner. But
when a session goes `ready` — idle, waiting for the user's next command —
nothing ambient signals it: the user has to read the small state pill.

Requested: while on an IDE scene whose agent session is waiting, glow the
screen boundaries with an animation; highlight which session is idle inside
the interactive bar; gate it behind a setting that defaults to enabled.

## Design

### Edge glow — `AgentWaitingGlow.vue` (new, mounted in DashboardView)

- Mounted next to `AgentActionBar`/`MobileAgentConsole` so it covers desktop
  and mobile layouts (each already shares `useAgentSession`).
- Teleported `<div>` to `body`: `position: fixed; inset: 0;
  pointer-events: none`, animated inset `box-shadow` in the `ready` accent
  (#22c55e), fade-in on entry, gentle breathing pulse while waiting.
- Visible when: `isAgentPossiblyRunning && currentState === 'ready' &&
  !isEditMode && settingsStore.agentWaitingGlowEnabled`.
- `prefers-reduced-motion` and `animationsEnabled` → static edge, no pulse.

### Session highlight — `AgentActionBar.vue`

- `effectiveSession.state === 'ready'` → `.agent-target-chip.waiting` gets a
  pulsing green ring; picker rows with `s.state === 'ready'` get a `waiting`
  tag/ring so the idle session stands out in the list.
- Applies to marker'd agents only (Claude, Devin — Cursor exposes no
  `session_marker`, so no per-session rows; it still gets the edge glow).

### Setting — `agentWaitingGlowEnabled`, default `true`

Mirrors `agentAlertsEnabled` at every lifecycle spot in `settings.ts`
(defaults map, `PersistedUserSettings`, ref, payload, apply, remote merge,
exports). Toggle row added to the existing **Agent attention alerts** panel
in `SettingsView`: "Glow when an agent is waiting".

## Implementation Results

Landed as designed:

- `components/AgentWaitingGlow.vue` (new) — teleported fixed edge-glow,
  breathing green pulse while `ready`, static under `prefers-reduced-motion`
  and `animationsEnabled: false`, hidden in edit mode; `role="status"` +
  aria-label announce the waiting agent.
  - Deviation: mounts via `v-if` (breathing starts on insert) rather than a
    Vue `<Transition>` fade — visually equivalent, one less lifecycle.
- `views/DashboardView.vue` — glow mounted beside the bar/console so desktop
  and mobile layouts share it.
- `components/AgentActionBar.vue` — `waiting` pulse on the target chip when
  the effective session is `ready`; `waiting` tag + row tint on idle rows in
  the session picker; both gated by the same setting.
- `stores/settings.ts` — `agentWaitingGlowEnabled` at all eight lifecycle
  spots, default `true`.
- `views/SettingsView.vue` — "Glow when an agent is waiting" toggle in the
  Agent attention alerts panel.

### Verification

- `agent-waiting-glow.test.ts` (new, 9 tests): glow on `ready` only, hidden
  by setting/edit-mode/not-running, `no-anim` class, default-on, chip pulse,
  picker-row highlight. Full suite: 60 files / 269 tests green;
  `vue-tsc --noEmit` clean.
- Live (dev servers + Chrome DevTools): POSTed `ready` to `/api/agent-events`
  → green edge glow around the viewport on the Claude scene, bar pill "Ready
  for your prompt"; settings toggle unchecked → glow gone, bar unchanged;
  re-enabled + `ended` state POSTed to clean up. Screenshot captured.

## Follow-up (2026-09-27): stronger frame + scene-level guidance

### Problem (follow-up)

The breathing edge-glow alone was not prominent enough, and it only existed
*on* the agent scene — a user on the Media scene had no signal that the
Claude scene's agent was waiting. Requested: a more distinguishable frame
animation around the screen, a highlight on the *scene pill* of whichever
scene's agent is idle when the user is on another scene, and a clearer
highlight on the *idle session* itself once inside.

### Design (follow-up)

Guide chain, weakest → strongest as the user closes in:

1. **Off-scene → scene pill ring.** `sceneAgentIsWaiting(scene, integrations)`
   (new `services/agentWaiting.ts`) resolves `sceneAppProfile → status_source
   → agentStateEntry(state) === 'ready'` — hook-driven, independent of the
   app-scanning poll (which is off by default). `GlassPillSceneSelector`
   (desktop rail) and `MobileDeckChrome` (mobile rail) add `.agent-waiting` to
   the matching segment: pulsing green ring + a stronger pulse on the live
   dot. Both rails `initAgentState()` + `loadProfileMaps()` on mount
   (idempotent) so they work without the action bar mounted.
2. **On-scene → animated frame.** `AgentWaitingGlow` gains a second layer,
   `.agent-waiting-orbit`: a bright conic-gradient "comet" travelling the
   viewport perimeter (registered `--agent-orbit` angle custom property,
   `mask-composite` to a 4px ring, one ~4s linear lap) over the existing
   breathing edge-glow, whose peak amplitude is raised. Constant motion +
   breathing = unmistakable vs. the static amber permission banner.
   `no-anim` / `prefers-reduced-motion` → orbit hidden, glow static.
3. **In-scene → idle session.** `AgentActionBar`: the target chip gains an
   inline `waiting` tag + a stronger pulse when the effective session is
   `ready`, and a small nudge dot when *another* session is the idle one
   (opens the picker, whose ready rows already flag + get a left accent).
   `MobileAgentConsole`: `.mac-session` chips with `state === 'ready'` get
   the same waiting ring.

All three layers gate on the existing `agentWaitingGlowEnabled` setting
(default on); the desktop pill also hides in edit mode like the glow does.
`SceneNavigation.vue` is dead code (no importers) — skipped.

### Implementation Plan (follow-up)

- [x] `services/agentWaiting.ts` — `sceneAgentIsWaiting` helper
- [x] `AgentWaitingGlow.vue` — orbit layer + stronger breathe
- [x] `GlassPillSceneSelector.vue` — per-scene waiting ring + dot + title
- [x] `MobileDeckChrome.vue` — same on `.mc-seg` / `.mc-live`
- [x] `AgentActionBar.vue` — chip `waiting` tag, nudge dot, stronger pulse,
      row accent
- [x] `MobileAgentConsole.vue` — waiting ring on idle session chips
- [x] `SettingsView.vue` — toggle copy updated to cover the new surfaces
- [x] `agent-waiting-glow.test.ts` — orbit, scene-pill, service, chip tests

### Implementation Results (follow-up)

Landed as designed:

- `services/agentWaiting.ts` (new) — `sceneAgentIsWaiting(scene, integrations)`
  resolves scene → profile → `status_source` → `agentStateEntry().state ===
  'ready'`; hook-driven so it works with app scanning off.
- `AgentWaitingGlow.vue` — new `.agent-waiting-orbit` layer: registered
  `@property --agent-orbit` `<angle>` driven by `agent-waiting-orbit` keyframes
  (one 4.5s linear lap), a conic-gradient comet masked to a 4px ring; base
  breathe peak raised (border 0.5→0.95 alpha). Orbit mounts only while
  `animationsEnabled`; `prefers-reduced-motion` hides it and freezes the glow.
- `GlassPillSceneSelector.vue` — `.segment.agent-waiting` pulsing ring +
  `.app-live-dot.agent-waiting-dot` on scenes whose agent is `ready`; dot now
  renders on `live || waiting` (waiting no longer depends on the scanning
  poll); tooltip says "waiting for input" vs "app is running". Rails call
  `initAgentState()`/`loadProfileMaps()` on mount. Gated by the
  `agentWaitingGlowEnabled` setting + `!isEditMode`.
- `MobileDeckChrome.vue` — same cue on `.mc-seg` / `.mc-live`.
- `AgentActionBar.vue` — chip gains an inline `waiting` tag + stronger pulse
  (1.8s, larger amplitude, tinted background) when the effective session is
  idle, plus a `.chip-waiting-nudge` beacon when a *different* session is the
  idle one; ready picker rows get a green left accent.
- `MobileAgentConsole.vue` — `.mac-session.waiting` ring on chips whose
  `state === 'ready'`; gated by the same setting. Deviation: the console
  needed `useSettingsStore`, which `mobile-agent-console.test.ts` didn't
  mock — a `useSettingsStore` mock was added to that file.
- `SettingsView.vue` — toggle copy now describes the comet frame, the scene
  pill ring, and the session flag.
- `SceneNavigation.vue` untouched — dead code (no importers).

### Verification (follow-up)

- `agent-waiting-glow.test.ts` (+12): orbit mount/anim-off/`@property`
  source, selector ring + dot + setting/edit-mode gating, chip `waiting`
  tag + other-session nudge, `sceneAgentIsWaiting` resolution chain, mobile
  chrome/console wiring. `mobile-agent-console.test.ts` (+1): waiting class
  on idle chip, off with the setting. Suite: **60 files / 282 tests green**
  (was 269); `vue-tsc --noEmit` clean.
- Live (Vite :4444 + backend :5000 + Playwright): POSTed `ready` to
  `/api/agent-events` → on the Media scene the Claude Code pill carried the
  ring + waiting dot + "waiting for input" title while Media/Cursor/Websites
  stayed clean; on the Claude Code scene the breathing frame + comet ran
  (`--agent-orbit` computed at 18.6° mid-lap, mask-composite resolved to a
  ring). Screenshots in `design-log/refs/agent-waiting-frame-*.png` and
  `agent-waiting-comet-*.png`. Chip tag/nudge covered by unit tests — no
  live session windows were present to target. State reset via `ended`.

## Follow-up #2 (2026-09-27): whole-dashboard flash, style config, snooze

### Problem (follow-up #2)

Reviewing the shipped follow-up, the travelling comet was not the wanted
cue: the user asked for the *whole dashboard* to flash — an unmistakable
"there is an idle agent session" signal no matter which scene is showing —
plus two missing controls: a way to **configure** the alert style, and an
intuitive way to **stop the alert** after seeing it when they don't want to
answer the session (without disabling the feature forever).

### Design (follow-up #2)

1. **Global frame.** `AgentWaitingGlow` no longer keys on the current scene:
   it scans `currentProfile.scenes` through a new
   `sceneWaitingAgent(scene, integrations)` helper and flashes the viewport
   frame while *any* scene's agent sits `ready`. The scene-pill ring (kept)
   identifies which scene wants the visit; the session rows/chips (kept)
   identify which session.

2. **Flash as the default style.** New persisted setting
   `agentWaitingGlowStyle: 'flash' | 'pulse' | 'orbit'` (default `flash`,
   wired at all eight `settings.ts` lifecycle spots). `flash` is a
   heartbeat double-blink of the entire border + inset glow — two quick
   bright pulses then a rest, ~2.4s cycle — unmistakable but under the
   3-flashes/sec photosensitive threshold. `pulse` keeps the earlier
   breathe; `orbit` keeps the comet layer (rendered only for that style).
   `no-anim`/`prefers-reduced-motion` → static frame for all styles.

3. **Snooze — dismiss until the next episode.** `agentWaiting.ts` keeps a
   reactive `dismissedReadyTs` map keyed by agent source: snoozing stores
   the `ts` of the current `ready` entry, and `sceneAgentIsWaiting` /
   `sceneWaitingAgent` report "not waiting" while the stored ts matches.
   The backend stamps a fresh `ts` on every hook event, so the next real
   `ready` episode (or any state change) re-arms the alert automatically —
   one tap, not a permanent opt-out. The affordance is a floating chip
   pinned to the bottom edge of the frame: "<label> is waiting for input —
   Snooze", `pointer-events: auto` (the frame itself stays none). Dismissal
   clears every surface at once — frame, pill ring, session-chip rings —
   because they all read the same helper. Kept in-memory: a page reload
   re-shows a still-idle session, which is honest.

4. **Configure.** A style `<select>` under the existing glow toggle in
   Settings → Agent attention alerts (visible only while the toggle is on):
   Flash / Pulse / Comet.

`sceneAgentIsWaiting` keeps its signature — both scene rails get the
dismissal semantics for free.

### Implementation Plan (follow-up #2)

- [x] `services/agentWaiting.ts` — `sceneWaitingAgent`, `dismissAgentWaiting`,
      `isAgentWaitingDismissed`; `sceneAgentIsWaiting` delegates
- [x] `AgentWaitingGlow.vue` — any-scene scope, `style-*` class, flash
      keyframes, bottom snooze chip; drop the `scene` prop
- [x] `stores/settings.ts` — `agentWaitingGlowStyle` (default `flash`)
- [x] `SettingsView.vue` — style select row
- [x] `DashboardView.vue` — mount without the `scene` prop
- [x] Tests + live verify + results

### Implementation Results (follow-up #2)

Landed as designed:

- `services/agentWaiting.ts` — new `sceneWaitingAgent(scene)` returns
  `{profile, entry}` when the scene's agent is `ready` and not snoozed;
  `sceneAgentIsWaiting` delegates so both rails inherit dismissal for free.
  `dismissAgentWaiting(source)` stores the ready entry's `ts`;
  `isAgentWaitingDismissed` matches on ts — the backend stamps a fresh `ts`
  per hook event, so the next `ready` episode re-arms automatically.
- `AgentWaitingGlow.vue` — scope widened from current-scene to
  any-scene-in-profile (`currentProfile.scenes` scanned via
  `sceneWaitingAgent`); `scene` prop dropped. `style-flash` (default) runs a
  heartbeat double-blink (`agent-waiting-flash`, 2.4s: two ~200ms bright
  pulses then a dim rest — under the 3-flashes/sec photosensitive floor);
  `style-pulse` keeps the breathe; `style-orbit` keeps the comet layer,
  mounted only for that style. New `.agent-waiting-snooze` chip pinned
  bottom-center over the empty footer strip: "<label> is waiting for input"
  + a Snooze button, `pointer-events: auto`, z-2100 (below the permission
  banner's 30000), pop transition on mount.
- `AgentActionBar.vue` / `MobileAgentConsole.vue` — `waitingGlowOn` now also
  requires `!isAgentWaitingDismissed(profile.status_source)`, so snoozing
  silences the chip pulse, nudge dot, and row accents along with the frame.
- `stores/settings.ts` — `agentWaitingGlowStyle` ('flash' | 'pulse' |
  'orbit', default 'flash') at all eight lifecycle spots.
- `SettingsView.vue` — "Waiting alert style" select (Flash / Pulse / Comet)
  under the glow toggle, shown only while the toggle is on; toggle copy
  updated to describe the dashboard-wide flash and the Snooze control.
- `DashboardView.vue` — `<AgentWaitingGlow />` (no prop).
- Deviation: none vs. the follow-up design. The original design sections
  still describe the current-scene breathe + comet as built; the flash and
  snooze supersede the default experience per this follow-up.

### Verification (follow-up #2)

- `agent-waiting-glow.test.ts` (26 tests, was 21): any-scene scope, flash
  default class + style switching, snooze chip render + click → all
  surfaces gone, orbit gated to its style, service-level dismiss +
  ts re-arm via a fired socket handler. `mobile-agent-console.test.ts`
  (11). Suite: **60 files / 287 tests green**; `vue-tsc --noEmit` clean.
  (One pre-existing vitest teardown flake — `onUserConsoleLog` rpc error in
  `property6_settings.test.ts` — reproduces on a clean tree, unrelated.)
- Live (Vite :4444 + backend :5000 + Playwright): POSTed `ready` → frame
  `style-flash` animating (`agent-waiting-flash` 2.4s infinite), snooze
  chip "Claude Code is waiting for input — Snooze" rendered bottom-center,
  Claude Code pill ringed while on the Media scene. Click Snooze → frame,
  chip, and pill ring all gone. Fresh `ready` POST → everything re-armed.
  Settings → Integrations → Agent attention alerts → "Waiting alert style"
  select: flash→orbit→pulse each applied live (orbit showed the comet at
  289° mid-lap; pulse ran `agent-waiting-breathe`). Restored `flash`,
  fake `default` session ended — the remaining `ready` state is the user's
  real Claude session. Screenshot:
  `design-log/refs/agent-waiting-flash-snooze-*.png`.

## Follow-up #3 (2026-09-27): louder scene/session markers on small panels

### Problem (follow-up #3)

The off-scene and in-scene markers use 2 px outline rings and ~10% alpha
fills — tuned for a desktop monitor at arm's reach. On the 7" touch panel
they are "barely visible" (user report): thin strokes and faint tints
disappear against the glass-pill rail and the sheet rows.

### Design (follow-up #3)

Escalate every waiting marker from *outline* to *filled + thick ring +
stronger pulse* — same `#22c55e` accent, higher alpha, faster cadence
(2.4s → 1.6s), larger glow radii. Reduced-motion still freezes animation
while keeping the filled static state.

- Scene pills (desktop `.segment.agent-waiting`, mobile
  `.mc-seg.agent-waiting`): 3 px inset ring + green background wash
  (0.16→0.38 alpha pulse) + 12→26 px outer glow; waiting dot up to 12 px
  with a halo shadow.
- Session rows (`.agent-target-row.waiting`): 10% → 18–34% fill pulse,
  4 px solid left bar, 1.5 px inner ring.
- Target chip (`.agent-target-chip.waiting`): 12% → 20–36% fill, 2→4 px
  glow ring at brighter peak; nudge dot 10 → 12 px.
- Mobile session chips (`.mac-session.waiting`): 1 px border → 2 px,
  dark fill → 25% green, glow ring pulse.

### Implementation Results (follow-up #3)

- `AgentActionBar.vue`: `.agent-target-chip.waiting` 0.12 → 0.20–0.36 fill
  pulse + `#4ade80` border + up to 4 px glow; `.agent-target-row.waiting`
  0.10 → 0.18–0.34 fill + 4 px solid `#7deba5` left bar + 1.5 px inner
  ring; `.chip-waiting-nudge` 10 → 12 px. Added missing reduced-motion
  rules for chip pulse, nudge, and row pulse.
- `GlassPillSceneSelector.vue` / `MobileDeckChrome.vue`: `.segment` /
  `.mc-seg.agent-waiting` now 3 px inset ring + green wash (peaks ~0.29–0.38)
  + outer glow up to ~26 px; waiting dots enlarged with halo shadows.
  Pulse cadence 2.4s → 1.6s.
- `MobileAgentConsole.vue`: `.mac-session.waiting` 1 px → 2 px `#4ade80`
  border + 0.25 fill + ring pulse.
- Verified live (Playwright, real `ready` state on session
  `fe21fdb4…`): desktop 1280×800 — scene pill ringed (`agent-waiting`),
  chip `pinned waiting`, picker row `active waiting` (bg
  `rgba(34,197,94,0.325)`, 4 px left bar + 1.5 px inset ring); mobile
  480×800 — `mc-seg.agent-waiting` (3 px inset ring, 0.29 fill,
  `mc-waiting-pulse` running), `mac-session.active.waiting` (2 px
  `#4ade80` border, 0.25 fill). Screenshots:
  `design-log/refs/agent-waiting-strong-cues.png`,
  `design-log/refs/agent-waiting-mobile-cues.png`.
- Tests: focused `agent-waiting-glow` + `mobile-agent-console` 37/37
  green; `vue-tsc --noEmit` clean.
- Note: the picker row had shown `state: null` — a synthetic test POST
  had overwritten the real session's hook `cwd` (repo root vs `backend`),
  breaking the cwd→hook join in `agent_sessions.py`; re-posting with the
  correct cwd restored the join. No code change needed.

## Follow-up #4 (2026-09-27): mobile guidance — scroll the rail to the waiting scene

### Problem (follow-up #4)

On mobile the scene rail (`.mc-scene-rail`) is `overflow-x: auto` — on a
narrow phone the glowing `.mc-seg.agent-waiting` segment can be scrolled
completely off-screen. The whole-dashboard frame flashes "an agent waits",
but the *where* is invisible: the user must guess and manually hunt the
rail. The highlight exists but isn't *applied intuitively* — it doesn't
reach the user's eye.

### Design (follow-up #4)

When a **non-active** scene's agent starts waiting and its rail segment is
clipped, smooth-scroll the rail so the segment becomes visible — once per
waiting episode:

- Episode key is `sceneId:entry.ts` (the same backend timestamp the snooze
  dismissal uses). The key is marked before scrolling, so if the user
  scrolls the rail away afterwards we never fight them; a new `ready`
  event (new `ts`) is a new episode and may scroll again.
- Only scrolls when the segment is actually clipped
  (`offsetLeft`/`offsetWidth` vs `scrollLeft`/`clientWidth`) — a visible
  waiting segment is never moved.
- Active scene is skipped (already kept visible by `measureGlider`'s
  `scrollIntoView` on scene change); dismissal is respected automatically
  because `sceneAgentIsWaiting` reports false for snoozed episodes.
- `prefers-reduced-motion` gets an instant (`behavior: 'auto'`) scroll.

### Implementation Results (follow-up #4)

- `MobileDeckChrome.vue`: new `waitingRailKey` computed (`sceneId:entry.ts`
  per waiting scene) watched with `flush: 'post'` →
  `scrollWaitingIntoView()` smooth-scrolls the first *clipped* waiting
  segment into view. Keys kept in `autoScrolledWaits` and pruned when the
  episode ends, so each episode auto-scrolls at most once. Also runs on
  mount (a session already waiting when the app opens still gets
  revealed). Deviation from the design note: the *active* scene is
  included too — the glider only re-scrolls it on scene change, and a
  waiting active segment is the guide target.
- Verified live at 360×640 (rail overflows: scrollW 408 vs clientW 238):
  manually scrolled `scrollLeft` to 170, clipping the waiting Claude Code
  segment; POSTed a fresh `ready` event → rail auto-scrolled to 84, the
  segment's exact offset — fully revealed, pulse visible.
- Screenshot: `design-log/refs/mobile-waiting-rail-reveal.png`.
- `vue-tsc --noEmit` clean. No unit test — jsdom has no layout
  (`offsetLeft`/`scrollIntoView` unstubbed = always "not clipped");
  behavior verified live.

### Addendum (2026-09-27): bigger snooze chip on touch panels

`.agent-waiting-snooze` was fixed-size (0.85rem, ~8px padding) — it ignored
`--touch-multiplier`, so the 7" panel got a desktop-mouse-sized chip.
Now scales: font 0.95rem×min(tm,1.6) (≈24px at tm=2), padding and gap
multiply, `.snooze-btn` gets `min-height: max(36px, --min-touch-target×0.8)`
and 0.9rem×1.6 text (≈53px tall, 23px font). The 520px compaction keeps a
0.85rem floor + `max-width: 100vw-16px` so it can't clip. Measured live:
599×87px chip at tm=2. Screenshot: `design-log/refs/snooze-chip-bigger-*.png`.

## Follow-up #3 — timed snooze (3 minutes)

**Problem.** Follow-up #2's snooze silenced the alert for the rest of the
waiting episode — effectively forever when the agent sits idle for a long
stretch. The user asked for a 3-minute mute: quiet now, re-alert later if
the session is *still* waiting.

**Design.** `dismissedReadyTs[source]` upgrades from a bare episode `ts`
to `{ ts, until }`. `isAgentWaitingDismissed` requires the same episode
**and** `Date.now() < until` — so three independent exit paths exist:

1. Timer expiry (~3 min): a per-source `setTimeout` deletes the reactive
   record; `Date.now()` isn't reactive, so the deletion is what wakes the
   `sceneAgentIsWaiting` computeds to re-fire the alert.
2. New episode: a fresh `ready` event stamps a new `entry.ts`, which
   fails the `d.ts === entry.ts` check regardless of time left — a NEW
   waiting episode is a new thing to alert about and re-arms instantly.
3. Agent leaves `ready` mid-snooze: entry check fails; the pending timer
   just deletes a stale record later.

Re-snoozing inside the window extends to a fresh 3 minutes
(`clearTimeout` + new `until`). The snooze chip reads "Snooze 3m" so the
duration is discoverable at the moment of decision.

**Implementation results (follow-up #3).** `dismissedReadyTs[source]` now
stores `{ ts, until }`; a per-source `setTimeout` deletes the record at
`AGENT_SNOOZE_MS + 250ms` — the deletion is the reactive poke that wakes
the waiting computeds. Snooze chip reads "Snooze 3m". Verified: unit
coverage for expire/re-arm/clear/extend paths (`agent-waiting.test.ts`,
4 new tests, fake timers); live in WebKit — snooze hid the frame, a fresh
`ready` event re-armed instantly; 291/291 green, `dist` rebuilt.
