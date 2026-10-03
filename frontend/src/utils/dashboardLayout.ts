import type { DeviceClass, Orientation } from '@/composables/useDeviceClass'

/**
 * DL-147 — the single answer to "is the deck column stacked, and what shape
 * is the docked sidebar?". Replaces `DockedSidebar`'s width rules and the
 * dashboard's `@media (max-width: 768px)`, which disagreed at exactly 768px
 * (sidebar stayed a full-height column inside a stacked layout, leaving the
 * deck 0px tall).
 *
 * - `column`: full-height column beside the deck.
 * - `strip`:  horizontal bar above the deck (deck column is stacked).
 * - `hidden`: not rendered (phones are a control surface; the legacy
 *   compact-touch rule keeps the 7" panel exactly as before).
 */
export interface DashboardLayout {
  stacked: boolean
  sidebar: 'column' | 'strip' | 'hidden'
}

export interface DashboardLayoutInput {
  layoutClass: DeviceClass
  orientation: Orientation
  innerWidth: number
  compactTouch: boolean
}

/** Width below which a desktop/panel window stacks (unchanged since DL-061). */
export const STACK_BREAKPOINT = 768

export function dashboardLayout(input: DashboardLayoutInput): DashboardLayout {
  if (input.compactTouch || input.layoutClass === 'phone') {
    return { stacked: false, sidebar: 'hidden' }
  }
  const stacked =
    input.layoutClass === 'tablet'
      ? input.orientation === 'portrait'
      : input.innerWidth < STACK_BREAKPOINT
  return { stacked, sidebar: stacked ? 'strip' : 'column' }
}
