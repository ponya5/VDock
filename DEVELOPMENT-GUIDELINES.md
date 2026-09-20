# Development Guidelines — How I Want Apps Built

Distilled from the VDock project (46 design logs, dozens of review rounds).
These are not project-specific rules — they're how I want *any* application
developed. Feed this file to whatever AI/agent/IDE you're working with.

---

## 1. The user experience bar

### Touch-first, always assume small screens
- Every interactive element must be a real, generous touch target
  (**≥44–48px**). "It's hard to click, it's too small" is a release blocker,
  not a nitpick.
- Affordances must be *obvious*: an invisible hit-area or an unlabeled thin
  bar is not a control. If a user can't tell what tapping does, redesign it.
- Buttons/controls that appear to do nothing are **bugs**, even if the
  backend worked — silence reads as broken. Every action needs visible
  feedback (state change, toast, spinner, or the thing visibly opening).

### Fit the viewport — no screen-inside-a-screen
- Content must fit the target resolution without inner scroll panes.
  If it can't fit, **adapt the layout**: accordion panels, multi-column
  flow, collapsible sections — never just let it scroll inside a box.
- Use free space wisely: a lone card in one narrow column while two-thirds
  of the screen is empty is a defect. Fill the width.
- Verify against the *real* target resolution (e.g. 1024×600), not a dev
  monitor guess. Measure actual pixel positions of card bottoms/edges.

### Visual hierarchy must be visible
- Different levels of navigation must *look* different (e.g. primary pill
  tabs vs. quieter underline sub-tabs). Two identical rows stacked is a bug.
- Proportional scaling: UI tuned for a small panel should scale up on
  bigger windows — not sit miniature in a sea of empty space.
- Cohesive design language: dark/glassmorphic, consistent radii, accent
  color discipline. When mockups are supplied, extract their design tokens
  (fonts, colors, spacing) rather than inventing approximations.

### Free-first, zero-config defaults
- Features must work out of the box with **no API keys and no paid
  services**. If a widget needs a key, find a free path (RSS, public
  endpoints) or it doesn't ship.
- First-run experience matters: a default profile/scene with real starter
  content, not an empty grid.

### Polish details I notice
- Empty-state artifacts must be invisible (no ghost dots, stray borders).
- Overlays need mutual exclusion — a tutorial must never float over a
  screensaver; an alert must appear above everything.
- Reset affordances: wherever a user can change a value, offer a per-item
  reset to default.
- No native `confirm()`/`alert()` — styled in-app dialogs only.
- Discoverability: visual pickers beat text dropdowns; if users can't find
  a feature, it doesn't exist.

---

## 2. Engineering approach

### Root cause, not symptom
- Reproduce first, trace the real path, fix the cause. (Example: a widget
  "not fitting" was a center-point clamp on a 640px-wide element — the fix
  was measuring the real rendered box, not nudging the clamp number.)
- When something "does nothing," check the whole delivery chain — the
  screensaver editor button failed because a cross-window command had no
  listener in that context; the fix was mounting the editor in-place.

### One source of truth; consume existing systems
- If a scaling/theming system exists (`--touch-multiplier`, design tokens,
  defaults objects), **consume it** — don't invent a parallel mechanism.
- Export defaults from a single typed constant; never scatter magic values.

### State sync is a first-class feature
- Multi-window/broadcast sync must not flicker or revert: guard
  stale-loads, don't rebroadcast echoes, version messages.
- Persistence writes should be debounced/batched; a slider drag shouldn't
  fire 60 writes/second.

### Environment-aware behavior
- A PWA service worker serving stale bundles is a real bug source —
  auto-reload on new bundle, or users see "fixes" that never landed.
- Rate limits must protect the abuse surface (auth, writes, uploads) —
  never the app's own asset/image reads. Self-imposed quotas that break
  your own UI are defects.
- Logs: visible in-app, bounded size, exportable. Users must be able to
  diagnose without devtools.

### Security & release hygiene
- Never commit secrets; `.env` stays local, `.env.example` holds
  placeholders. Ignore local data, logs (including rotated `*.log.*`),
  backups, uploads.
- Before modifying a user's config file programmatically (e.g. installing
  a hook), write a timestamped backup first.
- Public-repo readiness: LICENSE, SECURITY.md, README assets actually
  committed (no broken image links), no personal paths or test data.

---

## 3. Working process

### Design log discipline
- One numbered entry per non-trivial change (`DL-NNN-slug.md`), written
  **before** coding: context, root cause, approaches considered, decision.
- The design sections are frozen once implementation starts; corrections
  go under "Implementation Results" — the log records what was believed at
  decision time, not a tidied-up version.

### Verify, don't assume
- Run the suite (tests + typecheck + build) after every change.
- Verify live in a real browser at the target resolution; measure element
  boxes, take screenshots, click through the actual flow.
- Check the narrow/small fallback too — a fix at one size must not break
  the other.
- Report real numbers ("card bottom at 581px of 600", "231/231 tests")
  not "should work now."

### Bugs are information
- Treat every reported bug as a signal of a missing invariant: silent
  no-op → missing feedback; flicker → missing sync guard; clipped widget →
  missing measured clamp. Fix the invariant, and the class of bug dies.

### Communication
- Concise, direct, honest. Disagree when something is a bad idea rather
  than politely implementing it.
- When reporting: what changed, where, what was verified, what still
  scrolls/doesn't. Tables and short lists over prose.
