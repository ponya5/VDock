import type { AppShortcut } from '@/api/appProfiles'
import type { Button } from '@/types'
import { useAppIntegrations } from '@/composables/useAppIntegrations'

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
