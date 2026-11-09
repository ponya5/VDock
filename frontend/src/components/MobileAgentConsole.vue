<template>
  <section
    class="mobile-agent-console"
    :class="[`state-${displayState}`, { 'is-linked': !!linkAccent }]"
    :style="linkAccent ? { '--link-accent': linkAccent } : undefined"
    :aria-label="`${agentName} console`"
  >
    <div class="mac-side">
    <AgentStatusBanner
      variant="card"
      :state="displayState"
      :agent-name="agentName"
      :detail="statusLine"
      :since-ms="sinceMs"
      :linked="linked"
      :link-accent="linkAccent"
      :others-summary="othersSummary"
    >
      <!-- Session targeting (DL-071): a single chip that opens the shared
           listbox sheet - the old wrap-visible chip strip ate a whole row
           of the status card once several sessions were live. -->
      <AgentSessionPicker
        v-if="showSessionPicker"
        class="mac-target"
        :rows="targetRows"
        :pinned-pid="pinnedPid"
        :resolved-pid="resolvedPid"
        :waiting-glow-on="waitingGlowOn"
        :target-label="targetLabel"
        :effective-session="effectiveSession"
        :linked-accent="linkAccent"
        :linked-badge="linked?.badge"
        @pick="chooseTarget"
        @identify="identify"
        @opened="refreshTargets"
      />
      <!-- Only when the picker is absent - otherwise it duplicates the
           session chip's label (both read the project dir name). -->
      <span v-else-if="projectName" class="mac-project" :title="stateEntry?.cwd">
        <FontAwesomeIcon :icon="['fas', 'folder-open']" />
        {{ projectName }}
      </span>
    </AgentStatusBanner>

    <div
      v-if="isAgentPossiblyRunning && visibleActions.length > 0"
      class="mac-actions"
      :class="{ 'emphasizes-primary': emphasizesPrimaryAction }"
      :style="{ '--secondary-action-count': Math.max(visibleActions.length - 1, 1), '--action-count': visibleActions.length }"
    >
      <span v-if="linked" class="mac-actions-for" data-testid="actions-for">
        <FontAwesomeIcon :icon="['fas', 'link']" /> acts on {{ linked.label }}
      </span>
      <button
        v-for="action in visibleActions"
        :key="action.id"
        type="button"
        class="mac-action"
        :class="{ primary: action.isPrimary }"
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

    <div class="mac-main">
    <!-- DL-166: Groups / All switch, only when the scene splits into 2+ categories. -->
    <div v-if="showViewToggle" class="mac-shortcuts-head">
      <span class="mac-shortcuts-title">Shortcuts</span>
      <AgentViewToggle :model-value="agentView.mode.value" always-labels @update:model-value="agentView.setMode" />
    </div>
    <AgentCategoryRail
      v-if="showsGroups"
      :groups="railGroups"
      :selected="selectedId"
      :badge="sessionBadge"
      orientation="horizontal"
      @select="agentView.setCategory"
    />

    <div
      v-if="visibleShortcuts.length > 0"
      id="agent-cat-panel"
      ref="tilesEl"
      class="mac-shortcuts"
      :style="fitStyle"
      :class="{ 'in-groups': showsGroups, compact: (fit?.rowH ?? 99) < 64 }"
      :role="showsGroups ? 'tabpanel' : undefined"
      :aria-labelledby="showsGroups && selectedId ? `agent-cat-tab-${selectedId}` : undefined"
      aria-label="Shortcuts"
    >
      <button
        v-for="shortcut in visibleShortcuts"
        :key="shortcut.button.id"
        type="button"
        :class="[isQuiet(shortcut) ? 'mac-link' : 'mac-shortcut', { highlighted: shortcut.isHighlighted }]"
        :disabled="runningShortcutId !== null"
        :title="shortcut.button.tooltip || shortcut.label"
        @click="runShortcut(shortcut)"
      >
        <FontAwesomeIcon
          :icon="runningShortcutId === shortcut.button.id ? ['fas', 'spinner'] : shortcut.icon"
          :spin="runningShortcutId === shortcut.button.id"
          :class="isQuiet(shortcut) ? undefined : 'mac-shortcut-icon'"
        />
        <span :class="isQuiet(shortcut) ? undefined : 'mac-shortcut-label'">{{ shortcut.label }}</span>
      </button>
    </div>

    <!-- Web links (url-type buttons like claude.ai): they open a browser,
         they do not drive the session — kept aside from the action tiles
         and styled as quiet outline pills so they can't be mistaken for
         one. Rendered last so actions never reflow around them. -->
    <div v-if="visibleLinks.length > 0" class="mac-links" aria-label="Web links">
      <button
        v-for="link in visibleLinks"
        :key="link.button.id"
        type="button"
        class="mac-link"
        :disabled="runningShortcutId !== null"
        :title="link.button.tooltip || link.label"
        @click="runShortcut(link)"
      >
        <FontAwesomeIcon
          :icon="runningShortcutId === link.button.id ? ['fas', 'spinner'] : link.icon"
          :spin="runningShortcutId === link.button.id"
        />
        <span>{{ link.label }}</span>
      </button>
    </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, toRef, watch, watchEffect } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { Button, Scene } from '@/types'
import { useDashboardStore } from '@/stores/dashboard'
import { useNotificationsStore } from '@/stores/notifications'
import { useSettingsStore } from '@/stores/settings'
import type { AgentStateName } from '@/api/appProfiles'
import { trackAgentSurfaceVisibility, useAgentSession } from '@/composables/useAgentSession'
import { profileSessionMarker, useAgentTargets } from '@/composables/useAgentTargets'
import { isAgentWaitingDismissed } from '@/services/agentWaiting'
import { normalizeFaIcon } from '@/utils/normalizeFaIcon'
import { vibrate } from '@/utils/haptics'
import AgentSessionPicker from '@/components/AgentSessionPicker.vue'
import AgentStatusBanner from '@/components/AgentStatusBanner.vue'
import AgentViewToggle from '@/components/AgentViewToggle.vue'
import AgentCategoryRail from '@/components/AgentCategoryRail.vue'
import { selectedCategoryId, useAgentSceneView } from '@/composables/useAgentSceneView'
import { useAgentStateSince } from '@/composables/useAgentStateSince'
import { AGENT_CATEGORIES, PAGE_NAVIGATION_ACTIONS, resolveButtonCategory, type CategoryGroup } from '@/utils/agentCategories'
import { summarizeOtherSessions, toAgentState } from '@/utils/agentSessionSummary'

/**
 * Mobile agent console (DL-065): a portrait phone surface for driving a
 * coding agent running on the PC — its live state, the actions that fit the
 * moment, the target-session chips (DL-071), and the scene's shortcuts.
 *
 * There is deliberately no free-text composer and no conversation card: a
 * phone's on-screen keyboard eats most of the screen for a control surface
 * that's meant to be a quick tap away (DL-069 follow-up), and nobody reads
 * agent replies on the deck — the hook's detail line ("needs permission to
 * use Bash") shows in the status card instead. Free-text prompting stays a
 * desktop-only affordance, driven from the scene's own buttons via
 * `runShortcut` below.
 */

interface ConsoleShortcut {
  button: Button
  label: string
  icon: [string, string]
  isHighlighted: boolean
  isLink: boolean
}

const props = defineProps<{ scene: Scene | null }>()

/** Scene buttons that start the agent — highlighted while it isn't running. */
const LAUNCH_ACTIONS = new Set(['claude_continue', 'program'])
/** Buttons that open something OUTSIDE the session — web pages (url) and
    app/web launchers (claude_open → claude.ai / desktop app). They render
    in the links strip, not among session-driving action tiles. */
const WEB_LINK_ACTIONS = new Set(['url', 'claude_open'])

const dashboardStore = useDashboardStore()
const notificationsStore = useNotificationsStore()
const settingsStore = useSettingsStore()
// DL-165: the linked session's own state drives the actions (set below once the session list is known).
const stateOverride = ref<AgentStateName | null>(null)
const {
  profile,
  stateEntry,
  currentState,
  stateLabel,
  isAgentDetected,
  isAgentPossiblyRunning,
  visibleActions,
  runningActionId,
  runAction,
} = useAgentSession(toRef(props, 'scene'), stateOverride)

const runningShortcutId = ref<string | null>(null)

// DL-071: which live CLI session the actions/shortcuts drive. The chip strip
// shows whenever at least one session is detected (or a pin is set) so the
// current target is always visible — it only vanishes with zero sessions.
const sessionMarker = computed(() => profileSessionMarker(profile.value))
const {
  sessionRows: targetRows,
  pinnedPid,
  resolvedPid,
  effectiveSession,
  targetLabel,
  refresh: refreshTargets,
  setTarget,
  identify,
} = useAgentTargets(sessionMarker)

// DL-165: which session the actions are linked to (shown in its colour) and what the others are doing.
const linked = computed(() => targetRows.value.find(r => r.pid === effectiveSession.value?.pid) ?? null)
watchEffect(() => { stateOverride.value = linked.value ? toAgentState(linked.value.state) : null })
const linkAccent = computed(() => linked.value?.accent ?? null)
const othersSummary = computed(() => summarizeOtherSessions(targetRows.value, linked.value?.pid))

const showSessionPicker = computed(() =>
  Boolean(sessionMarker.value) &&
  (targetRows.value.length > 0 || pinnedPid.value !== null)
)

// DL-080: idle sessions get the same waiting cue the desktop bar gives —
// the phone's chip strip is where the "which session wants me" lands. A
// snoozed episode quiets the ring until the next ready event.
const waitingGlowOn = computed(() =>
  settingsStore.agentWaitingGlowEnabled !== false &&
  !isAgentWaitingDismissed(profile.value?.status_source)
)

async function chooseTarget(pid: number | null): Promise<void> {
  vibrate(10)
  // Arming a session flashes its real window — on a phone there's no room
  // to *describe* which terminal a chip is, so the terminal itself waves.
  if (pid !== null && pid !== pinnedPid.value) void identify(pid)
  // Tapping the pinned session releases it — same as tapping Auto.
  await setTarget(pid === pinnedPid.value ? null : pid)
}

const agentName = computed(() => profile.value?.label ?? props.scene?.name ?? 'Agent')
const projectName = computed(() => stateEntry.value?.project ?? '')

/** Status line: the hook's detail message when it has one ("needs permission
    to use Bash", the current task), else the generic state label. */
// "No open session" whenever nothing about the agent is observable — no
// detected process AND no hook state entry. Deliberately stronger than
// isAgentPossiblyRunning: with app scanning off the label is a guess
// anyway, and "Status unavailable" read as broken rather than "nothing
// to drive" (mobile-only wording; the desktop bar keeps its own).
// A live session in the target list is observable too (DL-007): without the
// agent hook and with app scanning off, the card said "No open session"
// right next to its own chip naming that session.
const hasLiveSession = computed(() => targetRows.value.length > 0)
const statusLine = computed(() => {
  if (!stateEntry.value && hasLiveSession.value) return 'Session running'
  if (profile.value && !stateEntry.value && !isAgentDetected.value) return 'No open session'
  // Blank falls through to the banner's own copy for the state.
  return stateEntry.value?.message || ''
})

const displayState = computed(() => (isAgentPossiblyRunning.value ? currentState.value : 'offline'))
const sinceMs = useAgentStateSince(
  computed(() => `${profile.value?.status_source ?? 'agent'}:${linked.value?.pid ?? 'all'}`),
  displayState,
)

/**
 * Interrupt (working) and Approve (permission) are the one thing to press;
 * while the agent is ready, the actions/shortcuts below are the primary
 * control instead of a composer (see the top-of-file note on why there
 * isn't one).
 */
const emphasizesPrimaryAction = computed(() =>
  currentState.value === 'working' || currentState.value === 'permission'
)

function shortcutLabel(button: Button): string {
  return button.layers?.label?.text || button.label || button.tooltip || ''
}

const shortcuts = computed<ConsoleShortcut[]>(() => {
  const pages = props.scene?.pages ?? []
  return pages
    .flatMap(page => page.buttons)
    .filter(button =>
      button.enabled !== false &&
      Boolean(button.action) &&
      !PAGE_NAVIGATION_ACTIONS.has(button.action?.type ?? '') &&
      Boolean(shortcutLabel(button))
    )
    .map(button => ({
      button,
      label: shortcutLabel(button),
      icon: normalizeFaIcon(button.layers?.icon?.value ?? button.icon),
      isHighlighted:
        !isAgentPossiblyRunning.value && LAUNCH_ACTIONS.has(button.action?.type ?? ''),
      isLink: WEB_LINK_ACTIONS.has(button.action?.type ?? ''),
    }))
})

/** Session-driving scene buttons — the tile grid. */
const shortcutTiles = computed(() => shortcuts.value.filter(s => !s.isLink))
/** Web links (claude.ai & friends) — rendered apart, styled differently. */
const linkShortcuts = computed(() => shortcuts.value.filter(s => s.isLink))

// DL-166: the shortcuts split into categories (Groups) or show whole (All).
const agentView = useAgentSceneView(computed(() => props.scene?.id))
const shortcutGroups = computed(() => {
  const buckets = new Map<string, ConsoleShortcut[]>()
  for (const shortcut of shortcuts.value) {
    const id = resolveButtonCategory(shortcut.button)
    buckets.set(id, [...(buckets.get(id) ?? []), shortcut])
  }
  return AGENT_CATEGORIES.filter(def => buckets.has(def.id)).map(def => ({ ...def, items: buckets.get(def.id)! }))
})
const railGroups = computed<CategoryGroup[]>(() =>
  shortcutGroups.value.map(g => ({ id: g.id, label: g.label, icon: g.icon, buttons: g.items.map(i => i.button) })))
const showViewToggle = computed(() => shortcutGroups.value.length >= 2)
const showsGroups = computed(() => showViewToggle.value && agentView.mode.value === 'groups')
const selectedId = computed(() => selectedCategoryId(agentView.category.value, shortcutGroups.value))
const visibleShortcuts = computed(() =>
  showsGroups.value
    ? shortcutGroups.value.find(g => g.id === selectedId.value)?.items ?? []
    : shortcutTiles.value)
/** In Groups the links are a category, so the separate strip is not rendered. */
const visibleLinks = computed(() => (showsGroups.value ? [] : linkShortcuts.value))
/** Web links (and the whole Links category) keep the quiet outline-pill style. */
function isQuiet(shortcut: ConsoleShortcut): boolean {
  return shortcut.isLink || (showsGroups.value && selectedId.value === 'links')
}
const sessionBadge = computed<'working' | 'permission' | null>(() =>
  displayState.value === 'working' || displayState.value === 'permission' ? displayState.value : null)

async function runShortcut(shortcut: ConsoleShortcut): Promise<void> {
  if (runningShortcutId.value) return
  vibrate(10)
  runningShortcutId.value = shortcut.button.id
  try {
    const result = await dashboardStore.executeButtonAction(shortcut.button)
    if (result && !result.success) {
      notificationsStore.error(
        `${shortcut.label} failed`,
        result.message || 'The action did not run',
        result.details || undefined,
      )
    }
  } finally {
    runningShortcutId.value = null
  }
}

// Fit the tiles to the room: pick a column count so every tile fits without
// scrolling, with a readable minimum size; only when even that cannot fit does
// the region scroll. Rows get an explicit height so tiles never balloon.
const tilesEl = ref<HTMLElement | null>(null)
const fit = ref<{ cols: number; rowH: number } | null>(null)
const FIT_GAP = 8
function computeFit(): void {
  const el = tilesEl.value
  const n = visibleShortcuts.value.length
  if (!el || n === 0) { fit.value = null; return }
  const landscape = window.innerWidth > window.innerHeight
  const W = el.clientWidth
  const H = el.clientHeight
  const minW = landscape ? 96 : 84
  const minH = 48
  const maxH = 92
  let best: { cols: number; rowH: number; score: number } | null = null
  for (let cols = 1; cols <= n; cols++) {
    const rows = Math.ceil(n / cols)
    const tw = (W - FIT_GAP * (cols - 1)) / cols
    const th = (H - FIT_GAP * (rows - 1)) / rows
    if (tw < minW || th < minH) continue
    const score = Math.min(tw, 170) * Math.min(th, maxH)
    if (!best || score > best.score) best = { cols, rowH: Math.min(th, maxH), score }
  }
  if (!best) {
    // Cannot fit: most columns that still respect the minimum width; scroll vertically.
    const cols = Math.max(1, Math.min(n, Math.floor((W + FIT_GAP) / (minW + FIT_GAP))))
    best = { cols, rowH: minH, score: 0 }
  }
  fit.value = { cols: best.cols, rowH: Math.floor(best.rowH) }
}
const fitStyle = computed(() => fit.value
  ? { gridTemplateColumns: `repeat(${fit.value.cols}, minmax(0, 1fr))`, gridAutoRows: `${fit.value.rowH}px` }
  : undefined)
let fitObserver: ResizeObserver | null = null
onMounted(() => {
  if (typeof ResizeObserver !== 'undefined') {
    fitObserver = new ResizeObserver(() => computeFit())
    if (tilesEl.value) fitObserver.observe(tilesEl.value)
  }
  void nextTick(computeFit)
})
onBeforeUnmount(() => fitObserver?.disconnect())
watch(tilesEl, (el, prev) => {
  if (prev) fitObserver?.unobserve(prev)
  if (el) fitObserver?.observe(el)
  void nextTick(computeFit)
})
watch(() => visibleShortcuts.value.length, () => void nextTick(computeFit))

trackAgentSurfaceVisibility(
  computed(() => profile.value?.status_source),
  computed(() => isAgentPossiblyRunning.value),
)
</script>

<style scoped>
.mobile-agent-console {
  --agent-accent: #94a3b8;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 10px 12px calc(10px + env(safe-area-inset-bottom, 0px));
  color: #e5e7eb;
}

/* Two regions: status + state actions (.mac-side) and the shortcuts (.mac-main).
   Portrait stacks them; a landscape phone puts them side by side so the tiles
   get the full height and nothing needs scrolling. */
.mac-side {
  flex: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}
.mac-main {
  flex: 1;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mobile-agent-console.state-ready { --agent-accent: #22c55e; }
.mobile-agent-console.state-working { --agent-accent: #38bdf8; }
.mobile-agent-console.state-permission { --agent-accent: #f59e0b; }
.mobile-agent-console.state-unknown { --agent-accent: #94a3b8; }
.mobile-agent-console.state-offline { --agent-accent: #64748b; }

/* --- Status card: see AgentStatusBanner (DL-166) -------------------------------- */
.mac-project {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 40%;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  font-size: clamp(0.72rem, 0.68rem + 0.3vw, 0.85rem);
  color: rgba(255, 255, 255, 0.7);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* --- Session targeting (DL-071) --------------------------------------------- */
/* The shared picker's chip hugs the right edge of the status card, exactly
   where the old wrap-strip lived. On wrap it right-aligns on the second
   line, which reads fine as a trailing control. */
.mac-target {
  margin-left: auto;
}

/* --- State actions ------------------------------------------------------------ */
/* One compact row of icon-over-label buttons; an urgent primary action
   gets a full-width row of its own. */
.mac-actions {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(var(--action-count, 3), minmax(0, 1fr));
  gap: 8px;
}

.mac-action {
  min-width: 0;
  overflow: hidden;
  -webkit-user-select: none;
  user-select: none;
  min-height: 60px;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 6px 4px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(15, 20, 28, 0.78);
  color: inherit;
  font-size: clamp(0.74rem, 0.7rem + 0.3vw, 0.88rem);
  font-weight: 600;
  line-height: 1.15;
  text-align: center;
  touch-action: manipulation;
  cursor: pointer;
}

.mac-action > svg {
  font-size: 1.3em;
  flex: none;
}
.mac-action > span {
  min-width: 0;
  max-width: 100%;
  overflow-wrap: anywhere;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}

.mac-action.primary {
  background: var(--agent-accent);
  border-color: transparent;
  color: #0b1015;
}

.mac-actions.emphasizes-primary {
  grid-template-columns: repeat(var(--secondary-action-count), minmax(0, 1fr));
}

.emphasizes-primary .mac-action.primary {
  grid-column: 1 / -1;
  flex-direction: row;
  gap: 10px;
  font-size: clamp(0.95rem, 0.9rem + 0.4vw, 1.1rem);
}

.mac-action:active:not(:disabled) { transform: scale(0.97); }
.mac-action:disabled { opacity: 0.6; cursor: default; }

/* --- Shortcuts --------------------------------------------------------------- */
/* A wrapping grid instead of a horizontal-scroll pill row (DL-069 follow-up):
   a scrolling row hides however many buttons don't fit the first screenful,
   with no visual hint more exist — every shortcut needs to be visible and
   reachable at once, on any phone width, without discovering a scrollbar.
   `auto-fit`/`minmax` reflows the tile count per row to whatever the screen
   actually fits, wrapping to more rows rather than ever hiding a button. */
.mac-shortcuts {
  flex: 1 1 auto;
  min-height: 0;
  display: grid;
  /* JS (computeFit) overrides columns and row height so every tile fits. */
  grid-template-columns: repeat(auto-fit, minmax(84px, 1fr));
  grid-auto-rows: 68px;
  align-content: start;
  gap: 8px;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.mac-shortcut {
  -webkit-user-select: none;
  user-select: none;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 4px 6px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.08);
  color: inherit;
  font-size: clamp(0.8rem, 0.75rem + 0.35vw, 0.95rem);
  font-weight: 600;
  line-height: 1.2;
  text-align: center;
  touch-action: manipulation;
  cursor: pointer;
}

.mac-shortcut-icon {
  font-size: 1.35em;
}

.mac-shortcut-label {
  min-width: 0;
  max-width: 100%;
  overflow-wrap: anywhere;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}
.mac-shortcuts.compact .mac-shortcut { flex-direction: row; gap: 8px; padding: 4px 10px; }
.mac-shortcuts.compact .mac-shortcut-icon { flex: none; }

.mac-shortcut.highlighted {
  border-color: var(--agent-accent);
  background: color-mix(in srgb, var(--agent-accent) 28%, transparent);
}

.mac-shortcut:active:not(:disabled) { transform: scale(0.96); }
.mac-shortcut:disabled { opacity: 0.6; cursor: default; }

/* --- DL-166: Groups / All header and the grouped tile region ---------------------- */
.mac-shortcuts-head {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.mac-shortcuts-title {
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.6);
}
/* Links inside the tile grid keep their pill look, centred. */
.mac-shortcuts .mac-link {
  justify-content: center;
}

/* --- Web links (claude.ai & friends) ----------------------------------------
   url-type scene buttons open a browser — they don't touch the session, so
   they render apart from the action tiles as quiet outline pills: dashed
   slate border, dimmed label, no accent fill. */
.mac-links {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mac-link {
  -webkit-user-select: none;
  user-select: none;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px dashed rgba(148, 163, 184, 0.45);
  background: rgba(148, 163, 184, 0.08);
  color: #a8b3c7;
  font-size: clamp(0.74rem, 0.7rem + 0.3vw, 0.88rem);
  font-weight: 600;
  touch-action: manipulation;
  cursor: pointer;
}

.mac-link:active:not(:disabled) { transform: scale(0.96); }
.mac-link:disabled { opacity: 0.6; cursor: default; }

/* Landscape phones: status + actions on the left, shortcuts on the right. */
@media (orientation: landscape) and (max-height: 520px) {
  .mobile-agent-console {
    flex-direction: row;
    gap: 10px;
    overflow: hidden;
    padding: 6px calc(10px + env(safe-area-inset-right, 0px)) calc(6px + env(safe-area-inset-bottom, 0px)) calc(10px + env(safe-area-inset-left, 0px));
  }
  .mac-side {
    flex: 0 0 clamp(230px, 36%, 340px);
    overflow-y: auto;
    overscroll-behavior: contain;
  }
  .mac-actions { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .mac-action { min-height: 44px; flex-direction: row; gap: 6px; padding: 6px; }
  .emphasizes-primary .mac-action.primary { min-height: 52px; }
  .mac-actions.emphasizes-primary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (prefers-reduced-motion: reduce) {
  .mac-session.waiting { animation: none; }
}
/* DL-165: the link to a session - badge, edge and a caption over the actions, in the session's colour. */
.mobile-agent-console.is-linked { border-left: 4px solid var(--link-accent); }
.mac-actions-for {
  grid-column: 1 / -1; justify-self: start; display: inline-flex; align-items: center; gap: 6px;
  padding: 1px 10px; border-radius: 8px; background: var(--link-accent); color: #0b1220; font-weight: 700;
  font-size: clamp(0.62rem, 0.8vw + 0.34rem, 0.82rem); max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
</style>
