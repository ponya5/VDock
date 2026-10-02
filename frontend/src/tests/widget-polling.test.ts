// DL-144 - GitHub CI/PR widgets refresh themselves while on screen, a newly
// failed build raises one notification, and pressing a widget opens its URL.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { defineComponent, nextTick, reactive } from 'vue'
import { mount } from '@vue/test-utils'

const executeButtonAction = vi.fn()
const executeAction = vi.fn()
const markFinished = vi.fn()
const notify = { error: vi.fn(), success: vi.fn(), warning: vi.fn() }

const dashboard = reactive({
  isEditMode: false,
  currentPage: { buttons: [] as any[] },
  executeButtonAction: (...a: unknown[]) => executeButtonAction(...a),
  executeAction: (...a: unknown[]) => executeAction(...a),
})
const buttonState = reactive<{ states: Record<string, any>; markFinished: (id: string, r: any) => void }>({
  states: {},
  markFinished: (id, r) => {
    markFinished(id, r)
    buttonState.states[id] = { tone: r?.data?.status === 'critical' ? 'critical' : 'normal' }
  },
})

vi.mock('@/stores/dashboard', () => ({ useDashboardStore: () => dashboard }))
vi.mock('@/stores/buttonState', () => ({ useButtonStateStore: () => buttonState }))
vi.mock('@/stores/notifications', () => ({ useNotificationsStore: () => notify }))

const catalog = reactive<{ byActionType: Record<string, any> }>({ byActionType: {} })
vi.mock('@/stores/actionCatalog', () => ({ useActionCatalogStore: () => catalog }))

import {
  ciJustFailed,
  isPolledWidget,
  MIN_LOCAL_POLL_SECONDS,
  MIN_POLL_SECONDS,
  pollSecondsFor,
  useWidgetPolling,
} from '@/composables/useWidgetPolling'

const widget = (id: string, type = 'gh_widget_ci', config: Record<string, unknown> = {}) =>
  ({ id, action: { type, config: { refresh_interval: 60, ...config } } })

const ok = (status: string, extra: Record<string, unknown> = {}) => ({
  success: true,
  data: { badge: '•', status, conclusion: status === 'critical' ? 'failure' : 'success',
          repo: 'me/app', sublabel: 'main', url: 'https://example.test/run/1', ...extra },
})

const Host = defineComponent({ setup() { useWidgetPolling(); return () => null } })
let wrapper: ReturnType<typeof mount> | null = null

beforeEach(() => {
  vi.useFakeTimers()
  executeButtonAction.mockReset().mockResolvedValue(ok('success'))
  executeAction.mockReset()
  markFinished.mockReset()
  notify.error.mockReset()
  dashboard.isEditMode = false
  dashboard.currentPage = { buttons: [] }
  buttonState.states = {}
  catalog.byActionType = {}
})

afterEach(() => {
  wrapper?.unmount()
  wrapper = null
  vi.useRealTimers()
})

async function mountHost(buttons: any[]) {
  dashboard.currentPage = { buttons }
  wrapper = mount(Host)
  await vi.advanceTimersByTimeAsync(0)
}

describe('helpers', () => {
  it('recognises only gh_widget_* buttons', () => {
    expect(isPolledWidget(widget('a', 'gh_widget_prs') as any)).toBe(true)
    expect(isPolledWidget(widget('a', 'gh_pr_list') as any)).toBe(false)
    expect(isPolledWidget(widget('a', 'metric_cpu_usage') as any)).toBe(false)
  })

  it('floors the refresh interval and falls back to a default', () => {
    expect(pollSecondsFor(widget('a', 'gh_widget_ci', { refresh_interval: 5 }) as any)).toBe(MIN_POLL_SECONDS)
    expect(pollSecondsFor(widget('a', 'gh_widget_ci', { refresh_interval: 300 }) as any)).toBe(300)
    expect(pollSecondsFor(widget('a', 'gh_widget_ci', { refresh_interval: 'x' }) as any)).toBe(120)
    expect(pollSecondsFor({ id: 'a', action: { type: 'gh_widget_ci', config: {} } } as any)).toBe(120)
  })

  it('only counts a failure that follows a known healthy reading', () => {
    expect(ciJustFailed(undefined, false, 'critical')).toBe(false) // already red at load
    expect(ciJustFailed('normal', true, 'critical')).toBe(true)
    expect(ciJustFailed('critical', true, 'critical')).toBe(false) // still red
    expect(ciJustFailed('normal', true, 'normal')).toBe(false)
    expect(ciJustFailed(undefined, true, 'critical')).toBe(true) // known reading, tone unset
  })
})

describe('catalog live buttons (DL-145)', () => {
  const liveSpec = { poll_seconds: 15, poll_config: { op: 'status' } }

  it('treats an action with poll_seconds as a polled widget', () => {
    const button = widget('t', 'dev_run_tests') as any
    expect(isPolledWidget(button)).toBe(false)
    expect(isPolledWidget(button, liveSpec as any)).toBe(true)
  })

  it('uses the spec interval, with a 3 s floor for non-GitHub and 30 s for GitHub', () => {
    const local = { id: 't', action: { type: 'dev_run_tests', config: {} } } as any
    expect(pollSecondsFor(local, liveSpec as any)).toBe(15)
    expect(pollSecondsFor({ ...local, action: { type: 'dev_run_tests', config: { refresh_interval: 1 } } }, liveSpec as any))
      .toBe(MIN_LOCAL_POLL_SECONDS)
    expect(pollSecondsFor(widget('g', 'gh_widget_ci', { refresh_interval: 1 }) as any)).toBe(MIN_POLL_SECONDS)
  })

  it('polls on the spec interval, merging poll_config without mutating the button', async () => {
    catalog.byActionType = { dev_run_tests: liveSpec }
    const button = { id: 't', action: { type: 'dev_run_tests', config: { watch: false } } }
    await mountHost([button])

    expect(executeButtonAction).toHaveBeenCalledTimes(1)
    expect(executeButtonAction.mock.calls[0][0].action.config).toEqual({ watch: false, op: 'status' })
    expect(button.action.config).toEqual({ watch: false })

    await vi.advanceTimersByTimeAsync(15_500)
    expect(executeButtonAction).toHaveBeenCalledTimes(2)
  })

  it('starts polling once the catalog loads', async () => {
    const button = { id: 't', action: { type: 'dev_run_tests', config: {} } }
    await mountHost([button])
    expect(executeButtonAction).not.toHaveBeenCalled()

    catalog.byActionType = { dev_run_tests: liveSpec }
    await nextTick()
    await vi.advanceTimersByTimeAsync(0)
    expect(executeButtonAction).toHaveBeenCalledTimes(1)
  })
})

describe('useWidgetPolling', () => {
  it('fetches each on-screen widget immediately and paints the result', async () => {
    await mountHost([widget('ci'), widget('prs', 'gh_widget_prs'), widget('vol', 'volume_up')])

    expect(executeButtonAction).toHaveBeenCalledTimes(2)
    expect(markFinished).toHaveBeenCalledTimes(2)
    expect(executeButtonAction.mock.calls.map((c) => c[0].id).sort()).toEqual(['ci', 'prs'])
  })

  it('re-polls at the configured interval, silently', async () => {
    await mountHost([widget('ci', 'gh_widget_ci', { refresh_interval: 60 })])
    executeButtonAction.mockClear()

    await vi.advanceTimersByTimeAsync(59_000)
    expect(executeButtonAction).not.toHaveBeenCalled()
    await vi.advanceTimersByTimeAsync(1_500)
    expect(executeButtonAction).toHaveBeenCalledTimes(1)
    await vi.advanceTimersByTimeAsync(60_000)
    expect(executeButtonAction).toHaveBeenCalledTimes(2)
    expect(notify.success).not.toHaveBeenCalled()
  })

  it('never polls non-widget buttons', async () => {
    await mountHost([widget('vol', 'volume_up')])
    await vi.advanceTimersByTimeAsync(10 * 60_000)

    expect(executeButtonAction).not.toHaveBeenCalled()
  })

  it('starts and stops following the buttons on the current page', async () => {
    await mountHost([widget('a')])
    executeButtonAction.mockClear()

    dashboard.currentPage = { buttons: [widget('b', 'gh_widget_prs')] }
    await nextTick()
    await vi.advanceTimersByTimeAsync(0)
    expect(executeButtonAction.mock.calls.map((c) => c[0].id)).toEqual(['b'])

    executeButtonAction.mockClear()
    await vi.advanceTimersByTimeAsync(61_000)
    expect(executeButtonAction.mock.calls.map((c) => c[0].id)).toEqual(['b']) // 'a' timer is gone
  })

  it('does not poll while editing, and catches up when editing ends', async () => {
    dashboard.isEditMode = true
    await mountHost([widget('ci')])
    expect(executeButtonAction).not.toHaveBeenCalled()

    dashboard.isEditMode = false
    await nextTick()
    await vi.advanceTimersByTimeAsync(0)
    expect(executeButtonAction).toHaveBeenCalledTimes(1)
  })

  it('stops all timers on unmount', async () => {
    await mountHost([widget('ci')])
    wrapper!.unmount()
    wrapper = null
    executeButtonAction.mockClear()

    await vi.advanceTimersByTimeAsync(10 * 60_000)
    expect(executeButtonAction).not.toHaveBeenCalled()
  })

  it('a failed poll leaves the face alone and keeps polling', async () => {
    executeButtonAction.mockRejectedValueOnce(new Error('offline'))
    await mountHost([widget('ci')])
    expect(markFinished).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(61_000)
    expect(markFinished).toHaveBeenCalledTimes(1)
  })

  it('notifies once when CI goes from passing to failing', async () => {
    await mountHost([widget('ci')])            // reading 1: success
    executeButtonAction.mockResolvedValue(ok('critical'))
    await vi.advanceTimersByTimeAsync(61_000)  // reading 2: failure
    await vi.advanceTimersByTimeAsync(61_000)  // reading 3: still failing

    expect(notify.error).toHaveBeenCalledTimes(1)
    expect(notify.error).toHaveBeenCalledWith('CI failed', 'me/app - main', 'https://example.test/run/1')
  })

  it('does not notify for a build that was already failing at startup', async () => {
    executeButtonAction.mockResolvedValue(ok('critical'))
    await mountHost([widget('ci')])
    await vi.advanceTimersByTimeAsync(61_000)

    expect(notify.error).not.toHaveBeenCalled()
  })

  it('does not raise CI notifications for other widgets', async () => {
    await mountHost([widget('prs', 'gh_widget_prs')])
    executeButtonAction.mockResolvedValue(ok('critical'))
    await vi.advanceTimersByTimeAsync(61_000)

    expect(notify.error).not.toHaveBeenCalled()
  })
})
