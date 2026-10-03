<template>
  <section class="panel" id="agent-alerts">
    <div class="panel-head">
      <h2>Agent attention alerts</h2>
      <span class="spacer"></span>
      <span v-if="hookStatusKnown" class="chip" :class="{ 'chip-ok': installedHookCount > 0 }">
        <FontAwesomeIcon :icon="['fas', installedHookCount === AGENT_HOOK_TARGETS.length ? 'circle-check' : 'circle-half-stroke']" />
        {{ installedHookCount }} of {{ AGENT_HOOK_TARGETS.length }} agents hooked
      </span>
    </div>
    <div class="panel-body">
      <div class="row">
        <div class="row-text">
          <span class="label">Alert me when an agent waits</span>
          <p>Pops a banner — over the dashboard and the screensaver — when a hooked agent needs input or finishes.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Agent attention alerts</span><input type="checkbox" :checked="settingsStore.agentAlertsEnabled" @change="toggleAgentAlerts" /><span class="track"></span></label>
        </div>
      </div>
      <div class="row">
        <div class="row-text">
          <span class="label">Glow when an agent is waiting</span>
          <p>Flashes the dashboard frame while any agent session sits idle, rings that scene's pill, and flags the idle session. Tap Snooze on the frame to quiet it until the agent needs you again.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Agent waiting glow</span><input type="checkbox" :checked="settingsStore.agentWaitingGlowEnabled" @change="toggleWaitingGlow" /><span class="track"></span></label>
        </div>
      </div>
      <div class="row" v-if="settingsStore.agentWaitingGlowEnabled">
        <div class="row-text">
          <span class="label">Waiting alert style</span>
          <p>Flash double-blinks the whole frame — hardest to miss. Pulse breathes softly. Comet runs a light around the edge.</p>
        </div>
        <div class="row-control">
          <select v-model="settingsStore.agentWaitingGlowStyle" class="select w-220" aria-label="Waiting alert style">
            <option value="flash">Flash</option>
            <option value="pulse">Pulse</option>
            <option value="orbit">Comet</option>
          </select>
        </div>
      </div>
      <div class="row" v-if="settingsStore.agentAlertsEnabled">
        <div class="row-text">
          <span class="label">Pin waiting agents on the deck</span>
          <p>Keeps a small chip per idle agent under the top bar — tap one to jump straight to that agent's scene.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Agent waiting chips</span><input type="checkbox" :checked="settingsStore.agentWaitingDockEnabled" @change="toggleWaitingDock" /><span class="track"></span></label>
        </div>
      </div>
      <div class="row" v-if="settingsStore.agentAlertsEnabled">
        <div class="row-text">
          <span class="label">Jump to the agent's scene</span>
          <p>When an agent starts waiting for you (idle after a prompt, or a permission dialog), the deck switches to that agent's scene on its own. Off while you're editing.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Auto-focus agent scene</span><input type="checkbox" :checked="settingsStore.agentAutoFocusScene" @change="settingsStore.agentAutoFocusScene = !settingsStore.agentAutoFocusScene" /><span class="track"></span></label>
        </div>
      </div>
      <div class="row">
        <div class="row-text">
          <span class="label">Agent hooks</span>
          <p>Adds a state hook to the agent's settings file — <code class="kv-code">{{ selectedHookTarget.settingsFile }}</code> — so the deck knows when it's ready for a prompt, working, or idle. Restart a running session to pick the hook up.</p>
          <p v-if="canRemoveSelectedHook">Removing a hook means VDock stops getting alerts from this agent; your other hooks are untouched.</p>
        </div>
        <div class="row-control hook-picker">
          <select v-model="selectedHookAgent" class="select" aria-label="Agent to hook">
            <option v-for="target in AGENT_HOOK_TARGETS" :key="target.id" :value="target.id">
              {{ target.label }}{{ hookOptionSuffix(target.id) }}
            </option>
          </select>
          <button type="button" class="btn sm" @click="installAgentHook(selectedHookAgent)" :disabled="agentHooks[selectedHookAgent].installing">
            <FontAwesomeIcon :icon="['fas', agentHooks[selectedHookAgent].installing ? 'spinner' : 'plug']" :spin="agentHooks[selectedHookAgent].installing" />
            {{ agentHookButtonLabel(selectedHookAgent) }}
          </button>
          <template v-if="canRemoveSelectedHook">
            <button v-if="!confirmingRemove" type="button" class="btn sm" data-action="remove-hook" :disabled="agentHooks[selectedHookAgent].installing" @click="confirmingRemove = true">
              <FontAwesomeIcon :icon="['fas', 'plug-circle-xmark']" />
              Remove hook
            </button>
            <span v-else class="hook-confirm" role="group" aria-label="Confirm hook removal">
              <span class="hook-confirm-text">Remove?</span>
              <button type="button" class="btn sm danger" data-action="confirm-remove-hook" :disabled="agentHooks[selectedHookAgent].installing" @click="removeAgentHook(selectedHookAgent)">Yes</button>
              <button type="button" class="btn sm" data-action="cancel-remove-hook" @click="confirmingRemove = false">Cancel</button>
            </span>
          </template>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'
import { useSetupStatus } from '@/composables/useSetupStatus'
import apiClient from '@/api/client'

const settingsStore = useSettingsStore()
const notificationsStore = useNotificationsStore()
const { refresh: refreshSetupStatus } = useSetupStatus()

// The hook files live on the PC VDock runs on; other devices can't edit them.
const isLocalDevice = ['localhost', '127.0.0.1', '[::1]'].includes(window.location.hostname)

// --- Agent attention alerts -------------------------------------------------
type HookAgentId = 'claude' | 'cursor' | 'antigravity' | 'codex'

interface AgentHookState {
  /** Whether the backend has answered a status request yet. */
  known: boolean
  installed: boolean
  /** An older install that hooks only some of the events. */
  partial: boolean
  installing: boolean
}

const AGENT_HOOK_TARGETS: ReadonlyArray<{ id: HookAgentId; label: string; settingsFile: string }> = [
  { id: 'claude', label: 'Claude Code', settingsFile: '~/.claude/settings.json' },
  { id: 'cursor', label: 'Cursor', settingsFile: '~/.cursor/hooks.json' },
  { id: 'antigravity', label: 'Antigravity', settingsFile: '~/.gemini/config/hooks.json' },
  { id: 'codex', label: 'Codex', settingsFile: '~/.codex/config.toml' },
]

function createAgentHookState(): AgentHookState {
  return { known: false, installed: false, partial: false, installing: false }
}

const agentHooks = reactive<Record<HookAgentId, AgentHookState>>(
  Object.fromEntries(AGENT_HOOK_TARGETS.map(t => [t.id, createAgentHookState()])) as Record<HookAgentId, AgentHookState>
)

const selectedHookAgent = ref<HookAgentId>('claude')
const confirmingRemove = ref(false)
watch(selectedHookAgent, () => { confirmingRemove.value = false })

const canRemoveSelectedHook = computed(() => {
  const hookState = agentHooks[selectedHookAgent.value]
  return isLocalDevice && (hookState.installed || hookState.partial)
})

const selectedHookTarget = computed(
  () => AGENT_HOOK_TARGETS.find(t => t.id === selectedHookAgent.value) ?? AGENT_HOOK_TARGETS[0]
)

const installedHookCount = computed(
  () => AGENT_HOOK_TARGETS.filter(t => agentHooks[t.id].installed).length
)

const hookStatusKnown = computed(
  () => AGENT_HOOK_TARGETS.some(t => agentHooks[t.id].known)
)

function hookOptionSuffix(id: HookAgentId): string {
  const state = agentHooks[id]
  if (!state.known) return ''
  if (state.installed) return ' — hooked'
  if (state.partial) return ' — partial'
  return ' — not hooked'
}

function toggleAgentAlerts() {
  settingsStore.agentAlertsEnabled = !settingsStore.agentAlertsEnabled
}

function toggleWaitingGlow() {
  settingsStore.agentWaitingGlowEnabled = !settingsStore.agentWaitingGlowEnabled
}

function toggleWaitingDock() {
  settingsStore.agentWaitingDockEnabled = !settingsStore.agentWaitingDockEnabled
}

function agentHookButtonLabel(agent: HookAgentId): string {
  const hookState = agentHooks[agent]
  if (hookState.partial) return 'Update'
  return hookState.installed ? 'Reinstall' : 'Install'
}

async function fetchAgentHookStatus() {
  try {
    // One call answers for every agent — the dropdown renders its
    // per-agent install state from this.
    const res = await apiClient.get('/agent-events/hook-status', { agent: 'all' })
    const statuses = res.data?.agents ?? {}
    for (const { id } of AGENT_HOOK_TARGETS) {
      const status = statuses[id]
      if (!status) continue
      agentHooks[id].installed = !!status.installed
      agentHooks[id].partial = !!status.partial
      agentHooks[id].known = true
    }
  } catch (error) {
    console.error('Failed to read hook statuses:', error)
  }
}

async function installAgentHook(agent: HookAgentId) {
  const hookState = agentHooks[agent]
  const agentLabel = AGENT_HOOK_TARGETS.find(target => target.id === agent)?.label ?? agent
  hookState.installing = true
  try {
    const res = await apiClient.post('/agent-events/install-hook', null, { params: { agent } })
    if (!res.data?.success) {
      notificationsStore.error('Hook install failed', res.data?.error || 'Unknown error')
      return
    }
    hookState.installed = true
    hookState.partial = false
    hookState.known = true
    notificationsStore.success(
      `${agentLabel} hook installed`,
      `The deck now follows ${agentLabel}'s state. Restart running ${agentLabel} sessions to pick it up.`
    )
  } catch (e: any) {
    notificationsStore.error('Hook install failed', e?.response?.data?.error || 'Backend unreachable')
  } finally {
    hookState.installing = false
  }
}

async function removeAgentHook(agent: HookAgentId) {
  const hookState = agentHooks[agent]
  const agentLabel = AGENT_HOOK_TARGETS.find(target => target.id === agent)?.label ?? agent
  hookState.installing = true
  try {
    const res = await apiClient.post('/agent-events/uninstall-hook', null, { params: { agent } })
    if (!res.data?.success) {
      notificationsStore.error('Hook removal failed', res.data?.error || 'Unknown error')
      return
    }
    hookState.installed = false
    hookState.partial = false
    notificationsStore.success('Hook removed', `VDock no longer follows ${agentLabel}. Your other hooks are untouched.`)
    void refreshSetupStatus()
  } catch (e: any) {
    notificationsStore.error('Hook removal failed', e?.response?.data?.error || 'Backend unreachable')
  } finally {
    confirmingRemove.value = false
    hookState.installing = false
  }
}

onMounted(fetchAgentHookStatus)
</script>

<style scoped>
.hook-picker {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.hook-picker .select {
  width: auto;
  min-width: 190px;
}
.settings-app .hook-picker .btn.sm { min-height: 44px; min-width: 44px; }
.hook-confirm {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}
.hook-confirm-text { font-weight: 600; }
.chip-ok {
  border-color: #1f5c41;
  background: rgba(61, 220, 151, 0.09);
  color: #8fe8bd;
}
</style>
