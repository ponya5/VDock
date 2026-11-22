// DL-166 layout: switching between two scenes of the same agent mounts the new surface before the
// old one unmounts; the old one's "hidden" must not clear the new one's "visible".
import { describe, it, expect } from 'vitest'
import { computed, defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { isAgentBarVisible } from '@/services/agentState'
import { trackAgentSurfaceVisibility } from '@/composables/useAgentSession'

const Surface = defineComponent({
  setup() {
    trackAgentSurfaceVisibility(computed(() => 'claude'), computed(() => true))
    return () => h('div')
  },
})

describe('agent surface visibility', () => {
  it('stays visible while a second surface for the same agent is still mounted', () => {
    const oldSurface = mount(Surface)
    const newSurface = mount(Surface)
    oldSurface.unmount()
    expect(isAgentBarVisible('claude')).toBe(true)
    newSurface.unmount()
    expect(isAgentBarVisible('claude')).toBe(false)
  })
})
