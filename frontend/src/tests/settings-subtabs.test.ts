// DL-127: Appearance + Integrations sections moved from sidebar sub-nav /
// one-long-scroll to top tabs inside the content header, and the MCP panel
// gained a Help & test modal with a live endpoint self-test.
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/client', () => ({
  default: { post: vi.fn(), get: vi.fn() },
}))
import apiClient from '@/api/client'
import McpInfoModal from '@/components/settings/McpInfoModal.vue'

const view = readFileSync(resolve(__dirname, '../views/SettingsView.vue'), 'utf-8')

describe('top sub-tab bar', () => {
  it('renders a tablist strip between the topbar and content', () => {
    expect(view).toContain('class="subtab-bar"')
    expect(view).toContain('role="tablist"')
    expect(view).toContain('role="tab"')
    expect(view).toContain('aria-selected')
    expect(view).toContain('v-for="sub in subTabsForTab"')
  })

  it('drives appearance subs through the shared selectSubTab', () => {
    expect(view).toContain("activeTab.value === 'appearance' ? appearanceSubs")
    expect(view).toContain("activeTab.value === 'integration' ? integrationSubs")
    expect(view).toContain('function selectSubTab(')
    // The old sidebar nav-sub block is gone.
    expect(view).not.toContain('class="nav-sub"')
    expect(view).not.toContain('selectAppearanceSub')
  })

  it('sections the integration page by integrationSubTab', () => {
    for (const sub of ['apps', 'alerts', 'triggers', 'mcp']) {
      expect(view).toContain(`id: '${sub}'`)
    }
    expect(view).toContain(`v-if="integrationSubTab === 'apps'" class="panel" id="auto-switch"`)
    expect(view).toContain(`v-if="integrationSubTab === 'alerts'" class="panel" id="agent-alerts"`)
    expect(view).toContain(`v-if="integrationSubTab === 'triggers'" class="panel" id="recent-actions"`)
    expect(view).toContain(`v-if="integrationSubTab === 'mcp'" class="panel" id="mcp-server"`)
    expect(view).toContain('<TriggersPanel v-if="integrationSubTab === \'triggers\'" />')
  })

  it('resolves ?sub= against the active tab and keeps per-sub crumbs', () => {
    expect(view).toContain("integrationSubs.some(s => s.id === subQuery)")
    expect(view).toContain("integrationSubTab.value = subQuery as IntegrationSubId")
    expect(view).toContain('`integration/${integrationSubTab.value}`')
    expect(view).toContain("'integration/mcp'")
    expect(view).toContain("'integration/apps'")
  })

  it('routes search hits to the right integration sub-tab', () => {
    expect(view).toContain("tabId: 'integration', subTab: 'mcp'")
    expect(view).toContain("tabId: 'integration', subTab: 'alerts'")
    expect(view).toContain("tabId: 'integration', subTab: 'triggers'")
    expect(view).toContain("tabId: 'integration', subTab: 'apps'")
  })
})

describe('MCP help modal', () => {
  it('is mounted from SettingsView and opened by the panel button', () => {
    expect(view).toContain("import McpInfoModal from '@/components/settings/McpInfoModal.vue'")
    expect(view).toContain('<McpInfoModal v-if="mcpHelpOpen" :endpoint="mcpEndpoint"')
    expect(view).toContain("@click=\"mcpHelpOpen = true\"")
  })
})

describe('McpInfoModal self-test', () => {
  const ENDPOINT = 'http://127.0.0.1:5000/api/mcp'
  const mcpPost = apiClient.post as ReturnType<typeof vi.fn>

  function mountModal() {
    return mount(McpInfoModal, {
      props: { endpoint: ENDPOINT },
      global: { stubs: { FontAwesomeIcon: true } },
    })
  }

  function batchReply(tools = ['press_button', 'deck_info']) {
    return {
      data: [
        { jsonrpc: '2.0', id: 1, result: { serverInfo: { name: 'vdock', version: '1.0.0' } } },
        { jsonrpc: '2.0', id: 2, result: { tools: tools.map((name) => ({ name })) } },
      ],
    }
  }

  beforeEach(() => {
    setActivePinia(createPinia())
    mcpPost.mockReset()
  })

  it('runs initialize + tools/list as one batch against /mcp', async () => {
    mcpPost.mockResolvedValue(batchReply())
    const wrapper = mountModal()
    await wrapper.find('.mcp-test-row .btn.primary').trigger('click')
    await flushPromises()
    expect(mcpPost).toHaveBeenCalledWith('/mcp', [
      { jsonrpc: '2.0', id: 1, method: 'initialize' },
      { jsonrpc: '2.0', id: 2, method: 'tools/list' },
    ])
    expect(wrapper.find('.mcp-test-result.ok').text()).toContain('2 tools')
  })

  it('surfaces a JSON-RPC error as a failure', async () => {
    mcpPost.mockResolvedValue({
      data: [
        { jsonrpc: '2.0', id: 1, error: { code: -32603, message: 'executor not wired' } },
        { jsonrpc: '2.0', id: 2, result: { tools: [{ name: 'x' }] } },
      ],
    })
    const wrapper = mountModal()
    await wrapper.find('.mcp-test-row .btn.primary').trigger('click')
    await flushPromises()
    expect(wrapper.find('.mcp-test-result.fail').text()).toContain('executor not wired')
  })

  it('explains a 503 as the server being disabled', async () => {
    mcpPost.mockRejectedValue({ response: { status: 503 } })
    const wrapper = mountModal()
    await wrapper.find('.mcp-test-row .btn.primary').trigger('click')
    await flushPromises()
    expect(wrapper.find('.mcp-test-result.fail').text()).toContain('disabled')
  })

  it('fails honestly on a malformed response', async () => {
    mcpPost.mockResolvedValue({ data: [{ jsonrpc: '2.0', id: 2, result: { tools: [] } }] })
    const wrapper = mountModal()
    await wrapper.find('.mcp-test-row .btn.primary').trigger('click')
    await flushPromises()
    expect(wrapper.find('.mcp-test-result.fail').text()).toContain('serverInfo')
  })

  it('disables the test while MCP is off', async () => {
    const { useSettingsStore } = await import('@/stores/settings')
    useSettingsStore().mcpEnabled = false
    const wrapper = mountModal()
    const btn = wrapper.find('.mcp-test-row .btn.primary')
    expect(btn.attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('Enable the MCP server toggle first')
  })

  it('embeds the passed endpoint in the client snippets', () => {
    const wrapper = mountModal()
    expect(wrapper.text()).toContain(ENDPOINT)
    expect(wrapper.text()).toContain('mcp-remote')
    expect(wrapper.text()).toContain('press_button')
  })
})
