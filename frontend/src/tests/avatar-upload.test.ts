// DL-011: animated GIF avatars. The picker always accepted gif in the accept
// list, but it posted to /api/upload/icon — a route that never existed, so
// every custom upload 404'd. It now uses /api/upload with type=avatar, and
// the picker bundles a few animated presets so the feature is discoverable.
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const source = readFileSync(
  resolve(__dirname, '../components/AvatarPicker.vue'),
  'utf-8'
)

describe('avatar picker GIF support', () => {
  it('accepts gif in the file input', () => {
    expect(source).toContain('image/gif')
  })

  it('uploads to the real /api/upload route', () => {
    // /api/upload/icon never existed backend-side — the post 404'd silently.
    // Match the call itself so the explanatory comment can't false-positive.
    expect(source).toContain("apiClient.post('/upload'")
    expect(source).not.toContain("apiClient.post('/upload/icon'")
  })

  it('tags the upload as an avatar so the backend files it correctly', () => {
    expect(source).toContain("formData.append('type', 'avatar')")
  })

  it('bundles animated presets and badges them', () => {
    expect(source).toContain('animated-orbit.gif')
    expect(source).toContain("avatar.url.endsWith('.gif')")
    expect(source).toContain('avatar-badge')
  })
})

describe('bundled animated presets', () => {
  const dir = resolve(__dirname, '../../public/avatars')

  it('are real looping GIFs on disk', () => {
    for (const name of [
      'animated-orbit.gif',
      'animated-pulse.gif',
      'animated-spin.gif',
    ]) {
      const buf = readFileSync(resolve(dir, name))
      expect(buf.subarray(0, 6).toString('ascii')).toMatch(/^GIF8[79]a/)
      // NETSCAPE2.0 application extension is what makes it loop forever.
      expect(buf.includes(Buffer.from('NETSCAPE2.0'))).toBe(true)
    }
  })
})
