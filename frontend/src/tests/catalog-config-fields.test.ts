// DL-145 - the generic config form for catalog (integration-pack) actions:
// one visible field, show_when, and a collapsed Advanced section.
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CatalogConfigFields from '@/components/CatalogConfigFields.vue'
import type { ActionSpec, ConfigFieldSpec } from '@/stores/actionCatalog'

const field = (f: Partial<ConfigFieldSpec> & { name: string }): ConfigFieldSpec => ({
  label: f.name, type: 'text', required: false, ...f,
})

const spec = (fields: ConfigFieldSpec[]): ActionSpec => ({
  id: 'agent_prompt', label: 'Agent Prompt', category: 'ai', icon: ['fas', 'x'],
  action_type: 'agent_prompt', description: '', default_config: {}, config_fields: fields,
  runs_on: 'backend', display_only: false, long_running: false, keywords: [],
})

const presetField = field({
  name: 'preset', label: 'Prompt', type: 'select', default: 'continue',
  options: [{ value: 'continue', label: 'Continue' }, { value: 'custom', label: 'Custom…' }],
})
const textField = field({ name: 'text', label: 'Custom prompt', type: 'textarea', show_when: { preset: 'custom' } })

function mountForm(fields: ConfigFieldSpec[], modelValue: Record<string, unknown> = {}) {
  return mount(CatalogConfigFields, {
    props: { spec: spec(fields), modelValue },
    global: { stubs: { FontAwesomeIcon: true } },
  })
}

describe('CatalogConfigFields', () => {
  it('renders a select with its options and emits the chosen value', async () => {
    const wrapper = mountForm([presetField])
    const options = wrapper.findAll('select option').map((o) => o.text())
    expect(options).toEqual(['Continue', 'Custom…'])

    await wrapper.find('select').setValue('custom')
    expect(wrapper.emitted('update:modelValue')![0][0]).toEqual({ preset: 'custom' })
  })

  it('hides a show_when field until its condition holds', async () => {
    const hidden = mountForm([presetField, textField], {})
    expect(hidden.find('textarea').exists()).toBe(false)

    const shown = mountForm([presetField, textField], { preset: 'custom' })
    expect(shown.find('textarea').exists()).toBe(true)
  })

  it('keeps advanced fields collapsed until Advanced is clicked', async () => {
    const wrapper = mountForm([presetField, field({ name: 'cwd', type: 'path', advanced: true })])
    expect(wrapper.findAll('[data-testid="ccf-field"]')).toHaveLength(1)

    const toggle = wrapper.find('[data-testid="ccf-advanced-toggle"]')
    expect(toggle.attributes('aria-expanded')).toBe('false')
    await toggle.trigger('click')
    expect(toggle.attributes('aria-expanded')).toBe('true')
  })

  it('starts expanded when an advanced field differs from its default', () => {
    const adv = field({ name: 'agent', type: 'select', advanced: true, default: 'auto',
      options: [{ value: 'auto', label: 'Auto' }, { value: 'cursor', label: 'Cursor' }] })
    const changed = mountForm([presetField, adv], { agent: 'cursor' })
    expect(changed.find('[data-testid="ccf-advanced-toggle"]').attributes('aria-expanded')).toBe('true')

    const untouched = mountForm([presetField, adv], { agent: 'auto' })
    expect(untouched.find('[data-testid="ccf-advanced-toggle"]').attributes('aria-expanded')).toBe('false')
  })

  it('renders a boolean as a checkbox switch and emits true/false', async () => {
    const wrapper = mountForm([field({ name: 'watch', label: 'Re-run', type: 'boolean', default: false })])
    const box = wrapper.find('input[type="checkbox"]')
    await box.setValue(true)
    expect(wrapper.emitted('update:modelValue')![0][0]).toEqual({ watch: true })
  })

  it('emits a number, not a string', async () => {
    const wrapper = mountForm([field({ name: 'limit', type: 'number', default: 5 })])
    await wrapper.find('input[type="number"]').setValue('12')
    expect(wrapper.emitted('update:modelValue')![0][0]).toEqual({ limit: 12 })
  })

  it('renders nothing for a spec without fields (no empty Advanced button)', () => {
    const wrapper = mountForm([])
    expect(wrapper.find('[data-testid="ccf-advanced-toggle"]').exists()).toBe(false)
    expect(wrapper.html()).not.toContain('Advanced')
  })

  it('skips field types the generic form cannot edit', () => {
    const wrapper = mountForm([field({ name: 'steps', type: 'steps' })])
    expect(wrapper.find('[data-testid="ccf-field"]').exists()).toBe(false)
  })
})
