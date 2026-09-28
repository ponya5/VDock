import { reactive } from 'vue'
import apiClient from '@/api/client'

/**
 * Per-app executable overrides (DL-084). `appPaths[key]` is the absolute
 * path the user pointed at (exe / .app bundle / script); empty = unset.
 * Consumed by find_binary, open_app, and the keymap launch-retry.
 */
export const appPaths = reactive<Record<string, string>>({})

let loaded = false

/** One-shot fill from /api/config; refresh() to re-pull explicitly. */
export async function loadAppPaths(force = false): Promise<void> {
  if (loaded && !force) return
  try {
    const { data } = await apiClient.get('/config')
    const map = data?.config?.app_paths
    if (map && typeof map === 'object') {
      // Rebuild in place — same reactive object identity for readers.
      for (const k of Object.keys(appPaths)) delete appPaths[k]
      for (const [k, v] of Object.entries(map)) {
        if (typeof v === 'string' && v.trim()) appPaths[k] = v
      }
    }
    loaded = true
  } catch {
    // Silent — a missing/stale endpoint just means "no overrides"; the
    // editor still renders and saves.
    loaded = true
  }
}

/** Persist the whole map (empty value clears its key). */
export async function saveAppPaths(map: Record<string, string>): Promise<void> {
  await apiClient.put('/config', { app_paths: map })
  for (const k of Object.keys(appPaths)) delete appPaths[k]
  for (const [k, v] of Object.entries(map)) {
    if (typeof v === 'string' && v.trim()) appPaths[k] = v
  }
}

/** Ask the backend to locate an app (PATH + known install dirs). */
export async function probeAppPath(key: string): Promise<string | null> {
  const { data } = await apiClient.get('/app-paths/probe', { app: key })
  return data?.path ?? null
}

/**
 * Apps that can be launched/keymapped but have no gallery template card —
 * the gear on a card only covers templates, so these get rows in the
 * "App launch paths" panel. Key = executable stem (what backend
 * `override_for` matches on).
 */
export const launchApps: { key: string; label: string }[] = [
  { key: 'antigravity', label: 'Antigravity' },
  { key: 'cursor', label: 'Cursor' },
  { key: 'code', label: 'VS Code' },
  { key: 'codium', label: 'VSCodium' },
  { key: 'windsurf', label: 'Windsurf' },
  { key: 'zed', label: 'Zed' },
  { key: 'claude', label: 'Claude CLI' },
  { key: 'codex', label: 'Codex CLI' },
  { key: 'ollama', label: 'Ollama' },
]

/** Map a template card to its app_paths key: an open_app program stem when
 *  the template launches a binary, a known alias for CLI packs whose id
 *  differs from the binary name ('claude-code' → 'claude'), else the id —
 *  inert for pure keymap/URL templates but consistent UX. */
const TEMPLATE_APP_KEYS: Record<string, string> = {
  'claude-code': 'claude',
  'claude': 'claude',
}

export function templateAppKey(template: {
  id: string
  buttons: { action?: { type?: string; config?: { action?: string; path?: string } } }[]
}): string {
  const opener = template.buttons.find(
    (b) => b.action?.type === 'cross_platform' && b.action?.config?.action === 'open_app',
  )
  const p = opener?.action?.config?.path
  if (p) {
    const base = p.replace(/\\/g, '/').split('/').pop() ?? p
    return base.replace(/\.(exe|cmd|bat|com|app|sh)$/i, '').toLowerCase()
  }
  return TEMPLATE_APP_KEYS[template.id] ?? template.id
}
