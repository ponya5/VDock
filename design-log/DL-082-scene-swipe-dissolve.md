# DL-082 — Horizontal swipe scene switching + directional dissolve

## Problem

Scene switching has no horizontal gesture: `DeckGrid`'s `useSwipe` maps
left/right to **page** flips and up/down to scene changes — and it only
listens on the grid element, so the mobile agent console (which replaces
the grid on agent scenes) has no swipe at all. Scenes live on a
horizontal rail in both chromes; left/right is the spatially-mapped
direction for them.

Separately, a scene switch is an instant cut: the rail segment snaps its
active state and the whole scene teleports. The user asked for a
directional dissolve: the outgoing scene button dissolves in the swipe
direction while the gesture is still tracking, and the scene content
dissolves out/in as a directional wave on commit.

## Design

### Gesture: left/right = scenes (desktop + mobile)

A single `useSwipe` on `.main-content` in `DashboardView` becomes the
one gesture source for the content area — it covers the deck grid, the
agent action bar, and the mobile agent console. Mapping:

- LEFT → next scene, RIGHT → previous scene (iOS paging convention:
  drag left advances).
- UP/DOWN keep their existing mapping to next/previous scene.
- Page flips lose their swipe gesture (page steppers in the chrome
  remain); horizontal is now owned by scenes.

Guards applied at swipe-start (the composable gains an event-passing
`onSwipeStart(e)` and an `onSwipeCancel` hook — both backward
compatible):

- Edit mode → ignored (a horizontal drag there is a button move).
- <2 scenes → ignored.
- Start target inside `input/textarea/select/[contenteditable]` or an
  open `.agent-target-popover` → ignored.
- Start inside an element that can actually scroll on the swipe axis
  (overflow-x/y auto|scroll AND scrollable overflow) → that axis is
  ignored, so swiping a scrollable region scrolls instead of switching.

### Live "scene button fades according to the swipe"

A tiny reactive singleton `services/sceneSwipe.ts`
(`{ dragging, dir, progress, justSwiped }`) is written by the
DashboardView swipe handler during `onSwipe` and read by both scene
rails (`GlassPillSceneSelector`, `MobileDeckChrome`).

While `dragging`, the ACTIVE segment's content dissolves with the
finger: a directional `mask-image` gradient (`mask-size: 250%`) sweeps
`mask-position` proportional to progress, plus a trailing opacity drop —
capped mid-way so the button never fully vanishes before commit.
`transition: none` during drag keeps it 1:1; release restores the
transition so a cancelled swipe animates back.

### Commit: directional dissolve

Direction is derived from the index delta (shortest path, so
wrap-around and rail clicks get the same treatment):

- `next` (index forward / swipe-left): dissolve wave travels **L→R** —
  the outgoing scene's leading (left) edge dissolves first.
- `prev`: wave travels **R→L**.

Scene content — `.main-content` wraps the per-scene content in a keyed
`.scene-pane` (`:key="currentScene.id"`) inside
`<Transition :name="scene-wipe-next|prev">` (simultaneous mode — a true
cross-dissolve, no blank gap; the leaving pane goes `position:absolute`
above the entering one). Each pane animates `mask-position` (soft wipe),
`opacity`, and a subtle ±28px `translateX` drift. 0.42s `--ease-io`.

The keyed pane remounts the subtree per scene — which conveniently
suppresses DeckGrid's own staggered page transition on scene switches
(it watches `page.id`; a fresh mount never fires it), while page flips
inside a scene keep it.

Scene buttons — on index change the rails mark `outIdx`/`inIdx` + dir
for ~0.5s. The outgoing segment runs a two-phase sweep keyframe:
dissolve out along the wave (starting from the live drag mask position
via `--sweep-from`), briefly transparent, then dissolve back in as the
inactive button — so the label never snaps. The incoming segment runs
the reveal half only, arriving with the wave. The glider keeps its
existing slide, which is already directional.

### Reduced motion

`prefers-reduced-motion`: live drag tracking drops the mask (keeps a
plain opacity fade), the pane transition collapses to an opacity
crossfade, and the segment sweep animation is disabled.

## Implementation Results

- `useGestures.ts`: `onSwipeStart` now receives the `PointerEvent` (for
  start-target gating); new optional `onSwipeCancel` fires on
  below-threshold release and — via a split `pointercancel` handler — on
  OS-canceled gestures, which previously could commit a crossed-threshold
  drag. Existing callers untouched.
- `services/sceneSwipe.ts` (new): reactive `{ dragging, dir, progress,
  justSwiped }` singleton bridging the gesture source and the two rails.
  `progress` intentionally survives release so the commit sweep resumes
  from the finger's position.
- `DashboardView.vue`: single `useSwipe` on `.main-content` (threshold
  50px). Gating in `onSwipeStart`: edit mode, <2 scenes, form fields,
  `.agent-target-popover`, `.onscreen-keypad`, and — computed per axis at
  start — targets inside an actually-scrollable ancestor keep scrolling
  instead of switching. Left/right/up/down all map to scene
  next/previous; the grid-level `useSwipe` and its four emits were
  removed from `DeckGrid.vue`.
- Scene pane: `currentPage` content wrapped in `.scene-pane` keyed on
  `currentScene.id` inside `<Transition :name="sceneTransitionName">`;
  direction derives from the shortest index delta in `setScene`.
  Cross-dissolve = travelling soft mask edge (`mask-image` 250% gradient,
  `mask-position` sweep) + opacity + ±28px drift, 0.42s `--ease-io`;
  leaving pane goes `absolute`/z-2 over the incoming one. Important fix
  during implementation: leave transitions need an explicit
  `*-leave-from` mask-position or the mask lands at its end state with
  no travel.
- Segment dissolve (both rails): live inline mask+opacity while
  `sceneSwipe.dragging` (55% of the travel capped, so the button never
  fully vanishes pre-commit); committed switches run
  `seg-wipe-out` (dissolve out → re-form in place) + `seg-wipe-in`
  keyframes starting from `--sweep-from`; cancelled swipes play
  `seg-wipe-back` so the wipe reverses instead of snapping.
  `prefers-reduced-motion`: drag keeps an opacity fade (mask dropped),
  pane falls back to a plain crossfade, sweeps disabled.
- Verified live in Playwright:
  - Desktop 1280×800: 35px drag → active segment `mask-position 61.5%`,
    `opacity .65`, `transition:none` (1:1). Commit → two panes coexist,
    `scene-wipe-next` leave/enter, mask sweeping 100→0%; old segment
    `seg-sweep-out`, new `is-active seg-sweep-in`. Swipe-right →
    `scene-wipe-prev`, back to Media. 30px cancel → `seg-sweep-back`
    with `--sweep-from: 67%`, no scene change.
  - Mobile 800×480: same live dissolve on `.mc-seg`, committed wipe;
    swipe directly on `.mobile-agent-console` switches scenes — the
    console had no swipe surface before. Portrait phones still show the
    rotate gate (gestures unreachable under it, as designed).
  - Screenshot: `design-log/refs/scene-wipe-mid-transition-*.png` —
    the dissolve seam visible mid-sweep.
- Deviation: drag-tracking touches only the segment + live mask; the
  scene pane itself does not pre-dissolve during the drag — the commit
  transition plays the full 0.42s wipe. Keeps the leaving pane's mask
  math stateless.
- `vue-tsc` clean; 287/287 vitest green (`matchMedia` jsdom stub needed
  `?.` guards — same pattern the rail already used); `npm run build`
  clean, dist rebuilt for the panel.
- Behavior change worth noting: horizontal swipe no longer flips pages
  (was `swipe-left/right` → `nextPage/previousPage` on the grid).
  Pages keep the ‹ › steppers in both chromes; vertical swipe still
  switches scenes as before.
