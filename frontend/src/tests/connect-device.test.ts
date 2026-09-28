import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, it, expect } from 'vitest'

const view = readFileSync(resolve(__dirname, '../views/SettingsView.vue'), 'utf-8')

// DL-069 follow-up: enabling "Allow LAN access" after the dev server (or
// backend) was already running leaves the QR encoding a URL nothing
// listens on — the phone silently fails to connect. The Connect card now
// probes the very URL it encodes and warns instead of printing a QR for
// a dead address.
describe('connect-a-device LAN reachability probe', () => {
  it('probes the encoded lanUrl with a no-cors fetch (opaque response = listening)', () => {
    expect(view).toContain('async function probeLanReachability()')
    expect(view).toContain("fetch(url, { mode: 'no-cors'")
    expect(view).toContain('lanReachable.value = true')
    expect(view).toContain('lanReachable.value = false')
  })

  it('warns when the QR target is unreachable instead of showing a dead code silently', () => {
    expect(view).toContain('lanUrl && lanReachable === false')
    expect(view).toContain("isn't answering on the network yet")
    expect(view).toContain('lanDeadHint')
  })

  it('names the real fix in dev — restarting the Vite dev server, not just VDock', () => {
    expect(view).toContain('npm run dev')
    expect(view).toContain("restart Vite")
  })

  it('re-probes when the URL changes and whenever the Connect tab opens', () => {
    expect(view).toContain('watch(lanUrl, probeLanReachability)')
    expect(view).toContain("if (tab === 'connect') probeLanReachability()")
  })
})
