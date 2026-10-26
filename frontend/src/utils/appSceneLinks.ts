import type { AppIntegration, Scene } from '@/types'
import { exeKey } from '@/utils/appExe'

/**
 * Repairs app→scene links against the scenes the profile really has (DL-152).
 *
 * - A link to a scene that no longer exists (profile reset, scene deleted on
 *   another device) is re-pointed at the scene created for that app
 *   (`triggeredByApp` matches), or cleared when there is none. A dangling id
 *   used to look "linked" everywhere: auto-switching silently did nothing and
 *   Settings never offered to create the missing scene.
 * - An unlinked integration picks up an existing scene made for its app.
 *
 * Returns the repaired list, or null when nothing needed fixing.
 */
export function relinkAppIntegrations(
  integrations: AppIntegration[],
  scenes: Scene[],
): AppIntegration[] | null {
  const ids = new Set(scenes.map(s => s.id))
  let changed = false
  const next = integrations.map(int => {
    if (int.sceneId && ids.has(int.sceneId)) return int
    const key = exeKey(int.appExe)
    const match = key
      ? scenes.find(s => s.triggeredByApp && exeKey(s.triggeredByApp) === key)
      : undefined
    const sceneId = match?.id ?? ''
    if (sceneId === (int.sceneId ?? '')) return int
    changed = true
    return { ...int, sceneId }
  })
  return changed ? next : null
}
