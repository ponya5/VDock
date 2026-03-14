# Design Document: Glass Pill Scene Selector

## Overview

The Glass Pill Scene Selector replaces `SceneNavigation.vue` with a single pill-shaped radio toggle group rendered using VDock's glassmorphism token system. All scenes in the active profile are displayed as equal-width segments inside one pill container. An absolutely-positioned glider element slides beneath the active segment using a spring cubic-bezier transition. The component integrates with `dashboardStore` for state, `vibrate()` from `haptics.ts` for touch feedback, and follows the roving-tabindex ARIA radio-group pattern for full keyboard/screen-reader accessibility.

The existing `btn-17` wipe animation style is removed entirely. The new component is a drop-in replacement that preserves the same props and emits interface so parent components (`DashboardView.vue`) require no structural changes.

### Key Design Decisions

- **Single pill, not individual buttons**: All segments share one container element. This gives the glider a natural track to slide within and avoids per-button border/radius management.
- **CSS-only glider positioning**: The glider uses `transform: translateX(index * 100%)` driven by a computed inline style. No JS animation libraries are needed.
- **`vibrate(10)` instead of `haptics.tap()`**: The current `haptics.ts` exports only a `vibrate(pattern)` function. The design uses `vibrate(10)` (10 ms, matching the tap pattern in the project guidelines) until a named `tap()` wrapper is added to that utility.
- **Width recompute on scene count change**: A `watch` on `scenes.length` sets a `disableAnimation` flag for one tick so glider repositioning after add/remove is instant.
- **Glass tokens are dark-theme only**: `--glass-bg`, `--glass-border`, `--glass-blur` are defined only under `.theme-dark`. The component falls back to `var(--color-surface)` / `var(--color-border)` for other themes.

---

## Architecture

```
DashboardView.vue
  └── GlassPillSceneSelector.vue   (replaces SceneNavigation.vue)
        ├── pill container  [role="radiogroup"]
        │     ├── .glider              (absolutely positioned, animated)
        │     └── .segment × N        [role="radio"] per scene
        │           ├── FontAwesomeIcon (optional, hidden <480px)
        │           └── span.label     (truncated <768px)
        └── .edit-controls (v-if isEditMode)
              ├── .edit-btn × N       (per-segment edit icon)
              └── .add-btn            (append new scene)
```

The component is purely presentational with respect to profile data — it receives `scenes`, `currentSceneIndex`, and `isEditMode` as props and emits `scene-change`, `add-scene`, and `edit-scene`. All store mutations are triggered by the parent or by the component calling `dashboardStore.setScene()` directly (matching the existing pattern in `SceneNavigation.vue`).

---

## Components and Interfaces

### GlassPillSceneSelector.vue

**Props**

```typescript
interface Props {
  scenes: Scene[]           // ordered list from currentProfile.scenes
  currentSceneIndex: number // zero-based active index from dashboardStore
  isEditMode?: boolean      // default false
}
```

**Emits**

```typescript
interface Emits {
  'scene-change': [index: number]   // after setScene() is called
  'add-scene': []                   // user tapped Add button
  'edit-scene': [scene: Scene]      // user tapped edit icon on a segment
}
```

**Internal state**

```typescript
const disableAnimation = ref(false)  // true for one tick after scenes.length changes
const focusedIndex = ref(currentSceneIndex) // roving tabindex tracking
```

**Key computed values**

```typescript
// Width of each segment as a percentage
const segmentWidth = computed(() => `${100 / props.scenes.length}%`)

// Glider transform
const gliderStyle = computed(() => ({
  width: segmentWidth.value,
  transform: `translateX(${props.currentSceneIndex * 100}%)`,
  transition: disableAnimation.value
    ? 'none'
    : 'transform 0.5s cubic-bezier(0.37, 1.95, 0.66, 0.56)',
}))
```

**Scene switch handler**

```typescript
function selectScene(index: number) {
  if (index === props.currentSceneIndex) return
  vibrate(10)
  dashboardStore.setScene(index)
  emit('scene-change', index)
}
```

**Keyboard handler (roving tabindex)**

```typescript
function onKeyDown(event: KeyboardEvent, index: number) {
  const count = props.scenes.length
  if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
    event.preventDefault()
    focusedIndex.value = (index + 1) % count
  } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
    event.preventDefault()
    focusedIndex.value = (index - 1 + count) % count
  } else if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    selectScene(index)
  }
}
```

A `watch(focusedIndex, ...)` focuses the corresponding DOM element after the next tick.

**Scene count watcher**

```typescript
watch(() => props.scenes.length, () => {
  disableAnimation.value = true
  nextTick(() => { disableAnimation.value = false })
})
```

### Haptics integration

`vibrate` is imported from `@/utils/haptics`:

```typescript
import { vibrate } from '@/utils/haptics'
// usage: vibrate(10)  — 10ms tap
```

---

## Data Models

No new data models are introduced. The component consumes the existing `Scene` type from `@/types`:

```typescript
interface Scene {
  id: string
  name: string
  icon?: string        // FontAwesome icon identifier, optional
  color?: string
  pages: Page[]
  // ...other fields not used by this component
}
```

The component reads `dashboardStore.currentSceneIndex` and `dashboardStore.setScene()` directly, consistent with the existing `SceneNavigation.vue` approach.

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Segment count and labels match the scene list

*For any* array of scenes of length N ≥ 1, the rendered pill container should contain exactly N elements with `role="radio"`, and each element's text content should contain the corresponding scene's `name` in the same order.

Edge cases: N = 0 → no segments rendered (empty fragment); N = 1 → exactly one segment rendered.

**Validates: Requirements 1.1, 1.3, 1.4, 1.5**

### Property 2: Glider geometry matches the active index

*For any* scene list of length N and any valid active index `i` (0 ≤ i < N), the glider's computed `width` style should equal `${100 / N}%` and its `transform` style should equal `translateX(${i * 100}%)`.

**Validates: Requirements 2.1, 2.2**

### Property 3: Tapping a non-active segment triggers the full interaction

*For any* scene list of length N ≥ 2 and any index `i` where `i ≠ currentSceneIndex`, tapping segment `i` should: call `dashboardStore.setScene` exactly once with argument `i`, emit a `scene-change` event with value `i`, and call `vibrate(10)` exactly once.

**Validates: Requirements 3.1, 3.3, 3.4**

### Property 4: Tapping the active segment is a no-op

*For any* scene list and any active index `i`, tapping the segment at index `i` should result in zero calls to `dashboardStore.setScene`, zero `scene-change` emissions, and zero calls to `vibrate`.

**Validates: Requirements 3.2**

### Property 5: Active segment ARIA and tabindex state

*For any* scene list of length N and any active index `i`, exactly one segment should have `aria-checked="true"` and `tabindex="0"` — the segment at index `i` — and all other segments should have `aria-checked="false"` and `tabindex="-1"`.

**Validates: Requirements 7.2, 7.5**

### Property 6: Keyboard navigation wraps at boundaries

*For any* scene list of length N ≥ 2 and any focused index `i`, pressing `ArrowRight` or `ArrowDown` should move focus to `(i + 1) % N`, and pressing `ArrowLeft` or `ArrowUp` should move focus to `(i - 1 + N) % N`. Pressing `Enter` or `Space` on any segment `i` where `i ≠ currentSceneIndex` should call `dashboardStore.setScene(i)`.

**Validates: Requirements 7.3, 7.4**

### Property 7: Edit controls visibility matches isEditMode

*For any* scene list of length N and any boolean value of `isEditMode`: when `isEditMode` is `false`, zero add buttons and zero edit buttons should be present in the DOM; when `isEditMode` is `true`, exactly one add button and exactly N edit buttons should be present.

**Validates: Requirements 6.1, 6.2, 6.5**

### Property 8: Edit-scene event carries the correct Scene object

*For any* scene list of length N ≥ 1 and any index `i`, tapping the edit button for segment `i` should emit an `edit-scene` event whose payload is strictly equal (by reference or deep equality) to `scenes[i]`.

**Validates: Requirements 6.4**

### Property 9: Icon rendered if and only if scene.icon is set

*For any* scene list, a `FontAwesomeIcon` element should be rendered inside a segment if and only if that segment's scene has a non-empty `icon` property.

**Validates: Requirements 1.6**

---

## Error Handling

| Condition | Behaviour |
|---|---|
| `scenes` prop is empty (length 0) | Component renders nothing (empty fragment). No glider or segments are mounted. |
| `currentSceneIndex` out of range | Glider clamps to `Math.max(0, Math.min(index, scenes.length - 1))` via a computed guard. No crash. |
| `vibrate()` unavailable (non-touch device) | `haptics.ts` already guards with `typeof window.navigator.vibrate === 'function'`. No action needed in the component. |
| `scene.icon` is undefined or empty string | `v-if="scene.icon"` prevents `FontAwesomeIcon` from rendering. No console error. |
| Single scene | Glider is permanently at index 0. Segment is rendered but `selectScene` is a no-op (index always equals `currentSceneIndex`). |

---

## Testing Strategy

### Unit Tests (Vitest)

Focus on specific examples, edge cases, and integration points:

- Renders nothing when `scenes` is empty
- Renders correct number of segments for a given scene list
- Active segment has `aria-checked="true"`, others have `"false"`
- Active segment has `tabindex="0"`, others have `"-1"`
- Clicking a non-active segment emits `scene-change` with correct index
- Clicking the active segment does not emit `scene-change`
- Edit buttons are hidden when `isEditMode=false`, shown when `true`
- Add button emits `add-scene`; edit button emits `edit-scene` with correct Scene object
- `Enter` / `Space` keydown on a segment activates it
- Single-scene profile: segment renders, no interaction side-effects

### Property-Based Tests (Vitest + fast-check)

Each property test runs a minimum of 100 iterations. Tests are tagged with the format:
`Feature: glass-pill-scene-selector, Property N: <property text>`

**Property 1 — Segment count and labels match the scene list**
Generate a random array of 1–20 Scene objects with random names. Mount the component. Assert segment count equals `scenes.length` and each segment's text contains the corresponding name in order. Also verify N=0 renders nothing.
`// Feature: glass-pill-scene-selector, Property 1: segment count and labels match the scene list`

**Property 2 — Glider geometry matches the active index**
Generate a random scene list (length 1–20) and a random valid active index. Assert glider `width` style equals `${100 / N}%` and `transform` equals `translateX(${i * 100}%)`.
`// Feature: glass-pill-scene-selector, Property 2: glider geometry matches the active index`

**Property 3 — Tapping a non-active segment triggers the full interaction**
Generate a random scene list (length ≥ 2) and a random non-active index. Simulate a click. Assert `setScene` called once with that index, `scene-change` emitted with that index, and `vibrate` called once with `10`.
`// Feature: glass-pill-scene-selector, Property 3: tapping a non-active segment triggers the full interaction`

**Property 4 — Tapping the active segment is a no-op**
Generate a random scene list and active index. Simulate a click on the active segment. Assert `setScene` not called, no `scene-change` emitted, `vibrate` not called.
`// Feature: glass-pill-scene-selector, Property 4: tapping the active segment is a no-op`

**Property 5 — Active segment ARIA and tabindex state**
Generate a random scene list and active index. Assert exactly one segment has `aria-checked="true"` and `tabindex="0"` at the active index; all others have `"false"` and `"-1"`.
`// Feature: glass-pill-scene-selector, Property 5: active segment ARIA and tabindex state`

**Property 6 — Keyboard navigation wraps at boundaries**
Generate a random scene list (length ≥ 2) and a random focused index. Simulate ArrowRight → assert focus at `(i+1)%N`. Simulate ArrowLeft → assert focus at `(i-1+N)%N`. Simulate Enter/Space on a non-active segment → assert `setScene` called.
`// Feature: glass-pill-scene-selector, Property 6: keyboard navigation wraps at boundaries`

**Property 7 — Edit controls visibility matches isEditMode**
Generate a random scene list and a random boolean `isEditMode`. Assert: when `false`, zero add/edit buttons; when `true`, exactly 1 add button and N edit buttons.
`// Feature: glass-pill-scene-selector, Property 7: edit controls visibility matches isEditMode`

**Property 8 — Edit-scene event carries the correct Scene object**
Generate a random scene list (length ≥ 1) and a random index. Mount with `isEditMode=true`. Simulate a click on edit button at index `i`. Assert emitted `edit-scene` payload deep-equals `scenes[i]`.
`// Feature: glass-pill-scene-selector, Property 8: edit-scene event carries the correct Scene object`

**Property 9 — Icon rendered if and only if scene.icon is set**
Generate a random scene list where each scene randomly has or lacks an `icon`. Assert a `FontAwesomeIcon` wrapper is present in segment `i` iff `scenes[i].icon` is truthy.
`// Feature: glass-pill-scene-selector, Property 9: icon rendered if and only if scene.icon is set`

### Property-Based Testing Library

Use **fast-check** (already a project dependency per `vdock-project.md`). Configure each `fc.assert` with `{ numRuns: 100 }` minimum.
