/**
 * Spectrum screensaver skins (DL-123, expanded DL-134).
 *
 * Two stacked fullscreen canvases and one rAF loop (owned by
 * SpectrumStage) let skin swaps cross-dissolve; a set of swappable
 * renderers does the drawing. The stage passes every renderer the same
 * smoothed frame — `bands` is 20 values 0-100 with a fast-attack /
 * slow-release envelope already applied — so a skin is just a draw
 * closure plus whatever history it keeps in its factory-created state
 * (fresh per activation, so a shuffle swap never inherits stale buffers).
 *
 * Skin catalogue maps to the Winamp/Tunebar references:
 *   winamp / mono / uv — segmented bars, three classic palettes
 *   rgb                — segmented bars whose hues drift the full wheel
 *   iso                — isometric frequency × history bar field, slow yaw
 *   scope              — radial polar spectrum + spokes + rings
 *   aurora             — concentric polar contours, pink/violet
 *   ember              — stacked amber ridgelines
 *   rotor              — Winamp's 3D Rotating Spectrum Analyzer: a spinning
 *                        field of needles + a dotted scope ring
 *   swarm              — Winamp-style cube cascade: a band-indexed swarm of
 *                        shaded cubes streaming toward the camera, glowing
 *                        orbs popping off the beat
 *   wave               — synthesized oscilloscope trace, phosphor echoes
 *   ring               — waveform wrapped in a circle, beat shockwaves
 *   mirror             — symmetric double comb off a lit center rail
 *   psyche             — kaleidoscope petals smearing into light ribbons
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

/** '#rrggbb' → "r, g, b" for rgba() template strings. */
function hexRgb(hex: string): string {
  const n = parseInt(hex.slice(1), 16)
  return `${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}`
}

/** hsl → "r, g, b" for rgba() template strings (h 0-360, s/l 0-100). */
function hslRgb(h: number, s: number, l: number): string {
  const sn = s / 100
  const ln = l / 100
  const a = sn * Math.min(ln, 1 - ln)
  const chan = (n: number) => {
    const k = (n + h / 30) % 12
    return Math.round((ln - a * Math.max(-1, Math.min(k - 3, 9 - k, 1))) * 255)
  }
  return `${chan(0)}, ${chan(8)}, ${chan(4)}`
}

/** Beat pulse: spikes when the level jumps, decays back over ~0.4 s — the
 *  "thump" that makes transients visible, not just bar height. */
function createPulse(): (level: number, dt: number) => number {
  let p = 0
  let prev = 0
  return (level, dt) => {
    p *= Math.exp(-dt * 3.6)
    const rise = level - prev
    if (rise > 6) p = Math.min(1, p + rise / 38)
    prev = level
    return p
  }
}

/** One rising ember/spark — the bar and ember skins share the pool. */
interface Spark {
  x: number; y: number; vx: number; vy: number
  life: number; ttl: number; r: number
}

/** Advance + draw a spark pool additively; expired sparks are removed. */
function drawSparks(ctx: CanvasRenderingContext2D, sparks: Spark[],
                    dt: number, rgb: string): void {
  if (!sparks.length) return
  ctx.globalCompositeOperation = 'lighter'
  for (let i = sparks.length - 1; i >= 0; i--) {
    const s = sparks[i]
    s.life += dt
    s.x += s.vx * dt
    s.y += s.vy * dt
    if (s.life >= s.ttl) { sparks.splice(i, 1); continue }
    const k = 1 - s.life / s.ttl
    ctx.fillStyle = `rgba(${rgb}, ${(k * 0.8).toFixed(3)})`
    ctx.beginPath()
    ctx.arc(s.x, s.y, s.r * (0.6 + k * 0.4), 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalCompositeOperation = 'source-over'
}

// ---------------------------------------------------------------------------
// Bars — the Winamp classic, three palettes + the hue-drifting RGB variant
// ---------------------------------------------------------------------------

interface BarPalette {
  stops: Array<[number, string]>
  peak: string
  dim: string
}

/** Optional dynamic colouring for the bars renderer (the RGB skin). */
interface BarsFx {
  /** Per-bar colour at height fraction 0 (base) … 1 (tip). When present it
   *  replaces the shared palette gradient — one gradient per bar. */
  colorAt?: (bar: number, y01: number, t: number, lvl: number) => string
  /** "r, g, b" strings feeding the ambient layers — may drift over time. */
  ambient?: (t: number) => { base: string; top: string }
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
  // Shape-only palette for the chroma skin — colorAt overrides the fill;
  // this contributes the ambient rgb fallback + cap colours.
  rgb: {
    stops: [[0, '#8a7fff'], [1, '#7fffd4']],
    peak: 'rgba(255, 255, 255, 0.9)',
    dim: 'rgba(200, 200, 255, 0.30)',
  },
}

function createBars(palette: BarPalette, fx: BarsFx = {}): SpectrumRenderer {
  const BANDS = 20
  const peaks = new Array<number>(BANDS).fill(0)
  const peakVel = new Array<number>(BANDS).fill(0)
  const peakSince = new Array<number>(BANDS).fill(0)
  const PEAK_HOLD_S = 0.5
  const pulse = createPulse()
  const sparks: Spark[] = []
  const baseRgb0 = hexRgb(palette.stops[0][1])
  const topRgb0 = hexRgb(palette.stops[palette.stops.length - 1][1])
  const barHs = new Array<number>(BANDS).fill(0)
  // Perf caches (60 fps budget): the ambient layers are all fullscreen
  // gradient fills — rasterized once per frame at ~1/8 scale and blitted
  // up, since upscale smoothing doubles as free bloom. The vignette is
  // static, so it rasterizes once per size and blits every frame. The
  // palette gradient is static per height — rebuilt only on resize.
  let ambMini: HTMLCanvasElement | null = null
  let ambCtx: CanvasRenderingContext2D | null = null
  let vigStatic: HTMLCanvasElement | null = null
  let vigCtx: CanvasRenderingContext2D | null | false = null
  let vigKey = ''
  let barGradient: CanvasGradient | null = null
  let barGradientH = 0

  function paintAmbient(g: CanvasRenderingContext2D, w: number, h: number,
    t: number, idle: boolean, lvl: number, p: number,
    amb: { base: string; top: string }): void {
    // Ambient nebula — two palette-tinted washes wandering slowly in
    // counter-phase (base pools low-left, tip drifts high-right) and
    // breathing with the level, so the stage never reads flat black.
    const drift = Math.sin(t * 0.13) * w * 0.07
    const nebLo = g.createRadialGradient(
      w * 0.24 + drift, h * 1.10, 0, w * 0.24 + drift, h * 1.10, h * 0.95)
    nebLo.addColorStop(0, `rgba(${amb.base}, ${idle ? 0.055 : 0.10 + lvl * 0.07})`)
    nebLo.addColorStop(1, `rgba(${amb.base}, 0)`)
    g.fillStyle = nebLo
    g.fillRect(0, 0, w, h)
    const nebHi = g.createRadialGradient(
      w * 0.78 - drift, -h * 0.12, 0, w * 0.78 - drift, -h * 0.12, h * 0.85)
    nebHi.addColorStop(0, `rgba(${amb.top}, ${idle ? 0.04 : 0.065 + lvl * 0.05 + p * 0.06})`)
    nebHi.addColorStop(1, `rgba(${amb.top}, 0)`)
    g.fillStyle = nebHi
    g.fillRect(0, 0, w, h)

    // Beat glow — a floor-lit wash that breathes with the level and
    // flashes on transients.
    const glowR = h * (0.45 + lvl * 0.55 + p * 0.4)
    const glow = g.createRadialGradient(w / 2, h * 1.05, 0, w / 2, h * 1.05, glowR)
    glow.addColorStop(0, `rgba(${amb.base}, ${idle ? 0.05 : 0.13 + lvl * 0.10 + p * 0.16})`)
    glow.addColorStop(1, `rgba(${amb.base}, 0)`)
    g.fillStyle = glow
    g.fillRect(0, 0, w, h)

    // Light beam sweeping left→right behind the bars — faster and
    // brighter as the music gets louder.
    const sweepX = ((t * (0.20 + lvl * 0.55)) % 1.35 - 0.175) * w
    const beamW = Math.max(50, w * 0.07)
    const beam = g.createLinearGradient(sweepX - beamW, 0, sweepX + beamW, 0)
    const beamA = idle ? 0.04 : 0.08 + lvl * 0.12
    beam.addColorStop(0, `rgba(${amb.base}, 0)`)
    beam.addColorStop(0.5, `rgba(${amb.top}, ${beamA})`)
    beam.addColorStop(1, `rgba(${amb.base}, 0)`)
    g.fillStyle = beam
    g.fillRect(sweepX - beamW, 0, beamW * 2, h)
  }

  return {
    draw(ctx, f) {
      const { w, h, t, dt } = f
      ctx.clearRect(0, 0, w, h)
      const gap = Math.max(3, w * 0.006)
      const barW = Math.max((w - (BANDS - 1) * gap) / BANDS, 2)
      const usableH = h - Math.max(4, h * 0.02)
      const segPitch = Math.max(4, Math.round(h * 0.028)) // block + carve
      const idle = !f.live
      const lvl = f.level / 100
      const p = pulse(f.level, dt)
      const amb = fx.ambient ? fx.ambient(t)
        : { base: baseRgb0, top: topRgb0 }

      if (!ambMini && typeof document !== 'undefined') {
        ambMini = document.createElement('canvas')
        ambCtx = ambMini.getContext('2d')
      }
      if (ambMini && ambCtx) {
        const mw = Math.max(8, Math.round(w / 8))
        const mh = Math.max(8, Math.round(h / 8))
        if (ambMini.width !== mw) ambMini.width = mw
        if (ambMini.height !== mh) ambMini.height = mh
        ambCtx.setTransform(mw / w, 0, 0, mh / h, 0, 0)
        ambCtx.clearRect(0, 0, w, h)
        paintAmbient(ambCtx, w, h, t, idle, lvl, p, amb)
        ctx.imageSmoothingEnabled = true
        ctx.drawImage(ambMini, 0, 0, mw, mh, 0, 0, w, h)
      } else {
        paintAmbient(ctx, w, h, t, idle, lvl, p, amb)
      }

      if (!barGradient || barGradientH !== h) {
        barGradient = ctx.createLinearGradient(0, h, 0, 0)
        barGradientH = h
        for (const [stop, color] of palette.stops) barGradient.addColorStop(stop, color)
      }
      const gradient = barGradient

      ctx.globalAlpha = idle ? 0.4 : 1
      for (let i = 0; i < BANDS; i++) {
        // Idle: a low breathing stub so an empty screen still reads alive.
        const stub = 0.012 + Math.sin(t * 1.4 + i * 0.55) * 0.004
        const v = idle ? stub * 100 : f.bands[i]
        const barH = Math.max(2, (v / 100) * usableH)
        barHs[i] = barH
        const x = i * (barW + gap)
        if (fx.colorAt) {
          const g = ctx.createLinearGradient(0, h, 0, h - barH)
          g.addColorStop(0, fx.colorAt(i, 0, t, lvl))
          g.addColorStop(0.55, fx.colorAt(i, 0.55, t, lvl))
          g.addColorStop(1, fx.colorAt(i, 1, t, lvl))
          ctx.fillStyle = g
        } else {
          ctx.fillStyle = gradient
        }
        ctx.fillRect(x, h - barH, barW, barH)
        if (v >= peaks[i]) {
          peaks[i] = v
          peakSince[i] = t
          peakVel[i] = 0
        } else if (t - peakSince[i] > PEAK_HOLD_S) {
          // Gravity fall — caps drop like they were let go, not faded.
          peakVel[i] += 240 * dt
          peaks[i] = Math.max(0, peaks[i] - peakVel[i] * dt)
        }
        // Sparks climb off bars that are running hot.
        if (!idle && v > 55 && sparks.length < 60
            && Math.random() < dt * (v - 45) * 0.05) {
          sparks.push({
            x: x + barW * (0.25 + Math.random() * 0.5),
            y: h - barH,
            vx: (Math.random() - 0.5) * 24,
            vy: -(34 + Math.random() * 60),
            life: 0,
            ttl: 0.45 + Math.random() * 0.55,
            r: 1 + Math.random() * 1.8,
          })
        }
      }

      // Segment carve — the analogue VU-meter blockiness. Clipped to each
      // lit column so the ambient layers survive between and above bars.
      ctx.globalCompositeOperation = 'destination-out'
      for (let i = 0; i < BANDS; i++) {
        const x = i * (barW + gap)
        for (let y = h - segPitch; y > h - barHs[i]; y -= segPitch) {
          ctx.fillRect(x, y, barW, Math.max(1, segPitch * 0.25))
        }
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

      drawSparks(ctx, sparks, dt, amb.top)

      // Vignette — a soft edge falloff settling the scene into depth;
      // also keeps the additive spark layer from blooming at the borders.
      // Static per size → rasterized once, blitted every frame.
      if (!vigStatic && typeof document !== 'undefined') {
        vigStatic = document.createElement('canvas')
        vigCtx = vigStatic.getContext('2d')
      }
      const key = `${w}x${h}`
      if (vigStatic && vigCtx) {
        if (vigKey !== key) {
          vigKey = key
          vigStatic.width = Math.max(1, w)
          vigStatic.height = Math.max(1, h)
          const vig = vigCtx.createRadialGradient(
            w / 2, h * 0.55, Math.min(w, h) * 0.42,
            w / 2, h * 0.55, Math.max(w, h) * 0.78)
          vig.addColorStop(0, 'rgba(0, 0, 0, 0)')
          vig.addColorStop(1, 'rgba(0, 0, 0, 0.34)')
          vigCtx.fillStyle = vig
          vigCtx.fillRect(0, 0, w, h)
        }
        ctx.drawImage(vigStatic, 0, 0, w, h)
      } else {
        const vig = ctx.createRadialGradient(
          w / 2, h * 0.55, Math.min(w, h) * 0.42,
          w / 2, h * 0.55, Math.max(w, h) * 0.78)
        vig.addColorStop(0, 'rgba(0, 0, 0, 0)')
        vig.addColorStop(1, 'rgba(0, 0, 0, 0.34)')
        ctx.fillStyle = vig
        ctx.fillRect(0, 0, w, h)
      }
    },
  }
}

// ---------------------------------------------------------------------------
// RGB Bars — the same segmented VU bars, but every bar's hue drifts the
// full colour wheel. A slow global rotation (~26 s per cycle) plus a fixed
// 9°/bar offset keeps neighbours adjacent hues — a flowing soft rainbow,
// not confetti — and the level adds a gentle beat twist. Colours run deep
// at the base to pastel at the tip, so the palette stays soft everywhere.
// ---------------------------------------------------------------------------

function createRgbBars(): SpectrumRenderer {
  const colorAt = (i: number, y01: number, t: number, lvl: number) => {
    const hue = (t * 14 + i * 9 + lvl * 24) % 360
    const sat = 62 + Math.sin(t * 0.6 + i * 0.4) * 8   // breathing saturation
    const light = 34 + y01 * 34 + lvl * 6              // deep base → pastel tip
    return `hsl(${hue}, ${sat}%, ${Math.min(76, light)}%)`
  }
  const ambient = (t: number) => ({
    // The scene's washes trail the lead hue pair, so the background
    // rotates through the same soft spectrum the bars are showing.
    base: hslRgb((t * 14 + 40) % 360, 58, 45),
    top: hslRgb((t * 14 + 160) % 360, 70, 60),
  })
  return createBars(BAR_PALETTES.rgb, { colorAt, ambient })
}

// ---------------------------------------------------------------------------
// Iso — isometric frequency × history field, slowly yawing (reference img 2)
// ---------------------------------------------------------------------------

/** Shared interactive backdrop for the non-bar skins: a tinted base so
 *  the stage never reads flat black, two roaming hue clouds on slow
 *  Lissajous paths, and a center aura that breathes with the level and
 *  flares on the beat pulse. `orbit` (deg/s) slowly cycles the tint
 *  around the wheel — the rainbow skins use it so their ambience drifts
 *  in step with their content. Hues come from each skin's own palette.
 *
 *  Perf: the five layers rasterize into a ~1/8-scale offscreen canvas and
 *  blit up once — fullscreen gradient fills are the expensive part on a
 *  weak panel GPU, and the upscale's smoothing is free bloom. Falls back
 *  to direct paints where 2D offscreen contexts are unavailable. */
interface AmbientSpec { h1: number; h2: number; orbit?: number }
function createAmbient(spec: AmbientSpec) {
  const pulse = createPulse()
  const SCALE = 8
  let mini: HTMLCanvasElement | null = null
  let mctx: CanvasRenderingContext2D | null = null

  function paintLayers(g: CanvasRenderingContext2D, w: number, h: number,
    t: number, lvl: number, p: number, dim: number, c1: string, c2: string,
    h1: number, h2: number): void {
    // Tinted base — very dark, keeps the canvas off pure black.
    const base = g.createLinearGradient(0, h, 0, 0)
    base.addColorStop(0, `rgb(${hslRgb(h1, 60, 6)})`)
    base.addColorStop(1, `rgb(${hslRgb(h2, 55, 9)})`)
    g.fillStyle = base
    g.fillRect(0, 0, w, h)

    // Two roaming clouds in counter-phase — one pools low-left, one
    // hangs high-right; both breathe with the level.
    const lx = Math.sin(t * 0.11) * w * 0.08
    const lo = g.createRadialGradient(
      w * 0.22 + lx, h * 1.08, 0, w * 0.22 + lx, h * 1.08, h * 0.95)
    lo.addColorStop(0, `rgba(${c1}, ${(0.10 + lvl * 0.08 + p * 0.10) * dim})`)
    lo.addColorStop(1, `rgba(${c1}, 0)`)
    g.fillStyle = lo
    g.fillRect(0, 0, w, h)
    const hx = Math.cos(t * 0.09 + 2) * w * 0.09
    const hi = g.createRadialGradient(
      w * 0.78 - hx, -h * 0.08, 0, w * 0.78 - hx, -h * 0.08, h * 0.8)
    hi.addColorStop(0, `rgba(${c2}, ${(0.065 + lvl * 0.05 + p * 0.08) * dim})`)
    hi.addColorStop(1, `rgba(${c2}, 0)`)
    g.fillStyle = hi
    g.fillRect(0, 0, w, h)

    // Center aura — the interactive heartbeat: radius and brightness ride
    // the level, flaring on transients.
    const auraR = Math.min(w, h) * (0.34 + lvl * 0.26 + p * 0.20)
    const aura = g.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, auraR)
    aura.addColorStop(0, `rgba(${c2}, ${(0.05 + lvl * 0.05 + p * 0.11) * dim})`)
    aura.addColorStop(1, `rgba(${c2}, 0)`)
    g.fillStyle = aura
    g.fillRect(0, 0, w, h)

    // Vignette — pulls the eye to the content, adds depth.
    const vig = g.createRadialGradient(
      w / 2, h / 2, Math.min(w, h) * 0.34,
      w / 2, h / 2, Math.max(w, h) * 0.72)
    vig.addColorStop(0, 'rgba(0,0,0,0)')
    vig.addColorStop(1, 'rgba(0,0,0,0.42)')
    g.fillStyle = vig
    g.fillRect(0, 0, w, h)
  }

  return (ctx: CanvasRenderingContext2D, f: SpectrumFrame) => {
    const { w, h, t, dt } = f
    const lvl = f.level / 100
    const p = pulse(f.level, dt)
    const dim = f.live ? 1 : 0.45
    const h1 = spec.h1 + (spec.orbit ? t * spec.orbit : Math.sin(t * 0.11) * 22)
    const h2 = spec.h2 + (spec.orbit ? t * spec.orbit : Math.cos(t * 0.09) * 18)
    const c1 = hslRgb(h1, 68, 55)
    const c2 = hslRgb(h2, 74, 58)

    if (!mini && typeof document !== 'undefined') {
      mini = document.createElement('canvas')
      mctx = mini.getContext('2d')
    }
    if (!mini || !mctx) {
      paintLayers(ctx, w, h, t, lvl, p, dim, c1, c2, h1, h2)
      return
    }
    const mw = Math.max(8, Math.round(w / SCALE))
    const mh = Math.max(8, Math.round(h / SCALE))
    if (mini.width !== mw) mini.width = mw
    if (mini.height !== mh) mini.height = mh
    // Paint in CSS-pixel coordinates — the transform maps them onto the
    // mini canvas, so the layer code runs unchanged at 1/8 resolution.
    mctx.setTransform(mw / w, 0, 0, mh / h, 0, 0)
    mctx.clearRect(0, 0, w, h)
    paintLayers(mctx, w, h, t, lvl, p, dim, c1, c2, h1, h2)
    ctx.imageSmoothingEnabled = true
    ctx.drawImage(mini, 0, 0, mw, mh, 0, 0, w, h)
  }
}

function createIso(): SpectrumRenderer {
  const COLS = 16
  const ROWS = 11
  const hist: number[][] = []
  let acc = 0
  const ROW_MS = 0.06
  const ambient = createAmbient({ h1: 205, h2: 285 })
  // Ripple distance per cell is static — precompute once instead of a
  // Math.hypot per cell per frame (176/frame saved).
  const rippleDist = new Float32Array(COLS * ROWS)
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      rippleDist[r * COLS + c] = Math.hypot(c - COLS / 2, r - ROWS / 2)
    }
  }

  for (let i = 0; i < ROWS; i++) hist.push(new Array<number>(COLS).fill(0))

  return {
    draw(ctx, f) {
      const { w, h, t, dt } = f
      ctx.clearRect(0, 0, w, h)
      ambient(ctx, f)
      acc += dt
      if (acc >= ROW_MS) {
        acc = 0
        hist.pop()
        hist.unshift(Array.from({ length: COLS }, (_, c) =>
          sampleBands(f.bands, c / (COLS - 1))))
      }

      const yaw = Math.sin(t * 0.17) * 0.55
      const cy = Math.cos(yaw), sy = Math.sin(yaw)
      const u = Math.min(w / (COLS * 1.55), h / (ROWS * 1.9))
      const maxZ = h * 0.34
      const cx = w / 2, cyOff = h * 0.52 + Math.sin(t * 0.45) * h * 0.008
      const cosA = Math.cos(Math.PI / 6), sinA = Math.sin(Math.PI / 6)
      const lvl = f.level / 100
      // A slow hue orbit keeps the field's palette alive between hits.
      const hueDrift = Math.sin(t * 0.18) * 18

      const proj = (gx: number, gy: number, z: number) => {
        const px = gx - COLS / 2
        const py = gy - ROWS / 2
        const rx = px * cy - py * sy
        const ry = px * sy + py * cy
        return [cx + (rx - ry) * cosA * u, cyOff + (rx + ry) * sinA * u - z] as const
      }

      // Under-glow pooling beneath the field, swelling with the level.
      const glowY = cyOff + u * ROWS * 0.55
      const gl = ctx.createRadialGradient(cx, glowY, 0, cx, glowY, u * COLS)
      gl.addColorStop(0, `rgba(96, 140, 255, ${(0.05 + lvl * 0.12) * (f.live ? 1 : 0.4)})`)
      gl.addColorStop(1, 'rgba(96, 140, 255, 0)')
      ctx.fillStyle = gl
      ctx.beginPath()
      ctx.ellipse(cx, glowY, u * COLS * 1.15, u * ROWS * 0.6, 0, 0, Math.PI * 2)
      ctx.fill()

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

      // Painter order: screen depth = px(cy+sy) + py(cy−sy) — both
      // coefficients stay positive for |yaw| < 45°, so front is always
      // the large-r/large-c corner. Draw back row → front row so nearer
      // columns overdraw farther ones (this used to run front→back —
      // rear bars painted over the faces in front of them and the 3D
      // read collapsed into a wall of colour).
      for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS; c++) {
          const v = hist[r][c]
          // Ripple rings radiating out of the field's centre — a constant
          // wave motion under the audio-driven heights.
          const dist = rippleDist[r * COLS + c]
          const ripple = Math.sin(dist * 0.55 - t * 2.8) * maxZ * 0.05
            * (0.35 + lvl * 0.9)
          const z = (v / 100) * maxZ + 1 + ripple
          // Hue sweeps blue at the back-left to red at the front-right.
          const hue = 225 - ((c / (COLS - 1)) + (1 - r / (ROWS - 1))) * 0.5 * 225
            + hueDrift
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
    },
  }
}

// ---------------------------------------------------------------------------
// Scope — radial polar spectrum (reference img 3)
// ---------------------------------------------------------------------------

function createScope(): SpectrumRenderer {
  const PTS = 96
  let rot = 0
  const pulse = createPulse()
  const ambient = createAmbient({ h1: 150, h2: 185 })
  return {
    draw(ctx, f) {
      const { w, h, t, dt } = f
      ctx.clearRect(0, 0, w, h)
      ambient(ctx, f)
      const cx = w / 2, cy = h / 2
      const R = Math.min(w, h) * 0.27
      const idle = !f.live
      const alpha = idle ? 0.35 : 1
      const lvl = f.level / 100
      const p = pulse(f.level, dt)
      // Level-driven spin — the dial winds up as the room gets loud.
      rot += dt * (0.12 + lvl * 1.1)

      // Breathing guide rings.
      ctx.lineWidth = 1
      for (const rr of [0.35, 0.7, 1.05]) {
        ctx.strokeStyle = `rgba(255,255,255,${0.04 + Math.sin(t * 0.9 + rr * 4) * 0.02})`
        ctx.beginPath()
        ctx.arc(cx, cy, R * rr, 0, Math.PI * 2)
        ctx.stroke()
      }

      ctx.globalCompositeOperation = 'lighter'

      // Pulsing core — a soft reactor orb swelling with level and beats.
      const coreR = R * (0.14 + lvl * 0.16 + p * 0.12)
      const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR)
      core.addColorStop(0, `rgba(150, 255, 235, ${(0.4 + p * 0.45) * alpha})`)
      core.addColorStop(0.55, `rgba(64, 220, 255, ${0.2 * alpha})`)
      core.addColorStop(1, 'rgba(64, 220, 255, 0)')
      ctx.fillStyle = core
      ctx.beginPath()
      ctx.arc(cx, cy, coreR, 0, Math.PI * 2)
      ctx.fill()

      // Comets orbiting just inside the ring — alternating directions,
      // short dot trails, brightening where the band under them is loud.
      for (let c = 0; c < 3; c++) {
        const dir = c % 2 ? -1 : 1
        const spd = 0.8 + c * 0.35
        const rr = R * (0.5 + c * 0.15)
        const head = t * spd * dir + c * 2.1
        const bandBoost = 0.4 + sampleBandsCircular(f.bands, (head / (Math.PI * 2)) % 1) / 100 * 0.6
        for (let tail = 0; tail < 7; tail++) {
          const a = head - dir * tail * 0.06
          const k = 1 - tail / 7
          ctx.fillStyle = `rgba(120, 255, 235, ${(0.55 * k * bandBoost) * alpha})`
          ctx.beginPath()
          ctx.arc(cx + Math.cos(a) * rr, cy + Math.sin(a) * rr, 1.6 * k + 0.5, 0, Math.PI * 2)
          ctx.fill()
        }
      }
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
  const ambient = createAmbient({ h1: 170, h2: 300 })
  return {
    draw(ctx, f) {
      const { w, h, t } = f
      ctx.clearRect(0, 0, w, h)
      ambient(ctx, f)
      const cx = w / 2, cy = h * 0.52
      const unit = Math.min(w, h)
      const r0 = unit * 0.055
      const dr = unit * 0.024
      const spread = unit * 0.36
      const rot = t * 0.1
      const alpha = f.live ? 1 : 0.4
      const lvl = f.level / 100
      const hueDrift = Math.sin(t * 0.12) * 16

      // A ring's sampled point at angle theta — shared by the base stroke
      // and its comet overlay. Spacing breathes slowly even between hits.
      const ringPoint = (theta: number, k: number) => {
        const kF = k / (RINGS - 1)
        const base = (r0 + k * dr) * (1 + Math.sin(t * 0.5 + k * 0.35) * 0.05)
        const v = sampleBandsCircular(f.bands, theta / (Math.PI * 2) + rot / (Math.PI * 2)) / 100
        const wob = Math.sin(theta * 3 + t * 0.7 + k * 0.45) * unit * 0.006
        const r = base + v * spread * (0.25 + 0.75 * kF) + wob
        return [cx + Math.cos(theta) * r, cy + Math.sin(theta) * r * 0.92] as const
      }

      ctx.globalCompositeOperation = 'lighter'
      ctx.lineJoin = 'round'

      // Core glow — a soft violet heart swelling with the level.
      const coreR = spread * (0.35 + lvl * 0.3)
      const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR)
      core.addColorStop(0, `rgba(210, 130, 255, ${(0.09 + lvl * 0.15) * alpha})`)
      core.addColorStop(1, 'rgba(210, 130, 255, 0)')
      ctx.fillStyle = core
      ctx.beginPath()
      ctx.arc(cx, cy, coreR, 0, Math.PI * 2)
      ctx.fill()

      for (let k = 0; k < RINGS; k++) {
        const kF = k / (RINGS - 1)
        ctx.beginPath()
        for (let i = 0; i <= PTS; i++) {
          const [x, y] = ringPoint((i / PTS) * Math.PI * 2, k)
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
        }
        ctx.closePath()
        const hue = 316 - kF * 52 + hueDrift // magenta → violet, drifting
        ctx.strokeStyle = `hsla(${hue}, 85%, ${60 - kF * 12}%, ${(0.30 - kF * 0.14) * alpha})`
        ctx.lineWidth = 1.3
        ctx.stroke()

        // Comet shimmer — a bright arc sweeping each ring; adjacent rings
        // counter-rotate so the field shimmers in both directions.
        const dir = k % 2 ? -1 : 1
        const head = dir * t * (0.3 + kF * 0.5) + k * 1.9
        const ARC = 0.9
        ctx.beginPath()
        for (let i = 0; i <= 22; i++) {
          const theta = head + dir * (i / 22) * ARC
          const [x, y] = ringPoint(theta, k)
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
        }
        ctx.strokeStyle = `hsla(${hue}, 95%, 75%, ${(0.5 - kF * 0.18) * alpha})`
        ctx.lineWidth = 2.2
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
  const sparks: Spark[] = []
  const ambient = createAmbient({ h1: 18, h2: 335 })
  return {
    draw(ctx, f) {
      const { w, h, t, dt } = f
      ctx.clearRect(0, 0, w, h)
      ambient(ctx, f)
      const alpha = f.live ? 1 : 0.4
      const lvl = f.level / 100
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
        let crestX = 0
        let crestY = Infinity
        for (let i = 0; i <= PTS; i++) {
          const x01 = i / PTS
          const x = x01 * w
          // The single-mountain silhouette: edges pinned flat.
          const env = Math.pow(Math.sin(Math.PI * x01), 1.15)
          const v = (sampleBands(f.bands, x01) / 100) * env
          // Heat shimmer + a slow swell that sweeps across the ridge.
          const shimmer = Math.sin(x01 * 9 + phase) * amp * 0.03
            + Math.sin(x01 * 4 - t * 2.1) * amp * 0.05 * (0.3 + lvl)
          const y = yBase - v * amp + shimmer
          if (y < crestY) { crestY = y; crestX = x }
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
        }
        const hue = 46 - (1 - jF) * 30 // amber → ember red toward the back
        const lineAlpha = (0.14 + (1 - jF) * 0.5) * alpha
        ctx.strokeStyle = `hsla(${hue}, 92%, ${52 + (1 - jF) * 10}%, ${lineAlpha})`
        ctx.lineWidth = 1.4
        ctx.stroke()

        // Hot spot at each ridge's crest — a glowing coal that dances with
        // the tallest peak.
        if (crestY < yBase - h * 0.02) {
          ctx.fillStyle = `hsla(${hue + 6}, 95%, 72%, ${lineAlpha * 0.9})`
          ctx.beginPath()
          ctx.arc(crestX, crestY, 2.2, 0, Math.PI * 2)
          ctx.fill()
          // Embers lift off the hottest front crests.
          if (f.live && jF < 0.4 && sparks.length < 50
              && Math.random() < dt * lvl * 1.6) {
            sparks.push({
              x: crestX + (Math.random() - 0.5) * 24,
              y: crestY,
              vx: (Math.random() - 0.5) * 18,
              vy: -(26 + Math.random() * 46),
              life: 0,
              ttl: 0.6 + Math.random() * 0.8,
              r: 0.9 + Math.random() * 1.6,
            })
          }
        }
      }
      ctx.globalCompositeOperation = 'source-over'

      drawSparks(ctx, sparks, dt, '255, 178, 96')
    },
  }
}

// ---------------------------------------------------------------------------
// Rotor — Winamp's "3D Rotating Spectrum Analyzer" (reference img 4):
// a grid of thin needles over frequency × history, slowly spinning a full
// turn, ringed by a dotted scope wave. Unlike the fat iso blocks these are
// sticks with a bright cap, and because the spin runs the full 360° the
// painter order can't be a fixed loop — the cell indices are sorted by
// rotated depth every frame (224 entries, trivial cost).
// ---------------------------------------------------------------------------

function createRotor(): SpectrumRenderer {
  const COLS = 16
  const ROWS = 14
  const hist: number[][] = []
  let acc = 0
  const ROW_MS = 0.055

  for (let i = 0; i < ROWS; i++) hist.push(new Array<number>(COLS).fill(0))

  const order: number[] = []
  for (let i = 0; i < COLS * ROWS; i++) order.push(i)
  const ambient = createAmbient({ h1: 190, h2: 270 })

  return {
    draw(ctx, f) {
      const { w, h, t, dt } = f
      ctx.clearRect(0, 0, w, h)
      ambient(ctx, f)
      acc += dt
      if (acc >= ROW_MS) {
        acc = 0
        hist.pop()
        hist.unshift(Array.from({ length: COLS }, (_, c) =>
          sampleBands(f.bands, c / (COLS - 1))))
      }

      const rot = t * 0.26                       // continuous slow spin
      const cy = Math.cos(rot), sy = Math.sin(rot)
      const dim = Math.min(w, h)
      const u = dim / (COLS * 1.5)               // cell pitch
      const squash = 0.52                        // vertical foreshortening
      const maxZ = dim * 0.5
      const cx = w / 2, cyOff = h * 0.55
      const lvl = f.level / 100
      const alpha = f.live ? 1 : 0.4

      const depthOf = (gx: number, gy: number) =>
        (gx - COLS / 2) * sy + (gy - ROWS / 2) * cy
      // Weak perspective — far cells converge and shrink like the plugin.
      const perspOf = (ry: number) => 1 / (1 - ry * 0.055)
      const proj = (gx: number, gy: number, z: number) => {
        const rx = (gx - COLS / 2) * cy - (gy - ROWS / 2) * sy
        const ry = depthOf(gx, gy)
        const p = perspOf(ry)
        return [cx + rx * u * p, cyOff + ry * u * squash * p - z * p, p] as const
      }

      // Faint floor so the spin reads even when the field sits low.
      ctx.strokeStyle = `rgba(255,255,255,${0.05 + lvl * 0.03})`
      ctx.lineWidth = 1
      ctx.beginPath()
      for (const [gx, gy] of [[0, 0], [COLS, 0], [COLS, ROWS], [0, ROWS]]) {
        const [x, y] = proj(gx, gy, 0)
        if (gx === 0 && gy === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
      ctx.closePath()
      ctx.stroke()

      // Dotted scope ring — the plugin's waveform halo. Radius wobbles
      // with the spectrum, a fast secondary wiggle fakes the
      // time-domain fuzz, and it counter-drifts against the field's spin.
      const ringR = u * COLS * 0.78
      const DOTS = 150
      ctx.fillStyle = `rgba(235, 240, 255, ${0.34 + lvl * 0.3 * alpha})`
      for (let i = 0; i < DOTS; i++) {
        const a = (i / DOTS) * Math.PI * 2 - rot * 0.4
        const wv = sampleBandsCircular(f.bands, i / DOTS) / 100
        const fuzz = Math.sin(a * 26 + t * 7) * (0.3 + lvl) * maxZ * 0.03
        const rr = ringR * (1 + wv * 0.14)
        const x = cx + Math.cos(a) * rr
        const y = cyOff + Math.sin(a) * rr * squash - wv * maxZ * 0.18 - fuzz
        ctx.fillRect(x - 1.2, y - 1.2, 2.4, 2.4)
      }

      // Needles, back → front by rotated depth.
      order.sort((ia, ib) =>
        depthOf(ia % COLS + 0.5, (ia / COLS | 0) + 0.5)
        - depthOf(ib % COLS + 0.5, (ib / COLS | 0) + 0.5))

      const stemW = Math.max(1.6, u * 0.12)
      const cap = Math.max(2.2, u * 0.26)
      for (const idx of order) {
        const c = idx % COLS, r = (idx / COLS) | 0
        const v = hist[r][c]
        const z = (v / 100) * maxZ + 1
        const [bx, by] = proj(c + 0.5, r + 0.5, 0)
        const [tx, ty, p] = proj(c + 0.5, r + 0.5, z)
        // Height-mapped hue — blue stubs to red spikes, like the plugin.
        const hue = 228 - (v / 100) * 228
        ctx.strokeStyle = `hsla(${hue}, 90%, ${(34 + (v / 100) * 18) * alpha}%, 0.9)`
        ctx.lineWidth = stemW * p
        ctx.beginPath()
        ctx.moveTo(bx, by)
        ctx.lineTo(tx, ty)
        ctx.stroke()
        // Bright cap — the little top face that sells each needle.
        const cp = cap * p
        ctx.fillStyle = `hsla(${hue}, 95%, ${(56 + (v / 100) * 16) * alpha}%, 0.95)`
        ctx.beginPath()
        ctx.moveTo(tx, ty - cp * 0.7)
        ctx.lineTo(tx + cp, ty)
        ctx.lineTo(tx, ty + cp * 0.7)
        ctx.lineTo(tx - cp, ty)
        ctx.closePath()
        ctx.fill()
      }
    },
  }
}

// ---------------------------------------------------------------------------
// Swarm — the Winamp cube-cascade visuals (reference img 5): a stream of
// little shaded cubes flowing out of the dark toward the camera. Each cube
// owns a spectrum band — its lane (left→right) and its lift (height) — so
// the swarm's silhouette IS the spectrum as it sweeps past. Depth is the
// flow axis: cubes spawn small in the distance, swell as they near, then
// respawn at the back. Painter order is a per-frame depth sort.
// ---------------------------------------------------------------------------

interface SwarmCube {
  band: number      // spectrum lane + hue
  z: number         // depth 0 (far) → 1 (at the camera)
  lat: number       // lateral scatter around the lane, -1..1
  hjit: number      // height scatter, -1..1
  hue0: number      // per-cube hue offset for the rainbow wash
}

function createSwarm(): SpectrumRenderer {
  const COUNT = 460
  const cubes: SwarmCube[] = Array.from({ length: COUNT }, (_, i) => ({
    band: i % 20,
    z: (i / COUNT) + Math.random() * 0.05,
    lat: Math.random() * 2 - 1,
    hjit: Math.random() * 2 - 1,
    hue0: Math.random() * 360,
  }))
  const drawOrder = cubes.map((_, i) => i)
  const pulse = createPulse()
  const orbs: Spark[] = []
  // Full hue orbit — the swarm's fireflies cycle the wheel, so the
  // ambience drifts with them instead of locking to one tint.
  const ambient = createAmbient({ h1: 200, h2: 320, orbit: 10 })

  // Perf: a cube is a fixed shape whose only variation is hue — three
  // path fills per cube meant ~1400 fills per frame. Pre-render the cube
  // once per hue bucket and blit it instead: ~460 drawImage calls, which
  // keeps the skin inside the 60 fps budget on the panel's small CPU.
  const SPRITE = 32            // sprite edge px — cubes stay small on screen
  const SPRITE_U = SPRITE * 0.30
  const BUCKETS = 30           // hue quantization — 12° steps are invisible
  let sprites: HTMLCanvasElement[] | null = null
  let spritesTried = false
  function cubeSprites(): HTMLCanvasElement[] | null {
    if (sprites || spritesTried) return sprites
    spritesTried = true
    if (typeof document === 'undefined') return null
    const out: HTMLCanvasElement[] = []
    const cx = SPRITE / 2, cy = SPRITE / 2
    const u = SPRITE_U, tz = u * 0.55
    for (let b = 0; b < BUCKETS; b++) {
      const hue = b * (360 / BUCKETS)
      const cv = document.createElement('canvas')
      cv.width = SPRITE
      cv.height = SPRITE
      const g = cv.getContext('2d')
      if (!g) return null
      g.fillStyle = `hsla(${hue}, 85%, 74%, 0.95)`
      g.beginPath()
      g.moveTo(cx, cy - tz); g.lineTo(cx + u, cy - tz * 0.5)
      g.lineTo(cx, cy); g.lineTo(cx - u, cy - tz * 0.5); g.closePath(); g.fill()
      g.fillStyle = `hsla(${hue}, 78%, 52%, 0.9)`
      g.beginPath()
      g.moveTo(cx - u, cy - tz * 0.5); g.lineTo(cx, cy)
      g.lineTo(cx, cy + tz); g.lineTo(cx - u, cy + tz * 0.5); g.closePath(); g.fill()
      g.fillStyle = `hsla(${hue}, 72%, 32%, 0.9)`
      g.beginPath()
      g.moveTo(cx + u, cy - tz * 0.5); g.lineTo(cx, cy)
      g.lineTo(cx, cy + tz); g.lineTo(cx + u, cy + tz * 0.5); g.closePath(); g.fill()
      out.push(cv)
    }
    sprites = out
    return sprites
  }

  return {
    draw(ctx, f) {
      const { w, h, t, dt } = f
      ctx.clearRect(0, 0, w, h)
      ambient(ctx, f)
      const lvl = f.level / 100
      const beat = pulse(f.level, dt)
      const dim = Math.min(w, h)
      const cx = w / 2
      const unit = dim / 60
      const alpha = f.live ? 1 : 0.4

      // Flow speed: a lazy drift that surges with level and on the beat.
      const speed = dt * (0.28 + lvl * 0.55 + beat * 0.9)
      for (const c of cubes) {
        c.z += speed
        if (c.z >= 1) {
          c.z -= 1
          c.lat = Math.random() * 2 - 1
          c.hjit = Math.random() * 2 - 1
        }
      }

      // Far → near so nearer cubes overdraw.
      drawOrder.sort((a, b) => cubes[a].z - cubes[b].z)

      const spriteList = cubeSprites()
      const horizon = h * 0.3
      const travel = h * 0.62               // far → near screen drop
      const maxLift = dim * 0.42
      for (const i of drawOrder) {
        const c = cubes[i]
        const v = sampleBands(f.bands, c.band / 19) / 100
        // Perspective: far cubes converge on the centre of the horizon.
        const s = 0.1 + c.z
        const lane = (c.band / 19 - 0.5) * 2
        const sway = Math.sin(t * 0.4 + c.z * 5) * 0.03
        const x = cx + (lane * 0.9 + c.lat * 0.16 + sway) * (w * 0.46) * s
        const lift = (v + c.hjit * 0.09) * maxLift
        const y = horizon + travel * s - lift * (0.25 + s * 0.75)

        const size = s * unit * (0.85 + v * 1.15 + beat * 0.3)
        if (size < 0.8) continue

        // Flowing rainbow wash — hue rides the lane, depth, and time.
        const hue = (c.band * 9 + c.z * 120 + c.hue0 * 0.15 + t * 34) % 360
        if (spriteList) {
          const b = Math.round(hue / 12) % BUCKETS
          // Baked lightness ≈ mid; level/beat still drive brightness via
          // globalAlpha. The sprite's cube sits centered, so the blit is
          // a single square scaled to the cube's "size".
          ctx.globalAlpha = alpha * Math.min(1, 0.5 + v * 0.4 + beat * 0.35)
          const dw = size * (SPRITE / SPRITE_U)
          ctx.drawImage(spriteList[b], x - dw / 2, y - dw / 2, dw, dw)
          continue
        }

        // Fallback for environments without an offscreen 2D context
        // (tests): the original three-face path cube.
        const li = (52 + v * 16 + beat * 10) * alpha
        const top = `hsla(${hue}, 85%, ${Math.min(82, li + 22)}%, 0.95)`
        const side = `hsla(${hue}, 78%, ${li}%, 0.9)`
        const shade = `hsla(${hue}, 72%, ${li * 0.62}%, 0.9)`

        // Mini iso-cube: top rhombus + two side faces.
        const tz = size * 0.55
        ctx.fillStyle = top
        ctx.beginPath()
        ctx.moveTo(x, y - tz)
        ctx.lineTo(x + size, y - tz * 0.5)
        ctx.lineTo(x, y)
        ctx.lineTo(x - size, y - tz * 0.5)
        ctx.closePath()
        ctx.fill()
        ctx.fillStyle = side
        ctx.beginPath()
        ctx.moveTo(x - size, y - tz * 0.5)
        ctx.lineTo(x, y)
        ctx.lineTo(x, y + tz)
        ctx.lineTo(x - size, y + tz * 0.5)
        ctx.closePath()
        ctx.fill()
        ctx.fillStyle = shade
        ctx.beginPath()
        ctx.moveTo(x + size, y - tz * 0.5)
        ctx.lineTo(x, y)
        ctx.lineTo(x, y + tz)
        ctx.lineTo(x + size, y + tz * 0.5)
        ctx.closePath()
        ctx.fill()
      }
      ctx.globalAlpha = 1

      // Beat orbs — glowing spheres that pop off the loudest lane and
      // float up through the swarm (the middle panel of the reference).
      if (beat > 0.3 && orbs.length < 9) {
        const bi = Math.floor(Math.random() * 20)
        orbs.push({
          x: cx + (bi / 19 - 0.5) * w * 0.7,
          y: h * (0.55 + Math.random() * 0.2),
          vx: (Math.random() - 0.5) * 30,
          vy: -(40 + Math.random() * 70 + beat * 60),
          life: 0, ttl: 1.1 + Math.random() * 0.5,
          r: dim * (0.014 + beat * 0.02),
        })
      }
      drawSparks(ctx, orbs, dt, '224, 186, 255')
    },
  }
}

// ---------------------------------------------------------------------------
// Wave — a synthesized oscilloscope trace. We get FFT bands, not the raw
// waveform, so the trace is a sum of three harmonics whose amplitudes track
// the bass/mid/treble band groups — it swings like a real scope while staying
// a pure function of the spectrum. Beat pulses thicken and flare the beam;
// two delayed ghost echoes give it a phosphor-trail feel.
// ---------------------------------------------------------------------------

function createWave(): SpectrumRenderer {
  const PTS = 160
  const pulse = createPulse()
  const ambient = createAmbient({ h1: 172, h2: 200 })

  /** Average a band range → 0..1. */
  const grp = (bands: number[], a: number, b: number) => {
    let s = 0
    for (let i = a; i <= b; i++) s += bands[i] ?? 0
    return s / ((b - a + 1) * 100)
  }

  const trace = (bands: number[], x01: number, t: number, idle: boolean) => {
    if (idle) return Math.sin(x01 * Math.PI * 2 * 2.2 + t * 1.2) * 0.10
    const bass = grp(bands, 0, 3)
    const mid = grp(bands, 4, 9)
    const high = grp(bands, 10, 19)
    return Math.sin(x01 * Math.PI * 2 * 2.4 + t * 2.2) * (0.10 + bass * 0.75)
      + Math.sin(x01 * Math.PI * 2 * 6.8 - t * 3.4) * (0.05 + mid * 0.42)
      + Math.sin(x01 * Math.PI * 2 * 15.5 + t * 5.1) * (0.03 + high * 0.28)
  }

  return {
    draw(ctx, f) {
      const { w, h, t, dt } = f
      ctx.clearRect(0, 0, w, h)
      ambient(ctx, f)
      const cy = h * 0.55
      const amp = h * 0.30
      const lvl = f.level / 100
      const p = pulse(f.level, dt)
      const idle = !f.live
      const alpha = idle ? 0.4 : 1

      // Faint graticule — center line + tick marks, oscilloscope furniture.
      ctx.strokeStyle = `rgba(140, 180, 255, ${0.05 + p * 0.05})`
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.moveTo(0, cy); ctx.lineTo(w, cy)
      ctx.stroke()

      ctx.globalCompositeOperation = 'lighter'
      ctx.lineJoin = 'round'
      ctx.lineCap = 'round'

      // Beat bloom — the whole beam zone washes bright on transients.
      if (p > 0.05) {
        const bg = ctx.createRadialGradient(w / 2, cy, 0, w / 2, cy, w * 0.4)
        bg.addColorStop(0, `rgba(120, 255, 220, ${p * 0.12})`)
        bg.addColorStop(1, 'rgba(120, 255, 220, 0)')
        ctx.fillStyle = bg
        ctx.fillRect(0, 0, w, h)
      }

      // Ghost echoes — the same trace a beat ago, dimmer and offset.
      const echo = (lag: number, lift: number, a: number, width: number) => {
        ctx.beginPath()
        for (let i = 0; i <= PTS; i++) {
          const x01 = i / PTS
          const x = x01 * w
          const y = cy + trace(f.bands, x01, t - lag, idle) * amp - lift
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
        }
        ctx.strokeStyle = `rgba(90, 200, 255, ${a * alpha})`
        ctx.lineWidth = width
        ctx.stroke()
      }
      echo(0.16, amp * 0.10, 0.10 + lvl * 0.04, 1.4)
      echo(0.08, amp * 0.05, 0.18 + lvl * 0.06, 2.0)

      // Main beam — thickness and glow swell with the beat.
      const beamW = 2.4 + p * 3.5 + lvl * 0.8
      const hue = 168 - p * 40 - lvl * 18 // green → teal as it gets loud
      ctx.beginPath()
      for (let i = 0; i <= PTS; i++) {
        const x01 = i / PTS
        const x = x01 * w
        const y = cy + trace(f.bands, x01, t, idle) * amp
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
      }
      ctx.strokeStyle = `hsla(${hue}, 100%, ${(58 + p * 26) * alpha}%, ${0.95 * alpha})`
      ctx.lineWidth = beamW
      ctx.stroke()
      // Hot halo pass.
      ctx.strokeStyle = `hsla(${hue}, 100%, 80%, ${(0.22 + p * 0.3) * alpha})`
      ctx.lineWidth = beamW * 2.6
      ctx.stroke()
      ctx.globalCompositeOperation = 'source-over'
    },
  }
}

// ---------------------------------------------------------------------------
// Ring — the audio waveform drawn in a circle. Angle acts as the time axis;
// three integer harmonics (guaranteed closed) are weighted by the
// bass/mid/treble band groups, so the radius ripples like a wrapped scope
// trace and keeps morphing over time. The whole ring breathes, thumps on
// beats, and lobs a fading shockwave ring on hard hits.
// ---------------------------------------------------------------------------

function createRing(): SpectrumRenderer {
  const PTS = 144
  const pulse = createPulse()
  const ambient = createAmbient({ h1: 190, h2: 315 })
  const shocks: Array<{ r: number; life: number }> = []
  let shockCd = 0

  const grp = (bands: number[], a: number, b: number) => {
    let s = 0
    for (let i = a; i <= b; i++) s += bands[i] ?? 0
    return s / ((b - a + 1) * 100)
  }

  const wave = (bands: number[], th: number, t: number, idle: boolean) => {
    if (idle) return Math.sin(th * 4 + t * 0.9) * 0.08
    const bass = grp(bands, 0, 3)
    const mid = grp(bands, 4, 9)
    const high = grp(bands, 10, 19)
    return Math.sin(th * 3 + t * 1.6) * (0.12 + bass * 0.8)
      + Math.sin(th * 6 - t * 2.6) * (0.06 + mid * 0.45)
      + Math.sin(th * 11 + t * 4.2) * (0.04 + high * 0.32)
  }

  return {
    draw(ctx, f) {
      const { w, h, t, dt } = f
      ctx.clearRect(0, 0, w, h)
      ambient(ctx, f)
      const cx = w / 2, cy = h / 2
      const dim = Math.min(w, h)
      const lvl = f.level / 100
      const p = pulse(f.level, dt)
      const idle = !f.live
      const alpha = idle ? 0.35 : 1
      // Slow breathing + beat swell — "radius changing over time".
      const R = dim * 0.30 * (1 + Math.sin(t * 0.55) * 0.05 + p * 0.12)

      // Shockwave rings expanding off hard beats.
      shockCd -= dt
      if (p > 0.45 && shockCd <= 0) { shocks.push({ r: R, life: 0 }); shockCd = 0.7 }
      for (let i = shocks.length - 1; i >= 0; i--) {
        const s = shocks[i]
        s.life += dt
        s.r += dt * dim * 0.55
        const k = 1 - s.life / 1.4
        if (k <= 0) { shocks.splice(i, 1); continue }
        ctx.strokeStyle = `rgba(150, 230, 255, ${(k * 0.28) * alpha})`
        ctx.lineWidth = 1.5 + k * 3
        ctx.beginPath()
        ctx.arc(cx, cy, s.r, 0, Math.PI * 2)
        ctx.stroke()
      }

      // Core orb — dim ember at rest, flares on the beat.
      const coreR = R * (0.10 + lvl * 0.10 + p * 0.10)
      const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR * 2.4)
      core.addColorStop(0, `rgba(255, 170, 255, ${(0.35 + p * 0.4) * alpha})`)
      core.addColorStop(1, 'rgba(255, 120, 255, 0)')
      ctx.fillStyle = core
      ctx.beginPath()
      ctx.arc(cx, cy, coreR * 2.4, 0, Math.PI * 2)
      ctx.fill()

      ctx.globalCompositeOperation = 'lighter'
      ctx.lineJoin = 'round'

      const ring = (scale: number, width: number, rgb: string, a: number) => {
        ctx.beginPath()
        for (let i = 0; i <= PTS; i++) {
          const th = (i / PTS) * Math.PI * 2
          const r = R * scale + wave(f.bands, th, t, idle) * R * 0.5 * scale
          const x = cx + Math.cos(th) * r
          const y = cy + Math.sin(th) * r
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
        }
        ctx.closePath()
        ctx.strokeStyle = `rgba(${rgb}, ${a * alpha})`
        ctx.lineWidth = width
        ctx.stroke()
      }
      ring(1, 5.5, '255, 90, 235', 0.14 + p * 0.12)   // magenta halo
      ring(1, 1.8, '255, 130, 245', 0.85)              // main trace
      ring(0.68, 4, '90, 220, 255', 0.12)              // cyan echo halo
      ring(0.68, 1.3, '120, 235, 255', 0.6)            // cyan echo

      // Orbiting grain — a few dozen dots riding the trace.
      for (let i = 0; i < 36; i++) {
        const th = (i / 36) * Math.PI * 2 + t * 0.35
        const r = R + wave(f.bands, th - t * 0.35, t, idle) * R * 0.5
        const tw = 0.5 + 0.5 * Math.sin(t * 3 + i * 1.7)
        ctx.fillStyle = `rgba(255, 200, 255, ${(0.16 + 0.3 * tw) * alpha})`
        ctx.beginPath()
        ctx.arc(cx + Math.cos(th) * r, cy + Math.sin(th) * r, 1.4, 0, Math.PI * 2)
        ctx.fill()
      }
      ctx.globalCompositeOperation = 'source-over'
    },
  }
}

// ---------------------------------------------------------------------------
// Mirror — FFT bars again, but grown off a lit center line upward AND
// reflected downward, so the spectrum reads as a symmetric neon double
// comb. Distinct from the bottom-anchored Winamp bar row.
// ---------------------------------------------------------------------------

function createMirror(): SpectrumRenderer {
  const BANDS = 20
  const pulse = createPulse()
  const ambient = createAmbient({ h1: 280, h2: 195 })
  return {
    draw(ctx, f) {
      const { w, h, t, dt } = f
      ctx.clearRect(0, 0, w, h)
      ambient(ctx, f)
      const cy = h * 0.5
      const lvl = f.level / 100
      const p = pulse(f.level, dt)
      const idle = !f.live
      const alpha = idle ? 0.4 : 1
      const gap = Math.max(4, w * 0.008)
      const barW = Math.max((w - (BANDS - 1) * gap) / BANDS, 2)
      const half = h * 0.42

      ctx.globalCompositeOperation = 'lighter'

      // Center bus — a lit rail that flares with the beat.
      const rail = ctx.createLinearGradient(0, cy - 14, 0, cy + 14)
      rail.addColorStop(0, 'rgba(80, 240, 255, 0)')
      rail.addColorStop(0.5, `rgba(140, 250, 255, ${(0.22 + p * 0.5) * alpha})`)
      rail.addColorStop(1, 'rgba(80, 240, 255, 0)')
      ctx.fillStyle = rail
      ctx.fillRect(0, cy - 14, w, 28)

      for (let i = 0; i < BANDS; i++) {
        const stub = 0.015 + Math.sin(t * 1.3 + i * 0.5) * 0.006
        const v = idle ? stub * 100 : f.bands[i]
        const barH = Math.max(2, (v / 100) * half)
        const x = i * (barW + gap)
        const hue = 195 + (i / (BANDS - 1)) * 100 + Math.sin(t * 0.5) * 14 // cyan→magenta drift

        // Up bar — full brightness.
        const up = ctx.createLinearGradient(0, cy, 0, cy - barH)
        up.addColorStop(0, `hsla(${hue}, 95%, 55%, ${0.55 * alpha})`)
        up.addColorStop(1, `hsla(${hue}, 100%, 68%, ${0.95 * alpha})`)
        ctx.fillStyle = up
        ctx.fillRect(x, cy - barH, barW, barH)

        // Down mirror — dimmer, slightly compressed, reads as reflection.
        const dn = ctx.createLinearGradient(0, cy, 0, cy + barH * 0.8)
        dn.addColorStop(0, `hsla(${hue}, 95%, 50%, ${0.40 * alpha})`)
        dn.addColorStop(1, `hsla(${hue}, 100%, 60%, ${0.08 * alpha})`)
        ctx.fillStyle = dn
        ctx.fillRect(x, cy, barW, barH * 0.8)

        // Tip cap on hot bars.
        if (v > 45) {
          ctx.fillStyle = `hsla(${hue}, 100%, 84%, ${(0.5 + v / 200) * alpha})`
          ctx.fillRect(x, cy - barH - 3, barW, 2.5)
        }
      }
      ctx.globalCompositeOperation = 'source-over'
    },
  }
}

// ---------------------------------------------------------------------------
// Psyche — the psychedelic one. A rotating kaleidoscope of spectrum-driven
// petals (10 wedges, each petal's reach is a mirrored band sample) drawn
// additively over a translucent-black trail fade, so motion smears into
// light ribbons. Hue races the full wheel continuously, the center bloom
// inverts the palette, and the whole mandala swells on the beat.
// ---------------------------------------------------------------------------

function createPsyche(): SpectrumRenderer {
  const K = 10
  const PTS = 20
  const pulse = createPulse()

  return {
    draw(ctx, f) {
      const { w, h, t, dt } = f
      const p = pulse(f.level, dt)
      const lvl = f.level / 100
      const idle = !f.live
      const alpha = idle ? 0.45 : 1
      const cx = w / 2, cy = h / 2
      const R = Math.min(w, h) * (0.40 + p * 0.05)
      const rot = t * 0.22
      const hueBase = (t * 42 + lvl * 90) % 360
      // Trail fade instead of a clear — the smear IS the effect. Tinted by
      // the drifting hue so the decay itself carries ambient color; a
      // solid ambient layer would erase the accumulation.
      ctx.fillStyle = `rgba(${hslRgb(hueBase + 180, 52, 5)}, ${0.16 - Math.min(0.06, p * 0.05)})`
      ctx.fillRect(0, 0, w, h)

      ctx.save()
      ctx.translate(cx, cy)
      ctx.globalCompositeOperation = 'lighter'

      for (let i = 0; i < K; i++) {
        const v = idle
          ? 0.18 + Math.sin(t * 1.1 + i * 0.7) * 0.06
          : sampleBandsCircular(f.bands, i / K) / 100
        const len = R * (0.28 + v * 0.95) + p * R * 0.14
        const wid = R * (0.18 + v * 0.12)
        const hue = (hueBase + i * (360 / K) + v * 40) % 360

        ctx.save()
        ctx.rotate(rot + (i / K) * Math.PI * 2)
        // Petal ribbon — a pointed ellipse kissing the center.
        ctx.beginPath()
        ctx.moveTo(0, 0)
        for (let j = 1; j <= PTS; j++) {
          const u = j / PTS
          const px = Math.sin(u * Math.PI) * wid
          const py = u * len
          ctx.lineTo(px, py)
        }
        for (let j = PTS; j >= 1; j--) {
          const u = j / PTS
          ctx.lineTo(-Math.sin(u * Math.PI) * wid, u * len)
        }
        ctx.closePath()
        ctx.fillStyle = `hsla(${hue}, 95%, 58%, ${0.14 * alpha})`
        ctx.fill()
        ctx.strokeStyle = `hsla(${hue}, 100%, 70%, ${0.50 * alpha})`
        ctx.lineWidth = 1.4
        ctx.stroke()

        // Petal tip spark.
        ctx.fillStyle = `hsla(${hue}, 100%, 82%, ${(0.4 + v * 0.4) * alpha})`
        ctx.beginPath()
        ctx.arc(0, len, 2 + v * 2.5, 0, Math.PI * 2)
        ctx.fill()
        ctx.restore()
      }

      // Inverted center bloom — the palette's complement, swelling on beats.
      const coreR = R * (0.16 + lvl * 0.12 + p * 0.10)
      const core = ctx.createRadialGradient(0, 0, 0, 0, 0, coreR * 2)
      core.addColorStop(0, `hsla(${(hueBase + 180) % 360}, 100%, 72%, ${(0.28 + p * 0.25) * alpha})`)
      core.addColorStop(1, 'rgba(0,0,0,0)')
      ctx.fillStyle = core
      ctx.beginPath()
      ctx.arc(0, 0, coreR * 2, 0, Math.PI * 2)
      ctx.fill()

      // Orbiting dust — two rings of hue-cycling grains, counter-rotating.
      for (let i = 0; i < 44; i++) {
        const dir = i % 2 ? -1 : 1
        const rr = R * (0.5 + (i % 11) * 0.055)
        const a = dir * t * (0.3 + (i % 5) * 0.06) + i * 2.4
        const hue = (hueBase + i * 17 + 90) % 360
        ctx.fillStyle = `hsla(${hue}, 100%, 78%, ${0.30 * alpha})`
        ctx.beginPath()
        ctx.arc(Math.cos(a) * rr, Math.sin(a) * rr * 0.96, 1.5, 0, Math.PI * 2)
        ctx.fill()
      }
      ctx.restore()
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
  { id: 'rgb', label: 'RGB Bars', create: createRgbBars },
  { id: 'iso', label: 'Iso Field', create: createIso },
  { id: 'scope', label: 'Scope', create: createScope },
  { id: 'aurora', label: 'Aurora', create: createAurora },
  { id: 'ember', label: 'Ember', create: createEmber },
  { id: 'rotor', label: 'Rotor 3D', create: createRotor },
  { id: 'swarm', label: 'Swarm', create: createSwarm },
  { id: 'wave', label: 'Waveform', create: createWave },
  { id: 'ring', label: 'Wave Ring', create: createRing },
  { id: 'mirror', label: 'Mirror Bars', create: createMirror },
  { id: 'psyche', label: 'Psychedelia', create: createPsyche },
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
