import type { AppShortcut } from '@/api/appProfiles'
import type { Button, Page, Scene } from '@/types'
import { useAppIntegrations, setAppIntegrations } from '@/composables/useAppIntegrations'
import { useDashboardStore } from '@/stores/dashboard'
import { fetchAppProfiles, hasAppShortcuts, topAppShortcuts } from '@/api/appProfiles'
import { presetRegistry, presetToButton } from '@/data/presets'
import { starterPresetIds } from '@/data/appStarterActions'
import { appIdForExe } from '@/data/appBackgrounds'

/** The scene an app is linked to (empty string when unlinked). */
export function getAppScene(appExe: string): string {
  return useAppIntegrations().value.find(i => i.appExe === appExe)?.sceneId || ''
}

/** A hotkey button for a known app shortcut, placed on a 5-column grid by index. */
export function createButtonFromShortcut(shortcut: AppShortcut, index: number): Button {
  return {
    id: `button-${Date.now()}-${index}`, label: shortcut.name, secondary_label: shortcut.keys.join(' + '),
    icon: ['fas', 'keyboard'], icon_type: 'fontawesome',
    action: { type: 'hotkey', config: { keys: shortcut.keys } }, shape: 'rounded',
    position: { row: Math.floor(index / 5), col: index % 5 }, size: { rows: 1, cols: 1 },
    style: { backgroundColor: '#3498db', textColor: '#ffffff' }, tooltip: shortcut.description, enabled: true
  }
}

type Size = { rows: number; cols: number }

/** First free cell (row-major) on the page that fits `size`, or null when full. */
export function firstFreeSlot(page: Page, size: Size = { rows: 1, cols: 1 }) {
  const { rows, cols } = page.grid_config
  const taken = (r: number, c: number) => page.buttons.some(b =>
    r >= b.position.row && r < b.position.row + (b.size?.rows ?? 1) &&
    c >= b.position.col && c < b.position.col + (b.size?.cols ?? 1))
  for (let r = 0; r + size.rows <= rows; r++) {
    for (let c = 0; c + size.cols <= cols; c++) {
      let free = true
      for (let dr = 0; dr < size.rows && free; dr++) {
        for (let dc = 0; dc < size.cols && free; dc++) free = !taken(r + dr, c + dc)
      }
      if (free) return { row: r, col: c }
    }
  }
  return null
}

/** Pushes the button into the first free cell of `page`; false when the page is full. */
export function placeButton(page: Page, button: Button): boolean {
  const slot = firstFreeSlot(page, button.size)
  if (!slot) return false
  button.position = slot
  page.buttons.push(button)
  return true
}

/**
 * True when `ensureSceneForApp` would seed the new scene with buttons
 * (keymap/misc shortcuts or starter deck presets) — false means it would
 * come out empty. Callers prompt before creating an empty scene (DL-025).
 * `appName` is a second lookup name for scanned apps whose process name and
 * display name differ.
 */
export async function appSceneHasStarterContent(
  appExe: string,
  appName?: string,
): Promise<boolean> {
  const profiles = await fetchAppProfiles()
  return hasAppShortcuts(profiles, appExe)
    || (appName ? hasAppShortcuts(profiles, appName) : false)
    || starterPresetIds(appExe).length > 0
    || (appName ? starterPresetIds(appName).length > 0 : false)
}

/**
 * The scene linked to an app, creating and linking one when there is none.
 * Starts with the app's keymap shortcuts, else its starter deck presets.
 */
export async function ensureSceneForApp(appExe: string, appName: string): Promise<Scene | null> {
  const dashboard = useDashboardStore()
  const profile = dashboard.currentProfile
  if (!profile) return null
  const existing = profile.scenes.find(s => s.id === getAppScene(appExe))
  if (existing) return existing

  const profiles = await fetchAppProfiles()
  const page: Page = { id: `page-${Date.now()}`, name: 'Page 1', buttons: [], grid_config: { rows: 4, cols: 5 } }
  if (hasAppShortcuts(profiles, appExe)) {
    topAppShortcuts(profiles, appExe, 8).forEach((sc, i) => placeButton(page, createButtonFromShortcut(sc, i)))
  } else {
    for (const id of starterPresetIds(appExe)) {
      const preset = presetRegistry.find(p => p.id === id)
      if (preset) placeButton(page, presetToButton(preset, { row: 0, col: 0 }))
    }
  }
  const scene: Scene = {
    id: `scene-${Date.now()}`, name: appName.replace(/\.exe$/i, ''), icon: 'window-maximize', color: '#3498db',
    pages: [page], triggeredByApp: appExe, appId: appIdForExe(appExe), autoCreated: true
  }
  dashboard.addScene(scene)
  const integrations = useAppIntegrations().value
  const link = integrations.find(i => i.appExe === appExe)
  if (link) {
    link.sceneId = scene.id
    setAppIntegrations(integrations)
  }
  return profile.scenes.find(s => s.id === scene.id) ?? scene
}
