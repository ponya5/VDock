import { ref } from 'vue'
import apiClient from '@/api/client'

const POLL_INTERVAL_MS = 2500

/** Normalized view-model for the screensaver System widget — the raw
 *  /api/metrics/all payload is per-section psutil output (see
 *  backend/utils/system_metrics.py), so the composable flattens it to the
 *  handful of numbers the strip actually renders. null = section missing or
 *  unreadable; the row degrades on its own instead of failing the widget. */
export interface DiskPartitionStat {
  mount: string
  percent: number
  usedGb: number | null
  totalGb: number | null
}

export interface TopProcess {
  name: string
  cpuPercent: number | null
  memMb: number | null
}

export interface SystemStats {
  cpuPercent: number | null
  memPercent: number | null
  diskPercent: number | null
  /** /all carries no `gpu` key today; stays null unless the payload grows one. */
  gpuPercent: number | null
  /** Throughput in bytes/s derived from the cumulative MB counters — null
   *  until a second sample gives the delta a baseline. */
  netDownBps: number | null
  netUpBps: number | null
  /** Rolling peak (bytes/s) so the NET meter can self-scale. */
  netPeakBps: number
  timestamp: string | null
  /* -- DL-125: richer fields for the fullscreen stats saver. Same contract:
        every one is optional and degrades to hidden/'—' when absent. -- */
  cpuPerCore: number[]
  cpuFreqMhz: number | null
  memUsedGb: number | null
  memTotalGb: number | null
  diskPartitions: DiskPartitionStat[]
  diskReadBps: number | null
  diskWriteBps: number | null
  uptimeHours: number | null
  hostname: string | null
  batteryPercent: number | null
  batteryCharging: boolean | null
  /** Hottest temperature sensor reading, when the platform exposes any. */
  tempC: number | null
  topProcesses: TopProcess[]
  processCount: number | null
}

function num(v: unknown): number | null {
  const n = typeof v === 'string' ? parseFloat(v) : (v as number)
  return Number.isFinite(n) ? (n as number) : null
}

/** One usage number out of the partition list: prefer the system mount
 *  (C:\ on Windows, / elsewhere — the drive whose fullness actually hurts),
 *  else the fullest partition so nothing renders a fake "all fine". */
function pickDiskPercent(disk: any): number | null {
  const parts = Array.isArray(disk?.partitions) ? disk.partitions : []
  if (!parts.length) return num(disk?.usage_percent)
  const isSystemMount = (p: any) => /^c:\\?$/i.test(String(p?.mountpoint ?? '')) || p?.mountpoint === '/'
  const system = parts.find(isSystemMount)
  const target = system
    ?? parts.reduce((a: any, b: any) => (num(b?.usage_percent) ?? -1) > (num(a?.usage_percent) ?? -1) ? b : a)
  return num(target?.usage_percent)
}

/** Partitions ordered the way the stage shows them: the system mount first
 *  (the drive whose fullness actually hurts), then the fullest of the rest,
 *  capped at 4 so the card stays compact. */
function pickDiskPartitions(disk: any): DiskPartitionStat[] {
  const parts = Array.isArray(disk?.partitions) ? disk.partitions : []
  const isSystemMount = (p: any) => /^c:\\?$/i.test(String(p?.mountpoint ?? '')) || p?.mountpoint === '/'
  const mapped = parts
    .map((p: any) => ({
      mount: String(p?.mountpoint ?? p?.device ?? '?'),
      percent: num(p?.usage_percent) ?? -1,
      usedGb: num(p?.used_gb),
      totalGb: num(p?.total_gb),
    }))
    .filter(p => p.percent >= 0)
  mapped.sort((a, b) => {
    const aSys = isSystemMount({ mountpoint: a.mount }) ? 0 : 1
    const bSys = isSystemMount({ mountpoint: b.mount }) ? 0 : 1
    return aSys - bSys || b.percent - a.percent
  })
  return mapped.slice(0, 4)
}

/** Hottest sensor across every psutil group — null when the platform has no
 *  temperature support at all (common on Windows desktops). */
function pickTempC(data: any): number | null {
  const sensors = data?.temperature?.sensors
  if (!Array.isArray(sensors) || !sensors.length) return null
  const temps = sensors.map(s => num(s?.current)).filter((t): t is number => t != null)
  return temps.length ? Math.max(...temps) : null
}

function pickTopProcesses(data: any): TopProcess[] {
  const top = data?.processes?.top_cpu
  if (!Array.isArray(top)) return []
  return top.slice(0, 5).map((p: any) => ({
    name: String(p?.name ?? '?'),
    cpuPercent: num(p?.cpu_percent),
    memMb: num(p?.memory_mb),
  }))
}

/** GPU arrives in one of a few plausible shapes — a bare object with a
 *  percent key, or the `[{load_percent}]` array form the metric buttons
 *  already read. Anything unrecognized just means "no GPU row". */
function pickGpuPercent(data: any): number | null {
  const g = data?.gpu
  if (g == null) return null
  const entry = Array.isArray(g) ? g[0] : g
  if (entry == null || typeof entry !== 'object') return num(entry)
  return (
    num(entry.usage_percent)
    ?? num(entry.load_percent)
    ?? num(entry.utilization_percent)
    ?? num(entry.utilization)
  )
}

export function useSystemStats() {
  const stats = ref<SystemStats | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  /** True while showing a kept reading whose latest fetch failed — the
   *  widget dims rather than flashing an empty state on one bad poll. */
  const stale = ref(false)
  const lastOkAt = ref<number | null>(null)
  let refreshTimer: ReturnType<typeof setInterval> | null = null
  let inFlight = false
  let prevNet: { sentMb: number; recvMb: number; at: number } | null = null
  let prevDisk: { readMb: number; writeMb: number; at: number } | null = null
  let netPeakBps = 0

  function applyPayload(data: any): SystemStats {
    const now = Date.now()
    let netDownBps: number | null = null
    let netUpBps: number | null = null
    let diskReadBps: number | null = null
    let diskWriteBps: number | null = null

    const sentMb = num(data?.network?.bytes_sent_mb)
    const recvMb = num(data?.network?.bytes_recv_mb)
    if (sentMb != null && recvMb != null) {
      if (prevNet) {
        const dt = (now - prevNet.at) / 1000
        if (dt > 0) {
          // Counters reset on reboot/NIC bounce — clamp negatives to 0.
          netDownBps = Math.max(0, ((recvMb - prevNet.recvMb) * 1024 * 1024) / dt)
          netUpBps = Math.max(0, ((sentMb - prevNet.sentMb) * 1024 * 1024) / dt)
          netPeakBps = Math.max(netPeakBps, netDownBps, netUpBps)
        }
      }
      prevNet = { sentMb, recvMb, at: now }
    }

    const readMb = num(data?.disk?.io_read_mb)
    const writeMb = num(data?.disk?.io_write_mb)
    if (readMb != null && writeMb != null) {
      if (prevDisk) {
        const dt = (now - prevDisk.at) / 1000
        if (dt > 0) {
          diskReadBps = Math.max(0, ((readMb - prevDisk.readMb) * 1024 * 1024) / dt)
          diskWriteBps = Math.max(0, ((writeMb - prevDisk.writeMb) * 1024 * 1024) / dt)
        }
      }
      prevDisk = { readMb, writeMb, at: now }
    }

    const battery = data?.battery
    return {
      cpuPercent: num(data?.cpu?.usage_percent),
      memPercent: num(data?.memory?.usage_percent),
      diskPercent: pickDiskPercent(data?.disk),
      gpuPercent: pickGpuPercent(data),
      netDownBps,
      netUpBps,
      netPeakBps,
      timestamp: typeof data?.timestamp === 'string' ? data.timestamp : null,
      cpuPerCore: Array.isArray(data?.cpu?.per_cpu_percent)
        ? data.cpu.per_cpu_percent.map((p: any) => num(p) ?? 0)
        : [],
      cpuFreqMhz: num(data?.cpu?.frequency_current),
      memUsedGb: num(data?.memory?.used_gb),
      memTotalGb: num(data?.memory?.total_gb),
      diskPartitions: pickDiskPartitions(data?.disk),
      diskReadBps,
      diskWriteBps,
      uptimeHours: num(data?.system_info?.uptime_hours),
      hostname: typeof data?.system_info?.hostname === 'string' ? data.system_info.hostname : null,
      batteryPercent: battery?.available === true ? num(battery.percent) : null,
      batteryCharging: battery?.available === true ? battery.is_charging === true : null,
      tempC: pickTempC(data),
      topProcesses: pickTopProcesses(data),
      processCount: num(data?.processes?.total_processes),
    }
  }

  async function refresh() {
    // /metrics/all costs the backend ~2 s of blocking psutil reads — never
    // stack a second request on top of a slow one.
    if (inFlight) return
    inFlight = true
    loading.value = true
    error.value = null
    try {
      const response = await apiClient.get('/metrics/all')
      const body = response?.data
      if (!body || body.success === false || typeof body.data !== 'object' || body.data == null) {
        throw new Error(body?.error || 'bad metrics payload')
      }
      stats.value = applyPayload(body.data)
      stale.value = false
      lastOkAt.value = Date.now()
    } catch (err) {
      stale.value = stats.value != null
      error.value = 'System metrics unavailable'
      console.warn('System stats fetch failed:', err)
    } finally {
      loading.value = false
      inFlight = false
    }
  }

  function start() {
    if (refreshTimer) return
    void refresh()
    refreshTimer = setInterval(refresh, POLL_INTERVAL_MS)
  }

  function stop() {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  return { stats, loading, error, stale, lastOkAt, refresh, start, stop }
}

export { POLL_INTERVAL_MS as SYSTEM_STATS_POLL_MS }
