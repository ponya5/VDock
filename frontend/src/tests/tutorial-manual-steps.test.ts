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

// DL-131 F/U2: steps whose targets live inside DeckHeader must reveal it
// first — showHeader defaults false and autohides, so the spotlight had
// nothing to measure. Mobile skips the reveal (it would replace the
// mobile chrome being spotlighted).
describe('header-targeted steps', () => {
  it('steps pointing into DeckHeader declare needsHeader', () => {
    const scenes = TUTORIAL_STEPS.find((s) => s.title === 'Scenes & Pages')
    const edit = TUTORIAL_STEPS.find((s) => s.title === 'Edit Mode')
    expect(scenes?.needsHeader).toBe(true)
    expect(edit?.needsHeader).toBe(true)
    // Steps not pointing into the header must not force a reveal.
    for (const s of TUTORIAL_STEPS) {
      if (s === scenes || s === edit) continue
      expect(s.needsHeader ?? false, `"${s.title}" must not reveal the header`).toBe(false)
    }
  })

  it('prepareStep reveals via the store, pins the countdown, restores', () => {
    expect(tourSrc).toContain('settingsStore.showHeader = true')
    expect(tourSrc).toContain('.autohide-pill:not(.pinned)')
    expect(tourSrc).toContain('headerRevealedByTour')
    expect(tourSrc).toContain('headerPinnedByTour')
    expect(tourSrc).toContain('restoreDashboardState')
    expect(tourSrc).toContain('isMobileViewport')
  })

  it('agent step spotlights the mobile console as a fallback', () => {
    const agents = TUTORIAL_STEPS.find((s) => s.title === 'Agent Sessions')
    expect(agents?.target).toContain('.agent-action-bar')
    expect(agents?.target).toContain('.mobile-agent-console')
  })

  it('agent step switches to an agent-backed scene before measuring', () => {
    const agents = TUTORIAL_STEPS.find((s) => s.title === 'Agent Sessions')
    expect(agents?.needsAgentScene).toBe(true)
    // The tour hops scenes via the store and restores it when leaving '/'.
    expect(tourSrc).toContain('sceneAppProfile')
    expect(tourSrc).toContain('dashboardStore.setScene')
    expect(tourSrc).toContain('sceneSwitchFrom')
    expect(tourSrc).toContain('restoreDashboardState')
  })
})
