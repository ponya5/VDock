// DL-147 Task 4.6 - the manifest keeps meeting what a phone needs to install
// VDock: standalone, matching colours, icons that really have the sizes claimed.
import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, it, expect } from 'vitest'
import { pwaManifest } from '../../pwa.manifest'

const root = resolve(__dirname, '..', '..')
const indexHtml = readFileSync(resolve(root, 'index.html'), 'utf-8')

function pngSize(file: string): string {
  const header = readFileSync(file)
  return `${header.readUInt32BE(16)}x${header.readUInt32BE(20)}`
}

describe('PWA manifest', () => {
  it('is a standalone app rooted at /', () => {
    expect(pwaManifest.display).toBe('standalone')
    expect(pwaManifest.start_url).toBe('/')
    expect(pwaManifest.scope).toBe('/')
  })

  it('uses the same colour as the theme-color meta tag', () => {
    const theme = /<meta name="theme-color" content="([^"]+)"/.exec(indexHtml)?.[1]
    expect(pwaManifest.theme_color).toBe(theme)
    expect(pwaManifest.background_color).toBe(theme)
  })

  it('ships 192 + 512 any icons and a 512 maskable one whose pixels match their sizes', () => {
    const find = (sizes: string, purpose: string) =>
      pwaManifest.icons.find(i => i.sizes === sizes && i.purpose === purpose)
    for (const [sizes, purpose] of [['192x192', 'any'], ['512x512', 'any'], ['512x512', 'maskable']]) {
      const icon = find(sizes, purpose)
      expect(icon, `${sizes} ${purpose}`).toBeDefined()
      const file = resolve(root, 'public', icon!.src.replace(/^\//, ''))
      expect(existsSync(file)).toBe(true)
      expect(pngSize(file)).toBe(sizes)
    }
  })

  it('index.html is ready for Home Screen launches', () => {
    expect(indexHtml).toContain('viewport-fit=cover')
    expect(indexHtml).toContain('name="apple-mobile-web-app-capable"')
    const touchIcon = /rel="apple-touch-icon"[^>]*href="\/([^"]+)"/.exec(indexHtml)?.[1]
    expect(touchIcon).toBeDefined()
    expect(existsSync(resolve(root, 'public', touchIcon!))).toBe(true)
  })

  it('is emitted by the build when dist exists', () => {
    const dist = resolve(root, 'dist', 'manifest.webmanifest')
    if (!existsSync(resolve(root, 'dist'))) return
    expect(JSON.parse(readFileSync(dist, 'utf-8')).display).toBe('standalone')
  })
})
