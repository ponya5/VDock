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
        <span class="mac-state-label">{{ stateLabel }}</span>
      </div>
      <span v-if="projectName" class="mac-project" :title="stateEntry?.cwd">
        <FontAwesomeIcon :icon="['fas', 'folder-open']" />
        {{ projectName }}
      </span>
    </header>

    <div ref="conversationRef" class="mac-conversation" :class="{ 'mac-conversation--empty': !hasConversation }">
      <template v-if="hasConversation">
        <article v-if="lastPrompt" class="mac-message from-user">
          <span class="mac-author">You</span>
          <p class="mac-message-text">{{ lastPrompt }}</p>
        </article>
        <article v-if="currentState === 'working'" class="mac-message from-agent is-working">
          <span class="mac-author">{{ agentName }}</span>
          <p class="mac-message-text">
            <FontAwesomeIcon :icon="['fas', 'spinner']" spin />
            {{ workingMessage }}
          </p>
        </article>
        <article v-else-if="lastReply" class="mac-message from-agent">
          <span class="mac-author">{{ agentName }}</span>
          <p class="mac-message-text">{{ lastReply }}</p>
        </article>
        <article v-if="currentState === 'permission'" class="mac-message from-agent is-permission">
          <span class="mac-author">{{ agentName }} is asking</span>
          <p class="mac-message-text">{{ stateEntry?.message || 'Needs your permission' }}</p>
        </article>
      </template>
      <div v-else class="mac-empty">
        <FontAwesomeIcon :icon="['fas', emptyStateIcon]" class="mac-empty-icon" />
        <p>{{ emptyStateText }}</p>
      </div>
    </div>

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

    <div v-if="shortcuts.length > 0" class="mac-shortcuts" aria-label="Shortcuts">
      <button
        v-for="shortcut in shortcuts"
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
        />
        <span>{{ shortcut.label }}</span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, toRef, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { Button, Scene } from '@/types'
import { useDashboardStore } from '@/stores/dashboard'
import { useNotificationsStore } from '@/stores/notifications'
import { trackAgentSurfaceVisibility, useAgentSession } from '@/composables/useAgentSession'
import { normalizeFaIcon } from '@/utils/normalizeFaIcon'
import { vibrate } from '@/utils/haptics'

/**
 * Mobile agent console (DL-065): a portrait phone surface for talking to a
 * coding agent running on the PC — its live state, the last prompt and
 * reply, the actions that fit the moment, and the scene's shortcuts.
 *
 * There is deliberately no free-text composer here (DL-069 follow-up): a
 * phone's on-screen keyboard eats most of the screen for a control surface
 * that's meant to be a quick tap away, and every state-driven action
 * (Submit, Continue, Interrupt, …) already covers what a follow-up message
 * would have said. Free-text prompting stays a desktop-only affordance,
 * driven from the scene's own buttons via `runShortcut` below.
 */

interface ConsoleShortcut {
  button: Button
  label: string
  icon: [string, string]
  isHighlighted: boolean
}

const props = defineProps<{ scene: Scene | null }>()

/** Page navigation means nothing on a surface without pages. */
const PAGE_NAVIGATION_ACTIONS = new Set(['next_page', 'previous_page', 'home_page', 'goto_page'])
/** Scene buttons that start the agent — highlighted while it isn't running. */
const LAUNCH_ACTIONS = new Set(['claude_continue', 'claude_open', 'program'])
const CONVERSATION_SCROLL_MARGIN_PX = 12

const dashboardStore = useDashboardStore()
const notificationsStore = useNotificationsStore()
const {
  profile,
  stateEntry,
  currentState,
  stateLabel,
  isAgentPossiblyRunning,
  visibleActions,
  runningActionId,
  runAction,
} = useAgentSession(toRef(props, 'scene'))

const conversationRef = ref<HTMLElement | null>(null)
const runningShortcutId = ref<string | null>(null)

const agentName = computed(() => profile.value?.label ?? props.scene?.name ?? 'Agent')
const projectName = computed(() => stateEntry.value?.project ?? '')
const lastPrompt = computed(() => stateEntry.value?.prompt ?? '')
const lastReply = computed(() => stateEntry.value?.reply ?? '')
const workingMessage = computed(() => stateEntry.value?.message || 'Working…')

const displayState = computed(() => (isAgentPossiblyRunning.value ? currentState.value : 'offline'))

const hasConversation = computed(() =>
  Boolean(lastPrompt.value || lastReply.value) ||
  currentState.value === 'working' ||
  currentState.value === 'permission'
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

const emptyStateIcon = computed(() => (isAgentPossiblyRunning.value ? 'comments' : 'power-off'))

const emptyStateText = computed(() => {
  if (!isAgentPossiblyRunning.value) {
    return `${agentName.value} isn't running on your PC. Start it from a shortcut below.`
  }
  return `Use the buttons below to drive ${agentName.value} on your PC.`
})

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
    }))
})

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

/** Brings the newest message's first line into view, so a long reply reads from its start. */
async function scrollToNewestMessage(): Promise<void> {
  await nextTick()
  const conversation = conversationRef.value
  const newestMessage = conversation?.querySelector<HTMLElement>('.mac-message:last-of-type')
  if (!conversation || !newestMessage) return
  conversation.scrollTop = newestMessage.offsetTop - CONVERSATION_SCROLL_MARGIN_PX
}

watch([lastPrompt, lastReply, currentState], scrollToNewestMessage)
onMounted(scrollToNewestMessage)

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
  gap: 12px;
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

/* --- Conversation ------------------------------------------------------------ */
.mac-conversation {
  position: relative;
  flex: 1;
  min-height: 96px;
  overflow-y: auto;
  overscroll-behavior: contain;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  border-radius: 18px;
  background: rgba(10, 14, 20, 0.62);
  border: 1px solid rgba(255, 255, 255, 0.08);
  -webkit-overflow-scrolling: touch;
}

/* With no composer to type into, there's nothing left to say about a card
   that just repeats "isn't running" / "use the buttons below" — so unlike
   a real conversation (which keeps flex: 1 to grow and scroll), the empty
   state only claims the room its one line of text actually needs, leaving
   the action buttons below as the visually dominant part of the screen. */
.mac-conversation--empty {
  flex: 0 0 auto;
  min-height: 0;
}

.mac-message {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 92%;
  padding: 10px 12px;
  border-radius: 16px;
}

.mac-message.from-user {
  align-self: flex-end;
  background: #1f6fd1;
  border-bottom-right-radius: 6px;
}

.mac-message.from-agent {
  align-self: flex-start;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-bottom-left-radius: 6px;
}

.mac-message.is-working {
  color: #bae6fd;
}

.mac-message.is-permission {
  border-color: rgba(245, 158, 11, 0.55);
  background: rgba(245, 158, 11, 0.12);
}

.mac-author {
  font-size: clamp(0.68rem, 0.64rem + 0.2vw, 0.78rem);
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  opacity: 0.7;
}

.mac-message-text {
  margin: 0;
  font-size: clamp(0.9rem, 0.85rem + 0.3vw, 1rem);
  line-height: 1.45;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  user-select: text;
  -webkit-user-select: text;
}

.mac-empty {
  margin: auto;
  max-width: 320px;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 10px;
  text-align: left;
  color: rgba(255, 255, 255, 0.65);
}

.mac-empty p {
  margin: 0;
  font-size: clamp(0.82rem, 0.78rem + 0.25vw, 0.92rem);
  line-height: 1.4;
}

.mac-empty-icon {
  flex-shrink: 0;
  font-size: clamp(1.1rem, 1rem + 0.5vw, 1.4rem);
  color: var(--agent-accent);
}

/* --- State actions ------------------------------------------------------------ */
/* One compact row of icon-over-label buttons, so the conversation keeps
   the height; an urgent primary action gets a full-width row of its own. */
.mac-actions {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(64px, 1fr));
  gap: 8px;
}

.mac-action {
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
.mac-shortcuts {
  flex-shrink: 0;
  display: flex;
  gap: 8px;
  overflow-x: auto;
  scrollbar-width: none;
  margin: 0 -12px;
  padding: 0 12px;
}

.mac-shortcuts::-webkit-scrollbar { display: none; }

.mac-shortcut {
  flex: 0 0 auto;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.08);
  color: inherit;
  font-size: clamp(0.82rem, 0.78rem + 0.3vw, 0.95rem);
  font-weight: 600;
  white-space: nowrap;
  touch-action: manipulation;
  cursor: pointer;
}

.mac-shortcut.highlighted {
  border-color: var(--agent-accent);
  background: color-mix(in srgb, var(--agent-accent) 28%, transparent);
}

.mac-shortcut:active:not(:disabled) { transform: scale(0.96); }
.mac-shortcut:disabled { opacity: 0.6; cursor: default; }

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
  }

  .mac-status-text {
    flex-direction: row;
    align-items: baseline;
    gap: 10px;
  }

  .mac-conversation {
    min-height: 56px;
    padding: 8px;
  }

  .mac-action {
    min-height: 44px;
    flex-direction: row;
    gap: 6px;
  }

  .mac-shortcut {
    min-height: 40px;
  }
}

@keyframes mac-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

@media (prefers-reduced-motion: reduce) {
  .mac-status-dot { animation: none !important; }
}
</style>
