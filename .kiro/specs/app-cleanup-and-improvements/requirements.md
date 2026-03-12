# Requirements Document

## Introduction

This document covers a set of improvements to the VDock application — a stream deck-like tool
with a Python/Flask backend and a Vue.js/Electron frontend. The improvements span four areas:
Python codebase cleanup, a footer copyright year update, responsive UI for main views, and
a review and fix of core functionalities.

## Glossary

- **VDock**: The full application, consisting of a Flask backend and a Vue.js/Electron frontend.
- **Backend**: The Python/Flask server located in `backend/`.
- **Frontend**: The Vue.js application located in `frontend/src/`.
- **Dashboard**: The main view (`DashboardView.vue`) where users interact with button grids.
- **Profile**: A named configuration containing scenes, pages, and buttons.
- **Scene**: A named group of pages within a profile.
- **Page**: A grid of buttons within a scene.
- **DeckButton**: A single interactive button rendered in the grid.
- **DockedSidebar**: The persistent left sidebar with pinned buttons.
- **ActionExecutor**: The Python class that routes and executes button actions.
- **FileManager**: The Python utility class for JSON file I/O.
- **SettingsView**: The settings page (`SettingsView.vue`).
- **ProfilesView**: The profiles management page (`ProfilesView.vue`).
- **LoginView**: The authentication page (`LoginView.vue`).
- **Dead Code**: Code that is unreachable, unused, or has no effect on program behavior.
- **Debug Log**: A `console.log` or Python `print` statement used during development.

---

## Requirements

### Requirement 1: Python Codebase Cleanup — Remove Unused and Dead Code

**User Story:** As a developer, I want unused imports, dead code paths, and redundant code
removed from the Python backend, so that the codebase is easier to read and maintain.

#### Acceptance Criteria

1. THE Backend SHALL have no unused top-level imports in any module under `backend/`.
2. THE Backend SHALL have no unreachable code paths (e.g., code after unconditional `return` statements).
3. WHEN a module-level logger is already defined, THE Backend SHALL NOT redefine the logger
   inside a local scope (e.g., the redundant `from utils import setup_logger` inside
   `get_profiles()` in `routes/profiles.py` SHALL be removed).
4. THE Backend SHALL have no `print()` statements used for logging; all logging SHALL use
   the `logging` module.
5. THE `backend/nul` file SHALL be deleted as it is an artifact with no purpose.

### Requirement 2: Python Codebase Cleanup — Consolidate Duplicate Code

**User Story:** As a developer, I want near-duplicate code patterns consolidated into shared
helpers, so that changes only need to be made in one place.

#### Acceptance Criteria

1. THE Backend SHALL consolidate the repeated try/except/jsonify error-response pattern
   across route handlers in `routes/system_metrics.py` into a shared helper or decorator,
   so that each route handler body is no longer than ~10 lines.
2. THE `FileManager` class SHALL use the module-level `logger` (via `logging.getLogger`)
   instead of `print()` for error reporting in `save_json`, `load_json`, `delete_file`,
   `copy_file`, and `list_files`.
3. THE `ActionExecutor` SHALL NOT instantiate a new `ActionExecutor` inside
   `routes/actions.py`; THE Backend SHALL reuse the single `action_executor` instance
   created in `app.py`.

### Requirement 3: Python Codebase Cleanup — Split Long Functions

**User Story:** As a developer, I want functions longer than ~40 lines split into smaller,
focused helpers, so that each function has a single clear responsibility.

#### Acceptance Criteria

1. THE `migrateProfileToScenes` function in `backend/` (if any equivalent exists) SHALL
   be no longer than 40 lines; logic for creating a default scene and logic for migrating
   existing pages SHALL each be extracted into separate helper functions.
2. THE `get_all_metrics` method in `SystemMetrics` is already a thin aggregator and SHALL
   remain as-is; individual metric methods that exceed 40 lines SHALL be split.
3. WHEN a route handler function in any file under `backend/routes/` exceeds 40 lines,
   THE Backend SHALL extract the business logic into a dedicated helper function or
   service method, keeping the route handler as a thin dispatcher.

### Requirement 4: Frontend Debug Log Cleanup

**User Story:** As a developer, I want debug `console.log` statements removed from
production frontend code, so that the browser console is not polluted during normal use.

#### Acceptance Criteria

1. THE Frontend SHALL have no `console.log` calls in `stores/dashboard.ts`.
2. THE Frontend SHALL have no `console.log` calls in `views/DashboardView.vue`.
3. THE Frontend SHALL have no `console.log` calls in `views/ProfilesView.vue`.
4. THE Frontend SHALL have no `console.log` calls in `components/DeckButton.vue`.
5. THE Frontend SHALL have no `console.log` calls in `components/DockedSidebar.vue`.
6. THE Frontend SHALL have no `console.log` calls in `services/appMonitor.ts` and
   `services/autoSceneSwitcher.ts`.
7. WHERE a `console.log` statement provides information useful for diagnosing errors,
   THE Frontend SHALL replace it with `console.error` or `console.warn` as appropriate.


### Requirement 5: Footer Copyright Year Update

**User Story:** As a user, I want the copyright year in the About section to reflect the
current year, so that the application appears up to date.

#### Acceptance Criteria

1. THE SettingsView SHALL display the copyright year as 2026 in the About tab footer text.
2. THE SettingsView SHALL display the copyright notice in the format:
   "Daniel Shalom. All rights reserved 2026 ©".

### Requirement 6: Responsive UI — Dashboard View

**User Story:** As a user, I want the Dashboard to adapt its layout to different screen
sizes and resolutions, so that the interface is usable on small laptops, tablets, and
large monitors without horizontal scrolling or clipped content.

#### Acceptance Criteria

1. WHEN the viewport width is less than 768px, THE Dashboard SHALL stack the header
   controls vertically and reduce button label font sizes so no content overflows
   horizontally.
2. WHEN the viewport width is between 768px and 1365px, THE Dashboard SHALL display
   the header in a single row with abbreviated button labels where needed.
3. WHEN the viewport width is 1920px or greater, THE Dashboard SHALL scale the deck
   grid and header proportionally using the existing 4K CSS variables.
4. WHEN the DockedSidebar is enabled on a viewport narrower than 480px, THE Dashboard
   SHALL hide the DockedSidebar to preserve grid space, and THE Dashboard SHALL provide
   a toggle button to show it as an overlay.
5. WHEN the edit sidebar is open on a viewport narrower than 768px, THE Dashboard SHALL
   display the edit sidebar as a bottom drawer instead of a right-side panel.
6. THE Dashboard header SHALL use `flex-wrap: wrap` so that header controls wrap to a
   second line rather than overflow on narrow viewports.

### Requirement 7: Responsive UI — Settings View

**User Story:** As a user, I want the Settings page to be fully usable on small screens,
so that I can configure the application from any device.

#### Acceptance Criteria

1. WHEN the viewport width is less than 768px, THE SettingsView SHALL display the tab
   buttons as a horizontally scrollable row or a 2-column grid instead of a single row
   that overflows.
2. WHEN the viewport width is less than 768px, THE SettingsView SHALL display form
   controls at full width with adequate vertical spacing for touch interaction.
3. THE SettingsView app-integration list SHALL use a responsive layout that collapses
   the "Scene" and "Actions" columns into a stacked layout on viewports narrower than
   600px.


### Requirement 8: Responsive UI — Profiles View

**User Story:** As a user, I want the Profiles page to adapt to small screens, so that
I can manage profiles on any device.

#### Acceptance Criteria

1. WHEN the viewport width is less than 600px, THE ProfilesView SHALL display profile
   cards in a single-column layout instead of the auto-fill grid.
2. THE ProfilesView profile card action buttons SHALL remain visible and tappable on
   small screens; WHEN the viewport is narrower than 480px, THE ProfilesView SHALL
   display action buttons in a 2×3 grid layout within each card.
3. THE ProfilesView import button SHALL be repositioned from `position: fixed` to an
   inline element within the page flow on viewports narrower than 600px to avoid
   overlapping content.

### Requirement 9: Responsive UI — Login View

**User Story:** As a user, I want the Login page to be properly centered and sized on
all screen sizes, so that it is easy to use on mobile and desktop.

#### Acceptance Criteria

1. THE LoginView login card SHALL have a maximum width of 400px and SHALL be centered
   horizontally and vertically on all viewport sizes.
2. WHEN the viewport width is less than 480px, THE LoginView login card SHALL use full
   viewport width minus 2×`--spacing-md` of horizontal padding.

### Requirement 10: Fix — SettingsView availableScenes Computed Property

**User Story:** As a user, I want the App Integration scene selector to list the correct
scenes from my profile, so that I can assign scenes to applications.

#### Acceptance Criteria

1. THE SettingsView `availableScenes` computed property SHALL read scenes from
   `profile.scenes` (the top-level scenes array on the Profile object), NOT from
   `profile.pages[n].scenes` which does not exist in the data model.
2. WHEN a profile has no scenes, THE SettingsView scene selector SHALL display an empty
   list without throwing a runtime error.

### Requirement 11: Fix — ActionExecutor Singleton in Route Handler

**User Story:** As a developer, I want the action executor to be a shared singleton,
so that a new instance is not created on every button press, avoiding unnecessary overhead.

#### Acceptance Criteria

1. THE `execute_action` route in `routes/actions.py` SHALL import and use the
   `action_executor` instance from `app.py` rather than instantiating a new
   `ActionExecutor()` on every request.
2. IF the shared instance is unavailable, THEN THE Backend SHALL return a 503 response
   with a descriptive error message.

### Requirement 12: Fix — Profile GET Routes Missing Auth Decorator

**User Story:** As a developer, I want profile read and write routes to consistently
enforce authentication, so that unauthenticated users cannot access profile data.

#### Acceptance Criteria

1. THE `GET /api/profiles` route SHALL apply the `@require_auth` decorator when
   `Config.REQUIRE_AUTH` is `True`.
2. THE `GET /api/profiles/<profile_id>` route SHALL apply the `@require_auth` decorator
   when `Config.REQUIRE_AUTH` is `True`.
3. THE `POST /api/profiles` route SHALL apply the `@require_auth` decorator when
   `Config.REQUIRE_AUTH` is `True`.
4. THE `PUT /api/profiles/<profile_id>` route SHALL apply the `@require_auth` decorator
   when `Config.REQUIRE_AUTH` is `True`.


### Requirement 13: Fix — FileManager Uses Proper Logging

**User Story:** As a developer, I want file operation errors to appear in the application
log file rather than only on stdout, so that errors are captured in `vdock.log`.

#### Acceptance Criteria

1. THE `FileManager` class SHALL obtain a logger via `logging.getLogger('vdock')` at
   module level.
2. WHEN `save_json` encounters an exception, THE FileManager SHALL log the error using
   the module logger instead of `print()`.
3. WHEN `load_json` encounters an exception, THE FileManager SHALL log the error using
   the module logger instead of `print()`.
4. WHEN `delete_file` encounters an exception, THE FileManager SHALL log the error using
   the module logger instead of `print()`.
5. WHEN `copy_file` encounters an exception, THE FileManager SHALL log the error using
   the module logger instead of `print()`.
6. WHEN `list_files` encounters an exception, THE FileManager SHALL log the error using
   the module logger instead of `print()`.

### Requirement 14: Fix — DashboardView TODO Stub for selectAction

**User Story:** As a user, I want clicking an action in the edit sidebar to open the
button editor pre-configured with that action type, so that I can quickly create buttons
from the sidebar.

#### Acceptance Criteria

1. WHEN a user clicks an action item in the edit sidebar, THE Dashboard SHALL open the
   ButtonEditor modal pre-populated with the selected action type.
2. WHEN no placeholder cell is selected and the user clicks an action item, THE Dashboard
   SHALL prompt the user to click a grid cell first before opening the editor.
3. THE `selectAction` function in `DashboardView.vue` SHALL NOT contain a `// TODO`
   comment indicating unimplemented logic.

### Requirement 15: Animated Background System

**User Story:** As a user, I want to choose an animated background style for the application,
so that I can personalise the visual experience to my preference.

#### Acceptance Criteria

1. THE SettingsView SHALL provide a background selector control in the Appearance tab
   offering four options: "None", "Solid Color", "Dark Veil", and "Floating Lines".
2. WHEN the user selects "Dark Veil", THE BackgroundRenderer SHALL render a full-screen
   Vue canvas component that applies a dark overlay with subtle noise, scanline, and warp
   effects behind all application content.
3. WHEN the user selects "Floating Lines", THE BackgroundRenderer SHALL render a full-screen
   Vue canvas component that animates gradient-colored floating lines using the colors
   #E945F5, #2F4BC0, and #E945F5, with interactive mouse parallax and bend effects.
4. WHEN the user selects "Solid Color", THE BackgroundRenderer SHALL apply the existing
   solid background color defined in the application theme without rendering a canvas layer.
5. WHEN the user selects "None", THE BackgroundRenderer SHALL remove any active canvas
   background and render no background effect.
6. THE BackgroundRenderer SHALL be mounted at the root layout level so that it renders
   behind all views, sidebars, and modals without obscuring or intercepting pointer events
   on any interactive element.
7. WHEN a background option is selected, THE SettingsView SHALL persist the selection to
   the application configuration file so that the chosen background is restored on the
   next application launch.
8. WHEN the application launches, THE BackgroundRenderer SHALL read the saved background
   preference from the configuration file and apply it before the first frame is rendered.
9. IF the saved background preference is missing or invalid, THEN THE BackgroundRenderer
   SHALL fall back to the "None" option without throwing a runtime error.
10. THE BackgroundRenderer canvas element SHALL use `pointer-events: none` and SHALL be
    positioned with `z-index` below all interactive UI layers so that mouse and keyboard
    interaction with buttons, inputs, and modals is not affected.

### Requirement 16: UI Design System — Glassmorphism Dark Theme

**User Story:** As a user, I want the application to have a cohesive glassmorphism dark
visual style, so that the interface feels modern, immersive, and visually elevated for
constant touchscreen use.

#### Acceptance Criteria

1. THE Frontend SHALL define a CSS design token system with the following custom properties:
   `--glass-bg`, `--glass-border`, `--glass-blur`, `--glass-shadow`, and `--glass-glow`,
   available globally for consistent reuse across all components.
2. THE DeckButton card SHALL apply glassmorphism styling: `backdrop-filter: blur(12px)`,
   a semi-transparent background using `rgba` at 15–20% opacity, a 1px border using
   `rgba(255, 255, 255, 0.20)`, and a `box-shadow` combining an inner highlight and
   outer depth layer.
3. THE DockedSidebar SHALL use a glass panel background treatment distinct from the main
   dashboard background, referencing `--glass-bg` and `--glass-blur`.
4. THE DockedSidebar SHALL have a right-edge accent line of 1–2px using
   `var(--color-primary)` at 60% opacity to create visual separation from the grid area.
5. THE app header/topbar SHALL use a frosted glass bar with `backdrop-filter` blur and a
   semi-transparent background instead of a flat opaque strip.
6. ALL interactive surfaces (buttons, cards, panels) SHALL have a subtle gradient overlay
   that is lighter at the top and transparent at the bottom to simulate surface depth.

### Requirement 17: Touch-Optimized Deck Button Interactions

**User Story:** As a user, I want deck buttons to respond to touch and pointer input with
clear, satisfying animations, so that the interface feels responsive and tactile during
constant touchscreen use.

#### Acceptance Criteria

1. WHEN a DeckButton is pressed (`:active` state), THE DeckButton SHALL apply a
   `transform: scale(0.94)` and collapse its box-shadow, returning to the default state
   on release with a transition duration of 100ms or less.
2. WHEN a pointer device (non-touch) hovers over a DeckButton, THE DeckButton SHALL apply
   a `transform: translateY(-2px)` lift and increase its glow intensity.
3. THE DeckButton minimum touch target SHALL be 60×60px regardless of the configured
   button size.
4. WHEN a DeckButton is pressed, THE DeckButton SHALL display a ripple effect originating
   from the touch or click point, implemented via CSS or JavaScript.
5. WHEN a DeckButton cell is empty or a placeholder, THE DeckButton SHALL render a dashed
   border at low opacity and a "+" icon to indicate the cell is available for assignment.

### Requirement 18: DockedSidebar Visual Elevation

**User Story:** As a user, I want the docked sidebar to feel visually distinct and
elevated from the main grid, so that the two regions are clearly separated at a glance.

#### Acceptance Criteria

1. THE DockedSidebar SHALL use a glass panel background that is visually distinct from
   the main dashboard background.
2. THE DockedSidebar SHALL render a visible right-edge accent line of 1–2px using
   `var(--color-primary)` at 60% opacity.
3. Sidebar button cards SHALL use the same glassmorphism treatment as DeckButton cards
   but with a slightly different tint value for `--glass-bg`.
4. THE DockedSidebar section label (e.g., "Docked Buttons") SHALL be styled as a small
   uppercase, letter-spacing-widened label rather than a plain text heading.
5. WHEN the viewport width is less than 480px, THE DockedSidebar SHALL collapse and be
   accessible via a floating toggle button that slides the sidebar in as an overlay.

### Requirement 19: Settings View — Two-Panel Nav Rail Layout

**User Story:** As a user, I want the Settings view to use a two-panel nav rail layout
similar to macOS System Settings, so that navigating between settings sections is fast
and visually clear.

#### Acceptance Criteria

1. THE SettingsView SHALL be structured as a two-panel layout with a fixed-width (220px)
   vertical nav rail on the left and a scrollable content panel on the right.
2. THE nav rail SHALL display each settings section as an icon + label row, with an active
   state indicator consisting of a left accent bar and a background highlight.
3. WHEN the viewport width is less than 900px, THE nav rail SHALL collapse to icon-only
   mode at 48px wide, with tooltips displayed on hover to identify each section.
4. WHEN the viewport width is less than 640px, THE nav rail SHALL transform into a
   horizontal scrollable icon bar positioned at the top of the SettingsView.
5. EACH settings section in the content panel SHALL be displayed as a distinct card
   containing a section title, a divider, and grouped form controls.
6. ALL form controls in the SettingsView (sliders, checkboxes, selects) SHALL have a
   minimum touch target height of 44px and clear visual focus and active states.

### Requirement 20: Responsive Layout System

**User Story:** As a user, I want the application layout to adapt fluidly across all
screen sizes from small phones to 4K monitors, so that the interface is always usable
without horizontal scrolling or broken layouts.

#### Acceptance Criteria

1. THE Frontend SHALL define CSS custom properties for breakpoints:
   `--bp-sm: 480px`, `--bp-md: 768px`, `--bp-lg: 1024px`, `--bp-xl: 1366px`,
   `--bp-2xl: 1920px`, available globally for use in media queries and component styles.
2. THE DeckGrid SHALL use CSS Grid with auto-sizing columns that adapt to the available
   width while maintaining a square aspect ratio for each button cell.
3. THE main layout (DockedSidebar, DeckGrid, and header) SHALL use CSS Grid template
   areas so that each region can be independently repositioned at different breakpoints.
4. ALL font sizes in the application SHALL use `clamp()` for fluid scaling between a
   defined minimum and maximum size across the supported viewport range.
5. THE application SHALL never display a horizontal scrollbar at any viewport width
   between 320px and 3840px.

### Requirement 21: Touch Gesture System — Deck Grid Navigation

**User Story:** As a user, I want to navigate between pages and scenes by swiping on the deck grid, so that I can move through my layout quickly without tapping small controls.

#### Acceptance Criteria

1. WHEN the user swipes left on the DeckGrid, THE DeckGrid SHALL navigate to the next page.
2. WHEN the user swipes right on the DeckGrid, THE DeckGrid SHALL navigate to the previous page.
3. WHEN the user swipes up on the DeckGrid, THE DeckGrid SHALL navigate to the next scene.
4. WHEN the user swipes down on the DeckGrid, THE DeckGrid SHALL navigate to the previous scene.
5. WHEN a swipe gesture is detected, THE DeckGrid SHALL apply a slide transition animation of 200ms with ease-out timing; THE DeckGrid SHALL NOT perform an instant page jump.
6. WHEN the user performs a pinch gesture on the DeckGrid, THE DeckGrid SHALL dynamically resize buttons to a scale between 0.6x and 2.0x, and THE DeckGrid SHALL persist the resulting scale value to the application settings.
7. THE DeckGrid SHALL display a page indicator (dots or numbers) that updates its position in real-time during a swipe gesture using interpolated values, not discrete jumps.
8. WHEN a touch movement on the DeckGrid is less than 10px from the touch origin, THE DeckGrid SHALL NOT trigger a swipe navigation, treating the gesture as a button tap instead.
9. WHEN a swipe gesture includes momentum (fast flick), THE DeckGrid SHALL continue the transition with momentum and snap to the nearest page boundary.

### Requirement 22: Touch Gesture System — Button Interactions

**User Story:** As a user, I want to reorder and edit buttons using touch gestures, so that I can manage my deck layout directly on the touchscreen without switching to a separate edit mode.

#### Acceptance Criteria

1. WHEN a user holds a finger on a DeckButton for 500ms, THE DeckButton SHALL enter per-button edit mode and display an overlay with "Edit", "Delete", and "Move" options.
2. WHEN a user holds a finger on an empty DeckGrid cell for 500ms, THE Dashboard SHALL open the ButtonEditor directly for that cell.
3. WHEN drag-to-reorder is active (initiated after a 500ms long-press), THE DeckGrid SHALL display a ghost image of the button following the user's finger.
4. WHILE drag-to-reorder is active, THE DeckGrid SHALL highlight the cell currently under the user's finger as the drop target.
5. WHEN the user releases a dragged button over a valid target cell, THE DeckGrid SHALL animate the button into its new position using a spring animation.
6. WHEN a user double-taps a DeckButton, THE DeckButton SHALL execute the button's assigned action.
7. WHEN a touch interaction completes on any interactive element, THE Frontend SHALL trigger a haptic feedback pulse via the Vibration API WHERE the Vibration API is available in the browser.

### Requirement 23: Touch Gesture System — Sidebar

**User Story:** As a user, I want to open and close the sidebar using edge swipe gestures, so that I can access docked buttons without needing a persistent toggle button.

#### Acceptance Criteria

1. WHEN the user swipes right starting from within 20px of the left screen edge, THE DockedSidebar SHALL open as an overlay panel.
2. WHEN the user swipes left while the DockedSidebar is open, THE DockedSidebar SHALL close.
3. THE DockedSidebar SHALL support vertical scrolling with native momentum scroll behavior; THE DockedSidebar SHALL NOT implement a custom scroll mechanism.
4. WHEN a user holds a finger on a DockedSidebar button for 500ms, THE DockedSidebar button SHALL enter the same per-button edit mode as DeckButton long-press (Requirement 22, criterion 1).

### Requirement 24: Touch UX — Visual Feedback and States

**User Story:** As a user, I want every touch interaction to produce immediate and clear visual feedback, so that the interface feels responsive and premium during constant use.

#### Acceptance Criteria

1. WHEN a touch event begins on any interactive element, THE Frontend SHALL apply a visible pressed state within 16ms of the touch event.
2. WHILE a finger is held down on a DeckButton, THE DeckButton SHALL maintain a color-brightened pressed state in addition to the scale-down animation.
3. WHEN a DeckButton action has been triggered within the last 500ms, THE DeckButton SHALL play a glow pulse animation that fades out over 500ms.
4. WHERE the DeviceOrientation API is available, THE DeckGrid SHALL apply a subtle parallax depth effect that responds to device tilt; IF the DeviceOrientation API is unavailable, THEN THE DeckGrid SHALL render without the parallax effect and SHALL NOT throw a runtime error.
5. WHEN the user is swiping between pages, THE page indicator dots SHALL animate their position using interpolated values that track the swipe progress continuously.

### Requirement 25: Touch UX — Edit Mode

**User Story:** As a user, I want a visually distinct edit mode for rearranging buttons, so that I can clearly tell when I am editing versus using the deck normally.

#### Acceptance Criteria

1. WHEN edit mode is active, THE DeckGrid SHALL apply a semi-transparent dark overlay to all non-selected buttons and SHALL apply a wiggle animation to all editable buttons.
2. WHEN the user performs a long-press on any DeckButton, THE Dashboard SHALL enter edit mode (equivalent to activating the existing edit button in the header).
3. WHEN the user taps outside all buttons while edit mode is active, THE Dashboard SHALL exit edit mode.
4. WHEN the user presses the Escape key while edit mode is active, THE Dashboard SHALL exit edit mode.
5. WHEN the user taps a "Done" button while edit mode is active, THE Dashboard SHALL exit edit mode.
6. WHILE edit mode is active, THE DeckGrid SHALL display a drag handle indicator on each button cell.
7. WHILE edit mode is active, THE DeckGrid SHALL support drag-and-drop reordering via touch and SHALL support click-to-select followed by click-to-place reordering via mouse or keyboard.

### Requirement 26: Performance — Touch Responsiveness

**User Story:** As a user, I want all touch interactions to remain smooth and responsive at all times, so that the app feels as fast as a physical hardware device.

#### Acceptance Criteria

1. THE Frontend SHALL maintain a rendering frame rate of 60fps during all touch interactions including swipe, drag, and pinch gestures.
2. THE Frontend SHALL register all touch event handlers as passive listeners WHERE the handler does not call `preventDefault()`, to avoid blocking the browser's scroll pipeline.
3. WHEN the application is not in the foreground (as detected by the Page Visibility API), THE BackgroundRenderer SHALL pause the animation loop for canvas-based backgrounds (DarkVeil, FloatingLines).
4. WHEN the Page Visibility API reports the application has returned to the foreground, THE BackgroundRenderer SHALL resume the animation loop.
5. THE DeckGrid SHALL apply `will-change: transform` to all elements that are actively animating during swipe or drag interactions to enable GPU compositing.
6. WHEN a touch event begins on a DeckButton, THE DeckButton SHALL apply its visual pressed state within 16ms of the touch event timestamp.
