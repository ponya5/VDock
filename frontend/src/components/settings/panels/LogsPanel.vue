<template>
  <div class="content">
    <div class="col">
      <section class="panel">
        <div class="panel-head">
          <h2>Session logs</h2>
          <span class="hint">Rotating session, launcher, and touchscreen events · {{ formatBytes(logsTotalBytes) }} used</span>
        </div>
        <div class="panel-body flush">
          <div class="logs-layout">
            <section class="logs-files-card">
              <h2><FontAwesomeIcon :icon="['fas', 'folder-open']" /> Log Files</h2>
              <div class="log-file-list">
                <button
                  v-for="file in logFiles"
                  :key="file.name"
                  type="button"
                  :class="['log-file-row', { active: selectedLog === file.name }]"
                  @click="selectLog(file.name)"
                >
                  <FontAwesomeIcon :icon="['fas', 'file-lines']" class="log-file-icon" />
                  <span class="log-file-name">{{ file.name }}</span>
                  <span class="log-file-meta">{{ formatBytes(file.size) }}</span>
                </button>
                <p v-if="!logFiles.length" class="form-help">No log files yet — they appear once the app writes events.</p>
              </div>
              <div class="logs-files-footer">
                {{ logFiles.length }} file{{ logFiles.length === 1 ? '' : 's' }} · {{ formatBytes(logsTotalBytes) }}
              </div>
            </section>

            <section class="logs-viewer-card">
              <div class="log-toolbar">
                <div class="log-toolbar-file">
                  <FontAwesomeIcon :icon="['fas', 'terminal']" class="log-toolbar-icon" />
                  <span class="log-toolbar-name">{{ selectedLog || 'Viewer' }}</span>
                  <span v-if="selectedLogFileSize !== null" class="log-size-badge">{{ formatBytes(selectedLogFileSize) }}</span>
                </div>
                <div class="log-toolbar-actions">
                  <label class="log-tail-label">
                    Tail
                    <select v-model.number="logTailCount" class="select log-tail-select" :disabled="!selectedLog" @change="refreshTail">
                      <option :value="100">100</option>
                      <option :value="300">300</option>
                      <option :value="1000">1000</option>
                    </select>
                  </label>
                  <span class="log-toolbar-divider"></span>
                  <button class="btn sm" :disabled="loadingLogs" title="Reload log list and tail" @click="refreshAll">
                    <FontAwesomeIcon :icon="['fas', loadingLogs ? 'spinner' : 'arrows-rotate']" :spin="loadingLogs" /> Refresh
                  </button>
                  <button class="btn sm" :disabled="exportingLogs || !logFiles.length" title="Download all logs as a zip" @click="exportLogs">
                    <FontAwesomeIcon :icon="['fas', exportingLogs ? 'spinner' : 'file-export']" :spin="exportingLogs" />
                    {{ exportingLogs ? 'Exporting…' : 'Export' }}
                  </button>
                  <button class="btn danger sm" :disabled="!logFiles.length" title="Empty every log file" @click="clearLogs">
                    <FontAwesomeIcon :icon="['fas', 'trash']" /> Clear All
                  </button>
                </div>
              </div>
              <div v-if="selectedLog" class="log-search-row">
                <FontAwesomeIcon :icon="['fas', 'magnifying-glass']" class="log-search-icon" />
                <input
                  v-model="logSearch"
                  type="text"
                  class="input log-search-input"
                  placeholder="Search the tail… try level:error"
                  aria-label="Search log lines"
                  @keydown.esc="logSearch = ''"
                />
                <span v-if="logQuery" class="log-search-count">{{ displayedLogLines.length }} of {{ logLines.length }}</span>
                <button v-if="logQuery" type="button" class="log-search-clear" title="Clear search" aria-label="Clear log search" @click="logSearch = ''">
                  <FontAwesomeIcon :icon="['fas', 'xmark']" />
                </button>
              </div>
              <div ref="logViewerEl" class="log-viewer">
                <template v-if="displayedLogLines.length">
                  <div v-for="(line, i) in displayedLogLines" :key="i" class="log-line" :class="logLineClass(line)"><span v-for="(part, j) in logLineParts(line)" :key="j" :class="{ 'log-hit': part.hit }">{{ part.text }}</span></div>
                </template>
                <p v-else class="form-help">{{ selectedLog ? (logQuery ? 'No lines match — widen the tail or clear the search.' : 'This log is empty.') : 'Pick a log file on the left to view its tail.' }}</p>
              </div>
              <div class="log-statusbar">
                <span>{{ selectedLog ? (logQuery ? `${displayedLogLines.length} of ${logLines.length} lines match` : `${logLines.length} lines shown`) : 'No file selected' }}</span>
                <span v-if="logsUpdatedAt">Updated {{ logsUpdatedAt }}</span>
              </div>
            </section>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref, nextTick } from 'vue'
import { useNotificationsStore } from '@/stores/notifications'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import apiClient from '@/api/client'
import { confirmDialog } from '@/composables/useConfirm'

const notificationsStore = useNotificationsStore()

// ── Session Logs tab (DL-029) ──
interface LogFileEntry { name: string; size: number; mtime: string }
const logFiles = ref<LogFileEntry[]>([])
const logsTotalBytes = ref(0)
const selectedLog = ref('')
const logLines = ref<string[]>([])
const logTailCount = ref(300)
const loadingLogs = ref(false)
const exportingLogs = ref(false)
const logsUpdatedAt = ref('')
const logViewerEl = ref<HTMLElement | null>(null)

const selectedLogFileSize = computed(() => {
  const file = logFiles.value.find(f => f.name === selectedLog.value)
  return file ? file.size : null
})

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function logLineClass(line: string) {
  if (/ - (ERROR|CRITICAL) /.test(line)) return 'log-error'
  if (/ - (WARNING|WARN) /.test(line)) return 'log-warn'
  return ''
}

const logSearch = ref('')
const logQuery = computed(() => logSearch.value.trim())

// "level:err|warn|info|critical" prefixes filter by logLineClass; any text
// after the prefix still substring-matches, so `level:error upload` works.
const LOG_LEVEL_RE = /^level:(error|err|warn|warning|info|critical)\b\s*(.*)$/i

function logLineLevel(line: string): 'error' | 'warn' | 'info' {
  const cls = logLineClass(line)
  if (cls === 'log-error') return 'error'
  if (cls === 'log-warn') return 'warn'
  return 'info'
}

const displayedLogLines = computed(() => {
  const q = logQuery.value
  if (!q) return logLines.value
  const levelMatch = q.match(LOG_LEVEL_RE)
  const needle = (levelMatch ? levelMatch[2] : q).toLowerCase()
  return logLines.value.filter(line => {
    if (levelMatch) {
      const lvl = levelMatch[1].toLowerCase()
      const want = lvl === 'err' ? 'error' : lvl === 'warning' ? 'warn' : lvl
      if (logLineLevel(line) !== want) return false
    }
    return !needle || line.toLowerCase().includes(needle)
  })
})

// Split a line into matched/unmatched segments — rendered as spans, so
// arbitrary log text never goes through v-html.
function logLineParts(line: string): { text: string; hit: boolean }[] {
  const levelMatch = logQuery.value.match(LOG_LEVEL_RE)
  const needle = (levelMatch ? levelMatch[2] : logQuery.value).toLowerCase()
  if (!needle) return [{ text: line, hit: false }]
  const parts: { text: string; hit: boolean }[] = []
  const lower = line.toLowerCase()
  let i = 0
  let idx = lower.indexOf(needle)
  while (idx !== -1) {
    if (idx > i) parts.push({ text: line.slice(i, idx), hit: false })
    parts.push({ text: line.slice(idx, idx + needle.length), hit: true })
    i = idx + needle.length
    idx = lower.indexOf(needle, i)
  }
  if (i < line.length) parts.push({ text: line.slice(i), hit: false })
  return parts.length ? parts : [{ text: line, hit: false }]
}

async function loadLogs() {
  loadingLogs.value = true
  try {
    const { data } = await apiClient.get('/logs')
    logFiles.value = data.logs ?? []
    logsTotalBytes.value = data.total_bytes ?? 0
    if (!selectedLog.value && logFiles.value.length) {
      await selectLog(logFiles.value[0].name)
    }
  } catch (err: any) {
    notificationsStore.error('Logs unavailable', err?.response?.data?.message || err?.message || 'Could not load log files.')
  } finally {
    loadingLogs.value = false
  }
}

async function selectLog(name: string) {
  selectedLog.value = name
  await refreshTail()
}

async function refreshTail() {
  if (!selectedLog.value) return
  try {
    const { data } = await apiClient.get(`/logs/${encodeURIComponent(selectedLog.value)}`, {
      tail: logTailCount.value
    })
    logLines.value = data.lines ?? []
    logsUpdatedAt.value = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    await nextTick()
    if (logViewerEl.value) logViewerEl.value.scrollTop = logViewerEl.value.scrollHeight
  } catch {
    logLines.value = []
  }
}

function refreshAll() {
  void loadLogs()
  void refreshTail()
}

async function exportLogs() {
  exportingLogs.value = true
  try {
    const response = await fetch('/api/logs/export')
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `vdock-logs-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.zip`
    anchor.click()
    URL.revokeObjectURL(url)
    notificationsStore.success('Logs exported', 'A zip with every log file was downloaded.')
  } catch (err: any) {
    notificationsStore.error('Export failed', err?.message || 'Could not export logs.')
  } finally {
    exportingLogs.value = false
  }
}

async function clearLogs() {
  const ok = await confirmDialog({
    title: 'Clear all logs?',
    message: 'Every session log file will be emptied. This cannot be undone.',
    confirmLabel: 'Clear',
    danger: true
  })
  if (!ok) return
  try {
    await apiClient.delete('/logs')
    logLines.value = []
    await loadLogs()
    notificationsStore.success('Logs cleared', 'All log files were emptied.')
  } catch (err: any) {
    notificationsStore.error('Clear failed', err?.message || 'Could not clear logs.')
  }
}

onMounted(loadLogs)
</script>

<style scoped>
.form-help {
  font-size: clamp(11px, 0.6vw + 8px, 13px);
  color: var(--color-text-secondary);
  margin: var(--spacing-xs) 0 0 0;
}
.logs-layout {
  display: flex;
  gap: var(--spacing-md);
  align-items: stretch;
  /* 100vh − settings header (72) − content padding (40) − compact page
     header (~33) — fills exactly, no scroll. */
  height: calc(100vh - 215px);
  min-height: 380px;
}
.logs-files-card {
  width: clamp(210px, 24vw, 270px);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 12px;
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
}
.logs-files-card > h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  padding: 2px 4px 10px;
  font-size: clamp(12px, 0.7vw + 9px, 14px);
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--color-text-secondary);
}
.logs-viewer-card {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  /* Tighter than the default card padding — every px goes to the tail. */
  padding: 12px 14px;
}
.log-file-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
.logs-files-footer {
  margin-top: var(--spacing-sm);
  padding-top: var(--spacing-sm);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  font-size: clamp(11px, 0.6vw + 8px, 13px);
  color: var(--color-text-secondary);
  font-variant-numeric: tabular-nums;
}
.log-file-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  min-height: 44px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(255, 255, 255, 0.04);
  color: var(--color-text);
  cursor: pointer;
  text-align: left;
  font-size: clamp(12px, 0.7vw + 9px, 14px);
  touch-action: manipulation;
  transition: background var(--transition-fast), border-color var(--transition-fast);
}
@media (hover: hover) and (pointer: fine) {
  .log-file-row:hover { background: rgba(255, 255, 255, 0.08); }
  .log-search-clear:hover {
    background: rgba(255, 255, 255, 0.08);
    color: var(--color-text);
  }
}
.log-file-row:active { background: rgba(255, 255, 255, 0.05); }
.log-file-row.active {
  border-color: var(--color-accent, #4aa3ff);
  background: color-mix(in srgb, var(--color-accent, #4aa3ff) 14%, transparent);
}
.log-file-icon {
  color: var(--color-text-secondary);
  flex-shrink: 0;
}
.log-file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: 'Consolas', 'Courier New', monospace;
}
.log-file-meta {
  color: var(--color-text-secondary);
  font-size: 0.85em;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 999px;
  padding: 2px 8px;
}
.log-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  flex-wrap: nowrap;
  padding-bottom: 8px;
  margin-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.log-toolbar-file {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  /* Never fully collapse — keep at least an icon + a sliver of name. */
  min-width: 70px;
}
.log-toolbar-icon { color: var(--color-text-secondary); }
.log-toolbar-name {
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: clamp(13px, 0.8vw + 9px, 15px);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.log-size-badge {
  font-size: clamp(10px, 0.5vw + 8px, 12px);
  color: var(--color-text-secondary);
  background: rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  padding: 2px 8px;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}
.log-toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.log-toolbar-actions .btn {
  white-space: nowrap;
  /* Compact diagnostic controls — don't let touch-mode min-height inflate
     the toolbar into stealing tail space on the 600px panel. */
  min-height: 34px;
  padding: 4px 10px;
}
.log-toolbar-divider {
  width: 1px;
  height: 20px;
  background: rgba(255, 255, 255, 0.12);
}
.log-tail-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: clamp(11px, 0.6vw + 8px, 13px);
  color: var(--color-text-secondary);
}
.log-tail-select {
  width: auto;
  min-width: 76px;
  padding: 4px 8px;
}
.log-search-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 0 2px;
}
.log-search-icon {
  color: var(--color-text-secondary);
  flex-shrink: 0;
  font-size: 0.9em;
}
.log-search-input {
  flex: 1;
  min-width: 0;
  min-height: 32px;
  padding: 4px 10px;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: clamp(11px, 0.6vw + 8px, 13px);
}
.log-search-count {
  font-size: clamp(10px, 0.5vw + 8px, 12px);
  color: var(--color-text-secondary);
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}
.log-search-clear {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  flex-shrink: 0;
}
.log-hit {
  background: color-mix(in srgb, var(--color-accent, #4aa3ff) 38%, transparent);
  color: var(--color-text);
  border-radius: 3px;
  padding: 0 1px;
}
.log-viewer {
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 10px 12px;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: clamp(11px, 0.6vw + 8px, 13px);
  line-height: 1.55;
}
.log-line {
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--color-text-secondary);
}
.log-statusbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding-top: 8px;
  margin-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  font-size: clamp(10px, 0.5vw + 8px, 12px);
  color: var(--color-text-secondary);
  font-variant-numeric: tabular-nums;
}
.log-file-row {
  touch-action: manipulation; }
@media (max-width: 880px) {
  .logs-layout {
    flex-direction: column;
    height: auto;
  }
  .logs-files-card { width: 100%; }
  .log-viewer { height: 46vh; }
}
</style>
