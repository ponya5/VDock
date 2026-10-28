import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, it, expect } from 'vitest'

const connectPanelSource = readFileSync(
  resolve(__dirname, '../components/settings/panels/PortsPanel.vue'),
  'utf-8',
)
const tutorialSource = readFileSync(resolve(__dirname, '../services/tutorial.ts'), 'utf-8')
const backendEnvExample = readFileSync(resolve(__dirname, '../../../backend/.env.example'), 'utf-8')

// A fresh install keeps LAN access off (safe default). The user must be told,
// plainly and at first launch, that phones cannot connect until they turn it on.
describe('LAN access is off by default and clearly explained', () => {
  it('ships with Allow LAN switched off', () => {
    expect(backendEnvExample).toMatch(/^ALLOW_LAN=False$/m)
  })

  it('has a single phone-access switch (no second "turn on" button)', () => {
    expect(connectPanelSource).toContain('Allow phone &amp; tablet access')
    expect(connectPanelSource).not.toContain('Turn on phone access')
  })

  it('states on the switch itself that no other device can connect without it', () => {
    expect(connectPanelSource).toContain('Off by default')
    expect(connectPanelSource).toContain('without it, no other device can connect')
  })

  it('spotlights the phone-access switch in the first-run tour', () => {
    expect(connectPanelSource).toContain('data-tour="allow-lan"')
    expect(tutorialSource).toContain("title: 'Use your phone or tablet'")
    expect(tutorialSource).toContain("target: '[data-tour=\"allow-lan\"]'")
    expect(tutorialSource).toContain('no other device can reach your deck')
  })
})
