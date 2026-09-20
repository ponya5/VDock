// Bundled default wallpapers for app-themed scenes.
//
// A scene belongs to an app via `scene.appId` (set by template adds and
// auto-create), `scene.triggeredByApp` (the integrating exe), or an enabled
// app integration pointing at the scene. Any of those resolving here gives
// the scene a default background; an explicit `scene.background` still wins
// (see utils/backgroundStyle.ts and DashboardView for the precedence chain).
//
// `exes` statically mirrors the backend keymap exe claims
// (backend/integrations/keymaps/base.py). Terminal exes resolve to
// claude-code on purpose: that profile owns them there too (a terminal
// window is how Claude Code runs — the app badge already reads
// "Claude Code"), so the wallpaper follows the same claim.

import type { AppIntegration, Scene } from '@/types'

export interface AppSceneBackground {
  /** Matches the backend app-profile id (and app-template id) where one exists. */
  id: string
  label: string
  /** Bundled asset URL under frontend/public. */
  image: string
  /** Lowercased process names that imply this app. */
  exes: readonly string[]
}

export const APP_SCENE_BACKGROUNDS: readonly AppSceneBackground[] = [
  {
    id: 'claude-code',
    label: 'Claude Code',
    image: '/assets/backgrounds/apps/claude-code.png',
    exes: [
      'claude.exe', 'claude', 'claude-code.exe',
      'windowsterminal.exe', 'wt.exe', 'cmd.exe', 'powershell.exe', 'pwsh.exe',
      'conhost.exe', 'mintty.exe', 'wezterm-gui.exe', 'alacritty.exe',
      'tabby.exe',
    ],
  },
  {
    id: 'cursor',
    label: 'Cursor',
    image: '/assets/backgrounds/apps/cursor.png',
    exes: ['cursor.exe'],
  },
]

const BY_ID = new Map(APP_SCENE_BACKGROUNDS.map(entry => [entry.id, entry]))
const BY_EXE = new Map(
  APP_SCENE_BACKGROUNDS.flatMap(entry => entry.exes.map(exe => [exe, entry] as const)),
)

/** The registry entry for an app id, if one exists. */
export function appBackgroundById(appId?: string | null): AppSceneBackground | undefined {
  return appId ? BY_ID.get(appId) : undefined
}

/** The registry entry for a process name, if one exists. */
export function appBackgroundForExe(exe?: string | null): AppSceneBackground | undefined {
  return exe ? BY_EXE.get(exe.toLowerCase()) : undefined
}

/** The app id implied by a process name — used to stamp `scene.appId`. */
export function appIdForExe(exe?: string | null): string | undefined {
  return appBackgroundForExe(exe)?.id
}

/**
 * The app a scene is associated with — via `appId`, `triggeredByApp`, or an
 * enabled integration targeting the scene. Ignores `disableAppBackground` so
 * settings UI can still show which default the toggle controls.
 */
export function appForScene(
  scene: Pick<Scene, 'id' | 'appId' | 'triggeredByApp'>,
  integrations?: readonly AppIntegration[],
): AppSceneBackground | undefined {
  const byId = appBackgroundById(scene.appId)
  if (byId) return byId

  const byTriggerExe = appBackgroundForExe(scene.triggeredByApp)
  if (byTriggerExe) return byTriggerExe

  const integration = integrations?.find(i => i.sceneId === scene.id && i.enabled)
  return appBackgroundForExe(integration?.appExe)
}

/**
 * The bundled default background for a scene, or undefined when the scene
 * isn't app-associated (or the app has no bundled artwork, or the user
 * disabled it via `disableAppBackground`).
 */
export function appBackgroundForScene(
  scene: Pick<Scene, 'id' | 'appId' | 'triggeredByApp' | 'disableAppBackground'>,
  integrations?: readonly AppIntegration[],
): AppSceneBackground | undefined {
  if (scene.disableAppBackground) return undefined
  return appForScene(scene, integrations)
}
