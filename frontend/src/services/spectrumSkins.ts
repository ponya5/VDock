/**
 * Spectrum screensaver skins (DL-123).
 *
 * One fullscreen canvas, one rAF loop (owned by SpectrumStage), and a set of
 * swappable renderers. The stage passes every renderer the same smoothed
 * frame — `bands` is 20 values 0-100 with rise-fast/fall-slow envelope
 * already applied — so a skin is just a draw closure plus whatever history
 * it keeps in its factory-created state (fresh per activation, so a shuffle
 * swap never inherits stale buffers).
 *
 * Skin catalogue maps to the Winamp/Tunebar references:
 *   winamp / mono / uv — segmented bars, three classic palettes
 *   iso                — isometric frequency × history bar field, slow yaw
 *   scope              — radial polar spectrum + spokes + rings
 *   aurora             — concentric polar contours, pink/violet
 *   ember              — stacked amber ridgelines
 */

export interface SpectrumFrame {
  /** 20 smoothed band values, 0..100, low→high frequency. */
  bands: number[]
  /** Overall level 0..100. */
  level: number
  /** False while the backend reports silence — bands will be ~0 anyway. */
  live: boolean
  /** Canvas CSS-pixel size. */
  w: number
  h: number
  /** Seconds since the stage mounted — drives drift/rotation phases. */
  t: number
  /** Seconds since the previous frame — drives history accumulation. */
  dt: number
}

export interface SpectrumRenderer {
  draw(ctx: CanvasRenderingContext2D, f: SpectrumFrame): void
}

export interface SpectrumSkin {
  id: string
  label: string
  create(): SpectrumRenderer
}

/** Piecewise-linear sample of the 20-band array at x ∈ [0,1]. */
export function sampleBands(bands: number[], x: number): number {
  const n = bands.length
  const pos = Math.max(0, Math.min(1, x)) * (n - 1)
  const i = Math.floor(pos)
  const frac = pos - i
  const a = bands[i] ?? 0
  const b = bands[Math.min(i + 1, n - 1)] ?? 0
  return a + (b - a) * frac
}

/** Mirrored band sample for radial skins: x wraps around the circle. */
function sampleBandsCircular(bands: number[], x: number): number {
  const wrapped = x - Math.floor(x)
  const mirrored = wrapped < 0.5 ? wrapped * 2 : (1 - wrapped) * 2
  return sampleBands(bands, mirrored)
}

// ---------------------------------------------------------------------------
// Bars — the Winamp classic, three palettes
// ---------------------------------------------------------------------------

interface BarPalette {
  stops: Array<[number, string]>
  peak: string
  dim: string
}

const BAR_PALETTES: Record<string, BarPalette> = {
  fire: {
    stops: [[0, '#35d45e'], [0.55, '#cfd63c'], [0.8, '#ef8a2a'], [1, '#e8402a']],
    peak: 'rgba(255, 246, 230, 0.95)',
    dim: 'rgba(53, 212, 94, 0.35)',
  },
  mono: {
    stops: [[0, '#5c5c66'], [0.5, '#a9a9b4'], [0.8, '#dcdce4'], [1, '#ffffff']],
    peak: 'rgba(255, 255, 255, 0.95)',
    dim: 'rgba(255, 255, 255, 0.22)',
  },
  uv: {
    stops: [[0, '#6a1fff'], [0.45, '#b13cff'], [0.75, '#ff4fd8'], [1, '#4ff0ff']],
    peak: 'rgba(230, 250, 255, 0.95)',
    dim: 'rgba(106, 31, 255, 0.35)',
  },
}

function createBars(palette: BarPalette): SpectrumRenderer {
  const BANDS = 20
  const peaks = new Array<number>(BANDS).fill(0)
  const peakSince = new Array<number>(BANDS).fill(0)
  const PEAK_HOLD_S = 0.4

  return {
    draw(ctx, f) {
      const { w, h, t } = f
      ctx.clearRect(0, 0, w, h)
      const gap = Math.max(3, w * 0.006)
      const barW = Math.max((w - (BANDS - 1) * gap) / BANDS, 2)
      const usableH = h - Math.max(4, h * 0.02)
      const segPitch = Math.max(4, Math.round(h * 0.028)) // block + carve
      const idle = !f.live

      const gradient = ctx.createLinearGradient(0, h, 0, 0)
      for (const [stop, color] of palette.stops) gradient.addColorStop(stop, color)

      ctx.globalAlpha = idle ? 0.4 : 1
      ctx.fillStyle = gradient
      for (let i = 0; i < BANDS; i++) {
        // Idle: a low breathing stub so an empty screen still reads alive.
        const stub = 0.012 + Math.sin(t * 1.4 + i * 0.55) * 0.004
        const v = idle ? stub * 100 : f.bands[i]
        const barH = Math.max(2, (v / 100) * usableH)
        const x = i * (barW + gap)
        ctx.fillRect(x, h - barH, barW, barH)
        if (v >= peaks[i]) {
          peaks[i] = v
          peakSince[i] = t
        } else if (t - peakSince[i] > PEAK_HOLD_S) {
          peaks[i] *= Math.pow(0.25, f.dt)
          if (peaks[i] < 0.5) peaks[i] = 0
        }
      }

      // Segment carve — the analogue VU-meter blockiness.
      ctx.globalCompositeOperation = 'destination-out'
      for (let y = h - segPitch; y > 0; y -= segPitch) {
        ctx.fillRect(0, y, w, Math.max(1, segPitch * 0.25))
      }
      ctx.globalCompositeOperation = 'source-over'

      // Baseline rule + detached peak caps.
      ctx.fillStyle = idle ? 'rgba(255,255,255,0.10)' : 'rgba(255,255,255,0.16)'
      ctx.fillRect(0, h - 1, w, 1)
      ctx.fillStyle = idle ? palette.dim : palette.peak
      for (let i = 0; i < BANDS; i++) {
        if (peaks[i] <= 0) continue
        const x = i * (barW + gap)
        const capY = h - (peaks[i] / 100) * usableH - segPitch
        ctx.fillRect(x, Math.max(capY, 0), barW, Math.max(2, segPitch * 0.4))
      }
      ctx.globalAlpha = 1
    },
  }
}

// ---------------------------------------------------------------------------
// Iso — isometric frequency × history field, slowly yawing (reference img 2)
// ---------------------------------------------------------------------------

function createIso(): SpectrumRenderer {
  const COLS = 16
  const ROWS = 11
  const hist: number[][] = []
  let acc = 0
  const ROW_MS = 0.06

  for (let i = 0; i < ROWS; i++) hist.push(new Array<number>(COLS).fill(0))

  return {
    draw(ctx, f) {
      const { w, h, t, dt } = f
      ctx.clearRect(0, 0, w, h)
      acc += dt
      if (acc >= ROW_MS) {
        acc = 0
        hist.pop()
        hist.unshift(Array.from({ length: COLS }, (_, c) =>
          sampleBands(f.bands, c / (COLS - 1))))
      }

      const yaw = Math.sin(t * 0.14) * 0.5
      const cy = Math.cos(yaw), sy = Math.sin(yaw)
      const u = Math.min(w / (COLS * 1.55), h / (ROWS * 1.9))
      const maxZ = h * 0.34
      const cx = w / 2, cyOff = h * 0.52
      const cosA = Math.cos(Math.PI / 6), sinA = Math.sin(Math.PI / 6)
      const colW = u * 0.62

      const proj = (gx: number, gy: number, z: number) => {
        const px = gx - COLS / 2
        const py = gy - ROWS / 2
        const rx = px * cy - py * sy
        const ry = px * sy + py * cy
        return [cx + (rx - ry) * cosA * u, cyOff + (rx + ry) * sinA * u - z] as const
      }

      // Faint waveform rails along the two back edges.
      ctx.strokeStyle = 'rgba(255,255,255,0.25)'
      ctx.lineWidth = 1
      ctx.beginPath()
      for (let c = 0; c < COLS; c++) {
        const z = (hist[ROWS - 1][c] / 100) * maxZ * 0.4 + Math.sin(t * 2 + c) * 3
        const [sx, sy2] = proj(c + 0.5, ROWS - 0.4, z)
        c === 0 ? ctx.moveTo(sx, sy2) : ctx.lineTo(sx, sy2)
      }
      ctx.stroke()

      // Back row → front row so nearer columns overdraw.
      for (let r = ROWS - 1; r >= 0; r--) {
        for (let c = 0; c < COLS; c++) {
          const v = hist[r][c]
          const z = (v / 100) * maxZ + 1
          // Hue sweeps blue at the back-left to red at the front-right.
          const hue = 225 - ((c / (COLS - 1)) + (1 - r / (ROWS - 1))) * 0.5 * 225
          const [x1, y1] = proj(c, r, z)
          const [x2, y2] = proj(c + 1, r, z)
          const [x3, y3] = proj(c + 1, r + 1, z)
          const [x4, y4] = proj(c, r + 1, z)
          const [, by2] = proj(c + 1, r, 0)
          const [, by3] = proj(c + 1, r + 1, 0)
          const [, by4] = proj(c, r + 1, 0)

          const light = f.live ? 1 : 0.45
          // Right face (darker), front face (mid), top (brightest).
          ctx.fillStyle = `hsla(${hue}, 85%, ${30 * light}%, 0.95)`
          ctx.beginPath()
          ctx.moveTo(x2, y2); ctx.lineTo(x3, y3); ctx.lineTo(x3, by3); ctx.lineTo(x2, by2)
          ctx.closePath(); ctx.fill()
          ctx.fillStyle = `hsla(${hue}, 85%, ${42 * light}%, 0.95)`
          ctx.beginPath()
          ctx.moveTo(x3, y3); ctx.lineTo(x4, y4); ctx.lineTo(x4, by4); ctx.lineTo(x3, by3)
          ctx.closePath(); ctx.fill()
          ctx.fillStyle = `hsla(${hue}, 90%, ${58 * light}%, 0.98)`
          ctx.beginPath()
          ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.lineTo(x3, y3); ctx.lineTo(x4, y4)
          ctx.closePath(); ctx.fill()
        }
      }
      void colW
    },
  }
}

// ---------------------------------------------------------------------------
// Scope — radial polar spectrum (reference img 3)
// ---------------------------------------------------------------------------

function createScope(): SpectrumRenderer {
  const PTS = 96
  return {
    draw(ctx, f) {
      const { w, h, t } = f
      ctx.clearRect(0, 0, w, h)
      const cx = w / 2, cy = h / 2
      const R = Math.min(w, h) * 0.27
      const rot = t * 0.1
      const idle = !f.live
      const alpha = idle ? 0.35 : 1

      // Faint guide rings.
      ctx.strokeStyle = 'rgba(255,255,255,0.05)'
      ctx.lineWidth = 1
      for (const rr of [0.35, 0.7, 1.05]) {
        ctx.beginPath()
        ctx.arc(cx, cy, R * rr, 0, Math.PI * 2)
        ctx.stroke()
      }

      ctx.globalCompositeOperation = 'lighter'
      // Radial spokes, one per band.
      for (let i = 0; i < 20; i++) {
        const theta = rot + (i / 20) * Math.PI * 2
        const v = f.bands[i] / 100
        const r0 = R * 0.35
        const r1 = r0 + R * 0.7 * v
        ctx.strokeStyle = `rgba(80, 255, 160, ${0.10 * alpha + v * 0.25 * alpha})`
        ctx.lineWidth = 1.5
        ctx.beginPath()
        ctx.moveTo(cx + Math.cos(theta) * r0, cy + Math.sin(theta) * r0)
        ctx.lineTo(cx + Math.cos(theta) * r1, cy + Math.sin(theta) * r1)
        ctx.stroke()
      }

      // Outer spectrum polyline + its dimmer inner echo.
      const drawRing = (scale: number, width: number, rgb: string, a: number) => {
        ctx.beginPath()
        for (let i = 0; i <= PTS; i++) {
          const theta = rot + (i / PTS) * Math.PI * 2
          const v = sampleBandsCircular(f.bands, i / PTS) / 100
          const wob = Math.sin(theta * 5 - t * 1.6) * R * 0.015
          const r = R * scale * (0.55 + 0.55 * v) + wob
          const x = cx + Math.cos(theta) * r
          const y = cy + Math.sin(theta) * r
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
        }
        ctx.closePath()
        ctx.strokeStyle = `rgba(${rgb}, ${a * alpha})`
        ctx.lineWidth = width
        ctx.stroke()
      }
      drawRing(1, 5, '60, 235, 255', 0.16)   // halo
      drawRing(1, 1.6, '80, 240, 255', 0.9)  // cyan main
      drawRing(0.62, 4, '255, 63, 216', 0.12)
      drawRing(0.62, 1.4, '255, 79, 224', 0.75) // magenta inner
      ctx.globalCompositeOperation = 'source-over'
    },
  }
}

// ---------------------------------------------------------------------------
// Aurora — concentric polar contours (reference img 4)
// ---------------------------------------------------------------------------

function createAurora(): SpectrumRenderer {
  const RINGS = 16
  const PTS = 72
  return {
    draw(ctx, f) {
      const { w, h, t } = f
      ctx.clearRect(0, 0, w, h)
      const cx = w / 2, cy = h * 0.52
      const unit = Math.min(w, h)
      const r0 = unit * 0.055
      const dr = unit * 0.024
      const spread = unit * 0.36
      const rot = t * 0.06
      const alpha = f.live ? 1 : 0.4

      ctx.globalCompositeOperation = 'lighter'
      ctx.lineJoin = 'round'
      for (let k = 0; k < RINGS; k++) {
        const kF = k / (RINGS - 1)
        const base = r0 + k * dr
        ctx.beginPath()
        for (let i = 0; i <= PTS; i++) {
          const theta = (i / PTS) * Math.PI * 2
          const v = sampleBandsCircular(f.bands, theta / (Math.PI * 2) + rot / (Math.PI * 2)) / 100
          const wob = Math.sin(theta * 3 + t * 0.7 + k * 0.45) * unit * 0.006
          const r = base + v * spread * (0.25 + 0.75 * kF) + wob
          const x = cx + Math.cos(theta) * r
          const y = cy + Math.sin(theta) * r * 0.92 // slight squash = depth
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
        }
        ctx.closePath()
        const hue = 316 - kF * 52 // magenta → violet
        ctx.strokeStyle = `hsla(${hue}, 85%, ${60 - kF * 12}%, ${(0.30 - kF * 0.14) * alpha})`
        ctx.lineWidth = 1.3
        ctx.stroke()
      }
      ctx.globalCompositeOperation = 'source-over'
    },
  }
}

// ---------------------------------------------------------------------------
// Ember — stacked ridgelines (reference img 5)
// ---------------------------------------------------------------------------

function createEmber(): SpectrumRenderer {
  const LINES = 20
  const PTS = 64
  return {
    draw(ctx, f) {
      const { w, h, t } = f
      ctx.clearRect(0, 0, w, h)
      const alpha = f.live ? 1 : 0.4
      const top = h * 0.12
      const bottom = h * 0.86

      ctx.globalCompositeOperation = 'lighter'
      ctx.lineJoin = 'round'
      for (let j = LINES - 1; j >= 0; j--) {
        const jF = j / (LINES - 1) // 0 = front, 1 = back
        const yBase = bottom - (1 - jF) * (bottom - top)
        const amp = h * 0.30 * Math.pow(1 - jF, 1.6) + h * 0.015
        const phase = t * 0.5 + j * 0.35
        ctx.beginPath()
        for (let i = 0; i <= PTS; i++) {
          const x01 = i / PTS
          const x = x01 * w
          // The single-mountain silhouette: edges pinned flat.
          const env = Math.pow(Math.sin(Math.PI * x01), 1.15)
          const v = (sampleBands(f.bands, x01) / 100) * env
          const shimmer = Math.sin(x01 * 9 + phase) * amp * 0.03
          const y = yBase - v * amp + shimmer
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
        }
        const hue = 46 - (1 - jF) * 30 // amber → ember red toward the back
        const lineAlpha = (0.14 + (1 - jF) * 0.5) * alpha
        ctx.strokeStyle = `hsla(${hue}, 92%, ${52 + (1 - jF) * 10}%, ${lineAlpha})`
        ctx.lineWidth = 1.4
        ctx.stroke()
      }
      ctx.globalCompositeOperation = 'source-over'
    },
  }
}

// ---------------------------------------------------------------------------
// Registry
// ---------------------------------------------------------------------------

export const SPECTRUM_SKINS: SpectrumSkin[] = [
  { id: 'winamp', label: 'Winamp', create: () => createBars(BAR_PALETTES.fire) },
  { id: 'mono', label: 'Mono Bars', create: () => createBars(BAR_PALETTES.mono) },
  { id: 'uv', label: 'UV Bars', create: () => createBars(BAR_PALETTES.uv) },
  { id: 'iso', label: 'Iso Field', create: createIso },
  { id: 'scope', label: 'Scope', create: createScope },
  { id: 'aurora', label: 'Aurora', create: createAurora },
  { id: 'ember', label: 'Ember', create: createEmber },
]

export const DEFAULT_SPECTRUM_SKIN = 'winamp'

/** Resolve a persisted id, tolerating skins that no longer exist. */
export function getSpectrumSkin(id: string | undefined | null): SpectrumSkin {
  return SPECTRUM_SKINS.find(s => s.id === id)
    ?? SPECTRUM_SKINS.find(s => s.id === DEFAULT_SPECTRUM_SKIN)!
}

/** Next skin for shuffle — always different from `current`. */
export function pickNextSkin(current: string, rand: () => number = Math.random): string {
  const others = SPECTRUM_SKINS.filter(s => s.id !== current)
  if (!others.length) return current
  return others[Math.floor(rand() * others.length) % others.length].id
}

/**
 * Deterministic synthetic bands for settings previews and tests — a musical
 * looking swatch without touching the audio stream.
 */
export function demoBands(t: number): number[] {
  return Array.from({ length: 20 }, (_, i) => {
    const base = 30
      + 24 * Math.sin(t * 1.9 + i * 0.62)
      + 16 * Math.sin(t * 3.7 + i * 1.31)
    const beat = i < 5 ? 16 * Math.max(0, Math.sin(t * 5.2 + i)) : 0
    return Math.max(2, Math.min(96, base + beat))
  })
}
