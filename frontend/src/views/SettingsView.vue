<template>
  <div class="settings-app">
    <aside class="nav">
      <div class="nav-brand">
        <span class="nav-mark"><img :src="'/assets/branding/vdock-logo.jpg'" alt="" class="nav-mark-img" /></span>
        <span class="nav-name">VDock</span>
        <span class="nav-ver">{{ appVersion }}</span>
      </div>
      <div class="nav-search">
        <FontAwesomeIcon :icon="['fas', 'magnifying-glass']" class="nav-search-icon" />
        <label class="sr-only" for="setting-search">Find a setting</label>
        <input
          id="setting-search"
          v-model="settingsSearch"
          type="search"
          placeholder="Find a setting…"
          autocomplete="off"
          @keydown.esc="settingsSearch = ''"
        />
        <div v-if="settingsSearch" class="nav-results">
          <button
            v-for="match in searchMatches"
            :key="match.tabId + (match.subTab || '') + (match.deepTab || '')"
            type="button"
            class="nav-result"
            @click="jumpToSearchResult(match)"
          >
            <FontAwesomeIcon :icon="match.icon" class="nav-result-icon" />
            <span class="nav-result-label">{{ match.label }}</span>
            <span class="nav-result-crumb">{{ searchEntryCrumb(match) }}</span>
          </button>
          <div v-if="!searchMatches.length" class="nav-results-empty">No matching settings</div>
        </div>
      </div>
      <nav class="nav-scroll" aria-label="Settings sections">
        <div class="nav-group">
          <button
            type="button"
            class="nav-item nav-rail-item"
            :class="{ 'is-open': activeTab === 'appearance' }"
            :aria-current="activeTab === 'appearance' ? 'page' : undefined"
            :aria-expanded="activeTab === 'appearance'"
            data-tour="nav-appearance"
            @click="activeTab = 'appearance'"
          >
            <FontAwesomeIcon :icon="['fas', 'palette']" />
            <span>Appearance</span>
            <FontAwesomeIcon :icon="['fas', 'chevron-down']" class="nav-item-chevron" :class="{ 'chevron-open': activeTab === 'appearance' }" />
          </button>
          <Collapse :open="activeTab === 'appearance'">
            <div class="nav-sub" data-tour="appearance-tabs">
              <button
                v-for="sub in appearanceSubs"
                :key="sub.id"
                type="button"
                :aria-current="appearanceSubTab === sub.id ? 'true' : undefined"
                :data-tour="sub.id === 'screensaver' ? 'subtab-screensaver' : undefined"
                @click="selectAppearanceSub(sub.id)"
              >{{ sub.name }}</button>
            </div>
          </Collapse>
        </div>
        <div class="nav-group">
          <button
            type="button"
            class="nav-item nav-rail-item"
            :aria-current="activeTab === 'templates' ? 'page' : undefined"
            data-tour="nav-templates"
            @click="activeTab = 'templates'"
          >
            <FontAwesomeIcon :icon="['fas', 'layer-group']" />
            <span>Templates</span>
          </button>
        </div>
        <div class="nav-group">
          <button
            type="button"
            class="nav-item nav-rail-item"
            :class="{ 'is-open': activeTab === 'server' }"
            :aria-current="activeTab === 'server' ? 'page' : undefined"
            :aria-expanded="activeTab === 'server'"
            data-tour="nav-server"
            @click="activeTab = 'server'"
          >
            <FontAwesomeIcon :icon="['fas', 'server']" />
            <span>Server</span>
            <FontAwesomeIcon :icon="['fas', 'chevron-down']" class="nav-item-chevron" :class="{ 'chevron-open': activeTab === 'server' }" />
          </button>
          <Collapse :open="activeTab === 'server'">
            <div class="nav-sub">
              <button type="button" @click="scrollToPanel('startup')">Startup &amp; navigation</button>
              <button type="button" @click="scrollToPanel('connection')">Connection</button>
            </div>
          </Collapse>
        </div>
        <div class="nav-group">
          <button
            type="button"
            class="nav-item nav-rail-item"
            :aria-current="activeTab === 'integration' ? 'page' : undefined"
            data-tour="nav-integration"
            @click="activeTab = 'integration'"
          >
            <FontAwesomeIcon :icon="['fas', 'plug']" />
            <span>Integrations</span>
          </button>
        </div>
        <div class="nav-group">
          <button
            type="button"
            class="nav-item nav-rail-item"
            :aria-current="activeTab === 'connect' ? 'page' : undefined"
            data-tour="nav-connect"
            @click="activeTab = 'connect'"
          >
            <FontAwesomeIcon :icon="['fas', 'mobile-screen-button']" />
            <span>Connect a device</span>
          </button>
        </div>
        <div class="nav-group">
          <button
            type="button"
            class="nav-item nav-rail-item"
            :aria-current="activeTab === 'logs' ? 'page' : undefined"
            data-tour="nav-logs"
            @click="activeTab = 'logs'"
          >
            <FontAwesomeIcon :icon="['fas', 'file-lines']" />
            <span>Logs</span>
          </button>
        </div>
        <div class="nav-group">
          <button
            type="button"
            class="nav-item nav-rail-item"
            :aria-current="activeTab === 'about' ? 'page' : undefined"
            data-tour="nav-about"
            @click="activeTab = 'about'"
          >
            <FontAwesomeIcon :icon="['fas', 'circle-info']" />
            <span>About</span>
          </button>
        </div>
      </nav>
      <div class="nav-foot">
        <button type="button" class="btn ghost sm nav-foot-btn" title="Reload profile and settings from the server" @click="refreshVdock()">
          <FontAwesomeIcon :icon="['fas', 'arrows-rotate']" /> Reload VDock
        </button>
        <button type="button" class="btn ghost sm nav-foot-btn" @click="handleSettingsBack">
          <FontAwesomeIcon :icon="['fas', isStandaloneSettings ? 'xmark' : 'arrow-left']" />
          {{ isStandaloneSettings ? 'Close' : 'Back' }}
        </button>
      </div>
    </aside>

    <main ref="mainEl" class="main">
      <header class="topbar">
        <div class="topbar-text">
          <p class="crumb">{{ topbarMeta.crumb }}</p>
          <h1>{{ topbarMeta.title }}</h1>
          <p>{{ topbarMeta.blurb }}</p>
        </div>
        <div class="topbar-actions">
          <button
            v-if="!isStandaloneSettings"
            type="button"
            class="btn ghost sm"
            title="Open only the settings panel in your browser so VDock stays on the dashboard"
            @click="openSettingsInBrowserTab"
          >
            <FontAwesomeIcon :icon="['fas', 'up-right-from-square']" /> Open in browser
          </button>
          <button
            v-if="activeTab === 'appearance'"
            type="button"
            class="btn ghost sm"
            @click="resetAppearanceSection"
          >
            <FontAwesomeIcon :icon="['fas', 'rotate-left']" /> Reset section
          </button>
        </div>
      </header>

        <!-- ── Appearance → Buttons ── -->
        <div v-if="activeTab === 'appearance' && appearanceSubTab === 'buttons'" class="content has-rail">
          <div class="col">
            <section class="panel" id="sizing">
              <div class="panel-head">
                <h2>Sizing &amp; touch</h2>
                <span class="hint">How big every key is. Touch mode and button size multiply.</span>
              </div>
              <div class="panel-body">
                <div class="row" id="touch">
                  <div class="row-text">
                    <span class="label">Touch mode</span>
                    <p>Scales hit targets for finger input. Presets set the multiplier, minimum target and key height together.</p>
                  </div>
                  <div class="row-control">
                    <div class="seg" role="radiogroup" aria-label="Touch mode">
                      <label><input type="radio" value="normal" v-model="settings.touchMode" /><span>Normal</span><span class="sub">1.0×</span></label>
                      <label><input type="radio" value="touch-friendly" v-model="settings.touchMode" /><span>Touch-friendly</span><span class="sub">1.5×</span></label>
                      <label><input type="radio" value="tablet" v-model="settings.touchMode" /><span>Tablet</span><span class="sub">2.0×</span></label>
                    </div>
                    <SettingResetButton label="Touch mode" :at-default="settings.touchMode === SETTINGS_DEFAULTS.touchMode" @reset="settings.touchMode = SETTINGS_DEFAULTS.touchMode" />
                  </div>
                </div>
                <div class="row">
                  <div class="row-text">
                    <span class="label">Resolved targets</span>
                    <p>Derived from the preset — override the minimum under Advanced.</p>
                  </div>
                  <div class="row-control">
                    <div class="chips">
                      <span class="chip">Multiplier <b>{{ settingsStore.touchModeMultiplier }}×</b></span>
                      <span class="chip">Min target <b>{{ settingsStore.minimumTouchTargetSize }}px</b></span>
                      <span class="chip">Key height <b>{{ resolvedKeyHeight }}px</b></span>
                    </div>
                    <button type="button" class="btn quiet sm" :aria-expanded="touchAdvancedOpen" @click="touchAdvancedOpen = !touchAdvancedOpen">
                      Advanced <FontAwesomeIcon :icon="['fas', 'chevron-down']" class="chev" :class="{ 'chevron-open': touchAdvancedOpen }" />
                    </button>
                  </div>
                </div>
                <Collapse :open="touchAdvancedOpen">
                  <div class="row stack row-inset">
                    <div class="row-head">
                      <div class="row-text">
                        <span class="label">Minimum touch target</span>
                        <p>WCAG 2.1 AA asks for at least 44px.</p>
                      </div>
                    </div>
                    <div class="row-control">
                      <div class="slider">
                        <span class="cap">24px</span>
                        <input type="range" min="24" max="64" step="4" v-model.number="settingsStore.minimumTouchTargetSize" :style="sliderFill(settingsStore.minimumTouchTargetSize, 24, 64)" aria-label="Minimum touch target" />
                        <span class="cap">64px</span>
                        <span class="val">{{ settingsStore.minimumTouchTargetSize }}px</span>
                      </div>
                    </div>
                  </div>
                </Collapse>
                <div class="row stack">
                  <div class="row-head">
                    <div class="row-text">
                      <span class="label">Button size</span>
                      <p>Resizes the key box and its icon inside the grid cell. Below 1× keys shrink; above 1× they grow into the gaps.</p>
                    </div>
                    <SettingResetButton label="Button size" :at-default="settings.buttonSize === SETTINGS_DEFAULTS.buttonSize" @reset="settings.buttonSize = SETTINGS_DEFAULTS.buttonSize" />
                  </div>
                  <div class="row-control">
                    <div class="slider">
                      <span class="cap">0.5×</span>
                      <input v-model.number="settings.buttonSize" type="range" min="0.5" max="2" step="0.1" :style="sliderFill(settings.buttonSize, 0.5, 2)" aria-label="Button size" />
                      <span class="cap">2×</span>
                      <span class="val">{{ settings.buttonSize.toFixed(1) }}×</span>
                    </div>
                  </div>
                </div>
                <div class="row stack">
                  <div class="row-head">
                    <div class="row-text">
                      <span class="label">Button transparency</span>
                      <p>Lets the dashboard background show through the keys. Capped at 90% so keys stay findable.</p>
                    </div>
                    <SettingResetButton label="Button transparency" :at-default="settings.buttonTransparency === SETTINGS_DEFAULTS.buttonTransparency" @reset="settings.buttonTransparency = SETTINGS_DEFAULTS.buttonTransparency" />
                  </div>
                  <div class="row-control">
                    <div class="slider">
                      <span class="cap">0%</span>
                      <input v-model.number="settings.buttonTransparency" type="range" min="0" max="90" step="5" :style="sliderFill(settings.buttonTransparency, 0, 90)" aria-label="Button transparency" />
                      <span class="cap">90%</span>
                      <span class="val">{{ settings.buttonTransparency }}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section class="panel" id="design">
              <div class="panel-head">
                <h2>Key design</h2>
                <span class="hint">The default face for every key.</span>
                <span class="spacer"></span>
                <SettingResetButton label="Button design" :at-default="previewEffect === SETTINGS_DEFAULTS.buttonDefaultEffect" @reset="resetButtonDefault('buttonDefaultEffect')" />
              </div>
              <div class="panel-body">
                <div class="row stack design-row">
                  <ButtonDesignPicker v-model="previewEffect" />
                </div>
              </div>
            </section>

            <section class="panel" id="motion">
              <div class="panel-head"><h2>Motion</h2><span class="hint">Press animation and idle icon motion.</span></div>
              <div class="panel-body">
                <div class="row">
                  <div class="row-text">
                    <span class="label">Button animation</span>
                    <p>Plays when a key is pressed.</p>
                  </div>
                  <div class="row-control">
                    <select v-model="previewAnimation" class="select w-220" aria-label="Button animation">
                      <option value="none">None</option>
                      <option value="pulse">Pulse</option>
                      <option value="shimmer">Shimmer</option>
                      <option value="bounce">Bounce</option>
                      <option value="rotate">Rotate</option>
                      <option value="wiggle">Wiggle</option>
                      <option value="float">Float</option>
                      <option value="scale">Scale</option>
                      <option value="slide">Slide</option>
                      <option value="fade">Fade</option>
                      <option value="spin">Spin</option>
                    </select>
                    <SettingResetButton label="Button animation" :at-default="previewAnimation === SETTINGS_DEFAULTS.buttonDefaultAnimation" @reset="resetButtonDefault('buttonDefaultAnimation')" />
                  </div>
                </div>
                <div class="row">
                  <div class="row-text">
                    <span class="label">Icon animation</span>
                    <p>Loops on the icon while the key is idle.</p>
                  </div>
                  <div class="row-control">
                    <select v-model="previewIconLoop" class="select w-220" aria-label="Icon animation">
                      <option value="none">None</option>
                      <option value="squash">Squash</option>
                      <option value="bob">Bob</option>
                      <option value="spin">Spin</option>
                      <option value="pulse">Pulse</option>
                      <option value="swing">Swing</option>
                      <option value="flip">Flip</option>
                      <option value="jump">Jump</option>
                    </select>
                    <SettingResetButton label="Icon animation" :at-default="previewIconLoop === SETTINGS_DEFAULTS.buttonDefaultIconLoop" @reset="resetButtonDefault('buttonDefaultIconLoop')" />
                  </div>
                </div>
                <div class="row">
                  <div class="row-text">
                    <span class="label">Enable animations</span>
                    <p>Master switch — off disables both of the above without losing them.</p>
                  </div>
                  <div class="row-control">
                    <label class="switch"><span class="sr-only">Enable animations</span><input v-model="settings.animationsEnabled" type="checkbox" /><span class="track"></span></label>
                    <SettingResetButton label="Enable animations" :at-default="settings.animationsEnabled === SETTINGS_DEFAULTS.animationsEnabled" @reset="settings.animationsEnabled = SETTINGS_DEFAULTS.animationsEnabled" />
                  </div>
                </div>
                <div class="row">
                  <div class="row-text">
                    <span class="label">Wiggle buttons in edit mode</span>
                    <p>A gentle shake shows keys are draggable while editing.</p>
                  </div>
                  <div class="row-control">
                    <label class="switch"><span class="sr-only">Wiggle buttons in edit mode</span><input v-model="settings.editModeWiggle" type="checkbox" /><span class="track"></span></label>
                    <SettingResetButton label="Wiggle buttons in edit mode" :at-default="settings.editModeWiggle === SETTINGS_DEFAULTS.editModeWiggle" @reset="settings.editModeWiggle = SETTINGS_DEFAULTS.editModeWiggle" />
                  </div>
                </div>
                <div class="row">
                  <div class="row-text">
                    <span class="label">3D tilt effect</span>
                    <p>Keys tilt toward the pointer on hover.</p>
                  </div>
                  <div class="row-control">
                    <label class="switch"><span class="sr-only">3D tilt effect</span><input v-model="settings.tiltEffectEnabled" type="checkbox" /><span class="track"></span></label>
                    <SettingResetButton label="3D tilt effect" :at-default="settings.tiltEffectEnabled === SETTINGS_DEFAULTS.tiltEffectEnabled" @reset="settings.tiltEffectEnabled = SETTINGS_DEFAULTS.tiltEffectEnabled" />
                  </div>
                </div>
              </div>
            </section>

            <section class="panel" id="feedback">
              <div class="panel-head"><h2>Labels &amp; feedback</h2></div>
              <div class="panel-body">
                <div class="row">
                  <div class="row-text">
                    <span class="label">Show button labels</span>
                    <p>Draws the label under each icon.</p>
                  </div>
                  <div class="row-control">
                    <label class="switch"><span class="sr-only">Show button labels</span><input v-model="settings.showLabels" type="checkbox" /><span class="track"></span></label>
                    <SettingResetButton label="Show button labels" :at-default="settings.showLabels === SETTINGS_DEFAULTS.showLabels" @reset="settings.showLabels = SETTINGS_DEFAULTS.showLabels" />
                  </div>
                </div>
                <div class="row">
                  <div class="row-text">
                    <span class="label">Show tooltips</span>
                    <p>Reveals the full action on hover — useful when labels are hidden.</p>
                  </div>
                  <div class="row-control">
                    <label class="switch"><span class="sr-only">Show tooltips</span><input v-model="settings.showTooltips" type="checkbox" /><span class="track"></span></label>
                    <SettingResetButton label="Show tooltips" :at-default="settings.showTooltips === SETTINGS_DEFAULTS.showTooltips" @reset="settings.showTooltips = SETTINGS_DEFAULTS.showTooltips" />
                  </div>
                </div>
                <div class="row">
                  <div class="row-text">
                    <span class="label">Press sound</span>
                    <p>A short click on every press — makes the panel feel physical.</p>
                  </div>
                  <div class="row-control">
                    <label class="switch"><span class="sr-only">Press sound</span><input v-model="settings.pressSoundEnabled" type="checkbox" /><span class="track"></span></label>
                    <SettingResetButton label="Press sound" :at-default="settings.pressSoundEnabled === SETTINGS_DEFAULTS.pressSoundEnabled" @reset="settings.pressSoundEnabled = SETTINGS_DEFAULTS.pressSoundEnabled" />
                  </div>
                </div>
                <div class="row" v-if="settings.pressSoundEnabled">
                  <div class="row-text">
                    <span class="label">Sound style</span>
                    <p>None silences presses without losing the setting.</p>
                  </div>
                  <div class="row-control">
                    <select v-model="settings.pressSoundStyle" class="select w-220" aria-label="Sound style">
                      <option value="click">Click</option>
                      <option value="blip">Blip</option>
                      <option value="pop">Pop</option>
                      <option value="none">None</option>
                    </select>
                  </div>
                </div>
              </div>
            </section>

            <div class="note warn">
              <FontAwesomeIcon :icon="['fas', 'triangle-exclamation']" />
              <div>
                Animation, icon motion and key design are drafts until <b>Save &amp; Apply</b>.
                <button type="button" class="btn sm warn-apply" :disabled="applyingButtonBehaviour" @click="applyButtonBehaviourToAll">
                  <FontAwesomeIcon :icon="['fas', applyingButtonBehaviour ? 'spinner' : 'wand-magic-sparkles']" :spin="applyingButtonBehaviour" />
                  {{ applyingButtonBehaviour ? 'Applying…' : 'Apply to every existing key' }}
                </button>
                rewrites all buttons, including per-key customisation.
              </div>
            </div>
          </div>

          <div class="rail">
            <div class="preview">
              <div class="preview-head"><FontAwesomeIcon :icon="['fas', 'eye']" /> Live preview</div>
              <div class="preview-stage preview-stage-bg" :class="previewBackgroundClass" :style="previewBackgroundStyle">
                <DeckButton
                  :button="previewButton"
                  :show-labels="settings.showLabels"
                  :show-tooltips="settings.showTooltips"
                  :button-size="settings.buttonSize * settingsStore.touchModeMultiplier"
                  style="width: 110px; height: 110px;"
                />
              </div>
              <div class="preview-foot">Reflects size, labels, tooltips, touch mode, design and the dashboard background.</div>
            </div>
            <div class="preview">
              <div class="preview-head">In context</div>
              <div class="preview-stage preview-stage-grid">
                <div class="mock-grid">
                  <span v-for="i in 12" :key="i" class="mock-key" :style="{ transform: `scale(${Math.min(settings.buttonSize * settingsStore.touchModeMultiplier, 1)})`, opacity: String(1 - settings.buttonTransparency / 130) }"></span>
                </div>
              </div>
              <div class="preview-foot">4 × 3 grid at the current size and transparency.</div>
            </div>
          </div>
        </div>

        <!-- ── Appearance → Layout & sidebar ── -->
        <div v-else-if="activeTab === 'appearance' && appearanceSubTab === 'layout'" class="content has-rail">
          <div class="col">
            <section class="panel" id="typography">
              <div class="panel-head">
                <h2>Typography</h2>
                <span class="hint">Button labels, scene pills and the sidebar. The screensaver keeps its own fonts.</span>
                <span class="spacer"></span>
                <SettingResetButton label="Dashboard font" :at-default="settingsStore.dashboardFont === SETTINGS_DEFAULTS.dashboardFont" @reset="settingsStore.dashboardFont = SETTINGS_DEFAULTS.dashboardFont" />
              </div>
              <div class="panel-body">
                <div class="row stack picker-row">
                  <div class="picker picker-3 font-style-picker">
                    <label v-for="opt in dashboardFontOptions" :key="opt.value" class="pick specimen">
                      <input type="radio" :value="opt.value" v-model="settingsStore.dashboardFont" />
                      <span class="tick"><FontAwesomeIcon :icon="['fas', 'check']" /></span>
                      <span class="aa" :style="{ fontFamily: opt.family }">Aa</span>
                      <span class="num" :style="{ fontFamily: opt.family }">12:34</span>
                      <span>{{ opt.name }}</span>
                    </label>
                  </div>
                </div>
              </div>
            </section>

            <section class="panel" id="sidebar">
              <div class="panel-head"><h2>Docked sidebar</h2><span class="hint">A permanent column of keys down the left of the dashboard.</span></div>
              <div class="panel-body">
                <div class="row">
                  <div class="row-text">
                    <span class="label">Show docked sidebar</span>
                    <p>A permanent column of scene and macro keys down the left of the dashboard.</p>
                  </div>
                  <div class="row-control">
                    <label class="switch"><span class="sr-only">Show docked sidebar</span><input v-model="settings.dockedSidebarEnabled" type="checkbox" /><span class="track"></span></label>
                    <SettingResetButton label="Show docked sidebar" :at-default="settings.dockedSidebarEnabled === SETTINGS_DEFAULTS.dockedSidebarEnabled" @reset="settings.dockedSidebarEnabled = SETTINGS_DEFAULTS.dockedSidebarEnabled" />
                  </div>
                </div>
                <template v-if="settings.dockedSidebarEnabled">
                  <div class="row stack">
                    <div class="row-head">
                      <div class="row-text">
                        <span class="label">Sidebar width</span>
                        <p>How much horizontal space the docked column takes.</p>
                      </div>
                      <SettingResetButton label="Sidebar width" :at-default="settings.dockedSidebarWidth === SETTINGS_DEFAULTS.dockedSidebarWidth" @reset="settings.dockedSidebarWidth = SETTINGS_DEFAULTS.dockedSidebarWidth" />
                    </div>
                    <div class="row-control">
                      <div class="slider">
                        <span class="cap">80px</span>
                        <input v-model.number="settings.dockedSidebarWidth" type="range" min="80" max="360" step="10" :style="sliderFill(settings.dockedSidebarWidth, 80, 360)" aria-label="Sidebar width" />
                        <span class="cap">360px</span>
                        <span class="val">{{ settings.dockedSidebarWidth }}px</span>
                      </div>
                    </div>
                  </div>
                  <div class="row stack">
                    <div class="row-head">
                      <div class="row-text">
                        <span class="label">Button height</span>
                        <p>Height of each docked key. Shrinks automatically if the column runs out of room.</p>
                      </div>
                      <SettingResetButton label="Button height" :at-default="settings.dockedButtonHeight === SETTINGS_DEFAULTS.dockedButtonHeight" @reset="settings.dockedButtonHeight = SETTINGS_DEFAULTS.dockedButtonHeight" />
                    </div>
                    <div class="row-control">
                      <div class="slider">
                        <span class="cap">48px</span>
                        <input v-model.number="settings.dockedButtonHeight" type="range" min="48" max="160" step="4" :style="sliderFill(settings.dockedButtonHeight, 48, 160)" aria-label="Docked button height" />
                        <span class="cap">160px</span>
                        <span class="val">{{ settings.dockedButtonHeight }}px</span>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </section>

            <section class="panel" id="notifications">
              <div class="panel-head"><h2>Notifications</h2></div>
              <div class="panel-body">
                <div class="row">
                  <div class="row-text">
                    <span class="label">Toast notifications</span>
                    <p>Which action results pop up over the dashboard.</p>
                  </div>
                  <div class="row-control">
                    <div class="seg" role="radiogroup" aria-label="Toast level">
                      <label v-for="opt in toastLevelOptions" :key="opt.value"><input type="radio" :value="opt.value" v-model="settings.toastLevel" /><span>{{ opt.label }}</span></label>
                    </div>
                    <SettingResetButton label="Toast notifications" :at-default="settings.toastLevel === SETTINGS_DEFAULTS.toastLevel" @reset="settings.toastLevel = SETTINGS_DEFAULTS.toastLevel" />
                  </div>
                </div>
              </div>
            </section>
          </div>

          <div class="rail">
            <div class="preview">
              <div class="preview-head"><FontAwesomeIcon :icon="['fas', 'eye']" /> Dashboard preview</div>
              <div class="preview-stage preview-stage-grid" :style="{ fontFamily: dashboardFontFamily }">
                <div class="mock-dash">
                  <div v-if="settings.dockedSidebarEnabled" class="mock-dash-side" :style="{ width: `${Math.round(settings.dockedSidebarWidth * 0.3)}px` }">
                    <span v-for="i in 3" :key="i" class="mock-key side" :style="{ height: `${Math.round(settings.dockedButtonHeight * 0.4)}px` }"></span>
                  </div>
                  <div class="mock-dash-grid">
                    <span v-for="i in 12" :key="i" class="mock-key"></span>
                  </div>
                </div>
              </div>
              <div class="preview-foot">
                {{ settings.dockedSidebarEnabled ? `Sidebar at ${settings.dockedSidebarWidth}px, keys at ${settings.dockedButtonHeight}px` : 'Sidebar hidden' }} — {{ dashboardFontOptions.find(o => o.value === settingsStore.dashboardFont)?.name }}.
              </div>
            </div>
          </div>
        </div>

        <!-- ── Appearance → Background ── -->
        <div v-else-if="activeTab === 'appearance' && appearanceSubTab === 'background'" class="content has-rail">
          <div class="col">
            <section class="panel" id="dashboard-bg">
              <div class="panel-head">
                <h2>Dashboard background</h2>
                <span class="hint">One background for the whole dashboard — animated effects included.</span>
                <span class="spacer"></span>
                <SettingResetButton label="Background style" :at-default="settings.background === SETTINGS_DEFAULTS.background" @reset="settings.background = SETTINGS_DEFAULTS.background" />
              </div>
              <div class="panel-body">
                <div class="row stack picker-row">
                  <BackgroundPicker
                    v-model="settings.background"
                    :groups="backgroundPickerGroups"
                    @change="settingsStore.saveSettings()"
                  />
                </div>
                <div class="row stack">
                  <div class="row-head">
                    <div class="row-text">
                      <span class="label">Custom image or GIF</span>
                      <p>PNG, JPG, WEBP or GIF. Replaces the style above.</p>
                    </div>
                  </div>
                  <div class="row-control">
                    <div class="drop">
                      <FontAwesomeIcon :icon="['fas', 'upload']" />
                      <span>{{ isCustomBackground ? 'A custom image is active.' : 'Drop a file here, or browse. Animated GIFs loop behind the keys.' }}</span>
                      <input ref="backgroundFileInput" type="file" accept="image/*,.gif" @change="handleBackgroundUpload" style="display:none" />
                      <button type="button" class="btn sm" :disabled="uploadingBackground" @click="($refs.backgroundFileInput as HTMLInputElement).click()">
                        <FontAwesomeIcon :icon="uploadingBackground ? ['fas', 'spinner'] : ['fas', 'upload']" :spin="uploadingBackground" />
                        {{ uploadingBackground ? 'Uploading…' : 'Choose file…' }}
                      </button>
                      <button v-if="isCustomBackground" type="button" class="btn danger sm" @click="removeCustomBackground">
                        <FontAwesomeIcon :icon="['fas', 'trash']" /> Remove
                      </button>
                    </div>
                  </div>
                  <div v-if="isCustomBackground" class="bg-thumb">
                    <img :src="settings.background" alt="Custom background" />
                  </div>
                </div>
              </div>
            </section>

            <section class="panel" id="scene-bg">
              <div class="panel-head">
                <h2>Per-scene overrides</h2>
                <span class="hint">A scene can replace the dashboard background while it is open.</span>
              </div>
              <div class="panel-body">
                <input ref="sceneBackgroundFileInput" type="file" accept="image/*,.gif" @change="handleSceneBackgroundUpload" style="display:none" />
                <div v-for="scene in sceneList" :key="scene.id" class="row">
                  <div class="row-text">
                    <span class="label">{{ scene.name }}<span v-if="currentScene?.id === scene.id" class="chip row-now">current</span></span>
                    <p>{{ sceneBackgroundDesc(scene) }}</p>
                  </div>
                  <div class="row-control">
                    <img v-if="sceneEffectiveImage(scene)" :src="sceneEffectiveImage(scene)" class="scene-thumb" :alt="`${scene.name} background`" />
                    <label v-if="sceneAppEntryFor(scene) && !scene.background?.image" class="switch" :title="`Use the bundled ${sceneAppEntryFor(scene)!.label} artwork`">
                      <span class="sr-only">Use app default for {{ scene.name }}</span>
                      <input type="checkbox" :checked="!scene.disableAppBackground" @change="toggleAppDefaultBackgroundFor(scene, $event)" />
                      <span class="track"></span>
                    </label>
                    <button type="button" class="btn sm" :disabled="uploadingSceneBackground" @click="pickSceneBackground(scene)">
                      {{ scene.background?.image ? 'Change…' : 'Set background' }}
                    </button>
                    <button v-if="scene.background?.image" type="button" class="btn quiet sm" :title="`Remove ${scene.name} override`" @click="removeSceneBackgroundFor(scene)">
                      <FontAwesomeIcon :icon="['fas', 'trash']" />
                    </button>
                  </div>
                </div>
                <p v-if="!sceneList.length" class="muted row-empty">No scenes in this profile yet — add one on the dashboard.</p>
              </div>
            </section>

            <div class="note">
              <FontAwesomeIcon :icon="['fas', 'circle-info']" />
              <div>
                Looking for the screensaver background? It lives with the rest of the screensaver, under
                <a href="#" @click.prevent="appearanceSubTab = 'screensaver'; scrollToPanel('ss-background')">Appearance → Screen saver</a>.
              </div>
            </div>
          </div>

          <div class="rail">
            <div class="preview">
              <div class="preview-head"><FontAwesomeIcon :icon="['fas', 'eye']" /> Preview</div>
              <div ref="bgPreviewStage" class="preview-stage preview-stage-bg preview-stage-bg-tall" :class="previewBackgroundClass" :style="previewBackgroundStyle">
                <!-- Component-kind backgrounds are position:fixed 100vw×100vh —
                     a transformed wrapper becomes their containing block, so a
                     viewport-sized inner stage scaled down renders the real
                     effect inside the rail instead of a checkerboard. -->
                <div v-if="previewBgComponent" class="preview-bg-clip">
                  <div class="preview-bg-viewport" :style="{ transform: `scale(${bgPreviewScale})` }">
                    <component :is="previewBgComponent" :key="settingsStore.background" :on-error="onPreviewBgError" />
                  </div>
                </div>
                <div class="mock-grid mock-grid-ghost">
                  <span v-for="i in 6" :key="i" class="mock-key ghost"></span>
                </div>
              </div>
              <div class="preview-foot">{{ backgroundPickerGroups.flatMap(g => g.options).find(o => o.id === settings.background)?.label ?? 'Custom' }} at {{ settings.buttonTransparency }}% key transparency.</div>
            </div>
          </div>
        </div>

        <!-- ── Appearance → Screen saver ── -->
        <div v-else-if="activeTab === 'appearance' && appearanceSubTab === 'screensaver'" class="content has-rail">
          <div class="col">
            <section class="panel" id="ss-activation">
              <div class="panel-head"><h2>Activation</h2></div>
              <div class="panel-body">
                <div class="row stack">
                  <div class="row-head">
                    <div class="row-text">
                      <span class="label">Idle delay</span>
                      <p>Time before the screensaver appears. 0 disables it entirely.</p>
                    </div>
                    <SettingResetButton label="Idle delay" :at-default="settingsStore.screensaverTimeout === SETTINGS_DEFAULTS.screensaverTimeout" @reset="settingsStore.screensaverTimeout = SETTINGS_DEFAULTS.screensaverTimeout" />
                  </div>
                  <div class="row-control">
                    <div class="slider">
                      <span class="cap">Off</span>
                      <input type="range" min="0" max="600" step="30" :value="settingsStore.screensaverTimeout" @input="settingsStore.screensaverTimeout = Number(($event.target as HTMLInputElement).value)" :style="sliderFill(settingsStore.screensaverTimeout, 0, 600)" aria-label="Idle delay" />
                      <span class="cap">10m</span>
                      <span class="val">{{ settingsStore.screensaverTimeout === 0 ? 'Off' : formatScreensaverTimeout(settingsStore.screensaverTimeout) }}</span>
                    </div>
                  </div>
                </div>
                <div class="row">
                  <div class="row-text">
                    <span class="label">Try it</span>
                    <p>Test shows the screensaver even when the delay is off. Customise opens a live editor — drag widgets to move them, drag a corner to resize.</p>
                  </div>
                  <div class="row-control">
                    <button type="button" class="btn sm" @click="handleTestScreensaver"><FontAwesomeIcon :icon="['fas', 'display']" /> Test</button>
                    <button type="button" class="btn sm" @click="handleCustomizeScreensaverLayout"><FontAwesomeIcon :icon="['fas', 'up-down-left-right']" /> Customise layout</button>
                  </div>
                </div>
              </div>
            </section>

            <section class="panel" id="ss-widgets" data-tour="screensaver-picker">
              <div class="panel-head">
                <h2>Widgets</h2>
                <span class="hint">What shows besides the clock. Each row opens its own settings.</span>
                <span class="spacer"></span>
                <SettingResetButton label="Screensaver widgets" :at-default="screensaverWidgetsAtDefault" @reset="resetScreensaverWidgets" />
              </div>
              <div class="panel-body">
                <div class="row">
                  <div class="row-text">
                    <span class="label">Clock</span>
                    <p>Large time and date. Always drawn.</p>
                  </div>
                  <div class="row-control">
                    <label class="switch"><span class="sr-only">Clock</span><input type="checkbox" checked disabled /><span class="track"></span></label>
                  </div>
                </div>
                <template v-for="w in screensaverWidgetOptions" :key="w.id">
                  <div class="row">
                    <div class="row-text">
                      <span class="label">{{ w.label }}</span>
                      <p>{{ w.description }}</p>
                    </div>
                    <div class="row-control">
                      <button
                        v-if="settingsStore.screensaverWidgets.includes(w.id)"
                        type="button"
                        class="btn quiet sm"
                        :aria-expanded="openWidgetCard === w.id"
                        @click="toggleWidgetCard(w.id)"
                      >
                        Options
                        <FontAwesomeIcon :icon="['fas', 'chevron-down']" class="chev" :class="{ 'chevron-open': openWidgetCard === w.id }" />
                      </button>
                      <label class="switch">
                        <span class="sr-only">{{ w.label }}</span>
                        <input type="checkbox" :checked="settingsStore.screensaverWidgets.includes(w.id)" @change="toggleScreensaverWidget(w.id)" />
                        <span class="track"></span>
                      </label>
                    </div>
                  </div>
                  <Collapse v-if="settingsStore.screensaverWidgets.includes(w.id)" :open="openWidgetCard === w.id">
                    <div class="row stack row-inset widget-detail">
                      <!-- weather: location + widget size -->
                      <template v-if="w.id === 'weather'">
                        <div class="grid-3">
                          <label class="stack-8">
                            <span class="muted field-label">Location</span>
                            <select v-model="settings.weatherLocationMode" class="select" aria-label="Weather location source">
                              <option value="auto">Use my current location</option>
                              <option value="manual">Set a city manually</option>
                            </select>
                          </label>
                          <label v-if="settings.weatherLocationMode === 'manual'" class="stack-8">
                            <span class="muted field-label">City</span>
                            <input v-model="settings.weatherManualCity" type="text" class="input" placeholder="e.g. Tel Aviv" @keyup.enter="refreshWeatherWidget" />
                          </label>
                          <label class="stack-8">
                            <span class="muted field-label">Widget size <b class="val-inline">{{ settingsStore.screensaverWeatherSize }}%</b></span>
                            <input type="range" min="50" max="300" step="10" :value="settingsStore.screensaverWeatherSize" @input="settingsStore.screensaverWeatherSize = Number(($event.target as HTMLInputElement).value)" :style="sliderFill(settingsStore.screensaverWeatherSize, 50, 300)" class="slider-bare" aria-label="Weather widget size" />
                          </label>
                        </div>
                        <p v-if="settings.weatherLocationMode !== 'manual'" class="muted field-note">Uses your browser location — falls back to a manual city if denied. Also feeds the docked weather card.</p>
                      </template>
                      <!-- news -->
                      <template v-else-if="w.id === 'news'">
                        <div class="stack-12">
                          <label class="stack-8">
                            <span class="muted field-label">Feed URLs — one RSS or Atom URL per line; blank uses the built-in sources</span>
                            <textarea v-model="settingsStore.newsFeeds" class="input textarea" rows="3" placeholder="https://feeds.bbci.co.uk/news/world/rss.xml&#10;https://hnrss.org/frontpage"></textarea>
                          </label>
                          <div class="widget-detail-foot">
                            <label class="stack-8 field-inline">
                              <span class="muted field-label">Seconds per headline</span>
                              <input v-model.number="settingsStore.newsRotateSeconds" type="number" min="3" max="60" class="input w-110" />
                            </label>
                            <button type="button" class="btn sm" :disabled="testingNews" @click="handleTestNews">
                              <FontAwesomeIcon :icon="['fas', testingNews ? 'spinner' : 'plug']" :spin="testingNews" /> Test feeds
                            </button>
                            <SettingResetButton label="News feeds" :at-default="settingsStore.newsFeeds === SETTINGS_DEFAULTS.newsFeeds && settingsStore.newsRotateSeconds === SETTINGS_DEFAULTS.newsRotateSeconds" @reset="settingsStore.newsFeeds = SETTINGS_DEFAULTS.newsFeeds; settingsStore.newsRotateSeconds = SETTINGS_DEFAULTS.newsRotateSeconds" />
                          </div>
                          <p v-if="newsTestResult" class="test-result" :class="{ ok: newsTestResult.ok }">
                            <FontAwesomeIcon :icon="['fas', newsTestResult.ok ? 'circle-check' : 'circle-exclamation']" /> {{ newsTestResult.text }}
                          </p>
                        </div>
                      </template>
                      <!-- sports -->
                      <template v-else-if="w.id === 'sports'">
                        <div class="stack-12">
                          <label class="stack-8">
                            <span class="muted field-label">Feed URLs — blank uses ESPN, BBC Sport and Sky Sports</span>
                            <textarea v-model="settingsStore.sportsFeeds" class="input textarea" rows="3" placeholder="https://www.espn.com/espn/rss/news&#10;https://feeds.bbci.co.uk/sport/rss.xml"></textarea>
                          </label>
                          <div class="widget-detail-foot">
                            <button type="button" class="btn sm" :disabled="testingSports" @click="handleTestSports">
                              <FontAwesomeIcon :icon="['fas', testingSports ? 'spinner' : 'plug']" :spin="testingSports" /> Test feeds
                            </button>
                            <SettingResetButton label="Sports feeds" :at-default="settingsStore.sportsFeeds === SETTINGS_DEFAULTS.sportsFeeds" @reset="settingsStore.sportsFeeds = SETTINGS_DEFAULTS.sportsFeeds" />
                          </div>
                          <p v-if="sportsTestResult" class="test-result" :class="{ ok: sportsTestResult.ok }">
                            <FontAwesomeIcon :icon="['fas', sportsTestResult.ok ? 'circle-check' : 'circle-exclamation']" /> {{ sportsTestResult.text }}
                          </p>
                        </div>
                      </template>
                      <!-- market -->
                      <template v-else-if="w.id === 'market'">
                        <div class="stack-12">
                          <label class="stack-8">
                            <span class="muted field-label">Symbols — comma-separated stock tickers and crypto, mixable</span>
                            <input v-model="settingsStore.marketTickers" type="text" class="input" placeholder="BTC, ETH, AAPL, MSFT, NVDA" />
                          </label>
                          <div class="widget-detail-foot">
                            <button type="button" class="btn sm" :disabled="testingMarket" @click="handleTestMarket">
                              <FontAwesomeIcon :icon="['fas', testingMarket ? 'spinner' : 'plug']" :spin="testingMarket" /> Test connection
                            </button>
                            <SettingResetButton label="Market symbols" :at-default="settingsStore.marketTickers === SETTINGS_DEFAULTS.marketTickers" @reset="settingsStore.marketTickers = SETTINGS_DEFAULTS.marketTickers" />
                          </div>
                          <p v-if="marketTestResult" class="test-result" :class="{ ok: marketTestResult.ok }">
                            <FontAwesomeIcon :icon="['fas', marketTestResult.ok ? 'circle-check' : 'circle-exclamation']" /> {{ marketTestResult.text }}
                          </p>
                        </div>
                      </template>
                      <!-- world clock -->
                      <template v-else-if="w.id === 'worldclock'">
                        <div class="stack-12">
                          <label class="stack-8">
                            <span class="muted field-label">Cities — one per line: a city name, an IANA zone, or Label=Zone</span>
                            <textarea v-model="settingsStore.worldClockTimezones" class="input textarea" rows="3" :placeholder="'Tel Aviv\nLondon\nHome Office=America/New_York\nAsia/Tokyo'"></textarea>
                          </label>
                          <div class="widget-detail-foot">
                            <span class="muted field-note">Blank shows New York, London and Tokyo.</span>
                            <SettingResetButton label="World clock cities" :at-default="settingsStore.worldClockTimezones === SETTINGS_DEFAULTS.worldClockTimezones" @reset="settingsStore.worldClockTimezones = SETTINGS_DEFAULTS.worldClockTimezones" />
                          </div>
                        </div>
                      </template>
                    </div>
                  </Collapse>
                </template>
                <div v-if="settingsStore.screensaverWidgets.some(w => ['news', 'sports', 'market', 'worldclock'].includes(w))" class="row stack">
                  <div class="row-head">
                    <div class="row-text">
                      <span class="label">Widget text size</span>
                      <p>Scales the news, sports, market and world-clock text. Touch mode already enlarges them — this adjusts on top.</p>
                    </div>
                    <SettingResetButton label="Widget text size" :at-default="settingsStore.screensaverWidgetSize === SETTINGS_DEFAULTS.screensaverWidgetSize" @reset="settingsStore.screensaverWidgetSize = SETTINGS_DEFAULTS.screensaverWidgetSize" />
                  </div>
                  <div class="row-control">
                    <div class="slider">
                      <span class="cap">80%</span>
                      <input type="range" min="80" max="250" step="10" :value="settingsStore.screensaverWidgetSize" @input="settingsStore.screensaverWidgetSize = Number(($event.target as HTMLInputElement).value)" :style="sliderFill(settingsStore.screensaverWidgetSize, 80, 250)" aria-label="Widget text size" />
                      <span class="cap">250%</span>
                      <span class="val">{{ settingsStore.screensaverWidgetSize }}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section class="panel" id="ss-background">
              <div class="panel-head">
                <h2>Screensaver background</h2>
                <span class="hint">Shown only while the screensaver is on — the dashboard keeps its own.</span>
                <span class="spacer"></span>
                <SettingResetButton label="Screensaver background" :at-default="settings.screensaverBackground === SETTINGS_DEFAULTS.screensaverBackground" @reset="settings.screensaverBackground = SETTINGS_DEFAULTS.screensaverBackground" />
              </div>
              <div class="panel-body">
                <div class="row stack picker-row">
                  <BackgroundPicker
                    v-model="settings.screensaverBackground"
                    :groups="screensaverPickerGroups"
                  />
                </div>
                <div class="row stack">
                  <div class="row-head">
                    <div class="row-text">
                      <span class="label">Custom image or GIF</span>
                      <p>Replaces the style above while the screensaver is on.</p>
                    </div>
                  </div>
                  <div class="row-control">
                    <div class="drop">
                      <FontAwesomeIcon :icon="['fas', 'upload']" />
                      <span>{{ isCustomScreensaverBackground ? 'A custom image is active.' : 'Drop a file here, or browse.' }}</span>
                      <input ref="screensaverBgFileInput" type="file" accept="image/*,.gif" @change="handleScreensaverBackgroundUpload" style="display:none" />
                      <button type="button" class="btn sm" :disabled="uploadingScreensaverBackground" @click="($refs.screensaverBgFileInput as HTMLInputElement).click()">
                        <FontAwesomeIcon :icon="uploadingScreensaverBackground ? ['fas', 'spinner'] : ['fas', 'upload']" :spin="uploadingScreensaverBackground" />
                        {{ uploadingScreensaverBackground ? 'Uploading…' : 'Choose file…' }}
                      </button>
                      <button v-if="isCustomScreensaverBackground" type="button" class="btn danger sm" @click="removeScreensaverBackground">
                        <FontAwesomeIcon :icon="['fas', 'trash']" /> Remove
                      </button>
                    </div>
                  </div>
                  <div v-if="isCustomScreensaverBackground" class="bg-thumb">
                    <img :src="settings.screensaverBackground" alt="Screensaver background" />
                  </div>
                </div>
              </div>
            </section>
          </div>

          <div class="rail">
            <div class="preview">
              <div class="preview-head"><FontAwesomeIcon :icon="['fas', 'moon']" /> Screensaver preview</div>
              <div class="preview-stage preview-stage-bg preview-stage-ss" :class="screensaverPreviewClass" :style="screensaverPreviewStyle">
                <div class="ss-mock">
                  <div class="ss-mock-clock" :style="{ fontSize: `${Math.round(46 * settingsStore.screensaverWidgetSize / 100)}px` }">12:34</div>
                  <div class="ss-mock-date">Monday, 21 September</div>
                  <div class="ss-mock-chips">
                    <span v-if="settingsStore.screensaverWidgets.includes('weather')" :style="{ fontSize: `${12 * settingsStore.screensaverWeatherSize / 100}px` }">☀ 27° Tel Aviv</span>
                    <span v-if="settingsStore.screensaverWidgets.includes('market')">BTC ▲ 1.4%</span>
                    <span v-if="settingsStore.screensaverWidgets.includes('worldclock')">NY 05:34</span>
                  </div>
                  <div v-if="settingsStore.screensaverWidgets.includes('news') || settingsStore.screensaverWidgets.includes('sports')" class="ss-mock-ticker" :style="{ fontSize: `${12 * settingsStore.screensaverWidgetSize / 100}px` }">
                    {{ settingsStore.screensaverWidgets.includes('news') && settingsStore.screensaverWidgets.includes('sports') ? 'Headline ticker — news and sports rotate here' : settingsStore.screensaverWidgets.includes('news') ? 'Headline ticker — news rotates here' : 'Headline ticker — sports rotate here' }}
                  </div>
                </div>
              </div>
              <div class="preview-foot">Live layout. Drag widgets in Customise layout to rearrange.</div>
            </div>
          </div>
        </div>


        <!-- ── Logs ── -->
        <div v-if="activeTab === 'logs'" class="content">
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
                    <div ref="logViewerEl" class="log-viewer">
                      <template v-if="logLines.length">
                        <div v-for="(line, i) in logLines" :key="i" class="log-line" :class="logLineClass(line)">{{ line }}</div>
                      </template>
                      <p v-else class="form-help">{{ selectedLog ? 'This log is empty.' : 'Pick a log file on the left to view its tail.' }}</p>
                    </div>
                    <div class="log-statusbar">
                      <span>{{ selectedLog ? `${logLines.length} lines shown` : 'No file selected' }}</span>
                      <span v-if="logsUpdatedAt">Updated {{ logsUpdatedAt }}</span>
                    </div>
                  </section>
                </div>
              </div>
            </section>
          </div>
        </div>


        <!-- ── Templates ── -->
        <div v-if="activeTab === 'templates'" class="content">
          <div class="col">
            <section
              v-for="category in templateCategories"
              :key="category.id"
              class="panel template-category"
            >
              <button class="panel-head category-header" type="button" @click="toggleCategory(category.id)" :aria-expanded="expandedCategories.includes(category.id)">
                <h2><FontAwesomeIcon :icon="category.icon" class="category-icon" /> {{ category.name }}</h2>
                <span class="hint">{{ category.templates.length }} template{{ category.templates.length === 1 ? '' : 's' }}</span>
                <span class="spacer"></span>
                <FontAwesomeIcon :icon="['fas', 'chevron-down']" class="category-chevron" :class="{ 'chevron-open': expandedCategories.includes(category.id) }" />
              </button>
              <Collapse :open="expandedCategories.includes(category.id)">
                <div class="panel-body pad">
                  <div class="template-grid">
                    <div v-for="template in category.templates" :key="template.id" class="template-card">
                      <div class="template-card-header" :style="{ borderLeftColor: template.color }">
                        <div class="template-icon-wrap" :style="{ background: template.color + '22' }">
                          <img v-if="template.logo" :src="template.logo" :alt="template.name" class="template-logo-img" />
                          <FontAwesomeIcon v-else :icon="template.icon" :style="{ color: template.color }" />
                        </div>
                        <div class="template-info">
                          <span class="template-name">{{ template.name }}</span>
                          <span class="template-desc">{{ template.description }}</span>
                        </div>
                        <button class="btn primary sm template-add-btn" :disabled="addingTemplate === template.id" @click="addTemplateAsScene(template)">
                          <FontAwesomeIcon :icon="addingTemplate === template.id ? ['fas', 'spinner'] : ['fas', 'plus']" :spin="addingTemplate === template.id" />
                          {{ addingTemplate === template.id ? 'Adding…' : 'Add Scene' }}
                        </button>
                      </div>
                      <div class="template-buttons-preview">
                        <span v-for="btn in template.buttons.slice(0, 8)" :key="btn.label" class="template-btn-chip"
                          :style="{ background: btn.style?.backgroundColor ? btn.style.backgroundColor + '33' : template.color + '22', borderColor: btn.style?.backgroundColor ?? template.color }">
                          <FontAwesomeIcon :icon="btn.icon" :style="{ color: btn.style?.backgroundColor ?? template.color }" />
                          {{ btn.label }}
                        </span>
                        <span v-if="template.buttons.length > 8" class="template-btn-chip template-btn-more">+{{ template.buttons.length - 8 }} more</span>
                      </div>
                    </div>
                  </div>
                </div>
              </Collapse>
            </section>
          </div>
        </div>


        <!-- ── Server ── -->
        <div v-if="activeTab === 'server'" class="content">
          <div class="col">
            <section class="panel" id="startup">
              <div class="panel-head"><h2>Startup &amp; navigation</h2></div>
              <div class="panel-body">
                <div class="row">
                  <div class="row-text">
                    <span class="label">Launch VDock on startup</span>
                    <p>Starts VDock when you log in to Windows, macOS or Linux.</p>
                  </div>
                  <div class="row-control">
                    <label class="switch"><span class="sr-only">Launch VDock on startup</span><input v-model="settings.startOnBoot" type="checkbox" @change="handleStartOnBootToggle" /><span class="track"></span></label>
                  </div>
                </div>
                <p v-if="startOnBootStatus" class="status-msg row-status" :class="startOnBootStatus.success ? 'status-success' : 'status-error'">{{ startOnBootStatus.message }}</p>
                <div class="row">
                  <div class="row-text">
                    <span class="label">Close launcher terminal after startup</span>
                    <p>Closes the launcher window once VDock starts. Turn off to keep it open for debugging.</p>
                  </div>
                  <div class="row-control">
                    <label class="switch"><span class="sr-only">Close launcher terminal</span><input v-model="settings.autoCloseLauncher" type="checkbox" /><span class="track"></span></label>
                  </div>
                </div>
                <div class="row">
                  <div class="row-text">
                    <span class="label">Open settings in a new browser tab</span>
                    <p>Opens Settings separately instead of navigating inside VDock.</p>
                  </div>
                  <div class="row-control">
                    <label class="switch"><span class="sr-only">Open settings in a new tab</span><input v-model="settings.openSettingsInNewTab" type="checkbox" /><span class="track"></span></label>
                  </div>
                </div>
              </div>
            </section>

            <section class="panel" id="connection">
              <div class="panel-head"><h2>Connection</h2><span class="hint">Ports are written to backend/.env and frontend/.env and take effect on the next launch.</span></div>
              <div class="panel-body">
                <div class="row">
                  <div class="row-text">
                    <span class="label">Host</span>
                    <p>The interface the server binds to.</p>
                  </div>
                  <div class="row-control">
                    <code class="kv-code">{{ serverConfig?.host ?? '127.0.0.1' }}</code>
                  </div>
                </div>
                <div class="row">
                  <div class="row-text">
                    <span class="label">Authentication</span>
                    <p>{{ serverConfig?.require_auth ? 'On. Requests must prove identity.' : 'Off. Anyone on your network who can reach the address below can control this deck.' }}</p>
                  </div>
                  <div class="row-control">
                    <span class="chip" :class="{ 'chip-warn': !serverConfig?.require_auth }">{{ serverConfig?.require_auth ? 'Enabled' : 'Disabled' }}</span>
                  </div>
                </div>
                <div class="row">
                  <div class="row-text">
                    <span class="label">Ports</span>
                    <p>Frontend is the port you open in the browser; backend is the API the frontend proxies to.</p>
                  </div>
                  <div class="row-control">
                    <label class="sr-only" for="fp">Frontend port</label>
                    <input id="fp" v-model.number="serverPorts.frontend" type="number" class="input w-110" min="1024" max="65535" placeholder="3000" />
                    <span class="muted">→</span>
                    <label class="sr-only" for="bp">Backend port</label>
                    <input id="bp" v-model.number="serverPorts.backend" type="number" class="input w-110" min="1024" max="65535" placeholder="5000" />
                    <button type="button" class="btn sm" :disabled="portsBusy" @click="checkPorts">
                      <FontAwesomeIcon :icon="['fas', 'plug']" /> Check
                    </button>
                    <button type="button" class="btn primary sm" :disabled="portsBusy" @click="savePorts">
                      <FontAwesomeIcon :icon="['fas', 'save']" /> Save ports
                    </button>
                  </div>
                </div>
                <div v-if="portErrors.frontend || portErrors.backend || portsStatus" class="row row-status-row">
                  <div class="row-text">
                    <p v-if="portErrors.frontend" class="status-msg status-error">Frontend: {{ portErrors.frontend }}</p>
                    <p v-if="portErrors.backend" class="status-msg status-error">Backend: {{ portErrors.backend }}</p>
                    <p v-if="portsStatus" class="status-msg" :class="portsStatus.success ? 'status-success' : 'status-error'">{{ portsStatus.message }}</p>
                  </div>
                </div>
                <div class="row">
                  <div class="row-text">
                    <span class="label">Applying port changes</span>
                    <p>Needs a restart of VDock via <code class="kv-code">launch.bat</code>.</p>
                  </div>
                </div>
              </div>
            </section>

          </div>
        </div>

        <!-- ── Connect a device ── -->
        <div v-if="activeTab === 'connect'" class="content">
          <div class="col">
            <section class="panel">
              <div class="panel-head"><h2>Connect a device</h2><span class="hint">Any phone or tablet on your Wi-Fi can be a second deck — no app to install.</span></div>
              <div class="panel-body">
                <ol class="connect-steps">
                  <li><b>Same Wi-Fi.</b> Connect the phone or tablet to the same network as this PC.</li>
                  <li><b>Allow LAN access.</b> Turn it on below and relaunch VDock once — this makes the deck reachable on your network.</li>
                  <li><b>Scan the code.</b> Point the device camera at the QR, or type the deck address into its browser.</li>
                </ol>
                <div class="row">
                  <div class="row-text">
                    <span class="label">Allow LAN access</span>
                    <p>Binds the server to your network so other devices can reach it. Applies on the next launch.</p>
                  </div>
                  <div class="row-control">
                    <label class="switch"><span class="sr-only">Allow LAN access</span><input type="checkbox" :checked="serverConfig?.allow_lan ?? false" @change="toggleAllowLan" /><span class="track"></span></label>
                  </div>
                </div>
                <div class="row" v-if="lanUrl">
                  <div class="row-text">
                    <span class="label">Deck address</span>
                    <p>Scan the code on the device, or type the address into its browser.</p>
                  </div>
                  <div class="row-control">
                    <code class="kv-code kv-accent">{{ lanUrl }}</code>
                    <button type="button" class="btn sm" @click="copyLanUrl">
                      <FontAwesomeIcon :icon="['fas', 'copy']" /> Copy
                    </button>
                  </div>
                </div>
                <div v-if="lanUrl" class="row stack">
                  <div class="row-control qr-row">
                    <canvas ref="qrCanvas" class="qr-canvas" />
                    <p class="muted qr-note">The code encodes the address above. It changes when the backend port or your LAN address changes.</p>
                  </div>
                </div>
                <div v-else class="row">
                  <div class="note warn qr-offline">
                    <FontAwesomeIcon :icon="['fas', 'triangle-exclamation']" />
                    <div>
                      LAN address unavailable. Enable <b>Allow LAN access</b> and relaunch —
                      until then VDock only listens on this PC.
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>


        <!-- ── Integrations ── -->
        <div v-if="activeTab === 'integration'" class="content">
          <div class="col">
            <section class="panel" id="auto-switch">
              <div class="panel-head"><h2>Auto scene switching</h2><span class="hint">Scenes follow the app in focus.</span></div>
              <div class="panel-body">
                <div class="row">
                  <div class="row-text">
                    <span class="label">Enable auto switching</span>
                    <p>Switch scenes when monitored apps become active.</p>
                  </div>
                  <div class="row-control">
                    <label class="switch"><span class="sr-only">Enable auto switching</span><input type="checkbox" :checked="autoSwitchingEnabled" @change="toggleAutoSwitching" /><span class="track"></span></label>
                  </div>
                </div>
                <div v-if="autoSwitchingEnabled" class="row row-status-row">
                  <div class="auto-switch-status">
                    <FontAwesomeIcon :icon="['fas', 'circle-check']" class="status-icon success" />
                    <span>Monitoring active application</span>
                  </div>
                </div>
              </div>
            </section>

            <section class="panel" id="agent-alerts">
              <div class="panel-head">
                <h2>Agent attention alerts</h2>
                <span class="spacer"></span>
                <span v-if="agentHookStatus" class="chip" :class="{ 'chip-ok': agentHookInstalled }">
                  <FontAwesomeIcon :icon="['fas', agentHookInstalled ? 'circle-check' : 'circle-xmark']" />
                  {{ agentHookInstalled ? 'Claude hook installed' : 'Hook not installed' }}
                </span>
              </div>
              <div class="panel-body">
                <div class="row">
                  <div class="row-text">
                    <span class="label">Alert me when an agent waits</span>
                    <p>Pops a banner — over the dashboard and the screensaver — when Claude Code needs input or finishes.</p>
                  </div>
                  <div class="row-control">
                    <label class="switch"><span class="sr-only">Agent attention alerts</span><input type="checkbox" :checked="settingsStore.agentAlertsEnabled" @change="toggleAgentAlerts" /><span class="track"></span></label>
                  </div>
                </div>
                <div class="row">
                  <div class="row-text">
                    <span class="label">Claude Code hook</span>
                    <p>Adds a Notification/Stop hook to <code class="kv-code">~/.claude/settings.json</code>. Other agents can POST <code class="kv-code">/api/agent-events</code> with <code class="kv-code">{source, event: "waiting"|"clear"}</code>.</p>
                  </div>
                  <div class="row-control">
                    <button type="button" class="btn sm" @click="installAgentHook" :disabled="installingHook">
                      <FontAwesomeIcon :icon="['fas', installingHook ? 'spinner' : 'plug']" :spin="installingHook" />
                      {{ agentHookInstalled ? 'Reinstall' : 'Install' }}
                    </button>
                  </div>
                </div>
              </div>
            </section>

            <section class="panel" id="running-apps">
              <div class="panel-head">
                <h2>Running applications</h2>
                <span class="hint">Periodically detected apps — powers the live scene dots and this list.</span>
                <span class="spacer"></span>
                <button v-if="settingsStore.appScanningEnabled" type="button" class="btn sm" @click="refreshRunningApps">
                  <FontAwesomeIcon :icon="['fas', 'sync']" :spin="loadingApps" /> Refresh
                </button>
              </div>
              <div class="panel-body">
                <div class="row">
                  <div class="row-text">
                    <span class="label">Enable app scanning</span>
                    <p>Detect running apps so scenes can follow them.</p>
                  </div>
                  <div class="row-control">
                    <label class="switch"><span class="sr-only">Enable app scanning</span><input type="checkbox" :checked="settingsStore.appScanningEnabled" @change="toggleAppScanning" /><span class="track"></span></label>
                  </div>
                </div>
              </div>
              <div class="panel-body flush app-list-body">
                <div v-if="!settingsStore.appScanningEnabled" class="empty-state">
                  <FontAwesomeIcon :icon="['fas', 'desktop']" /><p>App scanning is disabled</p>
                </div>
                <template v-else>
                  <div v-if="runningApps.length > 0" class="app-toolbar">
                    <div class="app-search">
                      <FontAwesomeIcon :icon="['fas', 'search']" class="app-search-icon" />
                      <input
                        v-model="appSearch"
                        type="text"
                        class="app-search-input"
                        placeholder="Filter apps — try 'terminal', 'vscode', 'git'"
                      />
                      <button v-if="appSearch" class="app-search-clear" title="Clear filter" @click="appSearch = ''">
                        <FontAwesomeIcon :icon="['fas', 'times']" />
                      </button>
                    </div>
                    <span v-if="appSearch" class="app-count">{{ filteredApps.length }} of {{ runningApps.length }}</span>
                  </div>
                  <div v-if="loadingApps" class="loading-state">
                    <FontAwesomeIcon :icon="['fas', 'spinner']" spin /><span>Loading applications...</span>
                  </div>
                  <div v-else-if="runningApps.length === 0" class="empty-state">
                    <FontAwesomeIcon :icon="['fas', 'desktop']" /><p>No applications detected</p>
                    <button class="btn sm" @click="refreshRunningApps">Refresh</button>
                  </div>
                  <div v-else class="app-integration-list">
                    <div class="list-header">
                      <span>Application</span><span>Status</span><span>Scene</span><span>Actions</span>
                    </div>
                    <div v-if="filteredApps.length === 0" class="empty-state app-filter-empty">
                      <FontAwesomeIcon :icon="['fas', 'search']" /><p>No apps match "{{ appSearch }}"</p>
                    </div>
                    <div v-for="app in filteredApps" :key="app.exe" class="app-item" :class="{ 'app-item--dev': appTier(app) < 2 }">
                      <div class="app-info">
                        <FontAwesomeIcon :icon="['fas', 'window-maximize']" class="app-icon" />
                        <div class="app-details">
                          <span class="app-name">{{ app.name }}</span>
                          <span class="app-exe">{{ app.exe }}</span>
                        </div>
                        <span v-if="appBadge(app)" class="app-badge" :class="{ 'app-badge--profile': appTier(app) === 0 }">{{ appBadge(app) }}</span>
                      </div>
                      <div class="app-status">
                        <label class="switch"><span class="sr-only">Integrate {{ app.name }}</span><input type="checkbox" :checked="isAppIntegrationEnabled(app.exe)" @change="toggleAppIntegration(app)" /><span class="track"></span></label>
                        <span class="status-text">{{ isAppIntegrationEnabled(app.exe) ? 'On' : 'Off' }}</span>
                      </div>
                      <div class="app-scene">
                        <select v-if="isAppIntegrationEnabled(app.exe)" :value="getAppScene(app.exe)" @change="updateAppScene(app.exe, ($event.target as HTMLSelectElement).value)" class="select select-sm">
                          <option value="">Create New Scene</option>
                          <option v-for="scene in availableScenes" :key="scene.id" :value="scene.id">{{ scene.name }}</option>
                        </select>
                        <span v-else class="scene-placeholder">—</span>
                      </div>
                      <div class="app-actions">
                        <button v-if="isAppIntegrationEnabled(app.exe)" class="btn-icon" @click="openShortcutManager(app)" title="Manage Shortcuts"><FontAwesomeIcon :icon="['fas', 'cog']" /></button>
                        <button v-if="isAppIntegrationEnabled(app.exe) && !getAppScene(app.exe)" class="btn-icon btn-icon-primary" @click="createSceneForApp(app)" title="Create Scene"><FontAwesomeIcon :icon="['fas', 'plus']" /></button>
                      </div>
                    </div>
                  </div>
                  <div v-if="appIntegrations.length > 0" class="integration-summary">
                    <FontAwesomeIcon :icon="['fas', 'circle-info']" />
                    <span>{{ appIntegrations.length }} app{{ appIntegrations.length > 1 ? 's' : '' }} integrated</span>
                  </div>
                </template>
              </div>
            </section>

            <section class="panel" id="recent-actions">
              <div class="panel-head">
                <h2>Recent actions</h2>
                <span class="spacer"></span>
                <button v-if="settings.recentActions.length" type="button" class="btn quiet sm" @click="clearRecentActions">Clear</button>
              </div>
              <div class="panel-body">
                <div v-if="settings.recentActions.length > 0" class="recent-actions">
                  <div v-for="(actionId, index) in settings.recentActions" :key="index" class="recent-action-item">{{ actionId }}</div>
                </div>
                <div v-else class="empty-state">No recent actions</div>
              </div>
            </section>
          </div>
        </div>

        <!-- ── About ── -->
        <div v-if="activeTab === 'about'" class="content">
          <div class="col col-about">
            <section class="panel">
              <div class="panel-body pad about-hero">
                <span class="nav-mark about-mark"><img :src="'/assets/branding/vdock-logo.jpg'" alt="VDock logo" class="nav-mark-img" /></span>
                <div class="about-hero-text">
                  <div class="about-title-row">
                    <h2 class="about-title">VDock</h2>
                    <span class="nav-ver">v{{ appVersion }}</span>
                  </div>
                  <p class="muted about-desc">A virtual stream interface for controlling your computer with customisable buttons, macros, system metrics and intelligent app integration.</p>
                  <div class="about-actions">
                    <button type="button" class="btn primary" data-tour="about-help" @click="settingsStore.showHelpGuide = true">
                      <FontAwesomeIcon :icon="['fas', 'circle-question']" /> Help &amp; guide
                    </button>
                    <button type="button" class="btn" @click="launchTutorial">
                      <FontAwesomeIcon :icon="['fas', 'route']" /> Launch tutorial
                    </button>
                    <a class="btn" href="https://github.com/ponya5/VDock2" target="_blank" rel="noopener"><FontAwesomeIcon :icon="['fab', 'github']" /> GitHub</a>
                    <a class="btn" href="https://github.com/ponya5/VDock2/issues" target="_blank" rel="noopener"><FontAwesomeIcon :icon="['fas', 'bug']" /> Report an issue</a>
                    <a class="btn" href="https://github.com/ponya5/VDock2" target="_blank" rel="noopener"><FontAwesomeIcon :icon="['fas', 'star']" /> Star the repo</a>
                  </div>
                </div>
              </div>
            </section>

            <section class="panel" id="features">
              <div class="panel-head"><h2>What's in it</h2></div>
              <div class="panel-body">
                <div class="row stack picker-row">
                  <div class="grid-3">
                    <div v-for="feature in aboutFeatures" :key="feature.label" class="feature">
                      <div class="feature-title"><FontAwesomeIcon :icon="feature.icon" class="feature-icon" /> {{ feature.label }}</div>
                      <div class="muted feature-desc">{{ feature.desc }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section class="panel" id="build">
              <div class="panel-head"><h2>Build</h2></div>
              <div class="panel-body">
                <dl class="kv-list">
                  <div class="kv"><dt>Version</dt><dd>{{ appVersion }}</dd></div>
                  <div class="kv"><dt>Licence</dt><dd>MIT — VDock Contributors</dd></div>
                  <div class="kv"><dt>Repository</dt><dd><a href="https://github.com/ponya5/VDock2" target="_blank" rel="noopener">github.com/ponya5/VDock2</a></dd></div>
                </dl>
              </div>
            </section>

            <div class="about-support">
              <a href="https://ko-fi.com/danielshalom" target="_blank" rel="noopener" class="kofi-btn">
                <img src="https://storage.ko-fi.com/cdn/cup-border.png" alt="Ko-fi" class="kofi-icon" />
                Buy me a coffee
              </a>
            </div>
          </div>
        </div>

      <!-- Save bar — settings autosave via the store's deep watch, so the
           honest state is "clean". The Buttons page additionally drafts its
           three motion/design defaults locally (buttonDraftDirty) until
           Save & Apply commits them to the store. -->
      <div v-if="savebarVisible" class="savebar" :data-state="buttonPageDirty ? 'dirty' : 'clean'">
        <span class="dot"></span>
        <span class="msg">{{ savebarMessage }}</span>
        <span class="grow">
          <template v-if="isButtonsPage">
            <button type="button" class="btn ghost" :disabled="!buttonPageDirty" @click="revertButtonDefaults">Revert</button>
            <button type="button" class="btn primary" :disabled="applyingButtonBehaviour" @click="saveAndApplyButtonSettings">
              <FontAwesomeIcon :icon="['fas', 'floppy-disk']" /> Save &amp; Apply
            </button>
          </template>
          <button v-else type="button" class="btn primary" @click="applyToDashboard">
            <FontAwesomeIcon :icon="['fas', 'check']" /> Apply to dashboard
          </button>
        </span>
      </div>
    </main>

    <!-- Shortcut Manager Modal -->
    <AppShortcutManager
      v-if="showShortcutManager"
      :app-exe="selectedAppForShortcuts?.exe || ''"
      :scene-id="getAppScene(selectedAppForShortcuts?.exe || '')"
      @close="showShortcutManager = false"
      @add-shortcut="handleAddShortcut"
    />

    <!-- Live screensaver layout editor — mounted in THIS window so Customize
         Layout works whether or not a deck window is reachable. Save writes
         settings.screensaverLayout, which syncs to every connected window. -->
    <ScreenSaver
      v-if="screensaverLayoutEditOpen"
      :visible="true"
      :layout-edit="true"
      @dismiss="screensaverLayoutEditOpen = false"
      @save-layout="onSaveScreensaverLayout"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useSettingsStore, SETTINGS_DEFAULTS } from '@/stores/settings'
import { useProfilesStore } from '@/stores/profiles'
import { LAST_PROFILE_STORAGE_KEY, useDashboardStore } from '@/stores/dashboard'
import { useNotificationsStore } from '@/stores/notifications'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { version as appVersion } from '../../package.json'
import ScreenSaver from '@/components/ScreenSaver.vue'
import type { ScreensaverLayout } from '@/utils/screensaverLayout'
import BackgroundPicker, { type BackgroundPickerGroup } from '@/components/BackgroundPicker.vue'
import DeckButton from '@/components/DeckButton.vue'
import ButtonDesignPicker from '@/components/ButtonDesignPicker.vue'
import SettingResetButton from '@/components/SettingResetButton.vue'
import Collapse from '@/components/Collapse.vue'
import apiClient from '@/api/client'
import { autoSceneSwitcher } from '@/services/autoSceneSwitcher'
import AppShortcutManager from '@/components/AppShortcutManager.vue'
import { fetchAppProfiles, hasAppShortcuts, topAppShortcuts, type AppShortcut, type AppProfileDto } from '@/api/appProfiles'
import { templateCategories, type AppTemplate } from '@/data/appTemplates'
import type { RunningApp, Scene, Button } from '@/types'
import { useWeather } from '@/composables/useWeather'
import { openStandaloneSettings, isStandaloneSettingsRoute } from '@/utils/openStandaloneSettings'
import { refreshVdock, requestVdockRefresh } from '@/composables/useVdockRefresh'
import { sendUiCommand } from '@/composables/useUiCommands'
import { useTutorial } from '@/services/tutorial'
import { confirmDialog } from '@/composables/useConfirm'
import { testNewsConnection, parseFeedList, DEFAULT_SPORTS_FEEDS } from '@/services/newsService'
import { testMarketConnection, parseTickers } from '@/services/marketService'
import { BACKGROUNDS, isImageBackground, resolveBackground } from '@/data/backgrounds'
import { appForScene, appIdForExe } from '@/data/appBackgrounds'
import { useAppIntegrations, setAppIntegrations, reloadAppIntegrations } from '@/composables/useAppIntegrations'
import { backgroundClassFor, backgroundStyleFor } from '@/utils/backgroundStyle'

const router = useRouter()
const route = useRoute()
const settingsStore = useSettingsStore()
const profilesStore = useProfilesStore()
const dashboardStore = useDashboardStore()
const notificationsStore = useNotificationsStore()
const { refresh: refreshWeatherWidget } = useWeather()

const isStandaloneSettings = computed(() => isStandaloneSettingsRoute(route))

function openSettingsInBrowserTab() {
  const opened = openStandaloneSettings({
    router,
    query: {
      tab: activeTab.value,
      ...(activeTab.value === 'appearance' ? { sub: appearanceSubTab.value } : {}),
    },
    returnMainWindowToDashboard: true,
  })

  if (!opened) {
    notificationsStore.warning(
      'Popup blocked',
      'Allow popups for VDock to open settings in your browser.',
      { duration: 6000 }
    )
  }
}

function handleTestScreensaver() {
  sendUiCommand('show_screensaver')
  if (!isStandaloneSettings.value) {
    // Same-tab settings: the dashboard is unmounted right now, so the queued
    // command only fires once it remounts. Navigate back so the preview is
    // actually seen instead of looking like nothing happened.
    router.push('/')
    return
  }
  notificationsStore.success(
    'Screensaver triggered',
    'It is now showing on the deck window — tap it to dismiss.'
  )
}

// Opens the real screensaver in drag/resize edit mode — mounted inside this
// window so it always works: the previous design sent a ui_command to the
// deck window, which silently did nothing when no deck window was mounted or
// reachable (e.g. settings opened standalone on the panel itself).
const screensaverLayoutEditOpen = ref(false)

function handleCustomizeScreensaverLayout() {
  screensaverLayoutEditOpen.value = true
}

function onSaveScreensaverLayout(layout: ScreensaverLayout) {
  // Assigning the store ref persists through the settings watch → local +
  // server sync, so the deck window picks the arrangement up live.
  settingsStore.screensaverLayout = layout
  screensaverLayoutEditOpen.value = false
  notificationsStore.success('Layout saved', 'The new widget arrangement is applied on the deck.')
}

function handleSettingsBack() {
  if (isStandaloneSettings.value) {
    // The main dashboard runs in a different tab/window here, so ask it to
    // refresh itself instead of calling refreshVdock() directly.
    requestVdockRefresh()
    window.close()
    return
  }

  // Settings changes made via direct API calls (templates, integrations,
  // shortcuts, etc.) don't all flow through the reactive settings store, so
  // re-sync everything from the backend when returning to the dashboard.
  void refreshVdock()
  router.push('/')
}

const settings = computed(() => settingsStore)
const serverConfig = computed(() => settingsStore.serverConfig)

// --- Connect a device (QR) ----------------------------------------------------
// The URL a phone needs is the one serving the app: the backend port, which
// serves the built frontend in production. In dev, Vite only binds localhost —
// so the backend port (serving dist/) is still the right target.
const qrCanvas = ref<HTMLCanvasElement | null>(null)
const lanUrl = computed(() => {
  const ip = serverConfig.value?.lan_ip
  const port = serverConfig.value?.port
  if (!ip || !port) return null
  return `http://${ip}:${port}`
})

async function renderQr() {
  await nextTick()
  if (!qrCanvas.value || !lanUrl.value) return
  try {
    const QRCode = (await import('qrcode')).default
    await QRCode.toCanvas(qrCanvas.value, lanUrl.value, {
      width: 180,
      margin: 1,
      color: { dark: '#0d0b26', light: '#ffffff' },
    })
  } catch { /* QR is best-effort; the URL text remains */ }
}

watch([lanUrl, () => serverConfig.value?.lan_reachable], renderQr, { immediate: false })

async function toggleAllowLan(event: Event) {
  const enabled = (event.target as HTMLInputElement).checked
  const ok = await settingsStore.updateServerConfig({ allow_lan: enabled })
  notificationsStore[ok ? 'success' : 'error'](
    ok ? 'LAN access ' + (enabled ? 'enabled' : 'disabled') : 'Could not save',
    ok ? 'Relaunch VDock to apply — the bind address is chosen at startup.' : 'Server rejected the change.'
  )
  await nextTick()
  renderQr()
}

function copyLanUrl() {
  if (!lanUrl.value) return
  navigator.clipboard?.writeText(lanUrl.value)
    .then(() => notificationsStore.success('Copied', lanUrl.value ?? ''))
    .catch(() => notificationsStore.info('Copy failed', lanUrl.value ?? ''))
}

// Ports are written to the .env files and bind at process start — the UI
// validates and probes collisions, then tells the user to relaunch.
const serverPorts = ref({ frontend: 0, backend: 0 })
const portErrors = ref<{ frontend: string; backend: string }>({ frontend: '', backend: '' })
const portsStatus = ref<{ success: boolean; message: string } | null>(null)
const portsBusy = ref(false)

async function loadPorts() {
  try {
    const { data } = await apiClient.get('/system/ports')
    if (data.success) {
      serverPorts.value = { frontend: data.frontend_port, backend: data.backend_port }
    }
  } catch { /* informational — fields stay editable */ }
}

async function submitPorts(checkOnly: boolean) {
  portsBusy.value = true
  portErrors.value = { frontend: '', backend: '' }
  portsStatus.value = null
  try {
    const { data } = await apiClient.put('/system/ports', {
      frontend_port: serverPorts.value.frontend,
      backend_port: serverPorts.value.backend,
      check_only: checkOnly,
    })
    portsStatus.value = { success: true, message: data.message }
    if (!checkOnly) notificationsStore.success('Ports saved', data.message)
  } catch (err: any) {
    const errors = err?.response?.data?.errors
    if (errors) {
      portErrors.value = {
        frontend: errors.frontend_port ?? '',
        backend: errors.backend_port ?? '',
      }
      portsStatus.value = { success: false, message: 'Fix the highlighted ports and try again.' }
    } else {
      portsStatus.value = { success: false, message: err?.message || 'Could not save ports.' }
    }
  } finally {
    portsBusy.value = false
  }
}

const checkPorts = () => submitPorts(true)
const savePorts = () => submitPorts(false)

const toastLevelOptions = [
  { value: 'all', label: 'All' },
  { value: 'errors-only', label: 'Errors only' },
  { value: 'off', label: 'Off' },
] as const

const activeTab = ref('appearance')
const appearanceSubTab = ref<'buttons' | 'layout' | 'background' | 'screensaver'>('buttons')

// DL-054: Appearance children are full pages in the sidebar now — the old
// nested sub-tab rows (buttonsSubTab/screensaverSubTab) are gone; panels on a
// page are reached by anchor scrolling instead.
const appearanceSubs = [
  { id: 'buttons', name: 'Buttons' },
  { id: 'layout', name: 'Layout & sidebar' },
  { id: 'background', name: 'Background' },
  { id: 'screensaver', name: 'Screen saver' },
] as const
type AppearanceSubId = (typeof appearanceSubs)[number]['id']

const PAGE_META: Record<string, { crumb: string; title: string; blurb: string }> = {
  'appearance/buttons': { crumb: 'Appearance · Buttons', title: 'Buttons', blurb: 'Sizing, motion and press feedback for every deck key.' },
  'appearance/layout': { crumb: 'Appearance · Layout & sidebar', title: 'Layout & sidebar', blurb: 'The docked sidebar, dashboard font and notifications.' },
  'appearance/background': { crumb: 'Appearance · Background', title: 'Background', blurb: 'Dashboard wallpaper and per-scene overrides.' },
  'appearance/screensaver': { crumb: 'Appearance · Screen saver', title: 'Screen saver', blurb: 'Idle screen widgets, timing and its own backdrop.' },
  templates: { crumb: 'Templates', title: 'App templates', blurb: 'Drop-in scenes for popular apps.' },
  server: { crumb: 'Server', title: 'Server', blurb: 'Ports, LAN access and startup behaviour.' },
  integration: { crumb: 'Integrations', title: 'Integrations', blurb: 'Scenes that follow the app in focus.' },
  connect: { crumb: 'Connect a device', title: 'Connect a device', blurb: 'Turn a phone or tablet into a second deck.' },
  logs: { crumb: 'Logs', title: 'Session logs', blurb: 'Backend and frontend logs for troubleshooting.' },
  about: { crumb: 'About', title: 'About VDock', blurb: 'Version, help and project links.' },
}
const topbarMeta = computed(() =>
  PAGE_META[activeTab.value === 'appearance' ? `appearance/${appearanceSubTab.value}` : activeTab.value]
  ?? PAGE_META.about
)

const mainEl = ref<HTMLElement | null>(null)
function scrollContentTop() {
  void nextTick(() => mainEl.value?.scrollTo({ top: 0 }))
}
function selectAppearanceSub(id: AppearanceSubId) {
  activeTab.value = 'appearance'
  appearanceSubTab.value = id
  scrollContentTop()
}
// Panels carry ids so nav sub-items and search results can land on the exact
// section rather than just the page.
function scrollToPanel(id: string) {
  void nextTick(() => {
    document.getElementById(id)?.scrollIntoView({ block: 'start', behavior: 'smooth' })
  })
}

// Dashboard font picker — samples render in the real font so the card can't
// drift from what the dashboard will show.
const dashboardFontOptions: { value: 'default' | 'editorial' | 'mono'; name: string; sample: string; family: string }[] = [
  { value: 'default', name: 'Modern Sans', sample: 'Aa 12:34', family: "'Heebo', system-ui, sans-serif" },
  { value: 'editorial', name: 'Editorial', sample: 'Aa 12:34', family: "'Instrument Serif', Georgia, serif" },
  { value: 'mono', name: 'Terminal Mono', sample: 'Aa 12:34', family: "'JetBrains Mono', monospace" },
]
const dashboardFontFamily = computed(() =>
  dashboardFontOptions.find(o => o.value === settingsStore.dashboardFont)?.family
)

// Sample button for the live preview card — never persisted, just rendered
// through the real DeckButton component so the preview matches actual
// dashboard rendering exactly. Initialized from the persisted defaults so the
// picker still shows the last-applied style when the tab is reopened.
const previewAnimation = ref(settingsStore.buttonDefaultAnimation)
const previewIconLoop = ref(settingsStore.buttonDefaultIconLoop)
const previewEffect = ref(settingsStore.buttonDefaultEffect)

// DL-028: resetting a demo control restores the factory default AND the
// persisted new-button default; applying to existing buttons stays behind
// the explicit "Save & Apply to All Buttons" action.
const previewDefaults = {
  buttonDefaultAnimation: previewAnimation,
  buttonDefaultIconLoop: previewIconLoop,
  buttonDefaultEffect: previewEffect
} as const
function resetButtonDefault(key: keyof typeof previewDefaults) {
  previewDefaults[key].value = SETTINGS_DEFAULTS[key]
  settingsStore[key] = SETTINGS_DEFAULTS[key]
}

const previewButton = computed<Button>(() => ({
  id: 'preview-button',
  label: 'Preview',
  tooltip: 'Sample tooltip',
  icon_type: 'fontawesome',
  icon: ['fas', 'star'],
  shape: 'rounded',
  position: { row: 0, col: 0 },
  size: { rows: 1, cols: 1 },
  style: {
    backgroundColor: '#3498db',
    textColor: '#ffffff',
    animation: previewAnimation.value === 'none' ? undefined : (previewAnimation.value as any)
  },
  layers: {
    // `layers.icon`, when present, is treated by resolveButtonVisual() as the
    // authoritative icon definition — it must always carry `type`/`value`
    // (not just `loop`), or the icon renders empty and the loop animation
    // has nothing left to animate.
    icon: previewIconLoop.value === 'none'
      ? undefined
      : { type: 'fontawesome', value: ['fas', 'star'], loop: previewIconLoop.value as any },
    effect: previewEffect.value === 'none' ? undefined : { type: previewEffect.value as any, tint: 'brand' }
  },
  enabled: true
}))

// Mirrors DashboardView's own background class/style resolution (minus the
// scene/page-background overrides, which aren't relevant to a settings
// preview) so the preview pane shows exactly what the dashboard would.
const previewBackgroundClass = computed(() => backgroundClassFor(settingsStore.background))

// The real component for 'component'-kind backgrounds, rendered inside the
// scaled-viewport stage (see template). Falls back to the checkerboard via
// previewBackgroundStyle when the component reports an init failure.
const bgPreviewFailed = ref<string | null>(null)
const previewBgComponent = computed(() => {
  const option = resolveBackground(settingsStore.background)
  return option.kind === 'component' && bgPreviewFailed.value !== option.id
    ? option.component
    : null
})
function onPreviewBgError(err: unknown) {
  console.warn('[settings-preview] background fell back:', settingsStore.background, err)
  bgPreviewFailed.value = settingsStore.background
}

// The inner stage is 100vw×100vh; scale = stage width / real viewport width.
const bgPreviewStage = ref<HTMLElement | null>(null)
const bgPreviewScale = ref(0.2)
let bgPreviewObserver: ResizeObserver | undefined
watch(bgPreviewStage, (el, _old, onCleanup) => {
  bgPreviewObserver?.disconnect()
  if (!el) return
  const update = () => {
    const vw = window.innerWidth
    const vh = window.innerHeight
    if (vw > 0 && vh > 0 && el.clientWidth > 0 && el.clientHeight > 0) {
      // cover, not contain — the stage clips whatever doesn't fit
      bgPreviewScale.value = Math.max(el.clientWidth / vw, el.clientHeight / vh)
    }
  }
  update()
  bgPreviewObserver = new ResizeObserver(update)
  bgPreviewObserver.observe(el)
  onCleanup(() => bgPreviewObserver?.disconnect())
})

// Inline styles always win over the (global, unscoped) dashboard-bg-* classes
// regardless of CSS specificity, so every branch here sets an explicit
// background — including a neutral checkerboard placeholder for the one case
// a settings preview can't render (a full animated background component).
const PREVIEW_CHECKERBOARD = 'repeating-conic-gradient(rgba(255, 255, 255, 0.06) 0% 25%, transparent 0% 50%) 50% / 20px 20px'

const previewBackgroundStyle = computed(() => {
  const option = resolveBackground(settingsStore.background)
  if (option.kind === 'component') {
    return { background: PREVIEW_CHECKERBOARD }
  }
  if (option.id === 'default') {
    return { background: 'var(--color-background)' }
  }
  return backgroundStyleFor(settingsStore.background)
})

// Screensaver preview rail: 'default' means the classic dark look, not the
// dashboard's gradient — same divergence as screensaverPickerGroups.
const screensaverPreviewClass = computed(() =>
  settingsStore.screensaverBackground === 'default' ? '' : backgroundClassFor(settingsStore.screensaverBackground)
)
const screensaverPreviewStyle = computed(() => {
  const id = settingsStore.screensaverBackground
  if (id === 'default') return { background: 'linear-gradient(180deg, #0c1526 0%, #070d18 100%)' }
  if (resolveBackground(id).kind === 'component') return { background: PREVIEW_CHECKERBOARD }
  return backgroundStyleFor(id)
})

// DL-054: the redesign's save bar. Settings autosave on every change, so the
// only real dirty state is the Buttons page's design draft — the three
// motion/effect defaults preview locally until committed to the store.
const isButtonsPage = computed(() => activeTab.value === 'appearance' && appearanceSubTab.value === 'buttons')
const buttonPageDirty = computed(() =>
  previewAnimation.value !== settingsStore.buttonDefaultAnimation ||
  previewIconLoop.value !== settingsStore.buttonDefaultIconLoop ||
  previewEffect.value !== settingsStore.buttonDefaultEffect
)
const savebarVisible = computed(() => activeTab.value !== 'about' && activeTab.value !== 'logs')
const savebarMessage = computed(() =>
  buttonPageDirty.value ? 'Design draft not applied — preview only' : 'All changes save automatically'
)
function revertButtonDefaults() {
  previewAnimation.value = settingsStore.buttonDefaultAnimation
  previewIconLoop.value = settingsStore.buttonDefaultIconLoop
  previewEffect.value = settingsStore.buttonDefaultEffect
}
function applyToDashboard() {
  settingsStore.saveSettings()
  requestVdockRefresh()
  notificationsStore.success('Applied', 'Settings saved and the dashboard was refreshed.')
}

// Range inputs draw their own fill via a --fill custom property (see CSS).
function sliderFill(value: number, min: number, max: number) {
  const pct = max > min ? ((value - min) / (max - min)) * 100 : 0
  return { '--fill': `${Math.min(100, Math.max(0, pct))}%` }
}

const touchAdvancedOpen = ref(false)
// Matches the store's --button-min-height formula so the chip reads the same
// number the deck actually enforces.
const resolvedKeyHeight = computed(() =>
  Math.round(Math.max(36 * settingsStore.touchModeMultiplier, settingsStore.minimumTouchTargetSize))
)

// Topbar "Reset section" — restores the current Appearance page's settings to
// defaults. Drafted button defaults are reset in the store too so the dirty
// state clears with everything else.
function resetAppearanceSection() {
  const D = SETTINGS_DEFAULTS
  switch (appearanceSubTab.value) {
    case 'buttons':
      settingsStore.touchMode = D.touchMode
      settingsStore.buttonSize = D.buttonSize
      settingsStore.buttonTransparency = D.buttonTransparency
      settingsStore.animationsEnabled = D.animationsEnabled
      settingsStore.editModeWiggle = D.editModeWiggle
      settingsStore.tiltEffectEnabled = D.tiltEffectEnabled
      settingsStore.showLabels = D.showLabels
      settingsStore.showTooltips = D.showTooltips
      settingsStore.pressSoundEnabled = D.pressSoundEnabled
      settingsStore.pressSoundStyle = D.pressSoundStyle
      settingsStore.buttonDefaultAnimation = D.buttonDefaultAnimation
      settingsStore.buttonDefaultIconLoop = D.buttonDefaultIconLoop
      settingsStore.buttonDefaultEffect = D.buttonDefaultEffect
      revertButtonDefaults()
      break
    case 'layout':
      settingsStore.dashboardFont = D.dashboardFont
      settingsStore.dockedSidebarEnabled = D.dockedSidebarEnabled
      settingsStore.dockedSidebarWidth = D.dockedSidebarWidth
      settingsStore.dockedButtonHeight = D.dockedButtonHeight
      settingsStore.toastLevel = D.toastLevel
      break
    case 'background':
      settingsStore.background = D.background
      break
    case 'screensaver':
      settingsStore.screensaverTimeout = D.screensaverTimeout
      settingsStore.screensaverWidgets = [...D.screensaverWidgets]
      settingsStore.screensaverWeatherSize = D.screensaverWeatherSize
      settingsStore.screensaverWidgetSize = D.screensaverWidgetSize
      settingsStore.screensaverBackground = D.screensaverBackground
      break
  }
  notificationsStore.success('Section reset', 'Defaults restored for this section.')
}

const expandedCategories = ref<string[]>([])
const addingTemplate = ref<string | null>(null)

const aboutFeatures = [
  { icon: ['fas', 'table-cells-large'], label: 'Customizable touch button grid', desc: 'Scenes, pages, sliders and folders on a drag-and-drop deck.' },
  { icon: ['fas', 'wand-magic-sparkles'], label: 'Advanced macro automation', desc: 'Hotkeys, scripts and multi-step actions on a single tap.' },
  { icon: ['fas', 'gauge-high'], label: 'Real-time system metrics', desc: 'CPU, RAM, GPU and network at a glance.' },
  { icon: ['fas', 'plug'], label: 'Smart app integration & templates', desc: 'Scenes that follow the focused app, plus ready-made layouts.' },
  { icon: ['fas', 'chart-line'], label: 'Free stock & crypto tickers', desc: 'Live quotes on the screensaver — no API key needed.' },
  { icon: ['fas', 'newspaper'], label: 'News & sports widgets', desc: 'Rotating headlines from free RSS feeds.' },
  { icon: ['fas', 'cloud-sun'], label: 'Live weather, no API key', desc: 'Current conditions powered by open data.' },
  { icon: ['fas', 'image'], label: 'Animated backgrounds & transparency', desc: 'Gradients, particle scenes and per-scene artwork.' },
  { icon: ['fas', 'display'], label: 'Customizable screensaver', desc: 'Arrangeable widgets with drag-snap alignment.' },
  { icon: ['fas', 'hand-pointer'], label: 'Touch-optimized 7-inch interface', desc: 'Sized and spaced for dedicated touch panels.' },
]

function toggleCategory(id: string) {
  const index = expandedCategories.value.indexOf(id)
  if (index === -1) {
    expandedCategories.value.push(id)
  } else {
    expandedCategories.value.splice(index, 1)
  }
}

async function addTemplateAsScene(template: AppTemplate) {
  const profile = dashboardStore.currentProfile
  if (!profile) { notificationsStore.error('No profile', 'Load a profile first.'); return }
  addingTemplate.value = template.id
  try {
    const buttons: Button[] = template.buttons.map((b, index) => ({
      id: `button-${Date.now()}-${index}`,
      label: b.label, icon: b.icon, icon_type: 'fontawesome', action: b.action as Button['action'], shape: 'rounded',
      position: { row: Math.floor(index / 5), col: index % 5 }, size: { rows: 1, cols: 1 },
      style: { backgroundColor: b.style?.backgroundColor ?? template.color, textColor: b.style?.textColor ?? '#ffffff' },
      tooltip: b.tooltip ?? b.label, enabled: true
    }))
    const newScene: Scene = {
      id: `scene-${Date.now()}`, name: template.name, icon: template.icon[1] ?? 'layer-group',
      color: template.color, pages: [{ id: `page-${Date.now()}`, name: 'Page 1', buttons, grid_config: { rows: 4, cols: 5 } }],
      appId: template.id, autoCreated: false
    }
    dashboardStore.addScene(newScene)
    notificationsStore.success('Scene added', `"${template.name}" scene added to your dashboard.`)
  } finally { addingTemplate.value = null }
}

const backgroundFileInput = ref<HTMLInputElement | null>(null)
const uploadingBackground = ref(false)
const sceneBackgroundFileInput = ref<HTMLInputElement | null>(null)
const uploadingSceneBackground = ref(false)
const screensaverBgFileInput = ref<HTMLInputElement | null>(null)
const uploadingScreensaverBackground = ref(false)

const backgroundsByGroup = computed(() => ({
  default: BACKGROUNDS.filter(b => b.group === 'default'),
  gradient: BACKGROUNDS.filter(b => b.group === 'gradient'),
  animated: BACKGROUNDS.filter(b => b.group === 'animated'),
}))

const backgroundPickerGroups = computed<BackgroundPickerGroup[]>(() => {
  const groups: BackgroundPickerGroup[] = [
    { label: 'Default', options: backgroundsByGroup.value.default },
    ...(isCustomBackground.value
      ? [
          {
            label: 'Custom Background',
            options: [{ id: settings.value.background, label: 'Custom Uploaded Image' }]
          }
        ]
      : []),
    { label: 'Gradients', options: backgroundsByGroup.value.gradient },
    { label: 'Animated', options: backgroundsByGroup.value.animated }
  ]
  return groups
})

const isCustomBackground = computed(() => isImageBackground(settings.value.background))

// Screensaver gets its own background picker: 'default' means the classic
// dark screensaver look, not the dashboard's gradient, so the option is
// relabeled here instead of reusing backgroundPickerGroups.
const screensaverPickerGroups = computed<BackgroundPickerGroup[]>(() => [
  { label: 'Default', options: [{ id: 'default', label: 'Default (Dark)' }] },
  ...(isCustomScreensaverBackground.value
    ? [
        {
          label: 'Custom Background',
          options: [{ id: settingsStore.screensaverBackground, label: 'Custom Uploaded Image' }]
        }
      ]
    : []),
  { label: 'Gradients', options: backgroundsByGroup.value.gradient },
  { label: 'Animated', options: backgroundsByGroup.value.animated }
])

const isCustomScreensaverBackground = computed(() =>
  isImageBackground(settingsStore.screensaverBackground)
)
const currentScene = computed(() => dashboardStore.currentScene)

// DL-054: per-scene background rows — every scene in the profile gets a row,
// not just the active one. The hidden file input is shared; sceneBgTargetId
// remembers which row's Pick button opened it.
const sceneList = computed<Scene[]>(() => dashboardStore.currentProfile?.scenes ?? [])
const sceneBgTargetId = ref<string | null>(null)

function sceneAppEntryFor(scene: Scene) {
  return appForScene(scene, appIntegrations.value)
}
function sceneEffectiveImage(scene: Scene): string | undefined {
  if (scene.background?.image) return scene.background.image
  return scene.disableAppBackground ? undefined : sceneAppEntryFor(scene)?.image
}
function sceneBackgroundDesc(scene: Scene): string {
  if (scene.background?.image) return 'Custom image override'
  if (scene.disableAppBackground) return 'Using the dashboard background'
  const app = sceneAppEntryFor(scene)
  return app ? `Bundled ${app.label} artwork` : 'Using the dashboard background'
}
function pickSceneBackground(scene: Scene) {
  sceneBgTargetId.value = scene.id
  sceneBackgroundFileInput.value?.click()
}
function toggleAppDefaultBackgroundFor(scene: Scene, event: Event) {
  const enabled = (event.target as HTMLInputElement).checked
  dashboardStore.updateScene(scene.id, { disableAppBackground: !enabled })
}
function removeSceneBackgroundFor(scene: Scene) {
  dashboardStore.updateScene(scene.id, { background: undefined })
  const app = sceneAppEntryFor(scene)
  notificationsStore.success(
    'Scene background removed',
    app ? `Reverted to the ${app.label} default.` : `Background cleared for "${scene.name}".`
  )
}

const handleBackgroundUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  if (!['image/png','image/jpeg','image/jpg','image/gif'].includes(file.type)) { notificationsStore.error('Invalid file', 'Please upload a PNG, JPG, or GIF image.'); return }
  if (file.size > 10 * 1024 * 1024) { notificationsStore.error('File too large', 'Maximum file size is 10MB.'); return }
  uploadingBackground.value = true
  try {
    const formData = new FormData()
    formData.append('file', file); formData.append('type', 'dashboard_background')
    const response = await apiClient.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    if (response.data.success) {
      const url = response.data.url.startsWith('/api') ? response.data.url : '/api' + response.data.url
      settingsStore.background = url
      notificationsStore.success('Background updated', 'Custom background applied successfully.')
    } else { notificationsStore.error('Upload failed', response.data.error || 'Unknown error') }
  } catch (error: any) { notificationsStore.error('Upload failed', error.message || 'Unknown error') }
  finally { uploadingBackground.value = false; if (target) target.value = '' }
}

const handleSceneBackgroundUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  const scene = sceneList.value.find(s => s.id === sceneBgTargetId.value)
  if (!file || !scene) return
  if (!['image/png','image/jpeg','image/jpg','image/gif'].includes(file.type)) { notificationsStore.error('Invalid file', 'Please upload a PNG, JPG, or GIF image.'); return }
  if (file.size > 10 * 1024 * 1024) { notificationsStore.error('File too large', 'Maximum file size is 10MB.'); return }
  uploadingSceneBackground.value = true
  try {
    const formData = new FormData()
    formData.append('file', file); formData.append('type', 'dashboard_background')
    const response = await apiClient.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    if (response.data.success) {
      const url = response.data.url.startsWith('/api') ? response.data.url : '/api' + response.data.url
      dashboardStore.updateScene(scene.id, { background: { type: 'image', image: url } })
      notificationsStore.success('Scene background updated', `Background applied to "${scene.name}".`)
    } else { notificationsStore.error('Upload failed', response.data.error || 'Unknown error') }
  } catch (error: any) { notificationsStore.error('Upload failed', error.message || 'Unknown error') }
  finally { uploadingSceneBackground.value = false; sceneBgTargetId.value = null; if (target) target.value = '' }
}

const removeCustomBackground = () => { settingsStore.background = 'default'; notificationsStore.success('Background removed', 'Reverted to default background.') }

const handleScreensaverBackgroundUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  if (!['image/png','image/jpeg','image/jpg','image/gif'].includes(file.type)) { notificationsStore.error('Invalid file', 'Please upload a PNG, JPG, or GIF image.'); return }
  if (file.size > 10 * 1024 * 1024) { notificationsStore.error('File too large', 'Maximum file size is 10MB.'); return }
  uploadingScreensaverBackground.value = true
  try {
    const formData = new FormData()
    formData.append('file', file); formData.append('type', 'dashboard_background')
    const response = await apiClient.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    if (response.data.success) {
      const url = response.data.url.startsWith('/api') ? response.data.url : '/api' + response.data.url
      settingsStore.screensaverBackground = url
      notificationsStore.success('Screensaver background updated', 'Custom background applied successfully.')
    } else { notificationsStore.error('Upload failed', response.data.error || 'Unknown error') }
  } catch (error: any) { notificationsStore.error('Upload failed', error.message || 'Unknown error') }
  finally { uploadingScreensaverBackground.value = false; if (target) target.value = '' }
}

const removeScreensaverBackground = () => {
  settingsStore.screensaverBackground = 'default'
  notificationsStore.success('Screensaver background removed', 'Reverted to the default dark look.')
}

const applyingButtonBehaviour = ref(false)

// Settings autosave via the store's deep watch — this explicit action makes
// the apply visible and covers Settings open in a second window, where the
// dashboard wouldn't see the change until manually refreshed. It also commits
// the local design draft (preview refs) to the persisted defaults.
function saveAndApplyButtonSettings() {
  settingsStore.buttonDefaultAnimation = previewAnimation.value
  settingsStore.buttonDefaultIconLoop = previewIconLoop.value
  settingsStore.buttonDefaultEffect = previewEffect.value
  settingsStore.saveSettings()
  requestVdockRefresh()
  notificationsStore.success('Applied', 'Button settings saved and applied to the dashboard.')
}

async function applyButtonBehaviourToAll() {
  applyingButtonBehaviour.value = true
  try {
    settingsStore.buttonDefaultAnimation = previewAnimation.value
    settingsStore.buttonDefaultIconLoop = previewIconLoop.value
    settingsStore.buttonDefaultEffect = previewEffect.value
    settingsStore.saveSettings()

    await dashboardStore.applyGlobalButtonStyle({
      animation: previewAnimation.value,
      iconLoop: previewIconLoop.value,
      effect: previewEffect.value
    })

    // applyGlobalButtonStyle mutates the dashboard/profile store, which — unlike
    // the settings store — has no live cross-window sync. If Settings is open in
    // a separate window/tab (e.g. via "Open in browser"), the actual dashboard
    // window wouldn't otherwise see this until it was manually refreshed.
    requestVdockRefresh()

    notificationsStore.success('Button style applied', 'Animation, icon motion, and effect applied to every button on your dashboard.')
  } catch (err: any) {
    notificationsStore.error('Failed to apply', err?.message || 'Could not apply the button style to all buttons.')
  } finally {
    applyingButtonBehaviour.value = false
  }
}

const screensaverWidgetOptions = [
  { id: 'weather', label: 'Weather', description: 'Current temperature and conditions' },
  { id: 'news', label: 'News', description: 'Rotating headlines from free RSS feeds' },
  { id: 'sports', label: 'Sports News', description: 'Sports headlines from free RSS feeds' },
  { id: 'market', label: 'Stocks / Crypto', description: 'Free stock & crypto quotes — no key' },
  { id: 'worldclock', label: 'World Clock', description: 'Time in a few other cities' },
]

// Widget config cards collapse to a header row — tap to expand one at a
// time so the tab fits a 600px touchscreen without scrolling.
const openWidgetCard = ref<string | null>(null)
function toggleWidgetCard(id: string) {
  openWidgetCard.value = openWidgetCard.value === id ? null : id
}

function toggleScreensaverWidget(id: string) {
  const list = settingsStore.screensaverWidgets
  const idx = list.indexOf(id)
  if (idx === -1) {
    settingsStore.screensaverWidgets = [...list, id]
  } else {
    settingsStore.screensaverWidgets = list.filter(w => w !== id)
    // Disabling the widget whose config card is open would leave
    // openWidgetCard pointing at a removed card — the picker stays
    // collapsed with nothing open to close. Release it.
    if (openWidgetCard.value === id) openWidgetCard.value = null
  }
}

// DL-028: section-level reset restores the default five-widget set.
const screensaverWidgetsAtDefault = computed(() =>
  settingsStore.screensaverWidgets.length === SETTINGS_DEFAULTS.screensaverWidgets.length &&
  SETTINGS_DEFAULTS.screensaverWidgets.every(w => settingsStore.screensaverWidgets.includes(w))
)
function resetScreensaverWidgets() {
  settingsStore.screensaverWidgets = [...SETTINGS_DEFAULTS.screensaverWidgets]
}

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

type TestResult = { ok: boolean; text: string }
const testingNews = ref(false)
const testingSports = ref(false)
const newsTestResult = ref<TestResult | null>(null)
const sportsTestResult = ref<TestResult | null>(null)
const marketTestResult = ref<TestResult | null>(null)

// Inline result next to the button plus a toast — toasts auto-dismiss, so
// the inline line is what persists as the visible answer.
function describeTestError(err: any, fallback: string): string {
  const status = err?.response?.status
  if (status === 429) return 'Server rate limit reached — wait a moment and retry.'
  if (!err?.response) return 'Server unreachable — is the backend running?'
  return err?.message || fallback
}

async function testFeeds(feeds: string[], testing: typeof testingNews, result: typeof newsTestResult) {
  testing.value = true
  result.value = null
  try {
    const count = await testNewsConnection(feeds)
    const text = `${count} headlines fetched`
    result.value = { ok: true, text }
    notificationsStore.success(
      'Feeds working',
      `Fetched ${count} headlines from ${feeds.length || 'the built-in'} ${feeds.length === 1 ? 'feed' : 'feeds'}.`
    )
  } catch (err: any) {
    const text = describeTestError(err, 'Could not read those feeds.')
    result.value = { ok: false, text }
    notificationsStore.error('Feed test failed', text)
  } finally {
    testing.value = false
  }
}
async function handleTestNews() {
  await testFeeds(parseFeedList(settingsStore.newsFeeds), testingNews, newsTestResult)
}
async function handleTestSports() {
  const feeds = parseFeedList(settingsStore.sportsFeeds)
  await testFeeds(feeds.length ? feeds : DEFAULT_SPORTS_FEEDS, testingSports, sportsTestResult)
}

const testingMarket = ref(false)
async function handleTestMarket() {
  testingMarket.value = true
  marketTestResult.value = null
  try {
    const tickers = parseTickers(settingsStore.marketTickers)
    await testMarketConnection(tickers)
    const text = tickers.length
      ? `Quotes fetched for ${tickers.join(', ')}`
      : 'Crypto prices fetched from CoinGecko'
    marketTestResult.value = { ok: true, text }
    notificationsStore.success('Market data connected', text + '.')
  } catch (err: any) {
    const text = describeTestError(err, 'Could not reach the price API.')
    marketTestResult.value = { ok: false, text }
    notificationsStore.error('Market connection failed', text)
  } finally {
    testingMarket.value = false
  }
}

const runningApps = ref<RunningApp[]>([])
const loadingApps = ref(false)
const appIntegrations = useAppIntegrations()
const autoSwitchingEnabled = ref(false)
const showShortcutManager = ref(false)
const selectedAppForShortcuts = ref<RunningApp | null>(null)
const appSearch = ref('')
const appProfiles = ref<AppProfileDto[]>([])
const appProfilesLoaded = ref(false)

// VDock is a development companion: dev tools sort above everything else.
// Tier 0 is stronger still — an exe with a backend app profile means VDock
// actually has keystroke actions for it.
const DEV_APP_EXES = new Set([
  'code.exe', 'code - insiders.exe', 'cursor.exe', 'devenv.exe', 'zed.exe',
  'rider64.exe', 'idea64.exe', 'webstorm64.exe', 'pycharm64.exe',
  'clion64.exe', 'goland64.exe', 'phpstorm64.exe', 'rubymine64.exe',
  'datagrip64.exe', 'rustrover64.exe', 'fleet64.exe', 'studio64.exe',
  'sublime_text.exe', 'notepad++.exe', 'neovide.exe',
  'windowsterminal.exe', 'wt.exe', 'cmd.exe', 'powershell.exe', 'pwsh.exe',
  'bash.exe', 'wsl.exe', 'wezterm-gui.exe', 'alacritty.exe', 'tabby.exe',
  'termius.exe', 'putty.exe',
  'gitkraken.exe', 'githubdesktop.exe', 'sourcetree.exe', 'fork.exe',
  'postman.exe', 'insomnia.exe', 'bruno.exe',
  'docker desktop.exe', 'com.docker.backend.exe', 'rancher desktop.exe',
  'podman.exe', 'dbeaver.exe', 'mongodbcompass.exe',
  'node.exe', 'python.exe', 'pythonw.exe', 'devtunnel.exe',
])

// Friendly queries -> exes, so "terminal" finds Windows Terminal, etc.
const APP_ALIASES: Record<string, string[]> = {
  vscode: ['code.exe', 'code - insiders.exe'],
  'vs code': ['code.exe', 'code - insiders.exe'],
  'visual studio code': ['code.exe'],
  'visual studio': ['devenv.exe'],
  terminal: ['windowsterminal.exe', 'wt.exe', 'cmd.exe', 'powershell.exe', 'pwsh.exe', 'wezterm-gui.exe', 'alacritty.exe', 'tabby.exe'],
  claude: ['windowsterminal.exe', 'wt.exe', 'cmd.exe', 'powershell.exe', 'pwsh.exe'],
  browser: ['chrome.exe', 'msedge.exe', 'firefox.exe', 'brave.exe', 'opera.exe'],
  git: ['gitkraken.exe', 'githubdesktop.exe', 'sourcetree.exe', 'fork.exe'],
  github: ['githubdesktop.exe'],
  docker: ['docker desktop.exe', 'com.docker.backend.exe', 'rancher desktop.exe'],
  jetbrains: ['idea64.exe', 'webstorm64.exe', 'pycharm64.exe', 'rider64.exe', 'clion64.exe', 'goland64.exe', 'phpstorm64.exe'],
  editor: ['code.exe', 'cursor.exe', 'sublime_text.exe', 'notepad++.exe', 'devenv.exe', 'zed.exe'],
}

const appProfileByExe = computed(() => {
  const map = new Map<string, AppProfileDto>()
  for (const profile of appProfiles.value) {
    for (const exe of profile.exes) {
      const key = exe.toLowerCase()
      if (!map.has(key)) map.set(key, profile)
    }
  }
  return map
})

function appTier(app: RunningApp): number {
  const exe = app.exe.toLowerCase()
  if (appProfileByExe.value.has(exe)) return 0
  if (DEV_APP_EXES.has(exe)) return 1
  return 2
}

function appBadge(app: RunningApp): string | null {
  const exe = app.exe.toLowerCase()
  return appProfileByExe.value.get(exe)?.label ?? (DEV_APP_EXES.has(exe) ? 'Dev' : null)
}

const filteredApps = computed(() => {
  const query = appSearch.value.trim().toLowerCase()
  let list = runningApps.value
  if (query) {
    const aliases = APP_ALIASES[query] ?? []
    list = list.filter((app) => {
      const name = app.name.toLowerCase()
      const exe = app.exe.toLowerCase()
      return name.includes(query) || exe.includes(query) || aliases.includes(exe)
    })
  }
  return [...list].sort(
    (a, b) => appTier(a) - appTier(b) || a.name.localeCompare(b.name)
  )
})
const startOnBootStatus = ref<{success: boolean, message: string} | null>(null)

const availableScenes = computed(() => {
  const profile = dashboardStore.currentProfile
  if (!profile) return []
  return (profile.scenes || []).map((scene: Scene) => ({ id: scene.id, name: scene.name }))
})

const tabs = [
  { id: 'appearance', name: 'Appearance', icon: ['fas', 'palette'] },
  { id: 'templates', name: 'Templates', icon: ['fas', 'layer-group'] },
  { id: 'server', name: 'Server', icon: ['fas', 'server'] },
  { id: 'integration', name: 'Integrations', icon: ['fas', 'plug'] },
  { id: 'connect', name: 'Connect a device', icon: ['fas', 'mobile-screen-button'] },
  { id: 'logs', name: 'Logs', icon: ['fas', 'file-lines'] },
  { id: 'about', name: 'About', icon: ['fas', 'info-circle'] }
]

interface SettingsSearchEntry {
  label: string
  keywords: string
  tabId: string
  subTab?: 'buttons' | 'layout' | 'background' | 'screensaver'
  /** Nested tab inside 'buttons' (DL-035) or 'screensaver' (DL-032). */
  deepTab?: 'display' | 'preview' | 'touch' | 'widgets' | 'settings' | 'backgrounds'
  icon: [string, string]
}

const settingsSearchIndex: SettingsSearchEntry[] = [
  { label: 'Touch Mode', keywords: 'touch mode finger tablet target size', tabId: 'appearance', subTab: 'buttons', deepTab: 'touch', icon: ['fas', 'hand-pointer'] },
  { label: 'Button Display', keywords: 'button size labels tooltips', tabId: 'appearance', subTab: 'buttons', deepTab: 'display', icon: ['fas', 'th-large'] },
  { label: 'Button Behaviour', keywords: 'button animation icon loop effect style apply all', tabId: 'appearance', subTab: 'buttons', deepTab: 'preview', icon: ['fas', 'sliders'] },
  { label: 'Notifications', keywords: 'notifications toast alerts', tabId: 'appearance', subTab: 'layout', icon: ['fas', 'bell'] },
  { label: 'Sidebar', keywords: 'docked sidebar width', tabId: 'appearance', subTab: 'layout', icon: ['fas', 'columns'] },
  { label: 'Screensaver Delay', keywords: 'screensaver idle timeout sleep', tabId: 'appearance', subTab: 'screensaver', deepTab: 'settings', icon: ['fas', 'moon'] },
  { label: 'Screensaver Widgets', keywords: 'screensaver widgets weather news stocks crypto world clock', tabId: 'appearance', subTab: 'screensaver', deepTab: 'widgets', icon: ['fas', 'grip'] },
  { label: 'Weather Widget Size', keywords: 'screensaver weather size scale small screen touch', tabId: 'appearance', subTab: 'screensaver', deepTab: 'widgets', icon: ['fas', 'cloud-sun'] },
  { label: 'Background', keywords: 'background animation particles waves aurora image wallpaper gradient', tabId: 'appearance', subTab: 'background', icon: ['fas', 'image'] },
  { label: 'Session Logs', keywords: 'logs errors troubleshoot debug export download', tabId: 'logs', icon: ['fas', 'file-lines'] },
  { label: 'App Templates', keywords: 'templates presets apps buttons', tabId: 'templates', icon: ['fas', 'layer-group'] },
  { label: 'Server Configuration', keywords: 'server host port connection', tabId: 'server', icon: ['fas', 'server'] },
  { label: 'Launch on startup', keywords: 'startup boot autostart launch windows mac login', tabId: 'server', icon: ['fas', 'power-off'] },
  { label: 'Startup', keywords: 'startup boot autostart launcher terminal close debug', tabId: 'server', icon: ['fas', 'power-off'] },
  { label: 'Open Settings in New Tab', keywords: 'settings browser tab window navigation external', tabId: 'server', icon: ['fas', 'up-right-from-square'] },
  { label: 'Weather Widget Location', keywords: 'weather location city temperature geolocation', tabId: 'appearance', subTab: 'screensaver', deepTab: 'widgets', icon: ['fas', 'cloud-sun'] },
  { label: 'Auto Scene Switching', keywords: 'auto scene switching monitored applications', tabId: 'integration', icon: ['fas', 'shuffle'] },
  { label: 'Running Applications', keywords: 'running apps processes filter search dev tools', tabId: 'integration', icon: ['fas', 'desktop'] },
  { label: 'Connect a device', keywords: 'connect device phone tablet qr lan wifi pair second deck', tabId: 'connect', icon: ['fas', 'mobile-screen-button'] },
  { label: 'About VDock', keywords: 'version about info', tabId: 'about', icon: ['fas', 'info-circle'] }
]

const settingsSearch = ref('')
const searchMatches = computed(() => {
  const query = settingsSearch.value.trim().toLowerCase()
  if (!query) return []
  return settingsSearchIndex.filter(
    (entry) => entry.label.toLowerCase().includes(query) || entry.keywords.includes(query)
  )
})

// DL-054: deepTab no longer selects a nested tab row — it names the panel the
// setting lives in, so a search hit scrolls straight to it.
const deepTabAnchor: Record<string, string> = {
  display: 'display',
  preview: 'design',
  touch: 'touch',
  widgets: 'ss-widgets',
  settings: 'ss-activation',
  backgrounds: 'ss-background',
}

function searchEntryCrumb(match: SettingsSearchEntry): string {
  const tab = tabs.find(t => t.id === match.tabId)?.name ?? match.tabId
  const sub = match.subTab ? appearanceSubs.find(s => s.id === match.subTab)?.name : undefined
  return sub ? `${tab} · ${sub}` : tab
}

function jumpToSearchResult(match: SettingsSearchEntry) {
  activeTab.value = match.tabId
  if (match.subTab) appearanceSubTab.value = match.subTab
  settingsSearch.value = ''
  const anchor = match.deepTab ? deepTabAnchor[match.deepTab] : undefined
  if (anchor) scrollToPanel(anchor)
  else scrollContentTop()
}

async function clearRecentActions() {
  const ok = await confirmDialog({
    title: 'Clear recent actions?',
    message: 'The list of recently used actions will be emptied.',
    confirmLabel: 'Clear',
    icon: 'clock-rotate-left',
  })
  if (ok) settingsStore.clearRecentActions()
}

async function syncStartOnBootFromSystem() {
  try {
    const response = await apiClient.get('/system/autostart')
    if (response.data?.success && typeof response.data.enabled === 'boolean') {
      settingsStore.startOnBoot = response.data.enabled
    }

    if (window.electronAPI?.isAutoLaunchEnabled) {
      const electronAutoLaunchEnabled = await window.electronAPI.isAutoLaunchEnabled()
      settingsStore.startOnBoot = electronAutoLaunchEnabled || settingsStore.startOnBoot
    }
  } catch (error) {
    console.warn('Failed to read launch-on-startup status:', error)
  }
}

// Single cross-platform "launch automatically" toggle. Always registers the
// backend's own OS-level autostart (works whether you're running via browser
// or Electron), and additionally syncs Electron's own auto-launch mechanism
// when running inside the desktop app, so both stay consistent instead of
// needing two separate toggles for what is, to the user, one setting.
async function handleStartOnBootToggle() {
  const desired = settings.value.startOnBoot
  try {
    const response = await apiClient.post('/system/autostart', { enabled: desired })
    if (!response.data.success) {
      startOnBootStatus.value = { success: false, message: response.data.message || 'Failed to update auto-start setting' }
      settings.value.startOnBoot = !desired
      setTimeout(() => { startOnBootStatus.value = null }, 5000)
      return
    }

    if (window.electronAPI) {
      await window.electronAPI.toggleAutoLaunch(desired)
    }

    startOnBootStatus.value = { success: true, message: desired ? 'VDock will now start automatically when your computer starts' : 'Auto-start disabled' }
  } catch {
    startOnBootStatus.value = { success: false, message: 'Failed to update auto-start setting. This feature may require administrator privileges.' }
    settings.value.startOnBoot = !desired
  }
  setTimeout(() => { startOnBootStatus.value = null }, 5000)
}

function formatScreensaverTimeout(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return s === 0 ? `${m}m` : `${m}m ${s}s`
}



// "Launch Tutorial" — flag the request, then go to the dashboard where the
// tour measures live targets on mount.
function launchTutorial() {
  useTutorial().requestLaunch()
  router.push('/')
}

function toggleAppScanning() {
  settingsStore.appScanningEnabled = !settingsStore.appScanningEnabled
  if (settingsStore.appScanningEnabled) void refreshRunningApps()
  else runningApps.value = []
}

// --- Agent attention alerts -------------------------------------------------
const agentHookInstalled = ref(false)
const agentHookStatus = ref(false) // whether we've asked the backend yet
const installingHook = ref(false)

function toggleAgentAlerts() {
  settingsStore.agentAlertsEnabled = !settingsStore.agentAlertsEnabled
}

async function fetchAgentHookStatus() {
  try {
    const res = await apiClient.get('/agent-events/hook-status')
    agentHookInstalled.value = !!res.data?.installed
    agentHookStatus.value = true
  } catch {
    agentHookStatus.value = false
  }
}

async function installAgentHook() {
  installingHook.value = true
  try {
    const res = await apiClient.post('/agent-events/install-hook')
    if (res.data?.success) {
      agentHookInstalled.value = true
      agentHookStatus.value = true
      notificationsStore.success(
        'Agent alerts enabled',
        'Claude Code will pop an alert when it waits for you.'
      )
    } else {
      notificationsStore.error('Hook install failed', res.data?.error || 'Unknown error')
    }
  } catch (e: any) {
    notificationsStore.error('Hook install failed', e?.response?.data?.error || 'Backend unreachable')
  } finally {
    installingHook.value = false
  }
}

async function refreshRunningApps() {
  if (!settingsStore.appScanningEnabled) {
    runningApps.value = []
    return
  }
  loadingApps.value = true
  if (!appProfilesLoaded.value) {
    appProfilesLoaded.value = true
    fetchAppProfiles()
      .then((profiles) => { appProfiles.value = profiles })
      .catch(() => { appProfilesLoaded.value = false })
  }
  try {
    const response = await apiClient.get('/metrics/running-apps')
    runningApps.value = response.data.success ? (response.data.data ?? []) : []
    if (!response.data.success) {
      console.error('Failed to load running applications:', response.data.error)
    }
  } catch (error) {
    console.error('Failed to load running applications:', error)
    runningApps.value = []
  } finally {
    loadingApps.value = false
  }
}

function isAppIntegrationEnabled(appExe: string): boolean { return appIntegrations.value.some(i => i.appExe === appExe && i.enabled) }
function getAppScene(appExe: string): string { return appIntegrations.value.find(i => i.appExe === appExe)?.sceneId || '' }

function toggleAppIntegration(app: RunningApp) {
  const idx = appIntegrations.value.findIndex(i => i.appExe === app.exe)
  if (idx >= 0) { appIntegrations.value[idx].enabled = !appIntegrations.value[idx].enabled }
  else { appIntegrations.value.push({ appExe: app.exe, appName: app.name, sceneId: '', enabled: true, autoCreateScene: false }) }
  saveAppIntegrations()
}

function updateAppScene(appExe: string, sceneId: string) {
  const integration = appIntegrations.value.find(i => i.appExe === appExe)
  if (integration) { integration.sceneId = sceneId; saveAppIntegrations() }
}

async function createSceneForApp(app: RunningApp) {
  const profile = dashboardStore.currentProfile
  if (!profile) { notificationsStore.error('No profile', 'No profile loaded.'); return }
  const sceneName = app.name.replace('.exe', '')
  try {
    const profiles = await fetchAppProfiles()
    const topShortcuts = hasAppShortcuts(profiles, app.exe) ? topAppShortcuts(profiles, app.exe, 8) : []
    const buttons: Button[] = topShortcuts.map((shortcut, index) => createButtonFromShortcut(shortcut, index))
    const newScene: Scene = {
      id: `scene-${Date.now()}`, name: sceneName, icon: 'window-maximize', color: '#3498db',
      pages: [{ id: `page-${Date.now()}`, name: 'Page 1', buttons, grid_config: { rows: 4, cols: 5 } }],
      triggeredByApp: app.exe, appId: appIdForExe(app.exe), autoCreated: true
    }
    dashboardStore.addScene(newScene)
    updateAppScene(app.exe, newScene.id)
    notificationsStore.success('Scene created', `"${sceneName}" created with ${buttons.length} shortcut buttons`)
  } catch { notificationsStore.error('Create failed', 'Failed to create scene') }
}

function createButtonFromShortcut(shortcut: AppShortcut, index: number): Button {
  return {
    id: `button-${Date.now()}-${index}`, label: shortcut.name, secondary_label: shortcut.keys.join(' + '),
    icon: ['fas', 'keyboard'], icon_type: 'fontawesome',
    action: { type: 'hotkey', config: { keys: shortcut.keys } }, shape: 'rounded',
    position: { row: Math.floor(index / 5), col: index % 5 }, size: { rows: 1, cols: 1 },
    style: { backgroundColor: '#3498db', textColor: '#ffffff' }, tooltip: shortcut.description, enabled: true
  }
}

function openShortcutManager(app: RunningApp) { selectedAppForShortcuts.value = app; showShortcutManager.value = true }

function handleAddShortcut(shortcut: AppShortcut) {
  const sceneId = getAppScene(selectedAppForShortcuts.value?.exe || '')
  if (!sceneId) { notificationsStore.error('No scene', 'Please create a scene first'); return }
  const profile = dashboardStore.currentProfile
  if (!profile) return
  const scene = profile.scenes.find(s => s.id === sceneId)
  if (!scene?.pages?.length) { notificationsStore.error('Scene missing', 'Scene not found'); return }
  const page = scene.pages[0]
  const buttons = page.buttons || []
  let emptySlot = null
  for (let row = 0; row < page.grid_config.rows && !emptySlot; row++) {
    for (let col = 0; col < page.grid_config.cols && !emptySlot; col++) {
      if (!buttons.some(b => b.position.row === row && b.position.col === col)) emptySlot = { row, col }
    }
  }
  if (!emptySlot) { notificationsStore.error('Scene full', 'No empty slots available in the scene'); return }
  const newButton = createButtonFromShortcut(shortcut, 0)
  newButton.position = emptySlot
  dashboardStore.addButton(newButton)
  showShortcutManager.value = false
  notificationsStore.success('Shortcut added', `"${shortcut.name}" added to scene`)
}

function saveAppIntegrations() {
  setAppIntegrations(appIntegrations.value)
  autoSceneSwitcher.updateIntegrations(appIntegrations.value)
}

function loadAppIntegrations() {
  reloadAppIntegrations()
  autoSceneSwitcher.updateIntegrations(appIntegrations.value)
  const autoSwitchStored = localStorage.getItem('autoSceneSwitching')
  if (autoSwitchStored) autoSwitchingEnabled.value = autoSwitchStored === 'true'
}

// Actual scene-switching callback is owned by App.vue for the app's whole
// lifetime; this only flips the enabled state the singleton acts on.
async function toggleAutoSwitching() {
  const newValue = !autoSwitchingEnabled.value
  try {
    if (newValue) {
      autoSceneSwitcher.initialize(appIntegrations.value)
      const success = await autoSceneSwitcher.enable()
      if (success) { autoSwitchingEnabled.value = true; localStorage.setItem('autoSceneSwitching', 'true') }
      else notificationsStore.error('Auto-switching', 'Failed to enable auto scene switching')
    } else {
      const success = await autoSceneSwitcher.disable()
      if (success) { autoSwitchingEnabled.value = false; localStorage.setItem('autoSceneSwitching', 'false') }
      else notificationsStore.error('Auto-switching', 'Failed to disable auto scene switching')
    }
  } catch { notificationsStore.error('Auto-switching', 'Error toggling auto scene switching') }
}

function applySettingsRouteQuery() {
  const tabQuery = route.query.tab
  if (typeof tabQuery === 'string' && tabs.some((tab) => tab.id === tabQuery)) {
    activeTab.value = tabQuery
  }

  const subQuery = route.query.sub
  if (
    typeof subQuery === 'string' &&
    appearanceSubs.some(s => s.id === subQuery)
  ) {
    appearanceSubTab.value = subQuery as AppearanceSubId
  }
}

// Settings is normally opened from within the already-running dashboard,
// which has already loaded a profile into dashboardStore. But when opened as
// its own standalone browser tab it's a fresh app instance with no profile
// loaded at all, which left features like "Scene Background" permanently
// disabled (no current scene to override). Mirrors the profile-loading logic
// in DashboardView's onMounted.
async function ensureProfileLoaded() {
  if (dashboardStore.currentProfile) return

  const lastProfileId = localStorage.getItem(LAST_PROFILE_STORAGE_KEY)
  if (lastProfileId) {
    const profile = await profilesStore.getProfile(lastProfileId)
    if (profile) {
      dashboardStore.setProfile(profile)
      return
    }
  }

  await profilesStore.loadProfiles()
  if (profilesStore.profiles.length > 0) {
    const profile = await profilesStore.getProfile(profilesStore.profiles[0].id)
    if (profile) {
      dashboardStore.setProfile(profile)
    }
  }
}

watch(activeTab, (tab) => {
  scrollContentTop()
  if (tab === 'integration') {
    void refreshRunningApps()
    void fetchAgentHookStatus()
  }
  if (tab === 'connect') {
    // DL-057: present the QR immediately — refresh the LAN URL, then wait
    // for the canvas to mount before drawing.
    void settingsStore.loadServerConfig().then(() => nextTick(renderQr))
  }
  if (tab === 'logs') {
    void loadLogs()
  }
})

onMounted(async () => {
  applySettingsRouteQuery()
  await ensureProfileLoaded()
  await syncStartOnBootFromSystem()
  settingsStore.loadServerConfig().then(() => renderQr())
  loadPorts()
  loadAppIntegrations()
  if (activeTab.value === 'integration') { await refreshRunningApps(); void fetchAgentHookStatus() }
  if (activeTab.value === 'logs') void loadLogs()
})
</script>

<style scoped>

/* ── Retained functional styles (logs viewer, integrations list, templates) ── */

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
}
.log-file-row:active { background: rgba(255, 255, 255, 0.05); }

.log-file-row.active {
  border-color: var(--color-accent, #4aa3ff);
  background: color-mix(in srgb, var(--color-accent, #4aa3ff) 14%, transparent);
}

.log-file-icon { color: var(--color-text-secondary); flex-shrink: 0; }

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

.log-line.log-error { color: #ff8a80; }

.log-line.log-warn { color: #f0c674; }

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

.status-msg {
  font-size: clamp(11px, 0.6vw + 8px, 13px);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  margin-top: var(--spacing-xs);
}

.status-success { background: rgba(39, 174, 96, 0.15); color: #27ae60; }

.status-error   { background: rgba(231, 76, 60, 0.15);  color: #e74c3c; }

.status-icon.success { color: var(--color-success, #27ae60); }

.test-result {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: var(--spacing-sm) 0 0;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-danger, #e74c3c);
  background: color-mix(in srgb, var(--color-danger, #e74c3c) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-danger, #e74c3c) 35%, transparent);
}

.test-result.ok {
  color: var(--color-success, #27ae60);
  background: color-mix(in srgb, var(--color-success, #27ae60) 12%, transparent);
  border-color: color-mix(in srgb, var(--color-success, #27ae60) 35%, transparent);
}

.app-integration-list {
  border: 1px solid var(--glass-border, var(--color-border));
  border-radius: var(--radius-md);
  overflow: hidden;
}

.list-header {
  display: grid;
  grid-template-columns: 1fr 80px 1fr 80px;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs) var(--spacing-md);
  background: rgba(0,0,0,0.15);
  font-size: clamp(10px, 0.5vw + 8px, 12px);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-secondary);
}

.app-item {
  display: grid;
  grid-template-columns: 1fr 80px 1fr 80px;
  gap: var(--spacing-sm);
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  border-top: 1px solid var(--glass-border, var(--color-border));
  transition: background var(--transition-fast);
  min-height: 56px;
}

@media (hover: hover) and (pointer: fine) {
  .app-item:hover { background: var(--color-surface-hover, rgba(255,255,255,0.04)); }
}
.app-item:active { background: rgba(255,255,255,0.06); }

.app-item--dev { border-left: 2px solid var(--color-primary, #3498db); }

.app-toolbar {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.app-search { position: relative; flex: 1; }

.app-search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-secondary);
  font-size: 0.8rem;
  pointer-events: none;
}

.app-search-input {
  width: 100%;
  box-sizing: border-box;
  padding: 8px 30px 8px 30px;
  border-radius: var(--radius-md);
  border: 1px solid var(--glass-border, var(--color-border));
  background: rgba(255, 255, 255, 0.06);
  color: var(--color-text);
  font-size: 0.85rem;
}

.app-search-input:focus {
  outline: none;
  border-color: var(--color-primary, #3498db);
}

.app-search-clear {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 4px;
}

@media (hover: hover) and (pointer: fine) {
  .app-search-clear:hover { color: var(--color-text); }
}

.app-count {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.app-badge {
  margin-left: var(--spacing-xs);
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 0.62rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.app-badge--profile {
  background: color-mix(in srgb, var(--color-primary, #3498db) 22%, transparent);
  color: var(--color-primary, #3498db);
}

.app-filter-empty { padding: var(--spacing-md); }

.app-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  min-width: 0;
}

.app-icon { color: var(--color-text-secondary); flex-shrink: 0; }

.app-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.app-name {
  font-size: clamp(12px, 0.7vw + 9px, 14px);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.app-exe {
  font-size: clamp(10px, 0.5vw + 8px, 12px);
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.app-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: clamp(11px, 0.6vw + 8px, 13px);
}

.status-text { color: var(--color-text-secondary); }

.app-scene { min-width: 0; }

.select-sm {
  width: 100%;
  padding: 4px 8px;
  background: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: clamp(11px, 0.6vw + 8px, 13px);
  min-height: 32px;
}

.scene-placeholder { color: var(--color-text-secondary); font-size: clamp(12px, 0.7vw + 9px, 14px); }

.app-actions {
  display: flex;
  gap: var(--spacing-xs);
  justify-content: flex-end;
}

.btn-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast);
}

@media (hover: hover) and (pointer: fine) {
  .btn-icon:hover { background: var(--color-surface-hover); color: var(--color-text); }
}

.btn-icon.btn-primary { background: var(--color-primary); color: white; border-color: var(--color-primary); }

.integration-summary {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: clamp(11px, 0.6vw + 8px, 13px);
  color: var(--color-text-secondary);
  border-top: 1px solid var(--glass-border, var(--color-border));
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xl);
  color: var(--color-text-secondary);
  font-size: clamp(12px, 0.7vw + 9px, 14px);
  text-align: center;
}

.template-category {
  margin-bottom: var(--spacing-md);
}

.category-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  background: transparent;
  border: none;
  color: var(--color-text);
  cursor: pointer;
  padding: 0;
  font-size: clamp(13px, 0.8vw + 10px, 16px);
  font-weight: 600;
  min-height: 44px;
  transition: background-color 0.12s ease;
}
@media (hover: hover) and (pointer: fine) {
  .category-header:hover { background-color: rgba(255, 255, 255, 0.02); }
}
.category-header:active { background-color: rgba(255, 255, 255, 0.035); }
.category-header:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }

.category-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.category-icon { color: var(--color-primary, #3498db); }

.category-chevron {
  color: var(--color-text-secondary);
  transition: transform 200ms var(--ease-out);
}

.category-chevron.chevron-open { transform: rotate(180deg); }

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
}

.template-card {
  border: 1px solid var(--glass-border, var(--color-border));
  border-radius: var(--radius-md);
  overflow: hidden;
  background: rgba(0,0,0,0.15);
  transition: box-shadow var(--transition-fast);
}

@media (hover: hover) and (pointer: fine) {
  .template-card:hover { box-shadow: var(--glass-glow, 0 0 20px rgba(52,152,219,0.2)); }
}

.template-card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-left: 3px solid transparent;
}

.template-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.template-logo-img {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.template-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.template-name {
  font-size: clamp(12px, 0.7vw + 9px, 14px);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.template-desc {
  font-size: clamp(10px, 0.5vw + 8px, 12px);
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.template-add-btn { flex-shrink: 0; min-height: 32px; }

.template-buttons-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: var(--spacing-xs) var(--spacing-md) var(--spacing-sm);
}

.template-btn-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  border: 1px solid;
  font-size: clamp(10px, 0.5vw + 8px, 11px);
  white-space: nowrap;
}

.template-btn-more {
  background: transparent !important;
  border-color: var(--color-border) !important;
  color: var(--color-text-secondary);
}

.recent-actions { display: flex; flex-direction: column; gap: var(--spacing-xs); }

.recent-action-item {
  padding: var(--spacing-xs) var(--spacing-sm);
  background: rgba(0,0,0,0.15);
  border-radius: var(--radius-sm);
  font-size: clamp(11px, 0.6vw + 8px, 13px);
  font-family: monospace;
}

/* ==========================================================================
   DL-054 — Settings redesign: sidebar shell + row/panel system.
   Ported from the mockup design system (settings.css) into scoped styles.
   Type scale is em-based off .settings-app's clamp() base so it scales with
   viewport width; control heights ride --min-touch-target so touch modes
   still enforce reachable targets.
   ========================================================================== */

.settings-app {
  /* surfaces */
  --bg: #0a111f;
  --bg-sunken: #070d18;
  --panel: #111c2f;
  --panel-2: #16233a;
  --field: #0d1728;
  --line: #1f2f4a;
  --line-soft: #172540;
  /* ink */
  --text: #e9eff8;
  --text-2: #9fb0c9;
  --text-3: #7286a4;
  /* accents */
  --accent: #4a8cff;
  --accent-2: #2f6fe0;
  --accent-ghost: rgba(74, 140, 255, 0.14);
  --ok: #3ddc97;
  --warn: #f5b547;
  --danger: #ff7a7a;
  /* geometry */
  --r-lg: 14px;
  --r-md: 10px;
  --r-sm: 8px;
  --nav-w: 240px;
  --rail-w: 320px;
  --gutter: 24px;
  --mono: ui-monospace, "Cascadia Mono", "JetBrains Mono", Consolas, monospace;
  /* type scale — em units ride the clamp() base below */
  --fs-xs: 0.79em;
  --fs-sm: 0.88em;
  --fs-md: 0.95em;
  --fs-lg: 1.07em;
  --fs-xl: 1.55em;
  --fs-clock: 3.2em;
  /* touch-aware minimum control height: 36px normal, grows in touch modes */
  --target: max(34px, calc(var(--min-touch-target, 40px) - 8px));
  --shadow: 0 1px 0 rgba(255, 255, 255, 0.03) inset, 0 8px 24px rgba(0, 0, 0, 0.28);

  display: grid;
  grid-template-columns: var(--nav-w) minmax(0, 1fr);
  width: 100%;
  height: 100vh;
  overflow: hidden;
  background: var(--bg);
  color: var(--text);
  font-size: clamp(12.5px, 0.55vw + 8px, 14.5px);
  line-height: 1.45;
  /* touch polish: no double-tap-zoom delay, no grey tap flash */
  -webkit-tap-highlight-color: transparent;
}

.settings-app .btn, .settings-app .select, .nav-item, .nav-sub button,
.nav-result, .switch, .seg label, .pick, .category-header,
.log-file-row, .app-item {
  touch-action: manipulation;
}

.settings-app ::selection { background: var(--accent-ghost); }
.settings-app a { color: var(--accent); text-decoration: none; }
@media (hover: hover) and (pointer: fine) {
  .settings-app a:hover { color: #7fb0ff; }
}

/* --- left rail ------------------------------------------------------------ */

.nav {
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 16px 12px 12px;
  gap: 14px;
  background: var(--bg-sunken);
  border-right: 1px solid var(--line-soft);
}

.nav-brand { display: flex; align-items: center; gap: 10px; padding: 2px 6px 0; }

.nav-mark {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 9px;
  background: linear-gradient(180deg, #1d3a68, #142743);
  border: 1px solid #2a4a7d;
  color: #9dc2ff;
  flex: none;
  overflow: hidden;
}
.nav-mark-img { width: 100%; height: 100%; object-fit: cover; }

.nav-name { font-size: var(--fs-lg); font-weight: 650; letter-spacing: 0.18em; text-transform: uppercase; }

.nav-ver {
  margin-left: auto;
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--accent-ghost);
  color: #9cc0ff;
  font-size: var(--fs-xs);
  font-variant-numeric: tabular-nums;
}

.nav-search { position: relative; display: flex; align-items: center; }
.nav-search-icon {
  position: absolute;
  left: 10px;
  color: var(--text-3);
  pointer-events: none;
}
.nav-search input {
  width: 100%;
  min-height: var(--target);
  padding: 8px 10px 8px 32px;
  border-radius: var(--r-md);
  border: 1px solid var(--line);
  background: var(--field);
  color: var(--text);
  font: inherit;
  font-size: var(--fs-md);
}
.nav-search input::placeholder { color: var(--text-3); }
.nav-search input:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; border-color: transparent; }

/* search results dropdown under the field */
.nav-results {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  z-index: 30;
  max-height: min(46vh, 360px);
  overflow-y: auto;
  padding: 5px;
  border-radius: var(--r-md);
  border: 1px solid var(--line);
  background: var(--panel);
  box-shadow: var(--shadow);
  transform-origin: top;
  animation: popover-in 160ms var(--ease-out, ease);
}
@keyframes popover-in {
  from { opacity: 0; transform: scale(0.97) translateY(-4px); }
}
.nav-result {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px 9px;
  width: 100%;
  padding: 8px 9px;
  border: 0;
  border-radius: var(--r-sm);
  background: transparent;
  color: var(--text-2);
  font: inherit;
  font-size: var(--fs-md);
  text-align: left;
  cursor: pointer;
  transition: background-color 0.12s ease, color 0.12s ease, transform 0.08s ease;
}
@media (hover: hover) and (pointer: fine) {
  .nav-result:hover { background: #0e1a2c; color: var(--text); }
}
.nav-result:active { transform: scale(0.98); }
.nav-result:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.nav-result-icon { flex: none; width: 14px; color: var(--text-3); }
.nav-result-label { flex: 1 1 auto; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.nav-result-crumb { flex-basis: 100%; margin-left: 23px; color: var(--text-3); font-size: var(--fs-xs); }
.nav-results-empty { padding: 10px; color: var(--text-3); font-size: var(--fs-sm); text-align: center; }

.nav-scroll { flex: 1 1 auto; min-height: 0; overflow-y: auto; margin: 0 -4px; padding: 0 4px; }
.nav-group + .nav-group { margin-top: 2px; }

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: var(--target);
  padding: 7px 10px;
  border: 0;
  border-radius: var(--r-md);
  background: transparent;
  color: var(--text-2);
  font: inherit;
  font-size: var(--fs-md);
  text-align: left;
  cursor: pointer;
  transition: background-color 0.12s ease, color 0.12s ease, transform 0.08s ease;
}
@media (hover: hover) and (pointer: fine) {
  .nav-item:hover { background: #0e1a2c; color: var(--text); }
}
.nav-item:active { transform: scale(0.98); }
.nav-item:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.nav-item[aria-current="page"], .nav-item.is-open {
  background: #13263f;
  color: var(--text);
  font-weight: 600;
}
.nav-item svg { flex: none; color: currentColor; opacity: 0.9; }
.nav-item-chevron { margin-left: auto; font-size: var(--fs-xs); transition: transform 0.2s var(--ease-out, ease); }

/* indented sub-items under the open group — replaces the old tab rows */
.nav-sub {
  margin: 2px 0 6px;
  margin-left: 19px;
  padding-left: 19px;
  border-left: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.nav-sub button {
  padding: 6px 10px;
  min-height: calc(var(--target) - 4px);
  border: 0;
  border-radius: var(--r-sm);
  background: transparent;
  color: var(--text-2);
  font: inherit;
  font-size: var(--fs-sm);
  text-align: left;
  cursor: pointer;
  transition: background-color 0.12s ease, color 0.12s ease, transform 0.08s ease;
}
@media (hover: hover) and (pointer: fine) {
  .nav-sub button:hover { background: #0e1a2c; color: var(--text); }
}
.nav-sub button:active { transform: scale(0.98); }
.nav-sub button:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.nav-sub button[aria-current="true"] { background: var(--accent-ghost); color: #b9d3ff; font-weight: 600; }

.nav-foot { display: flex; gap: 8px; padding-top: 10px; border-top: 1px solid var(--line-soft); }
.nav-foot-btn { flex: 1; justify-content: center; }

/* --- main column ---------------------------------------------------------- */

/* .main is the fixed-height column; .content is the scroller. The savebar
   used to be a sticky bottom:0 child INSIDE .main — but a sticky element is
   clamped to its containing block, and a scroll container's box is only the
   scrollport, so the bar scrolled off upward the moment you moved. */
.main { display: flex; flex-direction: column; min-width: 0; min-height: 0; }

.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: flex-end;
  gap: 16px;
  padding: 20px var(--gutter) 14px;
  border-bottom: 1px solid var(--line-soft);
  background: linear-gradient(180deg, #0c1424, var(--bg));
}
.topbar-text { min-width: 0; }
.topbar h1 { margin: 0; font-size: var(--fs-xl); font-weight: 650; letter-spacing: -0.01em; }
.topbar .crumb { margin: 0 0 2px; color: var(--text-3); font-size: var(--fs-xs); letter-spacing: 0.08em; text-transform: uppercase; }
.topbar p { margin: 4px 0 0; color: var(--text-2); max-width: 62ch; font-size: var(--fs-md); }
.topbar-actions { margin-left: auto; display: flex; align-items: center; gap: 8px; flex: none; }

.content {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 20px var(--gutter) 32px;
  display: grid;
  gap: var(--gutter);
  grid-template-columns: minmax(0, 1fr);
  align-content: start;
}
.content.has-rail { grid-template-columns: minmax(0, 1fr) var(--rail-w); align-items: start; }
.content:not(.has-rail) .col { max-width: 1000px; }
.col { display: flex; flex-direction: column; gap: 18px; min-width: 0; }
.rail { position: sticky; top: 0; display: flex; flex-direction: column; gap: 16px; }

/* page enter: panels rise in with a short stagger — page switches mount via
   v-if so the animation replays each navigation */
.col > *, .rail > * {
  animation: page-in 0.26s var(--ease-out, ease) backwards;
}
.col > *:nth-child(2), .rail > *:nth-child(2) { animation-delay: 45ms; }
.col > *:nth-child(3), .rail > *:nth-child(3) { animation-delay: 85ms; }
.col > *:nth-child(4), .rail > *:nth-child(4) { animation-delay: 120ms; }
.col > *:nth-child(n+5), .rail > *:nth-child(n+5) { animation-delay: 150ms; }
@keyframes page-in {
  from { opacity: 0; transform: translateY(10px); }
}

/* ==========================================================================
   Panels & rows
   ========================================================================== */

.panel {
  border: 1px solid var(--line-soft);
  border-radius: var(--r-lg);
  background: var(--panel);
  box-shadow: var(--shadow);
  scroll-margin-top: 16px;
}
.panel-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 10px;
  padding: 13px 18px 11px;
  border-bottom: 1px solid var(--line-soft);
}
.panel-head h2 {
  margin: 0;
  white-space: nowrap;
  font-size: var(--fs-xs);
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-2);
}
.panel-head .hint { color: var(--text-3); font-size: var(--fs-sm); }
.panel-head .spacer { margin-left: auto; }

.panel-body { padding: 4px 18px; }
.panel-body.flush { padding: 0; }
.panel-body.pad { padding: 16px 18px; }

/* one setting = one row: label + description left, control right */
.row {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 12px 0;
  border-bottom: 1px solid var(--line-soft);
}
.row:last-child { border-bottom: 0; }
.row-text { min-width: 0; flex: 1 1 auto; }
.row-text .label { display: block; font-size: var(--fs-md); font-weight: 560; color: var(--text); }
.row-text p { margin: 2px 0 0; color: var(--text-3); font-size: var(--fs-sm); max-width: 64ch; }
.row-control { flex: none; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }

/* stacked variant for wide controls */
.row.stack { display: block; }
.row.stack .row-control { margin-top: 10px; display: block; }
.row-head { display: flex; align-items: center; gap: 10px; }

/* expanded inline detail under a widget row */
.row-inset {
  margin: 0 0 6px;
  padding: 14px;
  border-radius: var(--r-md);
  background: var(--panel-2);
  border: 1px solid var(--line-soft);
}
.widget-detail { display: block; }
.widget-detail .grid-3 { margin-bottom: 12px; }
.widget-detail-foot { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.field-label { font-size: var(--fs-sm); color: var(--text-2); }
.field-note { margin: 4px 0 0; font-size: var(--fs-xs); }
.field-inline { display: flex; align-items: center; gap: 10px; }
.val-inline { color: var(--text); font-variant-numeric: tabular-nums; }

/* ==========================================================================
   Controls — scoped overrides of the global .btn/.select/.input so the
   settings chrome can be denser than the dashboard's touch-first sizing.
   ========================================================================== */

.settings-app .btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: var(--target);
  padding: 0 14px;
  border-radius: var(--r-md);
  border: 1px solid var(--line);
  background: var(--panel-2);
  color: var(--text);
  font: inherit;
  font-size: var(--fs-sm);
  font-weight: 560;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.12s ease, border-color 0.12s ease, transform 0.14s var(--ease-out, ease);
}
.settings-app .btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.settings-app .btn.primary { background: var(--accent-2); border-color: #3c7ef0; color: #fff; }
.settings-app .btn.ghost { background: transparent; border-color: var(--line); color: var(--text-2); }
.settings-app .btn.quiet { background: transparent; border-color: transparent; color: var(--text-2); }
.settings-app .btn.danger { background: transparent; border-color: #5a2c33; color: var(--danger); }
@media (hover: hover) and (pointer: fine) {
  .settings-app .btn:hover:not(:disabled) { background: #1b2b45; border-color: #2a3e60; }
  .settings-app .btn.primary:hover:not(:disabled) { background: #3b7ded; }
  .settings-app .btn.ghost:hover:not(:disabled) { color: var(--text); }
  .settings-app .btn.quiet:hover:not(:disabled) { background: var(--panel-2); color: var(--text); }
  .settings-app .btn.danger:hover:not(:disabled) { background: rgba(255, 122, 122, 0.1); border-color: var(--danger); }
}
.settings-app .btn:active:not(:disabled) { transform: scale(0.97); }
.settings-app .btn.sm { min-height: calc(var(--target) - 6px); padding: 0 10px; font-size: var(--fs-sm); }
.settings-app .btn[disabled] { opacity: 0.45; cursor: not-allowed; }

/* --- switch --------------------------------------------------------------- */

.switch { display: inline-flex; align-items: center; min-height: calc(var(--target) - 6px); cursor: pointer; }
.switch input { position: absolute; opacity: 0; width: 0; height: 0; }
.switch .track {
  position: relative;
  width: 46px;
  height: 26px;
  border-radius: 999px;
  background: #24344f;
  border: 1px solid #2c3f5f;
  transition: background 0.15s ease;
  flex: none;
}
.switch .track::after {
  content: "";
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #cfdcee;
  transition: transform 0.22s cubic-bezier(0.34, 1.3, 0.64, 1), background 0.15s ease;
}
.switch input:checked + .track { background: var(--accent-2); border-color: #4a86e8; }
.switch input:checked + .track::after { transform: translateX(20px); background: #fff; }
.switch input:focus-visible + .track { outline: 2px solid var(--accent); outline-offset: 2px; }
.switch input:disabled + .track { opacity: 0.45; }

/* --- segmented ------------------------------------------------------------ */

.seg {
  display: inline-flex;
  padding: 3px;
  border-radius: var(--r-md);
  border: 1px solid var(--line);
  background: var(--field);
  gap: 2px;
}
.seg label {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: calc(var(--target) - 8px);
  padding: 5px 13px;
  border-radius: 7px;
  color: var(--text-2);
  font-size: var(--fs-sm);
  font-weight: 560;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.15s ease, color 0.15s ease, transform 0.08s ease;
}
.seg input { position: absolute; opacity: 0; width: 0; height: 0; }
@media (hover: hover) and (pointer: fine) {
  .seg label:hover { color: var(--text); }
}
.seg label:active { transform: scale(0.97); }
.seg label:has(input:checked) { background: var(--accent-2); color: #fff; }
.seg label:has(input:focus-visible) { outline: 2px solid var(--accent); outline-offset: 2px; }
.seg .sub { opacity: 0.7; font-weight: 450; font-variant-numeric: tabular-nums; }

/* --- select / text input -------------------------------------------------- */

.settings-app .select, .settings-app .input {
  min-height: var(--target);
  padding: 0 32px 0 12px;
  border-radius: var(--r-md);
  border: 1px solid var(--line);
  background: var(--field);
  color: var(--text);
  font: inherit;
  font-size: var(--fs-sm);
  appearance: none;
  background-image: url("data:image/svg+xml;charset=utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%237286a4' stroke-width='2' stroke-linecap='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  cursor: pointer;
  transition: border-color 0.15s ease, background-color 0.15s ease;
}
@media (hover: hover) and (pointer: fine) {
  .settings-app .select:hover, .settings-app .input:hover { border-color: #2c4368; }
}
.settings-app .input { padding: 8px 12px; background-image: none; cursor: text; font-variant-numeric: tabular-nums; }
.settings-app .textarea { padding: 10px 12px; line-height: 1.5; resize: vertical; min-height: 72px; font-family: var(--mono); font-size: var(--fs-sm); }
.settings-app .select:focus-visible, .settings-app .input:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.settings-app .select.w-220 { width: 220px; }
.settings-app .input.w-110 { width: 110px; }
.settings-app input[type="number"].input { padding-right: 12px; }

/* --- slider --------------------------------------------------------------- */

.slider { display: flex; align-items: center; gap: 12px; width: 100%; }
.slider input[type="range"], .slider-bare {
  flex: 1 1 auto;
  appearance: none;
  -webkit-appearance: none;
  height: 6px;
  min-width: 120px;
  border-radius: 999px;
  background: linear-gradient(to right, var(--accent) var(--fill, 50%), #22334f var(--fill, 50%));
  cursor: pointer;
}
.slider input[type="range"]::-webkit-slider-thumb, .slider-bare::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  border: 3px solid var(--accent);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.5);
  cursor: pointer;
  transition: transform 0.12s var(--ease-out, ease);
}
.slider input[type="range"]:active::-webkit-slider-thumb, .slider-bare:active::-webkit-slider-thumb { transform: scale(1.2); }
.slider input[type="range"]::-moz-range-thumb, .slider-bare::-moz-range-thumb {
  width: 14px; height: 14px; border-radius: 50%;
  background: #fff; border: 3px solid var(--accent);
  transition: transform 0.12s var(--ease-out, ease);
}
.slider input[type="range"]:active::-moz-range-thumb, .slider-bare:active::-moz-range-thumb { transform: scale(1.2); }
.slider input[type="range"]:focus-visible, .slider-bare:focus-visible { outline: 2px solid var(--accent); outline-offset: 6px; }
.slider .val { flex: none; min-width: 52px; text-align: right; color: var(--text); font-size: var(--fs-sm); font-variant-numeric: tabular-nums; }
.slider .cap { flex: none; color: var(--text-3); font-size: var(--fs-xs); }

/* --- chips / meta --------------------------------------------------------- */

.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 9px;
  border-radius: 7px;
  background: var(--panel-2);
  border: 1px solid var(--line-soft);
  color: var(--text-2);
  font-size: var(--fs-xs);
}
.chip b { color: var(--text); font-weight: 600; font-variant-numeric: tabular-nums; }
.chip-ok { border-color: #1f5c41; background: rgba(61, 220, 151, 0.09); color: #8fe8bd; }
.chip-warn { border-color: #5c4a1f; background: rgba(245, 181, 71, 0.09); color: #f2cd8d; }
.row-now { margin-left: 8px; color: #9cc0ff; border-color: #2c4a7d; background: var(--accent-ghost); }
.row-empty { padding: 10px 0; }
.row-status { margin-left: 4px; }

.kv-list { margin: 0; }
.kv {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 9px 0;
  border-bottom: 1px solid var(--line-soft);
  font-size: var(--fs-sm);
}
.kv:last-child { border-bottom: 0; }
.kv dt { color: var(--text-2); }
.kv dd { margin: 0; font-family: var(--mono); font-size: var(--fs-sm); }
.kv-code { font-family: var(--mono); color: var(--text); }
.kv-accent { color: #9cc0ff; }

.note {
  display: flex;
  gap: 9px;
  padding: 11px 12px;
  border-radius: var(--r-md);
  background: var(--panel-2);
  border: 1px solid var(--line-soft);
  color: var(--text-2);
  font-size: var(--fs-sm);
}
.note svg { flex: none; margin-top: 1px; }
.note code { font-family: var(--mono); color: var(--text); font-size: var(--fs-sm); }
.note.warn { border-color: #4a3a18; background: #261e0d; color: #e7cd9a; }
.note.warn svg { color: var(--warn); }
.warn-apply { margin: 2px 4px; }

/* ==========================================================================
   Pickers (fonts, backgrounds, uploads)
   ========================================================================== */

.picker { display: grid; grid-template-columns: repeat(auto-fill, minmax(112px, 1fr)); gap: 10px; }
.picker-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }

.pick {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px 8px 10px;
  border-radius: var(--r-md);
  border: 1px solid var(--line-soft);
  background: var(--field);
  color: var(--text-2);
  font-size: var(--fs-xs);
  cursor: pointer;
  text-align: center;
  transition: border-color 0.15s ease, background-color 0.15s ease, color 0.15s ease, transform 0.08s ease;
}
.pick input { position: absolute; opacity: 0; width: 0; height: 0; }
@media (hover: hover) and (pointer: fine) {
  .pick:hover { border-color: #2c4368; color: var(--text); }
}
.pick:active { transform: scale(0.98); }
.pick:has(input:checked) { border-color: var(--accent); background: var(--accent-ghost); color: #fff; font-weight: 600; }
.pick:has(input:focus-visible) { outline: 2px solid var(--accent); outline-offset: 2px; }
.pick .tick {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--accent);
  display: none;
  place-items: center;
  color: #fff;
  font-size: var(--fs-xs);
}
.pick:has(input:checked) .tick { display: grid; animation: tick-pop 0.22s cubic-bezier(0.34, 1.4, 0.64, 1); }
@keyframes tick-pop {
  from { transform: scale(0.3); opacity: 0; }
}
.pick.specimen { padding: 14px 10px; gap: 4px; }
.pick.specimen .aa { font-size: var(--fs-xl); color: var(--text); line-height: 1.15; }
.pick.specimen .num { font-size: var(--fs-lg); letter-spacing: 0.04em; color: var(--text); }
.picker-row { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.design-row :deep(.design-swatch-grid) { width: 100%; }

/* upload drop zone */
.drop {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: var(--r-md);
  border: 1px dashed #2b4066;
  background: var(--field);
  color: var(--text-2);
  font-size: var(--fs-sm);
}
.drop .btn { margin-left: auto; }
.drop .btn ~ .btn { margin-left: 0; }

.scene-thumb {
  width: 74px;
  height: 44px;
  object-fit: cover;
  border-radius: var(--r-sm);
  border: 1px solid var(--line);
  flex: none;
}

/* ==========================================================================
   Preview rail
   ========================================================================== */

.preview { border: 1px solid var(--line-soft); border-radius: var(--r-lg); background: var(--panel); overflow: hidden; }
.preview-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px 14px;
  border-bottom: 1px solid var(--line-soft);
  font-size: var(--fs-xs);
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-2);
}
.preview-stage {
  display: grid;
  place-items: center;
  padding: 24px;
  min-height: 180px;
  background: radial-gradient(120% 90% at 50% 0%, #17294a 0%, #0c1526 60%, #0a111f 100%);
}
.preview-stage-bg { background-size: cover; background-position: center; position: relative; }
/* scaled-viewport host for real component backgrounds (DL-059) */
.preview-bg-clip { position: absolute; inset: 0; overflow: hidden; border-radius: inherit; z-index: 0; }
.preview-bg-viewport { width: 100vw; height: 100vh; transform-origin: top left; }
.preview-stage-bg .mock-grid { position: relative; z-index: 1; }
.preview-stage-grid { min-height: 150px; }
.preview-stage-bg-tall { min-height: 240px; }
.preview-foot { padding: 11px 14px; border-top: 1px solid var(--line-soft); color: var(--text-3); font-size: var(--fs-xs); }

/* ghost key grid for layout/background previews */
.mock-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; width: 100%; }
.mock-key {
  display: block;
  aspect-ratio: 1;
  border-radius: 12px;
  background: linear-gradient(180deg, #1d3a68, #142743);
  border: 1px solid #2a4a7d;
}
.mock-key.side { aspect-ratio: auto; }
.mock-grid-ghost .mock-key { background: rgba(255, 255, 255, 0.05); border-color: rgba(255, 255, 255, 0.12); }
.preview-stage-grid .mock-grid { grid-template-columns: repeat(4, 1fr); max-width: 240px; }

/* mini dashboard mock (Layout & sidebar preview rail) */
.mock-dash { display: flex; gap: 12px; width: 100%; max-width: 300px; align-items: stretch; }
.mock-dash-side { display: flex; flex-direction: column; gap: 6px; flex: 0 0 auto; }
.mock-dash-side .mock-key { border-radius: 8px; }
.mock-dash-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; flex: 1; align-content: start; }
.mock-dash-grid .mock-key { border-radius: 8px; }

/* screensaver mock */
.ss-mock { display: grid; place-items: center; gap: 6px; text-align: center; color: #dfe9f7; }
.ss-mock-clock { font-size: var(--fs-clock); font-weight: 250; letter-spacing: 0.02em; font-variant-numeric: tabular-nums; line-height: 1; }
.ss-mock-date { font-size: var(--fs-sm); color: rgba(223, 233, 247, 0.7); }
.ss-mock-chips { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; justify-content: center; }
.ss-mock-chips span {
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.09);
  border: 1px solid rgba(255, 255, 255, 0.12);
  font-size: var(--fs-xs);
}
.ss-mock-ticker { margin-top: 10px; font-size: var(--fs-xs); color: rgba(223, 233, 247, 0.55); }

/* ==========================================================================
   QR + server rows
   ========================================================================== */

.connect-steps {
  margin: 0 0 6px;
  padding: 12px 14px 12px 30px;
  display: grid;
  gap: 8px;
  background: var(--panel-2);
  border: 1px solid var(--line-soft);
  border-radius: var(--r-md);
  color: var(--text-2);
  font-size: var(--fs-sm);
}
.connect-steps b { color: var(--text); }

.qr-row { align-items: center; }
.qr-canvas { width: 128px; height: 128px; border-radius: var(--r-md); background: #fff; padding: 6px; flex: none; }
.qr-note { max-width: 22ch; }
.qr-offline { margin-top: 8px; }

/* ==========================================================================
   About
   ========================================================================== */

.col-about { max-width: 880px; }
.about-hero { display: flex; align-items: center; gap: 16px; }
.about-mark { width: 52px; height: 52px; border-radius: 14px; }
.about-title { margin: 0; font-size: var(--fs-xl); font-weight: 650; }
.about-lead { margin: 4px 0 0; color: var(--text-2); font-size: var(--fs-md); max-width: 56ch; }
.about-meta { margin-left: auto; text-align: right; color: var(--text-3); font-size: var(--fs-sm); }
.about-links { display: flex; flex-wrap: wrap; gap: 10px; }
.about-links .btn { text-decoration: none; }

.about-support { display: flex; justify-content: center; padding: 4px 0 8px; }

.kofi-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 14px;
  background: #ff5e5b;
  color: #fff;
  border-radius: var(--radius-full);
  text-decoration: none;
  font-size: var(--fs-xs);
  font-weight: 600;
  min-height: 30px;
  flex-shrink: 0;
  transition: opacity var(--transition-fast), transform var(--transition-fast);
}
.kofi-btn:hover { opacity: 0.9; transform: translateY(-1px); }
.kofi-icon { width: 18px; height: 18px; object-fit: contain; }

.feature-grid-new { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 10px; }
.feature {
  display: flex;
  gap: 10px;
  padding: 11px 12px;
  border-radius: var(--r-md);
  background: var(--panel-2);
  border: 1px solid var(--line-soft);
}
.feature-icon { color: var(--accent); margin-top: 2px; flex: none; }
.feature-title { font-size: var(--fs-sm); font-weight: 600; color: var(--text); }
.feature-desc { font-size: var(--fs-xs); margin-top: 2px; }

/* ==========================================================================
   Misc utilities
   ========================================================================== */

.grid-3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.stack-8 { display: flex; flex-direction: column; gap: 8px; }
.stack-12 { display: flex; flex-direction: column; gap: 12px; }
.muted { color: var(--text-3); }
.sub { color: var(--text-3); font-size: var(--fs-xs); }
.spacer { flex: 1; }
.sr-only {
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0;
}
.chev { transition: transform 0.2s var(--ease-out, ease); }
.chevron-open { transform: rotate(180deg); }

/* Collapse inner wrapper participates as a normal block child */
:deep(.collapse-inner) { min-width: 0; }

/* ==========================================================================
   Save bar — real footer of the main column, always in view
   ========================================================================== */

.savebar {
  position: static;
  flex: none;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px var(--gutter);
  border-top: 1px solid var(--line);
  background: #0c1526;
  box-shadow: 0 -8px 20px rgba(0, 0, 0, 0.35);
}
.savebar .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--warn); flex: none; transition: background-color 0.25s ease; }
.savebar .msg { color: var(--text-2); font-size: var(--fs-sm); }
.savebar .grow { margin-left: auto; display: flex; gap: 8px; }
.savebar[data-state="clean"] .dot { background: var(--ok); }
.savebar[data-state="clean"] .msg { color: var(--text-3); }
.savebar[data-state="dirty"] { animation: savebar-in 0.22s var(--ease-out, ease); }
@keyframes savebar-in {
  from { transform: translateY(100%); }
}

/* ==========================================================================
   Responsive — 1024×600 touch panel and up
   ========================================================================== */

@media (max-width: 1180px) {
  .content.has-rail { grid-template-columns: minmax(0, 1fr); }
  .rail { position: static; }
}

@media (max-width: 1100px) {
  .settings-app { --nav-w: 212px; --gutter: 18px; --rail-w: 300px; }
  .topbar { padding-top: 14px; padding-bottom: 12px; }
  .topbar p { display: none; }
  .content { padding-top: 16px; }
}

/* keep usable height on the 600px-tall panel */
@media (max-height: 700px) {
  .nav { padding-top: 10px; gap: 10px; }
  .nav-brand { padding-top: 0; }
  .topbar { padding-top: 12px; padding-bottom: 10px; }
  .content { padding-top: 14px; padding-bottom: 20px; }
  .panel-head { padding-top: 10px; padding-bottom: 9px; }
  .row { padding-top: 10px; padding-bottom: 10px; }
  .savebar { padding-top: 9px; padding-bottom: 9px; }
}

@media (max-width: 880px) {
  .settings-app { grid-template-columns: 1fr; height: auto; min-height: 100vh; overflow: visible; }
  .main, .content { overflow: visible; }
  .topbar { position: static; }
  .nav {
    border-right: 0;
    border-bottom: 1px solid var(--line-soft);
    max-height: 52vh;
    overflow-y: auto;
    position: sticky;
    top: 0;
    z-index: 30;
    background: var(--bg-1);
  }
  .row { flex-direction: column; align-items: flex-start; gap: 10px; }
  .row-control { width: 100%; justify-content: flex-start; }
  .list-header, .app-item { grid-template-columns: 1fr 60px; }
  .list-header span:nth-child(3), .list-header span:nth-child(4),
  .app-item .app-scene, .app-item .app-actions { display: none; }
  .logs-layout { flex-direction: column; height: auto; }
  .logs-files-card { width: 100%; }
  .log-viewer { height: 46vh; }
  .grid-3 { grid-template-columns: 1fr; }
  .picker-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .about-hero { flex-direction: column; align-items: flex-start; }
  .about-meta { margin-left: 0; text-align: left; }
}

@media (prefers-reduced-motion: reduce) {
  .nav-item, .nav-sub button, .nav-result, .chev, .nav-item-chevron,
  .switch .track, .switch .track::after, .seg label, .pick,
  .category-header, .settings-app .btn,
  .settings-app .select, .settings-app .input,
  .slider input[type="range"], .slider-bare,
  .slider input[type="range"]::-webkit-slider-thumb,
  .slider-bare::-webkit-slider-thumb,
  .slider input[type="range"]::-moz-range-thumb,
  .slider-bare::-moz-range-thumb {
    transition: none;
  }
  .nav-results, .col > *, .rail > *, .savebar[data-state="dirty"],
  .pick:has(input:checked) .tick {
    animation: none;
  }
}

</style>
