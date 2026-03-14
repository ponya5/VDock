# Implementation Plan: Glass Pill Scene Selector

## Overview

Replace `SceneNavigation.vue` with `GlassPillSceneSelector.vue` — a single glassmorphism pill container with an animated spring glider, roving-tabindex ARIA radio group, haptic feedback, edit-mode controls, and responsive behaviour. Update `DashboardView.vue` to use the new component. Cover all 9 correctness properties with fast-check property-based tests.

## Tasks

- [ ] 1. Create `GlassPillSceneSelector.vue` — structure and props
  - Create `frontend/src/components/GlassPillSceneSelector.vue`
  - Define props (`scenes`, `currentSceneIndex`, `isEditMode`) and emits (`scene-change`, `add-scene`, `edit-scene`) matching the interface in design.md
  - Add internal state: `disableAnimation` ref and `focusedIndex` ref
  - Render the pill container as `role="radiogroup"` with `aria-label="Scene selector"`
  - Render one `role="radio"` segment per scene with `aria-checked`, roving `tabindex`, `FontAwesomeIcon` (v-if scene.icon), and label span
  - Render `.glider` absolutely positioned inside the pill
  - Render `.edit-controls` block (add button + per-segment edit buttons) gated by `v-if="isEditMode"`
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 6.1, 6.2, 7.1, 7.2, 7.5_

- [ ] 2. Implement glider logic and scene switching
  - [ ] 2.1 Add `segmentWidth` and `gliderStyle` computed properties
    - `segmentWidth = 100 / scenes.length + '%'`
    - `gliderStyle` sets `width`, `transform: translateX(index * 100%)`, and conditional transition (spring vs `none`)
    - Clamp `currentSceneIndex` to `[0, scenes.length - 1]` to guard out-of-range prop
    - _Requirements: 2.1, 2.2, 2.5_

  - [ ] 2.2 Implement `selectScene(index)` handler
    - Guard: return early if `index === currentSceneIndex`
    - Call `vibrate(10)` from `@/utils/haptics`
    - Call `dashboardStore.setScene(index)`
    - Emit `scene-change` with index
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ] 2.3 Add scene-count watcher for instant glider reposition
    - `watch(() => props.scenes.length, () => { disableAnimation.value = true; nextTick(() => { disableAnimation.value = false }) })`
    - _Requirements: 2.5_

  - [ ]* 2.4 Write property test — Property 2: glider geometry matches the active index
    - **Property 2: Glider geometry matches the active index**
    - **Validates: Requirements 2.1, 2.2**
    - Generate random scene list (length 1–20) and valid active index; assert glider `width` equals `${100/N}%` and `transform` equals `translateX(${i*100}%)`

  - [ ]* 2.5 Write property test — Property 3: tapping a non-active segment triggers the full interaction
    - **Property 3: Tapping a non-active segment triggers the full interaction**
    - **Validates: Requirements 3.1, 3.3, 3.4**
    - Generate scene list (length ≥ 2) and non-active index; assert `setScene` called once with that index, `scene-change` emitted once, `vibrate` called once with `10`

  - [ ]* 2.6 Write property test — Property 4: tapping the active segment is a no-op
    - **Property 4: Tapping the active segment is a no-op**
    - **Validates: Requirements 3.2**
    - Generate scene list and active index; click active segment; assert `setScene` not called, no `scene-change` emitted, `vibrate` not called

- [ ] 3. Implement keyboard navigation (roving tabindex)
  - [ ] 3.1 Add `onKeyDown(event, index)` handler on each segment
    - `ArrowRight` / `ArrowDown` → `focusedIndex = (index + 1) % N`
    - `ArrowLeft` / `ArrowUp` → `focusedIndex = (index - 1 + N) % N`
    - `Enter` / `Space` → call `selectScene(index)`
    - Call `event.preventDefault()` for all handled keys
    - _Requirements: 7.3, 7.4_

  - [ ] 3.2 Add `watch(focusedIndex, ...)` to focus the corresponding DOM element after `nextTick`
    - Use a template ref array on segments; focus `segmentRefs[focusedIndex.value]`
    - _Requirements: 7.4, 7.5_

  - [ ]* 3.3 Write property test — Property 5: active segment ARIA and tabindex state
    - **Property 5: Active segment ARIA and tabindex state**
    - **Validates: Requirements 7.2, 7.5**
    - Generate scene list and active index; assert exactly one segment has `aria-checked="true"` and `tabindex="0"` at the active index; all others have `"false"` and `"-1"`

  - [ ]* 3.4 Write property test — Property 6: keyboard navigation wraps at boundaries
    - **Property 6: Keyboard navigation wraps at boundaries**
    - **Validates: Requirements 7.3, 7.4**
    - Generate scene list (length ≥ 2) and focused index; simulate ArrowRight → assert `(i+1)%N`; simulate ArrowLeft → assert `(i-1+N)%N`; simulate Enter on non-active → assert `setScene` called

- [ ] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Apply glassmorphism styles and responsive behaviour
  - [ ] 5.1 Style the pill container with glass tokens
    - `background: var(--glass-bg)`, `backdrop-filter: blur(var(--glass-blur))`, `border: 1px solid var(--glass-border)`, `border-radius: 1rem`
    - Fallback to `var(--color-surface)` / `var(--color-border)` for non-dark themes
    - `overflow-x: auto; scrollbar-width: none` on the pill container
    - _Requirements: 1.2, 4.3, 4.4_

  - [ ] 5.2 Style the glider
    - `background: linear-gradient(135deg, rgba(52,152,219,0.35), rgba(52,152,219,0.7))`
    - `box-shadow: 0 0 18px rgba(52,152,219,0.45), inset 0 0 10px rgba(255,255,255,0.15)`
    - `border-radius: 1rem; z-index: 1; position: absolute`
    - _Requirements: 2.3, 2.4_

  - [ ] 5.3 Style segments for touch compliance and responsive behaviour
    - `min-height: 44px; min-width: 80px`
    - `font-size: clamp(0.65rem, 0.8vw + 0.4rem, 0.85rem)`
    - `:active` → `transform: scale(0.96); transition: transform 80ms ease`
    - `@media (max-width: 768px)` → label `max-width: 72px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap`
    - `@media (max-width: 480px)` → `v-show` or CSS to hide icons
    - `will-change: transform` on the glider
    - _Requirements: 3.5, 4.1, 4.2, 5.1, 5.2, 5.3, 5.4_

  - [ ] 5.4 Style edit controls
    - Add button and edit icon buttons: `min-width: 44px; min-height: 44px`
    - Hover state: border-color and color shift to `var(--color-primary)`
    - _Requirements: 6.6_

  - [ ]* 5.5 Write property test — Property 1: segment count and labels match the scene list
    - **Property 1: Segment count and labels match the scene list**
    - **Validates: Requirements 1.1, 1.3, 1.4, 1.5**
    - Generate random array of 1–20 scenes; assert rendered `role="radio"` count equals `scenes.length` and each segment text contains the corresponding `name`; also verify N=0 renders nothing

  - [ ]* 5.6 Write property test — Property 9: icon rendered if and only if scene.icon is set
    - **Property 9: Icon rendered if and only if scene.icon is set**
    - **Validates: Requirements 1.6**
    - Generate scene list with randomly present/absent `icon`; assert `FontAwesomeIcon` wrapper present in segment `i` iff `scenes[i].icon` is truthy

- [ ] 6. Implement edit-mode controls behaviour
  - [ ] 6.1 Wire add-scene button to emit `add-scene`
    - _Requirements: 6.3_

  - [ ] 6.2 Wire per-segment edit buttons to emit `edit-scene` with `scenes[i]`
    - _Requirements: 6.4_

  - [ ]* 6.3 Write property test — Property 7: edit controls visibility matches isEditMode
    - **Property 7: Edit controls visibility matches isEditMode**
    - **Validates: Requirements 6.1, 6.2, 6.5**
    - Generate scene list and random boolean `isEditMode`; assert zero add/edit buttons when `false`; assert exactly 1 add button and N edit buttons when `true`

  - [ ]* 6.4 Write property test — Property 8: edit-scene event carries the correct Scene object
    - **Property 8: Edit-scene event carries the correct Scene object**
    - **Validates: Requirements 6.4**
    - Generate scene list (length ≥ 1) and random index; mount with `isEditMode=true`; click edit button at index `i`; assert emitted `edit-scene` payload deep-equals `scenes[i]`

- [ ] 7. Update `DashboardView.vue` to use `GlassPillSceneSelector`
  - Replace the `SceneNavigation` import with `GlassPillSceneSelector`
  - Update the template tag from `<SceneNavigation` to `<GlassPillSceneSelector`
  - Verify prop and emit bindings match (`scenes`, `currentSceneIndex`, `isEditMode`, `scene-change`, `add-scene`, `edit-scene`)
  - Note: existing `SceneNavigation.vue` is kept in place; only the import and usage in `DashboardView.vue` changes
  - _Requirements: all (integration)_

- [ ] 8. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- `vibrate(10)` is used directly from `@/utils/haptics` — `haptics.tap()` does not exist yet
- Property tests live in `frontend/src/components/__tests__/GlassPillSceneSelector.spec.ts` using Vitest + fast-check with `{ numRuns: 100 }`
- Each property test must be tagged: `// Feature: glass-pill-scene-selector, Property N: <text>`
- `disableAnimation` ensures the glider snaps instantly when scene count changes (no spring overshoot on add/remove)
- Glass tokens are dark-theme only; the component falls back to `--color-surface` / `--color-border` for other themes
