import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { BACKGROUNDS, resolveBackground } from '@/data/backgrounds'
import { backgroundClassFor, backgroundStyleFor } from '@/utils/backgroundStyle'

// Inline styles always win over the (global, unscoped) dashboard-bg-* classes
// regardless of CSS specificity, so every branch here sets an explicit
// background — including a neutral checkerboard placeholder for the one case
// a settings preview can't render (a full animated background component).
const PREVIEW_CHECKERBOARD = 'repeating-conic-gradient(rgba(255, 255, 255, 0.06) 0% 25%, transparent 0% 50%) 50% / 20px 20px'

/**
 * Background classes/styles for the Settings preview rails, plus the picker
 * groupings shared by the dashboard and screensaver background pickers.
 */
export function useBackgroundPreview() {
  const settingsStore = useSettingsStore()

  // The dashboard's own background class/style for the current setting
  // (scene/page-background overrides aren't relevant to a settings preview)
  // so the preview pane shows exactly what the dashboard would.
  const previewBackgroundClass = computed(() => backgroundClassFor(settingsStore.background))

  const previewBackgroundStyle = computed(() => {
    const option = resolveBackground(settingsStore.background)
    if (option.kind === 'component') {
      return { background: PREVIEW_CHECKERBOARD }
    }
    if (option.id === 'default') {
      return { background: 'var(--color-background)' }
    }
    return backgroundStyleFor(settingsStore.background)
  })

  // Screensaver preview rail: 'default' means the classic dark look, not the
  // dashboard's gradient — same divergence as the screensaver picker groups.
  const screensaverPreviewClass = computed(() =>
    settingsStore.screensaverBackground === 'default' ? '' : backgroundClassFor(settingsStore.screensaverBackground)
  )
  const screensaverPreviewStyle = computed(() => {
    const id = settingsStore.screensaverBackground
    if (id === 'default') return { background: 'linear-gradient(180deg, #0c1526 0%, #070d18 100%)' }
    if (resolveBackground(id).kind === 'component') return { background: PREVIEW_CHECKERBOARD }
    return backgroundStyleFor(id)
  })

  const backgroundsByGroup = computed(() => ({
    default: BACKGROUNDS.filter(b => b.group === 'default'),
    gradient: BACKGROUNDS.filter(b => b.group === 'gradient'),
    animated: BACKGROUNDS.filter(b => b.group === 'animated'),
  }))

  return { previewBackgroundClass, previewBackgroundStyle, screensaverPreviewClass, screensaverPreviewStyle, backgroundsByGroup }
}
