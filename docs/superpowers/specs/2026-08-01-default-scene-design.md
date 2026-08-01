# Resettable Default Scene

Date: 2026-08-01
Status: Approved

## Problem

Every profile is meant to have a "starter" scene (currently a one-time "Home" scene
built by `defaultProfile.ts` for first-time users) with sensible volume/playback
buttons. Once created, it's an ordinary scene: if the user edits or breaks it there's
no way back to the original layout short of deleting the profile.

## Goals

- Every profile (new and existing) has exactly one scene marked as the default scene.
- The default scene is editable like any other scene.
- The default scene can be reset back to its factory layout at any time.
- The default scene cannot be deleted (reset is the intended "undo" path instead).

## Non-goals

- Reconciling scenes from profiles that already have an unflagged, manually-created
  "Home" scene (see Known tradeoff below) — no automatic merge/detection.
- Per-profile custom "what counts as default" content — the factory template is fixed
  and identical across all profiles.

## Design

### 1. Data model

Add `isDefault?: boolean` to `Scene` (`frontend/src/types/index.ts`), alongside the
existing `autoCreated?: boolean` flag. Exactly one scene per profile carries
`isDefault: true`.

### 2. Factory template extraction

`frontend/src/utils/defaultProfile.ts` currently builds the "Home" scene inline
inside `createDefaultProfile()`. Extract that construction into a standalone
`createDefaultScene(): Scene` (sets `isDefault: true`, generates fresh IDs on every
call). `createDefaultProfile()` calls this function instead of building the scene
inline. This function becomes the single source of truth for the factory layout,
reused by first-run bootstrap, migration, and reset.

### 3. Migration for existing profiles

In the dashboard store's `setProfile(profile)` (`frontend/src/stores/dashboard.ts`):
if no scene in `profile.scenes` has `isDefault: true`, append one (via
`createDefaultScene()`) to the end of the array. This is idempotent — once a profile
has a flagged scene, reloading it (e.g. switching profiles and back) does not insert
another.

The scene is appended, not prepended: `setProfile` always resets
`currentSceneIndex` to `0`, so inserting at the front would silently change which
scene an existing user lands on every time they open the app (their real first scene
would shift to index 1). Appending leaves index 0 pointing at whatever was already
first.

The migration is in-memory only — `setProfile` does not call `saveProfile()`. Loading
a profile must never trigger a write (existing property test, "loading a profile
never triggers a write"); this matches how the existing `migrateProfileToScenes` step
already behaves. The inserted default scene is persisted the next time the profile is
saved for any other reason (e.g. the user's next edit), same as any other in-memory
migration.

**Known tradeoff:** profiles that went through the *old*, unflagged bootstrap already
have a manually-created "Home" scene. Migration can't detect that scene is "the same
one," so those profiles will end up with two similarly-named scenes after this ships.
Accepted as a minor, one-time cosmetic issue — not solved by this design.

### 4. Reset behavior

New store action `resetScene(sceneId: string)` in `dashboard.ts`:

- No-ops (does not mutate state) if the target scene's `isDefault` is not `true`.
- Otherwise replaces the scene's `name`, `icon`, `color`, `pages`/`buttons`, and
  style/overlay fields (`buttonSize`, `overlay_style`, `transition_style`,
  `stagger_order`) with a fresh `createDefaultScene()` output, **keeping the original
  scene's `id`** so its position in `scenes` and its active-scene status are
  undisturbed.
- Calls `addToHistory()` and the normal auto-save (`saveProfile()`), matching every
  other mutator in the store.

### 5. UI

`frontend/src/components/SceneEditor.vue`:

- When `editedScene.isDefault` is `true`, the modal footer shows a "Reset to
  Default" button (undo icon) in place of "Delete Scene," gated behind the same
  `confirm(...)` pattern the delete flow already uses.
- Confirming emits a new `reset: [sceneId: string]` event instead of `delete`.
- For any non-default scene, the footer is unchanged (Delete Scene, as today).

`frontend/src/views/DashboardView.vue`:

- Handles the new `@reset` event from `SceneEditor` by calling
  `dashboardStore.resetScene(id)`, showing a success notification, and closing the
  editor — the local `editedScene` copy in `SceneEditor` is stale after a reset, the
  same way it's stale after a delete today, so closing (rather than trying to patch
  it live) matches the existing pattern.

## Testing

- Unit: `resetScene()` on a mutated default scene (renamed, buttons changed) restores
  it to match a fresh `createDefaultScene()` output except for `id`.
- Unit: `resetScene()` on a non-default scene's id is a no-op — guards against a stray
  call ever wiping a user's custom scene.
- Unit: loading a profile with zero `isDefault` scenes results in exactly one being
  added with `isDefault: true`; loading a profile that already has one is unchanged
  (no duplicate insertion across repeated `setProfile` calls).
- Manual/component: `SceneEditor.vue` shows "Reset to Default" (not "Delete Scene")
  when editing the default scene, and shows normal "Delete Scene" for every other
  scene.
