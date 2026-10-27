// DL-153 — robot render components.
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RobotFace from '@/components/screensaver/robot/RobotFace.vue'
import RobotBubble from '@/components/screensaver/robot/RobotBubble.vue'
import { FaceAnimator } from '@/services/robot/animator'

function frameAfter(setup: (a: FaceAnimator) => void, ms = 1000) {
  const a = new FaceAnimator(() => 0.5)
  setup(a)
  for (let t = 0; t < ms; t += 16.7) a.step(16.7, t)
  return a.frame()
}

describe('RobotFace', () => {
  it('draws two eyes and a mouth from the frame', () => {
    const w = mount(RobotFace, { props: { frame: frameAfter(() => {}), level: 0 } })
    expect(w.findAll('[data-part="eye"]')).toHaveLength(2)
    expect(w.find('[data-part="mouth"]').attributes('d')).toMatch(/^M/)
    expect(w.find('svg').attributes('data-expression')).toBe('neutral')
  })

  it('shows glyph eyes, icons, accessories and props when present', () => {
    const f = frameAfter(a => { a.setExpression('love'); a.setAccessory('headphones'); a.addProp('notes') }, 600)
    const w = mount(RobotFace, { props: { frame: f, level: 0 } })
    expect(w.findAll('[data-glyph="heart"]')).toHaveLength(2)
    expect(w.find('[data-accessory="headphones"]').exists()).toBe(true)
    expect(w.find('[data-prop="notes"]').exists()).toBe(true)
    const g = mount(RobotFace, { props: { frame: frameAfter(a => a.setIcon('exclaim')), level: 0 } })
    expect(g.find('svg').attributes('data-icon')).toBe('exclaim')
  })

  it('uses a static glow filter (never animated)', () => {
    const w = mount(RobotFace, { props: { frame: frameAfter(() => {}), level: 0 } })
    expect(w.find('filter#robot-glow').exists()).toBe(true)
    expect(w.html()).not.toMatch(/<animate/)
  })
})

describe('RobotBubble', () => {
  it('renders the quip text, nothing when null', () => {
    expect(mount(RobotBubble, { props: { text: 'Bold choice.' } }).text()).toContain('Bold choice.')
    expect(mount(RobotBubble, { props: { text: null } }).find('.robot-bubble').exists()).toBe(false)
  })
})
