// DL-145 Phase 5 - a catalog `press: 'hold'` action (Dictate to Agent) is
// push-to-talk: pointerdown dispatches op 'start', pointerup / pointercancel
// dispatch op 'stop' exactly once, and ordinary buttons are untouched.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const executeAction = vi.fn()
const executeButtonAction = vi.fn()

vi.mock('@/stores/dashboard', () => ({
  useDashboardStore: () => ({
    currentProfile: null, currentScene: null, currentPage: null,
    executeAction: (...a: unknown[]) => executeAction(...a),
    executeButtonAction: (...a: unknown[]) => executeButtonAction(...a),
  }),
}))

import DeckButton from '@/components/DeckButton.vue'
import { useActionCatalogStore } from '@/stores/actionCatalog'
import { useButtonActions } from '@/composables/useButtonActions'
import type { Button } from '@/types'

const spec = (action_type: string, press: string) => ({
  id: action_type, action_type, press, label: action_type, category: 'ai',
  icon: ['fas', 'microphone'], description: '', default_config: {},
  config_fields: [], runs_on: 'backend', display_only: false,
  long_running: false, keywords: [],
})

function makeButton(type: string, config: Record<string, unknown> = {}): Button {
  return {
    id: 'b1', label: 'Dictate', secondary_label: '', icon: ['fas', 'microphone'],
    icon_type: 'fontawesome', shape: 'rounded', position: { col: 0, row: 0 },
    size: { cols: 1, rows: 1 }, enabled: true, action: { type, config },
  } as Button
}

function setup(type: string) {
  setActivePinia(createPinia())
  useActionCatalogStore().actions = [
    spec('agent_dictate', 'hold'), spec('agent_prompt', 'run'),
  ] as any
  const actions = useButtonActions()
  // DeckGrid forwards the button's events to these handlers.
  const wrapper = mount(DeckButton, {
    props: {
      button: makeButton(type, { agent: 'claude' }),
      onPress: actions.handleButtonPress,
      onRelease: actions.handleButtonRelease,
      onClick: actions.handleButtonClick,
    },
    global: { stubs: { FontAwesomeIcon: true } },
  })
  wrapper.element.setPointerCapture = () => {}
  return { actions, wrapper }
}

const down = (w: ReturnType<typeof mount>) =>
  w.trigger('pointerdown', { pointerId: 1, pointerType: 'touch' })

beforeEach(() => {
  executeAction.mockReset().mockResolvedValue({ success: true, message: 'ok' })
  executeButtonAction.mockReset().mockResolvedValue({ success: true, message: 'ok' })
})

describe('hold-to-talk dispatch', () => {
  it('pointerdown starts and pointerup stops, once each', async () => {
    const { wrapper } = setup('agent_dictate')
    await down(wrapper)
    expect(executeAction).toHaveBeenCalledTimes(1)
    expect(executeAction).toHaveBeenLastCalledWith(
      { type: 'agent_dictate', config: { agent: 'claude', op: 'start' } }, 'b1')

    await wrapper.trigger('pointerup')
    await wrapper.trigger('pointerup')
    expect(executeAction).toHaveBeenCalledTimes(2)
    expect(executeAction).toHaveBeenLastCalledWith(
      { type: 'agent_dictate', config: { agent: 'claude', op: 'stop' } }, 'b1')
  })

  it('pointercancel stops too, and the trailing click does not start again', async () => {
    const { wrapper } = setup('agent_dictate')
    await down(wrapper)
    await wrapper.trigger('pointercancel')
    await wrapper.trigger('click')

    expect(executeAction.mock.calls.map((c) => c[0].config.op)).toEqual(['start', 'stop'])
    expect(executeButtonAction).not.toHaveBeenCalled()
  })

  it('a bare click (no pointer) never starts dictation', () => {
    const { actions } = setup('agent_dictate')
    actions.handleButtonClick(makeButton('agent_dictate'))
    expect(executeAction).not.toHaveBeenCalled()
    expect(executeButtonAction).not.toHaveBeenCalled()
  })

  it('release of a button that never started sends nothing', () => {
    const { actions } = setup('agent_prompt')
    actions.handleButtonRelease(makeButton('agent_prompt'))
    expect(executeAction).not.toHaveBeenCalled()
  })

  it('a normal tap on a non-hold action still runs once on click', async () => {
    const { actions, wrapper } = setup('agent_prompt')

    await down(wrapper)
    await wrapper.trigger('pointerup')
    await wrapper.trigger('click')

    expect(executeAction).not.toHaveBeenCalled()
    expect(executeButtonAction).toHaveBeenCalledTimes(1)
  })
})
