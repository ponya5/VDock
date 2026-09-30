<script setup lang="ts">
/**
 * DL-127: "Help & test" dialog for the MCP integration — explains what the
 * endpoint exposes, gives copy-paste client configs, and runs a live
 * self-test ([initialize, tools/list] batch) against the real endpoint.
 */
import { computed, ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import apiClient from '@/api/client'
import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'

const props = defineProps<{ endpoint: string }>()
const emit = defineEmits<{ (e: 'close'): void }>()
const notifications = useNotificationsStore()
const settingsStore = useSettingsStore()

const TOOL_GROUPS = [
  {
    name: 'Control the deck',
    tools: 'press_button · run_action · switch_scene · show_notification',
  },
  {
    name: 'Read state',
    tools: 'deck_info · list_scenes · list_buttons · get_volume · get_now_playing · get_agent_states',
  },
  {
    name: 'Change state',
    tools: 'set_volume',
  },
]

const cursorConfig = computed(() =>
  JSON.stringify({ mcpServers: { vdock: { url: props.endpoint } } }, null, 2)
)
const claudeConfig = computed(() =>
  JSON.stringify(
    { mcpServers: { vdock: { command: 'npx', args: ['-y', 'mcp-remote', props.endpoint] } } },
    null,
    2
  )
)
const curlProbe = computed(
  () =>
    `curl -s ${props.endpoint} -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"initialize"}'`
)

async function copySnippet(text: string, label: string) {
  try {
    await navigator.clipboard.writeText(text)
    notifications.success('Copied', `${label} is on the clipboard.`)
  } catch {
    notifications.error('Copy failed', 'Clipboard access was denied — select the text and copy it manually.')
  }
}

// --- Self-test ---------------------------------------------------------------
// One batch: initialize proves the transport, tools/list proves discovery.
// Goes through apiClient so it exercises the same auth path agents would.
interface McpTestResult { ok: boolean; detail: string }
const testing = ref(false)
const testResult = ref<McpTestResult | null>(null)

async function runSelfTest() {
  if (testing.value) return
  testing.value = true
  testResult.value = null
  const started = performance.now()
  try {
    const { data } = await apiClient.post('/mcp', [
      { jsonrpc: '2.0', id: 1, method: 'initialize' },
      { jsonrpc: '2.0', id: 2, method: 'tools/list' },
    ])
    const ms = Math.round(performance.now() - started)
    const replies = Array.isArray(data) ? data : [data]
    const initReply = replies.find((m: any) => m?.id === 1)
    const toolsReply = replies.find((m: any) => m?.id === 2)
    const rpcError =
      [initReply, toolsReply].map((m: any) => m?.error?.message).find(Boolean) ||
      (replies.length === 0 ? 'Empty response — the server returned no JSON-RPC replies.' : '')
    if (rpcError) {
      testResult.value = { ok: false, detail: rpcError }
      return
    }
    const tools = toolsReply?.result?.tools
    const names = Array.isArray(tools) ? tools.map((t: any) => t?.name).filter(Boolean) : []
    if (!initReply?.result?.serverInfo) {
      testResult.value = { ok: false, detail: 'Malformed response — initialize returned no serverInfo.' }
    } else if (!names.length) {
      testResult.value = { ok: false, detail: 'Server answered but reported no tools.' }
    } else {
      testResult.value = {
        ok: true,
        detail: `Connected — ${initReply.result.serverInfo.name} ${initReply.result.serverInfo.version}, ${names.length} tools in ${ms} ms.`,
      }
    }
  } catch (e: any) {
    const status = e?.response?.status
    const serverMsg = e?.response?.data?.error || e?.response?.data?.message
    testResult.value = {
      ok: false,
      detail:
        status === 503 ? 'The server reports MCP is disabled — enable the toggle first.'
        : status === 401 ? 'Authentication required — the deck is locked.'
        : serverMsg || (status ? `Endpoint answered HTTP ${status}.` : 'Endpoint unreachable — is the backend running?'),
    }
  } finally {
    testing.value = false
  }
}
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal mcp-info" role="dialog" aria-modal="true" aria-label="MCP server help">
      <div class="modal-header">
        <h2><FontAwesomeIcon :icon="['fas', 'robot']" /> MCP server — what this is</h2>
        <button type="button" class="close-btn" aria-label="Close" @click="emit('close')">
          <FontAwesomeIcon :icon="['fas', 'times']" />
        </button>
      </div>

      <div class="mcp-body">
        <p class="mcp-lead">
          <strong>Model Context Protocol</strong> is the standard AI agents use to call tools.
          With this enabled, VDock itself becomes a local tool server — agents like Cursor or
          Claude Desktop can press deck buttons, switch scenes, push notifications and read
          what's playing, straight from a chat.
        </p>

        <section class="mcp-section">
          <h3>Capabilities</h3>
          <div v-for="group in TOOL_GROUPS" :key="group.name" class="mcp-group">
            <span class="mcp-group-name">{{ group.name }}</span>
            <code class="mcp-tools">{{ group.tools }}</code>
          </div>
        </section>

        <section class="mcp-section">
          <h3>Connect a client</h3>
          <div class="mcp-snippet-block">
            <div class="mcp-snippet-head">
              <span>Cursor — <code class="mcp-inline">.cursor/mcp.json</code></span>
              <button type="button" class="btn quiet sm" @click="copySnippet(cursorConfig, 'Cursor config')">
                <FontAwesomeIcon :icon="['fas', 'copy']" /> Copy
              </button>
            </div>
            <pre class="mcp-pre">{{ cursorConfig }}</pre>
          </div>
          <div class="mcp-snippet-block">
            <div class="mcp-snippet-head">
              <span>Claude Desktop — <code class="mcp-inline">claude_desktop_config.json</code> (via <code class="mcp-inline">mcp-remote</code>)</span>
              <button type="button" class="btn quiet sm" @click="copySnippet(claudeConfig, 'Claude Desktop config')">
                <FontAwesomeIcon :icon="['fas', 'copy']" /> Copy
              </button>
            </div>
            <pre class="mcp-pre">{{ claudeConfig }}</pre>
          </div>
          <div class="mcp-snippet-block">
            <div class="mcp-snippet-head">
              <span>Raw check (curl)</span>
              <button type="button" class="btn quiet sm" @click="copySnippet(curlProbe, 'curl command')">
                <FontAwesomeIcon :icon="['fas', 'copy']" /> Copy
              </button>
            </div>
            <pre class="mcp-pre">{{ curlProbe }}</pre>
          </div>
        </section>

        <section class="mcp-section">
          <h3>Access &amp; limits</h3>
          <ul class="mcp-notes">
            <li>HTTP POST, JSON-RPC 2.0 — single messages and batches.</li>
            <li>Localhost only by default; with password protection on, remote clients authenticate with a Bearer token.</li>
            <li>No SSE push channel — the server answers requests, it doesn't stream notifications.</li>
            <li>Full details in <code class="mcp-inline">docs/mcp.md</code>.</li>
          </ul>
        </section>

        <section class="mcp-section mcp-test">
          <h3>Self-test</h3>
          <div class="mcp-test-row">
            <button
              type="button"
              class="btn primary sm"
              :disabled="testing || !settingsStore.mcpEnabled"
              @click="runSelfTest"
            >
              <FontAwesomeIcon :icon="['fas', testing ? 'spinner' : 'stethoscope']" :spin="testing" />
              {{ testing ? 'Testing…' : 'Run self-test' }}
            </button>
            <span v-if="!settingsStore.mcpEnabled" class="mcp-test-note">Enable the MCP server toggle first.</span>
            <span
              v-else-if="testResult"
              class="mcp-test-result"
              :class="testResult.ok ? 'ok' : 'fail'"
            >
              <FontAwesomeIcon :icon="['fas', testResult.ok ? 'circle-check' : 'circle-exclamation']" />
              {{ testResult.detail }}
            </span>
          </div>
        </section>
      </div>

      <div class="mcp-actions">
        <button type="button" class="btn secondary" @click="emit('close')">Close</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mcp-info {
  width: 620px;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
}

.modal-header h2 {
  margin: 0;
  font-size: clamp(16px, 1.2vw + 12px, 20px);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.close-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  min-height: 36px;
  padding: 0;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text);
}

.mcp-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.mcp-lead {
  margin: 0;
  font-size: 0.88rem;
  line-height: 1.5;
  color: var(--color-text-secondary);
}

.mcp-lead strong { color: var(--color-text); }

.mcp-section h3 {
  margin: 0 0 var(--spacing-sm);
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-secondary);
}

.mcp-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 6px 0;
}

.mcp-group + .mcp-group { border-top: 1px solid var(--color-border); }

.mcp-group-name {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-text);
}

.mcp-tools {
  font-family: var(--mono, monospace);
  font-size: 0.72rem;
  color: var(--color-text-secondary);
}

.mcp-snippet-block {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.mcp-snippet-block + .mcp-snippet-block { margin-top: var(--spacing-sm); }

.mcp-snippet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: 6px 10px;
  font-size: 0.78rem;
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border);
}

.mcp-pre {
  margin: 0;
  padding: 10px 12px;
  font-family: var(--mono, monospace);
  font-size: 0.72rem;
  line-height: 1.5;
  color: var(--color-text);
  white-space: pre-wrap;
  word-break: break-all;
  user-select: text;
}

.mcp-inline {
  font-family: var(--mono, monospace);
  font-size: 0.72rem;
  color: var(--color-text);
}

.mcp-notes {
  margin: 0;
  padding-left: 18px;
  font-size: 0.82rem;
  line-height: 1.6;
  color: var(--color-text-secondary);
}

.mcp-test-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.mcp-test-note {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.mcp-test-result {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.82rem;
}

.mcp-test-result.ok { color: #34d399; }
.mcp-test-result.fail { color: #f87171; }

.mcp-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--spacing-lg);
}

@media (max-width: 680px) {
  .mcp-info { width: 92vw; }
}
</style>
