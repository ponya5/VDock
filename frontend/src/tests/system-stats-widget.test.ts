// DL-118 — System stats composable (StatsStage screensaver type).
// DL-141: the SystemStatsWidget component was removed — system stats are a
// screensaver *type*, not a widget; the composable coverage stays.
//
// The composable polls GET /api/metrics/all (~2.5 s) and normalizes the
// psutil-shaped payload into the numbers the stage renders. These tests
// cover cadence, payload mapping against the real backend key names
// (utils/system_metrics.py), net-rate deltas from cumulative counters, the
// optional GPU row, no request overlap, and stale-keep-last on failure.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

const get = vi.fn()
vi.mock('@/api/client', () => ({ default: { get: (...a: any[]) => get(...a) } }))

let useSystemStats: any
let SYSTEM_STATS_POLL_MS: number

/** Mirrors SystemMetrics.get_all_metrics(): every section is optional and
 *  numbers arrive under exactly these keys. */
function payload(over: Record<string, any> = {}) {
  return {
    data: {
      success: true,
      data: {
        timestamp: '2026-01-02T03:04:05',
        cpu: { usage_percent: 42.5, cores_logical: 16, status: 'normal' },
        memory: { usage_percent: 63.2, total_gb: 31.9, status: 'normal' },
        disk: {
          partitions: [
            { device: 'C:\\', mountpoint: 'C:\\', usage_percent: 71.4 },
            { device: 'D:\\', mountpoint: 'D:\\', usage_percent: 12.0 },
          ],
        },
        network: { bytes_sent_mb: 100, bytes_recv_mb: 250, status: 'normal' },
        temperature: { available: false, sensors: [] },
        battery: { available: false },
        processes: { total_processes: 210, top_cpu: [], top_memory: [] },
        system_info: { platform: 'Windows' },
        ...over,
      },
    },
  }
}

beforeEach(async () => {
  get.mockReset()
  get.mockResolvedValue(payload())
  vi.resetModules()
  const mod = await import('@/composables/useSystemStats')
  useSystemStats = mod.useSystemStats
  SYSTEM_STATS_POLL_MS = mod.SYSTEM_STATS_POLL_MS
})

afterEach(() => {
  vi.useRealTimers()
})

describe('useSystemStats polling', () => {
  it('fetches /metrics/all immediately on start and then every ~2.5 s', async () => {
    vi.useFakeTimers()
    const s = useSystemStats()
    s.start()
    await vi.advanceTimersByTimeAsync(0)
    expect(get).toHaveBeenCalledTimes(1)
    expect(get).toHaveBeenCalledWith('/metrics/all')

    await vi.advanceTimersByTimeAsync(SYSTEM_STATS_POLL_MS)
    expect(get).toHaveBeenCalledTimes(2)

    await vi.advanceTimersByTimeAsync(SYSTEM_STATS_POLL_MS * 2)
    expect(get).toHaveBeenCalledTimes(4)
    s.stop()
  })

  it('stops polling on stop()', async () => {
    vi.useFakeTimers()
    const s = useSystemStats()
    s.start()
    await vi.advanceTimersByTimeAsync(0)
    s.stop()
    await vi.advanceTimersByTimeAsync(SYSTEM_STATS_POLL_MS * 3)
    expect(get).toHaveBeenCalledTimes(1)
  })

  it('never overlaps requests — a slow poll skips the next tick', async () => {
    let resolveGet: any
    get.mockImplementation(() => new Promise((r) => { resolveGet = r }))
    const s = useSystemStats()

    const p1 = s.refresh()
    const p2 = s.refresh() // in-flight guard: returns without hitting the API
    await p2
    expect(get).toHaveBeenCalledTimes(1)

    resolveGet(payload())
    await p1
    expect(get).toHaveBeenCalledTimes(1)
    expect(s.stats.value.cpuPercent).toBe(42.5)
  })
})

describe('useSystemStats payload mapping', () => {
  it('maps cpu/memory/disk from the real backend keys', async () => {
    const s = useSystemStats()
    await s.refresh()

    expect(s.stats.value.cpuPercent).toBe(42.5)
    expect(s.stats.value.memPercent).toBe(63.2)
    // DISK prefers the system mount C:\ over the fullest partition.
    expect(s.stats.value.diskPercent).toBe(71.4)
    expect(s.stats.value.gpuPercent).toBeNull()
    expect(s.lastOkAt.value).not.toBeNull()
    expect(s.error.value).toBeNull()
  })

  it('derives NET bytes/s from the delta of cumulative MB counters', async () => {
    vi.useFakeTimers()
    const s = useSystemStats()
    s.start()
    await vi.advanceTimersByTimeAsync(0)

    // First sample has no baseline yet.
    expect(s.stats.value.netDownBps).toBeNull()
    expect(s.stats.value.netUpBps).toBeNull()

    get.mockResolvedValue(
      payload({ network: { bytes_sent_mb: 105, bytes_recv_mb: 260 } })
    )
    await vi.advanceTimersByTimeAsync(SYSTEM_STATS_POLL_MS) // +2.5 s

    // +10 MB recv / 2.5 s = 4 MiB/s; +5 MB sent / 2.5 s = 2 MiB/s.
    expect(s.stats.value.netDownBps).toBeCloseTo(4 * 1024 * 1024, 0)
    expect(s.stats.value.netUpBps).toBeCloseTo(2 * 1024 * 1024, 0)
    expect(s.stats.value.netPeakBps).toBeGreaterThanOrEqual(s.stats.value.netDownBps)
    s.stop()
  })

  it('falls back to the fullest partition when no system mount exists', async () => {
    get.mockResolvedValue(
      payload({
        disk: {
          partitions: [
            { device: '/home', mountpoint: '/home', usage_percent: 33 },
            { device: '/data', mountpoint: '/data', usage_percent: 88 },
          ],
        },
      })
    )
    const s = useSystemStats()
    await s.refresh()
    expect(s.stats.value.diskPercent).toBe(88)
  })

  it('picks the / mount on unix-style payloads', async () => {
    get.mockResolvedValue(
      payload({
        disk: {
          partitions: [
            { device: '/dev/sda1', mountpoint: '/', usage_percent: 55 },
            { device: '/dev/sdb1', mountpoint: '/data', usage_percent: 88 },
          ],
        },
      })
    )
    const s = useSystemStats()
    await s.refresh()
    expect(s.stats.value.diskPercent).toBe(55)
  })

  it('maps GPU when the payload carries it (object or array form)', async () => {
    get.mockResolvedValue(payload({ gpu: { usage_percent: 61 } }))
    const a = useSystemStats()
    await a.refresh()
    expect(a.stats.value.gpuPercent).toBe(61)

    get.mockResolvedValue(payload({ gpu: [{ load_percent: 42 }] }))
    const b = useSystemStats()
    await b.refresh()
    expect(b.stats.value.gpuPercent).toBe(42)
  })

  it('leaves a section null when that section errors out server-side', async () => {
    get.mockResolvedValue(payload({ memory: { error: 'boom' }, cpu: { usage_percent: 9 } }))
    const s = useSystemStats()
    await s.refresh()
    expect(s.stats.value.memPercent).toBeNull()
    expect(s.stats.value.cpuPercent).toBe(9)
  })
})

describe('useSystemStats honest states', () => {
  it('reports unavailable on first-load failure without fake stats', async () => {
    get.mockRejectedValue(new Error('offline'))
    const s = useSystemStats()
    await s.refresh()

    expect(s.stats.value).toBeNull()
    expect(s.error.value).toBeTruthy()
    expect(s.stale.value).toBe(false)
    expect(s.loading.value).toBe(false)
  })

  it('keeps the last reading on transient failure and flags it stale', async () => {
    const s = useSystemStats()
    await s.refresh()
    expect(s.stats.value.cpuPercent).toBe(42.5)

    get.mockRejectedValue(new Error('backend down'))
    await s.refresh()

    expect(s.stats.value.cpuPercent).toBe(42.5) // kept
    expect(s.error.value).toBeTruthy()
    expect(s.stale.value).toBe(true)

    // Recovery clears the flag and refreshes the numbers.
    get.mockResolvedValue(payload({ cpu: { usage_percent: 7 } }))
    await s.refresh()
    expect(s.stats.value.cpuPercent).toBe(7)
    expect(s.stale.value).toBe(false)
    expect(s.error.value).toBeNull()
  })

  it('treats a success:false envelope as an error', async () => {
    get.mockResolvedValue({ data: { success: false, error: 'nope' } })
    const s = useSystemStats()
    await s.refresh()
    expect(s.stats.value).toBeNull()
    expect(s.error.value).toBeTruthy()
  })
})
