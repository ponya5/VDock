import type { Component } from 'vue'

import Aurora from '@/components/backgrounds/Aurora.vue'
import BeamsBackground from '@/components/backgrounds/BeamsBackground.vue'
import DarkVeil from '@/components/backgrounds/DarkVeil.vue'
import FloatingLines from '@/components/backgrounds/FloatingLines.vue'
import FloatingLinesWave from '@/components/backgrounds/FloatingLinesWave.vue'
import FloatingPathsBackground from '@/components/backgrounds/FloatingPathsBackground.vue'
import FloatingPathsBackgroundV2 from '@/components/backgrounds/FloatingPathsBackgroundV2.vue'
import Iridescence from '@/components/backgrounds/Iridescence.vue'
import Lightning from '@/components/backgrounds/Lightning.vue'
import LightPillar from '@/components/backgrounds/LightPillar.vue'
import LightRays from '@/components/backgrounds/LightRays.vue'
import PrismaticBurst from '@/components/backgrounds/PrismaticBurst.vue'
import Silk from '@/components/backgrounds/Silk.vue'

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
