/**
 * GPU spectrum skins (DL-139) — two skins that draw into their own
 * offscreen WebGL canvas and blit into the stage's 2D context each frame,
 * so the crossfade/governor/widget pipeline is untouched.
 *
 *   wavegrid — Three.js: 16×16 instanced columns in a travelling height
 *              wave, coloured by height, one shadow key light + sky fill,
 *              orbiting camera
 *   flight   — Three.js: camera rides a closed Catmull-Rom spline
 *              through the bore of 60 neon rings + floating blocks,
 *              banking into turns, beat driving cruise speed and ring
 *              hues, exponential fog, grid floor
 *
 * (DL-139 follow-up: the WebGL-shader skins — Smoke Plume and Liquid
 * Chrome — were cut on taste grounds; the custom fragment-shader plumbing
 * went with them.)
 *
 * Every skin degrades to a 2D fallback when WebGL is unavailable (jsdom
 * tests, GL-less panels) — creation is guarded, never throws.
 */

import * as THREE from 'three'
import {
  createAmbient,
  createPulse,
  demoBands,
  hslRgb,
  type SpectrumFrame,
  type SpectrumRenderer,
} from './spectrumSkins'

// ---------------------------------------------------------------------------
// Shared audio drive + fallbacks
// ---------------------------------------------------------------------------

interface Drive {
  lvl: number
  bass: number
  beat: number
  bands: number[]
  t: number
  dt: number
}

/** Per-frame audio values; when the stream is silent a 122 BPM synthetic
 *  clock and the demo-band swatch keep the scene alive (beat-synced
 *  fallback). */
function makeDrive(): (f: SpectrumFrame) => Drive {
  const pulse = createPulse()
  return f => {
    const idle = !f.live
    const synth = Math.pow(
      Math.max(0, Math.sin(f.t * Math.PI * 2 * (122 / 60))), 3)
    const bands = idle ? demoBands(f.t).map(v => v * 0.35) : f.bands
    const bass = ((bands[0] ?? 0) + (bands[1] ?? 0)
      + (bands[2] ?? 0) + (bands[3] ?? 0)) / 400
    return {
      lvl: idle ? synth * 0.5 : f.level / 100,
      bass: idle ? synth * 0.7 : bass,
      beat: idle ? synth : pulse(f.level, f.dt),
      bands,
      t: f.t,
      dt: f.dt,
    }
  }
}

/** 2D stand-in used when WebGL can't be created — ambient wash + slow
 *  drifting orbs so GL-less devices still get a themed saver. */
function fallback2d(h1: number, h2: number): SpectrumRenderer {
  const ambient = createAmbient({ h1, h2 })
  return {
    draw(ctx, f) {
      ctx.clearRect(0, 0, f.w, f.h)
      ambient(ctx, f)
      const lvl = f.level / 100
      ctx.globalCompositeOperation = 'lighter'
      for (let i = 0; i < 6; i++) {
        const a = f.t * (0.12 + i * 0.03) + i * 1.1
        const x = f.w * (0.5 + Math.cos(a) * 0.28)
        const y = f.h * (0.5 + Math.sin(a * 1.3) * 0.25)
        const r = f.h * (0.10 + 0.06 * Math.sin(f.t + i))
        const g = ctx.createRadialGradient(x, y, 0, x, y, r)
        g.addColorStop(0, `rgba(${hslRgb(h1 + i * 18, 80, 60)}, ${0.16 + lvl * 0.12})`)
        g.addColorStop(1, 'rgba(0,0,0,0)')
        ctx.fillStyle = g
        ctx.beginPath()
        ctx.arc(x, y, r, 0, Math.PI * 2)
        ctx.fill()
      }
      ctx.globalCompositeOperation = 'source-over'
    },
  }
}

// ---------------------------------------------------------------------------
// Three.js plumbing — one offscreen renderer per skin, blitted per frame
// ---------------------------------------------------------------------------

interface ThreeScene {
  render(a: Drive, f: SpectrumFrame): void
  resize?(w: number, h: number): void
}

function createThreeSkin(build: (r: THREE.WebGLRenderer) => ThreeScene,
                         h1: number, h2: number): SpectrumRenderer {
  const drive = makeDrive()
  const fb = fallback2d(h1, h2)
  let cv: HTMLCanvasElement | null = null
  let renderer: THREE.WebGLRenderer | null = null
  let inst: ThreeScene | null = null
  return {
    draw(ctx, f) {
      if (!cv) {
        if (typeof document === 'undefined') { fb.draw(ctx, f); return }
        cv = document.createElement('canvas')
        try {
          renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true })
          renderer.setPixelRatio(1)
          inst = build(renderer)
        } catch {
          cv = null
          fb.draw(ctx, f)
          return
        }
      }
      if (!renderer || !inst) { fb.draw(ctx, f); return }
      const w = Math.max(64, Math.round(f.w))
      const h = Math.max(64, Math.round(f.h))
      if (cv.width !== w || cv.height !== h) {
        renderer.setSize(w, h, false)
        inst.resize?.(w, h)
      }
      inst.render(drive(f), f)
      ctx.drawImage(cv, 0, 0, w, h, 0, 0, f.w, f.h)
    },
  }
}

// ---------------------------------------------------------------------------
// Wave Grid — 16×16 instanced columns in a travelling height wave
// ---------------------------------------------------------------------------

function buildWaveGrid(renderer: THREE.WebGLRenderer): ThreeScene {
  const scene = new THREE.Scene()
  scene.background = new THREE.Color(0x060912)
  scene.fog = new THREE.Fog(0x060912, 34, 115)
  const cam = new THREE.PerspectiveCamera(50, 1, 0.1, 300)

  const N = 16
  const geo = new THREE.BoxGeometry(1.6, 1, 1.6)
  const mat = new THREE.MeshStandardMaterial({ roughness: 0.35, metalness: 0.55 })
  const mesh = new THREE.InstancedMesh(geo, mat, N * N)
  mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage)
  mesh.castShadow = true
  mesh.receiveShadow = true
  scene.add(mesh)

  // One shadow-casting key light + a soft sky fill.
  const key = new THREE.DirectionalLight(0xfff0dd, 2.6)
  key.position.set(28, 38, 14)
  key.castShadow = true
  key.shadow.mapSize.set(1024, 1024)
  key.shadow.camera.left = -26
  key.shadow.camera.right = 26
  key.shadow.camera.top = 26
  key.shadow.camera.bottom = -26
  scene.add(key)
  scene.add(new THREE.HemisphereLight(0x334466, 0x0a0c14, 1.1))

  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(500, 500),
    new THREE.MeshStandardMaterial({ color: 0x060a14, roughness: 1 }))
  ground.rotation.x = -Math.PI / 2
  ground.position.y = -0.6
  ground.receiveShadow = true
  scene.add(ground)

  const m4 = new THREE.Matrix4()
  const pos = new THREE.Vector3()
  const quat = new THREE.Quaternion()
  const scl = new THREE.Vector3()
  const col = new THREE.Color()

  return {
    resize(w, h) { cam.aspect = w / h; cam.updateProjectionMatrix() },
    render(a) {
      const { t, bands, bass, lvl } = a
      for (let gz = 0; gz < N; gz++) {
        for (let gx = 0; gx < N; gx++) {
          const i = gz * N + gx
          const x = (gx - (N - 1) / 2) * 2.1
          const z = (gz - (N - 1) / 2) * 2.1
          // Travelling wave + spectrum height — columns across x read the
          // bands, so bass lifts the left edge.
          const wave = Math.sin(gx * 0.55 + gz * 0.35 - t * 2.2) * 0.5 + 0.5
          const band = (bands[Math.min(19, gx)] ?? 0) / 100
          const ht = 0.35 + wave * 1.6 + band * 4.4 + bass * 0.8
          pos.set(x, ht / 2 - 0.55, z)
          scl.set(1, ht, 1)
          m4.compose(pos, quat, scl)
          mesh.setMatrixAt(i, m4)
          // Coloured by height: deep teal lows → hot magenta crests.
          const hn = Math.min(1, ht / 6.5)
          col.setHSL(0.60 - hn * 0.42, 0.85, 0.32 + hn * 0.34 + a.beat * 0.06)
          mesh.setColorAt(i, col)
        }
      }
      mesh.instanceMatrix.needsUpdate = true
      if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true
      const ang = t * 0.14
      cam.position.set(Math.cos(ang) * 34, 15 + Math.sin(t * 0.07) * 3 + lvl * 2,
        Math.sin(ang) * 34)
      cam.lookAt(0, 2.5, 0)
      renderer.render(scene, cam)
    },
  }
}

// ---------------------------------------------------------------------------
// Neon Flight — Catmull-Rom fly-through through rings + blocks
// ---------------------------------------------------------------------------

function buildFlight(renderer: THREE.WebGLRenderer): ThreeScene {
  const scene = new THREE.Scene()
  scene.background = new THREE.Color(0x04050c)
  scene.fog = new THREE.FogExp2(0x04050c, 0.030)
  const cam = new THREE.PerspectiveCamera(68, 1, 0.1, 400)

  const pts = [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(38, 6, -30),
    new THREE.Vector3(62, -4, 14),
    new THREE.Vector3(30, 8, 52),
    new THREE.Vector3(-18, 2, 62),
    new THREE.Vector3(-52, -6, 26),
    new THREE.Vector3(-46, 7, -28),
    new THREE.Vector3(-14, -3, -48),
  ]
  const curve = new THREE.CatmullRomCurve3(pts, true, 'centripetal')

  // 60 neon rings centered on the spline — the camera rides the same
  // curve, so it flies through every bore. A small wander keeps the
  // tunnel from feeling machine-straight (max ~3.4 off-axis, well inside
  // the 6-radius ring).
  const rings: THREE.Mesh[] = []
  const ringGeo = new THREE.TorusGeometry(6, 0.18, 8, 42)
  const ahead = new THREE.Vector3()
  for (let i = 0; i < 60; i++) {
    const u = i / 60
    const p = curve.getPointAt(u)
    const tan = curve.getTangentAt(u)
    const off = new THREE.Vector3(
      Math.sin(u * Math.PI * 9) * 2.4,
      Math.cos(u * Math.PI * 7) * 2.0,
      Math.sin(u * Math.PI * 5 + 1.3) * 1.4)
    const m = new THREE.Mesh(
      ringGeo,
      new THREE.MeshBasicMaterial({ color: 0x4466ff, fog: true }))
    m.position.copy(p).add(off)
    ahead.copy(m.position).add(tan)
    m.lookAt(ahead)
    scene.add(m)
    rings.push(m)
  }

  // Floating blocks drifting around the corridor — pushed clear of the
  // flight bore so the camera never clips through one.
  const blocks = new THREE.InstancedMesh(
    new THREE.BoxGeometry(1.4, 1.4, 1.4),
    new THREE.MeshBasicMaterial({ color: 0x1a2450, fog: true }), 90)
  const bm = new THREE.Matrix4()
  const bq = new THREE.Quaternion()
  const bs = new THREE.Vector3(1, 1, 1)
  const bp = new THREE.Vector3()
  for (let i = 0; i < 90; i++) {
    const u = (i * 37 % 90) / 90
    const p = curve.getPointAt(u)
    bp.set(p.x + Math.sin(i * 2.7) * 16, p.y + Math.cos(i * 1.9) * 12,
      p.z + Math.sin(i * 1.3 + 2) * 16)
    if (bp.distanceToSquared(p) < 81) bp.sub(p).setLength(9).add(p)
    bq.setFromEuler(new THREE.Euler(i * 0.4, i * 0.7, i * 0.2))
    bm.compose(bp, bq, bs)
    blocks.setMatrixAt(i, bm)
  }
  scene.add(blocks)

  // Grid floor far below.
  const grid = new THREE.GridHelper(600, 70, 0x2a3f8f, 0x0c1230)
  grid.position.y = -22
  scene.add(grid)

  const pos = new THREE.Vector3()
  const look = new THREE.Vector3()
  const tan0 = new THREE.Vector3()
  const tan1 = new THREE.Vector3()
  let uCruise = 0
  let hueFlow = 0

  return {
    resize(w, h) { cam.aspect = w / h; cam.updateProjectionMatrix() },
    render(a) {
      const { bands, beat, lvl, dt } = a
      // Cruise speed rides the kick — every beat is a burst of velocity.
      uCruise = (uCruise + dt * 0.012 * (1 + lvl * 0.9 + beat * 2.2)) % 1
      const u = uCruise
      curve.getPointAt(u, pos)
      curve.getPointAt((u + 0.018) % 1, look)
      cam.position.copy(pos)
      cam.lookAt(look)
      // Bank into turns: signed curvature → roll.
      curve.getTangentAt(u, tan0)
      curve.getTangentAt((u + 0.012) % 1, tan1)
      const bank = THREE.MathUtils.clamp(
        (tan0.x * tan1.z - tan0.z * tan1.x) * 6, -0.5, 0.5)
      cam.rotateZ(bank)
      // Speed surge you can feel: FOV widens a touch on each beat.
      const fov = 68 + beat * 9
      if (Math.abs(cam.fov - fov) > 0.05) {
        cam.fov = fov
        cam.updateProjectionMatrix()
      }

      // Rings: the hue wheel races faster on beats and every ring swells
      // a touch; the few ahead of the camera flash brighter.
      hueFlow = (hueFlow + dt * (0.05 + beat * 0.45)) % 1
      const lead = Math.floor(u * 60)
      for (let i = 0; i < rings.length; i++) {
        const b = (bands[i % 20] ?? 0) / 100
        const aheadness = ((i - lead + 60) % 60) < 6 ? beat * 0.25 : 0
        const m = rings[i].material as THREE.MeshBasicMaterial
        m.color.setHSL(
          (i / 60 + hueFlow) % 1, 1, 0.45 + b * 0.25 + beat * 0.15 + aheadness)
        rings[i].scale.setScalar(1 + beat * 0.07)
      }
      renderer.render(scene, cam)
    },
  }
}

// ---------------------------------------------------------------------------
// Skin factories
// ---------------------------------------------------------------------------

export function createWaveGrid(): SpectrumRenderer {
  return createThreeSkin(buildWaveGrid, 210, 265)
}

export function createFlight(): SpectrumRenderer {
  return createThreeSkin(buildFlight, 280, 200)
}
