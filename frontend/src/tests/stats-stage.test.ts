// DL-125 — 'stats' screensaver style: the fullscreen system monitor mounts
// via ScreenSaver's style switch, the extended SystemStats mapping carries
// the richer fields, and the stage renders meters/chips/processes with the
// same stale/honest-state contract as the widget.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const apiGet = vi.fn()

vi.mock('@/api/client', () => ({
  default: { get: (...args: unknown[]) => apiGet(...args) },
}))
vi.mock('@/api/socket', () => ({
  default: {
    on: vi.fn(),
    off: vi.fn(),
    isConnected: () => false,
    connect: vi.fn(),
    executeAction: vi.fn(),
    broadcastSettingsChange: vi.fn(),
  },
}))

import { useSystemStats } from '@/composables/useSystemStats'
import { useSettingsStore } from '@/stores/settings'
import StatsStage from '@/components/screensaver/StatsStage.vue'

function metricsPayload(over: Record<string, any> = {}) {
  return {
    data: {
      success: true,
      data: {
        timestamp: '2026-01-02T03:04:05',
        cpu: {
          usage_percent: 42.5,
          frequency_current: 3400,
          per_cpu_percent: [10, 90, 40, 5],
        },
        memory: { usage_percent: 63.2, used_gb: 20.1, total_gb: 31.9 },
        disk: {
          partitions: [
            { device: 'C:\\', mountpoint: 'C:\\', usage_percent: 71.4, used_gb: 500, total_gb: 700 },
            { device: 'D:\\', mountpoint: 'D:\\', usage_percent: 12.0, used_gb: 120, total_gb: 1000 },
          ],
          io_read_mb: 1000,
          io_write_mb: 500,
        },
        network: { bytes_sent_mb: 100, bytes_recv_mb: 250 },
        temperature: { available: true, sensors: [{ current: 55 }, { current: 61 }] },
        battery: { available: true, percent: 87.5, is_charging: true },
        processes: {
          total_processes: 210,
          top_cpu: [
            { name: 'chrome.exe', cpu_percent: 25.4, memory_mb: 900 },
            { name: 'node.exe', cpu_percent: 12.1, memory_mb: 300 },
          ],
          top_memory: [],
        },
        system_info: { hostname: 'TESTBOX', uptime_hours: 51.5 },
        ...over,
      },
    },
  }
}

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
  apiGet.mockReset()
  apiGet.mockResolvedValue(metricsPayload())
})

afterEach(() => {
  vi.useRealTimers()
})

describe('useSystemStats extended mapping (DL-125)', () => {
  it('maps the richer fields from /metrics/all', async () => {
    const s = useSystemStats()
    await s.refresh()
    const v = s.stats.value!
    expect(v.hostname).toBe('TESTBOX')
    expect(v.uptimeHours).toBe(51.5)
    expect(v.cpuPerCore).toEqual([10, 90, 40, 5])
    expect(v.cpuFreqMhz).toBe(3400)
    expect(v.memUsedGb).toBe(20.1)
    expect(v.memTotalGb).toBe(31.9)
    expect(v.diskPartitions.map(p => p.mount)).toEqual(['C:\\', 'D:\\'])
    expect(v.tempC).toBe(61)
    expect(v.batteryPercent).toBe(87.5)
    expect(v.batteryCharging).toBe(true)
    expect(v.processCount).toBe(210)
    expect(v.topProcesses[0].name).toBe('chrome.exe')
  })

  it('orders the system mount first even when another partition is fuller', async () => {
    apiGet.mockResolvedValue(metricsPayload({
      disk: { partitions: [
        { mountpoint: 'D:\\', usage_percent: 99 },
        { mountpoint: 'C:\\', usage_percent: 30 },
      ] },
    }))
    const s = useSystemStats()
    await s.refresh()
    expect(s.stats.value!.diskPartitions[0].mount).toBe('C:\\')
  })

  it('derives disk IO rates from cumulative counters', async () => {
    vi.useFakeTimers()
    const s = useSystemStats()
    await s.refresh()
    expect(s.stats.value!.diskReadBps).toBeNull() // first sample = baseline
    apiGet.mockResolvedValue(metricsPayload({
      disk: {
        partitions: [],
        io_read_mb: 1000 + 100,  // +100 MB over the delta window
        io_write_mb: 500 + 50,
      },
    }))
    vi.advanceTimersByTime(1000)
    await s.refresh()
    expect(s.stats.value!.diskReadBps).toBeGreaterThan(0)
    expect(s.stats.value!.diskWriteBps).toBeGreaterThan(0)
  })

  it('degrades optional fields when sections are absent', async () => {
    apiGet.mockResolvedValue(metricsPayload({
      temperature: { available: false, sensors: [] },
      battery: { available: false },
      processes: undefined,
      system_info: undefined,
    }))
    const s = useSystemStats()
    await s.refresh()
    const v = s.stats.value!
    expect(v.tempC).toBeNull()
    expect(v.batteryPercent).toBeNull()
    expect(v.batteryCharging).toBeNull()
    expect(v.topProcesses).toEqual([])
    expect(v.hostname).toBeNull()
  })
})

describe('StatsStage', () => {
  it('renders the meter cards and footer from live stats', async () => {
    const wrapper = mount(StatsStage)
    await vi.waitFor(() => expect(wrapper.text()).toContain('TESTBOX'))
    expect(wrapper.text()).toContain('up 2d')
    expect(wrapper.text()).toContain('43%')
    expect(wrapper.text()).toContain('chrome.exe')
    expect(wrapper.text()).toContain('61°C')
    expect(wrapper.text()).toContain('Charging 88%')
    expect(wrapper.findAll('.st-part')).toHaveLength(2)
    expect(wrapper.findAll('.st-core')).toHaveLength(4)
    wrapper.unmount()
  })

  it('shows the honest empty state when metrics are unavailable', async () => {
    apiGet.mockRejectedValue(new Error('down'))
    const wrapper = mount(StatsStage)
    await vi.waitFor(() => expect(wrapper.text()).toContain('System metrics unavailable'))
    wrapper.unmount()
  })

  it('marks kept readings stale after a failed poll', async () => {
    const s = useSystemStats()
    await s.refresh()
    expect(s.stats.value).not.toBeNull()
    apiGet.mockRejectedValueOnce(new Error('flap'))
    await s.refresh()
    expect(s.stale.value).toBe(true)
    expect(s.stats.value!.hostname).toBe('TESTBOX') // last good kept, not cleared
    s.stop()
  })
})

describe('screensaver style wiring', () => {
  it("ScreenSaver mounts StatsStage for style 'stats'", () => {
    const src = readFileSync(
      resolve(__dirname, '../components/ScreenSaver.vue'),
      'utf-8',
    )
    expect(src).toContain("screensaverStyle === 'stats'")
    expect(src).toContain('StatsStage')
    expect(src).toContain('v-else-if="statsMode"')
  })

  it('settings store accepts and persists the stats style', () => {
    const store = useSettingsStore()
    store.screensaverStyle = 'stats'
    expect(store.screensaverStyle).toBe('stats')
    store.screensaverStyle = 'widgets'
  })
})
