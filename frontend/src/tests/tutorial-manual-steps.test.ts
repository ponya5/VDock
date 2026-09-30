// DL-131: the tour never advances on its own — no `optional` skip, no
// `advanceOnPath` route trigger. A step whose target is absent renders
// as a centered card; the spotlight re-anchors continuously so it can't
// sit stale over the wrong content (the header auto-hide case).
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { flushPromises, mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(() => Promise.resolve({ data: {} })),
    post: vi.fn(() => Promise.resolve({ data: {} })),
    put: vi.fn(() => Promise.resolve({ data: { success: true } })),
    delete: vi.fn(),
  },
}))

vi.mock('@/api/socket', () => ({
  default: {
    on: vi.fn(),
    off: vi.fn(),
    isConnected: () => false,
    connect: vi.fn(),
    broadcastSettingsChange: vi.fn(),
  },
}))

import TutorialTour from '@/components/TutorialTour.vue'
import { useTutorial, TUTORIAL_STEPS } from '@/services/tutorial'

const serviceSrc = readFileSync(resolve(__dirname, '../services/tutorial.ts'), 'utf-8')
const tourSrc = readFileSync(resolve(__dirname, '../components/TutorialTour.vue'), 'utf-8')

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div/>' } },
      { path: '/settings', component: { template: '<div/>' } },
      { path: '/profiles', component: { template: '<div/>' } },
    ],
  })
}

async function mountTour() {
  const router = makeRouter()
  await router.push('/')
  const wrapper = mount(TutorialTour, {
    global: {
      plugins: [router],
      stubs: { FontAwesomeIcon: true },
    },
  })
  return wrapper
}

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
})

describe('manual-only progression', () => {
  it('no step declares an auto-advance trigger', () => {
    for (const s of TUTORIAL_STEPS) {
      expect('advanceOnPath' in s, `step "${s.title}" must not auto-advance`).toBe(false)
    }
    expect(serviceSrc).not.toContain('advanceOnPath')
  })

  it('a step with a missing target stays put — centered card, no skip', async () => {
    const wrapper = await mountTour()
    const tour = useTutorial()
    tour.start()
    // Jump to the 'Scenes & Pages' step (index 2): its target selectors
    // don't exist in this bare mount — the old code auto-skipped to 4.
    tour.state.stepIndex = 2
    await flushPromises()
    // waitForEl polls up to 2.5s — give it room, then the step must
    // still be index 2 with a centered (untargeted) bubble.
    await new Promise((r) => setTimeout(r, 2700))
    expect(tour.state.stepIndex).toBe(2)
    // The overlay is Teleport'ed to <body> — outside the wrapper tree.
    expect(document.querySelector('.tour-bubble')).not.toBeNull()
    expect(document.querySelector('.tour-spotlight')).toBeNull()
    expect(document.querySelector('.tour-dim')).not.toBeNull()
  }, 8000)

  it('next/back are the only way the index moves', async () => {
    await mountTour()
    const tour = useTutorial()
    tour.start()
    expect(tour.state.stepIndex).toBe(0)
    tour.next()
    expect(tour.state.stepIndex).toBe(1)
    tour.back()
    expect(tour.state.stepIndex).toBe(0)
    tour.back() // isFirst clamp
    expect(tour.state.stepIndex).toBe(0)
  })
})

describe('wiring (source)', () => {
  it('the route watcher no longer carries an advanceOnPath branch', () => {
    expect(tourSrc).not.toContain('advanceOnPath')
    expect(tourSrc).not.toContain('tour.next()') // no programmatic advance anywhere
  })

  it('re-anchors the spotlight on an interval while the tour is active', () => {
    expect(tourSrc).toContain('startReanchor')
    expect(tourSrc).toContain('setInterval')
    expect(tourSrc).toContain('getBoundingClientRect')
  })
})
