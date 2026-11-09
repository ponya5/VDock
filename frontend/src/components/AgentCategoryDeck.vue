<template>
  <div class="agent-category-deck" data-testid="agent-category-deck">
    <AgentCategoryRail
      :groups="groups"
      :selected="selectedId"
      :badge="sessionBadge"
      orientation="vertical"
      @select="view.setCategory"
    />
    <div
      id="agent-cat-panel"
      class="acd-panel"
      role="tabpanel"
      :aria-labelledby="selectedId ? `agent-cat-tab-${selectedId}` : undefined"
    >
      <Transition name="agent-cat-fade" mode="out-in">
        <div :key="selectedId ?? 'none'" class="acd-grid">
          <DeckGrid
            v-if="page"
            :page="page"
            :is-edit-mode="false"
            :button-size="buttonSize"
            :show-labels="showLabels"
            :show-tooltips="showTooltips"
            :compact="compact"
            @button-click="b => emit('button-click', original(b))"
            @button-press="b => emit('button-press', original(b))"
            @button-release="b => emit('button-release', original(b))"
            @double-tap="b => emit('double-tap', original(b))"
          />
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, toRef } from 'vue'
import type { Button, Page, Scene } from '@/types'
import DeckGrid from '@/components/DeckGrid.vue'
import AgentCategoryRail from '@/components/AgentCategoryRail.vue'
import { groupSceneButtons } from '@/utils/agentCategories'
import { selectedCategoryId, useAgentSceneView } from '@/composables/useAgentSceneView'
import { useAgentSession } from '@/composables/useAgentSession'

/**
 * DL-166 groups view for desktop and the 7" panel: a category rail beside a
 * read-only DeckGrid that shows only the selected category. The grid is given
 * a synthetic page (constant id, re-flowed positions, 1x1 cells) so cells keep
 * the size they have in the All view, and clicks are re-emitted with the
 * ORIGINAL Button objects so confirm prompts, live faces and rules behave as
 * they do in the All grid.
 */

const props = withDefaults(defineProps<{
  scene: Scene
  buttonSize?: number
  showLabels?: boolean
  showTooltips?: boolean
  compact?: boolean
}>(), { buttonSize: 1, showLabels: true, showTooltips: true, compact: false })

const emit = defineEmits<{
  'button-click': [button: Button]
  'button-press': [button: Button]
  'button-release': [button: Button]
  'double-tap': [button: Button]
}>()

const sceneRef = toRef(props, 'scene')
const view = useAgentSceneView(computed(() => props.scene?.id))
const { currentState, isAgentPossiblyRunning } = useAgentSession(sceneRef)

const groups = computed(() => groupSceneButtons(props.scene))
const selectedId = computed(() => selectedCategoryId(view.category.value, groups.value))
const selectedGroup = computed(() => groups.value.find(g => g.id === selectedId.value) ?? null)

const sessionBadge = computed<'working' | 'permission' | null>(() => {
  if (!isAgentPossiblyRunning.value) return null
  return currentState.value === 'working' || currentState.value === 'permission' ? currentState.value : null
})

const originals = computed(() => new Map((selectedGroup.value?.buttons ?? []).map(b => [b.id, b])))
function original(b: Button): Button {
  return originals.value.get(b.id) ?? b
}

const page = computed<Page | null>(() => {
  const group = selectedGroup.value
  if (!group) return null
  const pages = props.scene.pages
  const cols = Math.max(1, ...pages.map(p => p.grid_config.cols))
  const rows = Math.max(Math.ceil(group.buttons.length / cols), pages[0]?.grid_config.rows ?? 1)
  return {
    id: `${props.scene.id}::groups`,
    name: group.label,
    grid_config: { rows, cols },
    buttons: group.buttons.map((b, i) => ({
      ...b,
      position: { row: Math.floor(i / cols), col: i % cols },
      size: { rows: 1, cols: 1 },
    })),
  }
})
</script>

<style scoped>
.agent-category-deck {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 10px;
  padding: 12px 12px 0;
}

.acd-panel {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.acd-grid {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.agent-cat-fade-enter-active,
.agent-cat-fade-leave-active { transition: opacity 0.12s ease; }
.agent-cat-fade-enter-from,
.agent-cat-fade-leave-to { opacity: 0; }

@media (prefers-reduced-motion: reduce) {
  .agent-cat-fade-enter-active,
  .agent-cat-fade-leave-active { transition: none; }
}
</style>
