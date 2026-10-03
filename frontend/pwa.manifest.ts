/**
 * The web app manifest, kept apart from vite.config.ts so a test can hold it
 * to what installing on a phone needs (DL-147): standalone display, a
 * 192 + 512 "any" icon and a maskable one that really have those dimensions.
 */
export const pwaManifest = {
  name: 'VDock',
  short_name: 'VDock',
  description: 'Virtual Stream Deck - Control your computer with customizable buttons',
  theme_color: '#182235',
  background_color: '#182235',
  display: 'standalone' as const,
  start_url: '/',
  scope: '/',
  // Android (Samsung Internet / Chrome) needs a 192 + 512 "any" icon
  // and a separate full-bleed "maskable" one for adaptive launchers.
  icons: [
    {
      src: '/pwa-192x192.png',
      sizes: '192x192',
      type: 'image/png',
      purpose: 'any',
    },
    {
      src: '/pwa-512x512.png',
      sizes: '512x512',
      type: 'image/png',
      purpose: 'any',
    },
    {
      src: '/pwa-maskable-512x512.png',
      sizes: '512x512',
      type: 'image/png',
      purpose: 'maskable',
    },
  ],
}
