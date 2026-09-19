import { isImageBackground, resolveBackground } from '@/data/backgrounds'

export interface SceneBg { image?: string }

export interface PageBg {
  type: 'solid' | 'gradient' | 'image'
  color?: string
  image?: string
  gradient?: { direction?: string; from: string; to: string }
}

const COVER = {
  backgroundSize: 'cover',
  backgroundPosition: 'center',
  backgroundRepeat: 'no-repeat',
}

/**
 * The dashboard class for the resolved background.
 *
 * Component-kind backgrounds render in BackgroundRenderer, so they contribute
 * nothing here. A page or scene background overrides the global one instead of
 * being suppressed by it, which is what the old `backgroundPreference !== none`
 * bail-outs got wrong.
 */
export function backgroundClassFor(
  background: string,
  scene?: SceneBg,
  page?: PageBg,
): string {
  if (page) return ''
  if (scene?.image) return 'dashboard-bg-custom'
  if (isImageBackground(background)) return 'dashboard-bg-custom'

  const option = resolveBackground(background)
  if (option.kind === 'component') return ''
  if (option.id === 'default') return ''
  return `dashboard-bg-${option.id}`
}

/** Inline styles for the resolved background, following the same precedence. */
export function backgroundStyleFor(
  background: string,
  scene?: SceneBg,
  page?: PageBg,
): Record<string, string> {
  if (page) {
    if (page.type === 'solid' && page.color) {
      return { backgroundColor: page.color }
    }
    if (page.type === 'gradient' && page.gradient) {
      const { direction = '135deg', from, to } = page.gradient
      return { background: `linear-gradient(${direction}, ${from}, ${to})` }
    }
    if (page.type === 'image' && page.image) {
      return { backgroundImage: `url(${page.image})`, ...COVER }
    }
    return {}
  }

  if (scene?.image) {
    return { backgroundImage: `url(${scene.image})`, ...COVER }
  }

  if (isImageBackground(background)) {
    return { backgroundImage: `url(${background})`, ...COVER }
  }

  return {}
}
