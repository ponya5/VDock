<template>
  <div
    v-if="isVisible"
    class="agent-action-bar"
    :class="`state-${currentState}`"
    role="toolbar"
    :aria-label="`${profile?.label} actions`"
  >
    <div class="agent-state-pill" :title="stateEntry?.message || stateLabel">
      <span class="agent-state-dot" />
      <span class="agent-state-text">
        <strong>{{ profile?.label }}</strong>
        <span>{{ stateLabel }}</span>
      </span>
    </div>
    <div class="agent-actions">
      <button
        v-for="action in visibleActions"
        :key="action.id"
        type="button"
        class="agent-action"
        :class="{ primary: action.isPrimary, running: runningActionId === action.id }"
        :disabled="runningActionId !== null"
        :title="action.description"
        @click="runAction(action)"
      >
        <FontAwesomeIcon
          :icon="['fas', runningActionId === action.id ? 'spinner' : action.icon]"
          :spin="runningActionId === action.id"
        />
        <span>{{ action.label }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { AgentStateName, AppProfileDto } from '@/api/appProfiles'
import type { Scene } from '@/types'
import { useDashboardStore } from '@/stores/dashboard'
import { useNotificationsStore } from '@/stores/notifications'
import { useSettingsStore } from '@/stores/settings'
import { useAppIntegrations } from '@/composables/useAppIntegrations'
import { detectedProfiles, loadProfileMaps, sceneAppProfile } from '@/services/appDetection'
import { agentStateEntry, agentStateFor, initAgentState } from '@/services/agentState'

/**
 * Agent action bar (DL-064): on a Claude Code / Cursor / Devin scene, shows
 * what the agent is doing right now and the actions that fit that moment —
 * Submit while it waits for a prompt, Interrupt while it works, Approve/Deny
 * while a permission dialog is open.
 */

interface BarAction {
  id: string
  label: string
  icon: string
  description: string
  isPrimary: boolean
}

const props = defineProps<{ scene: Scene | null }>()

const STATE_LABELS: Record<AgentStateName, string> = {
  ready: 'Ready for your prompt',
  working: 'Working…',
  permission: 'Needs your permission',
  unknown: 'Session running',
}

const UNCONFIRMED_STATE_LABEL = 'Status unavailable'

const dashboardStore = useDashboardStore()
const settingsStore = useSettingsStore()
const notificationsStore = useNotificationsStore()
const appIntegrations = useAppIntegrations()
const runningActionId = ref<string | null>(null)

const profile = computed<AppProfileDto | null>(() =>
  props.scene ? sceneAppProfile(props.scene, appIntegrations.value) : null
)

const stateEntry = computed(() => agentStateEntry(profile.value?.status_source))

const currentState = computed<AgentStateName>(() => agentStateFor(profile.value?.status_source))

const isAgentDetected = computed(() => {
  const agentProfile = profile.value
  return agentProfile ? detectedProfiles.value.has(agentProfile.id) : false
})

/**
 * With app scanning off, "not detected" means "not looked for", so the bar
 * stays up with the generic actions instead of vanishing on a live agent.
 */
const isAgentPossiblyRunning = computed(() => {
  if (!profile.value) return false
  if (stateEntry.value || isAgentDetected.value) return true
  return !settingsStore.appScanningEnabled
})

const visibleActions = computed<BarAction[]>(() => {
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

const isVisible = computed(() =>
  !dashboardStore.isEditMode && isAgentPossiblyRunning.value && visibleActions.value.length > 0
)

const stateLabel = computed(() => {
  const isUnconfirmed = currentState.value === 'unknown' && !isAgentDetected.value
  return isUnconfirmed ? UNCONFIRMED_STATE_LABEL : STATE_LABELS[currentState.value]
})

async function runAction(action: BarAction): Promise<void> {
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

onMounted(() => {
  initAgentState()
  void loadProfileMaps()
})
</script>

<style scoped>
.agent-action-bar {
  --agent-accent: #38bdf8;
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 auto 10px;
  padding: 8px 10px;
  max-width: min(100%, 1100px);
  border-radius: 14px;
  background: rgba(15, 20, 28, 0.72);
  border: 1px solid color-mix(in srgb, var(--agent-accent) 45%, transparent);
  box-shadow: 0 0 18px color-mix(in srgb, var(--agent-accent) 22%, transparent);
  backdrop-filter: blur(10px);
  color: #e5e7eb;
  flex-wrap: wrap;
}

.agent-action-bar.state-ready { --agent-accent: #22c55e; }
.agent-action-bar.state-working { --agent-accent: #38bdf8; }
.agent-action-bar.state-permission { --agent-accent: #f59e0b; }
.agent-action-bar.state-unknown { --agent-accent: #94a3b8; }

.agent-state-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.agent-state-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--agent-accent);
  box-shadow: 0 0 8px var(--agent-accent);
  flex-shrink: 0;
}

.state-working .agent-state-dot,
.state-permission .agent-state-dot {
  animation: agent-pulse 1.2s ease-in-out infinite;
}

.agent-state-text {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
  font-size: 0.75rem;
}

.agent-state-text strong {
  font-size: 0.82rem;
}

.agent-state-text span {
  color: color-mix(in srgb, var(--agent-accent) 70%, #e5e7eb);
}

.agent-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-left: auto;
}

.agent-action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 40px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.06);
  color: inherit;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease, transform 0.1s ease;
}

.agent-action:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.12);
}

.agent-action:active:not(:disabled) {
  transform: scale(0.97);
}

.agent-action:disabled {
  cursor: default;
  opacity: 0.6;
}

.agent-action.primary {
  background: var(--agent-accent);
  border-color: transparent;
  color: #0b1015;
}

.agent-action.running {
  opacity: 1;
}

@keyframes agent-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

@media (prefers-reduced-motion: reduce) {
  .agent-state-dot { animation: none !important; }
}
</style>
