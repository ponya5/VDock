/// <reference types="vitest" />
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import { fileURLToPath, URL } from 'node:url'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

/**
 * Mirrors the backend's own `ALLOW_LAN` gate (`backend/config.py`) so the
 * Vite dev server only accepts LAN connections when the user has actually
 * opted in via Settings → "Allow LAN access" — binding every interface
 * unconditionally would let a phone reach the dev server (and, through its
 * `/api` proxy, the backend) even with that toggle switched off. See DL-069.
 */
function isLanAccessAllowed(): boolean {
  try {
    const configPath = resolve(__dirname, '../backend/data/config.json')
    const config = JSON.parse(readFileSync(configPath, 'utf-8')) as { allow_lan?: boolean }
    return config.allow_lan === true
  } catch {
    return false
  }
}

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())
  const frontendPort = Number(env.VITE_PORT) || 3000
  const backendPort = Number(env.VITE_BACKEND_PORT) || 5000

  return {
    plugins: [
      vue(),
      VitePWA({
        registerType: 'autoUpdate',
        includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
        manifest: {
          name: 'VDock',
          short_name: 'VDock',
          description: 'Virtual Stream Deck - Control your computer with customizable buttons',
          theme_color: '#1a1a1a',
          background_color: '#1a1a1a',
          display: 'standalone',
          icons: [
            {
              src: 'pwa-192x192.png',
              sizes: '192x192',
              type: 'image/png'
            },
            {
              src: 'pwa-512x512.png',
              sizes: '512x512',
              type: 'image/png'
            },
            {
              src: 'pwa-512x512.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'any maskable'
            }
          ]
        },
        workbox: {
          globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
          // The app bundle (~2.8MB) legitimately exceeds workbox's 2MiB
          // default; Electron serves it locally so precaching is safe.
          maximumFileSizeToCacheInBytes: 4 * 1024 * 1024,
          runtimeCaching: [
            {
              urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
              handler: 'CacheFirst',
              options: {
                cacheName: 'google-fonts-cache',
                expiration: {
                  maxEntries: 10,
                  maxAgeSeconds: 60 * 60 * 24 * 365 // 1 year
                },
                cacheableResponse: {
                  statuses: [0, 200]
                }
              }
            }
          ]
        }
      })
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    server: {
      // When LAN access is enabled, bind every interface instead of just
      // localhost — a LAN device (e.g. the Connect page's QR code) hitting
      // `npm run dev` directly then gets live HMR straight from source, the
      // same as the desktop Electron window. Without this, only the
      // backend's one-time `npm run build` output was reachable over LAN,
      // so mobile devices silently kept serving whatever dist/ happened to
      // contain until someone remembered to rebuild it — desktop (Vite dev
      // server, always fresh) and mobile (a stale static build) could drift
      // arbitrarily far apart. See DL-069.
      host: isLanAccessAllowed() ? true : 'localhost',
      port: frontendPort,
      // Fail loudly instead of silently drifting to the next free port when
      // frontendPort is already taken. The silent-drift default is how
      // orphaned dev servers from earlier sessions accumulate unnoticed on
      // adjacent ports (4444, 4445, 4446, ...) — each one still perfectly
      // reachable and each one frozen at whatever code existed when it
      // started. `ensure_fresh_frontend()` in the launcher (DL-068) only
      // knows to check the one configured port; it can't clean up strays it
      // doesn't know exist. See DL-069.
      strictPort: true,
      proxy: {
        '/api': {
          target: `http://127.0.0.1:${backendPort}`,
          changeOrigin: true
        }
      }
    },
    test: {
      environment: 'jsdom',
      globals: true
    }
  }
})
