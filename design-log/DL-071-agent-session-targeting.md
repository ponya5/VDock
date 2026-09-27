# DL-071 — Agent session targeting (session picker + pin)

## Background

Terminal-agent buttons (`cc_*`, `devin_*`) send keystrokes into the window
hosting a live CLI session. With several sessions running (multiple `claude`
terminals), `find_session_host_window` picks one by ranking: button's
configured "Session working directory" → focused editor's project dir →
newest session. The resolution works, but it is invisible — the user cannot
see which session a press will hit, and there is no way to say "this one".

## Problem

With multiple Claude CLIs open, deck buttons feel random. The user asked for
a way to see and choose the target session.

## Questions and Answers

**Q: Pin or per-button cwd?**
A: User picked "session picker + pin": one deck-level target that all
`session_marker` buttons route to until changed or the session dies.

**Q: Pin identity — hwnd or pid?**
A: PID. The host window is re-resolved live from the pid each press, so
surviving tab/window changes don't stale the pin. A dead pid clears the pin
and falls back to auto-resolution.

**Q: Pin vs per-button configured cwd precedence?**
A: Pin wins. It is the most recent explicit user choice ("control THIS
session"); a stale button-level cwd silently diverting presses elsewhere is
more confusing than the pin overriding it.

**Q: Session list source — process scan or hook-reported state?**
A: Process scan (`sessions.iter_session_pids` + host-window walk) is the
source of truth: it works without hooks installed. Hook state
(`agent_state` per-session entries carry `cwd`/`project`/`state`) enriches
rows by matching cwd — shows which session is working/waiting when the hook
is installed.

## Design

### Backend

- `utils/window_focus.py`
  - Extract per-session host enumeration into
    `session_host_candidates(marker)` → list of
    `(pid, hwnd, title, self_owned, cwd_tier, create_time)` rows; existing
    ranking stays on top.
  - `find_session_host_window(..., prefer_pid=None)`: a `prefer_pid` that has
    a host window wins outright, skipping ranking.
  - `list_session_hosts(marker)` → one dict per session that owns a window:
    `{pid, hwnd, title, cwd, create_time}` newest first. Windowless sessions
    (headless `claude -p` jobs) are excluded — nothing can be typed into them.
- `integrations/sessions.py` — pin registry keyed by marker:
  `pin_session(marker, pid)`, `unpin_session(marker)`,
  `pinned_pid(marker)` (returns None and clears when the pid no longer looks
  like a live session). In-memory only — a pin means nothing once the session
  or the backend restarts.
- `integrations/editor_base.py::_resolve_session_host` — check
  `sessions.pinned_pid` first; alive pin with a host window returns it, dead
  pin falls through to existing resolution.
- `integrations/agent_state.py` — `session_entries(source)` accessor
  returning the raw per-session entries (snapshot() only exposes the combined
  view).
- `routes/agent_sessions.py` — new blueprint, registered in `app.py`:
  - `GET /api/agent-sessions?source=claude` → `{sessions:[{pid, cwd,
    project, title, state}], pinned_pid, resolved_pid}`. `source` is
    validated against the set of `session_marker` values known to the keymaps
    so the param can't be used to scan arbitrary processes. `resolved_pid`
    runs the same resolution a press would (pin → focused editor cwd →
    newest) so the UI can label the effective target.
  - `POST /api/agent-sessions/target` `{source, pid}` pins; `pid: null`
    unpins. Pin validates the pid is a live session for that marker.

### Frontend

- `api/appProfiles.ts` — add `session_marker` to `AppCommandDto` (already
  serialized by the backend).
- `api/agentSessions.ts` — types + `fetchAgentSessions(source)` +
  `pinAgentSession(source, pid|null)`.
- `composables/useAgentTargets.ts` — per-source session list, pinned/resolved
  pid, refresh (polled while the bar is visible, ~4 s), `pinTarget`/`unpin`.
- `AgentActionBar.vue` — target chip between the state pill and the actions
  when the scene's profile has a session marker (kind `terminal_agent`):
  shows the effective target (project/cwd basename or "Auto"), opens a small
  popover listing live sessions (project dir + window title + hook state dot)
  with an "Auto (newest/project match)" entry to clear the pin.

Mobile console (`MobileAgentConsole.vue`) intentionally untouched this pass —
it can reuse `useAgentTargets` later.

## Trade-offs

- In-memory pin over persisted: a pinned pid is meaningless across restarts;
  persisting it would restore a dead target.
- Poll-based session list over socket push: sessions change rarely and the
  GET is a cheap process enum; a push channel adds backend→frontend wiring
  for no real latency win. Revisit if polling shows up in profiles.
- Picker in the action bar over a settings page: targeting is a live,
  in-the-moment decision; burying it in settings defeats the purpose.

## Verification Criteria

- With two `claude` terminals in different directories, the picker lists both
  with distinguishable cwd/title.
- Pinning session A then pressing Submit/Interrupt lands keys in A's window
  even when B is newer or the focused editor points at B's project.
- Killing the pinned session auto-falls back to auto resolution.
- `pid: null` restores auto behaviour.
- Existing resolution unchanged when no pin set (unit tests for
  `prefer_pid` ranking + pin lifecycle).

## Implementation Results

- Backend: `_session_host_candidates` extracted in `window_focus.py`
  (candidates now carry their session pid); `find_session_host_window`
  gained `prefer_pid` that wins outright before ranking; `list_session_hosts`
  returns one row per windowed session, newest first, preferring hosted over
  self-owned windows. `sessions.py` gained the `_pins` registry
  (pin/unpin/pinned_pid — validates liveness on every read and clears dead
  pins). `editor_base._resolve_session_host` checks the pin before the cwd
  heuristics. `agent_state.session_entries` exposes per-session hook rows.
  `routes/agent_sessions.py` (registered in `app.py`) serves
  `GET /api/agent-sessions?source=` and `POST /api/agent-sessions/target`.
- Frontend: `AppCommandDto.session_marker`; `api/agentSessions.ts`;
  `useAgentTargets` composable (4 s poll while mounted); `AgentActionBar`
  shows a crosshairs chip with the effective target and a popover listing
  Auto + live sessions (project/cwd/title, hook-state dot, auto tag).
  `/agent-sessions` added to the client's expected-404 list for stale
  backends.
- Tests: `tests/test_session_targeting.py` — 10 tests covering pin lifecycle,
  dead-pin self-clear, marker isolation, prefer_pid vs newest/cwd-match,
  one-row-per-session listing, and the routes. Backend suite: 864 green.
- Deviations:
  - **Matcher fix beyond the plan.** Live verification found
    `chrome-native-host.exe` (Claude desktop app's Chrome bridge) matching
    the `claude` marker via its argv[0] *path* — `_is_desktop_app` only
    checked the process name. Without the fix the picker listed a Chrome tab
    as a session. `_DESKTOP_APP_DIRS` now covers the MSIX package family
    (`packages\claude_`, `chromenativehost`) and the check applies to
    exe/argv[0] regardless of name.
  - **`detected-profiles` aligned to `iter_session_pids`.** The route had
    its own looser substring scan (`marker in joined_cmdline`), which is why
    `claude-code` showed detected while no real session existed — a live,
    pre-existing test failure on this machine. It now shares the tightened
    matcher, so the live dot, the picker and the keystroke gate all agree.
  - Two sessions sharing one terminal window (two claude tabs in the same
    `wt.exe`) still map to the same hwnd — pinning selects the process, but
    keystrokes land in whichever tab is active. Out of scope; real tab-level
    targeting would need per-terminal tab switching.

## Follow-up — mobile session strip

- `useAgentTargets` gained `profileSessionMarker(profile)` — marker
  derivation shared by the action bar and the mobile console (was
  duplicated inline in `AgentActionBar`).
- `MobileAgentConsole.vue` renders a `.mac-sessions` chip strip under the
  status card. Deliberately not a dropdown: DL-069's wrap-not-scroll rule —
  on a 390 px phone every choice must be visible at once. Chips are 44 px
  touch targets: an `Auto` chip plus one per live session (state dot,
  project/title label, thumbtack on the pinned one; the auto-resolved
  session gets a soft accent border).
- The strip renders **only** when `sessions > 1` or a pin is set — a single
  session resolves to itself, so the row would be clutter.
- Tap behaviour: tap session = pin; tap pinned session = release to Auto
  (same as tapping the Auto chip); haptic tick on selection.
- Other IDEs: editor profiles (Cursor, VS Code, …) carry no
  `session_marker` — keystrokes target the focused editor *window*, not a
  per-process session, so there is nothing to pick and the strip stays
  hidden. Per-window IDE targeting would be a separate feature.
- Tests: `mobile-agent-console.test.ts` mocks `useAgentTargets` and covers
  hidden-when-single, chip listing + pin on tap, and pin-release-to-Auto.
  Suite: 251 frontend tests + vue-tsc green.

## Follow-up 2 — popover trapped behind the deck

- **Bug (manual verification):** clicking the target chip showed only a
  sliver of the popover behind the deck buttons, and the click-away backdrop
  covered just the bar itself. Root cause: `.agent-action-bar`'s
  `backdrop-filter` makes the bar the containing block for `position: fixed`
  descendants *and* a stacking context that paints beneath the later-in-DOM
  deck grid — so both `fixed` pieces were clipped/confined to the bar box.
- **Fix:** backdrop + popover are `<Teleport to="body">`, popover anchored
  `position: fixed` at `chip.getBoundingClientRect().bottom`, left clamped
  to the viewport; backdrop z-1500 / popover z-1501 (above deck ~999 layers,
  below quick-deck/modals). Scoped styles still apply to teleported nodes.
- 254 frontend tests green after the change.

## Follow-up 3 — mobile console is control-only; strip always shows target

- **Conversation card removed from mobile.** The user does not read agent
  replies on the phone surface — `MobileAgentConsole.vue` dropped
  `.mac-conversation`, the prompt/reply/working/permission message articles,
  and the scroll-to-newest plumbing (`conversationRef`, `hasConversation`,
  `lastPrompt`, `lastReply`, `workingMessage`, watchers). The status card's
  second line now shows `stateEntry.message` (the hook's detail — "needs
  permission to use Bash", the current task) falling back to the generic
  state label, so Approve/Deny and Interrupt stay informed without a chat
  box. Mobile surface is now: status → session chips → state actions →
  shortcut tiles.
- **Strip visibility relaxed.** Was `sessions > 1 || pinned` — now shown
  whenever ≥1 live session exists or a pin is set, so the current target is
  always on screen. Also fixes the reported "no session handling visible":
  on this machine 3 `claude` sessions existed but the running backend
  predated `/api/agent-sessions` (404 → empty list → strip hidden);
  backend restart + page reload is required for the strip to appear.
- **Duplicate labels disambiguated by pid.** `useAgentTargets` gained
  `sessionRows` — rows with a `label` field; when several sessions share the
  same project/title label (this machine: 3 sessions all titled
  `✳ VDOCK-OK`, same cwd → three identical rows), a `· #<pid>` suffix is
  appended so every chip/picker row is distinguishable. `AgentActionBar`
  popover and the mobile strip both render `sessionRows`.
- Tests: `mobile-agent-console.test.ts` updated — asserts no conversation
  card/composer ever renders, permission detail shows in the status line,
  strip hides only with zero sessions, pin-on-tap and release-to-Auto.
  Suite: 253 frontend tests + vue-tsc green.

## Follow-up 4 — session identification (which row is which terminal)

A pid label (`backend · #30952`) doesn't tell the user which *physical*
window a session is — on this machine 3 sessions were identical (`✳
VDOCK-OK`, same cwd). Identification needed a real-world affordance, not
more metadata.

- **`flash_window(hwnd)` in `utils/window_focus.py`** — ctypes
  `FlashWindowEx(FLASHW_ALL, count=4)`: blinks the session window's
  titlebar + taskbar button without stealing focus.
- **`POST /api/agent-sessions/identify {source, pid}`** — finds the
  session's host hwnd and flashes it; 404 for a dead pid, marker validated
  like `/target`.
- **GET rows enriched**: `detail` (hook `message` — the current task — else
  the last `prompt`) and `started` (process create_time → "since HH:MM").
  Hook detail is the best distinguisher when installed; started-time still
  separates identical sessions without hooks.
- **Desktop popover**: rows are now a container with two controls — the
  pick button and a per-row **locate (eye) button** that flashes without
  pinning. Subtitle shows `detail · title · since HH:MM`.
- **Flash-on-pin**: `chooseTarget` on both surfaces fires `identify` when
  arming a session — the picked terminal visibly waves back. Auto/release
  flashes nothing (nothing was armed). Mobile relies on this especially:
  chips can't carry long descriptions, the flash is the identification.
- Not added: flash on every `send()` — `focus_first` already raises the
  target window on each press, so the terminal jumping forward is itself
  the confirmation; a taskbar blink on top would be noise.
- Tests: `test_session_targeting.py` +3 (identify flashes matching hwnd,
  dead-pid 404 / bad-source 400, GET exposes detail+started) — 13 backend
  session tests green. `mobile-agent-console.test.ts` +1 (pin flashes,
  Auto doesn't) — 254 frontend tests + vue-tsc green. Live-verified:
  `POST identify` on real pid flashed the actual terminal window.

## Follow-up 5 — rate limiter starved the picker ("No session" + toast spam)

- **Bug (user report):** picker showed "No live session windows found" with
  3 `claude` terminals running, plus a persistent "Too Many Requests" toast.
- **Root cause:** this repo's `.env` sets `RATELIMIT_ENABLED=True` /
  `RATELIMIT_DEFAULT=200 per day, 50 per hour`. `agent_sessions_bp` was
  registered but never `limiter.exempt()`ed — the only polling blueprint
  still under the cap. The 4 s poll (~900 req/hr) exhausts the quota in
  ~3 min; `fetchAgentSessions` then got 429 → the composable's catch keeps
  the last (empty) list → "No session", and each 429 fired the toast.
- **Fix:** `limiter.exempt(agent_sessions_bp)` in `app.py`, matching the
  established pattern (agent_events, metrics, app_monitor… already exempt
  as localhost polling, not abuse surface).
- Verified live: 6 rapid polls all 200; backend suite green.

## Follow-up 6 — params double-wrap broke every poll ("Unknown or missing
## agent source" toast + permanent "No session")

- **Bug (user report):** "Request Failed — Unknown or missing agent
  source" toasts on the deck, picker permanently empty despite live
  sessions.
- **Root cause:** `apiClient.get(url, params)` already wraps its second
  arg into axios's `{ params }` config. `fetchAgentSessions` passed
  `{ params: { source } }` — double-wrapped — so axios serialized
  `?params[source]=claude` and the backend never saw `source` → 400 →
  toast each 4 s poll → `sessions` stayed empty → "No session".
  Reproduced exactly: `?params[source]=claude` → 400 with the toast's
  text; `?source=claude` → 200 with all sessions.
- **Same latent bug fixed in two pre-existing callers** that silently
  degraded instead of erroring: `hook-status` in SettingsView (backend
  defaulted `agent=claude`, so every integration tile showed Claude's
  hook state) and `WeatherQueryButton` (`location`/`unit` never reached
  the backend). Convention in this client: pass the params OBJECT
  directly (`apiClient.get(url, { source })`), like `marketService` and
  `newsService` do.
- Verified: vue-tsc clean, affected test files green.

## Follow-up 7 — picker sizing for the 7" touch panel + mobile sheet

- **Bug (user report):** popover rows ~40 px at 0.95 rem on a 1024×600
  panel — too small for the device's primary input (touch); and the fixed
  280 px dropdown shape didn't adapt to phone widths.
- Chip now `min-height: 44px`, label `clamp(0.9rem, 2.6vh, 1.1rem)`,
  max-width 320 px; popover `min-width: 320px`, `max-width: min(480px,
  92vw)`, `max-height: 60vh`; `.row-pick` `min-height: 56px` with
  `clamp(0.95rem, 2.4vh, 1.1rem)`; `.row-locate` 44×44 px; sub line
  0.82 em.
- **Mobile (≤720 px):** popover becomes a full-width sheet (`left/right:
  8px`, `max-width: none`, `max-height: 55vh`) — `toggleTargetPicker`
  skips the inline `left` on narrow viewports so the media query owns
  placement. Rows stay ≥52 px and the locate button 44 px for thumbs.


## Follow-up 8 — picker still tiny on a 1024×600 7" landscape panel

- **Bug (user report):** on the 7" bottom screen the session picker is
  "very very small". Two causes: the sheet breakpoint only fires at
  `max-width: 720px` — a landscape 1024×600 panel misses it and gets the
  320 px floating dropdown — and none of the popover sizes consume the
  `--touch-multiplier` / `--min-touch-target` vars that touch mode sets
  (convention: `calc(<base> * var(--touch-multiplier, 1))`, per
  `ButtonActionsSidebar`/`DeckFooter`).
- **Design:** the sheet condition becomes `(max-width: 720px),
  (max-height: 700px)` — short viewports of any width get the full-width
  sheet. `toggleTargetPicker` stops writing the inline `left` when
  `innerHeight <= 700` too, so the media query owns placement (inline
  style would beat the stylesheet). Popover + row sizes scale with
  `var(--touch-multiplier)`/`var(--min-touch-target)`; row text uses a
  `vh`-driven clamp so it grows on short screens.
- **Landed:** sheet breakpoint is `(max-width: 720px), (max-height: 800px),
  (pointer: coarse)` — covers landscape 7" panels (600/720/800 tall) and
  touch-first devices regardless of size; the sheet centers itself via
  `margin-inline: auto` + `max-width: 560px × --touch-multiplier` instead of
  stretching edge to edge. `toggleTargetPicker` mirrors the same conditions
  (incl. `navigator.maxTouchPoints` for touch-as-secondary-pointer) before
  writing the inline `left`. Structural sizes (row min-height, locate
  button, dot, padding) scale with `--touch-multiplier` /
  `--min-touch-target`; text follows a `vh` clamp only — tablet mode (×2)
  doubled row text to 44.8 px against a 17.6 px chip label, so the
  multiplier was removed from font rules.
- **Bug fixed in passing:** the "Auto" row was a bare
  `button.agent-target-row` that never received `.row-pick` sizing — it
  rendered as a squished pill next to the tall session rows. Now wrapped in
  the same `.agent-target-row > .row-pick` structure.
- **Verified live (1280×800, tm=2):** sheet 1120 px centered, rows 75 px,
  main 22.4 px / sub 20.6 px, locate 52×52 px; Auto row identical to
  session rows. Suite: 60 files / 287 tests green, `vue-tsc` clean.
  Screenshot: `design-log/refs/picker-sheet-fixed-*.png`.

## Follow-up #9 (2026-09-27): picker sheet/detach desync + bigger reveal pill

### Problem (follow-up #9)

Two issues surfaced on the 7" panel:

1. **Stale dist build** — the backend serves `frontend/dist` (last built
   Sep 26), so the panel showed the pre-follow-up-#8 picker: a ~280px
   dropdown with a bare `<button>` Auto row rendered by UA styles as a
   squished white pill. Rebuilt dist; all fixes ship now.
2. **Real desync in follow-up #8** — the JS gate skipped the inline `left`
   when `maxTouchPoints > 0`, but the CSS sheet rules only fire on
   `max-width:720px / max-height:800px / pointer:coarse`. A touch-capable
   device at a roomy viewport (e.g. 1280×900) matched neither → no inline
   left, no sheet → popover pinned at `left:0` in the corner, and the
   "once" logic lived in two places that could disagree.

### Design (follow-up #9)

Single source of truth in JS: on open, compute `isSheet = matchMedia(
'(max-width: 720px), (max-height: 800px), (pointer: coarse)').matches ||
navigator.maxTouchPoints > 0` and bind a `pop-sheet` class on the popover.
The sheet styles move off the media query onto `.pop-sheet`, so the class
— not two parallel condition sets — decides the layout. Inline `left` is
set only when `!isSheet`, anchoring the dropdown under the chip; the
popover can no longer end up unanchored.

`DeckHeader.vue` `.reveal-pill`: enlarged to a finger-first 52px base
(scales to ~83px at touch-multiplier 2), 1rem→1.6rem font, wider padding —
it now floats free in the corner and can afford the size it couldn't when
it lived inside the 84px top strip.

### Implementation Results (follow-up #9)

- `AgentActionBar.vue`: `popSheet` ref computed once per open —
  `matchMedia('(max-width:720px), (max-height:800px), (pointer:coarse)') ||
  navigator.maxTouchPoints > 0` — bound as `.pop-sheet` on the popover;
  inline `left` only when `!popSheet`. Sheet CSS moved from the media
  query to `.agent-target-pop.pop-sheet` (row min-height, font clamp,
  sub size, locate button included).
- `DeckHeader.vue` `.reveal-pill`: 40→52px base height, `min(tm,1.5)` →
  `min(tm,1.6)` caps, font 0.85→1rem base, padding 18→26px base —
  measured live at tm=2: 273×83px (was 205×60), 25.6px text.
- Verified live (Playwright, maxTouchPoints=10, 1280×900 — the desync
  case): popover now `pop-sheet`, 1120px wide centered at left:8 —
  previously it sat orphaned at left:0. Screenshot:
  `design-log/refs/picker-sheet-desync-fixed-*.png` and
  `header-reveal-bigger-pill-*.png`.
- Rebuilt `frontend/dist` so the backend-served panel picks up this
  plus today's earlier work (the stale Sep 26 bundle is why the panel
  still showed the old narrow picker and top-strip Show Header).
- Tests: focused 37/37 green; `npm run build` (vue-tsc + vite) clean.

## Follow-up #10 (2026-09-27): guarantee the idle session's picker highlight

### Problem (follow-up #10)

The picker's `waiting` row/chip highlight depends on the backend's
cwd→hook join (`_hook_state_by_cwd`): a hook entry whose `cwd` doesn't
match the window's (stale path, symlinked dir, agent `cd`'d after the
event) leaves `state: null`, so the picker shows the idle session with
**no** highlight on both desktop rows and mobile chips — exactly the cue
that must not silently fail.

### Design (follow-up #10)

In `list_agent_sessions`: when the cwd join misses AND there is exactly
one live host AND exactly one hook entry for the marker, pair them — one
window and one recorded session can't be ambiguous. Two+ hosts or two+
entries keep the strict cwd join (a wrong guess there would flag the
wrong terminal).

### Implementation Results (follow-up #10)

- `backend/routes/agent_sessions.py`: `list_agent_sessions` collects the
  marker's hook entries once; when `len(hosts) == 1 and
  len(hook_entries) == 1` the lone entry pairs with the lone host
  regardless of cwd (`hook = by_cwd.get(...) or lone_entry`).
- Tests: `test_list_sessions_single_host_pairs_on_cwd_mismatch` (mismatched
  cwd still yields `state: ready`) and
  `test_list_sessions_no_fallback_with_multiple_hosts` (two hosts stay
  strict-join) — `pytest tests/test_session_targeting.py` 15/15 green.
- Verified live end-to-end: restarted the Flask backend (DEBUG=False, no
  reloader), POSTed `ready` with `cwd: C:/totally/different/path` —
  `/api/agent-sessions` row reported `state: ready`, and the desktop
  picker row rendered `agent-target-row waiting`. Mobile chips read the
  same `state` field via `useAgentTargets`, so `.mac-session.waiting`
  highlights identically (verified earlier at 480×800).
- Note: the backend needed a manual restart for the route change; the
  panel's socket reconnected cleanly. In-memory agent state cleared —
  the real Claude session re-posts on its next hook event.
