# DL-065: Mobile agent console — talk to Claude from a phone

**Date:** 2026-09-24
**Depends on:** DL-063 (mobile chrome), DL-064 (agent state, state actions,
layout-independent typing)

## Background

A phone that scans VDock's QR code gets the same deck as the desktop, with
the slim scene rail from DL-063 on top. On an agent scene (Claude Code,
Cursor, Devin) that deck is a landscape-only button grid plus the agent
action bar, and portrait shows a "Rotate your device" gate.

## Problem

Communicating with an agent from a phone needs three things the deck does
not offer:

1. **Say something.** There is no way to write a prompt on the phone.
   Typing into the PC's terminal is exactly what VDock does, but only with
   canned text.
2. **See what the agent said.** Away from the PC, nothing shows the agent's
   reply, so the state pill alone ("Ready") gives no context.
3. **Portrait.** Writing needs the on-screen keyboard, which wants portrait,
   and portrait is gated.

## Design

### Surface: `MobileAgentConsole`

On a phone (`isMobileViewport`), when the current scene resolves to an app
profile with `state_actions`, the console replaces the bar and grid in
`.main-content`. The scene rail stays, so switching scenes is unchanged. The
console is portrait-first; the rotate gate stands down for it, as it does
for the screensaver.

The layout is one column filling the viewport, top to bottom:

1. **State card:** a large coloured dot, the agent name, the state label
   (Ready for your prompt / Working… / Needs your permission / Status
   unavailable / Not running), and the hook message plus project.
2. **Conversation:** the last prompt ("You") and the agent's last reply,
   as selectable, scrollable plain text. While the agent works: "Working…"
   plus the hook message. When empty: guidance text.
3. **State actions:** the same entries as the desktop bar, in a two-column
   grid of 56 px buttons. The first one is primary.
4. **Shortcuts:** the scene's own buttons (Open Claude, Review, Fix
   Tests…) as a horizontally scrolling chip row, executed exactly as the
   deck executes them.
5. **Composer:** an auto-growing textarea (16 px text, so iOS doesn't zoom)
   and a Send button. It sends through the profile's `prompt_command`
   (Claude: `cc_prompt`; Devin: `devin_prompt`), so the text is typed into
   the live session and submitted. Newlines, Hebrew and emoji work (DL-064
   follow-ups). The composer is disabled in the permission state ("Answer
   the permission request first"), because typing into a permission dialog
   would pick an option. It is hidden for agents without a
   `prompt_command` (Cursor has no safe way to type into its chat).
   Ctrl/Cmd+Enter also sends. The draft survives failures and clears on
   success.

`index.html` gains `interactive-widget=resizes-content`, so the on-screen
keyboard shrinks the layout instead of covering the composer.

### Shared logic: `useAgentSession`

`AgentActionBar`'s profile, state, actions and run logic move into
`composables/useAgentSession.ts`, which both the bar and the console use.
Registering the alert overlay's "bar is visible" flag also moves into a
helper (`trackAgentSurfaceVisibility`), so the console suppresses the alert
overlay the same way the bar does.

### Conversation data: hooks carry the text

- Claude `UserPromptSubmit` → `prompt` from the payload.
- Claude `Stop` → `reply`, taken from `last_assistant_message` when present,
  otherwise from the last assistant text entry in the tail (512 KB) of
  `transcript_path`. The hook runs locally as the user, so the backend never
  reads files named by a request.
- Cursor `beforeSubmitPrompt` → `prompt`; `afterAgentResponse` → `reply`
  (`text`).
- `agent_state.record` accepts `prompt` and `reply` and carries them over
  between events of the same session: a new prompt clears the old reply,
  and a later event without text keeps what it had. Caps are 2 000 chars
  for a prompt and 6 000 for a reply. The route passes them through, and
  the text is rendered as text, never as HTML.

### Profile field

`AppProfile.prompt_command: Optional[str]`, serialised, and
`AppProfileDto.prompt_command`.

## Trade-offs

- **Plain text, not markdown:** replies are readable as `pre-wrap` text
  with no new dependency and no HTML injection risk. Markdown rendering can
  come later.
- **Last turn only, not full history:** it matches what the hook reliably
  provides and keeps the socket payload small.
- **No Cursor composer:** typing into Cursor's chat needs a focus chord
  that varies by version, and it can't be tested safely from inside Cursor.

## Verification Criteria

- Unit: the hook extracts `prompt` and `reply` (both the payload field and
  the transcript fallback), `record` carries them over and clears them
  correctly with caps, profiles serialise `prompt_command`, and the
  composable-driven bar still passes the existing tests.
- Browser, phone emulation (390×844 portrait, touch): the console renders
  on the Claude scene with no rotate gate; the Media scene still shows the
  grid and the gate. The state card and actions follow live state, the
  conversation shows the hook's prompt and reply, a chip runs its action,
  and Send types into the live Claude session. In the permission state the
  composer is disabled. No console errors.

## Implementation Results

### What shipped

| Piece | Where |
|---|---|
| Console surface | `frontend/src/components/MobileAgentConsole.vue` |
| Shared session logic | `frontend/src/composables/useAgentSession.ts`; `AgentActionBar.vue` now uses it |
| Wiring | `DashboardView.vue`: `showsMobileAgentConsole`, rotate gate `portrait-allowed` |
| Rotate gate prop | `RotateToLandscape.vue`: `screensaverActive` renamed to `portraitAllowed` |
| Hook conversation | `scripts/vdock_agent_hook.py`: `conversation_fields`, `last_assistant_reply` |
| State carry-over | `integrations/agent_state.py`: `_conversation`, caps; `routes/agent_events.py` passes `prompt`/`reply` |
| Profile field | `AppProfile.prompt_command` (Claude `cc_prompt`, Devin `devin_prompt`) + DTO |
| Viewport | `index.html`: `interactive-widget=resizes-content` |

### Deviations from the design

- **Compact actions.** The first build used a two-column grid of 56 px
  buttons. On a 390×664 viewport five actions took three rows and left the
  conversation about 190 px. Actions are now one row of icon-over-label
  buttons. The primary action gets a full-width row only while it is urgent
  (Interrupt while working, Approve for a permission request); while the
  agent is ready, the composer is the primary control.
- **Short screens.** A `max-height: 480px` block slims every row, so the
  composer stays on screen in landscape. At 664×390 the composer ends at
  384 px and the conversation keeps 120 px.
- **Screen wake.** Not in the design. During the live test the 120 s
  screensaver covered the console while waiting for a reply. Now a change
  in the agent's state, prompt or reply wakes it while the console shows.
  Tool-use churn in the same state doesn't count.
- **Reading position.** The conversation opens and scrolls so the newest
  message's first line is in view. A long reply reads from its start
  instead of opening at its end.
- **On-screen keypad.** VDock's global keypad opened on top of the phone's
  own keyboard when the composer was focused. Inputs marked
  `data-native-keyboard` are now skipped.
- **Focus bug found live (DL-064 area).** The first live Send failed with
  "Windows would not bring it forward": the Claude desktop app was in the
  foreground and refused `AttachThreadInput` (Access is denied). The error
  was raised outside the `try` in `_try_set_foreground`, so `focus_hwnd`
  gave up before its Alt-tap and minimise/restore fallbacks ran. The attach
  moved into `_attach_input`, which treats a refusal as "not attached".
  With that fix the retry succeeded. The composer kept the draft and showed
  the error toast, as designed.
- **No Cursor composer**, as designed. The Cursor console shows state,
  actions and shortcuts only.

### Verification

- **Unit, backend (851 passed):**
  - prompt capture;
  - `last_assistant_message` preferred over the transcript;
  - transcript tail parse (the last text entry wins; tool-use entries and a
    cut first line are skipped);
  - a missing transcript;
  - long-reply tail with `…`;
  - Cursor prompt/reply;
  - carry-over, and a new prompt clearing the reply;
  - caps;
  - `prompt_command` per profile, which must be a text-typing command;
  - two `focus_hwnd` escalation tests with a refused attach.
- **Unit, frontend (250 passed):** `mobile-agent-console.test.ts`, 9 cases:
  - plain-text rendering (HTML stays text);
  - shortcuts without page navigation;
  - send-and-clear;
  - keep the draft on failure;
  - permission lock;
  - the native-keyboard opt-out;
  - no composer without `prompt_command`;
  - the not-running state;
  - action and shortcut dispatch.
  - Also `property8` (font sizes) passes.
- **Browser, iPhone 13 emulation (touch, 390×664 portrait / 664×390
  landscape):**
  - The console renders on Claude Code with no rotate gate; Media still
    shows the gate.
  - The ready, working and permission states render correctly with
    simulated events.
  - With `attention: true` the alert overlay stays hidden behind the
    console.
  - A reply event dismisses the screensaver.
- **Live end to end:**
  - Open Claude was tapped on the phone, and the real `SessionStart` hook
    reported ready.
  - The prompt `Reply with exactly this line and nothing else: VDock mobile
    console OK ✓ שלום` was sent from the composer. The state went Status
    unavailable → Working… → Ready.
  - The real hook returned the reply `VDock mobile console OK ✓ שלום` about
    9.5 s after Send, and the draft cleared.
- **Console errors:** only headless geolocation ("Weather fetch failed")
  and two transient Vite reloads during mid-edit states. All edited modules
  compile (HTTP 200).

### Open point

`useMobileViewport` counts any touch device whose smaller side is 700 px or
less as a phone. A touch 7" panel at 1024×600 therefore gets the mobile
chrome (DL-060–063) and, on agent scenes, this console instead of the grid.
The user's panel wasn't running during the test, so its classification is
unconfirmed.

## Follow-up: console/action bar not appearing on a real phone (2026-09-25)

### Problem

On the user's own device, a Claude Code scene showed the mobile chrome and
the plain shortcut grid (Open Claude, Review, Commit…) with **no** agent
action row at all — neither the desktop-style `AgentActionBar` nor this
console's state/actions/composer. The same scene's `AgentActionBar` renders
correctly on desktop.

### Root cause

`showsMobileAgentConsole` (`DashboardView.vue`) and `AgentActionBar`'s own
`visibleActions` both key off `sceneAppProfile()`, which reads
`profilesById` — populated once by `loadProfileMaps()`
(`services/appDetection.ts`). Nothing calls that function until whichever
agent surface mounts first pulls it in via `useAgentSession`'s `onMounted`:

- **Desktop:** `AgentActionBar` always mounts (it's the unconditional
  `v-else-if` branch), so it triggers the load itself and self-heals once
  the request resolves.
- **Mobile:** `showsMobileAgentConsole` starts `false` (empty profile map),
  so the same `AgentActionBar` + grid branch mounts first and *should*
  self-heal identically — except `appScanningEnabled` defaults to `false`
  (DL-057), so `MobileDeckChrome`'s scanning watcher never calls
  `startAppDetection()` either. The only path left is `loadProfileMaps()`'s
  own `try/catch`, which swallowed a failed request with the comment "retry
  on next poll tick" — a poll tick that never happens with scanning off. A
  single failed request (very plausible for a phone's first request right
  after joining over LAN/QR) permanently starves both surfaces of
  `state_actions`, leaving only the plain grid with no way to recover.

### Fix

- `loadProfileMaps()` now retries the `/app-profiles` fetch up to 3 times
  (1s/3s/8s backoff) before giving up, and concurrent callers share one
  in-flight request instead of firing duplicate fetches.
- `DashboardView.vue` calls `loadProfileMaps()` unconditionally in
  `onMounted`, instead of waiting for `AgentActionBar`/`MobileAgentConsole`
  to mount and request it themselves — removes the mount-order dependency
  entirely so `showsMobileAgentConsole` resolves correctly regardless of
  the app-scanning setting or which surface would otherwise have loaded it
  first.
- No change to grid sizing: `DeckGrid`'s existing host-`ResizeObserver` +
  compact-cell logic (DL-057/059) already shrinks buttons to fit whatever
  height remains once the console/action bar claims its space, down to its
  existing 36px floor, so the "make buttons smaller to fit" concern from
  the same report is resolved by the console/bar reliably appearing at all
  rather than by a separate sizing change.

### Verification

- Frontend suite: 59 files / 250 tests green, `vue-tsc --noEmit` clean.
- Not yet re-verified live on the reporting user's physical device (no
  access to it from this session) — flagged for the user to confirm on
  their phone.

## Follow-up 2: drop the composer entirely — actions/shortcuts only (2026-09-25)

### Problem

Live on a phone, the console's original design didn't hold up:

1. The empty-state "conversation" card (`.mac-conversation` with no
   messages yet) rendered as a huge, mostly-empty box — "Type below — your
   message is typed into Claude Code on your PC and sent" — dominating the
   screen above the actual controls.
2. The user didn't want free-text prompting on mobile at all: a phone's
   on-screen keyboard eating the screen for something typed one-handed is a
   worse experience than just tapping a purpose-built action, and every
   state-driven action (Submit, Continue, Interrupt, …) plus the scene's own
   shortcuts (Open Claude, Review, Commit, Explain, Write Tests, Fix Tests,
   …) already covers what a typed follow-up would have said.

This directly reverses this entry's original problem statement #1 ("Say
something — there is no way to write a prompt on the phone"): once live,
that turned out to be solving a problem the user didn't actually have on a
phone, where the state actions and per-scene shortcut buttons are enough.

### Fix

- Removed the entire `<form class="mac-composer">` (textarea + send button)
  and every script/style piece that only existed to support it:
  `hasComposer`, `composerPlaceholder`, `isComposerLocked`, `canSend`,
  `resizeComposer`, `submitDraft`, the `draft`/`isSending`/`composerRef`
  refs, the `sendPrompt` destructure from `useAgentSession`, and the
  `.mac-composer`/`.mac-composer-input`/`.mac-send` styles (including their
  landscape media-query overrides).
- `emptyStateText` no longer branches on whether a composer exists — it
  always reads "Use the buttons below to drive {agent} on your PC."
- The empty-state card (`.mac-conversation--empty`) switched from `flex: 1`
  (grow to fill all remaining space) to `flex: 0 0 auto` and a row layout
  for its icon + text, so it claims only the room one line of text needs.
  A conversation with real messages is unaffected — it still keeps
  `flex: 1` to grow and scroll normally.
- Free-text prompting (`sendPrompt`, `prompt_command`) remains fully intact
  for desktop's `AgentActionBar` — this change is mobile-only.

### Trade-offs

- A phone can no longer send an arbitrary custom message to the agent —
  only what a state action or scene shortcut already expresses. This is
  the explicit, intentional trade the user asked for; genuinely novel
  prompts still need the desktop.

### Verification

- `mobile-agent-console.test.ts`: replaced the four composer-specific tests
  (typing/sending, failure handling, permission-lock, native-keyboard
  attribute) with `never renders a text composer — actions and shortcuts
  are the only controls`, and simplified the permission-state test to just
  check the conversation card.
- Full frontend suite: 59 files / 250 tests green; `vue-tsc --noEmit`
  clean.
- `frontend/dist/` rebuilt so the change reaches the backend-served path
  too (see DL-069).

## Follow-up 3: drop the empty-state card too; shortcuts as a wrapping grid (2026-09-25)

### Problem

Follow-up 2 shrank the empty-state card but still rendered it — live, its
"Use the buttons below to drive Claude Code on your PC" line was itself
exactly the kind of filler the user wanted gone entirely, still eating a
full-width card above the buttons it was describing. Separately, the
shortcut row (Open Claude, Review, Commit, claude.ai, Explain, Write
Tests, Fix Tests, …) was a horizontal-scrolling pill strip: on a narrower
phone, several of those buttons scrolled off-screen with no visible
indication more existed, and the pills themselves were sized for a label,
not for an easy thumb target.

### Fix

- The `.mac-conversation` card is now `v-if="hasConversation"` — it does
  not render *at all* when there is no prompt, reply, working, or
  permission state to show, rather than rendering a smaller "nothing to
  say" version of itself. Removed `emptyStateIcon`/`emptyStateText` and the
  `.mac-empty` styles entirely, since nothing references them anymore.
- `.mac-shortcuts` changed from a horizontal-scrolling flex row
  (`overflow-x: auto`) to a wrapping CSS grid
  (`grid-template-columns: repeat(auto-fit, minmax(84px, 1fr))`): every
  shortcut is visible on screen at once on any phone width, reflowing into
  more rows instead of ever scrolling off-screen, and each tile grew to a
  68px-tall icon-over-label button (up from a 44px-tall pill) for an
  easier tap target. The landscape/short-viewport media query switches
  tiles to a row layout (icon beside label, 110px minimum column) to keep
  them compact without shrinking back to hard-to-hit pills.

### Verification

- `mobile-agent-console.test.ts`: updated the "agent not running" test to
  assert `.mac-conversation` doesn't exist at all (previously asserted its
  text content); added `renders no conversation card at all when there is
  nothing to show` for the ready-but-idle case.
- Full frontend suite: 59 files / 251 tests green; `vue-tsc --noEmit`
  clean.
- `frontend/dist/` rebuilt again so this reaches the LAN-served path too
  (see DL-069).
