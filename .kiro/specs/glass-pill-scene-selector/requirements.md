# Requirements Document

## Introduction

The Glass Pill Scene Selector replaces the existing `SceneNavigation` component in the VDock dashboard header with a glassmorphism-styled pill/radio toggle group. The selector renders each scene as a labeled segment inside a single pill container, with an animated glider that slides to the active scene using a spring cubic-bezier transition. The design is adapted from the provided CSS reference and integrated with VDock's glass token system and touch-first interaction model.

## Glossary

- **Scene_Selector**: The new pill-style toggle component that replaces `SceneNavigation.vue` in the dashboard header.
- **Glider**: The absolutely-positioned highlight element that slides beneath the active scene label.
- **Scene**: A named group of pages within a VDock profile, identified by a unique `id` and zero-based index.
- **Active_Scene**: The scene currently displayed, tracked by `currentSceneIndex` in `dashboardStore`.
- **Dashboard_Header**: The `<header>` element in `DashboardView.vue` that contains the profile avatar, scene selector, page navigation, and action buttons.
- **Glass_Token**: A CSS custom property defined in `main.css` (e.g. `--glass-bg`, `--glass-border`, `--glass-blur`).

## Requirements

### Requirement 1: Render Scene Segments as a Glass Pill

**User Story:** As a VDock user, I want to see all my scenes displayed as a single pill-shaped toggle group in the header, so that I can identify and switch scenes at a glance.

#### Acceptance Criteria

1. THE Scene_Selector SHALL render one labeled segment per scene in the current profile, in the same order as `currentProfile.scenes`.
2. THE Scene_Selector SHALL wrap all segments in a single pill container styled with `background: var(--glass-bg)`, `backdrop-filter: blur(var(--glass-blur))`, `border: 1px solid var(--glass-border)`, and `border-radius: 1rem`.
3. WHEN a profile has zero scenes, THE Scene_Selector SHALL render nothing (empty fragment).
4. WHEN a profile has exactly one scene, THE Scene_Selector SHALL render a single non-interactive segment with the Glider permanently positioned on it.
5. THE Scene_Selector SHALL display each scene's `name` as the segment label text.
6. WHERE a scene has an `icon` property set, THE Scene_Selector SHALL render the icon before the label text using `FontAwesomeIcon`.

### Requirement 2: Animated Glider Tracks the Active Scene

**User Story:** As a VDock user, I want a smooth sliding highlight to follow the active scene, so that the current selection is always visually obvious.

#### Acceptance Criteria

1. THE Glider SHALL be absolutely positioned inside the pill container and span the width of exactly one segment (`width: calc(100% / N)` where N is the scene count).
2. WHEN the Active_Scene changes, THE Glider SHALL translate horizontally to `translateX(index * 100%)` using `transition: transform 0.5s cubic-bezier(0.37, 1.95, 0.66, 0.56)`.
3. THE Glider SHALL use a `background: linear-gradient(135deg, rgba(52,152,219,0.35), rgba(52,152,219,0.7))` and `box-shadow: 0 0 18px rgba(52,152,219,0.45), inset 0 0 10px rgba(255,255,255,0.15)` to match the VDock primary color.
4. THE Glider SHALL have `border-radius: 1rem` and `z-index: 1` so it renders behind the label text.
5. WHEN the scene count changes (scene added or removed), THE Glider SHALL immediately recompute its width and position without animation.

### Requirement 3: Scene Switching on Tap

**User Story:** As a VDock user, I want to tap a scene segment to switch to it, so that I can navigate scenes with a single touch.

#### Acceptance Criteria

1. WHEN a user taps a segment, THE Scene_Selector SHALL call `dashboardStore.setScene(index)` with the zero-based index of the tapped segment.
2. WHEN a user taps the already-active segment, THE Scene_Selector SHALL perform no action.
3. THE Scene_Selector SHALL emit a `scene-change` event with the new scene index after calling `setScene`.
4. WHEN a segment is tapped, THE Scene_Selector SHALL trigger `haptics.tap()` for touch feedback.
5. THE Scene_Selector SHALL apply a `scale(0.96)` press animation on `:active` with `transition: transform 80ms ease` on each segment label.

### Requirement 4: Touch Target Compliance

**User Story:** As a VDock user on a touchscreen, I want scene segments to be large enough to tap reliably, so that I don't accidentally miss or hit the wrong scene.

#### Acceptance Criteria

1. THE Scene_Selector SHALL ensure each segment has a minimum height of 44px to comply with VDock touch target standards.
2. THE Scene_Selector SHALL ensure each segment has a minimum width of 80px.
3. WHEN the total pill width would exceed the available header space, THE Scene_Selector SHALL allow horizontal scrolling within the pill container using `overflow-x: auto` with `scrollbar-width: none`.
4. THE Scene_Selector SHALL never cause the dashboard header to overflow horizontally or trigger a page-level scrollbar.

### Requirement 5: Responsive Behaviour

**User Story:** As a VDock user on a small screen, I want the scene selector to adapt gracefully, so that it remains usable at all viewport widths.

#### Acceptance Criteria

1. WHILE the viewport width is below 768px, THE Scene_Selector SHALL truncate segment labels to a maximum of 72px using `max-width` and `text-overflow: ellipsis`.
2. WHILE the viewport width is below 480px, THE Scene_Selector SHALL hide scene icons and show only the text label.
3. THE Scene_Selector SHALL use `font-size: clamp(0.65rem, 0.8vw + 0.4rem, 0.85rem)` for all segment labels.
4. THE Scene_Selector SHALL never render wider than `100%` of its parent container.

### Requirement 6: Edit Mode — Add and Edit Scene Controls

**User Story:** As a VDock user in edit mode, I want to add new scenes and edit existing ones directly from the selector, so that I can manage scenes without leaving the dashboard.

#### Acceptance Criteria

1. WHILE `isEditMode` is `true`, THE Scene_Selector SHALL render an "Add Scene" button (`+` icon) appended after the pill container.
2. WHILE `isEditMode` is `true`, THE Scene_Selector SHALL render a small edit icon button overlaid on each segment.
3. WHEN the "Add Scene" button is tapped, THE Scene_Selector SHALL emit an `add-scene` event.
4. WHEN an edit icon button is tapped, THE Scene_Selector SHALL emit an `edit-scene` event with the corresponding `Scene` object.
5. WHILE `isEditMode` is `false`, THE Scene_Selector SHALL hide all add and edit controls.
6. THE "Add Scene" button and edit icon buttons SHALL each have a minimum touch target of 44×44px.

### Requirement 7: Accessibility

**User Story:** As a VDock user relying on keyboard or assistive technology, I want the scene selector to be navigable and announced correctly, so that I can use it without a touchscreen.

#### Acceptance Criteria

1. THE Scene_Selector SHALL render the pill container as a `role="radiogroup"` element with `aria-label="Scene selector"`.
2. THE Scene_Selector SHALL render each segment as a `role="radio"` element with `aria-checked` set to `"true"` for the active scene and `"false"` for all others.
3. WHEN a segment has keyboard focus and the user presses `Enter` or `Space`, THE Scene_Selector SHALL activate that scene.
4. THE Scene_Selector SHALL support arrow-key navigation: pressing `ArrowRight` or `ArrowDown` SHALL move focus to the next segment, and `ArrowLeft` or `ArrowUp` SHALL move focus to the previous segment, wrapping at the ends.
5. THE Scene_Selector SHALL set `tabindex="0"` on the active segment and `tabindex="-1"` on all others (roving tabindex pattern).
