<template>
  <section class="panel triggers-panel" aria-label="Triggers">
    <div class="panel-head">
      <h2>Triggers</h2>
      <span class="hint">When something happens, do something — schedules, app focus, agent state, webhooks.</span>
      <span class="spacer" />
      <span v-if="!engineEnabled" class="tp-paused-chip">Paused</span>
      <label class="tp-switch" :title="engineEnabled ? 'Pause all triggers' : 'Resume all triggers'">
        <span class="sr-only">All triggers on or off</span>
        <input type="checkbox" :checked="engineEnabled" @change="toggleEngine">
        <span class="tp-track" />
      </label>
      <button
        v-if="!formOpen"
        type="button"
        class="tp-btn tp-primary"
        @click="openCreate"
      >
        <FontAwesomeIcon :icon="['fas', 'plus']" /> Add trigger
      </button>
    </div>

    <div class="panel-body">
      <div v-if="loading" class="tp-empty">Loading…</div>
      <div v-else-if="error" class="tp-empty tp-bad">{{ error }}</div>
      <div v-else-if="!triggers.length && !formOpen" class="tp-empty">
        No triggers yet. One can fire an action on a schedule, when an app is
        focused, when an agent needs you, or from a local webhook.
      </div>

      <!-- ── trigger list ─────────────────────────────────────────── -->
      <div
        v-for="trigger in triggers"
        :key="trigger.id"
        class="tp-row"
        :class="{ 'tp-off': !trigger.enabled || !engineEnabled }"
      >
        <div class="tp-row-text">
          <span class="tp-label">{{ trigger.label }}</span>
          <p>{{ eventSummary(trigger.event) }} → {{ actionSummary(trigger.action) }}</p>
          <p v-if="lastFired[trigger.id]" class="tp-fired" :class="{ 'tp-bad': !lastFired[trigger.id].ok }">
            <FontAwesomeIcon :icon="['fas', lastFired[trigger.id].ok ? 'circle-check' : 'triangle-exclamation']" />
            {{ lastFired[trigger.id].ok ? 'Fired' : 'Failed' }} {{ ago(lastFired[trigger.id].ts) }}<template v-if="lastFired[trigger.id].detail"> — {{ lastFired[trigger.id].detail }}</template>
          </p>
        </div>
        <div class="tp-row-ctl">
          <label class="tp-switch" :title="trigger.enabled ? 'Disable trigger' : 'Enable trigger'">
            <span class="sr-only">Enable {{ trigger.label }}</span>
            <input
              type="checkbox"
              :checked="trigger.enabled"
              @change="toggleEnabled(trigger)"
            >
            <span class="tp-track" />
          </label>
          <button
            type="button"
            class="tp-btn tp-sm"
            :disabled="testing.has(trigger.id)"
            title="Fire this trigger now"
            @click="fireTest(trigger)"
          >
            <FontAwesomeIcon :icon="['fas', 'play']" /> {{ testing.has(trigger.id) ? 'Firing…' : 'Test' }}
          </button>
          <button
            type="button"
            class="tp-btn tp-icon"
            title="Edit trigger"
            @click="openEdit(trigger)"
          >
            <FontAwesomeIcon :icon="['fas', 'pen']" />
          </button>
          <button
            type="button"
            class="tp-btn tp-icon"
            :class="{ 'tp-danger': confirmDeleteId === trigger.id }"
            :title="confirmDeleteId === trigger.id ? 'Tap again to confirm' : 'Delete trigger'"
            @click="onDelete(trigger)"
          >
            <FontAwesomeIcon :icon="['fas', 'trash']" />
          </button>
        </div>
      </div>

      <!-- ── add / edit form ──────────────────────────────────────── -->
      <form v-if="formOpen" class="tp-form" @submit.prevent="save">
        <div class="tp-grid">
          <label class="tp-field tp-span2">
            <span class="tp-field-label">Label</span>
            <input v-model="form.label" type="text" class="tp-input" placeholder="e.g. Evening scene" maxlength="120">
          </label>

          <label class="tp-field">
            <span class="tp-field-label">When (event)</span>
            <select v-model="form.eventType" class="tp-select">
              <option value="time">At a time</option>
              <option value="app_foreground">App becomes focused</option>
              <option value="agent_state">Agent enters a state</option>
              <option value="webhook">Webhook is called</option>
            </select>
          </label>

          <!-- event: time -->
          <template v-if="form.eventType === 'time'">
            <label class="tp-field">
              <span class="tp-field-label">At</span>
              <input v-model="form.at" type="time" class="tp-input" required>
            </label>
            <div class="tp-field tp-span2">
              <span class="tp-field-label">Days <span class="tp-note">(none = every day)</span></span>
              <div class="tp-days" role="group" aria-label="Days of week">
                <button
                  v-for="(name, idx) in DAY_NAMES"
                  :key="idx"
                  type="button"
                  class="tp-day"
                  :class="{ 'tp-on': form.days.includes(idx) }"
                  @click="toggleDay(idx)"
                >
                  {{ name }}
                </button>
              </div>
            </div>
          </template>

          <!-- event: app_foreground -->
          <label v-else-if="form.eventType === 'app_foreground'" class="tp-field tp-span2">
            <span class="tp-field-label">Executable</span>
            <input v-model="form.exe" type="text" class="tp-input" placeholder="spotify.exe" required>
            <span class="tp-note">Fires once when this app enters the foreground — matching is case-insensitive.</span>
          </label>

          <!-- event: agent_state -->
          <template v-else-if="form.eventType === 'agent_state'">
            <label class="tp-field">
              <span class="tp-field-label">Agent</span>
              <select v-model="form.source" class="tp-select">
                <option v-for="s in AGENT_SOURCES" :key="s" :value="s">{{ s }}</option>
              </select>
            </label>
            <label class="tp-field">
              <span class="tp-field-label">State</span>
              <select v-model="form.state" class="tp-select">
                <option value="ready">ready — waiting for a prompt</option>
                <option value="working">working — busy</option>
                <option value="permission">permission — blocked on you</option>
              </select>
            </label>
          </template>

          <!-- event: webhook -->
          <div v-else-if="form.eventType === 'webhook'" class="tp-field tp-span2">
            <span class="tp-field-label">Webhook URL</span>
            <div class="tp-webhook">
              <code class="tp-url">POST {{ webhookUrl }}</code>
              <button type="button" class="tp-btn tp-sm" title="Copy URL" @click="copyWebhookUrl">
                <FontAwesomeIcon :icon="['fas', copied ? 'check' : 'copy']" /> {{ copied ? 'Copied' : 'Copy' }}
              </button>
              <button type="button" class="tp-btn tp-sm" title="Regenerate key" @click="form.key = newWebhookKey()">
                <FontAwesomeIcon :icon="['fas', 'rotate']" /> New key
              </button>
            </div>
            <span class="tp-note">Localhost only — call it from scripts, agent hooks or Task Scheduler on this machine.</span>
          </div>

          <label class="tp-field">
            <span class="tp-field-label">Do (action)</span>
            <select v-model="form.actionType" class="tp-select">
              <option value="show_notification">Show a notification</option>
              <option value="switch_scene">Switch scene</option>
              <option value="execute_action">Run an action</option>
            </select>
          </label>

          <!-- action: show_notification -->
          <template v-if="form.actionType === 'show_notification'">
            <label class="tp-field">
              <span class="tp-field-label">Title</span>
              <input v-model="form.title" type="text" class="tp-input" placeholder="Heads up" maxlength="80" required>
            </label>
            <label class="tp-field tp-span2">
              <span class="tp-field-label">Message</span>
              <input v-model="form.message" type="text" class="tp-input" placeholder="Optional detail" maxlength="300">
            </label>
          </template>

          <!-- action: switch_scene -->
          <label v-else-if="form.actionType === 'switch_scene'" class="tp-field">
            <span class="tp-field-label">Scene name</span>
            <input v-model="form.scene" type="text" class="tp-input" placeholder="e.g. Media" required>
          </label>

          <!-- action: execute_action -->
          <template v-else-if="form.actionType === 'execute_action'">
            <label class="tp-field">
              <span class="tp-field-label">Action type</span>
              <select v-model="form.execType" class="tp-select">
                <option v-for="t in EXEC_ACTION_TYPES" :key="t" :value="t">{{ t }}</option>
              </select>
            </label>
            <label class="tp-field tp-span2">
              <span class="tp-field-label">Config (JSON)</span>
              <textarea
                v-model="form.execConfig"
                class="tp-input tp-textarea"
                rows="3"
                spellcheck="false"
                placeholder='{"url": "https://example.com"}'
              />
              <span class="tp-note">Same shape as a button action's config — e.g. url actions take {"url": "…"}.</span>
            </label>
          </template>
        </div>

        <p v-if="formError" class="tp-bad tp-form-err">{{ formError }}</p>
        <div class="tp-form-actions">
          <button type="button" class="tp-btn" @click="closeForm">Cancel</button>
          <button type="submit" class="tp-btn tp-primary" :disabled="saving">
            {{ saving ? 'Saving…' : editingId ? 'Save changes' : 'Add trigger' }}
          </button>
        </div>
      </form>
    </div>
  </section>
</template>

<script setup lang="ts">
/**
 * Triggers settings panel (DL-120 / W5) — self-contained; the orchestrator
 * mounts it inside SettingsView. Talks straight to /api/triggers via
 * services/triggersApi — no settingsStore involvement.
 *
 * Subscribes to `trigger_fired` so a row shows its last outcome inline
 * (the test-fire button answers synchronously too, but scheduled/webhook
 * fires only ever surface over the socket).
 */
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import socketClient from '@/api/socket'
import { useNotificationsStore } from '@/stores/notifications'
import {
  createTrigger,
  fetchTriggersState,
  removeTrigger,
  setTriggersEnabled,
  testTrigger,
  updateTrigger,
  type Trigger,
  type TriggerAction,
  type TriggerActionType,
  type TriggerDraft,
  type TriggerEvent,
  type TriggerEventType,
} from '@/services/triggersApi'

const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const AGENT_SOURCES = ['claude', 'cursor', 'devin', 'antigravity', 'generic']
// Common built-in types — the textarea accepts any config JSON regardless.
const EXEC_ACTION_TYPES = [
  'url', 'program', 'command', 'hotkey', 'system', 'cross_platform',
  'http_request', 'multi_action', 'toggle', 'random',
]

const notifications = useNotificationsStore()

const triggers = ref<Trigger[]>([])
const engineEnabled = ref(true)
const loading = ref(true)
const error = ref('')
const testing = reactive(new Set<string>())
const confirmDeleteId = ref('')
const lastFired = reactive<Record<string, { ok: boolean; detail: string; ts: number }>>({})

// --------------------------------------------------------------------------
// list
// --------------------------------------------------------------------------

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    const state = await fetchTriggersState()
    engineEnabled.value = state.enabled
    triggers.value = state.triggers
  } catch {
    error.value = 'Could not load triggers'
  } finally {
    loading.value = false
  }
}

async function toggleEngine() {
  const next = !engineEnabled.value
  engineEnabled.value = next // optimistic
  try {
    engineEnabled.value = await setTriggersEnabled(next)
  } catch {
    engineEnabled.value = !next
    notifications.error('Triggers', 'Could not update the master switch.')
  }
}

onMounted(() => {
  void refresh()
  socketClient.on('trigger_fired', onTriggerFired)
})
onUnmounted(() => socketClient.off('trigger_fired', onTriggerFired))

function onTriggerFired(payload: { id?: string; ok?: boolean; detail?: string; ts?: number }) {
  if (!payload?.id) return
  lastFired[payload.id] = {
    ok: !!payload.ok,
    detail: String(payload.detail ?? ''),
    ts: payload.ts ?? Date.now() / 1000,
  }
}

// --------------------------------------------------------------------------
// summaries
// --------------------------------------------------------------------------

function eventSummary(event: TriggerEvent): string {
  switch (event.type) {
    case 'time': {
      const days = event.days?.length
        ? event.days.map((d) => DAY_NAMES[d]).join(' ')
        : 'daily'
      return `${event.at} ${days}`
    }
    case 'app_foreground':
      return `${event.exe} focused`
    case 'agent_state':
      return `${event.source} is ${event.state}`
    case 'webhook':
      return `webhook …/${event.key}`
    default:
      return event.type
  }
}

function actionSummary(action: TriggerAction): string {
  switch (action.type) {
    case 'show_notification':
      return `notify “${action.title}”`
    case 'switch_scene':
      return `switch to ${action.scene}`
    case 'execute_action':
      return `run ${action.action?.type ?? 'action'}`
    default:
      return action.type
  }
}

function ago(ts: number): string {
  const seconds = Math.max(0, Date.now() / 1000 - ts)
  if (seconds < 60) return `${Math.round(seconds)}s ago`
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.round(seconds / 3600)}h ago`
  return `${Math.round(seconds / 86400)}d ago`
}

// --------------------------------------------------------------------------
// row actions
// --------------------------------------------------------------------------

async function toggleEnabled(trigger: Trigger) {
  const next = !trigger.enabled
  trigger.enabled = next // optimistic — a failed save reverts below
  try {
    const saved = await updateTrigger(trigger.id, { enabled: next })
    Object.assign(trigger, saved)
  } catch {
    trigger.enabled = !next
    notifications.error('Trigger', 'Could not update the trigger.')
  }
}

async function fireTest(trigger: Trigger) {
  if (testing.has(trigger.id)) return
  testing.add(trigger.id)
  try {
    const result = await testTrigger(trigger.id)
    lastFired[trigger.id] = { ok: result.ok, detail: result.detail, ts: Date.now() / 1000 }
    if (result.ok) {
      notifications.success('Trigger fired', result.detail || trigger.label)
    } else {
      notifications.warning('Trigger failed', result.detail || 'The action did not run.')
    }
  } catch {
    notifications.error('Trigger', 'Test fire request failed.')
  } finally {
    testing.delete(trigger.id)
  }
}

let confirmTimer: ReturnType<typeof setTimeout> | undefined
function onDelete(trigger: Trigger) {
  // Two-tap confirm — no modal needed for a single row.
  if (confirmDeleteId.value !== trigger.id) {
    confirmDeleteId.value = trigger.id
    clearTimeout(confirmTimer)
    confirmTimer = setTimeout(() => { confirmDeleteId.value = '' }, 3000)
    return
  }
  clearTimeout(confirmTimer)
  confirmDeleteId.value = ''
  void doDelete(trigger)
}

async function doDelete(trigger: Trigger) {
  try {
    await removeTrigger(trigger.id)
    triggers.value = triggers.value.filter((t) => t.id !== trigger.id)
  } catch {
    notifications.error('Trigger', 'Could not delete the trigger.')
  }
}

// --------------------------------------------------------------------------
// add / edit form
// --------------------------------------------------------------------------

const formOpen = ref(false)
const editingId = ref<string | null>(null)
const saving = ref(false)
const formError = ref('')
const copied = ref(false)

const form = reactive({
  label: '',
  eventType: 'time' as TriggerEventType,
  at: '07:30',
  days: [] as number[],
  exe: '',
  source: 'claude',
  state: 'permission',
  key: '',
  actionType: 'show_notification' as TriggerActionType,
  execType: 'url',
  execConfig: '{}',
  scene: '',
  title: '',
  message: '',
})

const webhookUrl = computed(
  () => `${window.location.origin}/api/triggers/fire/${form.key || '<key>'}`,
)

function newWebhookKey(): string {
  const bytes = new Uint8Array(8)
  crypto.getRandomValues(bytes)
  return 'whk_' + Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
}

async function copyWebhookUrl() {
  try {
    await navigator.clipboard.writeText(`POST ${webhookUrl.value}`)
    copied.value = true
    setTimeout(() => { copied.value = false }, 1500)
  } catch {
    notifications.warning('Copy failed', 'Select and copy the URL manually.')
  }
}

function toggleDay(idx: number) {
  const i = form.days.indexOf(idx)
  if (i >= 0) form.days.splice(i, 1)
  else form.days.push(idx)
}

function resetForm() {
  form.label = ''
  form.eventType = 'time'
  form.at = '07:30'
  form.days = []
  form.exe = ''
  form.source = 'claude'
  form.state = 'permission'
  form.key = newWebhookKey()
  form.actionType = 'show_notification'
  form.execType = 'url'
  form.execConfig = '{}'
  form.scene = ''
  form.title = ''
  form.message = ''
  formError.value = ''
}

function openCreate() {
  editingId.value = null
  resetForm()
  formOpen.value = true
}

function openEdit(trigger: Trigger) {
  editingId.value = trigger.id
  resetForm()
  form.label = trigger.label
  form.eventType = trigger.event.type
  form.at = trigger.event.at ?? '07:30'
  form.days = [...(trigger.event.days ?? [])]
  form.exe = trigger.event.exe ?? ''
  form.source = trigger.event.source ?? 'claude'
  form.state = trigger.event.state ?? 'permission'
  form.key = trigger.event.key ?? newWebhookKey()
  form.actionType = trigger.action.type
  form.execType = trigger.action.action?.type ?? 'url'
  form.execConfig = JSON.stringify(trigger.action.action?.config ?? {}, null, 2)
  form.scene = trigger.action.scene ?? ''
  form.title = trigger.action.title ?? ''
  form.message = trigger.action.message ?? ''
  formOpen.value = true
}

function closeForm() {
  formOpen.value = false
  editingId.value = null
  formError.value = ''
}

function buildEvent(): TriggerEvent {
  switch (form.eventType) {
    case 'time':
      return {
        type: 'time',
        at: form.at,
        ...(form.days.length ? { days: [...form.days].sort() } : {}),
      }
    case 'app_foreground':
      return { type: 'app_foreground', exe: form.exe.trim() }
    case 'agent_state':
      return { type: 'agent_state', source: form.source, state: form.state }
    case 'webhook':
      return { type: 'webhook', key: form.key || newWebhookKey() }
  }
}

function buildAction(): TriggerAction | string {
  switch (form.actionType) {
    case 'show_notification':
      if (!form.title.trim()) return 'Give the notification a title.'
      return { type: 'show_notification', title: form.title.trim(), message: form.message }
    case 'switch_scene':
      if (!form.scene.trim()) return 'Name the scene to switch to.'
      return { type: 'switch_scene', scene: form.scene.trim() }
    case 'execute_action': {
      let config: Record<string, any> = {}
      if (form.execConfig.trim()) {
        try {
          const parsed = JSON.parse(form.execConfig)
          if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
            return 'Config must be a JSON object.'
          }
          config = parsed
        } catch {
          return 'Config is not valid JSON.'
        }
      }
      return { type: 'execute_action', action: { type: form.execType, config } }
    }
  }
}

async function save() {
  const action = buildAction()
  if (typeof action === 'string') {
    formError.value = action
    return
  }
  const event = buildEvent()
  saving.value = true
  formError.value = ''
  try {
    if (editingId.value) {
      // Partial patch — enabled is untouched so editing a disabled trigger
      // never silently re-arms it.
      const saved = await updateTrigger(editingId.value, {
        label: form.label.trim(),
        event,
        action,
      })
      const idx = triggers.value.findIndex((t) => t.id === editingId.value)
      if (idx >= 0) triggers.value[idx] = saved
    } else {
      const draft: TriggerDraft = {
        label: form.label.trim(),
        enabled: true,
        event,
        action,
      }
      triggers.value.push(await createTrigger(draft))
    }
    closeForm()
  } catch (e: any) {
    formError.value = e?.response?.data?.error || 'Could not save the trigger'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
/* Mirrors SettingsView's panel/row idiom, but self-contained: the variable
   block is duplicated so the panel still renders correctly outside
   .settings-app. */
.triggers-panel {
  --bg: #0a111f;
  --panel: #111c2f;
  --panel-2: #16233a;
  --field: #0d1728;
  --line: #1f2f4a;
  --line-soft: #172540;
  --text: #e9eff8;
  --text-2: #9fb0c9;
  --text-3: #7286a4;
  --accent: #4a8cff;
  --accent-2: #2f6fe0;
  --danger: #ff7a7a;
  --ok: #3ddc97;
  --r-md: 10px;
  --fs-xs: 0.79em;
  --fs-sm: 0.88em;
  --fs-md: 0.95em;
  --target: max(34px, calc(var(--min-touch-target, 40px) - 8px));
  --mono: ui-monospace, "Cascadia Mono", "JetBrains Mono", Consolas, monospace;

  border: 1px solid var(--line-soft);
  border-radius: 14px;
  background: var(--panel);
  color: var(--text);
  overflow: hidden;
}

.panel-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 10px;
  padding: 13px 18px 11px;
  border-bottom: 1px solid var(--line-soft);
}
.panel-head h2 {
  margin: 0;
  font-size: var(--fs-sm);
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.panel-head .hint { color: var(--text-3); font-size: var(--fs-sm); }
.panel-head .spacer { margin-left: auto; }

.panel-body { padding: 4px 18px 14px; }

.tp-empty { padding: 16px 0; color: var(--text-3); font-size: var(--fs-sm); }
.tp-bad { color: var(--danger); }

/* --- rows -------------------------------------------------------------- */

.tp-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid var(--line-soft);
}
.tp-row:last-of-type { border-bottom: 0; }
.tp-off .tp-row-text { opacity: 0.55; }
.tp-paused-chip {
  font-size: var(--fs-xs);
  font-weight: 700;
  letter-spacing: .04em;
  text-transform: uppercase;
  color: var(--warn, #e8a33d);
  border: 1px solid color-mix(in srgb, var(--warn, #e8a33d) 40%, transparent);
  border-radius: 99px;
  padding: 2px 9px;
}
.tp-row-text { min-width: 0; flex: 1 1 auto; }
.tp-label { display: block; font-size: var(--fs-md); font-weight: 560; }
.tp-row-text p { margin: 2px 0 0; color: var(--text-3); font-size: var(--fs-sm); }
.tp-fired { display: flex; align-items: center; gap: 6px; color: var(--ok) !important; }
.tp-fired.tp-bad { color: var(--danger) !important; }

.tp-row-ctl {
  flex: none;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

/* --- buttons / inputs (settings density, touch-friendly) ---------------- */

.tp-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: var(--target);
  padding: 0 14px;
  border-radius: var(--r-md);
  border: 1px solid var(--line);
  background: var(--panel-2);
  color: var(--text);
  font: inherit;
  font-size: var(--fs-sm);
  font-weight: 560;
  cursor: pointer;
  white-space: nowrap;
  touch-action: manipulation;
}
.tp-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
@media (hover: hover) and (pointer: fine) {
  .tp-btn:hover:not(:disabled) { background: #1b2b45; border-color: #2a3e60; }
}
.tp-btn:active:not(:disabled) { transform: scale(0.97); }
.tp-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.tp-btn.tp-sm { min-height: calc(var(--target) - 6px); padding: 0 10px; }
.tp-btn.tp-primary { background: var(--accent-2); border-color: #3c7ef0; color: #fff; }
.tp-btn.tp-icon { width: var(--target); padding: 0; }
.tp-btn.tp-icon.tp-sm { width: calc(var(--target) - 6px); }
.tp-btn.tp-danger { border-color: #5a2c33; color: var(--danger); }
.tp-btn.tp-danger:hover:not(:disabled) { background: rgba(255, 122, 122, 0.12); border-color: var(--danger); }

.tp-switch { display: inline-flex; align-items: center; min-height: calc(var(--target) - 6px); cursor: pointer; }
.tp-switch input { position: absolute; opacity: 0; width: 0; height: 0; }
.tp-track {
  position: relative;
  width: 46px;
  height: 26px;
  border-radius: 999px;
  background: #24344f;
  border: 1px solid #2c3f5f;
  transition: background 0.15s ease;
  flex: none;
}
.tp-track::after {
  content: "";
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #cfdcee;
  transition: transform 0.22s cubic-bezier(0.34, 1.3, 0.64, 1), background 0.15s ease;
}
.tp-switch input:checked + .tp-track { background: var(--accent-2); border-color: #4a86e8; }
.tp-switch input:checked + .tp-track::after { transform: translateX(20px); background: #fff; }
.tp-switch input:focus-visible + .tp-track { outline: 2px solid var(--accent); outline-offset: 2px; }

.tp-input, .tp-select {
  min-height: var(--target);
  padding: 0 12px;
  border-radius: var(--r-md);
  border: 1px solid var(--line);
  background: var(--field);
  color: var(--text);
  font: inherit;
  font-size: var(--fs-sm);
  width: 100%;
}
.tp-select {
  padding-right: 32px;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%237286a4' stroke-width='2' stroke-linecap='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  cursor: pointer;
}
.tp-input:focus-visible, .tp-select:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.tp-textarea { padding: 10px 12px; line-height: 1.5; resize: vertical; min-height: 72px; font-family: var(--mono); }

/* --- form ---------------------------------------------------------------- */

.tp-form {
  margin-top: 8px;
  padding: 14px;
  border-radius: var(--r-md);
  background: var(--panel-2);
  border: 1px solid var(--line-soft);
}
.tp-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 16px;
}
@media (max-width: 640px) {
  .tp-grid { grid-template-columns: 1fr; }
  .tp-span2 { grid-column: auto; }
}
.tp-field { display: flex; flex-direction: column; gap: 5px; min-width: 0; }
.tp-span2 { grid-column: span 2; }
.tp-field-label { font-size: var(--fs-sm); color: var(--text-2); font-weight: 560; }
.tp-note { font-size: var(--fs-xs); color: var(--text-3); font-weight: 400; }

.tp-days { display: flex; gap: 6px; flex-wrap: wrap; }
.tp-day {
  min-width: var(--target);
  min-height: var(--target);
  padding: 0 10px;
  border-radius: var(--r-md);
  border: 1px solid var(--line);
  background: var(--field);
  color: var(--text-2);
  font: inherit;
  font-size: var(--fs-sm);
  font-weight: 560;
  cursor: pointer;
  touch-action: manipulation;
}
.tp-day.tp-on { background: var(--accent-2); border-color: #3c7ef0; color: #fff; }
.tp-day:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

.tp-webhook { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.tp-url {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 8px 12px;
  border-radius: var(--r-md);
  border: 1px solid var(--line);
  background: var(--field);
  color: var(--text-2);
  font-family: var(--mono);
  font-size: var(--fs-xs);
}

.tp-form-err { margin: 10px 0 0; font-size: var(--fs-sm); }
.tp-form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 14px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}
</style>
