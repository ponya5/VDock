import { computed, reactive, type Ref } from 'vue'
import { isAgentCategoryId, type AgentCategoryId } from '@/utils/agentCategories'

/**
 * DL-166: per-scene, per-device view of an AI coding scene - "groups"
 * (category rail / chips) or "all" (every button). Device-local on purpose: a
 * 390px phone and a 7" panel legitimately want different views, and phones do
 * not write the profile. Storage failures (private mode) fall back to memory.
 */

export type AgentViewMode = 'groups' | 'all'

interface SceneView {
  mode: AgentViewMode
  category?: AgentCategoryId
}

const STORAGE_KEY = 'vdock.agentSceneView'

function load(): Record<string, SceneView> {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : {}
    if (!parsed || typeof parsed !== 'object') return {}
    const out: Record<string, SceneView> = {}
    for (const [id, view] of Object.entries(parsed as Record<string, Partial<SceneView>>)) {
      if (!view || typeof view !== 'object') continue
      out[id] = {
        mode: view.mode === 'all' ? 'all' : 'groups',
        category: isAgentCategoryId(view.category) ? view.category : undefined,
      }
    }
    return out
  } catch {
    return {}
  }
}

function save(views: Record<string, SceneView>): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(views))
  } catch {
    // Memory-only for this session.
  }
}

const views = reactive<Record<string, SceneView>>(load())

/** Test hook: forget every remembered view (memory and storage). */
export function resetAgentSceneViews(): void {
  for (const key of Object.keys(views)) delete views[key]
  try { window.localStorage.removeItem(STORAGE_KEY) } catch { /* ignore */ }
}

export function useAgentSceneView(sceneId: Ref<string | null | undefined>) {
  const mode = computed<AgentViewMode>(() => (sceneId.value && views[sceneId.value]?.mode) || 'groups')
  const category = computed<AgentCategoryId | undefined>(() => (sceneId.value ? views[sceneId.value]?.category : undefined))

  function update(patch: Partial<SceneView>): void {
    const id = sceneId.value
    if (!id) return
    views[id] = { mode: views[id]?.mode ?? 'groups', category: views[id]?.category, ...patch }
    save(views)
  }

  return {
    mode,
    category,
    setMode: (m: AgentViewMode) => update({ mode: m }),
    setCategory: (id: AgentCategoryId) => update({ category: id }),
  }
}

/** The category to show: the remembered one if it still has buttons, else the first group. */
export function selectedCategoryId(
  remembered: AgentCategoryId | undefined,
  groups: ReadonlyArray<{ id: AgentCategoryId }>,
): AgentCategoryId | null {
  if (remembered && groups.some(g => g.id === remembered)) return remembered
  return groups[0]?.id ?? null
}
