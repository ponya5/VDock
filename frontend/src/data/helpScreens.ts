/**
 * Annotated help screenshots. `markers` positions are percentages of the
 * captured image so arrows stay accurate at any render scale.
 * `x`/`y` point at the feature; the numbered badge renders there with a
 * short arrow stem. Captured from the live app — see DL-044.
 */

export interface HelpMarker {
  n: number
  x: number // % from left — where the feature is
  y: number // % from top
  label: string
}

export interface HelpScreen {
  id: string
  title: string
  img: string
  markers: HelpMarker[]
}

export const HELP_SCREENS: HelpScreen[] = [
  {
    id: 'dashboard',
    title: 'Dashboard',
    img: '/assets/help/dashboard.png',
    markers: [
      { n: 1, x: 22, y: 5, label: 'Scene pills — tap to switch contexts, or swipe up/down on the deck' },
      { n: 2, x: 7, y: 50, label: 'Docked sidebar — buttons visible on every scene (weather, clock, volume)' },
      { n: 3, x: 50, y: 70, label: 'Button grid — tap to run an action; swipe left/right for more pages' },
      { n: 4, x: 68, y: 5, label: 'Edit Mode — add, move, resize, and configure buttons' },
      { n: 5, x: 77, y: 5, label: 'Settings — appearance, screensaver widgets, integrations, templates' },
    ],
  },
  {
    id: 'edit-mode',
    title: 'Edit Mode',
    img: '/assets/help/edit-mode.png',
    markers: [
      { n: 1, x: 30, y: 67, label: 'Tap an empty dashed slot to add a button — or long-press to enter edit mode' },
      { n: 2, x: 86, y: 33, label: 'Button Actions panel — pick what the button does (hotkey, app, URL, macro…)' },
      { n: 3, x: 40, y: 80, label: 'Grid size — set rows × columns for the current page' },
      { n: 4, x: 66, y: 86, label: 'Save Profile — keep your changes; Add/Delete Page manage extra pages' },
      { n: 5, x: 6, y: 34, label: 'Docked buttons — drag to reorder, tap the red minus to remove' },
    ],
  },
  {
    id: 'settings',
    title: 'Settings',
    img: '/assets/help/settings.png',
    markers: [
      { n: 1, x: 7, y: 60, label: 'Sections — Appearance, Templates, Server, Integrations, Logs, About' },
      { n: 2, x: 48, y: 4, label: 'Search — jump straight to any setting by name' },
      { n: 3, x: 50, y: 8.5, label: 'Sub-tabs — each section splits into focused pages that fit the screen' },
      { n: 4, x: 70, y: 60, label: 'Setting cards — every option has a reset icon to restore its default' },
      { n: 5, x: 95, y: 4, label: 'Back — return to the dashboard' },
    ],
  },
]
