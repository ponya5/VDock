<template>
  <section class="panel" id="mcp-server">
    <div class="panel-head">
      <h2>MCP server</h2>
      <span class="hint">Let local agents act on the deck.</span>
      <span class="spacer"></span>
      <button
        type="button"
        class="btn ghost sm"
        title="What MCP exposes, how to connect a client, and a self-test"
        @click="$emit('show-help')"
      >
        <FontAwesomeIcon :icon="['fas', 'circle-question']" /> Help &amp; test
      </button>
    </div>
    <div class="panel-body">
      <div class="row">
        <div class="row-text">
          <span class="label">Enable MCP server</span>
          <p>When off, the endpoint below answers "disabled" — nothing on this machine can drive the deck through it.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Enable MCP server</span><input type="checkbox" :checked="settingsStore.mcpEnabled" @change="toggleMcpEnabled" /><span class="track"></span></label>
        </div>
      </div>
      <div class="row" v-if="settingsStore.mcpEnabled">
        <div class="row-text">
          <span class="label">Endpoint</span>
          <p>Agents on this machine can press buttons, switch scenes, post notifications and read state. Point an MCP client at:</p>
        </div>
        <div class="row-control">
          <code class="kv-code">{{ mcpEndpoint }}</code>
        </div>
      </div>
      <div class="row" v-if="settingsStore.mcpEnabled">
        <div class="row-text">
          <span class="label">Tools</span>
          <p>press_button, run_action, switch_scene, show_notification, get/set_volume, get_now_playing, get_agent_states, list_scenes, list_buttons, deck_info. Localhost-only (or Bearer auth when password protection is on). Setup: <code class="kv-code">docs/mcp.md</code>.</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useSettingsStore } from '@/stores/settings'
import { useServerConfig } from '@/composables/useServerConfig'

defineEmits<{ (e: 'show-help'): void }>()

const settingsStore = useSettingsStore()
const { mcpEndpoint } = useServerConfig()

function toggleMcpEnabled() {
  settingsStore.mcpEnabled = !settingsStore.mcpEnabled
}
</script>


