import { describe, it, expect } from 'vitest'
import { resolveSocketUrl } from '@/utils/socketUrl'

const location = { protocol: 'http:', hostname: '192.168.1.20', origin: 'http://192.168.1.20:5055' }

describe('resolveSocketUrl', () => {
  it('uses the page origin in a built bundle, whatever port the backend runs on', () => {
    expect(resolveSocketUrl({ isDev: false, location })).toBe('http://192.168.1.20:5055')
  })

  it('keeps https when the backend serves TLS', () => {
    const tls = { protocol: 'https:', hostname: 'deck.local', origin: 'https://deck.local:5000' }
    expect(resolveSocketUrl({ isDev: false, location: tls })).toBe('https://deck.local:5000')
  })

  it('dials the backend port from the dev server', () => {
    expect(resolveSocketUrl({ isDev: true, location })).toBe('http://192.168.1.20:5000')
    expect(resolveSocketUrl({ isDev: true, backendPort: '5100', location })).toBe('http://192.168.1.20:5100')
  })

  it('lets VITE_WS_URL override both', () => {
    expect(resolveSocketUrl({ wsUrl: 'http://pc:9000', isDev: false, location })).toBe('http://pc:9000')
  })
})
