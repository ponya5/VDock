/**
 * Scene packs — share a scene as a single JSON file.
 *
 * Format:
 *   { "vdock_pack": { "kind": "scene", "version": 1 }, "scene": {...} }
 *
 * Export deliberately carries ONLY the scene (name/icon/colour/pages/buttons) —
 * no profile settings, no user settings — so a pack is safe to post publicly.
 * Import regenerates every id (a pack pasted twice shouldn't collide) and
 * strips credential-shaped config keys, since a shared scene can otherwise
 * smuggle someone's API key or webhook token into your deck.
 */
import type { Scene } from '@/types'

const PACK_KIND = 'scene'
const PACK_VERSION = 1

/** Config keys that can hold secrets — always stripped on import AND export. */
const SECRET_KEYS = new Set([
  'api_key', 'apikey', 'token', 'access_token', 'secret',
  'password', 'passwd', 'authorization', 'auth_header', 'webhook_secret',
])

let counter = 0
function freshId(prefix: string): string {
  counter = (counter + 1) % 1_000_000
  return `${prefix}_${Date.now().toString(36)}_${counter}`
}

function stripSecrets(config: Record<string, any> | undefined): Record<string, any> {
  if (!config || typeof config !== 'object') return {}
  const out: Record<string, any> = {}
  for (const [k, v] of Object.entries(config)) {
    if (SECRET_KEYS.has(k.toLowerCase())) continue
    // Recurse one level — multi_action steps and toggle sides nest configs.
    out[k] = v && typeof v === 'object' && !Array.isArray(v) && v.config
      ? { ...v, config: stripSecrets(v.config) }
      : v
  }
  return out
}

function sanitizeButton(button: any): any | null {
  if (!button || typeof button !== 'object') return null
  const pos = button.position
  if (!pos || typeof pos.row !== 'number' || typeof pos.col !== 'number') return null
  return {
    ...button,
    id: freshId('btn'),
    position: { row: pos.row, col: pos.col },
    size: {
      rows: Math.max(1, Math.min(6, Number(button.size?.rows) || 1)),
      cols: Math.max(1, Math.min(8, Number(button.size?.cols) || 1)),
    },
    action: button.action
      ? { ...button.action, config: stripSecrets(button.action.config) }
      : button.action ?? null,
  }
}

export function buildScenePack(scene: Scene): string {
  const pack = {
    vdock_pack: { kind: PACK_KIND, version: PACK_VERSION, app: 'VDock' },
    scene: {
      ...scene,
      // Strip runtime markers — a pack is a template, not a live scene.
      isActive: undefined,
      triggeredByApp: undefined,
      pages: (scene.pages ?? []).map((page) => ({
        ...page,
        buttons: (page.buttons ?? []).map((b) => ({
          ...b,
          action: b?.action
            ? { ...b.action, config: stripSecrets(b.action.config) }
            : b?.action ?? null,
        })),
      })),
    },
  }
  return JSON.stringify(pack, null, 2)
}

export function downloadScenePack(scene: Scene): void {
  const blob = new Blob([buildScenePack(scene)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `vdock-scene-${(scene.name || 'scene').toLowerCase().replace(/[^a-z0-9]+/g, '-')}.json`
  a.click()
  URL.revokeObjectURL(url)
}

export interface ScenePackResult {
  scene?: Scene
  error?: string
}

/** Parse + validate + sanitize a pack file's text into a ready-to-add Scene. */
export function parseScenePack(text: string): ScenePackResult {
  let data: any
  try {
    data = JSON.parse(text)
  } catch {
    return { error: 'Not valid JSON' }
  }

  // Accept both wrapped packs and a bare scene object.
  const meta = data?.vdock_pack
  const raw = meta?.kind === PACK_KIND ? data.scene : (data?.pages ? data : null)
  if (meta && meta.kind !== PACK_KIND) {
    return { error: `This is a ${meta.kind} pack, not a scene` }
  }
  if (!raw || !Array.isArray(raw.pages) || raw.pages.length === 0) {
    return { error: 'No pages found — not a VDock scene' }
  }

  const pages = raw.pages.map((page: any, i: number) => ({
    id: freshId('page'),
    name: String(page?.name ?? `Page ${i + 1}`).slice(0, 60),
    grid_config: {
      rows: Math.max(1, Math.min(8, Number(page?.grid_config?.rows) || 3)),
      cols: Math.max(1, Math.min(10, Number(page?.grid_config?.cols) || 3)),
    },
    buttons: (Array.isArray(page?.buttons) ? page.buttons : [])
      .map(sanitizeButton)
      .filter(Boolean),
  }))

  return {
    scene: {
      id: freshId('scene'),
      name: String(raw.name ?? 'Imported Scene').slice(0, 50),
      icon: typeof raw.icon === 'string' ? raw.icon.slice(0, 60) : '',
      color: typeof raw.color === 'string' ? raw.color.slice(0, 32) : '#3498db',
      pages,
      isActive: false,
      buttonSize: typeof raw.buttonSize === 'number' ? raw.buttonSize : 1.0,
    },
  }
}
