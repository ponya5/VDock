// DL-129 — the Now Playing deck button: a 2-cell live track card under
// Media Controls. The face renders the SMTC feed (art, title, artist,
// state, progress), and a tap toggles play/pause through the normal
// cross-platform path — the action itself never reaches the backend.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { flushPromises, mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

const socketHandlers = new Map<string, (payload: unknown) => void>()
const apiGet = vi.fn()
const apiPost = vi.fn()

vi.mock('@/api/socket', () => ({
  default: {
    on: (event: string, cb: (payload: unknown) => void) => socketHandlers.set(event, cb),
    off: (event: string) => socketHandlers.delete(event),
    isConnected: () => true,
    connect: vi.fn(),
    broadcastSettingsChange: vi.fn(),
  },
}))

vi.mock('@/api/client', () => ({
  default: {
    get: (...args: unknown[]) => apiGet(...args),
    post: (...args: unknown[]) => apiPost(...args),
    put: vi.fn(() => Promise.resolve({ data: { success: true } })),
    delete: vi.fn(),
  },
}))

import { useDashboardStore } from '@/stores/dashboard'
import { createDefaultScene } from '@/utils/defaultProfile'
import type { Button } from '@/types'

const catalog = readFileSync(
  resolve(__dirname, '../../../backend/actions/catalog.py'), 'utf-8')
const typesSrc = readFileSync(resolve(__dirname, '../types/index.ts'), 'utf-8')
const templates = readFileSync(resolve(__dirname, '../data/buttonTemplates.ts'), 'utf-8')
const presets = readFileSync(resolve(__dirname, '../data/presets/system.ts'), 'utf-8')

function trackPayload(over: Record<string, unknown> = {}) {
  return {
    playing: true,
    title: 'Song',
    artist: 'Artist',
    album: 'Album',
    source_app: 'spotify.exe',
    position_s: 42.5,
    duration_s: 201,
    has_art: true,
    ts: 1759200000,
    ...over,
  }
}

function makeButton(): Button {
  return {
    id: 'np1',
    label: 'Now Playing',
    secondary_label: '',
    icon: ['fas', 'music'],
    icon_type: 'fontawesome',
    action: { type: 'now_playing', config: {} },
    shape: 'rounded',
    position: { col: 3, row: 1 },
    size: { cols: 2, rows: 1 },
    enabled: true,
  }
}

/** Fresh nowPlaying singleton per mount — the service guards on a
 *  module-level `initialized` flag, so re-importing DeckButton after
 *  resetModules binds the face to a clean feed (otherwise the track set
 *  by one test leaks into the next). */
async function mountFace() {
  vi.resetModules()
  const { default: DeckButton } = await import('@/components/DeckButton.vue')
  const wrapper = mount(DeckButton, {
    props: { button: makeButton() },
    global: { stubs: { FontAwesomeIcon: true } },
  })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  setActivePinia(createPinia())
  socketHandlers.clear()
  apiGet.mockReset().mockResolvedValue({
    data: { success: true, available: false, track: null },
  })
  apiPost.mockReset().mockResolvedValue({ data: { success: true } })
})

describe('now_playing catalog wiring', () => {
  it('is a Media Controls catalog entry running on the frontend', () => {
    expect(catalog).toContain("id='now_playing'")
    const block = catalog.slice(catalog.indexOf("id='now_playing'"))
    expect(block).toContain("category='media'")
    expect(block).toContain("action_type='now_playing'")
    // RUNS_FRONTEND: the tap is client-orchestrated (play/pause toggle),
    // not a widget that never dispatches and not a backend keypress.
    expect(block.slice(0, block.indexOf('description'))).toContain('runs_on=RUNS_FRONTEND')
  })

  it('is in the frontend ActionType union', () => {
    expect(typesSrc).toContain("'now_playing'")
  })

  it('is offered under Media Controls in templates and presets', () => {
    expect(templates).toContain("type: 'now_playing'")
    expect(templates).toContain("category: 'media'")
    expect(presets).toContain("type: 'now_playing'")
    // Every create path stamps the 2-cell span.
    expect(presets).toContain('size: { rows: 1, cols: 2 }')
    expect(templates).toContain('size: { rows: 1, cols: 2 }')
  })
})

describe('default Media scene', () => {
  it('ships a 2-wide Now Playing card that fits the grid without collisions', () => {
    const scene = createDefaultScene()
    const page = scene.pages[0]
    const np = page.buttons.find((b) => b.action?.type === 'now_playing')
    expect(np).toBeDefined()
    expect(np!.size).toEqual({ rows: 1, cols: 2 })

    const { rows, cols } = page.grid_config
    expect(np!.position.col + np!.size.cols).toBeLessThanOrEqual(cols)
    expect(np!.position.row + np!.size.rows).toBeLessThanOrEqual(rows)

    for (const other of page.buttons) {
      if (other === np) continue
      const overlap = !(
        np!.position.row + np!.size.rows <= other.position.row ||
        other.position.row + other.size.rows <= np!.position.row ||
        np!.position.col + np!.size.cols <= other.position.col ||
        other.position.col + other.size.cols <= np!.position.col
      )
      expect(overlap, `overlaps "${other.label}"`).toBe(false)
    }
  })

  it('uses the contextual Play/Stop transport instead of standalone Stop', () => {
    const scene = createDefaultScene()
    const actions = scene.pages[0].buttons.map(
      (b) => b.action?.type === 'cross_platform' ? b.action.config?.action : undefined)
    expect(actions).toContain('media_play_stop')
    expect(actions).not.toContain('media_stop')
    expect(actions).not.toContain('media_play_pause')
  })
})

describe('now_playing face', () => {
  it('renders the idle state when nothing is playing', async () => {
    apiGet.mockResolvedValue({
      data: { success: true, available: true, track: null },
    })
    const wrapper = await mountFace()
    expect(wrapper.find('.np-face').exists()).toBe(true)
    expect(wrapper.text()).toContain('Nothing playing')
  })

  it('tells the user when no media session exists at all', async () => {
    const wrapper = await mountFace() // default mock: available=false
    expect(wrapper.text()).toContain('No media session')
  })

  it('renders title, artist and source for a live track', async () => {
    // Art is fetched via the authed client and shown as a blob: URL.
    URL.createObjectURL = vi.fn(() => 'blob:art')
    URL.revokeObjectURL = vi.fn()
    apiGet.mockImplementation((url: string) => Promise.resolve({
      data: url === '/now-playing/art'
        ? new Blob(['x'], { type: 'image/jpeg' })
        : { success: true, available: true, track: trackPayload() },
    }))
    const wrapper = await mountFace()
    expect(wrapper.find('.np-title').text()).toBe('Song')
    expect(wrapper.find('.np-artist').text()).toBe('Artist · Spotify')
    expect(wrapper.find('.np-art-img').exists()).toBe(true)
    expect(wrapper.text()).toContain('Playing')
    expect(wrapper.find('.np-progress-fill').exists()).toBe(true)
  })

  it('shows Paused and no progress fill when the app reports no duration', async () => {
    apiGet.mockResolvedValue({
      data: {
        success: true, available: true,
        track: trackPayload({ playing: false, duration_s: undefined, has_art: false }),
      },
    })
    const wrapper = await mountFace()
    expect(wrapper.text()).toContain('Paused')
    expect(wrapper.find('.np-art-img').exists()).toBe(false)
    expect(wrapper.find('.np-progress-fill').exists()).toBe(false)
  })
})

describe('now_playing press', () => {
  it('toggles play/pause through cross_platform instead of dispatching itself', async () => {
    const store = useDashboardStore()
    await store.executeButtonAction(makeButton())
    expect(apiPost).toHaveBeenCalledWith('/actions/execute', {
      action: { type: 'cross_platform', config: { action: 'media_play_pause' } },
      button_id: 'np1',
    })
    // The widget type itself must never be the dispatched action.
    for (const call of apiPost.mock.calls) {
      expect((call[1] as { action: { type: string } }).action.type).not.toBe('now_playing')
    }
  })
})
