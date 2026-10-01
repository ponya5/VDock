// DL-130 follow-up: the header auto-hide indicator is a real countdown
// chip — gradient-border pill with live seconds — not just the 4px line,
// and tapping it pins the header open. The reveal FAB grew again to
// 120×68 with the DL-134 slick redesign (orbit rim + sheen).
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { flushPromises, mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

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

import DeckHeader from '@/components/DeckHeader.vue'
import { useSettingsStore } from '@/stores/settings'
import type { Profile } from '@/types'

const headerSrc = readFileSync(
  resolve(__dirname, '../components/DeckHeader.vue'), 'utf-8')
const viewSrc = readFileSync(
  resolve(__dirname, '../views/DashboardView.vue'), 'utf-8')

function makeProfile(): Profile {
  return {
    id: 'p1',
    name: 'Test',
    description: '',
    theme: 'default',
    scenes: [{
      id: 's1',
      name: 'Media',
      pages: [{ id: 'pg1', name: 'Page 1', buttons: [], grid_config: { rows: 3, cols: 6 } }],
    }],
    dockedButtons: [],
    settings: {
      animationsEnabled: true,
      editModeWiggle: false,
      showLabels: true,
      showTooltips: true,
      defaultGridRows: 3,
      defaultGridCols: 3,
      buttonSize: 1,
    },
    created_at: '',
    updated_at: '',
  } as Profile
}

async function mountHeader() {
  const store = useSettingsStore()
  // startAutohide only runs on the showHeader watcher — mount hidden,
  // then reveal, exactly like the real reveal path.
  store.showHeader = false
  const wrapper = mount(DeckHeader, {
    props: {
      currentProfile: makeProfile(),
      currentScene: makeProfile().scenes[0],
      currentSceneIndex: 0,
      currentPageIndex: 0,
      isEditMode: false,
    },
    global: { stubs: { FontAwesomeIcon: true, Teleport: true } },
  })
  store.showHeader = true
  await flushPromises()
  return wrapper
}

describe('auto-hide countdown pill', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders the seconds countdown while the header is open', async () => {
    const wrapper = await mountHeader()
    const pill = wrapper.find('.autohide-pill')
    expect(pill.exists()).toBe(true)
    expect(pill.text()).toMatch(/\ds/)
    expect(pill.attributes('aria-label')).toContain('tap to keep it open')
  })

  it('tap pins the header — stops the countdown and flips the face', async () => {
    const wrapper = await mountHeader()
    await wrapper.find('.autohide-pill').trigger('click')
    const pill = wrapper.find('.autohide-pill')
    expect(pill.classes()).toContain('pinned')
    expect(pill.text()).toContain('Pinned')
    // And the header stays open well past the 5s window (real timers —
    // the interval is cleared, so waiting it out proves it).
    await new Promise((r) => setTimeout(r, 5400))
    expect(useSettingsStore().showHeader).toBe(true)
  }, 8000)

  it('the countdown ticks down and fires while unpaused', async () => {
    const wrapper = await mountHeader()
    expect(wrapper.find('.pill-secs').text()).toBe('5s')
    // jsdom throttles setInterval under vitest load — the 100 ticks take
    // longer than 5s wall time, so poll until the hide lands.
    await vi.waitFor(
      () => expect(useSettingsStore().showHeader).toBe(false),
      { timeout: 14000, interval: 250 }
    )
    await flushPromises()
    expect(wrapper.find('.autohide-pill').exists()).toBe(false)
  }, 16000)
})

describe('wiring (source)', () => {
  it('pill carries the gradient-border, star and glow layers', () => {
    expect(headerSrc).toContain('pill-stars')
    expect(headerSrc).toContain('pill-glow')
    expect(headerSrc).toContain('background-clip: padding-box, border-box')
    expect(headerSrc).toContain('pill-border-sweep')
  })

  it('pin resumes from the paused remainder, not a fresh 5s', () => {
    expect(headerSrc).toContain('startAutohide(autohideRemainingMs)')
  })

  it('pin state resets when the header hides', () => {
    expect(headerSrc).toContain('autohidePaused.value = false')
  })

  it('the reveal FAB is enlarged to 120×68', () => {
    expect(viewSrc).toContain('max(120px, calc(120px')
    expect(viewSrc).toContain('max(68px, calc(68px')
  })

  it('reduced-motion kills the pill animations', () => {
    const rm = headerSrc.slice(headerSrc.lastIndexOf('prefers-reduced-motion'))
    expect(rm).toContain('pill-stars')
    expect(rm).toContain('pill-circle')
  })
})
