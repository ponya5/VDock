<template>
  <div class="guide-view">
    <div class="guide-shell">
      <!-- ── Side nav — fixed docs rail: search + grouped sections ────── -->
      <aside class="guide-nav" aria-label="Guide navigation">
        <div class="brand nav-brand">
          <span class="brand-mark">V</span>
          <span class="brand-name">Dock</span>
          <span class="brand-ver">v{{ appVersion }}</span>
        </div>

        <div class="hero-search nav-search" :class="{ 'has-query': query }">
          <FontAwesomeIcon :icon="['fas', 'search']" class="search-ico" />
          <input
            ref="searchEl"
            v-model="query"
            type="search"
            class="search-input"
            placeholder="Search — “MCP”, “screensaver”…"
            aria-label="Search the guide"
            @keydown.enter.prevent="scrollToFirst"
            @keydown.esc.prevent="clearSearch"
          />
          <button v-if="query" type="button" class="search-clear" aria-label="Clear search" @click="clearSearch">
            <FontAwesomeIcon :icon="['fas', 'xmark']" />
          </button>
          <kbd class="search-kbd">/</kbd>
        </div>

        <nav class="nav-groups">
          <div v-for="g in navGroups" :key="g.label" class="nav-group">
            <p class="nav-group-label">{{ g.label }}</p>
            <a
              v-for="item in g.items"
              :key="item.id"
              :href="`#${item.id}`"
              class="nav-item"
              :class="{ active: activeId === item.id }"
              @click.prevent="jumpTo(item.id)"
            >
              <FontAwesomeIcon :icon="item.icon" class="nav-ico" />
              <span>{{ item.title }}</span>
              <span v-if="item.badge" class="hot-badge hot-badge-sm">{{ item.badge }}</span>
            </a>
          </div>
        </nav>

        <router-link to="/" class="back-link nav-back">
          <FontAwesomeIcon :icon="['fas', 'arrow-left']" /> Back to the deck
        </router-link>
      </aside>

      <!-- ── Scrollport — #app clips overflow, so this column scrolls ── -->
      <div ref="scrollEl" class="guide-content" @scroll.passive="onScroll">
        <header class="guide-hero">
          <div class="hero-top">
            <div class="brand">
              <span class="brand-mark">V</span>
              <span class="brand-name">Dock</span>
              <span class="brand-ver">v{{ appVersion }}</span>
            </div>
            <router-link to="/" class="back-link">
              <FontAwesomeIcon :icon="['fas', 'arrow-left']" /> Back to the deck
            </router-link>
          </div>

          <h1 class="hero-title">Every feature, in one place.</h1>
          <p class="hero-sub">
            VDock is a touch-first control deck for your PC and your AI agents —
            scenes of buttons, live media, awareness of what your agents are
            doing, and an MCP server so agents can drive the deck back.
          </p>

          <div class="hero-search mobile-search" :class="{ 'has-query': query }">
            <FontAwesomeIcon :icon="['fas', 'search']" class="search-ico" />
            <input
              ref="mobileSearchEl"
              v-model="query"
              type="search"
              class="search-input"
              placeholder="Search features — try “MCP”, “screensaver”, “scene”…"
              aria-label="Search the guide"
              @keydown.enter.prevent="scrollToFirst"
              @keydown.esc.prevent="clearSearch"
            />
            <button v-if="query" type="button" class="search-clear" aria-label="Clear search" @click="clearSearch">
              <FontAwesomeIcon :icon="['fas', 'xmark']" />
            </button>
            <kbd class="search-kbd">/</kbd>
          </div>
          <p v-if="query" class="search-status" role="status">
            {{ filteredFeatures.length
              ? `${filteredFeatures.length} section${filteredFeatures.length === 1 ? '' : 's'} match “${query}”`
              : `Nothing matches “${query}” — try a single word like “media” or “agent”.` }}
          </p>
        </header>

        <!-- Sub tabs — sticky rail on narrow screens where the nav hides -->
        <nav class="hero-chips chips-bar" aria-label="Jump to a section">
          <a
            v-for="f in filteredFeatures"
            :key="f.id"
            :href="`#${f.id}`"
            class="chip"
            :class="{ active: activeId === f.id }"
            @click.prevent="jumpTo(f.id)"
          >
            <FontAwesomeIcon :icon="f.icon" /> {{ f.title }}
            <span v-if="f.badge" class="hot-badge hot-badge-sm">{{ f.badge }}</span>
          </a>
        </nav>

        <!-- ── Feature sections ──────────────────────────────────────── -->
        <main class="guide-main">
          <section
            v-for="(f, i) in filteredFeatures"
            :key="f.id"
            :id="f.id"
            :ref="el => registerSection(f.id, el)"
            class="feature"
            :class="{ flip: i % 2 === 1 }"
          >
            <div class="feature-text">
              <div class="feature-head">
                <span class="feature-ico"><FontAwesomeIcon :icon="f.icon" /></span>
                <div>
                  <h2>{{ f.title }}<span v-if="f.badge" class="hot-badge">{{ f.badge }}</span></h2>
                  <p class="feature-tagline">{{ f.tagline }}</p>
                </div>
              </div>
              <p v-for="(para, j) in f.body" :key="j" class="feature-para" v-html="para" />
              <ul v-if="f.points" class="feature-points">
                <li v-for="(p, j) in f.points" :key="j" v-html="p" />
              </ul>
              <pre v-if="f.code" class="feature-code"><code>{{ f.code }}</code></pre>
            </div>
            <figure v-if="f.shot" class="feature-shot">
              <img :src="`/guide/${f.shot}`" :alt="`${f.title} — screenshot`" loading="lazy" />
              <figcaption>{{ f.shotCaption }}</figcaption>
            </figure>
          </section>
        </main>

        <SiteFooter />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Dedicated guide landing page (DL-132) — replaces the embedded Settings
// guide tab. Opens in its own browser window so the deck stays visible.
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import type { ComponentPublicInstance } from 'vue'
import { useRoute } from 'vue-router'
import { version as appVersion } from '../../package.json'
import SiteFooter from '@/components/SiteFooter.vue'

interface GuideFeature {
  id: string
  icon: [string, string]
  title: string
  /** Short animated label next to the title and nav item, e.g. "HOT!!". */
  badge?: string
  tagline: string
  body: string[]
  points?: string[]
  code?: string
  shot?: string
  shotCaption?: string
  keywords: string
}

const features: GuideFeature[] = [
  {
    id: 'deck',
    icon: ['fas', 'th-large'],
    title: 'The Deck',
    tagline: 'Your grid of live buttons',
    body: [
      'The deck is a grid of buttons. Tap one and its action fires — launch an app, press a hotkey, change the volume, switch scene. Everything on it is yours to arrange.',
      'Toggle <strong>Edit Mode</strong> (the pencil in the header, or <code>Ctrl+E</code>) and the grid opens up: tap an empty cell to add a button, drag to move, drag a corner to resize, right-click for copy/paste/delete.',
    ],
    points: [
      '<strong>Pages</strong> — a scene that outgrows its grid gets extra pages; flip with the dots or ‹ › under the grid.',
      '<strong>Swipe</strong> — left/right anywhere on the deck moves between scenes; up/down reveals or hides the header.',
      '<strong>Quick search</strong> — <code>Ctrl+F</code> in edit mode searches existing buttons and new actions.',
      '<strong>Small windows</strong> — shrink the desktop window and keys turn icon-only and scale to fit; alerts and the agent bar shrink with them.',
    ],
    shot: 'guide-deck.png',
    shotCaption: 'The deck — a scene of live buttons on the 7″ panel.',
    keywords: 'button grid edit mode drag resize page swipe gesture layout cell keyboard shortcut ctrl e f small window icon only',
  },
  {
    id: 'mobile',
    icon: ['fas', 'mobile-screen-button'],
    title: 'Mobile View',
    badge: 'HOT!!',
    tagline: 'Your phone or tablet is a deck',
    body: [
      'Open VDock on any phone or tablet on your Wi-Fi — scan the QR code in <strong>Settings → Devices &amp; network → Connect &amp; security</strong>. No app store, no account. Add it to the Home Screen for a full-screen deck with no browser bars.',
      '🔐 <strong>Secure without the hassle:</strong> the QR code carries a unique, one-time <strong>pairing token</strong>, so the phone is signed in the moment you scan it, with no password to type. The token works once and expires within minutes, and each phone gets its own login you can revoke.',
    ],
    points: [
      '<strong>Phone = a remote</strong> — a portrait grid sized for your thumb, a Claude Code console, and an approval remote: approve or deny a waiting agent from the couch.',
      '<strong>Tablet = a full deck</strong> — portrait and landscape grids, editing on the device, and the screen stays awake.',
      '<strong>Landscape phones</strong> get a slim header and a compact scene rail that can auto-hide; swipe left and right to change scenes.',
      '<strong>Follows your work</strong> — auto scene switching works on the phone too: bring Cursor forward on the PC and the phone jumps to the Cursor scene.',
      '<strong>Per device</strong> — Day mode, touch size and menu toggles are set on each phone, so the panel and your phone can look different.',
      '<strong>Stays in sync</strong> — reconnects on its own, resumes on the right scene, and edits on one device show up on every other.',
    ],
    shot: 'guide-mobile.png',
    shotCaption: 'Media on one phone, Claude Code on a phone and a tablet — same deck, same QR code.',
    keywords: 'mobile phone tablet ipad android iphone remote portrait landscape touch thumb approval approve deny couch home screen pwa install wifi qr pair pairing token secure security swipe rail keep awake day mode sync reconnect hot',
  },
  {
    id: 'scenes',
    icon: ['fas', 'layer-group'],
    title: 'Scenes & Profiles',
    tagline: 'A deck per context',
    body: [
      'A <strong>scene</strong> is a screen of buttons — Media, Cursor, Claude Code, Websites. The pills in the header switch between them; in edit mode the <strong>+</strong> adds a new one. A live dot on a pill means that app is running.',
      'Each scene has its own name, icon, accent color, grid size and button set. A scene can also be <em>app-linked</em>: VDock switches to it when that app comes to the front (see Integrations). Change the order of the pills from the scene editor.',
      '<strong>Profiles</strong> are whole decks — separate button sets you can swap from the Profiles page, duplicate, or export.',
    ],
    shot: 'guide-scene-editor.png',
    shotCaption: 'The scene editor — name, icon, color, grid, pages.',
    keywords: 'scene pill profile switch new add editor icon color grid size page duplicate export import deck set order reorder live dot',
  },
  {
    id: 'templates',
    icon: ['fas', 'wand-magic-sparkles'],
    title: 'App Templates',
    tagline: 'Ready-made scenes for the tools you use',
    body: [
      'Start from a template instead of a blank grid. Claude Code, Claude Cowork, Cursor, VS Code, JetBrains, GitHub, OBS, Spotify, ChatGPT, Figma, n8n and dozens more come with sensible buttons.',
      'The first-run tour asks which apps you use and builds a scene for each. Later, turning an app on in <strong>Agents &amp; automation → Apps &amp; scenes</strong> asks before it adds a scene, pre-filled with that app’s shortcuts when VDock knows them.',
      'The <strong>GitHub</strong> scene drives the <code>gh</code> CLI: open PRs, review requests, CI, PR checks, issues, runs and “rerun failed”.',
    ],
    shot: 'guide-templates.png',
    shotCaption: 'The GitHub scene, with every app scene in the top bar.',
    keywords: 'template app scene starter preset claude code cowork cursor vscode jetbrains github gh pr ci checks issues runs obs spotify chatgpt figma n8n import pack',
  },
  {
    id: 'appearance',
    icon: ['fas', 'palette'],
    title: 'Look & Feel',
    tagline: 'Day mode, key designs, clocks',
    body: [
      '<strong>Day mode</strong> swaps the dark look for a light one — on, off, or Auto to follow each device’s own light/dark setting. It is set per device, so the panel can stay dark while your phone goes light.',
      'Pick a <strong>key design</strong> in <strong>Appearance → Buttons</strong> (glass, Deck Key and more), then use <strong>Apply to all keys</strong> to restyle every button at once. It shows you what will change first and can be undone.',
      'Under <strong>Clocks</strong>, choose 12- or 24-hour time for the screensaver, session lists and logs.',
      'Want more room for buttons? Hide the header from <strong>Appearance → Layout &amp; sidebar</strong>. Tap the reveal chip in the corner, or swipe down from the top, to bring it back; it hides again after a countdown unless you tap the pill to pin it.',
    ],
    keywords: 'appearance day mode light dark theme auto key design style glass deck key apply all undo font typography clock 12 24 hour background wallpaper header reveal auto hide countdown pill pin',
  },
  {
    id: 'media',
    icon: ['fas', 'music'],
    title: 'Media & Now Playing',
    tagline: 'Your music, on the glass',
    body: [
      'VDock reads the system media session (SMTC on Windows), so the deck always knows what Spotify — or any player — is doing.',
      'The <strong>Now Playing</strong> card shows album art, track, artist · source and a live progress bar — and <em>tapping it toggles play/pause</em>. Add it from the Media Controls list when editing a button.',
      'The merged <strong>Play / Stop</strong> button shows what it will do, and the <strong>volume slider</strong> drags the system volume with quick 25/50/75/100 stops.',
    ],
    shot: 'guide-media.png',
    shotCaption: 'The Media scene — transport, volume slider, Now Playing.',
    keywords: 'media now playing spotify smtc track artist album art progress play pause stop volume slider music mute next previous',
  },
  {
    id: 'screensaver',
    icon: ['fas', 'moon'],
    title: 'Screen Savers',
    tagline: 'Idle, but still useful',
    body: [
      'Leave the deck alone and it becomes a glanceable display. Pick the type in <strong>Appearance → Screen saver</strong>; <strong>Test</strong> shows it right away and <strong>Customise layout</strong> lets you drag widgets around.',
    ],
    points: [
      '<strong>Widget dashboard</strong> — clock, weather, news, sports, markets and world clocks, each draggable and resizable.',
      '<strong>Spectrum visualizer</strong> — 16 skins from Winamp bars to Iso Field, Wave Grid and Neon Flight, reacting to whatever plays. The bars follow the music itself, so turning the volume up or down doesn’t change them. Shuffle the skins on a timer and keep a Now Playing card with media controls on top.',
      '<strong>System stats</strong> — a full-screen board of CPU, memory, disk and network gauges, plus the busiest processes.',
      '<strong>Robot buddy</strong> — Wingy and a big clock (see the next section).',
      '<strong>Shuffle</strong> — rotates through the other types every few minutes.',
    ],
    shot: 'guide-screensaver.png',
    shotCaption: 'The four screen saver types — Wingy, widget dashboard, system stats and the Iso Field spectrum.',
    keywords: 'screensaver idle sleep widgets weather news sports market clock system stats spectrum visualizer winamp aurora ember neon skin shuffle wake test customise layout',
  },
  {
    id: 'wingy',
    icon: ['fas', 'face-smile'],
    title: 'Wingy, the Robot Buddy',
    tagline: 'A screensaver that knows what you’re up to',
    body: [
      'Choose <strong>Robot buddy</strong> as the screensaver type and Wingy takes one half of the screen, with a big clock on the other. Wingy shows what the PC is doing:',
    ],
    points: [
      '<strong>Coding agents</strong> — types along on a laptop while Claude Code or Cursor works, waves a phone at you when the agent waits, and celebrates with a party hat when it’s done.',
      '<strong>Music</strong> — puts on headphones and dances, in time with the beat.',
      '<strong>System load</strong> — sweats through CPU spikes and complains about a low battery.',
      '<strong>Time &amp; weather</strong> — morning coffee, sleepy nights, sunglasses on sunny days.',
      '<strong>Poke it</strong> — its eyes follow your finger or mouse; tickle its mouth, circle around it or linger and it reacts.',
      '<strong>Moods</strong> — Funny, Grumpy, Sarcastic, Sweet, or a random one each day, with optional speech bubbles. Choose Wingy’s side and switch each kind of reaction on or off.',
    ],
    shot: 'guide-wingy.png',
    shotCaption: 'Wingy with headphones on while music plays.',
    keywords: 'wingy robot buddy screensaver face eyes mouth mood funny grumpy sarcastic sweet random quips speech bubble music beat agent coding cpu battery weather poke pet tickle',
  },
  {
    id: 'agents',
    icon: ['fas', 'robot'],
    title: 'Agent Awareness',
    tagline: 'See what your agents need',
    body: [
      'AI coding scenes (Claude Code, Cursor, Codex, Devin, Copilot…) open with a <strong>status tile</strong> — READY, WORKING or WAITING — next to the session picker and one-tap actions like Submit, Continue, Mode, New Session and Compact, sent straight into the running session.',
      'Flip between <strong>Groups</strong> and <strong>All</strong>: Groups sorts the buttons into a sidebar (Session, Review &amp; Ship, Mode &amp; Model, Context); All shows them in one grid.',
      'When an agent needs you, a <strong>waiting bar</strong> appears at the bottom with <strong>Snooze</strong> and <strong>Dismiss</strong>, and a toast follows each state change. Set the snooze length, or turn Snooze off, in <strong>Agents &amp; automation → Alerts</strong>.',
      'VDock focuses the session’s window before it types, so keystrokes never land in the wrong place.',
    ],
    shot: 'guide-agents.png',
    shotCaption: 'The Claude Code scene — status tile, session actions, Groups view and the waiting bar.',
    keywords: 'agent session claude cursor codex devin copilot status ready working waiting tile groups all category waiting bar snooze dismiss toast permission focus pin prompt submit continue mode compact new session keystroke',
  },
  {
    id: 'mission-control',
    icon: ['fas', 'satellite-dish'],
    title: 'Mission Control',
    tagline: 'Every agent session in one place',
    body: [
      'Open <strong>Mission Control</strong> from the header or the chip on the deck to see every agent session at once: working, waiting or done, with the project each one runs in.',
      'Approve, deny or open a waiting session right from the list — from your phone too — and the answer goes into the <em>live</em> session, not a new one.',
    ],
    keywords: 'mission control sessions agents list approve deny open waiting working done inbox approval remote phone',
  },
  {
    id: 'mcp',
    icon: ['fas', 'server'],
    title: 'MCP Server',
    tagline: 'Agents drive the deck back',
    body: [
      'VDock runs a local <strong>MCP server</strong> — the same protocol Cursor, Claude and Windsurf speak — so agents can press deck buttons, switch scenes, read what’s playing, set the volume, or push a notification.',
      'Enable it in <strong>Settings → Agents &amp; automation → MCP server</strong>, then point your agent at the endpoint. The <strong>Help &amp; test</strong> button in that section has copy-paste config blocks for each client and a one-click self-test.',
    ],
    code: `// .cursor/mcp.json (or claude mcp add --transport http)
{ "mcpServers": { "vdock": { "url": "http://127.0.0.1:5000/api/mcp" } } }`,
    shot: 'guide-mcp.png',
    shotCaption: 'MCP help & self-test — connected, 11 tools.',
    keywords: 'mcp model context protocol server tools agent cursor claude press button switch scene notification api json rpc self test',
  },
  {
    id: 'integrations',
    icon: ['fas', 'plug'],
    title: 'Integrations & Triggers',
    tagline: 'The deck reacts on its own',
    body: [
      '<strong>Auto scene switching</strong> watches the app in front: bring Cursor forward and its scene appears, on the panel and on your phone. Pick the apps and their scenes under <strong>Agents &amp; automation → Apps &amp; scenes</strong>; a link to a deleted scene repairs itself.',
      '<strong>Triggers</strong> fire actions without a tap — on a schedule, when an app launches, when an agent finishes, or when a webhook arrives. Each trigger pairs an event with any deck action.',
      '<strong>Agent alerts</strong> tune how the waiting glow appears: banner, chips, dock — pick what you notice.',
    ],
    shot: 'guide-integrations.png',
    shotCaption: 'Integrations — apps, alerts, triggers, MCP.',
    keywords: 'integration trigger schedule automation app foreground switch scene webhook agent alert glow banner dock running apps monitor auto',
  },
  {
    id: 'connect',
    icon: ['fas', 'shield-halved'],
    title: 'Connect & Security',
    tagline: 'Your phone or tablet as a second deck',
    body: [
      'Any browser on your Wi-Fi can be a deck — the 7″ panel, a phone, a tablet next to the keyboard. Open <strong>Settings → Devices &amp; network → Connect &amp; security</strong>, turn on <strong>Allow phone &amp; tablet access</strong>, and scan the QR code. Add VDock to the Home Screen for a full-screen deck.',
      'Lock it down with <strong>Require pairing</strong> (only devices that scan the code get in) or a deck password. Pairing needs no typing: the QR code holds a unique, random, single-use <strong>pairing token</strong> that expires after 3 minutes, and the QR code refreshes itself. The phone trades it once for its own login token. An old screenshot of the code is useless, and repeated attempts are rate-limited. That login token protects the HTTP API, the socket and the MCP endpoint.',
      'Every device that joins is listed with its name and when it was last seen — <strong>Rename</strong> or <strong>Revoke</strong> it — and a toast announces each new one. Phone can’t connect? <strong>Check connection</strong> tests the address, phone access and the firewall and offers a one-click fix.',
      '<strong>Ask before pushing or committing code</strong> makes push, commit, merge and deploy buttons ask “Are you sure?” first.',
    ],
    shot: 'guide-connect.png',
    shotCaption: 'Connect & security — QR code, pairing, connected devices (address masked).',
    keywords: 'connect device phone tablet qr lan wifi remote second deck mirror pair pairing security password auth token lock revoke rename check connection firewall push commit confirm',
  },
  {
    id: 'updates',
    icon: ['fas', 'cloud-arrow-down'],
    title: 'Updates',
    tagline: 'New versions in one tap',
    body: [
      'VDock checks GitHub for a new release each time it starts. A prompt offers <strong>Update now</strong> (the Windows installer and source checkouts update themselves) or <strong>Download</strong> on other installs; <strong>Later</strong> hides it until the next launch.',
      'After an update, VDock restarts on its own and shows an <strong>Updated to vX</strong> toast. The current version sits in the bottom-left corner of the deck and in <strong>Settings → About</strong>, where <strong>Check now</strong> looks again.',
    ],
    code: `vdock-backend --version   # installed app: prints "VDock x.y.z"
launch.bat --version      # source checkout (launch.sh on macOS / Linux)`,
    keywords: 'update upgrade release version new installer download check now later about toast watermark command line version flag',
  },
  {
    id: 'settings',
    icon: ['fas', 'sliders'],
    title: 'Settings',
    tagline: 'Organized, searchable',
    body: [
      'Settings opens on an <strong>Overview</strong> of what needs attention, then groups everything into Appearance, Agents &amp; automation, Devices &amp; network, System and About. Each section breaks into <strong>top sub-tabs</strong>, so every panel is one click away.',
      'The sidebar search jumps straight to a setting: “spectrum”, “day mode”, “MCP” — hit it and you land on the exact panel. Changes save as you go, and <strong>Reset section</strong> puts a panel back to its defaults.',
    ],
    shot: 'guide-settings.png',
    shotCaption: 'Settings — sidebar tabs plus top sub-tabs.',
    keywords: 'settings overview appearance agents automation devices network system about sub tabs sidebar search reset preferences options',
  },
  {
    id: 'tour',
    icon: ['fas', 'route'],
    title: 'Onboarding Tour',
    tagline: 'A one-minute start',
    body: [
      'First run offers a short tour: pick the apps you use (each gets a ready-made scene), then meet scenes, the deck, Agents &amp; automation and phone access. It only moves when <em>you</em> press Next, Back or Skip.',
      'Replay it any time from <strong>Settings → About → Launch tutorial</strong>.',
    ],
    shot: 'guide-tour.png',
    shotCaption: 'The tour spotlighting the scene pills.',
    keywords: 'tour tutorial onboarding walkthrough guide help first run steps skip next back apps picker phone',
  },
]

const query = ref(typeof useRoute().query.q === 'string' ? String(useRoute().query.q) : '')
const searchEl = ref<HTMLInputElement | null>(null)
const mobileSearchEl = ref<HTMLInputElement | null>(null)
const scrollEl = ref<HTMLElement | null>(null)
const activeId = ref(features[0].id)
const sections = new Map<string, Element>()

/** Sidebar grouping — the "sub tabs" under which sections cluster. */
const NAV_GROUPS: Array<{ label: string; ids: string[] }> = [
  { label: 'The Deck', ids: ['deck', 'mobile', 'scenes', 'templates', 'appearance'] },
  { label: 'Media & Display', ids: ['media', 'screensaver', 'wingy'] },
  { label: 'Agents & Automation', ids: ['agents', 'mission-control', 'mcp', 'integrations'] },
  { label: 'System', ids: ['connect', 'updates', 'settings', 'tour'] },
]

function registerSection(id: string, el: Element | ComponentPublicInstance | null) {
  if (el instanceof Element) sections.set(id, el)
  else sections.delete(id)
}

const tokens = computed(() => query.value.toLowerCase().split(/\s+/).filter(Boolean))
const filteredFeatures = computed(() => {
  if (!tokens.value.length) return features
  return features.filter((f) => {
    const hay = [f.title, f.tagline, f.keywords, ...f.body, ...(f.points ?? [])]
      .join(' ').toLowerCase()
    return tokens.value.every((t) => hay.includes(t))
  })
})

/** Groups filtered down to the sections matching the current search. */
const navGroups = computed(() => {
  const visible = new Set(filteredFeatures.value.map(f => f.id))
  const byId = new Map(features.map(f => [f.id, f]))
  return NAV_GROUPS
    .map(g => ({ label: g.label, items: g.ids.filter(id => visible.has(id)).map(id => byId.get(id)!) }))
    .filter(g => g.items.length)
})

function jumpTo(id: string) {
  activeId.value = id
  sections.get(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
function scrollToFirst() {
  const first = filteredFeatures.value[0]
  if (first) jumpTo(first.id)
}
function clearSearch() {
  query.value = ''
  focusSearch()
}

/** Scroll-spy: the active section is the last one whose top passed the
 *  mark a bit below the content column's top edge. */
function onScroll() {
  const el = scrollEl.value
  if (!el) return
  const mark = el.getBoundingClientRect().top + Math.min(220, el.clientHeight * 0.3)
  let cur = filteredFeatures.value[0]?.id ?? ''
  for (const f of filteredFeatures.value) {
    const s = sections.get(f.id)
    if (s && s.getBoundingClientRect().top <= mark) cur = f.id
  }
  activeId.value = cur
}

function focusSearch() {
  const el = [searchEl.value, mobileSearchEl.value].find(e => e && e.offsetParent !== null)
  el?.focus()
}

function onKeydown(e: KeyboardEvent) {
  const tag = (e.target as HTMLElement)?.tagName
  if (e.key === '/' && tag !== 'INPUT' && tag !== 'TEXTAREA') {
    e.preventDefault()
    focusSearch()
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  nextTick(onScroll)
})
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
/* Same editorial palette as SettingsView (DL-017) — defined locally since
   the tokens live on each view's root, not :root. */
.guide-view {
  --bg: #0a111f;
  --bg-sunken: #070d18;
  --panel: #111c2f;
  --panel-2: #16233a;
  --field: #0d1728;
  --line: #1f2f4a;
  --line-soft: #172540;
  --text: #e9eff8;
  --text-2: #9fb0c9;
  --text-3: #7286a4;
  --accent: #4a8cff;
  --accent-ghost: rgba(74, 140, 255, 0.14);
  --r-lg: 14px;
  --r-md: 10px;
  --r-sm: 8px;
  --gutter: 24px;
  --mono: ui-monospace, "Cascadia Mono", "JetBrains Mono", Consolas, monospace;
  --fs-xs: 0.79em;
  --fs-sm: 0.88em;
  --fs-md: 0.95em;
  --fs-lg: 1.07em;

  /* The app shell (#app) is height:100dvh + overflow:hidden — the body can
     never scroll. This view owns its scrollport: a fixed-height shell with
     a static side rail and a scrolling content column. */
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background:
    radial-gradient(90% 60% at 80% -10%, rgba(74, 140, 255, 0.10) 0%, transparent 55%),
    radial-gradient(70% 50% at 5% 10%, rgba(139, 92, 246, 0.10) 0%, transparent 60%),
    var(--bg);
  color: var(--text);
  font-size: clamp(13px, 0.86rem + 0.2vw, 15.5px);
}

.guide-shell {
  display: flex;
  height: 100%;
  min-height: 0;
}
.guide-content {
  flex: 1;
  min-width: 0;
  height: 100%;
  overflow-y: auto;
  overscroll-behavior: contain;
}

/* ── side nav rail ─────────────────────────────────────────────────────── */
.guide-nav {
  flex: none;
  width: 264px;
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 14px;
  background: var(--bg-sunken);
  border-right: 1px solid var(--line-soft);
}
.nav-brand { margin: 2px 4px 6px; }
.nav-search { max-width: none; }
.nav-search .search-input { padding: 10px 4px; font-size: var(--fs-sm); }
.nav-search .search-kbd { display: none; }

.nav-groups { display: flex; flex-direction: column; gap: 14px; }
.nav-group-label {
  margin: 0 4px 5px;
  font-size: var(--fs-xs);
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-3);
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 8px 10px;
  margin: 1px 0;
  border-radius: var(--r-sm);
  border-left: 2px solid transparent;
  color: var(--text-2);
  text-decoration: none;
  font-size: var(--fs-sm);
  transition: color var(--transition-fast), background var(--transition-fast);
}
.nav-item .nav-ico { width: 14px; flex: none; color: var(--text-3); }
.nav-item:hover { color: var(--text); background: var(--panel); }
.nav-item.active {
  color: var(--text);
  background: var(--accent-ghost);
  border-left-color: var(--accent);
}
.nav-item.active .nav-ico { color: var(--accent); }
.nav-back { margin-top: auto; justify-content: center; }

/* ── hero ──────────────────────────────────────────────────────────────── */
.guide-hero {
  max-width: 980px;
  margin: 0 auto;
  padding: 26px var(--gutter) 8px;
}
/* Desktop: brand + back live in the side rail, not the hero. */
.hero-top { display: none; }
.brand { display: flex; align-items: center; gap: 9px; }
.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--accent), #8b5cf6);
  color: #fff;
  font-weight: 800;
  font-size: 1.13em;
}
.brand-name { font-weight: 700; font-size: 1.2em; letter-spacing: 0.2px; }
.brand-ver {
  font-size: var(--fs-xs);
  color: var(--text-3);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 2px 9px;
  margin-left: 2px;
}
.back-link {
  color: var(--text-2);
  text-decoration: none;
  font-size: var(--fs-sm);
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 7px 12px;
  border-radius: var(--r-sm);
  border: 1px solid var(--line-soft);
  background: var(--panel);
  transition: color var(--transition-fast), border-color var(--transition-fast);
}
.back-link:hover { color: var(--text); border-color: var(--line); }

.hero-title {
  font-size: clamp(28px, 4.4vw, 44px);
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.1;
  margin: 0 0 12px;
}
.hero-sub {
  max-width: 640px;
  color: var(--text-2);
  font-size: var(--fs-lg);
  line-height: 1.55;
  margin: 0 0 26px;
}

.hero-search {
  position: relative;
  display: flex;
  align-items: center;
  max-width: 560px;
  background: var(--field);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}
.hero-search.has-query, .hero-search:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ghost);
}
.search-ico { margin: 0 12px; color: var(--text-3); }
.search-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--text);
  font-size: clamp(13px, 0.86rem + 0.2vw, 15.5px);
  padding: 13px 4px;
  min-width: 0;
}
.search-input::placeholder { color: var(--text-3); }
.search-input::-webkit-search-cancel-button { display: none; }
.search-clear {
  border: none;
  background: none;
  color: var(--text-3);
  cursor: pointer;
  padding: 6px 8px;
  font-size: var(--fs-md);
}
.search-clear:hover { color: var(--text); }
/* Desktop: the search lives in the side rail — the hero copy is mobile
   only. Scoped after .hero-search so the two-class selector wins. */
.hero-search.mobile-search { display: none; }
.search-kbd {
  margin: 0 10px;
  padding: 2px 7px;
  border: 1px solid var(--line);
  border-bottom-width: 2px;
  border-radius: 5px;
  background: var(--panel);
  color: var(--text-3);
  font-size: var(--fs-xs);
  font-family: var(--mono);
}
.search-status { margin: 8px 2px 0; font-size: var(--fs-sm); color: var(--text-3); }

/* Sub-tab chip rail — desktop gets the side rail instead. */
.chips-bar { display: none; }
.hero-chips {
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 0;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--line-soft);
  background: var(--panel);
  color: var(--text-2);
  font-size: var(--fs-sm);
  text-decoration: none;
  transition: color var(--transition-fast), border-color var(--transition-fast);
}
.chip:hover { color: var(--text); border-color: var(--accent); }
.chip.active { color: var(--text); border-color: var(--accent); background: var(--accent-ghost); }

/* ── feature rows ─────────────────────────────────────────────────────── */
.guide-main {
  max-width: 980px;
  margin: 0 auto;
  padding: 18px var(--gutter) 40px;
  display: flex;
  flex-direction: column;
  gap: 34px;
}
.feature {
  display: grid;
  grid-template-columns: 1fr 1.05fr;
  gap: 30px;
  align-items: center;
  padding: 26px;
  border: 1px solid var(--line-soft);
  border-radius: var(--r-lg);
  background: var(--panel);
  scroll-margin-top: 20px;
}
.feature.flip .feature-text { order: 2; }
.feature:not(:has(.feature-shot)) { grid-template-columns: 1fr; }

.feature-head {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  margin-bottom: 14px;
}
.feature-ico {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  flex: none;
  border-radius: var(--r-md);
  background: var(--accent-ghost);
  color: var(--accent);
  font-size: 1.2em;
}
.feature-head h2 { margin: 2px 0 3px; font-size: calc(var(--fs-lg) * 1.25); font-weight: 700; letter-spacing: -0.01em; }
.feature-tagline { margin: 0; color: var(--text-3); font-size: var(--fs-sm); }

/* "HOT!!" badge — moving fire gradient, a heartbeat pulse and a glow. */
.hot-badge {
  display: inline-block;
  margin-left: 10px;
  padding: 3px 9px;
  border-radius: 999px;
  vertical-align: middle;
  font-size: 0.6em;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.35);
  background: linear-gradient(90deg, #ff3d3d, #ff8a00, #ffd400, #ff8a00, #ff3d3d);
  background-size: 300% 100%;
  box-shadow: 0 0 0 0 rgba(255, 90, 0, 0.6);
  animation: hot-flow 2.4s linear infinite, hot-pulse 1.4s ease-in-out infinite;
}
.hot-badge-sm { margin-left: 6px; padding: 1px 6px; font-size: 0.62rem; }
.nav-item .hot-badge { margin-left: auto; }

@keyframes hot-flow {
  to { background-position: 300% 0; }
}
@keyframes hot-pulse {
  0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 90, 0, 0.55); }
  50% { transform: scale(1.08) rotate(-2deg); box-shadow: 0 0 14px 3px rgba(255, 90, 0, 0.45); }
}
@media (prefers-reduced-motion: reduce) {
  .hot-badge { animation: none; }
}
.feature-para { margin: 0 0 10px; color: var(--text-2); line-height: 1.6; font-size: var(--fs-md); }
.feature-para :deep(code), .feature-points :deep(code) {
  font-family: var(--mono);
  font-size: 0.85em;
  background: var(--field);
  border: 1px solid var(--line-soft);
  border-radius: 5px;
  padding: 1px 5px;
}
.feature-para :deep(strong), .feature-points :deep(strong) { color: var(--text); }
.feature-points {
  margin: 4px 0 0;
  padding-left: 18px;
  color: var(--text-2);
  font-size: var(--fs-md);
  line-height: 1.6;
}
.feature-points li { margin-bottom: 6px; }
.feature-points li::marker { color: var(--accent); }

.feature-code {
  margin: 12px 0 0;
  padding: 12px 14px;
  background: var(--field);
  border: 1px solid var(--line-soft);
  border-radius: var(--r-sm);
  overflow-x: auto;
  font-family: var(--mono);
  font-size: var(--fs-xs);
  line-height: 1.5;
  color: var(--text-2);
}

.feature-shot {
  margin: 0;
  border-radius: var(--r-md);
  overflow: hidden;
  border: 1px solid var(--line);
  box-shadow: 0 14px 40px rgba(0, 0, 0, 0.38);
}
.feature-shot img { display: block; width: 100%; height: auto; }
.feature-shot figcaption {
  padding: 9px 12px;
  font-size: var(--fs-xs);
  color: var(--text-3);
  background: var(--bg-sunken);
  border-top: 1px solid var(--line-soft);
}

@media (max-width: 900px) {
  .feature { grid-template-columns: 1fr; }
  .feature.flip .feature-text { order: 0; }
}

/* Narrow viewports: the rail collapses; brand/back/search return to the
   hero and the sub tabs become a sticky, horizontally scrolling bar. */
@media (max-width: 980px) {
  .guide-nav { display: none; }
  .hero-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 30px;
  }
  .mobile-search { display: flex; margin-bottom: 4px; }
  .chips-bar {
    display: flex;
    position: sticky;
    top: 0;
    z-index: 20;
    flex-wrap: nowrap;
    overflow-x: auto;
    padding: 10px var(--gutter);
    background: color-mix(in srgb, var(--bg-sunken) 88%, transparent);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--line-soft);
    scrollbar-width: none;
  }
  .chips-bar::-webkit-scrollbar { display: none; }
  .chips-bar .chip { flex: none; }
}
</style>
