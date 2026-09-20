# DL-010 — Per-App Default Scene Backgrounds

## Background

Scenes can already carry an explicit `background` image that overrides the
global dashboard background (DL-001 unified the picker; `Scene.background` +
`backgroundStyleFor` handle the override). App integrations map running
processes to scenes and auto-switch on focus change (`autoSceneSwitcher` +
`appIntegrations` in localStorage). Backend app profiles (`keymaps.ALL_PROFILES`)
give each known app a stable id (`claude-code`, `cursor`, `vscode`, ...).

The user supplied branded wallpapers (Claude Code, Cursor) and asked that each
"main app" scene shows its own background by default, overridable in options.

## Problem

There is no way to associate a bundled default wallpaper with an app. Scenes
auto-created for an app (`createSceneForApp`) or assigned to an app integration
fall back to the global background; template scenes (`addTemplateAsScene`) have
no background either. A Claude scene should look like Claude without the user
uploading anything — and an explicit per-scene upload must still win.

## Questions and Answers

**Q: Bake the image into `scene.background` at scene-creation time, or resolve
at render time?**
A: Render time. Baking makes the default indistinguishable from a user
override — "Remove" would drop to the global background instead of back to the
app default, and scenes created before this feature would never get a default.
Render-time fallback keeps `scene.background` purely "the user's override".

**Q: How does a scene know which app it belongs to?**
A: Three carriers, checked in order: `scene.appId` (new field; set by template
adds and auto-create — template ids are app ids), `scene.triggeredByApp`
(existing exe field), and the `appIntegrations` list (an enabled integration
whose `sceneId` matches — covers existing scenes assigned to an app without
`triggeredByApp`).

**Q: Do terminal exes map to the Claude Code wallpaper?**
A: Yes. The backend keymaps deliberately let `claude-code` claim TERMINAL_EXES
(a terminal window is how Claude Code runs; the badge already reads "Claude
Code"). The scene background follows the same claim. The per-scene opt-out
covers users who want a plain terminal scene.

**Q: How does the user get *no* special background on an app scene?**
A: `scene.disableAppBackground = true` — a "Use app default background" toggle
in the Scene Background settings section and in SceneEditor. Absent = enabled.

**Q: Where do app integrations come from in the render path?**
A: New `useAppIntegrations` composable — a module-level `ref` mirroring the
`appIntegrations` localStorage blob, synced on `storage` events (cross-window)
and written through `setAppIntegrations` (same-window). SettingsView's private
copy writes through it.

## Design

```
page.background
  > scene.background            (explicit user override — existing)
    > app default               (bundled wallpaper, unless disableAppBackground)
      resolved via scene.appId → scene.triggeredByApp → integration.sceneId
    > global background         (settings.background — existing)
```

- Assets: `frontend/public/assets/backgrounds/apps/<app-id>.png` (served
  statically by Vite dev / dist / nginx — same pattern as `/logos/`).
- `frontend/src/data/appBackgrounds.ts`: `APP_SCENE_BACKGROUNDS`
  `{id, label, image, exes[]}`, `appBackgroundById`, `appBackgroundForExe`,
  `appBackgroundForScene(scene, integrations)`.
- `frontend/src/composables/useAppIntegrations.ts`: reactive integrations list.
- `Scene` gains `appId?: string` and `disableAppBackground?: boolean` —
  whitelisted in `backend/models/profile.py` (`from_dict`/`to_dict`), or the
  fields would be silently dropped on profile save.
- `DashboardView` computes `effectiveSceneBackground` and feeds it to
  `backgroundClassFor`/`backgroundStyleFor` in place of `scene.background`.
- `createSceneForApp` sets `appId` (from exe) alongside `triggeredByApp`;
  `addTemplateAsScene` sets `appId: template.id`.
- Settings "Scene Background" section shows the effective background, its
  source ("Custom override" / "<App> default"), the opt-out toggle, and Remove
  only clears the override. SceneEditor shows the same preview + toggle.

## Implementation Plan

- [x] Phase 1: bundle wallpapers (`assets/backgrounds/apps/`), registry module,
  Scene type + backend model fields.
- [x] Phase 2: `useAppIntegrations` composable; DashboardView resolution;
  set `appId` in `createSceneForApp` / `addTemplateAsScene`.
- [x] Phase 3: Settings Scene Background UI (effective preview, source caption,
  opt-out toggle); SceneEditor parity.
- [x] Phase 4: vitest coverage for resolvers + precedence; type-check.

## Trade-offs

- Chosen: render-time fallback + `appId`/`disableAppBackground` fields.
- Rejected: baking `scene.background` at creation (can't distinguish default
  from override; no retroactive benefit).
- Rejected: per-app background upload in the Running Applications list — the
  scene override already covers it and the row UI has no room.
- exe→app mapping is a static frontend mirror of backend `exes` lists — same
  accepted drift pattern as `miscAppShortcuts.ts`.

## Verification Criteria

- `npm test` covers: exe→entry, appId→entry, scene resolution order
  (appId > triggeredByApp > integration), `disableAppBackground` opt-out.
- `vue-tsc --noEmit` clean.
- Manual: Claude scene shows Claude wallpaper; uploading an override wins;
  Remove restores the app default; opt-out falls back to global background.

## Implementation Results

- Phase 1: `claude-code.png` + `cursor.png` bundled under
  `frontend/public/assets/backgrounds/apps/`; `data/appBackgrounds.ts` registry
  (`APP_SCENE_BACKGROUNDS`, `appBackgroundById`, `appBackgroundForExe`,
  `appIdForExe`, `appForScene`, `appBackgroundForScene`); `Scene.appId` +
  `Scene.disableAppBackground` added to `types/index.ts` and whitelisted in
  `backend/models/profile.py`.
- Phase 2: `composables/useAppIntegrations.ts` (module ref + `storage`-event
  sync + `setAppIntegrations`/`reloadAppIntegrations`); DashboardView computes
  `effectiveSceneBackground` (override → app default) feeding
  `backgroundClassFor`/`backgroundStyleFor`; `createSceneForApp` stamps
  `appId` from exe, `addTemplateAsScene` stamps `appId: template.id`;
  SettingsView's private `appIntegrations` ref replaced by the shared
  composable (`saveAppIntegrations` writes through `setAppIntegrations`).
- Phase 3: Settings → Appearance → Background → "Scene Background" shows the
  effective image (override or app default) with a source caption, a
  "Use <App> background" opt-out toggle, and Remove clearing only the
  override; SceneEditor mirrors this (app-default preview + opt-out checkbox).
- Phase 4: `app-backgrounds.test.ts` — 10 new tests, all pass; full suite
  148/148 frontend + 735/735 backend; `vue-tsc --noEmit` clean.
- Deviations:
  - `appForScene` was split out of `appBackgroundForScene` during
    implementation — the settings toggle needs the app association even while
    `disableAppBackground` suppresses the wallpaper itself.
  - Preview caption sits outside `.background-preview` because that container
    clips at 120px (`overflow: hidden`).
- Manual browser verification outstanding: the running instance serves
  `.worktrees/unified-background` (`feat/unified-background`), which is an
  ancestor of `upgrade/upgrade--keypad` — this work landed on the latter, so
  it reaches the served tree on the next merge.
