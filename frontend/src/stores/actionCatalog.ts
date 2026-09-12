import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/api/client'
import type { ButtonAction } from '@/types'

/**
 * The action catalog, served by GET /api/actions/catalog.
 *
 * The picker and the button editor's config forms are built from this rather
 * than from hardcoded markup, so the UI cannot offer an action the backend has
 * no handler for. That used to happen constantly: 22 of the 46 entries
 * ButtonActionsSidebar.vue hardcoded dispatched to a non-existent action type
 * and failed on press.
 *
 * See backend/actions/catalog.py for the authoritative definitions.
 */

export type ActionRunsOn = 'backend' | 'frontend' | 'widget'

export interface ConfigFieldSpec {
  name: string
  label: string
  type: 'text' | 'textarea' | 'number' | 'select' | 'boolean' | 'keys' | 'steps' | 'path' | 'url'
  required: boolean
  default?: unknown
  options?: Array<{ value: string; label: string }>
  placeholder?: string
  help?: string
}

export interface ActionSpec {
  id: string
  label: string
  category: string
  icon: [string, string]
  action_type: string
  description: string
  default_config: Record<string, unknown>
  config_fields: ConfigFieldSpec[]
  runs_on: ActionRunsOn
  display_only: boolean
  long_running: boolean
  keywords: string[]
  /** Present when the action is listed but not currently usable. */
  unavailable_reason?: string
}

export interface CategorySpec {
  id: string
  label: string
  icon: [string, string]
}

/**
 * Used only until the catalog loads (or if it fails to). Every widget action
 * type in backend/actions/catalog.py matches one of these shapes.
 */
const FALLBACK_DISPLAY_ONLY_PREFIXES = ['metric_', 'time_'] as const
const FALLBACK_DISPLAY_ONLY_EXACT = ['weather', 'calendar'] as const

const FALLBACK_DISPLAY_ONLY_TYPES: ReadonlySet<string> = {
  has: (value: string) =>
    FALLBACK_DISPLAY_ONLY_EXACT.includes(value as never) ||
    FALLBACK_DISPLAY_ONLY_PREFIXES.some((prefix) => value.startsWith(prefix))
} as ReadonlySet<string>

export const useActionCatalogStore = defineStore('actionCatalog', () => {
  const actions = ref<ActionSpec[]>([])
  const categories = ref<CategorySpec[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const loadedAt = ref<number | null>(null)

  const byId = computed<Record<string, ActionSpec>>(() =>
    Object.fromEntries(actions.value.map((a) => [a.id, a]))
  )

  const byActionType = computed<Record<string, ActionSpec>>(() =>
    Object.fromEntries(actions.value.map((a) => [a.action_type, a]))
  )

  /**
   * Action types that must not dispatch on press (live widgets).
   *
   * Falls back to a naming-convention guess when the catalog has not loaded --
   * if the backend is unreachable, dispatching a widget would pop an error
   * toast every time the user touched a CPU or clock button. The catalog test
   * asserts this fallback covers every real widget type.
   */
  const displayOnlyTypes = computed(() => {
    if (!actions.value.length) return FALLBACK_DISPLAY_ONLY_TYPES
    return new Set(actions.value.filter((a) => a.display_only).map((a) => a.action_type))
  })

  /** Categories that actually have at least one action, in server order. */
  const populatedCategories = computed(() =>
    categories.value.filter((c) => actions.value.some((a) => a.category === c.id))
  )

  function actionsInCategory(categoryId: string): ActionSpec[] {
    return actions.value.filter((a) => a.category === categoryId)
  }

  /** Case-insensitive match over label, description and keywords. */
  function search(query: string): ActionSpec[] {
    const q = query.trim().toLowerCase()
    if (!q) return actions.value
    return actions.value.filter(
      (a) =>
        a.label.toLowerCase().includes(q) ||
        a.description.toLowerCase().includes(q) ||
        a.keywords.some((k) => k.toLowerCase().includes(q))
    )
  }

  function matches(spec: ActionSpec, query: string): boolean {
    const q = query.trim().toLowerCase()
    if (!q) return true
    return (
      spec.label.toLowerCase().includes(q) ||
      spec.description.toLowerCase().includes(q) ||
      spec.keywords.some((k) => k.toLowerCase().includes(q))
    )
  }

  /**
   * Build the ButtonAction a catalog entry produces.
   *
   * This is the distinction the old sidebar got wrong: entries like `volume_up`
   * are not action *types*, they are the `cross_platform` type carrying a
   * config. Emitting the entry id as the action type is what broke them.
   */
  function toButtonAction(spec: ActionSpec): ButtonAction {
    return {
      type: spec.action_type as ButtonAction['type'],
      config: { ...spec.default_config }
    }
  }

  async function load(force = false): Promise<void> {
    if (!force && loadedAt.value !== null) return
    if (isLoading.value) return

    isLoading.value = true
    error.value = null
    try {
      // apiClient.get returns the full axios response.
      const response = await apiClient.get('/actions/catalog')
      const data = (response?.data ?? {}) as {
        actions?: ActionSpec[]
        categories?: CategorySpec[]
      }
      actions.value = data.actions ?? []
      categories.value = data.categories ?? []
      loadedAt.value = Date.now()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load action catalog'
    } finally {
      isLoading.value = false
    }
  }

  return {
    actions,
    categories,
    isLoading,
    error,
    loadedAt,
    byId,
    byActionType,
    displayOnlyTypes,
    populatedCategories,
    actionsInCategory,
    search,
    matches,
    toButtonAction,
    load
  }
})
