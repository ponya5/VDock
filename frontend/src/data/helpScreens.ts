/**
 * Annotated help screenshots. `markers` positions are percentages of the
 * captured image (1024×600) so arrows stay accurate at any render scale.
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
      { n: 1, x: 21, y: 13, label: 'Scene pills — tap to switch contexts, or swipe up/down on the deck' },
      { n: 2, x: 8, y: 54, label: 'Docked sidebar — buttons visible on every scene (weather, clock, volume)' },
      { n: 3, x: 50, y: 54, label: 'Button grid — tap to run an action; swipe left/right for more pages' },
      { n: 4, x: 50, y: 12, label: 'Edit Mode — add, move, resize, and configure buttons' },
      { n: 5, x: 70, y: 12, label: 'Settings — appearance, screensaver widgets, integrations, templates' },
    ],
  },
  {
    id: 'edit-mode',
    title: 'Edit Mode',
    img: '/assets/help/edit-mode.png',
    markers: [
      { n: 1, x: 30, y: 37, label: 'Tap an empty dashed slot to add a button — or long-press to enter edit mode' },
      { n: 2, x: 79, y: 46, label: 'Button Actions panel — pick what the button does (hotkey, app, URL, macro…)' },
      { n: 3, x: 47, y: 73, label: 'Grid size — set rows × columns for the current page' },
      { n: 4, x: 79, y: 93, label: 'Save Profile — keep your changes; Add/Delete Page manage extra pages' },
      { n: 5, x: 8, y: 37, label: 'Docked buttons — drag to reorder, tap the red minus to remove' },
    ],
  },
  {
    id: 'settings',
    title: 'Settings',
    img: '/assets/help/settings.png',
    markers: [
      { n: 1, x: 10, y: 55, label: 'Sections — Appearance, Templates, Server, Integrations, Logs, About' },
      { n: 2, x: 39, y: 5, label: 'Search — jump straight to any setting by name' },
      { n: 3, x: 57, y: 17, label: 'Sub-tabs — each section splits into focused pages that fit the screen' },
      { n: 4, x: 57, y: 55, label: 'Setting cards — every option has a reset icon to restore its default' },
      { n: 5, x: 94, y: 5, label: 'Back — return to the dashboard' },
    ],
  },
]
