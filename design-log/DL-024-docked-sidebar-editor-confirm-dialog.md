# DL-024 — Docked Sidebar Legibility, Pinned Edit-Button Layout, In-App Confirm Dialog

## Request

Three UI fixes for the 7" (1024×600) panel:

1. Docked sidebar controls too small — weather card nearly unreadable.
2. Edit Button (button configuration) modal wastes space / hard to use on short screens.
3. Button removal used a native `confirm()` — replace with a properly designed prompt.

## Implementation Results

### 1. Docked sidebar sizing (`DockedSidebar.vue`)

- Compact-width cap raised `132px → 168px`. At 132px the weather card text
  and button labels squeezed past legibility; 168px still leaves ~840px for
  the main grid at 1024×600.
- Weather card enlarged for arm's-length reading: icon `34→46px`,
  temperature `1.5→2.1rem` (Instrument Serif), description `0.68→0.8rem`,
  location `0.62→0.72rem`, padding `10→14px`, gap `4→6px`.
- `paddingBlock` reservation for the card updated `104→150px` so grid
  sizing math matches the taller card.
- "DOCKED BUTTONS" header clamp floor raised `0.60→0.70rem`.

### 2. Edit Button modal layout (`ButtonEditor.vue`)

- Converted `.button-editor` to `display: flex; flex-direction: column;
  overflow: hidden` — the whole modal no longer scrolls.
- `.modal-body` is now the sole scroll region (`flex: 1 1 auto;
  min-height: 0; overflow-y: auto`); `.modal-header` and `.modal-footer`
  are `flex-shrink: 0` so **Save/Cancel stay pinned and always reachable**
  at 600px viewport height.
- Width made responsive: `600px → min(600px, 94vw)`.
- `@media (max-height: 700px)` tightening: modal max-height `94vh`, reduced
  padding, smaller title, tighter `form-group` margins.

Verified live at 1024×600: editor is 600×564, body scrolls
(`scrollHeight > clientHeight`), footer fully visible (bottom edge at
566px).

### 3. `ConfirmDialog` — in-app confirmation system

New files:

- `frontend/src/composables/useConfirm.ts` — `confirmDialog(options)`
  returns `Promise<boolean>`; a shared ref holds the pending request and
  `settleConfirmDialog` resolves it.
- `frontend/src/components/ConfirmDialog.vue` — glass/dark modal matching
  the design language: icon-in-circle (blue default / red `danger`),
  title, message, Cancel + confirm actions (46px min-height touch
  targets), Esc/Enter keyboard affordances, overlay-click cancel.

Mounted once in `App.vue` (inside the themed root).

All 7 native `confirm()` call sites replaced:

- `useButtonActions.ts` — grid + docked button deletion
- `DashboardView.vue` — page deletion
- `NotificationCenter.vue` — clear-all
- `ProfilesView.vue` — profile deletion
- `SettingsView.vue` — profile deletion, clear recent actions
- `SceneEditor.vue` — scene deletion, scene reset, page deletion

**Teleport-target fix:** initial implementation teleported to `body`, which
escapes App.vue's `.theme-dark` root — the dialog rendered with unstyled
light `:root` vars (milky card, washed-out text). Retargeted to
`.theme-dark` per the existing `TouchModeSelector`/`BackgroundPicker`
pattern. Verified: bg `#17233a`, title `#eef2fa`.

Also fixed a leaked `keydown` listener (now removed `onUnmounted`).

### 4. Native `alert()` sweep

The remaining `alert()` calls (validation errors, upload failures, import
errors) are the same class of ugly OS popup — all converted to
`notificationsStore.error/success` toasts:

- `SceneEditor.vue` ×5 (image validation, upload, scene-name)
- `SettingsView.vue` ×10 (scene creation, shortcut add, auto-switching)
- `ProfilesView.vue` ×1 (import) + store wiring
- `useButtonActions.ts` ×1 (page full)
- `AvatarPicker.vue` ×4 + store wiring

Zero `confirm(`/`alert(` calls remain in `src/`.

## Verification

- `vue-tsc --noEmit` clean
- 49 test files / 176 tests pass
- `npm run build` succeeds (pre-existing precache-size warning)
- Live at 1024×600: sidebar 168px + enlarged weather card; editor footer
  pinned; confirm dialog renders themed, Cancel dismisses without deleting
