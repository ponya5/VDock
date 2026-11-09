// DL-166: one word, one glyph shape and one colour per agent state, plus how long it has lasted.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import AgentStatusBanner from '@/components/AgentStatusBanner.vue'
import { formatElapsed } from '@/composables/useAgentStateSince'

const NOW = new Date('2026-11-09T12:00:00Z').getTime()

beforeEach(() => {
  vi.useFakeTimers()
  vi.setSystemTime(NOW)
})
afterEach(() => vi.useRealTimers())

function banner(props: Record<string, unknown>) {
  return mount(AgentStatusBanner, {
    props: { agentName: 'Claude Code', ...props } as never,
    global: { stubs: { FontAwesomeIcon: true } },
  })
}

describe('AgentStatusBanner', () => {
  const cases: Array<[string, string, string]> = [
    ['working', 'Working', 'circle-notch'],
    ['ready', 'Ready', 'circle-check'],
    ['permission', 'Needs you', 'triangle-exclamation'],
    ['unknown', 'Running', 'circle-dot'],
    ['offline', 'No session', 'power-off'],
  ]
  it.each(cases)('%s shows its word, glyph and state class', (state, word, icon) => {
    const w = banner({ state })
    expect(w.classes()).toContain(`state-${state}`)
    expect(w.find('[role="status"]').exists()).toBe(true)
    expect(w.find('.asb-word').text()).toBe(word)
    expect(w.find('.asb-glyph').attributes('data-icon')).toBe(icon)
  })

  it('every state has a distinct glyph, so colour is never the only signal', () => {
    const icons = cases.map(([state]) => banner({ state }).find('.asb-glyph').attributes('data-icon'))
    expect(new Set(icons).size).toBe(cases.length)
  })

  it('counts up while working', async () => {
    const w = banner({ state: 'working', sinceMs: NOW })
    expect(w.find('.asb-elapsed').text()).toBe('for 0:00')
    await vi.advanceTimersByTimeAsync(5000)
    expect(w.find('.asb-elapsed').text()).toBe('for 0:05')
    await vi.advanceTimersByTimeAsync(3600 * 1000)
    expect(w.find('.asb-elapsed').text()).toBe('for 1h 00m')
    w.unmount()
  })

  it('formats minutes and hours', () => {
    expect(formatElapsed(134_000)).toBe('2:14')
    expect(formatElapsed((3600 + 5 * 60) * 1000)).toBe('1h 05m')
  })

  it('ready shows idle minutes only once it has been idle for a minute', async () => {
    const w = banner({ state: 'ready', sinceMs: NOW })
    expect(w.find('.asb-elapsed').exists()).toBe(false)
    await vi.advanceTimersByTimeAsync(4 * 60 * 1000 + 10_000)
    expect(w.find('.asb-elapsed').text()).toBe('idle 4m')
    w.unmount()
  })

  it('hides the elapsed span from screen readers and keeps the accessible text', () => {
    const w = banner({ state: 'permission', sinceMs: NOW, detail: 'needs permission to use Bash' })
    expect(w.find('.asb-text').attributes('aria-hidden')).toBe('true')
    expect(w.find('.asb-sr').text()).toBe('Claude Code: Needs you. needs permission to use Bash')
  })

  it('uses state copy for offline / unknown and the hook detail otherwise', () => {
    expect(banner({ state: 'offline' }).find('.asb-detail').text()).toBe('Open a session to start')
    expect(banner({ state: 'unknown' }).find('.asb-detail').text()).toContain('No live status')
    expect(banner({ state: 'working', detail: 'Running tests' }).find('.asb-detail').text()).toBe('Running tests')
  })

  it('renders the link badge with the session accent and the others summary', () => {
    const w = banner({
      state: 'working',
      linked: { pid: 2, label: 'frontend', badge: 'WT', accent: '#63d0a3' },
      linkAccent: '#63d0a3',
      othersSummary: '1 other: 1 ready',
    })
    const badge = w.find('.agent-link-badge')
    expect(badge.text()).toBe('WT')
    expect(badge.attributes('style')).toContain('background')
    expect(w.find('[data-testid="others-summary"]').text()).toBe('1 other: 1 ready')
    const card = banner({ state: 'working', variant: 'card', linked: { pid: 2, label: 'f', badge: 'WT', accent: '#63d0a3' }, linkAccent: '#63d0a3' })
    expect(card.find('.mac-link-badge').exists()).toBe(true)
    expect(card.find('.asb-stripe').exists()).toBe(true)
  })
})
