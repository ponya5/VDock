// DL-153 — robot render components.
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import RobotFace from '@/components/screensaver/robot/RobotFace.vue'
import RobotBubble from '@/components/screensaver/robot/RobotBubble.vue'
import { FaceAnimator } from '@/services/robot/animator'
import { PointerSense } from '@/services/robot/pointerSense'
import { setActivePinia, createPinia } from 'pinia'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import RobotStage from '@/components/screensaver/RobotStage.vue'

vi.mock('@/composables/useSystemStats', () => ({ useSystemStats: () => ({ stats: { value: null }, start: () => {}, stop: () => {} }) }))
vi.mock('@/composables/useWeather', () => ({ useWeather: () => ({ weather: { value: null }, start: () => {}, stop: () => {} }) }))

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
    expect(w.find('g[data-accessory="headphones"]').exists()).toBe(true)
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

describe('RobotStage', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => setTimeout(() => cb(performance.now()), 16) as unknown as number)
    vi.stubGlobal('cancelAnimationFrame', (id: number) => clearTimeout(id))
  })
  afterEach(() => vi.unstubAllGlobals())

  it('renders face and clock halves with live data attributes', async () => {
    const w = mount(RobotStage, { attachTo: document.body })
    await new Promise(r => setTimeout(r, 80))
    expect(w.find('.rs-face svg.robot-face').exists()).toBe(true)
    expect(w.find('.rs-clock').exists()).toBe(true)
    expect(w.attributes('data-mood')).toBe('funny')
    w.unmount()
  })

  it('stops the animation loop on unmount (Review Focus 3)', async () => {
    const cancel = vi.fn((id: number) => clearTimeout(id))
    vi.stubGlobal('cancelAnimationFrame', cancel)
    const w = mount(RobotStage, { attachTo: document.body })
    await new Promise(r => setTimeout(r, 50))
    w.unmount()
    expect(cancel).toHaveBeenCalled()
  })

  it('a touch drag on the face cancels the synthetic click; a tap does not (Review Focus 1)', async () => {
    const w = mount(RobotStage, { attachTo: document.body })
    const face = w.find('.rs-face').element
    const touch = (type: string, x: number, y: number) => {
      const e = new Event(type, { bubbles: true, cancelable: true }) as any
      e.touches = type === 'touchend' ? [] : [{ clientX: x, clientY: y }]
      e.changedTouches = [{ clientX: x, clientY: y }]
      face.dispatchEvent(e)
      return e as Event
    }
    touch('touchstart', 100, 100)
    touch('touchmove', 160, 100)
    expect(touch('touchend', 160, 100).defaultPrevented).toBe(true)
    touch('touchstart', 100, 100)
    expect(touch('touchend', 102, 101).defaultPrevented).toBe(false)
    w.unmount()
  })

  it('a finger lift (touch pointerleave) is not a lost-pointer reaction; mouse leave is', async () => {
    const leave = vi.spyOn(PointerSense.prototype, 'leave')
    const w = mount(RobotStage, { attachTo: document.body })
    const fire = (pointerType: string) => {
      const e = new Event('pointerleave') as any
      e.pointerType = pointerType
      w.element.dispatchEvent(e)
    }
    fire('touch')
    expect(leave).not.toHaveBeenCalled()
    fire('mouse')
    expect(leave).toHaveBeenCalledTimes(1)
    w.unmount()
    leave.mockRestore()
  })

  it('touchstart on the face does not reach the saver root', () => {
    const w = mount(RobotStage, { attachTo: document.body })
    const seen = vi.fn()
    document.body.addEventListener('touchstart', seen)
    const e = new Event('touchstart', { bubbles: true }) as any
    e.touches = [{ clientX: 1, clientY: 1 }]
    w.find('.rs-face').element.dispatchEvent(e)
    expect(seen).not.toHaveBeenCalled()
    document.body.removeEventListener('touchstart', seen)
    w.unmount()
  })
})

describe('ScreenSaver wiring', () => {
  const src = readFileSync(resolve(__dirname, '../components/ScreenSaver.vue'), 'utf8')
  it('mounts RobotStage in robot mode and hides widgets + now playing', () => {
    expect(src).toMatch(/<RobotStage v-else-if="robotMode" \/>/)
    expect(src).toMatch(/robotMode = computed\(\(\) => effectiveStyle\.value === 'robot' && !props\.layoutEdit\)/)
    expect(src).toMatch(/!statsMode\.value && !robotMode\.value/)
    expect(src).toMatch(/v-if="!spectrumBackdrop && !robotMode"/)
  })
})
