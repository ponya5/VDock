// Accounts & keys: the per-key "Test" button runs a real check and shows the verdict.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { ref } from 'vue'

const apiPost = vi.fn()
const apiGet = vi.fn()

vi.mock('@/api/client', () => ({
  default: {
    get: (...a: unknown[]) => apiGet(...a),
    post: (...a: unknown[]) => apiPost(...a),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))
const toast = { success: vi.fn(), info: vi.fn(), error: vi.fn() }
vi.mock('@/stores/notifications', () => ({ useNotificationsStore: () => toast }))

const scenes = ref<Array<{ id: string }>>([])
const addScene = vi.fn((scene: { id: string }) => { scenes.value = [...scenes.value, scene] })
const hasProfile = { value: true }
vi.mock('@/stores/dashboard', () => ({
  useDashboardStore: () => ({
    get currentProfile() { return hasProfile.value ? { scenes: scenes.value } : null },
    addScene,
  }),
}))
vi.mock('@/utils/copyText', () => ({ copyText: vi.fn(async () => true) }))

const items = ref([
  { id: 'GITHUB_TOKEN', label: 'GitHub token', kind: 'secret', configured: true, reason: '', help_url: 'https://x', unlocks: 'Live PR' },
  { id: 'ANTHROPIC_API_KEY', label: 'Anthropic API key', kind: 'secret', configured: false, reason: 'missing', help_url: 'https://x', unlocks: 'Claude' },
  { id: 'WEATHERAPI_KEY', label: 'WeatherAPI key', kind: 'secret', configured: false, builtin: true, builtin_label: 'Built-in (Open-Meteo)', reason: '', help_url: 'https://x', unlocks: 'Weather' },
])
vi.mock('@/composables/useSetupStatus', () => ({
  useSetupStatus: () => ({
    secrets: items,
    tools: ref([]),
    envFile: ref('backend/.env'),
    refresh: vi.fn(async () => {}),
  }),
}))

import AccountsPanel from '@/components/settings/panels/AccountsPanel.vue'

const mountPanel = () => mount(AccountsPanel, { global: { stubs: { FontAwesomeIcon: true } } })
const row = (w: ReturnType<typeof mountPanel>, id: string) => w.find(`[data-key="${id}"]`)

beforeEach(() => {
  apiPost.mockReset(); apiGet.mockReset(); addScene.mockClear()
  Object.values(toast).forEach((f) => f.mockClear())
  scenes.value = []; hasProfile.value = true
})

describe('Accounts & keys → Test', () => {
  it('only offers Test for keys that are set (or built in), not missing ones', () => {
    const w = mountPanel()
    expect(row(w, 'GITHUB_TOKEN').find('[data-action="test"]').exists()).toBe(true)
    expect(row(w, 'WEATHERAPI_KEY').find('[data-action="test"]').exists()).toBe(true)
    expect(row(w, 'ANTHROPIC_API_KEY').find('[data-action="test"]').exists()).toBe(false)
  })

  it('shows a green verdict with the account for a valid key', async () => {
    apiPost.mockResolvedValue({ data: { ok: true, status: 'valid', message: 'Valid - signed in as octocat.' } })
    const w = mountPanel()
    await row(w, 'GITHUB_TOKEN').find('[data-action="test"]').trigger('click')
    await flushPromises()
    expect(apiPost).toHaveBeenCalledWith('/config/integrations/GITHUB_TOKEN/test')
    const result = row(w, 'GITHUB_TOKEN').find('[data-testid="key-test-result"]')
    expect(result.text()).toContain('signed in as octocat')
    expect(result.classes()).toContain('is-ok')
  })

  it('shows a red verdict for a rejected key', async () => {
    apiPost.mockResolvedValue({ data: { ok: false, status: 'invalid', message: 'GitHub rejected this token.' } })
    const w = mountPanel()
    await row(w, 'GITHUB_TOKEN').find('[data-action="test"]').trigger('click')
    await flushPromises()
    const result = row(w, 'GITHUB_TOKEN').find('[data-testid="key-test-result"]')
    expect(result.text()).toContain('rejected')
    expect(result.classes()).toContain('is-bad')
  })

  it('reports a failed request instead of hanging', async () => {
    apiPost.mockRejectedValue({ response: { data: { error: 'Keys can only be tested from the PC VDock runs on.' } } })
    const w = mountPanel()
    await row(w, 'GITHUB_TOKEN').find('[data-action="test"]').trigger('click')
    await flushPromises()
    expect(row(w, 'GITHUB_TOKEN').find('[data-testid="key-test-result"]').text()).toContain('only be tested from the PC')
  })
})

describe('Accounts & keys → Test against an older backend', () => {
  it.each([404, 405])('explains a %i by asking for a restart', async (status) => {
    apiPost.mockRejectedValue({ response: { status, data: {} } })
    const w = mountPanel()
    await row(w, 'GITHUB_TOKEN').find('[data-action="test"]').trigger('click')
    await flushPromises()
    const result = row(w, 'GITHUB_TOKEN').find('[data-testid="key-test-result"]')
    expect(result.text()).toContain('Restart VDock')
    expect(result.classes()).toContain('is-bad')
  })
})

describe('Accounts & keys → "?" guide and starter scene', () => {
  it('opens a guide with setup steps and a recommendation', async () => {
    const w = mountPanel()
    expect(row(w, 'GITHUB_TOKEN').find('[data-testid="key-guide"]').exists()).toBe(false)
    await row(w, 'GITHUB_TOKEN').find('[data-action="help"]').trigger('click')
    const guide = row(w, 'GITHUB_TOKEN').find('[data-testid="key-guide"]')
    expect(guide.text()).toContain('Set it up')
    expect(guide.text()).toContain('Recommendation')
    expect(guide.text()).toContain('gh auth login') // the "you may not need a token" advice
    await row(w, 'GITHUB_TOKEN').find('[data-action="help"]').trigger('click')
    expect(row(w, 'GITHUB_TOKEN').find('[data-testid="key-guide"]').exists()).toBe(false)
  })

  it('every key row has a "?" guide', () => {
    const w = mountPanel()
    for (const id of ['GITHUB_TOKEN', 'ANTHROPIC_API_KEY', 'WEATHERAPI_KEY']) {
      expect(row(w, id).find('[data-action="help"]').exists()).toBe(true)
    }
  })

  it('offers the scene only once a key is set, and adds it with the real GitHub actions', async () => {
    const w = mountPanel()
    expect(row(w, 'ANTHROPIC_API_KEY').find('[data-action="add-scene"]').exists()).toBe(false)
    const btn = row(w, 'GITHUB_TOKEN').find('[data-action="add-scene"]')
    expect(btn.text()).toContain('Add GitHub scene')
    await btn.trigger('click')

    expect(addScene).toHaveBeenCalledTimes(1)
    const scene = addScene.mock.calls[0][0] as any
    expect(scene.id).toBe('integration-scene:integration-github')
    const types = scene.pages[0].buttons.map((b: any) => b.action.type)
    expect(types).toEqual(expect.arrayContaining([
      'gh_widget_prs', 'gh_widget_ci', 'gh_widget_notifications', 'gh_pr_list', 'gh_pr_checks', 'gh_run_list',
    ]))
    expect(toast.success).toHaveBeenCalled()
    // ...and the button now reads as done and cannot add a duplicate.
    const after = row(w, 'GITHUB_TOKEN').find('[data-action="add-scene"]')
    expect(after.text()).toContain('Scene added')
    expect(after.attributes('disabled')).toBeDefined()
  })

  it('built-in weather also gets a scene (works without a key)', async () => {
    const w = mountPanel()
    await row(w, 'WEATHERAPI_KEY').find('[data-action="add-scene"]').trigger('click')
    const scene = addScene.mock.calls[0][0] as any
    expect(scene.pages[0].buttons.every((b: any) => b.action.type === 'weather')).toBe(true)
  })

  it('offers the scene right after saving a key, and "Not now" dismisses it', async () => {
    const w = mountPanel()
    await row(w, 'GITHUB_TOKEN').find('[data-action="set"]').trigger('click')
    await w.find('input.key-input').setValue('ghp_newtoken123')
    await w.find('form.key-edit').trigger('submit')
    await flushPromises()
    expect(row(w, 'GITHUB_TOKEN').find('[data-testid="scene-offer"]').exists()).toBe(true)
    await row(w, 'GITHUB_TOKEN').find('[data-action="offer-skip"]').trigger('click')
    expect(row(w, 'GITHUB_TOKEN').find('[data-testid="scene-offer"]').exists()).toBe(false)
    expect(addScene).not.toHaveBeenCalled()
  })

  it('accepting the offer adds the scene', async () => {
    const w = mountPanel()
    await row(w, 'GITHUB_TOKEN').find('[data-action="set"]').trigger('click')
    await w.find('input.key-input').setValue('ghp_newtoken123')
    await w.find('form.key-edit').trigger('submit')
    await flushPromises()
    await row(w, 'GITHUB_TOKEN').find('[data-action="offer-add"]').trigger('click')
    expect(addScene).toHaveBeenCalledTimes(1)
  })

  it('explains instead of failing when no profile is loaded', async () => {
    hasProfile.value = false
    const w = mountPanel()
    await row(w, 'GITHUB_TOKEN').find('[data-action="add-scene"]').trigger('click')
    expect(addScene).not.toHaveBeenCalled()
    expect(toast.error).toHaveBeenCalled()
  })
})
