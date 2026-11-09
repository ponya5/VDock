<template>
  <div
    class="agent-status-banner"
    :class="[`state-${state}`, `variant-${variant}`]"
    data-testid="agent-status-banner"
  >
    <div class="asb-main" role="status" aria-live="polite">
      <span class="asb-sr">{{ accessibleText }}</span>
      <span class="asb-glyph" aria-hidden="true" :data-icon="glyph.icon">
        <FontAwesomeIcon :icon="['fas', glyph.icon]" />
      </span>
      <span class="asb-text" aria-hidden="true">
        <span class="asb-name">
          <span
            v-if="linked"
            :class="variant === 'card' ? 'mac-link-badge' : 'agent-link-badge'"
            :style="{ background: linkAccent! }"
            :title="`Linked to ${linked.label}`"
          >{{ linked.badge || '·' }}</span>
          <span class="asb-agent">{{ agentName }}</span>
        </span>
        <span class="asb-word">{{ glyph.word }}</span>
        <span class="asb-sub">
          <span v-if="elapsedText" class="asb-elapsed" data-testid="asb-elapsed">{{ elapsedText }}</span>
          <span v-if="elapsedText && subText" class="asb-dot"> &middot; </span>
          <span class="asb-detail" :class="{ 'mac-state-label': variant === 'card' }">{{ subText }}</span>
        </span>
        <span v-if="othersSummary" class="asb-others agent-others mac-others" data-testid="others-summary">{{ othersSummary }}</span>
      </span>
    </div>
    <div v-if="$slots.default" class="asb-slot"><slot /></div>
    <span v-if="variant === 'card' && state === 'working'" class="asb-stripe" aria-hidden="true" />
  </div>
</template>

<script setup lang="ts">
import { computed, toRef } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { AgentSessionRow } from '@/composables/useAgentTargets'
import { formatElapsed, useAgentClock } from '@/composables/useAgentStateSince'

/**
 * DL-166: the agent status, readable from across the desk. One word, one
 * glyph shape and one colour per state - colour is never the only signal
 * (WCAG 1.4.1) - plus how long the agent has been in the state.
 */

export type BannerState = 'working' | 'ready' | 'permission' | 'unknown' | 'offline'

const props = withDefaults(defineProps<{
  state: BannerState
  agentName: string
  /** The hook's message ("needs permission to use Bash") or other state copy; blank means the default for the state. */
  detail?: string
  /** Epoch ms when the current state began (see useAgentStateSince). */
  sinceMs?: number | null
  linked?: AgentSessionRow | null
  linkAccent?: string | null
  othersSummary?: string
  variant?: 'bar' | 'card'
}>(), {
  detail: '',
  sinceMs: null,
  linked: null,
  linkAccent: null,
  othersSummary: '',
  variant: 'bar',
})

const GLYPHS: Record<BannerState, { word: string; icon: string; sub: string }> = {
  working: { word: 'Working', icon: 'circle-notch', sub: '' },
  ready: { word: 'Ready', icon: 'circle-check', sub: 'Waiting for your prompt' },
  permission: { word: 'Needs you', icon: 'triangle-exclamation', sub: 'Approve or deny in the session' },
  unknown: { word: 'Running', icon: 'circle-dot', sub: 'No live status. Install the agent hook in Settings → AI agents' },
  offline: { word: 'No session', icon: 'power-off', sub: 'Open a session to start' },
}

const glyph = computed(() => GLYPHS[props.state])

const now = useAgentClock(computed(() => props.state === 'working' || props.state === 'permission'))
const sinceMs = toRef(props, 'sinceMs')

const elapsedText = computed(() => {
  if (sinceMs.value == null) return ''
  const ms = Math.max(0, now.value - sinceMs.value)
  if (props.state === 'working' || props.state === 'permission') return `for ${formatElapsed(ms)}`
  if (props.state === 'ready' && ms >= 60_000) {
    const text = formatElapsed(ms)
    // Minutes only below an hour: "idle 4m", not "idle 4:12".
    return `idle ${text.includes('h') ? text : `${Math.floor(ms / 60_000)}m`}`
  }
  return ''
})

const subText = computed(() => props.detail || glyph.value.sub)
const accessibleText = computed(() => `${props.agentName}: ${glyph.value.word}. ${subText.value}`.trim())
</script>

<style scoped>
.agent-status-banner {
  --asb-fill: rgba(148, 163, 184, 0.12);
  --asb-edge: #94a3b8;
  --asb-word: #cbd5e1;
  --asb-sub: rgba(226, 232, 240, 0.82);
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px 12px;
  min-width: 0;
  border-radius: 14px;
  background: var(--asb-fill);
  border: 2px solid var(--asb-edge);
  color: var(--asb-sub);
  overflow: hidden;
}

.state-working { --asb-fill: rgba(56, 189, 248, 0.18); --asb-edge: #38bdf8; --asb-word: #7dd3fc; }
.state-ready { --asb-fill: rgba(34, 197, 94, 0.12); --asb-edge: #22c55e; --asb-word: #86efac; }
.state-permission { --asb-fill: #f59e0b; --asb-edge: #f59e0b; --asb-word: #1a1203; --asb-sub: #1a1203; }
.state-unknown { --asb-fill: rgba(148, 163, 184, 0.12); --asb-edge: #64748b; --asb-word: #cbd5e1; }
.state-offline { --asb-fill: rgba(100, 116, 139, 0.10); --asb-edge: #475569; --asb-word: #94a3b8; }

.asb-main {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1 1 auto;
  min-width: 0;
}

.asb-sr {
  position: absolute; width: 1px; height: 1px; overflow: hidden;
  clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap;
}

.asb-glyph { flex: none; line-height: 1; color: var(--asb-word); }
.asb-text { display: flex; flex-direction: column; gap: 2px; min-width: 0; line-height: 1.1; }

.asb-name {
  display: flex; align-items: center; gap: 6px; min-width: 0;
  color: var(--asb-sub);
  font-weight: 600;
}
.agent-link-badge, .mac-link-badge {
  display: inline-flex; align-items: center; justify-content: center; flex: none;
  min-width: 2em; height: 1.7em; padding: 0 0.4em; border-radius: 7px;
  color: #0b1220; font-weight: 800; font-size: clamp(0.62rem, 0.9vw + 0.35rem, 0.85rem);
}
.asb-agent { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.asb-word {
  color: var(--asb-word);
  text-transform: uppercase;
  font-weight: 800;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.asb-sub {
  display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  font-variant-numeric: tabular-nums;
}
.asb-elapsed { font-weight: 700; }

.asb-others { display: block; opacity: 0.85; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.asb-slot { flex: none; margin-left: auto; min-width: 0; max-width: 100%; }

/* --- bar variant: sits at the start of the desktop / panel action bar --- */
.variant-bar {
  flex: 0 1 auto;
  min-width: clamp(200px, 24vw, 340px);
  min-height: var(--agent-action-height, 64px);
  padding: 4px clamp(10px, 1.2vw, 16px);
}
.variant-bar .asb-glyph { font-size: 28px; }
.variant-bar .asb-name { font-size: clamp(0.72rem, 1.6vh, 0.85rem); }
.variant-bar .asb-word { font-size: clamp(1.25rem, 4vh, 1.9rem); }
.variant-bar .asb-sub { font-size: clamp(0.78rem, 2vh, 0.95rem); }
.variant-bar .asb-others { font-size: clamp(0.62rem, 1.4vh, 0.78rem); }

/* --- card variant: full-width status card on the phone console --- */
.variant-card {
  min-height: 84px;
  padding: 14px;
  border-radius: 18px;
  flex-wrap: wrap;
}
.variant-card .asb-glyph { font-size: 32px; }
.variant-card .asb-name { font-size: clamp(0.72rem, 1.6vh, 0.85rem); }
.variant-card .asb-word { font-size: clamp(1.6rem, 7.5vw, 2.1rem); }
.variant-card .asb-sub { font-size: clamp(0.78rem, 2vh, 0.95rem); }
.variant-card .asb-others { font-size: clamp(0.62rem, 1.4vh, 0.78rem); }

/* Landscape phones: slim the card so the shortcuts keep their room. */
@media (max-height: 480px) {
  .variant-card { min-height: 56px; padding: 8px 12px; border-radius: 14px; }
  .variant-card .asb-glyph { font-size: 24px; }
  .variant-card .asb-word { font-size: 1.3rem; }
}

/* --- motion --- */
.state-working .asb-glyph svg { animation: asb-spin 1s linear infinite; }
.state-permission { animation: asb-ring 1.1s ease-out infinite; }

.asb-stripe {
  position: absolute; left: 0; right: 0; bottom: 0; height: 4px; overflow: hidden;
  background: rgba(56, 189, 248, 0.25);
}
.asb-stripe::after {
  content: ''; position: absolute; top: 0; bottom: 0; width: 40%; background: #38bdf8;
  animation: asb-sweep 1.6s ease-in-out infinite;
}

@keyframes asb-spin { to { transform: rotate(360deg); } }
@keyframes asb-ring {
  from { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.55); }
  to { box-shadow: 0 0 0 12px rgba(245, 158, 11, 0); }
}
@keyframes asb-sweep {
  from { transform: translateX(-100%); }
  to { transform: translateX(250%); }
}

/* Reduced motion: shape and text carry the meaning. The ring is a static
   three-quarter arc, the stripe a static bar, the permission pulse a static outline. */
@media (prefers-reduced-motion: reduce) {
  .state-working .asb-glyph svg { animation: none; }
  .state-permission { animation: none; outline: 3px solid #fbbf24; outline-offset: -3px; }
  .asb-stripe::after { animation: none; width: 100%; }
}
</style>
