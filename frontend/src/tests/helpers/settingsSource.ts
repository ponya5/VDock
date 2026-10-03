import { readdirSync, readFileSync } from 'node:fs'
import { join, resolve } from 'node:path'

const SRC = resolve(__dirname, '..', '..')

function vueFilesUnder(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true })
    .sort((a, b) => a.name.localeCompare(b.name))
    .flatMap((entry) => {
      const full = join(dir, entry.name)
      if (entry.isDirectory()) return vueFilesUnder(full)
      return entry.name.endsWith('.vue') ? [full] : []
    })
}

/** Source of `views/SettingsView.vue` alone - for assertions about the view shell (nav, topbar, wiring). */
export function settingsViewSource(): string {
  return readFileSync(join(SRC, 'views', 'SettingsView.vue'), 'utf-8')
}

/**
 * Concatenated source of SettingsView.vue plus every SFC under components/settings/**,
 * so "the settings UI contains X" assertions survive panel extraction.
 */
export function settingsSource(): string {
  const panels = vueFilesUnder(join(SRC, 'components', 'settings')).map((f) => readFileSync(f, 'utf-8'))
  return [settingsViewSource(), ...panels].join('\n')
}
