<template>
  <Teleport to="body">
    <Transition name="mc-fade">
      <div
        v-if="missionControlOpen"
        class="mc-backdrop"
        role="dialog"
        aria-modal="true"
        aria-label="Agent mission control"
        @click.self="closeMissionControl"
        @keydown.esc="closeMissionControl"
      >
        <section class="mc-panel" tabindex="-1" ref="panelEl">
          <header class="mc-head">
            <div class="mc-title">
              <FontAwesomeIcon :icon="['fas', 'satellite-dish']" />
              <h2>Mission Control</h2>
              <span v-if="snapshot.needs_you" class="mc-count" data-testid="mc-needs-count">
                {{ snapshot.needs_you }} need{{ snapshot.needs_you === 1 ? 's' : '' }} you
              </span>
            </div>
            <button type="button" class="mc-close" aria-label="Close mission control" @click="closeMissionControl">
              <FontAwesomeIcon :icon="['fas', 'times']" />
            </button>
          </header>

          <div class="mc-body">
            <p v-if="loadError" class="mc-error" role="alert">{{ loadError }}</p>

            <p v-else-if="loaded && !snapshot.sessions.length" class="mc-empty" data-testid="mc-empty">
              No agent sessions are reporting right now. Start Claude Code, Cursor
              or Codex with the VDock hook installed (Settings → Integrations →
              Agent alerts) and they appear here.
            </p>

            <section
              v-for="group in groups"
              :key="group.id"
              class="mc-group"
              :data-group="group.id"
            >
              <h3 class="mc-group-title" :class="`mc-g-${group.id}`">
                {{ group.title }}
                <span class="mc-group-n">{{ group.sessions.length }}</span>
              </h3>

              <article
                v-for="s in group.sessions"
                :key="rowKey(s)"
                class="mc-row"
                :class="`mc-state-${s.state}`"
                data-testid="mc-row"
              >
                <div class="mc-row-main">
                  <div class="mc-row-top">
                    <span class="mc-agent">{{ sourceLabelFor(s.source) }}</span>
                    <span class="mc-project">{{ s.project || folderOf(s.cwd) || 'unknown project' }}</span>
                    <span class="mc-chip" :class="`mc-chip-${s.state}`">{{ stateLabel(s) }}</span>
                    <span class="mc-idle" :title="'Time since the last event'">{{ idleFor(s) }}</span>
                  </div>
                  <span
                    v-if="s.usage"
                    class="mc-usage"
                    :class="`mc-usage-${s.usage.status}`"
                    :title="usageTitle(s.usage)"
                    data-testid="mc-usage"
                  >
                    {{ formatUsageCost(s.usage.cost_usd, s.usage.estimate) }} · ctx {{ s.usage.context_pct }}%
                  </span>
                  <p v-if="s.message && s.state === 'permission'" class="mc-line mc-ask">{{ s.message }}</p>
                  <p v-if="s.prompt" class="mc-line"><span class="mc-tag">You</span>{{ s.prompt }}</p>
                  <p v-if="s.reply" class="mc-line"><span class="mc-tag mc-tag-ai">Agent</span>{{ s.reply }}</p>

                  <button
                    v-if="changesOf(s)"
                    type="button"
                    class="mc-changes"
                    :aria-expanded="changesOpen === rowKey(s)"
                    data-testid="mc-changes"
                    @click="toggleChanges(s)"
                  >
                    <FontAwesomeIcon :icon="['fas', 'file-pen']" />
                    {{ changesLabel(changesOf(s)!) }}
                  </button>
                  <ul v-if="changesOpen === rowKey(s) && changesOf(s)" class="mc-files" data-testid="mc-files">
                    <li v-for="f in changesOf(s)!.files" :key="f.path">
                      <button type="button" class="mc-file" data-testid="mc-file" @click="openDiff(s, f.path)">
                        <span class="mc-file-path">{{ f.path }}</span>
                        <span class="mc-file-stat">+{{ f.added }} −{{ f.removed }}</span>
                      </button>
                    </li>
                  </ul>

                  <div v-if="promptOpen === rowKey(s)" class="mc-presets" data-testid="mc-presets">
                    <button
                      v-for="p in snapshot.presets"
                      :key="p.id"
                      type="button"
                      class="mc-btn mc-preset"
                      :disabled="isBusy(s)"
                      data-testid="mc-preset"
                      @click="sendPrompt(s, p)"
                    >
                      {{ p.label }}
                    </button>
                  </div>
                </div>

                <div class="mc-row-actions">
                  <button
                    v-if="s.can_prompt"
                    type="button"
                    class="mc-btn"
                    :disabled="isBusy(s)"
                    :aria-expanded="promptOpen === rowKey(s)"
                    data-testid="mc-prompt"
                    @click="promptOpen = promptOpen === rowKey(s) ? null : rowKey(s)"
                  >
                    <FontAwesomeIcon :icon="['fas', 'paper-plane']" /> Prompt
                  </button>
                  <button
                    v-if="canCompact(s)"
                    type="button"
                    class="mc-btn"
                    :disabled="isBusy(s)"
                    data-testid="mc-compact"
                    @click="compact(s)"
                  >
                    <FontAwesomeIcon :icon="['fas', 'compress']" /> Compact
                  </button>
                  <template v-if="s.can_decide">
                    <button
                      type="button"
                      class="mc-btn mc-approve"
                      :disabled="isBusy(s)"
                      data-testid="mc-approve"
                      @click="decide(s, 'approve')"
                    >
                      <FontAwesomeIcon :icon="['fas', 'check']" /> Approve
                    </button>
                    <button
                      type="button"
                      class="mc-btn mc-deny"
                      :disabled="isBusy(s)"
                      data-testid="mc-deny"
                      @click="decide(s, 'deny')"
                    >
                      <FontAwesomeIcon :icon="['fas', 'xmark']" /> Deny
                    </button>
                  </template>
                  <button
                    v-if="s.can_focus"
                    type="button"
                    class="mc-btn"
                    :disabled="isBusy(s)"
                    data-testid="mc-open"
                    @click="focus(s)"
                  >
                    <FontAwesomeIcon :icon="['fas', 'arrow-up-right-from-square']" /> Open
                  </button>
                </div>
              </article>
            </section>
          </div>

          <footer class="mc-foot">
            Approve / Deny answer the prompt in <em>that</em> session’s window (Claude Code).
            Other agents can be opened from here and answered there.
          </footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onUnmounted, reactive, ref, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import socketClient from '@/api/socket'
import { sourceLabelFor } from '@/services/agentAlerts'
import {
  closeMissionControl,
  compactMissionSession,
  decideMissionSession,
  formatUsageCost,
  fetchMission,
  focusMissionSession,
  fetchSessionChanges,
  formatIdle,
  groupMission,
  missionControlOpen,
  openSessionDiff,
  promptMissionSession,
  type MissionDecision,
  type MissionPreset,
  type MissionSession,
  type MissionSnapshot,
  type MissionUsage,
  type SessionChanges,
} from '@/services/missionControl'
import { useNotificationsStore } from '@/stores/notifications'

/**
 * DL-144 - one place for every live agent session, plus the approval inbox
 * (the "Needs your approval" section). Data comes from /api/agent-mission;
 * it refreshes on the `agent_state` socket event while open, with a slow
 * poll as a safety net and a 1 s ticker so "idle 4m" keeps counting.
 */

const notifications = useNotificationsStore()

const snapshot = ref<MissionSnapshot>({ sessions: [], presets: [], needs_you: 0, pending_approvals: 0 })
const loaded = ref(false)
const loadError = ref('')
const busy = reactive(new Set<string>())
const panelEl = ref<HTMLElement | null>(null)

const groups = computed(() => groupMission(snapshot.value.sessions))

// "now" for idle math - bumped each second while the panel is open.
const nowMs = ref(Date.now())
let fetchedAt = Date.now()
let ticker: ReturnType<typeof setInterval> | undefined
let poller: ReturnType<typeof setInterval> | undefined
let refreshTimer: ReturnType<typeof setTimeout> | undefined

function rowKey(s: MissionSession): string {
  return `${s.source}:${s.session_id}`
}

function folderOf(path: string): string {
  const parts = (path || '').split(/[\\/]/).filter(Boolean)
  return parts[parts.length - 1] ?? ''
}

function idleFor(s: MissionSession): string {
  return formatIdle(s.idle_seconds + (nowMs.value - fetchedAt) / 1000)
}

function stateLabel(s: MissionSession): string {
  if (s.state === 'permission') return 'Needs approval'
  if (s.state === 'working') return 'Working'
  return s.needs_you ? 'Ready for prompt' : 'Idle'
}

function isBusy(s: MissionSession): boolean {
  return busy.has(rowKey(s))
}

async function refresh() {
  try {
    snapshot.value = await fetchMission()
    fetchedAt = Date.now()
    nowMs.value = fetchedAt
    loadError.value = ''
  } catch {
    loadError.value = 'Could not load agent sessions.'
  } finally {
    loaded.value = true
  }
}

// DL-145: Prompt menu + "what changed this turn" for sessions that can be prompted.
const promptOpen = ref<string | null>(null)
const changesOpen = ref<string | null>(null)
const changes = reactive<Record<string, SessionChanges>>({})
const changesFetchedFor = new Map<string, number>()

function changesOf(s: MissionSession): SessionChanges | undefined {
  const entry = s.can_prompt ? changes[rowKey(s)] : undefined
  return entry && entry.totals.files > 0 ? entry : undefined
}

function changesLabel(c: SessionChanges): string {
  const n = c.totals.files
  return `${n} file${n === 1 ? '' : 's'} +${c.totals.added} −${c.totals.removed}`
}

async function loadChanges(s: MissionSession) {
  if (!s.can_prompt) return
  const key = rowKey(s)
  if (changesFetchedFor.get(key) === s.ts) return
  changesFetchedFor.set(key, s.ts)
  try {
    const result = await fetchSessionChanges(s.source, s.session_id)
    if (result.success) changes[key] = result
    else delete changes[key]
  } catch {
    delete changes[key]
  }
}

watch(() => snapshot.value.sessions, (sessions) => { sessions.forEach((s) => { void loadChanges(s) }) })

function toggleChanges(s: MissionSession) {
  changesOpen.value = changesOpen.value === rowKey(s) ? null : rowKey(s)
}

async function openDiff(s: MissionSession, path: string) {
  try {
    await openSessionDiff(s.source, s.session_id, path)
  } catch (error: any) {
    notifications.error('Could not open the diff', error?.response?.data?.error || 'The editor did not respond.')
  }
}

function usageTitle(usage: MissionUsage): string {
  const basis = usage.estimate
    ? 'Estimated at API list prices (subscription plans are not billed per token)'
    : 'Reported by Claude Code when the session closed'
  return `${basis}. Context: ${usage.context_pct}% of the window used.`
}

/** Offered once context is filling up (the server only accepts a ready Claude session). */
function canCompact(s: MissionSession): boolean {
  return s.source === 'claude' && s.can_prompt && !!s.usage && s.usage.status !== 'normal'
}

async function compact(s: MissionSession) {
  const key = rowKey(s)
  if (busy.has(key)) return
  busy.add(key)
  try {
    await compactMissionSession(s.source, s.session_id)
    notifications.success('Compacting context', `${sourceLabelFor(s.source)}${s.project ? ` - ${s.project}` : ''}`)
  } catch (error: any) {
    notifications.error(
      'Could not compact the session',
      error?.response?.data?.error || 'The session did not accept the command.',
      error?.response?.data?.details,
    )
  } finally {
    busy.delete(key)
    void refresh()
  }
}

async function sendPrompt(s: MissionSession, preset: MissionPreset) {
  const key = rowKey(s)
  if (busy.has(key)) return
  busy.add(key)
  try {
    await promptMissionSession(s.source, s.session_id, preset.id)
    notifications.success(preset.label, `${sourceLabelFor(s.source)}${s.project ? ` - ${s.project}` : ''}`)
    promptOpen.value = null
  } catch (error: any) {
    notifications.error(
      'Could not send the prompt',
      error?.response?.data?.error || 'The session did not accept the prompt.',
      error?.response?.data?.details,
    )
  } finally {
    busy.delete(key)
    void refresh()
  }
}

function scheduleRefresh() {
  clearTimeout(refreshTimer)
  refreshTimer = setTimeout(() => { void refresh() }, 150)
}

async function decide(s: MissionSession, decision: MissionDecision) {
  const key = rowKey(s)
  if (busy.has(key)) return
  busy.add(key)
  try {
    await decideMissionSession(s.source, s.session_id, decision)
    notifications.success(
      decision === 'approve' ? 'Approved' : 'Denied',
      `${sourceLabelFor(s.source)}${s.project ? ` - ${s.project}` : ''}`,
    )
  } catch (error: any) {
    notifications.error(
      'Could not answer the prompt',
      error?.response?.data?.error || 'The session did not accept the answer.',
      error?.response?.data?.details,
    )
  } finally {
    busy.delete(key)
    void refresh()
  }
}

async function focus(s: MissionSession) {
  const key = rowKey(s)
  if (busy.has(key)) return
  busy.add(key)
  try {
    await focusMissionSession(s.source, s.session_id)
  } catch (error: any) {
    notifications.error(
      'Could not open the session',
      error?.response?.data?.error || 'No window was found for that session.',
    )
  } finally {
    busy.delete(key)
  }
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') closeMissionControl()
}

function onStateEvent() {
  if (missionControlOpen.value) scheduleRefresh()
}

watch(missionControlOpen, (open) => {
  if (open) {
    loaded.value = false
    void refresh()
    ticker = setInterval(() => { nowMs.value = Date.now() }, 1000)
    poller = setInterval(() => { void refresh() }, 15_000)
    socketClient.on('agent_state', onStateEvent)
    window.addEventListener('keydown', onKey)
    queueMicrotask(() => panelEl.value?.focus())
  } else {
    clearInterval(ticker)
    clearInterval(poller)
    clearTimeout(refreshTimer)
    socketClient.off('agent_state', onStateEvent)
    window.removeEventListener('keydown', onKey)
  }
}, { immediate: true })

onUnmounted(() => {
  clearInterval(ticker)
  clearInterval(poller)
  clearTimeout(refreshTimer)
  socketClient.off('agent_state', onStateEvent)
  window.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.mc-backdrop {
  position: fixed;
  inset: 0;
  z-index: 31000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(8px, 2.5vh, 28px);
  background: rgba(4, 8, 16, 0.72);
  -webkit-backdrop-filter: blur(6px);
  backdrop-filter: blur(6px);
}

.mc-panel {
  width: min(880px, 100%);
  max-height: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 18px;
  background: #0f1829;
  border: 1px solid #243556;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.6);
  color: #e9eff8;
  outline: none;
  overflow: hidden;
}

.mc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: clamp(10px, 2vh, 16px) clamp(14px, 2.4vw, 22px);
  border-bottom: 1px solid #1f2f4a;
}
.mc-title { display: flex; align-items: center; gap: 12px; min-width: 0; color: #7fb0ff; }
.mc-title h2 { margin: 0; font-size: clamp(1rem, 2.6vh, 1.25rem); color: #e9eff8; letter-spacing: 0.02em; }
.mc-count {
  font-size: 0.8rem;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 999px;
  color: #ffd89e;
  background: rgba(245, 165, 36, 0.16);
  border: 1px solid rgba(245, 165, 36, 0.5);
  white-space: nowrap;
}
.mc-close {
  flex: none;
  width: 40px; height: 40px;
  border-radius: 10px;
  border: 1px solid #243556;
  background: #16233a;
  color: #cfdcee;
  cursor: pointer;
  touch-action: manipulation;
}

.mc-body { padding: clamp(8px, 1.6vh, 14px) clamp(14px, 2.4vw, 22px); overflow-y: auto; flex: 1 1 auto; }
.mc-empty, .mc-error { margin: 18px 0; color: #9fb0c9; line-height: 1.55; }
.mc-error { color: #ff8f8f; }

.mc-group { margin-bottom: 14px; }
.mc-group-title {
  display: flex; align-items: center; gap: 8px;
  margin: 8px 0;
  font-size: 0.78rem; font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase;
  color: #7286a4;
}
.mc-g-approval { color: #ffb84d; }
.mc-g-waiting { color: #6fd4a3; }
.mc-group-n {
  font-size: 0.72rem; padding: 1px 8px; border-radius: 999px;
  background: #16233a; color: #9fb0c9; letter-spacing: 0;
}

.mc-row {
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 14px;
  padding: 12px 14px;
  margin-bottom: 8px;
  border-radius: 12px;
  background: #121f35;
  border: 1px solid #1f2f4a;
}
.mc-state-permission {
  border-color: rgba(245, 165, 36, 0.65);
  background: linear-gradient(0deg, rgba(245, 165, 36, 0.07), rgba(245, 165, 36, 0.07)), #121f35;
}
.mc-row-main { min-width: 0; flex: 1 1 auto; }
.mc-row-top { display: flex; align-items: center; flex-wrap: wrap; gap: 8px 10px; }
.mc-agent { font-weight: 700; }
.mc-project { color: #9fb0c9; font-size: 0.92rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 36ch; }
.mc-idle { margin-left: auto; color: #7286a4; font-size: 0.82rem; font-variant-numeric: tabular-nums; }
.mc-chip {
  font-size: 0.72rem; font-weight: 700; padding: 2px 9px; border-radius: 999px;
  background: #1b2b45; color: #9fb0c9; white-space: nowrap;
}
.mc-chip-permission { background: rgba(245, 165, 36, 0.18); color: #ffd89e; }
.mc-chip-working { background: rgba(74, 140, 255, 0.18); color: #9cc2ff; }
.mc-chip-ready { background: rgba(61, 220, 151, 0.16); color: #7fe6b6; }

.mc-line {
  margin: 6px 0 0;
  color: #b9c7dc;
  font-size: 0.88rem;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.mc-ask { color: #ffd89e; font-weight: 600; }
.mc-tag {
  display: inline-block; margin-right: 8px; padding: 0 6px; border-radius: 4px;
  font-size: 0.68rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;
  background: #1b2b45; color: #9fb0c9; vertical-align: 1px;
}
.mc-tag-ai { background: rgba(74, 140, 255, 0.2); color: #9cc2ff; }

.mc-row-actions { flex: none; display: flex; flex-direction: column; justify-content: center; gap: 8px; min-width: 112px; }
.mc-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  min-height: 44px; padding: 0 14px;
  border-radius: 10px; border: 1px solid #2a3e60; background: #16233a; color: #e9eff8;
  font: inherit; font-size: 0.92rem; font-weight: 600; cursor: pointer; touch-action: manipulation; white-space: nowrap;
}
.mc-btn:active:not(:disabled) { transform: scale(0.97); }
.mc-btn:disabled { opacity: 0.5; cursor: progress; }
.mc-approve { background: #1c7a4d; border-color: #2fb374; }
.mc-deny { background: #6b2630; border-color: #b4414f; }

.mc-changes {
  display: inline-flex; align-items: center; gap: 8px; margin-top: 8px;
  min-height: 36px; padding: 0 12px; border-radius: 999px;
  border: 1px solid #2a3e60; background: #16233a; color: #b9c7dc;
  font: inherit; font-size: 0.82rem; font-weight: 600; cursor: pointer; touch-action: manipulation;
}
.mc-usage {
  display: inline-block; margin-top: 8px; padding: 2px 10px; border-radius: 999px;
  border: 1px solid #2a3e60; background: #16233a; color: #b9c7dc;
  font-size: 0.8rem; font-weight: 600; font-variant-numeric: tabular-nums;
}
.mc-usage-warning { border-color: rgba(245, 165, 36, 0.6); background: rgba(245, 165, 36, 0.16); color: #ffd89e; }
.mc-usage-critical { border-color: rgba(220, 70, 70, 0.7); background: rgba(220, 70, 70, 0.18); color: #ffb0b0; }
.mc-files { list-style: none; margin: 6px 0 0; padding: 0; display: grid; gap: 4px; }
.mc-file {
  width: 100%; display: flex; justify-content: space-between; gap: 12px; align-items: center;
  min-height: 40px; padding: 0 12px; border-radius: 8px;
  border: 1px solid #1f2f4a; background: #0f1829; color: #cfdcee;
  font: inherit; font-size: 0.84rem; text-align: left; cursor: pointer; touch-action: manipulation;
}
.mc-file-path { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mc-file-stat { flex: none; color: #7fe6b6; font-variant-numeric: tabular-nums; }
.mc-presets { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.mc-preset { min-height: 40px; }

.mc-foot { padding: 10px clamp(14px, 2.4vw, 22px); border-top: 1px solid #1f2f4a; color: #7286a4; font-size: 0.78rem; }

.mc-fade-enter-active, .mc-fade-leave-active { transition: opacity 0.16s ease; }
.mc-fade-enter-from, .mc-fade-leave-to { opacity: 0; }

@media (max-width: 560px) {
  .mc-row { flex-direction: column; }
  .mc-row-actions { flex-direction: row; min-width: 0; }
  .mc-row-actions .mc-btn { flex: 1; }
}
</style>
