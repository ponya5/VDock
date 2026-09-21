// DL-033: green "app session is live" dot on scene pills.
// Backend detects app profiles (marker-verified for terminal agents); the
// frontend resolves scene→profile via appId, button command ids, or trigger
// exe, then GlassPillSceneSelector renders .app-live-dot top-right.
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const service = readFileSync(resolve(__dirname, '../services/appDetection.ts'), 'utf-8')
const selector = readFileSync(resolve(__dirname, '../components/GlassPillSceneSelector.vue'), 'utf-8')
const backend = readFileSync(resolve(__dirname, '../../../backend/routes/app_monitor.py'), 'utf-8')

describe('scene live-dot component wiring', () => {
  it('renders an app-live-dot inside each segment', () => {
    expect(selector).toContain('class="app-live-dot"')
    expect(selector).toContain('sceneAppIsLive(scene, appIntegrations)')
    expect(selector).toContain('.app-live-dot {')
    expect(selector).toContain('top: 3px')
    expect(selector).toContain('right: 3px')
  })

  it('starts the shared poller only while app scanning is enabled', () => {
    expect(selector).toContain('startAppDetection()')
    expect(selector).toContain('stopAppDetection()')
    expect(selector).toContain('appScanningEnabled')
    expect(selector).toContain('immediate: true')
  })
})

describe('appDetection service', () => {
  it('polls the detected-profiles endpoint and loads app-profiles once', () => {
    expect(service).toContain("'/app-monitor/detected-profiles'")
    expect(service).toContain("'/app-profiles'")
    expect(service).toContain('detectedProfiles')
    expect(service).toContain('runningExes')
  })

  it('resolves scenes by command id before falling back to exe', () => {
    const cmdIdx = service.indexOf('profileIdBySceneCommands')
    const exeIdx = service.indexOf('integ?.appExe')
    expect(cmdIdx).toBeGreaterThan(-1)
    expect(exeIdx).toBeGreaterThan(cmdIdx)
    expect(service).toContain('profileIdByCommand')
  })

  it('reads detected profiles unconditionally (reactivity on every path)', () => {
    const fnStart = service.indexOf('export function sceneAppIsLive')
    const body = service.slice(fnStart)
    const detectedRead = body.indexOf('detectedProfiles.value')
    const firstBranch = body.indexOf('if (scene.appId)')
    expect(detectedRead).toBeGreaterThan(-1)
    expect(detectedRead).toBeLessThan(firstBranch)
  })
})

describe('backend detected-profiles endpoint', () => {
  it('exposes /detected-profiles using marker-aware matching', () => {
    expect(backend).toContain("'/detected-profiles'")
    expect(backend).toContain('detected_profiles')
    expect(backend).toMatch(/session_marker|_session_pids/)
  })
})

describe('sceneAppIsLive behavior', () => {
  let loadedServices: Array<typeof import('@/services/appDetection')> = []

  beforeEach(() => {
    vi.resetModules()
  })

  // stopAppDetection now clears the detected sets (DL-040), so it must run
  // after the assertions — not inside loadService — or every check reads
  // wiped state.
  afterEach(() => {
    loadedServices.forEach(m => m.stopAppDetection())
    loadedServices = []
  })

  async function loadService() {
    vi.doMock('@/api/client', () => ({
      default: {
        get: vi.fn(async (url: string) => {
          if (url === '/app-profiles') {
            return {
              data: {
                profiles: [
                  {
                    id: 'claude-code',
                    exes: ['windowsterminal.exe'],
                    commands: [{ id: 'cc_prompt' }, { id: 'cc_interrupt' }],
                    action_types: ['claude_prompt', 'claude_slash'],
                  },
                  {
                    id: 'cursor',
                    exes: ['cursor.exe'],
                    commands: [{ id: 'cursor_chat' }],
                  },
                ],
              },
            }
          }
          return { data: { detected_profiles: ['claude-code'], running_exes: ['windowsterminal.exe'] } }
        }),
      },
    }))
    const mod = await import('@/services/appDetection')
    mod.startAppDetection()
    await new Promise(r => setTimeout(r, 0))
    loadedServices.push(mod)
    return mod
  }

  const sceneWith = (over: object) => ({
    id: 's1',
    pages: [],
    ...over,
  })

  it('lights a scene whose buttons run detected-profile commands', async () => {
    const svc = await loadService()
    const scene = sceneWith({
      pages: [{ buttons: [{ action: { type: 'cc_prompt' } }, { action: { type: 'cc_interrupt' } }] }],
    })
    expect(svc.sceneAppIsLive(scene as any)).toBe(true)
  })

  it('lights a scene whose buttons are plugin action types, not commands', async () => {
    // The shipped Claude Code scene uses claude_pack actions (claude_prompt
    // etc.), which are not keymap commands — the profile's action_types
    // must carry the vote (DL-033 follow-up).
    const svc = await loadService()
    const scene = sceneWith({
      pages: [{ buttons: [{ action: { type: 'claude_prompt' } }, { action: { type: 'claude_slash' } }] }],
    })
    expect(svc.sceneAppIsLive(scene as any)).toBe(true)
  })

  it('does not light a scene whose profile is not detected', async () => {
    const svc = await loadService()
    const scene = sceneWith({
      pages: [{ buttons: [{ action: { type: 'cursor_chat' } }] }],
    })
    expect(svc.sceneAppIsLive(scene as any)).toBe(false)
  })

  it('honors explicit appId and marker-verified trigger exes', async () => {
    const svc = await loadService()
    expect(svc.sceneAppIsLive(sceneWith({ appId: 'claude-code' }) as any)).toBe(true)
    // windowsterminal.exe resolves to claude-code via the exe map — detected.
    expect(svc.sceneAppIsLive(sceneWith({ triggeredByApp: 'WindowsTerminal.exe' }) as any)).toBe(true)
    // Unknown custom exe falls back to raw running-exe list.
    expect(svc.sceneAppIsLive(sceneWith({ triggeredByApp: 'spotify.exe' }) as any)).toBe(false)
    // Unassociated scene → false.
    expect(svc.sceneAppIsLive(sceneWith({}) as any)).toBe(false)
  })
})
