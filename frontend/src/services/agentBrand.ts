/**
 * Per-agent branding for the "waiting / needs you" surfaces: the product's own
 * logo and accent colour, so Claude Code reads orange, Cursor reads neutral,
 * and so on. Sources without a brand (generic hooks, Devin has no logo asset)
 * fall back to the original green + robot glyph.
 */
import type { CSSProperties } from 'vue'

export interface AgentBrand {
  /** Logo under /public/logos; undefined keeps the robot glyph. */
  logo?: string
  /** Accent as "r, g, b" so it can be used inside rgba(). */
  rgb: string
  /** Lighter tint for glows and the icon. */
  lightRgb: string
  /** Very dark, accent-tinted surface for the chip background. */
  bgRgb: string
  /** Text colour on the dark surface. */
  text: string
  /** Solid accent (button background). */
  solid: string
  /** Text colour on the solid accent. */
  onSolid: string
  /** Near-white highlight used at the head of the orbit. */
  pale: string
}

const DEFAULT_BRAND: AgentBrand = {
  rgb: '34, 197, 94',
  lightRgb: '134, 239, 172',
  bgRgb: '8, 26, 14',
  text: '#bbf7d0',
  solid: '#22c55e',
  onSolid: '#052e14',
  pale: '#e7fce9',
}

const BRANDS: Record<string, AgentBrand> = {
  // Anthropic's signature clay orange.
  claude: {
    logo: '/logos/claudecode-color.png',
    rgb: '217, 119, 87',
    lightRgb: '244, 176, 148',
    bgRgb: '32, 17, 11',
    text: '#fde4d6',
    solid: '#d97757',
    onSolid: '#2a1209',
    pale: '#fff1e8',
  },
  cursor: {
    logo: '/logos/cursor.png',
    rgb: '203, 213, 225',
    lightRgb: '241, 245, 249',
    bgRgb: '15, 17, 21',
    text: '#e2e8f0',
    solid: '#e2e8f0',
    onSolid: '#0f1115',
    pale: '#ffffff',
  },
  antigravity: {
    logo: '/logos/antigravity-color.png',
    rgb: '66, 133, 244',
    lightRgb: '158, 193, 251',
    bgRgb: '9, 16, 31',
    text: '#dbe8fd',
    solid: '#4285f4',
    onSolid: '#06142e',
    pale: '#eef4ff',
  },
  codex: {
    logo: '/logos/codex-color.png',
    rgb: '16, 163, 127',
    lightRgb: '110, 220, 190',
    bgRgb: '7, 24, 20',
    text: '#c7f3e6',
    solid: '#10a37f',
    onSolid: '#031a14',
    pale: '#e6fbf4',
  },
}

export function agentBrandFor(source: string | undefined | null): AgentBrand {
  return (source && BRANDS[source]) || DEFAULT_BRAND
}

/** CSS custom properties consumed by the waiting frame, chip and banner. */
export function agentBrandVars(source: string | undefined | null): CSSProperties {
  const b = agentBrandFor(source)
  return {
    '--agent-rgb': b.rgb,
    '--agent-light-rgb': b.lightRgb,
    '--agent-bg-rgb': b.bgRgb,
    '--agent-text': b.text,
    '--agent-solid': b.solid,
    '--agent-on-solid': b.onSolid,
    '--agent-pale': b.pale,
  } as CSSProperties
}
