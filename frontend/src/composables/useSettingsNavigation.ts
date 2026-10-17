import { computed, nextTick, ref, watch, type Ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  LANDING, findPage, findSection, resolveRoute,
  type SectionId, type SettingsRoute,
} from '@/settings/registry'

const LAST_SECTION_KEY = 'vdock.settings.section'
// Query keys that carry navigation; everything else (e.g. `standalone`) is left alone.
const NAV_KEYS = ['section', 'page', 'anchor', 'tab', 'sub'] as const

function rememberedSection(): SectionId | undefined {
  try {
    const id = sessionStorage.getItem(LAST_SECTION_KEY)
    return findSection(id ?? undefined)?.id
  } catch {
    return undefined
  }
}

/**
 * Current Settings section + page, kept in sync with the URL (`?section=&page=`,
 * plus legacy `?tab=&sub=` and `?anchor=`) and remembered per browser session.
 */
export function useSettingsNavigation(scroller: Ref<HTMLElement | null>) {
  const route = useRoute()
  const router = useRouter()

  const section = ref<SectionId>(LANDING)
  const page = ref('')

  const activeSection = computed(() => findSection(section.value)!)
  const activePage = computed(() => findPage(activeSection.value, page.value) ?? activeSection.value.pages[0])

  function scrollTop() {
    void nextTick(() => scroller.value?.scrollTo({ top: 0 }))
  }

  // Scroll to the anchor and pulse it so the user sees which setting the link meant.
  // The element may mount a beat later (rows gated on an async status fetch), so retry briefly.
  function scrollToPanel(id: string, tries = 15) {
    void nextTick(() => {
      const el = document.getElementById(id)
      if (!el) {
        if (tries > 0) setTimeout(() => scrollToPanel(id, tries - 1), 100)
        return
      }
      el.scrollIntoView({ block: 'center', behavior: 'smooth' })
      el.classList.remove('nav-flash')
      void el.offsetWidth // restart the animation when the same anchor is hit twice
      el.classList.add('nav-flash')
      setTimeout(() => el.classList.remove('nav-flash'), 2600)
    })
  }

  function syncQuery() {
    const query: Record<string, unknown> = { ...route.query }
    for (const key of NAV_KEYS) delete query[key]
    query.section = section.value
    query.page = page.value
    const changed = NAV_KEYS.some((k) => String(route.query[k] ?? '') !== String(query[k] ?? ''))
    if (changed) void router.replace({ query: query as Record<string, string> })
  }

  function go(target: SettingsRoute) {
    const moved = target.section !== section.value || target.page !== page.value
    section.value = target.section
    page.value = target.page
    try { sessionStorage.setItem(LAST_SECTION_KEY, target.section) } catch { /* private mode */ }
    syncQuery()
    if (target.anchor) scrollToPanel(target.anchor)
    else if (moved) scrollTop()
  }

  function selectSection(id: SectionId) {
    go({ section: id, page: findSection(id)!.pages[0].id })
  }

  function selectPage(id: string) {
    go({ section: section.value, page: id })
  }

  function hasNavQuery() {
    return NAV_KEYS.some((k) => route.query[k] !== undefined)
  }

  function applyRoute() {
    if (hasNavQuery()) {
      go(resolveRoute(route.query))
      return
    }
    const remembered = rememberedSection()
    go(resolveRoute({ section: remembered ?? LANDING }))
  }

  applyRoute()

  // Only react while Settings itself is the route: leaving it empties the query.
  watch(() => route.query, () => {
    if (route.path === '/settings' && hasNavQuery()) go(resolveRoute(route.query))
  })

  return { section, page, activeSection, activePage, selectSection, selectPage, go, scrollToPanel }
}
