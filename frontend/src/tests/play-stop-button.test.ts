// DL-128: media_play_stop merges Play and Stop into one state-aware cell —
// the backend splits the press by the SMTC snapshot (playing → media_stop,
// otherwise → media_play_pause) and the face swaps icon/sublabel on the live
// now-playing feed.
import { describe, it, expect, beforeEach } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

import DeckButton from '@/components/DeckButton.vue'
import conditionalState from '@/services/conditionalState'
import type { Button } from '@/types'

const backend = readFileSync(
  resolve(__dirname, '../../../backend/actions/cross_platform_action.py'), 'utf-8')
const catalog = readFileSync(
  resolve(__dirname, '../../../backend/actions/catalog.py'), 'utf-8')
const templates = readFileSync(resolve(__dirname, '../data/buttonTemplates.ts'), 'utf-8')

function makeButton(): Button {
  return {
    id: 'b1',
    label: 'Play / Stop',
    secondary_label: '',
    icon: ['fas', 'play'],
    icon_type: 'fontawesome',
    action: { type: 'cross_platform', config: { action: 'media_play_stop' } },
    shape: 'rounded',
    position: { col: 0, row: 0 },
    size: { cols: 1, rows: 1 },
    enabled: true,
  }
}

function mountButton() {
  return mount(DeckButton, {
    props: { button: makeButton() },
    global: { stubs: { FontAwesomeIcon: true } },
  })
}

describe('media_play_stop backend dispatch', () => {
  it('splits the press on the now-playing snapshot', () => {
    expect(backend).toContain("'media_play_stop'")
    expect(backend).toContain('def _media_play_stop')
    expect(backend).toContain("snap.get('playing') is True")
    expect(backend).toContain('return self._media_stop()')
    expect(backend).toContain('return self._media_play_pause()')
  })

  it('is listed in the action catalog so pickers can offer it', () => {
    expect(catalog).toContain("id='media_play_stop'")
  })

  it('is offered in the media button templates', () => {
    expect(templates).toContain("'media_play_stop'")
  })
})

describe('media_play_stop face', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    conditionalState.nowPlaying.playing = false
  })

  it('shows the Play face when nothing is playing', async () => {
    conditionalState.nowPlaying.playing = false
    const wrapper = mountButton()
    await wrapper.vm.$nextTick()
    const icon = wrapper.find('.button-icon font-awesome-icon-stub')
    expect(icon.attributes('icon')).toContain('play')
    expect(wrapper.find('.button-secondary-label').text()).toBe('Play')
  })

  it('shows the Stop face while media is playing', async () => {
    conditionalState.nowPlaying.playing = true
    const wrapper = mountButton()
    await wrapper.vm.$nextTick()
    const icon = wrapper.find('.button-icon font-awesome-icon-stub')
    expect(icon.attributes('icon')).toContain('stop')
    expect(wrapper.find('.button-secondary-label').text()).toBe('Stop')
  })

  it('reacts when the feed flips mid-render', async () => {
    conditionalState.nowPlaying.playing = false
    const wrapper = mountButton()
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.button-secondary-label').text()).toBe('Play')

    conditionalState.nowPlaying.playing = true
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.button-secondary-label').text()).toBe('Stop')
    expect(wrapper.find('.button-icon font-awesome-icon-stub').attributes('icon'))
      .toContain('stop')
  })
})
