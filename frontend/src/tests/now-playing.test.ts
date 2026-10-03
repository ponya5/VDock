// DL-116 — nowPlaying service (W1): socket subscription, REST re-sync on
// connect, empty-payload normalization, and the art URL cache-buster.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const socketHandlers = new Map<string, (payload: unknown) => void>()
const apiGet = vi.fn()

vi.mock('@/api/socket', () => ({
  default: {
    on: (event: string, cb: (payload: unknown) => void) => socketHandlers.set(event, cb),
    off: (event: string) => socketHandlers.delete(event),
    isConnected: () => true,
    connect: vi.fn(),
  },
}))

vi.mock('@/api/client', () => ({
  default: { get: (...args: unknown[]) => apiGet(...args) },
}))

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

/** Fresh singleton bound to the mocked socket + api for each test. */
async function freshService() {
  vi.resetModules()
  const mod = await import('@/services/nowPlaying')
  const svc = mod.useNowPlaying()
  await flushPromises() // initial /now-playing re-sync
  return svc
}

/** Route the art fetch to a blob; everything else gets `sync`. */
function mockApi(sync: unknown) {
  apiGet.mockReset().mockImplementation((url: string) =>
    url === '/now-playing/art'
      ? Promise.resolve({ data: new Blob(['x'], { type: 'image/jpeg' }) })
      : Promise.resolve({ data: sync }))
}

beforeEach(() => {
  socketHandlers.clear()
  mockApi({ success: true, available: false, track: null })
  // jsdom has no object-URL support; derive a stable fake from the call order.
  let n = 0
  URL.createObjectURL = vi.fn(() => `blob:art-${++n}`)
  URL.revokeObjectURL = vi.fn()
})

describe('nowPlaying service', () => {
  it('starts in the loading state until the first sync resolves', async () => {
    apiGet.mockReturnValue(new Promise(() => {})) // never resolves
    const svc = await freshService()
    expect(svc.available.value).toBeNull()
    expect(svc.track.value).toBeNull()
  })

  it('maps a now_playing socket payload and implies available', async () => {
    const svc = await freshService()
    expect(svc.available.value).toBe(false) // REST said unsupported…

    socketHandlers.get('now_playing')?.(trackPayload())

    // …but a socket event means the monitor is live — trust it.
    expect(svc.available.value).toBe(true)
    expect(svc.track.value?.title).toBe('Song')
    expect(svc.playing.value).toBe(true)
  })

  it('normalizes the empty "nothing plays" payload to a null track', async () => {
    const svc = await freshService()
    socketHandlers.get('now_playing')?.(trackPayload())
    socketHandlers.get('now_playing')?.({
      playing: false, title: '', artist: '', album: '',
      source_app: '', has_art: false, ts: 2,
    })

    expect(svc.track.value).toBeNull()
    expect(svc.playing.value).toBe(false)
    expect(svc.available.value).toBe(true) // supported, just silent
  })

  it('fetches art through the authed client as a blob URL, only when has_art', async () => {
    const svc = await freshService()
    socketHandlers.get('now_playing')?.(trackPayload({ ts: 123 }))
    await flushPromises()
    expect(apiGet).toHaveBeenCalledWith(
      '/now-playing/art', { ts: 123 }, { responseType: 'blob' },
    )
    expect(svc.artUrl.value).toMatch(/^blob:/)

    socketHandlers.get('now_playing')?.(trackPayload({ has_art: false, ts: 124 }))
    expect(svc.artUrl.value).toBeNull()
  })

  it('drops the art when the fetch fails', async () => {
    const svc = await freshService()
    apiGet.mockRejectedValue(new Error('401'))
    socketHandlers.get('now_playing')?.(trackPayload({ ts: 5 }))
    await flushPromises()
    expect(svc.artUrl.value).toBeNull()
  })

  it('re-syncs from GET /api/now-playing on connect', async () => {
    apiGet.mockResolvedValue({
      data: { success: true, available: true, track: trackPayload({ ts: 9 }) },
    })
    const svc = await freshService()

    expect(apiGet).toHaveBeenCalledWith('/now-playing')
    expect(svc.available.value).toBe(true)
    expect(svc.track.value?.title).toBe('Song')

    apiGet.mockResolvedValue({
      data: { success: true, available: true, track: null },
    })
    socketHandlers.get('connect')?.()
    await flushPromises()
    expect(svc.track.value).toBeNull()
  })

  it('keeps the last state when the REST sync fails', async () => {
    const svc = await freshService()
    socketHandlers.get('now_playing')?.(trackPayload())
    expect(svc.track.value?.title).toBe('Song')

    apiGet.mockRejectedValue(new Error('offline'))
    socketHandlers.get('connect')?.()
    await flushPromises()

    expect(svc.track.value?.title).toBe('Song') // kept, not blanked
  })
})

describe('NowPlayingWidget', () => {
  async function freshWidget() {
    vi.resetModules()
    const mod = await import('@/components/screensaver/NowPlayingWidget.vue')
    await import('@/services/nowPlaying') // warm the same fresh module
    return mod.default
  }

  const mountOpts = { global: { stubs: { FontAwesomeIcon: true } } }

  it('renders the track: section head, title, artist, source tag, art', async () => {
    mockApi({ success: true, available: true, track: trackPayload() })
    const Widget = await freshWidget()
    const wrapper = mount(Widget, mountOpts)
    await flushPromises()

    expect(wrapper.text()).toContain('Now Playing')
    expect(wrapper.text()).toContain('Song')
    expect(wrapper.text()).toContain('Artist')
    expect(wrapper.text()).toContain('Spotify') // '.exe' stripped
    const img = wrapper.find('img')
    expect(img.attributes('src')).toMatch(/^blob:/)
    expect(wrapper.find('.np-progress').exists()).toBe(true)
  })

  it('shows the unsupported empty state when available is false', async () => {
    const Widget = await freshWidget()
    const wrapper = mount(Widget, mountOpts)
    await flushPromises() // REST resolved {available:false}

    expect(wrapper.text()).toContain('Not supported on this system')
    expect(wrapper.find('.np-art').exists()).toBe(false)
  })

  it('shows "Nothing playing" when supported but silent', async () => {
    apiGet.mockResolvedValue({
      data: { success: true, available: true, track: null },
    })
    const Widget = await freshWidget()
    const wrapper = mount(Widget, mountOpts)
    await flushPromises()

    expect(wrapper.text()).toContain('Nothing playing')
  })

  it('hides the progress bar when duration is unknown', async () => {
    apiGet.mockResolvedValue({
      data: {
        success: true, available: true,
        track: trackPayload({ duration_s: 0, has_art: false }),
      },
    })
    const Widget = await freshWidget()
    const wrapper = mount(Widget, mountOpts)
    await flushPromises()

    expect(wrapper.find('.np-progress').exists()).toBe(false)
    expect(wrapper.find('img').exists()).toBe(false) // music icon fallback
  })
})
