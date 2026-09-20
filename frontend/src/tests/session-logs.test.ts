// DL-029: Session Logs settings tab — bounded log storage (rotating backend
// handler + launcher truncation), client event capture, tail viewer, zip
// export, and clear-all.
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(__dirname, '..', '..', '..')
const logsRoute = readFileSync(resolve(root, 'backend/routes/logs.py'), 'utf-8')
const loggerUtil = readFileSync(resolve(root, 'backend/utils/logger.py'), 'utf-8')
const launcher = readFileSync(resolve(root, 'scripts/VDock-Launcher.py'), 'utf-8')
const appPy = readFileSync(resolve(root, 'backend/app.py'), 'utf-8')
const sessionLog = readFileSync(resolve(__dirname, '../services/sessionLog.ts'), 'utf-8')
const mainTs = readFileSync(resolve(__dirname, '../main.ts'), 'utf-8')
const settingsView = readFileSync(resolve(__dirname, '../views/SettingsView.vue'), 'utf-8')

describe('bounded log storage', () => {
  it('rotates the app log via RotatingFileHandler', () => {
    expect(loggerUtil).toContain('RotatingFileHandler')
    expect(loggerUtil).toContain('LOG_MAX_BYTES')
    expect(loggerUtil).toContain('LOG_BACKUP_COUNT')
  })

  it('truncates oversized launcher logs before appending', () => {
    expect(launcher).toContain('LAUNCHER_LOG_MAX_BYTES')
    expect(launcher).toContain('_truncate_oversized_log')
  })

  it('registers the logs blueprint and exempts it from rate limits', () => {
    expect(appPy).toContain('logs_bp')
    expect(appPy).toContain('limiter.exempt(logs_bp)')
  })
})

describe('logs API', () => {
  it('lists, tails, exports, and clears logs', () => {
    expect(logsRoute).toContain("route('/api/logs', methods=['GET'])")
    expect(logsRoute).toContain("route('/api/logs/<name>', methods=['GET'])")
    expect(logsRoute).toContain("route('/api/logs/export', methods=['GET'])")
    expect(logsRoute).toContain("route('/api/logs', methods=['DELETE'])")
    expect(logsRoute).toContain("route('/api/logs/client', methods=['POST'])")
  })

  it('rejects path traversal via a strict log-name regex', () => {
    expect(logsRoute).toContain('LOG_NAME_RE')
    expect(logsRoute).toContain("r'^[A-Za-z0-9][A-Za-z0-9_.\\-]*\\.log$'")
  })

  it('closes file handlers before truncating so writers reopen cleanly', () => {
    expect(logsRoute).toContain('handler.close()')
    expect(logsRoute).toContain('baseFilename')
  })
})

describe('frontend session capture', () => {
  it('hooks vue errors, window errors, rejections, and console', () => {
    expect(sessionLog).toContain('app.config.errorHandler')
    expect(sessionLog).toContain("window.addEventListener('error'")
    expect(sessionLog).toContain("'unhandledrejection'")
    expect(sessionLog).toContain("console[method]")
  })

  it('batches events with a queue cap and failure backoff', () => {
    expect(sessionLog).toContain('MAX_QUEUE')
    expect(sessionLog).toContain('FAILURE_BACKOFF_MS')
    expect(sessionLog).toContain('sendBeacon')
  })

  it('is installed in main.ts', () => {
    expect(mainTs).toContain('installSessionLog')
  })
})

describe('logs settings tab', () => {
  it('adds a Logs tab and loads files when activated', () => {
    expect(settingsView).toContain("id: 'logs'")
    expect(settingsView).toContain("activeTab === 'logs'")
    expect(settingsView).toContain("if (tab === 'logs')")
  })

  it('shows the file list, tail viewer, export, and clear controls', () => {
    expect(settingsView).toContain('log-file-row')
    expect(settingsView).toContain('log-viewer')
    expect(settingsView).toContain('exportLogs')
    expect(settingsView).toContain('clearLogs')
    expect(settingsView).toContain('logsTotalBytes')
  })
})
