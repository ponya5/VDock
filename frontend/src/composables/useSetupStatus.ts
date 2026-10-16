import { computed, ref } from 'vue'
import apiClient from '@/api/client'

/** One row of `GET /api/config/integrations`: status and links only, never a value. */
export interface IntegrationItem {
  id: string
  label: string
  kind: 'secret' | 'cli'
  configured: boolean
  /** Works without a key through a free built-in provider (e.g. Open-Meteo). */
  builtin?: boolean
  builtin_label?: string
  reason: string
  help_url: string
  unlocks?: string
}

interface IntegrationsResponse {
  env_file: string
  items: IntegrationItem[]
}

// Shared by Overview and Accounts & keys so both agree and fetch once per visit.
const items = ref<IntegrationItem[]>([])
const envFile = ref('')
const hooksInstalled = ref<number | null>(null)
const hooksTotal = ref(0)
const loaded = ref(false)
// macOS only: Accessibility not granted, so every keystroke button fails (DL-007).
const keystrokesBlocked = ref(false)

/** What is set up and what is not, for the Settings Overview and Accounts & keys. */
export function useSetupStatus() {
  async function refresh() {
    const [integrations, hooks, permissions] = await Promise.allSettled([
      apiClient.get('/config/integrations'),
      apiClient.get('/agent-events/hook-status', { agent: 'all' }),
      apiClient.get('/system/permissions'),
    ])
    if (integrations.status === 'fulfilled') {
      const body: IntegrationsResponse = integrations.value.data
      items.value = body?.items ?? []
      envFile.value = body?.env_file ?? ''
    }
    if (hooks.status === 'fulfilled') {
      const agents = Object.values<{ installed?: boolean }>(hooks.value.data?.agents ?? {})
      hooksTotal.value = agents.length
      hooksInstalled.value = agents.filter((a) => a.installed).length
    }
    if (permissions.status === 'fulfilled') {
      keystrokesBlocked.value = permissions.value.data?.accessibility === false
    }
    loaded.value = true
  }

  const secrets = computed(() => items.value.filter((i) => i.kind === 'secret'))
  const tools = computed(() => items.value.filter((i) => i.kind === 'cli'))
  const githubTokenMissing = computed(() => items.value.some((i) => i.id === 'GITHUB_TOKEN' && !i.configured))
  const hooksMissing = computed(() => hooksInstalled.value !== null && hooksInstalled.value < hooksTotal.value)

  return { secrets, tools, envFile, hooksInstalled, hooksTotal, loaded, githubTokenMissing, hooksMissing, keystrokesBlocked, refresh }
}
