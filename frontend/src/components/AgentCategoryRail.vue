<template>
  <div
    ref="rootRef"
    :class="[horizontal ? 'agent-cat-chips' : 'agent-cat-rail', { 'fade-right': horizontal && canScrollRight }]"
    role="tablist"
    :aria-orientation="horizontal ? 'horizontal' : 'vertical'"
    aria-label="Button categories"
    data-testid="agent-category-tabs"
    @scroll.passive="measure"
    @keydown="onKeydown"
  >
    <button
      v-for="g in groups"
      :id="`agent-cat-tab-${g.id}`"
      :key="g.id"
      type="button"
      role="tab"
      class="acr-item"
      :class="{ selected: g.id === selected }"
      :aria-selected="g.id === selected"
      aria-controls="agent-cat-panel"
      :aria-label="itemLabel(g)"
      :tabindex="g.id === selected ? 0 : -1"
      :data-category="g.id"
      @click="choose(g.id)"
    >
      <span class="acr-icon" aria-hidden="true"><FontAwesomeIcon :icon="['fas', g.icon]" /></span>
      <span class="acr-label" aria-hidden="true">{{ g.label }}</span>
      <span
        v-if="g.id === 'session' && badge === 'working'"
        class="acr-badge working"
        data-testid="session-badge"
        data-badge="working"
        aria-hidden="true"
      />
      <span
        v-else-if="g.id === 'session' && badge === 'permission'"
        class="acr-badge permission"
        data-testid="session-badge"
        data-badge="permission"
        aria-hidden="true"
      >!</span>
      <span class="acr-count" aria-hidden="true">{{ g.buttons.length }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { AgentCategoryId, CategoryGroup } from '@/utils/agentCategories'
import { vibrate } from '@/utils/haptics'

/**
 * DL-166: the category picker. Vertical rail on desktop / the 7" panel,
 * horizontally scrolling chip row on a phone. Calm on purpose: it never uses
 * state colours; the only marks are a small badge on Session while the agent
 * is working or needs you.
 */

const props = withDefaults(defineProps<{
  groups: CategoryGroup[]
  selected: AgentCategoryId | null
  orientation?: 'vertical' | 'horizontal'
  /** What the agent is doing, shown on the Session entry only. */
  badge?: 'working' | 'permission' | null
}>(), { orientation: 'vertical', badge: null })

const emit = defineEmits<{ select: [id: AgentCategoryId] }>()

const horizontal = computed(() => props.orientation === 'horizontal')
const rootRef = ref<HTMLElement | null>(null)
const canScrollRight = ref(false)

function itemLabel(g: CategoryGroup): string {
  const suffix = g.id === 'session'
    ? props.badge === 'working' ? ', agent working' : props.badge === 'permission' ? ', needs permission' : ''
    : ''
  return `${g.label}, ${g.buttons.length} ${g.buttons.length === 1 ? 'button' : 'buttons'}${suffix}`
}

function choose(id: AgentCategoryId): void {
  if (id !== props.selected) vibrate(10)
  emit('select', id)
}

function onKeydown(e: KeyboardEvent): void {
  const ids = props.groups.map(g => g.id)
  if (!ids.length) return
  const prev = horizontal.value ? 'ArrowLeft' : 'ArrowUp'
  const next = horizontal.value ? 'ArrowRight' : 'ArrowDown'
  const i = Math.max(0, ids.indexOf(props.selected as AgentCategoryId))
  let target = -1
  if (e.key === next) target = Math.min(ids.length - 1, i + 1)
  else if (e.key === prev) target = Math.max(0, i - 1)
  else if (e.key === 'Home') target = 0
  else if (e.key === 'End') target = ids.length - 1
  if (target < 0) return
  e.preventDefault()
  emit('select', ids[target])
  void nextTick(() => rootRef.value?.querySelector<HTMLElement>(`[data-category="${ids[target]}"]`)?.focus())
}

function measure(): void {
  const el = rootRef.value
  canScrollRight.value = Boolean(el && horizontal.value && el.scrollWidth - el.clientWidth - el.scrollLeft > 4)
}

watch(() => props.selected, async () => {
  await nextTick()
  const el = rootRef.value?.querySelector<HTMLElement>('.acr-item.selected')
  if (el && typeof el.scrollIntoView === 'function') el.scrollIntoView({ inline: 'nearest', block: 'nearest' })
  measure()
})
watch(() => props.groups.length, () => void nextTick(measure))

onMounted(() => {
  measure()
  window.addEventListener('resize', measure)
})
onBeforeUnmount(() => window.removeEventListener('resize', measure))
</script>

<style scoped>
/* ---- shared item bits ---- */
.acr-item {
  position: relative;
  display: flex;
  border: 0;
  color: rgba(255, 255, 255, 0.72);
  background: transparent;
  font-weight: 600;
  cursor: pointer;
  touch-action: manipulation;
  -webkit-user-select: none;
  user-select: none;
}
.acr-item.selected { color: #fff; }
.acr-item:focus-visible { outline: 2px solid #e5e7eb; outline-offset: -2px; }

.acr-count {
  background: rgba(255, 255, 255, 0.14);
  color: inherit;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  text-align: center;
  border-radius: 999px;
}

.acr-badge {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.acr-badge.working {
  width: 9px; height: 9px; border-radius: 50%; background: #38bdf8;
  animation: acr-pulse 1.6s ease-in-out infinite;
}
.acr-badge.permission {
  width: 16px; height: 16px; border-radius: 50%; background: #f59e0b; color: #1a1203;
  font-size: 0.7rem; font-weight: 800; line-height: 1;
}
@keyframes acr-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }

/* ---- vertical rail (desktop / panel) ---- */
.agent-cat-rail {
  flex: 0 0 clamp(84px, 9vw, 120px);
  width: clamp(84px, 9vw, 120px);
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 0;
  padding: 6px;
  overflow-y: auto;
  overscroll-behavior: contain;
  border-radius: 16px;
  background: rgba(15, 20, 28, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.1);
  -webkit-backdrop-filter: blur(8px);
  backdrop-filter: blur(8px);
}
.agent-cat-rail .acr-item {
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  flex: none;
  min-height: max(64px, calc(56px * min(var(--touch-multiplier, 1), 1.5)));
  padding: 8px 4px;
  border-radius: 12px;
}
.agent-cat-rail .acr-item.selected {
  background: rgba(255, 255, 255, 0.14);
  box-shadow: inset 4px 0 0 #e5e7eb;
}
.agent-cat-rail .acr-icon { font-size: 1.35rem; line-height: 1; }
.agent-cat-rail .acr-label {
  font-size: clamp(0.72rem, 1.6vh, 0.9rem);
  line-height: 1.15;
  text-align: center;
  overflow-wrap: anywhere;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}
.agent-cat-rail .acr-count {
  position: absolute; top: 4px; right: 4px;
  min-width: 1.5em; padding: 0 5px; font-size: 0.7rem;
}
.agent-cat-rail .acr-badge { position: absolute; top: 8px; left: 8px; }

/* ---- horizontal chips (phone) ---- */
.agent-cat-chips {
  display: flex;
  gap: 8px;
  flex: none;
  overflow-x: auto;
  overscroll-behavior-x: contain;
  scroll-snap-type: x proximity;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  padding: 2px 0;
}
.agent-cat-chips::-webkit-scrollbar { display: none; }
.agent-cat-chips.fade-right {
  -webkit-mask-image: linear-gradient(to right, #000 calc(100% - 16px), transparent);
  mask-image: linear-gradient(to right, #000 calc(100% - 16px), transparent);
}
.agent-cat-chips .acr-item {
  flex: none;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 0 14px;
  border-radius: 999px;
  scroll-snap-align: start;
  white-space: nowrap;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.9rem;
}
.agent-cat-chips .acr-item.selected { background: #f1f5f9; color: #0b1220; }
.agent-cat-chips .acr-count {
  min-width: 1.6em; padding: 0 6px; font-size: 0.78rem;
  background: rgba(255, 255, 255, 0.16);
}
.agent-cat-chips .acr-item.selected .acr-count { background: rgba(11, 18, 32, 0.14); }

@media (prefers-reduced-motion: reduce) {
  .acr-badge.working { animation: none; }
}
</style>
