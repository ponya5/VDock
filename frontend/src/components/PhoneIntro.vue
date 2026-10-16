<template>
  <Teleport to="body">
    <div v-if="open" class="phone-intro" role="dialog" aria-modal="true" aria-label="Welcome to VDock" data-testid="phone-intro">
      <div class="pi-card">
        <div class="pi-icon" aria-hidden="true">
          <FontAwesomeIcon :icon="['fas', card.icon]" />
        </div>
        <h2 class="pi-title">{{ card.title }}</h2>
        <p class="pi-text">{{ card.text }}</p>
        <div class="pi-dots" aria-hidden="true">
          <span v-for="(_, i) in CARDS" :key="i" class="pi-dot" :class="{ on: i === index }"></span>
        </div>
        <div class="pi-actions">
          <button type="button" class="pi-skip" @click="close">Skip</button>
          <button type="button" class="pi-next" data-action="intro-next" @click="next">
            {{ index < CARDS.length - 1 ? 'Next' : 'Start' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

/**
 * DL-011 - the first time VDock opens on a phone or tablet. The desktop tour
 * is skipped on touch devices (its targets are desktop-only) and the welcome
 * toast pointed at Settings, which phones can't open - so new phone users
 * got nothing. Three cards, once per device, skippable.
 */
const SEEN_KEY = 'vdock.phoneIntroSeen'

const CARDS = [
  {
    icon: 'hand-pointer',
    title: 'Your deck, in your hand',
    text: 'Tap a button and it runs on your computer. Swipe left or right — or tap the bar at the top — to switch scenes.',
  },
  {
    icon: 'robot',
    title: 'Your coding wingman',
    text: 'The Claude Code scene shows what your agent is doing. Approve or deny what it asks, interrupt it, or tell it to continue — without walking back to the computer.',
  },
  {
    icon: 'mobile-screen-button',
    title: 'Make it a fixture',
    text: 'Open ⋮ and choose Add to Home Screen for a full-screen deck, then prop the phone next to your keyboard.',
  },
] as const

function alreadySeen(): boolean {
  try {
    return localStorage.getItem(SEEN_KEY) === '1'
  } catch {
    return true // no storage: never nag on every visit
  }
}

const open = ref(!alreadySeen())
const index = ref(0)
const card = computed(() => CARDS[index.value])

function close() {
  open.value = false
  try {
    localStorage.setItem(SEEN_KEY, '1')
  } catch { /* private mode: it shows again next visit */ }
}

function next() {
  if (index.value < CARDS.length - 1) index.value += 1
  else close()
}
</script>

<style scoped>
.phone-intro {
  position: fixed;
  inset: 0;
  z-index: 20000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: max(16px, env(safe-area-inset-top, 0px)) 16px max(16px, env(safe-area-inset-bottom, 0px));
  background: rgba(4, 6, 20, 0.72);
  -webkit-backdrop-filter: blur(6px);
  backdrop-filter: blur(6px);
}
.pi-card {
  width: min(420px, 100%);
  padding: 28px 24px 20px;
  border-radius: 20px;
  background: rgba(22, 24, 44, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.5);
  color: #fff;
  text-align: center;
}
.pi-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 18px;
  background: #1f6fd1;
  font-size: clamp(24px, 6vw, 28px);
}
.pi-title { margin: 16px 0 8px; font-size: 1.3rem; }
.pi-text { margin: 0; color: rgba(255, 255, 255, 0.82); line-height: 1.5; }
.pi-dots { display: flex; justify-content: center; gap: 8px; margin: 20px 0 16px; }
.pi-dot { width: 8px; height: 8px; border-radius: 50%; background: rgba(255, 255, 255, 0.25); }
.pi-dot.on { background: #fff; }
.pi-actions { display: flex; gap: 12px; }
.pi-skip, .pi-next {
  flex: 1;
  min-height: 48px;
  border-radius: 12px;
  border: none;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
}
.pi-skip { background: rgba(255, 255, 255, 0.1); color: #fff; }
.pi-next { background: #1f6fd1; color: #fff; }
</style>
