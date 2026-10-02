<template>
  <Teleport to="body">
    <Transition name="lam-fade">
      <div
        v-if="liveMenu"
        class="lam-backdrop"
        role="dialog"
        aria-modal="true"
        :aria-label="liveMenu.button.label"
        @click.self="closeLiveMenu"
        @keydown.esc="closeLiveMenu"
      >
        <section class="lam-sheet" data-testid="lam-sheet">
          <header class="lam-head">
            <div class="lam-title">
              <h2>{{ liveMenu.button.label }}</h2>
              <span v-if="sublabel" class="lam-sub">{{ sublabel }}</span>
            </div>
            <button type="button" class="lam-close" aria-label="Close" @click="closeLiveMenu">
              <FontAwesomeIcon :icon="['fas', 'times']" />
            </button>
          </header>

          <pre v-if="liveMenu.panelText" class="lam-panel" data-testid="lam-panel">{{ liveMenu.panelText }}</pre>

          <ul v-if="liveMenu.items.length" class="lam-items">
            <li v-for="item in liveMenu.items" :key="item.id">
              <button
                type="button"
                class="lam-item"
                :class="{ 'lam-danger': item.danger }"
                data-testid="lam-item"
                @click="chooseLiveMenuItem(item)"
              >
                {{ item.label }}
              </button>
            </li>
          </ul>
          <p v-else-if="!liveMenu.panelText" class="lam-empty" data-testid="lam-empty">
            {{ liveMenu.message || 'Nothing to show right now.' }}
          </p>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { chooseLiveMenuItem, closeLiveMenu, liveMenu } from '@/services/liveActionMenu'
import { useButtonStateStore } from '@/stores/buttonState'

/**
 * DL-145 - the sheet a `press: 'menu'` live button opens: its status line,
 * the rows the backend offered, and (after a row ran) a log tail.
 */

const buttonState = useButtonStateStore()

const sublabel = computed(() =>
  liveMenu.value ? buttonState.states[liveMenu.value.button.id]?.sublabel : undefined,
)
</script>

<style scoped>
.lam-backdrop {
  position: fixed;
  inset: 0;
  z-index: 3900; /* below ConfirmDialog (4000): a confirm opens over this sheet */
  display: flex;
  align-items: flex-end;
  justify-content: center;
  background: rgba(4, 8, 16, 0.6);
}

.lam-sheet {
  width: min(560px, 100%);
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px clamp(14px, 3vw, 22px) calc(14px + env(safe-area-inset-bottom, 0px));
  border-radius: 18px 18px 0 0;
  background: #0f1829;
  border: 1px solid #243556;
  border-bottom: none;
  color: #e9eff8;
  overflow-y: auto;
}

.lam-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.lam-title { display: flex; align-items: baseline; gap: 10px; min-width: 0; }
.lam-title h2 { margin: 0; font-size: 1.1rem; }
.lam-sub { color: #9fb0c9; font-size: 0.85rem; }
.lam-close {
  flex: none; width: 40px; height: 40px;
  border-radius: 10px; border: 1px solid #243556;
  background: #16233a; color: #cfdcee; cursor: pointer; touch-action: manipulation;
}

.lam-items { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.lam-item {
  width: 100%; min-height: calc(48px * var(--touch-multiplier, 1)); padding: 0 16px;
  border-radius: 12px; border: 1px solid #2a3e60; background: #16233a; color: #e9eff8;
  font: inherit; font-size: 0.95rem; font-weight: 600; text-align: left;
  cursor: pointer; touch-action: manipulation;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.lam-item:active { transform: scale(0.98); }
.lam-danger { border-color: #b4414f; }

.lam-panel {
  margin: 0; padding: 10px 12px; max-height: 40vh; overflow: auto;
  border-radius: 10px; background: #0a111f; border: 1px solid #1f2f4a;
  color: #b9c7dc; font-size: 0.78rem; line-height: 1.4; white-space: pre-wrap;
}
.lam-empty { margin: 8px 0 4px; color: #9fb0c9; line-height: 1.5; }

.lam-fade-enter-active, .lam-fade-leave-active { transition: opacity 0.16s ease; }
.lam-fade-enter-from, .lam-fade-leave-to { opacity: 0; }
</style>
