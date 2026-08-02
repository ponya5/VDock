# VDock Touch Redesign — Design Spec
**Date:** 2026-08-02  
**Target device:** 7-inch 1024×600 touch screen (Electron app)

---

## 1. Problem Summary

Seven distinct UX issues are reported on the 7" touch device:

1. Scene navigation duplicated in header and footer
2. Full Screen + Hide buttons are redundant clutter in the header
3. Header buttons are too small for comfortable touch use
4. Accidental pinch gesture resizes buttons during tap
5. Touch drag-and-drop from Edit sidebar to grid is non-functional
6. Tapping Settings highlights the button but does not navigate
7. Weather/Calendar sidebar takes persistent screen space; user wants a screensaver mode instead

---

## 2. Header — Swipe-Down Reveal

### Default state
- The header is **not visible** on launch; it takes zero vertical space.
- A **16 px transparent trigger zone** sits fixed at the top of the screen with a small drag handle pill (44 × 5 px, `rgba(255,255,255,0.22)`).
- The existing `header-reveal-trigger` element in `DeckHeader.vue` covers this role; its swipe detection is extended (see §2.2).

### Reveal gesture
- A **swipe-down** anywhere in the trigger zone slides the header in from the top.
- Spring/ease-out animation, ~280 ms.
- `settingsStore.showHeader` transitions to `true` to drive existing conditional rendering.

### Header dimensions (when visible)
| Element | Size |
|---|---|
| Header bar height | 90 px min |
| Avatar | 56 × 56 px |
| Scene pill height | 56 px min |
| Icon button diameter | 64 px |
| Icon button font size | 26 px |

### Header content (left → right)
1. **Avatar** (56 px circle) — profile image or user icon
2. **Scene pills** — one pill per scene; active pill highlighted; `+` add-scene button (56 px circle); edit pencils shown in edit mode
3. **Three icon-only circular buttons** (right): Profiles · Edit · Settings

Full Screen and Hide buttons are **removed entirely** from the header. They will not be replaced with new controls — these actions are no longer needed as discrete buttons.

### Auto-hide
- A **5-second idle timer** starts the moment the header becomes visible.
- A thin 4 px progress bar directly below the header shows the countdown (draining left-to-right in blue).
- Any tap on a header button **resets** the 5-second timer.
- When the timer expires, the header slides back up (same spring animation).
- `settingsStore.showHeader` returns to `false`.

### Manual dismiss
- **Swipe up** on the visible header → immediately slides back up.
- The `useSwipe` composable already wired to the trigger ref is extended to the header element itself for the upward swipe.

---

## 3. Footer Cleanup

- **Remove** the `scene-pills` block from `DeckFooter.vue` (right side). Scene selection is now exclusively handled by `GlassPillSceneSelector` in the header.
- The footer retains: **page dots** (left) and **edit-mode controls** (center, grid size + Add/Delete Page + Save).
- Footer minimum height increases to **44 px** so page dots are easily tappable.

---

## 4. Pinch Gesture — Disable

- In `DeckGrid.vue`, the `usePinch` composable is imported and active.
- **Remove** the `usePinch` call entirely. The pinch handler that mutates button size is the source of accidental resizing on multi-touch.
- If pinch-to-zoom is desired in a future release it can be re-added with a deliberate guard (≥ 200 ms dwell before activating).

---

## 5. Touch Drag-and-Drop (Edit Sidebar → Grid)

`useTouchActionDrag.ts` is implemented but not wired to the action list in `EditSidebar.vue`.

### What needs to connect

1. **EditSidebar**: call `bindTouchDragSource(el, { type: 'action', data: action })` on each action list item element after mount (via `v-for` + template ref or directive).
2. **DeckGrid / DashboardView**: listen for the `vdock-touch-drop` custom event on `document`. On receipt, resolve the drop target placeholder and call the existing `handleActionDrop` or `handlePlaceholderClick` path with the dragged action payload.
3. Ghost element styling is already handled by `useTouchActionDrag` (clones the source element at 0.8 opacity, fixed-positioned, follows finger).

### Long-press threshold
- Default 400 ms (already in composable). No change needed.

---

## 6. Settings Navigation Fix

`DeckHeader.vue` emits `navigateSettings` → `DashboardView.vue` calls `router.push('/settings')`.

### Root cause investigation required
The likely candidates are:
- The `animate-tap` touch handler consuming the event before the click fires.
- A pointer-events CSS issue on the button or a parent overlay.
- A Vue router navigation guard silently blocking the push.

### Fix approach
- Add a `console.log` diagnostic to confirm whether the button `click` event fires at all.
- If the emit fires but router.push silently fails, check for a navigation guard that rejects without logging.
- Ensure the button has `touch-action: manipulation` CSS so the browser does not delay the click 300 ms.

---

## 7. Screensaver

### Remove WidgetColumn
- Delete the `<WidgetColumn>` component from `DashboardView.vue`.
- The `showWidgets` ref and the `WidgetColumn` import can be removed.
- The `WidgetColumn.vue` file itself is kept (not deleted) in case it is needed later.

### New ScreenSaver.vue component

**Trigger:** a configurable idle timer (see §7.1) running on the main dashboard. If no touch/click/key event is detected for the configured duration, the screensaver overlay appears.

**Layout (Option A — approved):**

```
┌──────────────────────────────────────────┐
│                                          │
│            14:32                         │  ← huge clock, center
│          SATURDAY, AUG 2                 │  ← date subtitle
│                                          │
│  ┌──────────────┐  ┌────────────────┐   │
│  │ ⛅  24°C      │  │ Standup 10:00  │   │  ← slim bottom bar
│  │  Tel Aviv     │  │  next event    │   │
│  └──────────────┘  └────────────────┘   │
└──────────────────────────────────────────┘
```

- Full-screen dark overlay (`position: fixed; inset: 0; z-index: 500`).
- Background: `#050510` with a subtle blue radial glow centered behind the clock.
- Clock: `font-size: clamp(4rem, 12vw, 7rem)`, `font-weight: 200`, letter-spacing.
- Date: small, `rgba(255,255,255,0.4)`, uppercase.
- Bottom bar: two glass-card panels side by side — weather (icon + temp + city) and next calendar event (name + time). Pulled from existing `useWeather` composable and a static events list for now.
- **Dismiss:** any touch/click anywhere on the screensaver hides it and resets the idle timer.
- The clock slowly drifts position (±20 px, 30-second cycle) to avoid OLED burn-in.

### 7.1 Idle Timeout Setting

- Add `screensaverTimeout` (number, seconds) to `settingsStore` with default `120` (2 minutes).
- Expose a range slider in the Settings page: **30 s – 10 min** in steps of 30 s, labelled "Screensaver delay".
- Value `0` means screensaver is disabled.

---

## 8. Out of Scope

- Full Screen API / OS-level window controls (unchanged)
- Calendar integration with a real calendar service (events remain static placeholder data)
- Screensaver background animations beyond the slow clock drift
- Any changes to button editor, profiles page, or scene editor

---

## 9. Files Changed (Expected)

| File | Change |
|---|---|
| `DeckHeader.vue` | Remove Full Screen + Hide buttons; resize avatar/pills/buttons; add 5s auto-hide timer + progress bar; swipe-up dismiss |
| `DeckFooter.vue` | Remove scene-pills block; increase footer min-height |
| `DeckGrid.vue` | Remove `usePinch` call |
| `EditSidebar.vue` | Wire `bindTouchDragSource` to each action item |
| `DashboardView.vue` | Listen for `vdock-touch-drop`; remove `<WidgetColumn>`; add `<ScreenSaver>` with idle timer |
| `WidgetColumn.vue` | No change (kept, just unused) |
| `ScreenSaver.vue` | **New file** — fullscreen clock+weather+event overlay |
| `stores/settings.ts` | Add `screensaverTimeout` ref, persist, expose |
| Settings page | Add screensaver delay slider |
