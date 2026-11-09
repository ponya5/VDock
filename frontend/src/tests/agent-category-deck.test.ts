// DL-166: desktop / panel groups view - rail + a synthetic read-only page for the selected category.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { computed, defineComponent, h, ref, toRaw } from 'vue'
import { mount } from '@vue/test-utils'
import type { Button, Scene } from '@/types'
import AgentCategoryDeck from '@/components/AgentCategoryDeck.vue'
import { resetAgentSceneViews } from '@/composables/useAgentSceneView'

const agent = { state: ref<'ready' | 'working' | 'permission'>('ready'), running: ref(true) }
vi.mock('@/composables/useAgentSession', () => ({
  useAgentSession: () => ({
    currentState: computed(() => agent.state.value),
    isAgentPossiblyRunning: computed(() => agent.running.value),
  }),
}))

const gridProps: { page?: any } = {}
const DeckGridStub = defineComponent({
  name: 'DeckGrid',
  props: ['page', 'isEditMode'],
  emits: ['button-click', 'button-press', 'button-release', 'double-tap'],
  setup(props, { emit }) {
    return () => {
      gridProps.page = props.page
      return h('div', { class: 'grid-stub' }, props.page.buttons.map((b: Button) =>
        h('button', { class: 'stub-btn', 'data-id': b.id, onClick: () => emit('button-click', b) }, b.label)))
    }
  },
})

const mk = (id: string, label: string, type: string, row: number, col: number): Button => ({
  id, label, shape: 'rounded', position: { row, col }, size: { rows: 1, cols: 2 },
  enabled: true, action: { type, config: {} },
}) as Button

function makeScene(): Scene {
  return {
    id: 'scene-deck', name: 'Claude Code',
    pages: [{ id: 'p', name: 'P', grid_config: { rows: 2, cols: 4 }, buttons: [
      mk('open', 'Open Claude', 'claude_continue', 0, 0),
      mk('int', 'Interrupt', 'cc_interrupt', 0, 1),
      mk('mode', 'Mode', 'cc_mode', 1, 0),
      mk('clear', 'New Session', 'cc_clear', 1, 1),
      mk('compact', 'Compact', 'cc_compact', 1, 2),
    ] }],
  } as Scene
}

function mountDeck(scene = makeScene()) {
  return {
    scene,
    w: mount(AgentCategoryDeck, {
      props: { scene },
      global: { stubs: { DeckGrid: DeckGridStub, FontAwesomeIcon: true } },
    }),
  }
}

beforeEach(() => {
  resetAgentSceneViews()
  agent.state.value = 'ready'
  agent.running.value = true
})

describe('AgentCategoryDeck', () => {
  it('renders one tab per non-empty group with counts and the first selected', () => {
    const { w } = mountDeck()
    const tabs = w.findAll('[role="tab"]')
    expect(tabs.map(t => t.attributes('data-category'))).toEqual(['session', 'control', 'context'])
    expect(tabs.map(t => t.find('.acr-count').text())).toEqual(['2', '1', '2'])
    expect(tabs[0].attributes('aria-selected')).toBe('true')
    expect(tabs[1].attributes('aria-selected')).toBe('false')
    expect(w.find('[role="tabpanel"]').attributes('aria-labelledby')).toBe('agent-cat-tab-session')
  })

  it('click and ArrowDown change the selection and the grid contents', async () => {
    const { w } = mountDeck()
    await w.find('[data-category="context"]').trigger('click')
    expect(w.find('[data-category="context"]').attributes('aria-selected')).toBe('true')
    expect(gridProps.page.buttons.map((b: Button) => b.id)).toEqual(['clear', 'compact'])

    await w.find('[data-category="context"]').trigger('keydown', { key: 'ArrowUp' })
    expect(w.find('[data-category="control"]').attributes('aria-selected')).toBe('true')
    await w.find('[data-category="control"]').trigger('keydown', { key: 'ArrowDown' })
    expect(w.find('[data-category="context"]').attributes('aria-selected')).toBe('true')
  })

  it('hands DeckGrid a synthetic page: constant id, re-flowed positions, 1x1 cells', async () => {
    const { w } = mountDeck()
    const first = gridProps.page
    expect(first.id).toBe('scene-deck::groups')
    expect(first.grid_config).toEqual({ rows: 2, cols: 4 })
    expect(first.buttons.map((b: Button) => b.position)).toEqual([{ row: 0, col: 0 }, { row: 0, col: 1 }])
    expect(first.buttons.every((b: Button) => b.size.rows === 1 && b.size.cols === 1)).toBe(true)
    await w.find('[data-category="context"]').trigger('click')
    expect(gridProps.page.id).toBe('scene-deck::groups')
  })

  it('re-emits clicks with the original Button object', async () => {
    const { w, scene } = mountDeck()
    await w.find('.stub-btn[data-id="int"]').trigger('click')
    const emitted = w.emitted('button-click')![0][0]
    // Same object (the test harness wraps props in a reactive proxy, so compare the raw targets).
    expect(toRaw(emitted)).toBe(scene.pages[0].buttons[1])
  })

  it('shows the session badge only while the agent works or needs permission', async () => {
    const { w } = mountDeck()
    expect(w.find('[data-testid="session-badge"]').exists()).toBe(false)
    agent.state.value = 'working'
    await w.vm.$nextTick()
    expect(w.find('[data-testid="session-badge"]').attributes('data-badge')).toBe('working')
    agent.state.value = 'permission'
    await w.vm.$nextTick()
    expect(w.find('[data-testid="session-badge"]').attributes('data-badge')).toBe('permission')
    expect(w.find('[data-category="session"]').attributes('aria-label')).toContain('needs permission')
    agent.state.value = 'ready'
    await w.vm.$nextTick()
    expect(w.find('[data-testid="session-badge"]').exists()).toBe(false)
  })
})
