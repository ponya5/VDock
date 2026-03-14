# Implementation Plan: App Cleanup and Improvements

## Overview

Incremental upgrades to VDock across four areas: Python backend cleanup, frontend debug
log removal, responsive UI, and new visual/interactive features. The app is currently
working — all tasks are additive or refactoring-based and must preserve existing behavior.

## Tasks

- [ ] 1. Python backend cleanup — dead code and logging
  - [ ] 1.1 Remove unused imports, dead code, and the `backend/nul` artifact file
    - Remove unused top-level imports in all modules under `backend/`
    - Delete `backend/nul`
    - Remove any code after unconditional `return` statements
    - Remove the redundant inner `from utils import setup_logger` inside `get_profiles()` in `routes/profiles.py`
    - _Requirements: 1.1, 1.2, 1.3, 1.5_

  - [ ] 1.2 Replace `print()` with `logger` in `FileManager`
    - Add `logger = logging.getLogger('vdock')` at module level in `utils/file_manager.py`
    - Replace every `print()` call in `save_json`, `load_json`, `delete_file`, `copy_file`, `list_files` with `logger.error()`
    - _Requirements: 1.4, 2.2, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_

  - [ ]* 1.3 Write property test for FileManager logging (Property 3)
    - **Property 3: FileManager logs errors via logger, not stdout**
    - **Validates: Requirements 2.2, 13.1–13.6**


- [ ] 2. Python backend cleanup — consolidate and refactor
  - [ ] 2.1 Fix `ActionExecutor` singleton in `routes/actions.py`
    - Import `action_executor` from `app.py` instead of instantiating a new `ActionExecutor()` per request
    - Return HTTP 503 with JSON error body if `action_executor is None`
    - _Requirements: 2.3, 11.1, 11.2_

  - [ ] 2.2 Add `@require_auth` to profile routes in `routes/profiles.py`
    - Apply `@require_auth` to `GET /api/profiles`, `GET /api/profiles/<id>`, `POST /api/profiles`, `PUT /api/profiles/<id>`
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

  - [ ]* 2.3 Write property test for profile route auth (Property 2)
    - **Property 2: Profile routes require auth when REQUIRE_AUTH is enabled**
    - **Validates: Requirements 12.1–12.4**

  - [ ] 2.4 Extract `metric_route` decorator in `routes/system_metrics.py`
    - Create `metric_route(fetch_fn)` decorator that wraps try/except/jsonify pattern
    - Refactor each route handler to use the decorator, keeping each handler body ≤ 10 lines
    - _Requirements: 2.1, 3.3_

  - [ ] 2.5 Split any route handler functions exceeding 40 lines
    - Audit all files under `backend/routes/` for handlers > 40 lines
    - Extract business logic into dedicated helper functions or service methods
    - _Requirements: 3.1, 3.2, 3.3_

- [ ] 3. Checkpoint — backend cleanup
  - Ensure all existing backend tests pass and the Flask server starts without errors. Ask the user if questions arise.


- [ ] 4. Frontend debug log cleanup
  - [ ] 4.1 Remove or downgrade `console.log` calls in stores and services
    - Remove all `console.log` calls from `stores/dashboard.ts`
    - Replace diagnostic logs with `console.warn` / `console.error` where appropriate in `services/appMonitor.ts` and `services/autoSceneSwitcher.ts`
    - _Requirements: 4.1, 4.6, 4.7_

  - [ ] 4.2 Remove or downgrade `console.log` calls in views and components
    - Remove all `console.log` calls from `views/DashboardView.vue`, `views/ProfilesView.vue`
    - Remove all `console.log` calls from `components/DeckButton.vue`, `components/DockedSidebar.vue`
    - _Requirements: 4.2, 4.3, 4.4, 4.5_

- [ ] 5. Global CSS foundations — tokens, breakpoints, fluid typography
  - [ ] 5.1 Add glassmorphism design tokens to `main.css`
    - Add `--glass-bg`, `--glass-border`, `--glass-blur`, `--glass-shadow`, `--glass-glow` to `.theme-dark` in `assets/styles/main.css`
    - _Requirements: 16.1_

  - [ ] 5.2 Add breakpoint tokens and CSS Grid template areas to `main.css`
    - Add `--bp-sm` through `--bp-2xl` custom properties to `:root`
    - Add `.dashboard-layout` grid template areas with sidebar/header/grid regions
    - Add `@media (max-width: 480px)` override that collapses to single-column layout
    - _Requirements: 20.1, 20.3_

  - [ ] 5.3 Update font sizes to use `clamp()` for fluid scaling
    - Update `body`, `.button-label`, and other base font-size declarations in `main.css` to use `clamp(min, preferred, max)`
    - _Requirements: 20.4_

  - [ ]* 5.4 Write property test for fluid font sizes (Property 8)
    - **Property 8: Font sizes use clamp() for fluid scaling**
    - **Validates: Requirements 20.4**


- [ ] 6. Gesture composable layer — `useGestures.ts` and `useParallax.ts`
  - [ ] 6.1 Implement `useGestures.ts` with all four composables
    - Create `frontend/src/composables/useGestures.ts`
    - Implement `useTouchSwipe` with 10px threshold, velocity calculation, passive listeners
    - Implement `usePinchZoom` with two-finger distance tracking, passive listeners
    - Implement `useLongPress` with 500ms timer, 5px movement cancellation, passive listeners
    - Implement `useEdgeSwipe` attached to `document`, 20px left-edge threshold, passive listeners
    - _Requirements: 21.1–21.9, 22.1–22.7, 23.1, 23.2, 26.2_

  - [ ]* 6.2 Write property test for swipe threshold (Property 9)
    - **Property 9: Swipe threshold — no navigation below 10px**
    - **Validates: Requirements 21.8**

  - [ ]* 6.3 Write property test for long-press cancellation (Property 11)
    - **Property 11: Long-press cancels on movement > 5px**
    - **Validates: Requirements 22.1, 22.2**

  - [ ] 6.4 Implement `useParallax.ts` composable
    - Create `frontend/src/composables/useParallax.ts`
    - Guard with `window.DeviceOrientationEvent` check; return early if unavailable
    - Apply EMA smoothing (α = 0.1) and clamp rotation to ±3 degrees
    - _Requirements: 24.4_

  - [ ]* 6.5 Write property test for parallax graceful degradation (Property 18)
    - **Property 18: Parallax graceful degradation when DeviceOrientationEvent is undefined**
    - **Validates: Requirements 24.4**

- [ ] 7. Haptics utility
  - [ ] 7.1 Create `frontend/src/utils/haptics.ts`
    - Implement `haptics.tap()`, `haptics.longPress()`, `haptics.success()`, `haptics.error()` using `navigator.vibrate?.()` optional chaining
    - _Requirements: 22.7, 26.2_

  - [ ]* 7.2 Write property test for haptics never throws (Property 12)
    - **Property 12: Haptics never throws without Vibration API**
    - **Validates: Requirements 22.7**


- [ ] 8. Checkpoint — composables and utilities
  - Ensure `useGestures.ts`, `useParallax.ts`, and `haptics.ts` compile without errors. Ask the user if questions arise.

- [ ] 9. Animated background system
  - [ ] 9.1 Add `backgroundPreference` to `stores/settings.ts`
    - Add `BackgroundPreference` type and `backgroundPreference` ref (default `'none'`)
    - Include in `loadSettings()` and `saveSettings()` with fallback to `'none'` on invalid value
    - _Requirements: 15.7, 15.8, 15.9_

  - [ ]* 9.2 Write property test for background preference round-trip (Property 5)
    - **Property 5: Background preference round-trip**
    - **Validates: Requirements 15.7, 15.8**

  - [ ] 9.3 Create `DarkVeil.vue` canvas component
    - Create `frontend/src/components/backgrounds/DarkVeil.vue`
    - Full-screen `<canvas>` with RAF loop: dark fill, noise grain, scanline pass, sine-wave warp
    - Pause/resume loop on `visibilitychange` (Page Visibility API)
    - _Requirements: 15.2, 26.3, 26.4_

  - [ ] 9.4 Create `FloatingLines.vue` canvas component
    - Create `frontend/src/components/backgrounds/FloatingLines.vue`
    - Animate 12 gradient lines using colors `#E945F5`, `#2F4BC0`, `#E945F5`
    - Add mouse parallax shift and quadratic bezier bend with time-varying control point
    - Pause/resume loop on `visibilitychange`
    - _Requirements: 15.3, 26.3, 26.4_

  - [ ] 9.5 Create `BackgroundRenderer.vue` and mount in `App.vue`
    - Create `frontend/src/components/BackgroundRenderer.vue`
    - Use `<Teleport to="body">` with `.background-layer` (`position: fixed; inset: 0; z-index: 0; pointer-events: none`)
    - Conditionally render `DarkVeil` or `FloatingLines` based on `settingsStore.backgroundPreference`
    - Wrap canvas init in try/catch; fall back to `'none'` on error
    - Mount `<BackgroundRenderer />` in `App.vue` before `<router-view />`
    - _Requirements: 15.1, 15.4, 15.5, 15.6, 15.9, 26.3, 26.4_

  - [ ] 9.6 Add background selector control to `SettingsView.vue` Appearance tab
    - Add selector offering "None", "Solid Color", "Dark Veil", "Floating Lines"
    - Bind to `settingsStore.backgroundPreference`
    - _Requirements: 15.1, 15.7_


- [ ] 10. DeckButton — glass styling, animations, ripple, and touch target
  - [ ] 10.1 Apply glassmorphism styling to `DeckButton.vue`
    - Apply `--glass-bg`, `--glass-border`, `--glass-blur`, `--glass-shadow` tokens to `.deck-button`
    - Add gradient overlay (lighter top, transparent bottom) for surface depth
    - Set `min-width: 60px; min-height: 60px` on `.deck-button`
    - _Requirements: 16.2, 16.6, 17.3_

  - [ ]* 10.2 Write property test for DeckButton minimum touch target (Property 4)
    - **Property 4: DeckButton minimum touch target is 60×60px**
    - **Validates: Requirements 17.3**

  - [ ] 10.3 Add press, hover, and ripple interactions to `DeckButton.vue`
    - Add `:active` CSS rule: `transform: scale(0.94)`, box-shadow collapse, `transition: 80ms ease`
    - Add `@media (hover: hover)` hover lift: `translateY(-2px)`, increased glow
    - Implement `triggerRipple(event: PointerEvent)` function and `.ripple` CSS keyframe
    - Add `.triggered` glow-pulse CSS keyframe; call `haptics.tap()` on press
    - _Requirements: 17.1, 17.2, 17.4, 24.1, 24.2, 24.3, 26.6_

  - [ ] 10.4 Add placeholder cell rendering to `DeckButton.vue`
    - When `button` prop is absent in non-edit mode, render dashed-border placeholder with `+` icon at low opacity
    - _Requirements: 17.5_

- [ ] 11. DockedSidebar — glass panel, accent line, overlay mode
  - [ ] 11.1 Apply glass panel styling and right-edge accent to `DockedSidebar.vue`
    - Replace solid background with `var(--glass-bg)` + `backdrop-filter: blur(var(--glass-blur))`
    - Add `border-right: 2px solid rgba(var(--color-primary-rgb), 0.6)`
    - Style `.sidebar-header h3` as uppercase, letter-spaced small label
    - Apply same glassmorphism treatment to sidebar button cards with a slightly different tint
    - _Requirements: 16.3, 16.4, 18.1, 18.2, 18.3, 18.4_

  - [ ] 11.2 Implement overlay mode for narrow viewports in `DockedSidebar.vue`
    - At `max-width: 480px`: `position: fixed; left: -100%; transition: left 200ms ease`
    - Add floating toggle button (`position: fixed; bottom: 1rem; left: 1rem; z-index: 200`)
    - Wire `useTouchSwipe` on sidebar for swipe-left-to-close
    - Wire `useEdgeSwipe` in `App.vue` / `DashboardView.vue` for swipe-right-to-open
    - _Requirements: 6.4, 18.5, 23.1, 23.2, 23.3_


- [ ] 12. DeckGrid — swipe navigation, pinch zoom, page indicator, parallax
  - [ ] 12.1 Wire swipe navigation in `DeckGrid.vue`
    - Wire `useTouchSwipe` with left/right/up/down callbacks for page and scene navigation
    - Implement real-time finger-follow during swipe (no transition), then snap with `200ms ease-out`
    - Apply `will-change: transform` during active swipe/drag
    - Implement momentum logic: advance if velocity > 0.3 px/ms or displacement > 50% page width
    - _Requirements: 21.1–21.9, 26.1, 26.5_

  - [ ]* 12.2 Write property test for swipe navigation direction (Property 13)
    - **Property 13: Swipe navigation direction correctness**
    - **Validates: Requirements 21.1, 21.2**

  - [ ]* 12.3 Write property test for scene navigation direction (Property 14)
    - **Property 14: Scene navigation direction correctness**
    - **Validates: Requirements 21.3, 21.4**

  - [ ]* 12.4 Write property test for momentum advance (Property 15)
    - **Property 15: Momentum advance on fast flick**
    - **Validates: Requirements 21.9**

  - [ ] 12.5 Implement `PageIndicator` component and wire to `DeckGrid.vue`
    - Create `PageIndicator.vue` with `currentPage`, `totalPages`, `swipeProgress` props
    - Compute active dot offset as `(currentPage + swipeProgress) * DOT_SPACING_PX`
    - Drive dot position via `transform: translateX()` for smooth continuous tracking
    - _Requirements: 21.7, 24.5_

  - [ ]* 12.6 Write property test for swipeProgress bounds (Property 19)
    - **Property 19: swipeProgress always in [0, 1]**
    - **Validates: Requirements 21.7, 24.5**

  - [ ] 12.7 Wire pinch-to-zoom in `DeckGrid.vue`
    - Wire `usePinchZoom` to clamp `buttonScale` to [0.6, 2.0] and persist via `settingsStore.saveSettings()`
    - Bind `--button-scale` CSS custom property on `.deck-grid` to `dashboardStore.buttonScale`
    - _Requirements: 21.6_

  - [ ]* 12.8 Write property test for pinch scale bounds (Property 10)
    - **Property 10: Pinch scale bounds [0.6, 2.0]**
    - **Validates: Requirements 21.6**

  - [ ] 12.9 Wire `useParallax` in `DeckGrid.vue`
    - Pass `gridRef` to `useParallax(gridRef)`; no additional wiring needed (composable self-contained)
    - _Requirements: 24.4_

  - [ ] 12.10 Apply DeckGrid CSS Grid auto-sizing for responsive square cells
    - Set `grid-template-columns: repeat(var(--grid-cols, 5), 1fr)` and `aspect-ratio: 1 / 1` on cells
    - _Requirements: 20.2_


- [ ] 13. Long-press drag-to-reorder and edit mode
  - [ ] 13.1 Wire long-press in `DeckButton.vue` and implement drag ghost in `DeckGrid.vue`
    - Wire `useLongPress` in `DeckButton.vue`; emit `long-press` with `cellIndex` and call `haptics.longPress()`
    - In `DeckGrid.vue`: on `long-press`, enter edit mode and create ghost element (`position: fixed; opacity: 0.7; pointer-events: none; will-change: transform`)
    - Track `touchmove` to move ghost and hit-test drop target via `document.elementFromPoint`
    - Highlight drop target cell with `.drop-target` outline
    - _Requirements: 22.1, 22.3, 22.4, 25.2, 25.6_

  - [ ]* 13.2 Write property test for drag-drop data swap (Property 17)
    - **Property 17: Drag-drop data swap correctness**
    - **Validates: Requirements 22.3, 22.4, 22.5**

  - [ ] 13.3 Implement drop and spring animation in `DeckGrid.vue`
    - On `touchend`: remove ghost, call `dashboardStore.swapButtons(src, target)`, call `haptics.success()`
    - Add `.spring-in` CSS keyframe animation to destination cell
    - _Requirements: 22.5_

  - [ ] 13.4 Implement edit mode visuals in `DeckGrid.vue`
    - Apply `.edit-mode` class to `.deck-grid` when edit mode is active
    - CSS: dim non-selected buttons (`filter: brightness(0.6)`), wiggle animation on all buttons, drag handle pseudo-element (`::after`)
    - _Requirements: 25.1, 25.6, 25.7_

  - [ ] 13.5 Implement edit mode exit triggers in `DashboardView.vue` / `DeckGrid.vue`
    - Exit on: tap outside buttons (`@click.self`), `Escape` keydown, "Done" button click, drag drop completion
    - Show "Done" button in dashboard header only when `editMode` is true
    - _Requirements: 25.3, 25.4, 25.5_

  - [ ] 13.6 Implement double-tap action execution on `DeckButton.vue`
    - Detect double-tap (two taps within ~300ms) and execute the button's assigned action
    - _Requirements: 22.6_

  - [ ] 13.7 Implement long-press on empty cell to open `ButtonEditor` in `DashboardView.vue`
    - When long-press fires on an empty cell, open `ButtonEditor` directly for that cell
    - _Requirements: 22.2_

  - [ ] 13.8 Implement long-press on `DockedSidebar` button for per-button edit mode
    - Wire `useLongPress` on sidebar buttons; enter same per-button edit mode as `DeckButton`
    - _Requirements: 23.4_

- [ ] 14. Checkpoint — gesture and interaction system
  - Ensure swipe, pinch, long-press, drag-to-reorder, and edit mode all work end-to-end. Ask the user if questions arise.


- [ ] 15. SettingsView — two-panel nav rail layout and bug fixes
  - [ ] 15.1 Redesign `SettingsView.vue` as two-panel nav rail layout
    - Restructure template: 220px fixed nav rail (left) + scrollable content panel (right)
    - Nav rail: icon + label rows, active state with left accent bar (`border-left: 3px solid var(--color-primary)`) and `var(--glass-bg)` highlight
    - Content panel: each section as a card with title, divider, and grouped form controls
    - _Requirements: 19.1, 19.2, 19.5_

  - [ ] 15.2 Add nav rail responsive breakpoints to `SettingsView.vue`
    - At `640px–899px`: collapse to 48px icon-only with hover tooltips
    - At `< 640px`: transform to horizontal scrollable icon bar at top
    - _Requirements: 7.1, 19.3, 19.4_

  - [ ] 15.3 Ensure all `SettingsView` form controls meet 44px touch target height
    - Set `min-height: 44px` on all `input`, `select`, and slider elements in `SettingsView.vue`
    - _Requirements: 7.2, 19.6_

  - [ ]* 15.4 Write property test for SettingsView form control touch targets (Property 6)
    - **Property 6: SettingsView form controls meet 44px touch target height**
    - **Validates: Requirements 19.6**

  - [ ] 15.5 Fix `availableScenes` computed property in `SettingsView.vue`
    - Change from `profile.pages.flatMap(p => p.scenes)` to `profile.scenes`
    - Return `[]` when `profile` is null or `profile.scenes` is empty
    - _Requirements: 10.1, 10.2_

  - [ ]* 15.6 Write property test for availableScenes never throws (Property 1)
    - **Property 1: availableScenes never throws**
    - **Validates: Requirements 10.1, 10.2**

  - [ ] 15.7 Update copyright year and app-integration responsive layout in `SettingsView.vue`
    - Change copyright text to "Daniel Shalom. All rights reserved 2026 ©"
    - Make app-integration list collapse "Scene" and "Actions" columns to stacked layout at `< 600px`
    - _Requirements: 5.1, 5.2, 7.3_

- [ ] 16. DashboardView — responsive layout, header, and `selectAction` fix
  - [ ] 16.1 Implement `selectAction` in `DashboardView.vue`
    - Replace TODO stub: if no `selectedPlaceholderCell`, show notification; otherwise call `openButtonEditor({ action: { type: actionType, config: {} } })`
    - _Requirements: 14.1, 14.2, 14.3_

  - [ ] 16.2 Apply responsive header and layout to `DashboardView.vue`
    - Add `flex-wrap: wrap` to `.dashboard-header` so controls wrap on narrow viewports
    - At `< 768px`: stack header controls vertically, reduce button label font sizes
    - At `< 768px`: display edit sidebar as bottom drawer instead of right-side panel
    - Apply `.dashboard-layout` grid template areas from task 5.2
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 6.6, 20.3_

  - [ ] 16.3 Apply frosted glass styling to `.dashboard-header`
    - Set `background: rgba(0,0,0,0.3); backdrop-filter: blur(12px); border-bottom: 1px solid var(--glass-border)`
    - _Requirements: 16.5_


- [ ] 17. Responsive layouts — ProfilesView and LoginView
  - [ ] 17.1 Make `ProfilesView.vue` responsive
    - At `< 600px`: single-column profile card layout
    - At `< 480px`: action buttons in 2×3 grid within each card
    - At `< 600px`: move import button from `position: fixed` to inline page flow
    - _Requirements: 8.1, 8.2, 8.3_

  - [ ] 17.2 Make `LoginView.vue` responsive
    - Set `max-width: 400px` and center card horizontally and vertically on all viewport sizes
    - At `< 480px`: card uses full viewport width minus `2 × var(--spacing-md)` horizontal padding
    - _Requirements: 9.1, 9.2_

- [ ] 18. No horizontal overflow validation
  - [ ] 18.1 Audit and fix any horizontal overflow sources
    - Verify `#app` has `overflow-x: hidden`
    - Verify sidebar is hidden at `< 480px` via grid template area collapse (task 5.2)
    - Verify grid uses `1fr` columns and never exceeds viewport width
    - _Requirements: 20.5_

  - [ ]* 18.2 Write property test for no horizontal overflow (Property 7)
    - **Property 7: No horizontal overflow at any supported viewport width**
    - **Validates: Requirements 20.5**

- [ ] 19. Sidebar open/close round-trip validation
  - [ ]* 19.1 Write property test for sidebar open/close round-trip (Property 16)
    - **Property 16: Sidebar open/close round-trip via edge swipe**
    - **Validates: Requirements 23.1, 23.2**

- [ ] 20. Final checkpoint — full integration
  - Ensure all tests pass, the app builds without errors, and all new features are wired end-to-end. Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at logical boundaries
- Property tests validate universal correctness; unit tests validate specific examples and edge cases
- All gesture listeners use `{ passive: true }` unless `preventDefault()` is explicitly required
