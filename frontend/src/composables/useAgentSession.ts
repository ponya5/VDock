import { computed, onMounted, onUnmounted, ref, watch, type ComputedRef, type Ref } from 'vue'
import type { AgentStateName, AppProfileDto } from '@/api/appProfiles'
import type { Scene } from '@/types'
import { useDashboardStore } from '@/stores/dashboard'
import { useNotificationsStore } from '@/stores/notifications'
import { useSettingsStore } from '@/stores/settings'
import { useAppIntegrations } from '@/composables/useAppIntegrations'
import { detectedProfiles, loadProfileMaps, sceneAppProfile } from '@/services/appDetection'
import {
  agentStateEntry,
  agentStateFor,
  initAgentState,
  setAgentBarVisible,
  type AgentStateEntry,
} from '@/services/agentState'

/**
 * The live agent behind a scene (DL-064, DL-065): which profile it is, what
 * it is doing, and the actions that fit that moment. Shared by the desktop
 * action bar and the mobile agent console.
 */

export interface AgentSessionAction {
  id: string
  label: string
  icon: string
  description: string
  isPrimary: boolean
}

export interface AgentActionResult {
  success: boolean
  message?: string
  details?: string
}

const STATE_LABELS: Record<AgentStateName, string> = {
  ready: 'Ready for your prompt',
  working: 'Working…',
  permission: 'Needs your permission',
  unknown: 'Session running',
}

const UNCONFIRMED_STATE_LABEL = 'Status unavailable'
const NOT_RUNNING_STATE_LABEL = 'Not running'

export interface AgentSession {
  profile: ComputedRef<AppProfileDto | null>
  stateEntry: ComputedRef<AgentStateEntry | undefined>
  currentState: ComputedRef<AgentStateName>
  stateLabel: ComputedRef<string>
  isAgentDetected: ComputedRef<boolean>
  isAgentPossiblyRunning: ComputedRef<boolean>
  visibleActions: ComputedRef<AgentSessionAction[]>
  runningActionId: Ref<string | null>
  runAction: (action: AgentSessionAction) => Promise<void>
  sendPrompt: (promptText: string) => Promise<AgentActionResult>
}

export function useAgentSession(scene: Ref<Scene | null>): AgentSession {
  const dashboardStore = useDashboardStore()
  const settingsStore = useSettingsStore()
  const notificationsStore = useNotificationsStore()
  const appIntegrations = useAppIntegrations()
  const runningActionId = ref<string | null>(null)

  const profile = computed<AppProfileDto | null>(() =>
    scene.value ? sceneAppProfile(scene.value, appIntegrations.value) : null
  )

  const stateEntry = computed(() => agentStateEntry(profile.value?.status_source))

  const currentState = computed<AgentStateName>(() => agentStateFor(profile.value?.status_source))

  const isAgentDetected = computed(() => {
    const agentProfile = profile.value
    return agentProfile ? detectedProfiles.value.has(agentProfile.id) : false
  })

  /**
   * With app scanning off, "not detected" means "not looked for", so the
   * agent counts as possibly running instead of vanishing on a live session.
   */
  const isAgentPossiblyRunning = computed(() => {
    if (!profile.value) return false
    if (stateEntry.value || isAgentDetected.value) return true
    return !settingsStore.appScanningEnabled
  })

  const visibleActions = computed<AgentSessionAction[]>(() => {
    const agentProfile = profile.value
    const stateActions = agentProfile?.state_actions
    if (!agentProfile || !stateActions) return []
    const entries = stateActions[currentState.value] ?? stateActions.unknown ?? []
    const commandsById = new Map(agentProfile.commands.map(command => [command.id, command]))
    return entries.flatMap((entry, index) => {
      const command = commandsById.get(entry.id)
      if (!command) return []
      return [{
        id: command.id,
        label: entry.label ?? command.label,
        icon: command.icon,
        description: command.description,
        isPrimary: index === 0,
      }]
    })
  })

  const stateLabel = computed(() => {
    if (!isAgentPossiblyRunning.value) return NOT_RUNNING_STATE_LABEL
    const isUnconfirmed = currentState.value === 'unknown' && !isAgentDetected.value
    return isUnconfirmed ? UNCONFIRMED_STATE_LABEL : STATE_LABELS[currentState.value]
  })

  async function runAction(action: AgentSessionAction): Promise<void> {
    if (runningActionId.value) return
    runningActionId.value = action.id
    try {
      const result = await dashboardStore.executeAction(
        { type: action.id, config: {} },
        `agent-bar-${action.id}`,
      )
      if (!result?.success) {
        notificationsStore.error(
          `${action.label} failed`,
          result?.details || result?.message || 'The agent did not receive it',
        )
      }
    } finally {
      runningActionId.value = null
    }
  }

  async function sendPrompt(promptText: string): Promise<AgentActionResult> {
    const promptCommand = profile.value?.prompt_command
    if (!promptCommand) return { success: false, message: 'This agent has no prompt input' }
    const result = await dashboardStore.executeAction(
      { type: promptCommand, config: { text: promptText } },
      `agent-composer-${promptCommand}`,
    )
    return result ?? { success: false, message: 'The agent did not receive it' }
  }

  onMounted(() => {
    initAgentState()
    void loadProfileMaps()
  })

  return {
    profile,
    stateEntry,
    currentState,
    stateLabel,
    isAgentDetected,
    isAgentPossiblyRunning,
    visibleActions,
    runningActionId,
    runAction,
    sendPrompt,
  }
}

/**
 * Tells the alert overlay that a surface already shows this agent's state
 * and Approve/Deny, so the overlay doesn't cover it.
 */
export function trackAgentSurfaceVisibility(
  source: ComputedRef<string | null | undefined>,
  isVisible: ComputedRef<boolean>,
): void {
  watch(
    () => [source.value, isVisible.value] as const,
    ([currentSource, visible], previous) => {
      const previousSource = previous?.[0]
      if (previousSource && previousSource !== currentSource) setAgentBarVisible(previousSource, false)
      if (currentSource) setAgentBarVisible(currentSource, visible)
    },
    { immediate: true },
  )

  onUnmounted(() => {
    if (source.value) setAgentBarVisible(source.value, false)
  })
}
