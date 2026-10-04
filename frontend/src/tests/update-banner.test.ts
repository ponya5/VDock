// DL-150 - update store + banner: visibility, per-launch dismissal,
// Update now vs Download, and the 403 "update from your PC" hint.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import type { UpdateStatus } from '@/api/update'

const api = vi.hoisted(() => ({
  getUpdateStatus: vi.fn(),
  installUpdate: vi.fn(),
  getHealthVersion: vi.fn(),
}))
vi.mock('@/api/update', () => api)
const reload = vi.hoisted(() => ({ reloadPage: vi.fn() }))
vi.mock('@/utils/reloadPage', () => reload)

import { useUpdateStore } from '@/stores/update'
import UpdateBanner from '@/components/UpdateBanner.vue'

const base: UpdateStatus = {
  current: '2.3.0',
  latest: '2.4.0',
  available: true,
  notes: '',
  releaseUrl: 'https://github.com/ponya5/VDock/releases/tag/v2.4.0',
  downloadUrl: 'https://github.com/ponya5/VDock/releases/download/v2.4.0/x.exe',
  installKind: 'windows-installer',
  canAutoInstall: true,
  checkedAt: 1,
  error: null,
  state: 'idle',
}

async function mountBanner(over: Partial<UpdateStatus> = {}) {
  api.getUpdateStatus.mockResolvedValue({ ...base, ...over })
  const w = mount(UpdateBanner)
  await flushPromises()
  return w
}

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
  vi.clearAllMocks()
})

describe('UpdateBanner', () => {
  it('shows when an update is available', async () => {
    const w = await mountBanner()
    expect(w.text()).toContain('VDock 2.4.0 is available')
  })

  it('is hidden when nothing is available', async () => {
    const w = await mountBanner({ available: false })
    expect(w.find('[data-testid="update-banner"]').exists()).toBe(false)
  })

  it('hides after Later for that version and reappears for a newer one', async () => {
    const w = await mountBanner()
    await w.find('[data-testid="update-later"]').trigger('click')
    expect(w.find('[data-testid="update-banner"]').exists()).toBe(false)

    api.getUpdateStatus.mockResolvedValue({ ...base, latest: '2.5.0' })
    await useUpdateStore().refresh()
    await flushPromises()
    expect(w.text()).toContain('VDock 2.5.0 is available')
  })

  it('prompts again on the next launch after Later', async () => {
    const first = await mountBanner()
    await first.find('[data-testid="update-later"]').trigger('click')
    expect(first.find('[data-testid="update-banner"]').exists()).toBe(false)
    first.unmount()
    useUpdateStore().stop()

    setActivePinia(createPinia()) // fresh launch
    const w = await mountBanner()
    expect(w.text()).toContain('VDock 2.4.0 is available')
  })

  it('ignores a dismissal persisted by older builds', async () => {
    localStorage.setItem('vdock.update.dismissedVersion', '2.4.0')
    const w = await mountBanner()
    expect(w.text()).toContain('VDock 2.4.0 is available')
  })

  it('offers Update now when canAutoInstall', async () => {
    const w = await mountBanner()
    expect(w.find('[data-testid="update-now"]').exists()).toBe(true)
    expect(w.find('[data-testid="update-download"]').exists()).toBe(false)
  })

  it('offers Download (opens downloadUrl) when it cannot auto-install', async () => {
    const open = vi.spyOn(window, 'open').mockReturnValue(null)
    const w = await mountBanner({ canAutoInstall: false, installKind: 'mac' })
    expect(w.find('[data-testid="update-now"]').exists()).toBe(false)
    await w.find('[data-testid="update-download"]').trigger('click')
    expect(open).toHaveBeenCalledWith(base.downloadUrl, '_blank', 'noopener,noreferrer')
    open.mockRestore()
  })

  it('shows the PC hint when install returns 403', async () => {
    api.installUpdate.mockRejectedValue({ response: { status: 403 } })
    const w = await mountBanner()
    await w.find('[data-testid="update-now"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-testid="update-now"]').exists()).toBe(false)
    expect(w.find('[data-testid="update-pc-hint"]').text()).toBe('Update from your PC')
  })

  it('shows progress text while installing', async () => {
    const w = await mountBanner({ state: 'downloading', stateMessage: 'Downloading 40%' })
    expect(w.find('[data-testid="update-progress"]').text()).toBe('Downloading 40%')
    useUpdateStore().stop()
  })
})

describe('update store', () => {
  it('survives a localStorage that throws', async () => {
    const get = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('blocked') })
    const set = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked') })
    setActivePinia(createPinia())
    api.getUpdateStatus.mockResolvedValue(base)
    const store = useUpdateStore()
    await store.refresh()
    expect(store.visible).toBe(true)
    expect(() => store.dismiss()).not.toThrow()
    expect(store.visible).toBe(false)
    get.mockRestore()
    set.mockRestore()
  })

  it('polls every 2s while downloading', async () => {
    vi.useFakeTimers()
    api.getUpdateStatus.mockResolvedValue({ ...base, state: 'downloading' })
    const store = useUpdateStore()
    await store.refresh()
    expect(api.getUpdateStatus).toHaveBeenCalledTimes(1)
    await vi.advanceTimersByTimeAsync(2000)
    expect(api.getUpdateStatus).toHaveBeenCalledTimes(2)
    store.stop()
    vi.useRealTimers()
  })

  it('reloads once /health reports a new version after restarting', async () => {
    vi.useFakeTimers()
    api.getUpdateStatus.mockResolvedValue({ ...base, state: 'restarting' })
    api.getHealthVersion.mockResolvedValueOnce('2.3.0').mockResolvedValue('2.4.0')
    const store = useUpdateStore()
    await store.refresh()
    await vi.advanceTimersByTimeAsync(2000)
    expect(reload.reloadPage).not.toHaveBeenCalled()
    await vi.advanceTimersByTimeAsync(2000)
    expect(reload.reloadPage).toHaveBeenCalled()
    store.stop()
    vi.useRealTimers()
  })
})

describe('after an update', () => {
  it('reloads when the backend comes back on a new version, even if restarting was never seen', async () => {
    setActivePinia(createPinia())
    const store = useUpdateStore()
    api.getUpdateStatus.mockResolvedValueOnce({ ...base, current: '2.3.1', state: 'installing', stateMessage: 'Building frontend' })
    await store.refresh()
    expect(reload.reloadPage).not.toHaveBeenCalled()

    // Backend restarted between polls: the next answer is already the new version.
    api.getUpdateStatus.mockResolvedValueOnce({ ...base, current: '2.4.0', available: false, state: 'idle' })
    await store.refresh()
    expect(reload.reloadPage).toHaveBeenCalledTimes(1)
    store.stop()
  })

  it('does not reload while the version is unchanged', async () => {
    setActivePinia(createPinia())
    const store = useUpdateStore()
    api.getUpdateStatus.mockResolvedValue(base)
    await store.refresh()
    await store.refresh()
    expect(reload.reloadPage).not.toHaveBeenCalled()
  })
})
