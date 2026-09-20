import type { Component } from 'vue'

import AcidSquares from '@/components/backgrounds/AcidSquares.vue'
import AeroShards from '@/components/backgrounds/AeroShards.vue'
import Aurora from '@/components/backgrounds/Aurora.vue'
import Balatro from '@/components/backgrounds/Balatro.vue'
import BeamsBackground from '@/components/backgrounds/BeamsBackground.vue'
import CrtWarp from '@/components/backgrounds/CrtWarp.vue'
import DarkVeil from '@/components/backgrounds/DarkVeil.vue'
import EvilEye from '@/components/backgrounds/EvilEye.vue'
import FaultyTerminal from '@/components/backgrounds/FaultyTerminal.vue'
import Ferrofluid from '@/components/backgrounds/Ferrofluid.vue'
import FloatingLines from '@/components/backgrounds/FloatingLines.vue'
import FloatingLinesWave from '@/components/backgrounds/FloatingLinesWave.vue'
import FloatingPathsBackground from '@/components/backgrounds/FloatingPathsBackground.vue'
import FloatingPathsBackgroundV2 from '@/components/backgrounds/FloatingPathsBackgroundV2.vue'
import Galaxy from '@/components/backgrounds/Galaxy.vue'
import GhostFibers from '@/components/backgrounds/GhostFibers.vue'
import GradientBlinds from '@/components/backgrounds/GradientBlinds.vue'
import GradientWavesOgl from '@/components/backgrounds/GradientWaves.vue'
import Grainient from '@/components/backgrounds/Grainient.vue'
import Iridescence from '@/components/backgrounds/Iridescence.vue'
import LetterGlitch from '@/components/backgrounds/LetterGlitch.vue'
import Lightfall from '@/components/backgrounds/Lightfall.vue'
import Lightning from '@/components/backgrounds/Lightning.vue'
import LightPillar from '@/components/backgrounds/LightPillar.vue'
import LightRays from '@/components/backgrounds/LightRays.vue'
import LightTunnel from '@/components/backgrounds/LightTunnel.vue'
import LineWaves from '@/components/backgrounds/LineWaves.vue'
import LiquidChrome from '@/components/backgrounds/LiquidChrome.vue'
import MoltenMetal from '@/components/backgrounds/MoltenMetal.vue'
import Orb from '@/components/backgrounds/Orb.vue'
import ParticlesOgl from '@/components/backgrounds/Particles.vue'
import Plasma from '@/components/backgrounds/Plasma.vue'
import PlasmaWave from '@/components/backgrounds/PlasmaWave.vue'
import Prism from '@/components/backgrounds/Prism.vue'
import PrismaticBurst from '@/components/backgrounds/PrismaticBurst.vue'
import Radar from '@/components/backgrounds/Radar.vue'
import RippleGrid from '@/components/backgrounds/RippleGrid.vue'
import Scanner from '@/components/backgrounds/Scanner.vue'
import ShapeGrid from '@/components/backgrounds/ShapeGrid.vue'
import ShapeWaves from '@/components/backgrounds/ShapeWaves.vue'
import Silk from '@/components/backgrounds/Silk.vue'
import SlicedWaves from '@/components/backgrounds/SlicedWaves.vue'
import SoftAurora from '@/components/backgrounds/SoftAurora.vue'
import Threads from '@/components/backgrounds/Threads.vue'
import Topography from '@/components/backgrounds/Topography.vue'
import WavesCanvas from '@/components/backgrounds/Waves.vue'
import WebThreads from '@/components/backgrounds/WebThreads.vue'

export type BackgroundKind = 'css' | 'component' | 'image'
export type BackgroundGroup = 'default' | 'gradient' | 'animated' | 'custom'

export interface BackgroundOption {
  id: string
  label: string
  group: BackgroundGroup
  kind: BackgroundKind
  /** Present only when kind === 'component'. */
  component?: Component
}

export const DEFAULT_BACKGROUND_ID = 'default'

/**
 * Every background VDock offers, declared once.
 *
 * The picker, the renderer and the settings migration all read this array.
 * Two settings used to declare backgrounds separately and silently cancel
 * each other out; a single list is what makes that impossible.
 *
 * `particles`/`floating-particles` and `aurora`/`aurora-borealis` are kept as
 * separate entries on purpose: they are visually distinct WebGL and CSS
 * implementations, and deleting either would remove a background someone is
 * already using. Their labels disambiguate them.
 */
export const BACKGROUNDS: readonly BackgroundOption[] = [
  { id: 'default', label: 'Default (Gradient)', group: 'default', kind: 'css' },

  { id: 'ocean-breeze', label: 'Ocean Breeze', group: 'gradient', kind: 'css' },
  { id: 'sunset-glow', label: 'Sunset Glow', group: 'gradient', kind: 'css' },
  { id: 'forest-mist', label: 'Forest Mist', group: 'gradient', kind: 'css' },
  { id: 'royal-purple', label: 'Royal Purple', group: 'gradient', kind: 'css' },
  { id: 'golden-hour', label: 'Golden Hour', group: 'gradient', kind: 'css' },

  { id: 'floating-particles', label: 'Floating Particles (CSS)', group: 'animated', kind: 'css' },
  { id: 'gradient-waves', label: 'Gradient Waves', group: 'animated', kind: 'css' },
  { id: 'geometric-patterns', label: 'Geometric Patterns', group: 'animated', kind: 'css' },
  { id: 'aurora-borealis', label: 'Aurora Borealis (CSS)', group: 'animated', kind: 'css' },
  { id: 'starfield', label: 'Starfield', group: 'animated', kind: 'css' },
  { id: 'bubble-float', label: 'Floating Bubbles', group: 'animated', kind: 'css' },
  { id: 'neon-grid', label: 'Neon Grid', group: 'animated', kind: 'css' },

  { id: 'particles', label: 'Dark Veil (Particles)', group: 'animated', kind: 'component', component: DarkVeil },
  { id: 'waves', label: 'Floating Lines (Waves)', group: 'animated', kind: 'component', component: FloatingLines },
  { id: 'lightning', label: 'Lightning', group: 'animated', kind: 'component', component: Lightning },
  { id: 'light-pillar', label: 'Light Pillar', group: 'animated', kind: 'component', component: LightPillar },
  { id: 'floating-lines-wave', label: 'Floating Lines Wave', group: 'animated', kind: 'component', component: FloatingLinesWave },
  { id: 'prismatic-burst', label: 'Prismatic Burst', group: 'animated', kind: 'component', component: PrismaticBurst },
  { id: 'iridescence', label: 'Iridescence', group: 'animated', kind: 'component', component: Iridescence },
  { id: 'silk', label: 'Silk', group: 'animated', kind: 'component', component: Silk },
  { id: 'light-rays', label: 'Light Rays', group: 'animated', kind: 'component', component: LightRays },
  { id: 'aurora', label: 'Aurora (WebGL)', group: 'animated', kind: 'component', component: Aurora },
  { id: 'floating-paths', label: 'Floating Paths', group: 'animated', kind: 'component', component: FloatingPathsBackground },
  { id: 'floating-paths-v2', label: 'Floating Paths V2', group: 'animated', kind: 'component', component: FloatingPathsBackgroundV2 },
  { id: 'beams-background', label: 'Beams Background', group: 'animated', kind: 'component', component: BeamsBackground },

  // reactbits.dev ports. The WebGPU pair needs navigator.gpu (Chromium);
  // they fail soft (reportFailure) where WebGPU is unavailable.
  { id: 'ghost-fibers', label: 'Ghost Fibers', group: 'animated', kind: 'component', component: GhostFibers },
  { id: 'gradient-waves-ogl', label: 'Gradient Waves (WebGL)', group: 'animated', kind: 'component', component: GradientWavesOgl },
  { id: 'molten-metal', label: 'Molten Metal', group: 'animated', kind: 'component', component: MoltenMetal },
  { id: 'crt-warp', label: 'CRT Warp', group: 'animated', kind: 'component', component: CrtWarp },
  { id: 'shape-waves', label: 'Shape Waves (WebGPU)', group: 'animated', kind: 'component', component: ShapeWaves },
  { id: 'aero-shards', label: 'Aero Shards (WebGPU)', group: 'animated', kind: 'component', component: AeroShards },

  // Second reactbits.dev batch — ogl/canvas ports, verbatim renderer cores.
  { id: 'plasma', label: 'Plasma', group: 'animated', kind: 'component', component: Plasma },
  { id: 'galaxy', label: 'Galaxy', group: 'animated', kind: 'component', component: Galaxy },
  { id: 'liquid-chrome', label: 'Liquid Chrome', group: 'animated', kind: 'component', component: LiquidChrome },
  { id: 'balatro', label: 'Balatro', group: 'animated', kind: 'component', component: Balatro },
  { id: 'orb', label: 'Orb', group: 'animated', kind: 'component', component: Orb },
  { id: 'particles-ogl', label: 'Particles (WebGL)', group: 'animated', kind: 'component', component: ParticlesOgl },
  { id: 'threads', label: 'Threads', group: 'animated', kind: 'component', component: Threads },
  { id: 'faulty-terminal', label: 'Faulty Terminal', group: 'animated', kind: 'component', component: FaultyTerminal },
  { id: 'radar', label: 'Radar', group: 'animated', kind: 'component', component: Radar },
  { id: 'prism', label: 'Prism', group: 'animated', kind: 'component', component: Prism },
  { id: 'plasma-wave', label: 'Plasma Wave', group: 'animated', kind: 'component', component: PlasmaWave },
  { id: 'sliced-waves', label: 'Sliced Waves', group: 'animated', kind: 'component', component: SlicedWaves },
  { id: 'topography', label: 'Topography', group: 'animated', kind: 'component', component: Topography },
  { id: 'web-threads', label: 'Web Threads', group: 'animated', kind: 'component', component: WebThreads },
  { id: 'soft-aurora', label: 'Soft Aurora', group: 'animated', kind: 'component', component: SoftAurora },
  { id: 'light-tunnel', label: 'Light Tunnel', group: 'animated', kind: 'component', component: LightTunnel },
  { id: 'lightfall', label: 'Lightfall', group: 'animated', kind: 'component', component: Lightfall },
  { id: 'line-waves', label: 'Line Waves', group: 'animated', kind: 'component', component: LineWaves },
  { id: 'ferrofluid', label: 'Ferrofluid', group: 'animated', kind: 'component', component: Ferrofluid },
  { id: 'acid-squares', label: 'Acid Squares', group: 'animated', kind: 'component', component: AcidSquares },
  { id: 'evil-eye', label: 'Evil Eye', group: 'animated', kind: 'component', component: EvilEye },
  { id: 'grainient', label: 'Grainient', group: 'animated', kind: 'component', component: Grainient },
  { id: 'scanner', label: 'Scanner', group: 'animated', kind: 'component', component: Scanner },
  { id: 'ripple-grid', label: 'Ripple Grid', group: 'animated', kind: 'component', component: RippleGrid },
  { id: 'gradient-blinds', label: 'Gradient Blinds', group: 'animated', kind: 'component', component: GradientBlinds },
  { id: 'waves-canvas', label: 'Waves', group: 'animated', kind: 'component', component: WavesCanvas },
  { id: 'shape-grid', label: 'Shape Grid', group: 'animated', kind: 'component', component: ShapeGrid },
  { id: 'letter-glitch', label: 'Letter Glitch', group: 'animated', kind: 'component', component: LetterGlitch },
]

const BY_ID = new Map(BACKGROUNDS.map(bg => [bg.id, bg]))

const IMAGE_PREFIXES = ['/api/uploads/', '/uploads/', 'http://', 'https://']

/** True when `id` is an uploaded or remote image URL rather than a catalog id. */
export function isImageBackground(id: string): boolean {
  return IMAGE_PREFIXES.some(prefix => id.startsWith(prefix))
}

/**
 * The catalog entry for `id`.
 *
 * Unknown ids fall back to the default entry rather than returning undefined:
 * a stale or hand-edited setting should show the default background, never a
 * blank screen.
 */
export function resolveBackground(id: string): BackgroundOption {
  if (isImageBackground(id)) {
    return { id, label: 'Custom Image', group: 'custom', kind: 'image' }
  }
  return BY_ID.get(id) ?? BY_ID.get(DEFAULT_BACKGROUND_ID)!
}
