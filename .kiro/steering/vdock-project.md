# VDock Project Guidelines

## What This App Is

VDock is a virtual stream deck — a touchscreen-first application where users interact constantly by pressing, swiping, pinching, and dragging buttons. Think of it as a software replacement for a physical Elgato Stream Deck. The user is always touching the screen.

This context must inform every UI decision: touch targets, animations, responsiveness, and feedback must all be production-quality.

## Tech Stack

- **Frontend:** Vue 3 + TypeScript + Pinia + Vue Router, wrapped in Electron
- **Backend:** Python/Flask REST API
- **Styling:** CSS custom properties only — no Tailwind, no component library
- **Testing:** Vitest + fast-check (frontend), pytest + Hypothesis (backend)

## Project Structure

```
frontend/src/
  assets/styles/main.css     ← global CSS tokens and base styles
  components/                ← reusable components (DeckButton, DockedSidebar, etc.)
  composables/               ← Vue composables (useGestures, useParallax, etc.)
  utils/                     ← pure utilities (haptics, etc.)
  stores/                    ← Pinia stores (settings, dashboard, etc.)
  views/                     ← page-level views (DashboardView, SettingsView, etc.)
  services/                  ← background services (appMonitor, autoSceneSwitcher)

backend/
  routes/                    ← Flask blueprints
  utils/                     ← Python utilities (file_manager, logger, etc.)
  actions/                   ← action executor and action types
  models/                    ← data models (profile, button, theme)
```

## UI Design System

### Glassmorphism Dark Theme

All interactive surfaces use the glass token system defined in `main.css`:

```css
--glass-bg: rgba(0, 0, 0, 0.25)
--glass-border: rgba(255, 255, 255, 0.12)
--glass-blur: 14px
--glass-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.08)
--glass-glow: 0 0 20px rgba(52, 152, 219, 0.25)
```

Never use flat solid backgrounds on interactive cards. Always use `backdrop-filter: blur(var(--glass-blur))` with `var(--glass-bg)`.

### Touch Targets

- Minimum touch target: **60×60px** for deck buttons
- Minimum touch target: **44px height** for all form controls (inputs, selects, sliders)
- Never make interactive elements smaller than these minimums regardless of configured size

### Responsive Breakpoints

```
480px  → --bp-sm  (narrow phone, sidebar collapses to overlay)
768px  → --bp-md  (tablet portrait, header stacks)
1024px → --bp-lg  (tablet landscape / small laptop)
1366px → --bp-xl  (standard laptop)
1920px → --bp-2xl (1080p monitor, scale up)
```

The app must never show a horizontal scrollbar at any width from 320px to 3840px.

### Font Sizes

All font-size declarations must use `clamp()`:
```css
/* correct */
font-size: clamp(13px, 1vw + 10px, 18px);

/* wrong */
font-size: 14px;
```

## Touch Interaction Rules

### Gesture Composables

All touch gestures are implemented via `frontend/src/composables/useGestures.ts`:

- `useTouchSwipe` — swipe left/right/up/down with 10px threshold and velocity
- `usePinchZoom` — two-finger pinch to scale grid (0.6x–2.0x)
- `useLongPress` — 500ms hold, cancels if finger moves > 5px
- `useEdgeSwipe` — swipe right from within 20px of left edge to open sidebar

**All listeners must be registered as `{ passive: true }` unless `preventDefault()` is explicitly required (drag reorder only).**

### Haptic Feedback

Use `frontend/src/utils/haptics.ts` for all touch feedback:

```typescript
haptics.tap()        // button press (10ms)
haptics.longPress()  // long-press trigger (30ms)
haptics.success()    // drag drop complete ([10, 50, 10]ms)
haptics.error()      // action error (100ms)
```

Always use optional chaining — `navigator.vibrate?.()` — never assume the API exists.

### Animation Performance

- Use `will-change: transform` on elements actively animating during swipe or drag
- Use `transform` and `opacity` for animations — never animate `width`, `height`, `top`, `left`
- Press animation: `scale(0.94)` + shadow collapse, `transition: 80ms ease`
- Hover lift (pointer devices only, guarded by `@media (hover: hover)`): `translateY(-2px)`
- Spring drop animation: `scale(1.0) → scale(1.1) → scale(0.95) → scale(1.0)` over 300ms

## Python Backend Rules

### Logging

Never use `print()` for logging. Always use the module-level logger:

```python
import logging
logger = logging.getLogger('vdock')

# correct
logger.error('Failed to save: %s', e)

# wrong
print(f'Failed to save: {e}')
```

### Route Handlers

- Route handlers must be thin dispatchers — no business logic inline
- Extract logic > 40 lines into dedicated helper functions or service methods
- Use the `metric_route` decorator in `routes/system_metrics.py` for all metrics routes
- Always apply `@require_auth` when `Config.REQUIRE_AUTH` is `True`

### ActionExecutor

The `action_executor` singleton is created once in `app.py`. Never instantiate a new `ActionExecutor()` inside a route handler. Import and reuse the singleton:

```python
from app import action_executor

if action_executor is None:
    return jsonify({'error': 'Action executor unavailable'}), 503
```

## Settings View Layout

The Settings view uses a two-panel nav rail layout:
- Left: 220px fixed vertical nav rail with icon + label rows
- Right: scrollable content panel with section cards
- At < 900px: nav rail collapses to 48px icon-only with tooltips
- At < 640px: nav rail becomes a horizontal scrollable icon bar at the top

## Animated Backgrounds

Background preference is stored in `localStorage` via `settingsStore.backgroundPreference`. Options: `'none'`, `'solid-color'`, `'dark-veil'`, `'floating-lines'`.

`BackgroundRenderer.vue` is mounted at the root in `App.vue` using `<Teleport to="body">` with `pointer-events: none` and `z-index: 0`. It must never block touch or click events.

Canvas backgrounds (`DarkVeil.vue`, `FloatingLines.vue`) must pause their RAF loop when the app is backgrounded (Page Visibility API).

## What Not To Do

- Do not use `console.log` in production code — use `console.warn` or `console.error`
- Do not use `position: fixed` for UI elements that should be in page flow on small screens
- Do not animate `width`, `height`, `top`, or `left` — use `transform` instead
- Do not register touch listeners without `{ passive: true }` unless `preventDefault()` is needed
- Do not instantiate `ActionExecutor` in route handlers
- Do not use `print()` in Python — use the logger
- Do not make touch targets smaller than 60×60px (buttons) or 44px height (form controls)
- Do not use flat solid backgrounds on interactive cards — use the glass token system
