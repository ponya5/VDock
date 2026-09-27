<template>
  <section
    class="mobile-agent-console"
    :class="`state-${displayState}`"
    :aria-label="`${agentName} console`"
  >
    <header class="mac-status" aria-live="polite">
      <span class="mac-status-dot" aria-hidden="true" />
      <div class="mac-status-text">
        <strong class="mac-agent-name">{{ agentName }}</strong>
        <span class="mac-state-label">{{ statusLine }}</span>
      </div>
      <!-- Session targeting (DL-071) merged into this row — saves a whole
           stacked row on the phone. flex-wrap still lets the chips fall
           to a second line inside the card on narrow widths. -->
      <div
        v-if="showSessionPicker"
        class="mac-sessions"
        role="radiogroup"
        aria-label="Target session"
      >
        <button
          type="button"
          class="mac-session"
          :class="{ active: pinnedPid === null }"
          role="radio"
          :aria-checked="pinnedPid === null"
          @click="chooseTarget(null)"
        >
          <FontAwesomeIcon :icon="['fas', 'wand-magic-sparkles']" class="mac-session-auto" />
          <span class="mac-session-label">Auto</span>
        </button>
        <button
          v-for="s in targetRows"
          :key="s.pid"
          type="button"
          class="mac-session"
          :class="{
            active: s.pid === pinnedPid,
            'is-resolved': s.pid === resolvedPid && pinnedPid === null,
            waiting: waitingGlowOn && s.state === 'ready',
          }"
          role="radio"
          :aria-checked="s.pid === pinnedPid"
          :title="s.cwd || s.title"
          @click="chooseTarget(s.pid)"
        >
          <span class="mac-session-dot" :class="`dot-${s.state || 'idle'}`" aria-hidden="true" />
          <span class="mac-session-label">{{ s.label }}</span>
          <FontAwesomeIcon
            v-if="s.pid === pinnedPid"
            :icon="['fas', 'thumbtack']"
            class="mac-session-pin"
          />
        </button>
      </div>
      <!-- Only when the picker is absent — otherwise it duplicates the
           session chip's label (both read the project dir name). -->
      <span v-else-if="projectName" class="mac-project" :title="stateEntry?.cwd">
        <FontAwesomeIcon :icon="['fas', 'folder-open']" />
        {{ projectName }}
      </span>
    </header>

    <div
      v-if="isAgentPossiblyRunning && visibleActions.length > 0"
      class="mac-actions"
      :class="{ 'emphasizes-primary': emphasizesPrimaryAction }"
      :style="{ '--secondary-action-count': Math.max(visibleActions.length - 1, 1) }"
    >
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

    <div v-if="shortcutTiles.length > 0" class="mac-shortcuts" aria-label="Shortcuts">
      <button
        v-for="shortcut in shortcutTiles"
        :key="shortcut.button.id"
        type="button"
        class="mac-shortcut"
        :class="{ highlighted: shortcut.isHighlighted }"
        :disabled="runningShortcutId !== null"
        :title="shortcut.button.tooltip || shortcut.label"
        @click="runShortcut(shortcut)"
      >
        <FontAwesomeIcon
          :icon="runningShortcutId === shortcut.button.id ? ['fas', 'spinner'] : shortcut.icon"
          :spin="runningShortcutId === shortcut.button.id"
          class="mac-shortcut-icon"
        />
        <span class="mac-shortcut-label">{{ shortcut.label }}</span>
      </button>
    </div>

    <!-- Web links (url-type buttons like claude.ai): they open a browser,
         they do not drive the session — kept aside from the action tiles
         and styled as quiet outline pills so they can't be mistaken for
         one. Rendered last so actions never reflow around them. -->
    <div v-if="linkShortcuts.length > 0" class="mac-links" aria-label="Web links">
      <button
        v-for="link in linkShortcuts"
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
  </section>
</template>

<script setup lang="ts">
import { computed, ref, toRef } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { Button, Scene } from '@/types'
import { useDashboardStore } from '@/stores/dashboard'
import { useNotificationsStore } from '@/stores/notifications'
import { useSettingsStore } from '@/stores/settings'
import { trackAgentSurfaceVisibility, useAgentSession } from '@/composables/useAgentSession'
import { profileSessionMarker, useAgentTargets } from '@/composables/useAgentTargets'
import { isAgentWaitingDismissed } from '@/services/agentWaiting'
import { normalizeFaIcon } from '@/utils/normalizeFaIcon'
import { vibrate } from '@/utils/haptics'

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

/** Page navigation means nothing on a surface without pages. */
const PAGE_NAVIGATION_ACTIONS = new Set(['next_page', 'previous_page', 'home_page', 'goto_page'])
/** Scene buttons that start the agent — highlighted while it isn't running. */
const LAUNCH_ACTIONS = new Set(['claude_continue', 'program'])
/** Buttons that open something OUTSIDE the session — web pages (url) and
    app/web launchers (claude_open → claude.ai / desktop app). They render
    in the links strip, not among session-driving action tiles. */
const WEB_LINK_ACTIONS = new Set(['url', 'claude_open'])

const dashboardStore = useDashboardStore()
const notificationsStore = useNotificationsStore()
const settingsStore = useSettingsStore()
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
} = useAgentSession(toRef(props, 'scene'))

const runningShortcutId = ref<string | null>(null)

// DL-071: which live CLI session the actions/shortcuts drive. The chip strip
// shows whenever at least one session is detected (or a pin is set) so the
// current target is always visible — it only vanishes with zero sessions.
const sessionMarker = computed(() => profileSessionMarker(profile.value))
const {
  sessionRows: targetRows,
  pinnedPid,
  resolvedPid,
  setTarget,
  identify,
} = useAgentTargets(sessionMarker)

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
const statusLine = computed(() => {
  if (profile.value && !stateEntry.value && !isAgentDetected.value) return 'No open session'
  return stateEntry.value?.message || stateLabel.value
})

const displayState = computed(() => (isAgentPossiblyRunning.value ? currentState.value : 'offline'))

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

async function runShortcut(shortcut: ConsoleShortcut): Promise<void> {
  if (runningShortcutId.value) return
  vibrate(10)
  runningShortcutId.value = shortcut.button.id
  try {
    const result = await dashboardStore.executeButtonAction(shortcut.button)
    if (result && !result.success) {
      notificationsStore.error(`${shortcut.label} failed`, result.message || 'The action did not run')
    }
  } finally {
    runningShortcutId.value = null
  }
}

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
  padding: 10px 12px calc(10px + env(safe-area-inset-bottom, 0px));
  color: #e5e7eb;
}

.mobile-agent-console.state-ready { --agent-accent: #22c55e; }
.mobile-agent-console.state-working { --agent-accent: #38bdf8; }
.mobile-agent-console.state-permission { --agent-accent: #f59e0b; }
.mobile-agent-console.state-unknown { --agent-accent: #94a3b8; }
.mobile-agent-console.state-offline { --agent-accent: #64748b; }

/* --- Status card ------------------------------------------------------------ */
.mac-status {
  display: flex;
  align-items: center;
  /* Session chips live inside this row now — wrap lets them fall to a
     second line inside the same card instead of forcing one long line. */
  flex-wrap: wrap;
  gap: 10px 12px;
  flex-shrink: 0;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(15, 20, 28, 0.78);
  border: 1px solid color-mix(in srgb, var(--agent-accent) 50%, transparent);
  box-shadow: 0 0 18px color-mix(in srgb, var(--agent-accent) 20%, transparent);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.mac-status-dot {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--agent-accent);
  box-shadow: 0 0 10px var(--agent-accent);
}

.state-working .mac-status-dot,
.state-permission .mac-status-dot {
  animation: mac-pulse 1.2s ease-in-out infinite;
}

.mac-status-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.2;
}

.mac-agent-name {
  font-size: clamp(1rem, 0.9rem + 0.6vw, 1.2rem);
}

.mac-state-label {
  font-size: clamp(0.85rem, 0.8rem + 0.4vw, 1rem);
  color: color-mix(in srgb, var(--agent-accent) 75%, #e5e7eb);
}

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
/* A wrap-visible chip strip — DL-069's rule applies here too: no horizontal
   scroll row hiding sessions. Chips render whenever ≥1 live session exists
   (or a pin is set), so the current target is always on screen. The strip
   sits inside .mac-status: margin-left:auto hugs the right edge when it
   shares the status line; on a wrapped second line it right-aligns there,
   which reads fine as a trailing control group. */
.mac-sessions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-left: auto;
}

.mac-session {
  -webkit-user-select: none;
  user-select: none;
  min-height: 44px;
  max-width: 48%;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(15, 20, 28, 0.78);
  color: inherit;
  font-size: clamp(0.78rem, 0.74rem + 0.3vw, 0.92rem);
  font-weight: 600;
  touch-action: manipulation;
  cursor: pointer;
}

/* The session auto-resolution would pick right now (no pin set). */
.mac-session.is-resolved {
  border-color: color-mix(in srgb, var(--agent-accent) 40%, transparent);
}

.mac-session.active {
  border-color: var(--agent-accent);
  background: color-mix(in srgb, var(--agent-accent) 24%, transparent);
}

/* Idle session waiting for a prompt — filled + thick ring like the desktop
   picker rows; a thin border was invisible on the 7" panel (DL-080 #3). */
.mac-session.waiting {
  border-color: #4ade80;
  border-width: 2px;
  background: rgba(34, 197, 94, 0.25);
  animation: mac-session-waiting-pulse 1.6s ease-in-out infinite;
}

@keyframes mac-session-waiting-pulse {
  0%, 100% {
    background: rgba(34, 197, 94, 0.2);
    box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.45), 0 0 10px rgba(34, 197, 94, 0.5);
  }
  50% {
    background: rgba(34, 197, 94, 0.38);
    box-shadow: 0 0 0 4px rgba(134, 239, 172, 0.8), 0 0 24px rgba(34, 197, 94, 0.85);
  }
}

.mac-session:active:not(:disabled) { transform: scale(0.96); }

.mac-session-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex-shrink: 0;
  background: #6b7280;
}

.mac-session-dot.dot-ready { background: #22c55e; }
.mac-session-dot.dot-working { background: #38bdf8; }
.mac-session-dot.dot-permission { background: #f59e0b; }

.mac-session-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mac-session-auto {
  color: var(--agent-accent);
  font-size: 0.9em;
}

.mac-session-pin {
  color: var(--agent-accent);
  font-size: 0.8em;
  flex-shrink: 0;
}

/* --- State actions ------------------------------------------------------------ */
/* One compact row of icon-over-label buttons; an urgent primary action
   gets a full-width row of its own. */
.mac-actions {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(64px, 1fr));
  gap: 8px;
}

.mac-action {
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
  font-size: clamp(0.78rem, 0.74rem + 0.3vw, 0.9rem);
  font-weight: 600;
  line-height: 1.15;
  text-align: center;
  touch-action: manipulation;
  cursor: pointer;
}

.mac-action > svg {
  font-size: 1.3em;
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
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(84px, 1fr));
  gap: 10px;
}

.mac-shortcut {
  -webkit-user-select: none;
  user-select: none;
  min-height: 68px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 6px;
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
  overflow-wrap: anywhere;
}

.mac-shortcut.highlighted {
  border-color: var(--agent-accent);
  background: color-mix(in srgb, var(--agent-accent) 28%, transparent);
}

.mac-shortcut:active:not(:disabled) { transform: scale(0.96); }
.mac-shortcut:disabled { opacity: 0.6; cursor: default; }

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
  min-height: 36px;
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

/* Landscape phones (~390px tall): every row slims down so the action
   buttons and shortcuts stay comfortably reachable in a shorter viewport. */
@media (max-height: 480px) {
  .mobile-agent-console {
    gap: 6px;
    padding-top: 6px;
    padding-bottom: calc(6px + env(safe-area-inset-bottom, 0px));
  }

  .mac-status {
    padding: 6px 12px;
    border-radius: 14px;
    gap: 6px 10px;
  }

  /* Chips share the status row now — slim them so the merged line stays
     one compact band in landscape. */
  .mac-session {
    min-height: 36px;
    padding: 4px 10px;
  }

  .mac-status-text {
    flex-direction: row;
    align-items: baseline;
    gap: 10px;
  }

  .mac-action {
    min-height: 44px;
    flex-direction: row;
    gap: 6px;
  }

  .mac-shortcuts {
    grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  }

  .mac-shortcut {
    min-height: 44px;
    flex-direction: row;
    gap: 8px;
    padding: 8px 10px;
  }
}

@keyframes mac-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

@media (prefers-reduced-motion: reduce) {
  .mac-status-dot { animation: none !important; }
  .mac-session.waiting { animation: none; }
}
</style>
