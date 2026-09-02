<template>
  <div class="settings-view">
    <header class="settings-header">
      <h1>Settings</h1>
      <div class="settings-search">
        <FontAwesomeIcon :icon="['fas', 'search']" class="settings-search-icon" />
        <input
          v-model="settingsSearch"
          type="text"
          class="settings-search-input"
          placeholder="Find a setting..."
          @keydown.esc="settingsSearch = ''"
        />
        <div v-if="settingsSearch && searchMatches.length > 0" class="settings-search-results">
          <button
            v-for="match in searchMatches"
            :key="match.tabId + (match.subTab || '')"
            class="settings-search-result"
            @click="jumpToSearchResult(match)"
          >
            <FontAwesomeIcon :icon="match.icon" />
            <span>{{ match.label }}</span>
          </button>
        </div>
        <div v-else-if="settingsSearch" class="settings-search-results">
          <div class="settings-search-empty">No matching settings</div>
        </div>
      </div>
      <div class="settings-header-actions">
        <button
          v-if="!isStandaloneSettings"
          class="btn btn-secondary"
          title="Open only the settings panel in your browser so VDock stays on the dashboard"
          @click="openSettingsInBrowserTab"
        >
          <FontAwesomeIcon :icon="['fas', 'up-right-from-square']" /> Open in browser
        </button>
        <button class="btn btn-secondary" @click="handleSettingsBack">
          <FontAwesomeIcon :icon="['fas', isStandaloneSettings ? 'xmark' : 'arrow-left']" />
          {{ isStandaloneSettings ? 'Close' : 'Back' }}
        </button>
      </div>
    </header>

    <div class="settings-layout-content">
      <nav class="settings-nav-rail">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="['nav-rail-item', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          <FontAwesomeIcon :icon="tab.icon" />
          <span>{{ tab.name }}</span>
        </button>
      </nav>

      <div class="settings-content">

        <!-- ── Appearance ── -->
        <div v-if="activeTab === 'appearance'" class="tab-content">
          <div class="sub-tab-bar">
            <button :class="['sub-tab-btn', { active: appearanceSubTab === 'buttons' }]" @click="appearanceSubTab = 'buttons'">
              <FontAwesomeIcon :icon="['fas', 'sliders']" /> Button Behaviour
            </button>
            <button :class="['sub-tab-btn', { active: appearanceSubTab === 'layout' }]" @click="appearanceSubTab = 'layout'">
              <FontAwesomeIcon :icon="['fas', 'table-columns']" /> Layout &amp; Behavior
            </button>
            <button :class="['sub-tab-btn', { active: appearanceSubTab === 'background' }]" @click="appearanceSubTab = 'background'">
              <FontAwesomeIcon :icon="['fas', 'image']" /> Background
            </button>
            <button :class="['sub-tab-btn', { active: appearanceSubTab === 'screensaver' }]" @click="appearanceSubTab = 'screensaver'">
              <FontAwesomeIcon :icon="['fas', 'moon']" /> Screen Saver
            </button>
          </div>

          <div class="appearance-main">
              <div v-if="appearanceSubTab === 'buttons'" class="settings-grid">
                <section class="settings-section card">
                  <h2><FontAwesomeIcon :icon="['fas', 'hand-pointer']" /> Touch Mode</h2>
                  <TouchModeSelector />
                </section>

                <section class="settings-section card">
                  <h2><FontAwesomeIcon :icon="['fas', 'th-large']" /> Button Display</h2>
                  <div class="form-group">
                    <div class="form-group-header">
                      <label>Button Size</label>
                      <button class="btn-reset" @click="settings.buttonSize = 1.0" title="Reset">
                        <FontAwesomeIcon :icon="['fas', 'undo']" /> Reset
                      </button>
                    </div>
                    <input v-model.number="settings.buttonSize" type="range" min="0.5" max="2" step="0.1" class="slider" />
                    <span class="slider-value">{{ settings.buttonSize.toFixed(1) }}x</span>
                    <p class="form-help">Scales button icons and labels. Combines with Touch Mode above.</p>
                  </div>
                  <div class="toggle-row">
                    <label class="toggle-row-label">Show button labels</label>
                    <label class="toggle-switch"><input v-model="settings.showLabels" type="checkbox" /><span class="toggle-slider"></span></label>
                  </div>
                  <div class="toggle-row">
                    <label class="toggle-row-label">Show tooltips</label>
                    <label class="toggle-switch"><input v-model="settings.showTooltips" type="checkbox" /><span class="toggle-slider"></span></label>
                  </div>
                  <div class="toggle-row">
                    <label class="toggle-row-label">Enable animations</label>
                    <label class="toggle-switch"><input v-model="settings.animationsEnabled" type="checkbox" /><span class="toggle-slider"></span></label>
                  </div>
                  <div class="toggle-row">
                    <div>
                      <label class="toggle-row-label">3D tilt effect</label>
                      <p class="form-help">Tilts the button grid as your mouse moves over it</p>
                    </div>
                    <label class="toggle-switch"><input v-model="settings.tiltEffectEnabled" type="checkbox" /><span class="toggle-slider"></span></label>
                  </div>
                </section>

                <section class="settings-section card preview-card">
                  <h2><FontAwesomeIcon :icon="['fas', 'eye']" /> Live Preview</h2>
                  <div class="button-preview-stage" :class="previewBackgroundClass" :style="previewBackgroundStyle">
                    <DeckButton
                      :button="previewButton"
                      :show-labels="settings.showLabels"
                      :show-tooltips="settings.showTooltips"
                      :button-size="settings.buttonSize * settingsStore.touchModeMultiplier"
                      style="width: 110px; height: 110px;"
                    />
                  </div>
                  <p class="form-help">Reflects your button size, labels, tooltips, touch mode, and background.</p>

                  <div class="preview-demo-controls">
                    <p class="preview-demo-label">Choose the animation, icon motion, and visual effect to apply to ALL buttons:</p>
                    <div class="form-group">
                      <label class="small-label">Button animation</label>
                      <select v-model="previewAnimation" class="select">
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
                    </div>
                    <div class="form-group">
                      <label class="small-label">Icon animation</label>
                      <select v-model="previewIconLoop" class="select">
                        <option value="none">None</option>
                        <option value="squash">Squash</option>
                        <option value="bob">Bob</option>
                        <option value="spin">Spin</option>
                        <option value="pulse">Pulse</option>
                        <option value="swing">Swing</option>
                        <option value="flip">Flip</option>
                        <option value="jump">Jump</option>
                      </select>
                    </div>
                    <div class="form-group">
                      <label class="small-label">Visual effect</label>
                      <select v-model="previewEffect" class="select">
                        <option value="none">None</option>
                        <option value="glass">Glass</option>
                        <option value="neumorphism">Neumorphism</option>
                        <option value="gradient">Gradient</option>
                        <option value="glow">Glow</option>
                        <option value="neon">Neon</option>
                        <option value="metallic">Metallic</option>
                        <option value="liquid">Liquid</option>
                        <option value="holographic">Holographic</option>
                        <option value="shadow">Shadow</option>
                        <option value="emissive">Emissive</option>
                        <option value="fire">Fire</option>
                        <option value="plasma">Plasma</option>
                        <option value="particles">Particles</option>
                        <option value="aurora">Aurora</option>
                        <option value="scanline">Scanline</option>
                        <option value="rain">Rain</option>
                      </select>
                    </div>
                  </div>

                  <div class="form-group" style="margin-top: var(--spacing-md)">
                    <button class="btn btn-primary" :disabled="applyingButtonBehaviour" @click="applyButtonBehaviourToAll">
                      <FontAwesomeIcon :icon="['fas', applyingButtonBehaviour ? 'spinner' : 'floppy-disk']" :spin="applyingButtonBehaviour" />
                      {{ applyingButtonBehaviour ? 'Applying...' : 'Save & Apply to All Buttons' }}
                    </button>
                    <p class="form-help" style="color: var(--color-warning, #f0ad4e)">
                      <FontAwesomeIcon :icon="['fas', 'triangle-exclamation']" />
                      This overwrites the animation, icon motion, and visual effect on every button across all scenes and pages — including any per-button customization made in the Button Editor.
                    </p>
                  </div>
                </section>
              </div>

              <div v-if="appearanceSubTab === 'layout'" class="settings-grid">
            <section class="settings-section card">
              <h2><FontAwesomeIcon :icon="['fas', 'table-columns']" /> Sidebar</h2>
              <div class="toggle-row">
                <label class="toggle-row-label">Show docked sidebar</label>
                <label class="toggle-switch"><input v-model="settings.dockedSidebarEnabled" type="checkbox" /><span class="toggle-slider"></span></label>
              </div>
              <div v-if="settings.dockedSidebarEnabled" class="form-group" style="margin-top: var(--spacing-md)">
                <div class="form-group-header">
                  <label>Sidebar Width</label>
                  <span class="slider-value">{{ settings.dockedSidebarWidth }}px</span>
                </div>
                <input v-model.number="settings.dockedSidebarWidth" type="range" min="80" max="360" step="10" class="slider" />
                <p class="form-help">How much horizontal space the docked buttons column takes up.</p>
              </div>
            </section>

            <section class="settings-section card">
              <h2><FontAwesomeIcon :icon="['fas', 'bell']" /> Notifications</h2>
              <div class="toggle-row">
                <div>
                  <label class="toggle-row-label">Toast notifications</label>
                  <p class="form-help">Controls which action results appear as pop-up toasts.</p>
                </div>
                <div class="toast-level-group" role="radiogroup" aria-label="Toast level">
                  <label
                    v-for="opt in toastLevelOptions"
                    :key="opt.value"
                    :class="['toast-level-btn', { active: settings.toastLevel === opt.value }]"
                  >
                    <input
                      type="radio"
                      :value="opt.value"
                      v-model="settings.toastLevel"
                    />
                    {{ opt.label }}
                  </label>
                </div>
              </div>
            </section>
          </div>

          <div v-if="appearanceSubTab === 'background'" class="settings-grid">
            <section class="settings-section card">
              <h2>Animated Effect</h2>
              <div class="form-group">
                <label>Background Effect</label>
                <select v-model="settings.backgroundPreference" class="select" @change="onAnimatedEffectChange">
                  <option value="none">None</option>
                  <option value="particles">Dark Veil (Particles)</option>
                  <option value="waves">Floating Lines (Waves)</option>
                  <option value="lightning">Lightning</option>
                  <option value="light-pillar">Light Pillar</option>
                  <option value="floating-lines-wave">Floating Lines Wave</option>
                  <option value="prismatic-burst">Prismatic Burst</option>
                  <option value="iridescence">Iridescence</option>
                  <option value="silk">Silk</option>
                  <option value="light-rays">Light Rays</option>
                  <option value="aurora">Aurora</option>
                </select>
                <p class="form-help">Animated overlay on your dashboard</p>
              </div>
            </section>

            <section class="settings-section card">
              <h2>Dashboard Background</h2>
              <div class="form-group">
                <label>Background Style</label>
                <select v-model="settings.dashboardBackground" class="select" @change="onDashboardBackgroundChange">
                  <option value="default">Default (Gradient)</option>
                  <optgroup label="Custom Background" v-if="isCustomBackground">
                    <option :value="settings.dashboardBackground">Custom Uploaded Image</option>
                  </optgroup>
                  <optgroup label="Static Gradients">
                    <option value="ocean-breeze">Ocean Breeze</option>
                    <option value="sunset-glow">Sunset Glow</option>
                    <option value="forest-mist">Forest Mist</option>
                    <option value="royal-purple">Royal Purple</option>
                    <option value="golden-hour">Golden Hour</option>
                  </optgroup>
                  <optgroup label="Animated Backgrounds">
                    <option value="floating-particles">Floating Particles</option>
                    <option value="gradient-waves">Gradient Waves</option>
                    <option value="geometric-patterns">Geometric Patterns</option>
                    <option value="aurora-borealis">Aurora Borealis</option>
                    <option value="starfield">Starfield</option>
                    <option value="bubble-float">Floating Bubbles</option>
                    <option value="neon-grid">Neon Grid</option>
                    <option value="floating-paths">Floating Paths</option>
                    <option value="floating-paths-v2">Floating Paths V2</option>
                    <option value="beams-background">Beams Background</option>
                  </optgroup>
                </select>
              </div>
              <div class="form-group">
                <label>Custom Upload</label>
                <div class="upload-section">
                  <input ref="backgroundFileInput" type="file" accept="image/*,.gif" @change="handleBackgroundUpload" style="display:none" />
                  <button class="btn btn-secondary upload-btn" :disabled="uploadingBackground" @click="($refs.backgroundFileInput as HTMLInputElement).click()">
                    <FontAwesomeIcon :icon="uploadingBackground ? ['fas', 'spinner'] : ['fas', 'upload']" :spin="uploadingBackground" />
                    {{ uploadingBackground ? 'Uploading...' : 'Choose Image or GIF' }}
                  </button>
                  <button v-if="isCustomBackground" class="btn btn-danger" @click="removeCustomBackground">
                    <FontAwesomeIcon :icon="['fas', 'trash']" /> Remove
                  </button>
                </div>
                <div v-if="isCustomBackground" class="background-preview">
                  <img :src="settings.dashboardBackground" alt="Custom Background" />
                </div>
              </div>
            </section>

            <section class="settings-section card">
              <h2>Scene Background</h2>
              <p class="form-help" style="margin-bottom:var(--spacing-md)">Override for: <strong>{{ currentScene?.name ?? 'No scene selected' }}</strong></p>
              <div class="upload-section">
                <input ref="sceneBackgroundFileInput" type="file" accept="image/*,.gif" @change="handleSceneBackgroundUpload" style="display:none" />
                <button class="btn btn-secondary upload-btn" :disabled="uploadingSceneBackground || !currentScene" @click="($refs.sceneBackgroundFileInput as HTMLInputElement).click()">
                  <FontAwesomeIcon :icon="uploadingSceneBackground ? ['fas', 'spinner'] : ['fas', 'image']" :spin="uploadingSceneBackground" />
                  {{ uploadingSceneBackground ? 'Uploading...' : 'Set Scene Background' }}
                </button>
                <button v-if="hasSceneBackground" class="btn btn-danger" @click="removeSceneBackground">
                  <FontAwesomeIcon :icon="['fas', 'trash']" /> Remove
                </button>
              </div>
              <div v-if="hasSceneBackground" class="background-preview">
                <img :src="currentScene!.background!.image" alt="Scene Background" />
              </div>
            </section>
              </div>

              <div v-if="appearanceSubTab === 'screensaver'" class="settings-grid">
                <section class="settings-section card" id="setting-screensaver">
                  <h2><FontAwesomeIcon :icon="['fas', 'moon']" /> Screensaver</h2>
                  <div class="form-group">
                    <div class="form-group-header">
                      <label>Screensaver Delay</label>
                      <span class="slider-value">{{ settingsStore.screensaverTimeout === 0 ? 'Off' : formatScreensaverTimeout(settingsStore.screensaverTimeout) }}</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="600"
                      step="30"
                      :value="settingsStore.screensaverTimeout"
                      @input="settingsStore.screensaverTimeout = Number(($event.target as HTMLInputElement).value)"
                      class="slider"
                    />
                    <p class="form-help">Time before screensaver appears. 0 = disabled.</p>
                  </div>
                </section>

                <section class="settings-section card">
                  <h2><FontAwesomeIcon :icon="['fas', 'grip']" /> Screensaver Widgets</h2>
                  <p class="form-help">Choose what shows on the screensaver besides the clock.</p>

                  <div class="widget-toggle-list">
                    <div class="widget-toggle-row">
                      <div class="widget-toggle-preview" v-html="CLOCK_PREVIEW_SVG"></div>
                      <div class="widget-toggle-label">
                        <strong>Clock</strong>
                        <span class="form-help">Always shown</span>
                      </div>
                      <label class="toggle-switch disabled"><input type="checkbox" checked disabled /><span class="toggle-slider"></span></label>
                    </div>

                    <div v-for="w in screensaverWidgetOptions" :key="w.id" class="widget-toggle-row">
                      <div class="widget-toggle-preview" v-html="w.previewSvg"></div>
                      <div class="widget-toggle-label">
                        <strong>{{ w.label }}</strong>
                        <span class="form-help">{{ w.description }}</span>
                      </div>
                      <label class="toggle-switch">
                        <input type="checkbox" :checked="settingsStore.screensaverWidgets.includes(w.id)" @change="toggleScreensaverWidget(w.id)" />
                        <span class="toggle-slider"></span>
                      </label>
                    </div>
                  </div>
                </section>

                <section v-if="settingsStore.screensaverWidgets.includes('news')" class="settings-section card">
                  <h2><FontAwesomeIcon :icon="['fas', 'newspaper']" /> News Headlines</h2>
                  <div class="form-group">
                    <label>GNews.io API Key</label>
                    <input v-model="settingsStore.newsApiKey" type="password" class="input" placeholder="Paste your free API key" />
                    <p class="form-help">Get a free key at gnews.io. Required for the news widget to show real headlines.</p>
                  </div>
                  <button class="btn btn-secondary" :disabled="testingNews" @click="handleTestNews">
                    <FontAwesomeIcon :icon="['fas', testingNews ? 'spinner' : 'plug']" :spin="testingNews" /> Test Connection
                  </button>
                </section>

                <section v-if="settingsStore.screensaverWidgets.includes('market')" class="settings-section card">
                  <h2><FontAwesomeIcon :icon="['fas', 'chart-line']" /> Stocks / Crypto Ticker</h2>
                  <p class="form-help">Crypto prices (Bitcoin, Ethereum) work automatically via CoinGecko — no key needed.</p>
                  <div class="form-group">
                    <label>Stock quotes API key (optional)</label>
                    <input v-model="settingsStore.marketApiKey" type="password" class="input" placeholder="Optional — leave blank for crypto only" />
                  </div>
                  <button class="btn btn-secondary" :disabled="testingMarket" @click="handleTestMarket">
                    <FontAwesomeIcon :icon="['fas', testingMarket ? 'spinner' : 'plug']" :spin="testingMarket" /> Test Connection
                  </button>
                </section>
              </div>
          </div>
        </div>

        <!-- ── Templates ── -->
        <div v-if="activeTab === 'templates'" class="tab-content">
          <div class="tab-page-header">
            <h2>App Templates</h2>
            <p>Add pre-built scenes for popular apps. Each template creates a new scene with ready-to-use buttons.</p>
          </div>
          <section
            v-for="category in templateCategories"
            :key="category.id"
            class="settings-section card template-category"
          >
            <button class="category-header" @click="toggleCategory(category.id)">
              <span class="category-title">
                <FontAwesomeIcon :icon="category.icon" class="category-icon" />
                {{ category.name }}
              </span>
              <FontAwesomeIcon :icon="['fas', expandedCategory === category.id ? 'chevron-up' : 'chevron-down']" class="category-chevron" />
            </button>
            <div v-if="expandedCategory === category.id" class="template-grid">
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
                  <button class="btn btn-primary btn-sm template-add-btn" :disabled="addingTemplate === template.id" @click="addTemplateAsScene(template)">
                    <FontAwesomeIcon :icon="addingTemplate === template.id ? ['fas', 'spinner'] : ['fas', 'plus']" :spin="addingTemplate === template.id" />
                    {{ addingTemplate === template.id ? 'Adding...' : 'Add Scene' }}
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
          </section>
        </div>

        <!-- ── Server ── -->
        <div v-if="activeTab === 'server'" class="tab-content">
          <div class="tab-page-header">
            <h2>Server Configuration</h2>
            <p>Manage startup and connection settings.</p>
          </div>
          <div class="settings-grid">
            <section class="settings-section card">
              <h2>Startup</h2>
              <div class="toggle-row">
                <div>
                  <label class="toggle-row-label">Launch VDock on startup</label>
                  <p class="form-help">Automatically start VDock when you log in to Windows or macOS. Also works on Linux.</p>
                </div>
                <label class="toggle-switch"><input v-model="settings.startOnBoot" type="checkbox" @change="handleStartOnBootToggle" /><span class="toggle-slider"></span></label>
              </div>
              <p v-if="startOnBootStatus" class="status-msg" :class="startOnBootStatus.success ? 'status-success' : 'status-error'">{{ startOnBootStatus.message }}</p>
              <div class="toggle-row">
                <div>
                  <label class="toggle-row-label">Close launcher terminal after startup</label>
                  <p class="form-help">When enabled, the black launcher window closes automatically once VDock starts. Disable to keep it open for logs and debugging. Takes effect on the next launch.</p>
                </div>
                <label class="toggle-switch"><input v-model="settings.autoCloseLauncher" type="checkbox" /><span class="toggle-slider"></span></label>
              </div>
            </section>

            <section class="settings-section card">
              <h2>Navigation</h2>
              <div class="toggle-row">
                <div>
                  <label class="toggle-row-label">Open settings in a new browser tab</label>
                  <p class="form-help">When enabled, the Settings button opens settings in a separate browser tab instead of navigating within VDock</p>
                </div>
                <label class="toggle-switch"><input v-model="settings.openSettingsInNewTab" type="checkbox" /><span class="toggle-slider"></span></label>
              </div>
            </section>

            <section class="settings-section card">
              <h2>Connection</h2>
              <div v-if="serverConfig" class="server-info">
                <div class="info-row"><span class="info-label">Host</span><span class="info-value">{{ serverConfig.host }}</span></div>
                <div class="info-row"><span class="info-label">Port</span><span class="info-value">{{ serverConfig.port }}</span></div>
                <div class="info-row"><span class="info-label">Auth</span><span class="info-value">{{ serverConfig.require_auth ? 'Enabled' : 'Disabled' }}</span></div>
              </div>
              <p class="form-help mt-md">
                Host and port are set via <code>HOST</code>/<code>PORT</code> environment variables in <code>backend/.env</code> and require restarting VDock to change &mdash; they can't be changed live from here.
              </p>
            </section>
          </div>
        </div>

        <!-- ── Integration ── -->
        <div v-if="activeTab === 'integration'" class="tab-content">
          <div class="tab-page-header">
            <h2>App Integration</h2>
            <p>Widget data sources and automatic scene switching for monitored applications.</p>
          </div>
          <div class="settings-grid">
            <section class="settings-section card">
              <h2>Weather Widget Location</h2>
              <div class="form-group">
                <label>Location Source</label>
                <select v-model="settings.weatherLocationMode" class="select">
                  <option value="auto">Use my current location</option>
                  <option value="manual">Set a city manually</option>
                </select>
              </div>
              <div v-if="settings.weatherLocationMode === 'manual'" class="form-group" style="margin-top: var(--spacing-sm)">
                <label>City</label>
                <input v-model="settings.weatherManualCity" type="text" class="input" placeholder="e.g. Tel Aviv" @keyup.enter="refreshWeatherWidget" />
                <p class="form-help">Used to fetch weather for the dashboard widget</p>
              </div>
              <p v-else class="form-help">Requires location permission in your browser. If denied, falls back to the manual city above if set.</p>
            </section>

            <section class="settings-section card">
              <h2>Auto Scene Switching</h2>
              <div class="toggle-row">
                <div>
                  <label class="toggle-row-label">Enable Auto Switching</label>
                  <p class="form-help">Switch scenes when monitored apps become active</p>
                </div>
                <label class="toggle-switch-inline">
                  <input type="checkbox" :checked="autoSwitchingEnabled" @change="toggleAutoSwitching" />
                  <span class="toggle-slider"></span>
                </label>
              </div>
              <div v-if="autoSwitchingEnabled" class="auto-switch-status">
                <FontAwesomeIcon :icon="['fas', 'check-circle']" class="status-icon success" />
                <span>Monitoring active application</span>
              </div>
            </section>

            <section class="settings-section card">
              <h2>Recent Actions</h2>
              <div v-if="settings.recentActions.length > 0" class="recent-actions">
                <div v-for="(actionId, index) in settings.recentActions" :key="index" class="recent-action-item">{{ actionId }}</div>
                <button class="btn btn-secondary" style="margin-top:var(--spacing-sm)" @click="clearRecentActions">Clear Recent Actions</button>
              </div>
              <div v-else class="empty-state">No recent actions</div>
            </section>
          </div>

          <section class="settings-section card" style="margin-top:var(--spacing-lg)">
            <div class="section-header">
              <h2>Running Applications</h2>
              <button class="btn btn-sm btn-primary" @click="refreshRunningApps">
                <FontAwesomeIcon :icon="['fas', 'sync']" :spin="loadingApps" /> Refresh
              </button>
            </div>
            <div v-if="loadingApps" class="loading-state">
              <FontAwesomeIcon :icon="['fas', 'spinner']" spin /><span>Loading applications...</span>
            </div>
            <div v-else-if="runningApps.length === 0" class="empty-state">
              <FontAwesomeIcon :icon="['fas', 'desktop']" /><p>No applications detected</p>
              <button class="btn btn-secondary" @click="refreshRunningApps">Refresh</button>
            </div>
            <div v-else class="app-integration-list">
              <div class="list-header">
                <span>Application</span><span>Status</span><span>Scene</span><span>Actions</span>
              </div>
              <div v-for="app in runningApps" :key="app.exe" class="app-item">
                <div class="app-info">
                  <FontAwesomeIcon :icon="['fas', 'window-maximize']" class="app-icon" />
                  <div class="app-details">
                    <span class="app-name">{{ app.name }}</span>
                    <span class="app-exe">{{ app.exe }}</span>
                  </div>
                </div>
                <div class="app-status">
                  <label class="toggle-switch"><input type="checkbox" :checked="isAppIntegrationEnabled(app.exe)" @change="toggleAppIntegration(app)" /><span class="toggle-slider"></span></label>
                  <span class="status-text">{{ isAppIntegrationEnabled(app.exe) ? 'On' : 'Off' }}</span>
                </div>
                <div class="app-scene">
                  <select v-if="isAppIntegrationEnabled(app.exe)" :value="getAppScene(app.exe)" @change="updateAppScene(app.exe, ($event.target as HTMLSelectElement).value)" class="select-sm">
                    <option value="">Create New Scene</option>
                    <option v-for="scene in availableScenes" :key="scene.id" :value="scene.id">{{ scene.name }}</option>
                  </select>
                  <span v-else class="scene-placeholder">—</span>
                </div>
                <div class="app-actions">
                  <button v-if="isAppIntegrationEnabled(app.exe)" class="btn-icon" @click="openShortcutManager(app)" title="Manage Shortcuts"><FontAwesomeIcon :icon="['fas', 'cog']" /></button>
                  <button v-if="isAppIntegrationEnabled(app.exe) && !getAppScene(app.exe)" class="btn-icon btn-primary" @click="createSceneForApp(app)" title="Create Scene"><FontAwesomeIcon :icon="['fas', 'plus']" /></button>
                </div>
              </div>
            </div>
            <div v-if="appIntegrations.length > 0" class="integration-summary">
              <FontAwesomeIcon :icon="['fas', 'info-circle']" />
              <span>{{ appIntegrations.length }} app{{ appIntegrations.length > 1 ? 's' : '' }} integrated</span>
            </div>
          </section>
        </div>

        <!-- Shortcut Manager Modal -->
        <AppShortcutManager
          v-if="showShortcutManager"
          :app-exe="selectedAppForShortcuts?.exe || ''"
          :scene-id="getAppScene(selectedAppForShortcuts?.exe || '')"
          @close="showShortcutManager = false"
          @add-shortcut="handleAddShortcut"
        />

        <!-- ── About ── -->
        <div v-if="activeTab === 'about'" class="tab-content">
          <section class="settings-section card about-card">
            <div class="about-brand">
              <h2 class="about-title">VDock</h2>
              <p class="about-version">Virtual Stream Interface v2.0.0</p>
              <p class="about-desc">A powerful virtual stream interface for controlling your computer with customizable buttons, macros, system metrics, and intelligent app integration.</p>
            </div>

            <div class="feature-highlights">
              <h4>Key Features</h4>
              <ul>
                <li>✨ Real-time System Metrics Monitoring</li>
                <li>🎬 Advanced Macro Automation</li>
                <li>🔗 Smart App Integration</li>
                <li>🎨 Customizable Buttons &amp; Backgrounds</li>
                <li>🤖 Automatic Scene Switching</li>
                <li>📊 Professional Dashboard Interface</li>
              </ul>
            </div>

            <div class="about-divider"></div>

            <div class="about-row">
              <div>
                <h3>Need help?</h3>
                <p class="form-help">New to VDock? Walk through the quick start guide.</p>
              </div>
              <button class="btn btn-primary" @click="settingsStore.showHelpGuide = true">
                <FontAwesomeIcon :icon="['fas', 'question-circle']" /> Open Help &amp; Guide
              </button>
            </div>

            <div class="about-divider"></div>

            <div class="about-links">
              <a href="https://www.daniel-shalom.com/" target="_blank" rel="noopener" class="about-link-btn"><FontAwesomeIcon :icon="['fas', 'globe']" /> Website</a>
              <a href="https://github.com/ponya5" target="_blank" rel="noopener" class="about-link-btn"><FontAwesomeIcon :icon="['fab', 'github']" /> GitHub</a>
              <a href="https://www.linkedin.com/in/daniel-shalom-13987a1a/" target="_blank" rel="noopener" class="about-link-btn"><FontAwesomeIcon :icon="['fab', 'linkedin']" /> LinkedIn</a>
              <button class="about-link-btn" @click="contactEmail"><FontAwesomeIcon :icon="['fas', 'envelope']" /> Contact</button>
            </div>

            <div class="about-divider"></div>

            <div class="about-row">
              <div>
                <h3>Support the project</h3>
                <p class="form-help">If you enjoy using VDock, consider buying me a coffee. It helps keep the project alive and growing.</p>
              </div>
              <a href="https://ko-fi.com/danielshalom" target="_blank" rel="noopener" class="kofi-btn">
                <img src="https://storage.ko-fi.com/cdn/cup-border.png" alt="Ko-fi" class="kofi-icon" />
                Support me on Ko-fi
              </a>
            </div>

            <p class="about-copyright">Daniel Shalom. All rights reserved 2026 ©</p>
          </section>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import { useProfilesStore } from '@/stores/profiles'
import { LAST_PROFILE_STORAGE_KEY, useDashboardStore } from '@/stores/dashboard'
import { useNotificationsStore } from '@/stores/notifications'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import TouchModeSelector from '@/components/TouchModeSelector.vue'
import DeckButton from '@/components/DeckButton.vue'
import apiClient from '@/api/client'
import { autoSceneSwitcher } from '@/services/autoSceneSwitcher'
import AppShortcutManager from '@/components/AppShortcutManager.vue'
import { hasShortcuts, getTopShortcutsForApp, type AppShortcut } from '@/data/appShortcuts'
import { templateCategories, type AppTemplate } from '@/data/appTemplates'
import type { RunningApp, AppIntegration, Scene, Button } from '@/types'
import { useWeather } from '@/composables/useWeather'
import { openStandaloneSettings, isStandaloneSettingsRoute } from '@/utils/openStandaloneSettings'
import { refreshVdock, requestVdockRefresh } from '@/composables/useVdockRefresh'
import { testNewsConnection } from '@/services/newsService'
import { testMarketConnection } from '@/services/marketService'

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

const toastLevelOptions = [
  { value: 'all', label: 'All' },
  { value: 'errors-only', label: 'Errors only' },
  { value: 'off', label: 'Off' },
] as const

const activeTab = ref('appearance')
const appearanceSubTab = ref<'buttons' | 'layout' | 'background' | 'screensaver'>('buttons')

// Sample button for the live preview card — never persisted, just rendered
// through the real DeckButton component so the preview matches actual
// dashboard rendering exactly. Initialized from the persisted defaults so the
// picker still shows the last-applied style when the tab is reopened.
const previewAnimation = ref(settingsStore.buttonDefaultAnimation)
const previewIconLoop = ref(settingsStore.buttonDefaultIconLoop)
const previewEffect = ref(settingsStore.buttonDefaultEffect)

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
const previewBackgroundClass = computed(() => {
  if (settingsStore.backgroundPreference !== 'none') return ''
  const bg = settingsStore.dashboardBackground
  if (bg === 'default') return ''
  if (bg.startsWith('/api/uploads/') || bg.startsWith('/uploads/') || bg.startsWith('http')) return ''
  return `dashboard-bg-${bg}`
})

// Inline styles always win over the (global, unscoped) dashboard-bg-* classes
// regardless of CSS specificity, so every branch here sets an explicit
// background — including a neutral checkerboard placeholder for the one case
// a settings preview can't render (a full animated background component).
const PREVIEW_CHECKERBOARD = 'repeating-conic-gradient(rgba(255, 255, 255, 0.06) 0% 25%, transparent 0% 50%) 50% / 20px 20px'

const previewBackgroundStyle = computed(() => {
  if (settingsStore.backgroundPreference !== 'none') {
    return { background: PREVIEW_CHECKERBOARD }
  }
  const bg = settingsStore.dashboardBackground
  if (bg.startsWith('/api/uploads/') || bg.startsWith('/uploads/') || bg.startsWith('http')) {
    return {
      backgroundImage: `url(${bg})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat'
    }
  }
  if (bg === 'default') {
    return { background: 'var(--color-background)' }
  }
  return {}
})

const expandedCategory = ref<string | null>(null)
const addingTemplate = ref<string | null>(null)

function toggleCategory(id: string) {
  expandedCategory.value = expandedCategory.value === id ? null : id
}

async function addTemplateAsScene(template: AppTemplate) {
  const profile = dashboardStore.currentProfile
  if (!profile) { notificationsStore.error('No profile', 'Load a profile first.'); return }
  addingTemplate.value = template.id
  try {
    const buttons: Button[] = template.buttons.map((b, index) => ({
      id: `button-${Date.now()}-${index}`,
      label: b.label, icon: b.icon, icon_type: 'fontawesome', action: b.action, shape: 'rounded',
      position: { row: Math.floor(index / 5), col: index % 5 }, size: { rows: 1, cols: 1 },
      style: { backgroundColor: b.style?.backgroundColor ?? template.color, textColor: b.style?.textColor ?? '#ffffff' },
      tooltip: b.tooltip ?? b.label, enabled: true
    }))
    const newScene: Scene = {
      id: `scene-${Date.now()}`, name: template.name, icon: template.icon[1] ?? 'layer-group',
      color: template.color, pages: [{ id: `page-${Date.now()}`, name: 'Page 1', buttons, grid_config: { rows: 4, cols: 5 } }], autoCreated: false
    }
    dashboardStore.addScene(newScene)
    notificationsStore.success('Scene added', `"${template.name}" scene added to your dashboard.`)
  } finally { addingTemplate.value = null }
}

const backgroundFileInput = ref<HTMLInputElement | null>(null)
const uploadingBackground = ref(false)
const sceneBackgroundFileInput = ref<HTMLInputElement | null>(null)
const uploadingSceneBackground = ref(false)
const NAMED_BACKGROUNDS = ['ocean-breeze','sunset-glow','forest-mist','royal-purple','golden-hour','floating-particles','gradient-waves','geometric-patterns','aurora-borealis','starfield','bubble-float','neon-grid','floating-paths','floating-paths-v2','beams-background','default']

const isCustomBackground = computed(() => {
  const bg = settings.value.dashboardBackground
  return bg.startsWith('/api/uploads/') || bg.startsWith('/uploads/') || (bg.startsWith('http') && !NAMED_BACKGROUNDS.includes(bg))
})
const currentScene = computed(() => dashboardStore.currentScene)
const hasSceneBackground = computed(() => !!currentScene.value?.background?.image)

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
      settingsStore.dashboardBackground = url
      notificationsStore.success('Background updated', 'Custom background applied successfully.')
    } else { notificationsStore.error('Upload failed', response.data.error || 'Unknown error') }
  } catch (error: any) { notificationsStore.error('Upload failed', error.message || 'Unknown error') }
  finally { uploadingBackground.value = false; if (target) target.value = '' }
}

const handleSceneBackgroundUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file || !currentScene.value) return
  if (!['image/png','image/jpeg','image/jpg','image/gif'].includes(file.type)) { notificationsStore.error('Invalid file', 'Please upload a PNG, JPG, or GIF image.'); return }
  if (file.size > 10 * 1024 * 1024) { notificationsStore.error('File too large', 'Maximum file size is 10MB.'); return }
  uploadingSceneBackground.value = true
  try {
    const formData = new FormData()
    formData.append('file', file); formData.append('type', 'dashboard_background')
    const response = await apiClient.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    if (response.data.success) {
      const url = response.data.url.startsWith('/api') ? response.data.url : '/api' + response.data.url
      dashboardStore.updateScene(currentScene.value!.id, { background: { type: 'image', image: url } })
      notificationsStore.success('Scene background updated', `Background applied to "${currentScene.value!.name}".`)
    } else { notificationsStore.error('Upload failed', response.data.error || 'Unknown error') }
  } catch (error: any) { notificationsStore.error('Upload failed', error.message || 'Unknown error') }
  finally { uploadingSceneBackground.value = false; if (target) target.value = '' }
}

const removeCustomBackground = () => { settingsStore.dashboardBackground = 'default'; notificationsStore.success('Background removed', 'Reverted to default background.') }

function onAnimatedEffectChange() {
  if (settingsStore.backgroundPreference !== 'none') {
    settingsStore.dashboardBackground = 'default'
  }
  settingsStore.saveSettings()
}

function onDashboardBackgroundChange() {
  if (settingsStore.dashboardBackground !== 'default' && settingsStore.backgroundPreference !== 'none') {
    settingsStore.backgroundPreference = 'none'
  }
  settingsStore.saveSettings()
}

const applyingButtonBehaviour = ref(false)

async function applyButtonBehaviourToAll() {
  applyingButtonBehaviour.value = true
  try {
    settingsStore.buttonDefaultAnimation = previewAnimation.value
    settingsStore.buttonDefaultIconLoop = previewIconLoop.value
    settingsStore.buttonDefaultEffect = previewEffect.value
    settingsStore.saveSettings()

    dashboardStore.applyGlobalButtonStyle({
      animation: previewAnimation.value,
      iconLoop: previewIconLoop.value,
      effect: previewEffect.value
    })

    notificationsStore.success('Button style applied', 'Animation, icon motion, and effect applied to every button on your dashboard.')
  } catch (err: any) {
    notificationsStore.error('Failed to apply', err?.message || 'Could not apply the button style to all buttons.')
  } finally {
    applyingButtonBehaviour.value = false
  }
}

const removeSceneBackground = () => {
  if (!currentScene.value) return
  dashboardStore.updateScene(currentScene.value.id, { background: undefined })
  notificationsStore.success('Scene background removed', `Background cleared for "${currentScene.value.name}".`)
}

// Static mockup SVGs for the screensaver widget picker — never data-bound or
// timer-driven, unlike the real widgets in ScreenSaver.vue, so they're cheap
// to render as a simple "what this looks like" swatch next to each toggle.
const CLOCK_PREVIEW_SVG = `<svg viewBox="0 0 64 40" xmlns="http://www.w3.org/2000/svg"><rect width="64" height="40" rx="8" fill="#1c1c28"/><circle cx="32" cy="20" r="13" fill="none" stroke="#e5e5ea" stroke-width="2"/><line x1="32" y1="20" x2="32" y2="11" stroke="#e5e5ea" stroke-width="2"/><line x1="32" y1="20" x2="38" y2="20" stroke="#e5e5ea" stroke-width="2"/></svg>`
const WEATHER_PREVIEW_SVG = `<svg viewBox="0 0 64 40" xmlns="http://www.w3.org/2000/svg"><rect width="64" height="40" rx="8" fill="#1c1c28"/><circle cx="16" cy="20" r="8" fill="#ff9f0a"/><rect x="30" y="14" width="26" height="5" rx="2" fill="#e5e5ea"/><rect x="30" y="23" width="18" height="4" rx="2" fill="#666"/></svg>`
const NEWS_PREVIEW_SVG = `<svg viewBox="0 0 64 40" xmlns="http://www.w3.org/2000/svg"><rect width="64" height="40" rx="8" fill="#1c1c28"/><rect x="8" y="10" width="48" height="6" rx="2" fill="#e5e5ea"/><rect x="8" y="20" width="34" height="4" rx="2" fill="#777"/><rect x="8" y="27" width="24" height="4" rx="2" fill="#555"/></svg>`
const MARKET_PREVIEW_SVG = `<svg viewBox="0 0 64 40" xmlns="http://www.w3.org/2000/svg"><rect width="64" height="40" rx="8" fill="#1c1c28"/><polyline points="8,28 18,22 26,25 36,14 46,17 56,9" fill="none" stroke="#34c759" stroke-width="2"/><rect x="8" y="31" width="20" height="4" rx="2" fill="#999"/></svg>`
const WORLDCLOCK_PREVIEW_SVG = `<svg viewBox="0 0 64 40" xmlns="http://www.w3.org/2000/svg"><rect width="64" height="40" rx="8" fill="#1c1c28"/><rect x="8" y="8" width="48" height="10" rx="5" fill="#2c2c3a"/><text x="32" y="16" font-size="7" fill="#e5e5ea" text-anchor="middle">10:24</text><rect x="8" y="22" width="48" height="10" rx="5" fill="#2c2c3a"/><text x="32" y="30" font-size="7" fill="#e5e5ea" text-anchor="middle">03:24</text></svg>`

const screensaverWidgetOptions = [
  { id: 'weather', label: 'Weather', description: 'Current temperature and conditions', previewSvg: WEATHER_PREVIEW_SVG },
  { id: 'news', label: 'News', description: 'Latest headline (requires free API key)', previewSvg: NEWS_PREVIEW_SVG },
  { id: 'market', label: 'Stocks / Crypto', description: 'Live crypto prices; stocks optional', previewSvg: MARKET_PREVIEW_SVG },
  { id: 'worldclock', label: 'World Clock', description: 'Time in a few other cities', previewSvg: WORLDCLOCK_PREVIEW_SVG },
]

function toggleScreensaverWidget(id: string) {
  const list = settingsStore.screensaverWidgets
  const idx = list.indexOf(id)
  if (idx === -1) settingsStore.screensaverWidgets = [...list, id]
  else settingsStore.screensaverWidgets = list.filter(w => w !== id)
}

const testingNews = ref(false)
async function handleTestNews() {
  testingNews.value = true
  try {
    await testNewsConnection(settingsStore.newsApiKey.trim())
    notificationsStore.success('News connected', 'Successfully fetched a headline from GNews.io.')
  } catch (err: any) {
    notificationsStore.error('News connection failed', err?.message || 'Could not reach GNews.io with this key.')
  } finally {
    testingNews.value = false
  }
}

const testingMarket = ref(false)
async function handleTestMarket() {
  testingMarket.value = true
  try {
    await testMarketConnection()
    notificationsStore.success('Market data connected', 'Successfully fetched crypto prices from CoinGecko.')
  } catch (err: any) {
    notificationsStore.error('Market connection failed', err?.message || 'Could not reach the price API.')
  } finally {
    testingMarket.value = false
  }
}

const runningApps = ref<RunningApp[]>([])
const loadingApps = ref(false)
const appIntegrations = ref<AppIntegration[]>([])
const autoSwitchingEnabled = ref(false)
const showShortcutManager = ref(false)
const selectedAppForShortcuts = ref<RunningApp | null>(null)
const startOnBootStatus = ref<{success: boolean, message: string} | null>(null)

const availableScenes = computed(() => {
  const profile = profilesStore.currentProfile
  if (!profile) return []
  return (profile.scenes || []).map(scene => ({ id: scene.id, name: scene.name }))
})

const tabs = [
  { id: 'appearance', name: 'Appearance', icon: ['fas', 'palette'] },
  { id: 'templates', name: 'Templates', icon: ['fas', 'layer-group'] },
  { id: 'server', name: 'Server', icon: ['fas', 'server'] },
  { id: 'integration', name: 'Widgets & Integration', icon: ['fas', 'plug'] },
  { id: 'about', name: 'About', icon: ['fas', 'info-circle'] }
]

interface SettingsSearchEntry {
  label: string
  keywords: string
  tabId: string
  subTab?: 'buttons' | 'layout' | 'background' | 'screensaver'
  icon: [string, string]
}

const settingsSearchIndex: SettingsSearchEntry[] = [
  { label: 'Touch Mode', keywords: 'touch mode finger tablet target size', tabId: 'appearance', subTab: 'buttons', icon: ['fas', 'hand-pointer'] },
  { label: 'Button Display', keywords: 'button size labels tooltips', tabId: 'appearance', subTab: 'buttons', icon: ['fas', 'th-large'] },
  { label: 'Button Behaviour', keywords: 'button animation icon loop effect style apply all', tabId: 'appearance', subTab: 'buttons', icon: ['fas', 'sliders'] },
  { label: 'Notifications', keywords: 'notifications toast alerts', tabId: 'appearance', subTab: 'layout', icon: ['fas', 'bell'] },
  { label: 'Sidebar', keywords: 'docked sidebar width', tabId: 'appearance', subTab: 'layout', icon: ['fas', 'columns'] },
  { label: 'Screensaver Delay', keywords: 'screensaver idle timeout sleep', tabId: 'appearance', subTab: 'screensaver', icon: ['fas', 'moon'] },
  { label: 'Screensaver Widgets', keywords: 'screensaver widgets weather news stocks crypto world clock', tabId: 'appearance', subTab: 'screensaver', icon: ['fas', 'grip'] },
  { label: 'Animated Effect', keywords: 'background animation particles waves aurora', tabId: 'appearance', subTab: 'background', icon: ['fas', 'wand-magic-sparkles'] },
  { label: 'Dashboard Background', keywords: 'background image wallpaper', tabId: 'appearance', subTab: 'background', icon: ['fas', 'image'] },
  { label: 'App Templates', keywords: 'templates presets apps buttons', tabId: 'templates', icon: ['fas', 'layer-group'] },
  { label: 'Server Configuration', keywords: 'server host port connection', tabId: 'server', icon: ['fas', 'server'] },
  { label: 'Launch on startup', keywords: 'startup boot autostart launch windows mac login', tabId: 'server', icon: ['fas', 'power-off'] },
  { label: 'Startup', keywords: 'startup boot autostart launcher terminal close debug', tabId: 'server', icon: ['fas', 'power-off'] },
  { label: 'Open Settings in New Tab', keywords: 'settings browser tab window navigation external', tabId: 'server', icon: ['fas', 'up-right-from-square'] },
  { label: 'Weather Widget Location', keywords: 'weather location city temperature geolocation', tabId: 'integration', icon: ['fas', 'cloud-sun'] },
  { label: 'Auto Scene Switching', keywords: 'auto scene switching monitored applications', tabId: 'integration', icon: ['fas', 'shuffle'] },
  { label: 'Running Applications', keywords: 'running apps processes', tabId: 'integration', icon: ['fas', 'desktop'] },
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

function jumpToSearchResult(match: SettingsSearchEntry) {
  activeTab.value = match.tabId
  if (match.subTab) appearanceSubTab.value = match.subTab
  settingsSearch.value = ''
}

function clearRecentActions() { if (confirm('Clear all recent actions?')) settingsStore.clearRecentActions() }

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

function contactEmail() { window.location.href = 'mailto:ponya81@gmail.com?subject=VDock%20Support' }

async function refreshRunningApps() {
  loadingApps.value = true
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
  if (!profile) { alert('No profile loaded.'); return }
  const sceneName = app.name.replace('.exe', '')
  try {
    const topShortcuts = hasShortcuts(app.exe) ? getTopShortcutsForApp(app.exe, 8) : []
    const buttons: Button[] = topShortcuts.map((shortcut, index) => createButtonFromShortcut(shortcut, index))
    const newScene: Scene = {
      id: `scene-${Date.now()}`, name: sceneName, icon: 'window-maximize', color: '#3498db',
      pages: [{ id: `page-${Date.now()}`, name: 'Page 1', buttons, grid_config: { rows: 4, cols: 5 } }],
      triggeredByApp: app.exe, autoCreated: true
    }
    dashboardStore.addScene(newScene)
    updateAppScene(app.exe, newScene.id)
    alert(`Scene "${sceneName}" created with ${buttons.length} shortcut buttons!`)
  } catch { alert('Failed to create scene') }
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
  if (!sceneId) { alert('Please create a scene first'); return }
  const profile = dashboardStore.currentProfile
  if (!profile) return
  const scene = profile.scenes.find(s => s.id === sceneId)
  if (!scene?.pages?.length) { alert('Scene not found'); return }
  const page = scene.pages[0]
  const buttons = page.buttons || []
  let emptySlot = null
  for (let row = 0; row < page.grid_config.rows && !emptySlot; row++) {
    for (let col = 0; col < page.grid_config.cols && !emptySlot; col++) {
      if (!buttons.some(b => b.position.row === row && b.position.col === col)) emptySlot = { row, col }
    }
  }
  if (!emptySlot) { alert('No empty slots available in the scene'); return }
  const newButton = createButtonFromShortcut(shortcut, 0)
  newButton.position = emptySlot
  dashboardStore.addButton(newButton)
  showShortcutManager.value = false
  alert(`Added "${shortcut.name}" to scene!`)
}

function saveAppIntegrations() {
  localStorage.setItem('appIntegrations', JSON.stringify(appIntegrations.value))
  autoSceneSwitcher.updateIntegrations(appIntegrations.value)
}

function loadAppIntegrations() {
  const stored = localStorage.getItem('appIntegrations')
  if (stored) {
    try { appIntegrations.value = JSON.parse(stored); autoSceneSwitcher.updateIntegrations(appIntegrations.value) } catch {}
  }
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
      else alert('Failed to enable auto scene switching')
    } else {
      const success = await autoSceneSwitcher.disable()
      if (success) { autoSwitchingEnabled.value = false; localStorage.setItem('autoSceneSwitching', 'false') }
      else alert('Failed to disable auto scene switching')
    }
  } catch { alert('Error toggling auto scene switching') }
}

function applySettingsRouteQuery() {
  const tabQuery = route.query.tab
  if (typeof tabQuery === 'string' && tabs.some((tab) => tab.id === tabQuery)) {
    activeTab.value = tabQuery
  }

  const subQuery = route.query.sub
  if (
    typeof subQuery === 'string' &&
    (subQuery === 'buttons' || subQuery === 'layout' || subQuery === 'background')
  ) {
    appearanceSubTab.value = subQuery
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
  if (tab === 'integration') {
    void refreshRunningApps()
  }
})

onMounted(async () => {
  applySettingsRouteQuery()
  await ensureProfileLoaded()
  await syncStartOnBootFromSystem()
  settingsStore.loadServerConfig()
  loadAppIntegrations()
  if (activeTab.value === 'integration') await refreshRunningApps()
})
</script>

<style scoped>
/* ── Layout ── */
.settings-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: var(--color-background);
  color: var(--color-text);
}

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--glass-border, var(--color-border));
  background: var(--glass-bg, var(--color-surface));
  backdrop-filter: blur(var(--glass-blur, 14px));
  flex-shrink: 0;
}

.settings-header h1 {
  font-size: clamp(16px, 1.2vw + 12px, 24px);
  font-weight: 600;
  margin: 0;
}

.settings-header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-shrink: 0;
}

.settings-search {
  position: relative;
  flex: 1;
  max-width: 320px;
  margin: 0 var(--spacing-lg);
}

.settings-search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-secondary);
  font-size: 0.8rem;
  pointer-events: none;
}

.settings-search-input {
  width: 100%;
  box-sizing: border-box;
  padding: 8px 12px 8px 34px;
  border-radius: var(--radius-md);
  border: 1px solid var(--glass-border, var(--color-border));
  background: rgba(255, 255, 255, 0.06);
  color: var(--color-text);
  font-size: 0.85rem;
}

.settings-search-input:focus {
  outline: none;
  border-color: var(--color-primary, #3498db);
}

.settings-search-results {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  z-index: 50;
  background: var(--glass-bg, rgba(20, 20, 25, 0.95));
  backdrop-filter: blur(var(--glass-blur, 14px));
  border: 1px solid var(--glass-border, var(--color-border));
  border-radius: var(--radius-md);
  box-shadow: var(--glass-shadow, var(--shadow-md));
  max-height: 320px;
  overflow-y: auto;
  padding: 4px;
}

.settings-search-result {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  width: 100%;
  padding: 8px 10px;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm, 6px);
  color: var(--color-text);
  font-size: 0.8rem;
  text-align: left;
  cursor: pointer;
}

.settings-search-result:hover {
  background: rgba(255, 255, 255, 0.08);
}

.settings-search-empty {
  padding: 10px;
  color: var(--color-text-secondary);
  font-size: 0.8rem;
}

.settings-layout-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ── Nav Rail ── */
.settings-nav-rail {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--spacing-md) var(--spacing-sm);
  background: var(--glass-bg, var(--color-surface));
  backdrop-filter: blur(var(--glass-blur, 14px));
  border-right: 1px solid var(--glass-border, var(--color-border));
  overflow-y: auto;
}

.nav-rail-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 10px var(--spacing-md);
  border-radius: var(--radius-md);
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: clamp(12px, 0.8vw + 9px, 15px);
  font-weight: 500;
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast);
  text-align: left;
  min-height: 44px;
  width: 100%;
}

.nav-rail-item:hover {
  background: var(--color-surface-hover, rgba(255,255,255,0.08));
  color: var(--color-text);
}

.nav-rail-item.active {
  background: rgba(52, 152, 219, 0.18);
  color: var(--color-primary, #3498db);
  border-left: 3px solid var(--color-primary, #3498db);
}

.nav-rail-item svg {
  width: 16px;
  flex-shrink: 0;
}

/* ── Content Area ── */
.settings-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
}

.tab-content {
  animation: fadeIn 150ms ease;
}

/* ── Grid Layout ── */
.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: var(--spacing-lg);
  align-items: start;
}

.appearance-main {
  min-width: 0;
}

.button-preview-stage {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
  border-radius: var(--radius-md);
  min-height: 160px;
  overflow: hidden;
}

.preview-demo-controls {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--glass-border, var(--color-border));
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.preview-demo-label {
  font-size: clamp(10px, 0.6vw + 8px, 12px);
  color: var(--color-text-secondary);
  margin: 0;
}

.preview-demo-controls .small-label {
  display: block;
  font-size: clamp(10px, 0.6vw + 8px, 12px);
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

/* ── Screensaver widget picker ── */
.widget-toggle-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.widget-toggle-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--glass-border, var(--color-border));
}

.widget-toggle-row:last-child {
  border-bottom: none;
}

.widget-toggle-preview {
  flex-shrink: 0;
  width: 64px;
  height: 40px;
  border-radius: var(--radius-sm, 6px);
  overflow: hidden;
}

.widget-toggle-preview svg {
  display: block;
  width: 100%;
  height: 100%;
}

.widget-toggle-label {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.toggle-switch.disabled {
  opacity: 0.5;
  pointer-events: none;
}

/* ── Section Cards ── */
.settings-section.card {
  background: var(--glass-bg, var(--color-surface));
  backdrop-filter: blur(var(--glass-blur, 14px));
  border: 1px solid var(--glass-border, var(--color-border));
  box-shadow: var(--glass-shadow, var(--shadow-md));
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.settings-section h2 {
  font-size: clamp(10px, 0.6vw + 8px, 13px);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-md) 0;
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--glass-border, var(--color-border));
}

/* ── Tab Page Header ── */
.tab-page-header {
  margin-bottom: var(--spacing-lg);
}

.tab-page-header h2 {
  font-size: clamp(16px, 1.2vw + 12px, 22px);
  font-weight: 600;
  margin: 0 0 var(--spacing-xs) 0;
  color: var(--color-text);
  text-transform: none;
  letter-spacing: normal;
  border-bottom: none;
  padding-bottom: 0;
}

.tab-page-header p {
  font-size: clamp(12px, 0.7vw + 9px, 14px);
  color: var(--color-text-secondary);
  margin: 0;
}

/* ── Sub-tab Bar ── */
.sub-tab-bar {
  display: flex;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--glass-border, var(--color-border));
  padding-bottom: 0;
}

.sub-tab-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: clamp(12px, 0.7vw + 9px, 14px);
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color var(--transition-fast), border-color var(--transition-fast);
  min-height: 44px;
}

.sub-tab-btn:hover { color: var(--color-text); }
.sub-tab-btn.active {
  color: var(--color-primary, #3498db);
  border-bottom-color: var(--color-primary, #3498db);
}

/* ── Form Groups ── */
.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  font-size: clamp(12px, 0.7vw + 9px, 14px);
  font-weight: 500;
  margin-bottom: var(--spacing-xs);
  color: var(--color-text);
}

.form-group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-xs);
}

.form-help {
  font-size: clamp(11px, 0.6vw + 8px, 13px);
  color: var(--color-text-secondary);
  margin: var(--spacing-xs) 0 0 0;
}

/* ── Slider ── */
.slider {
  width: 100%;
  height: 6px;
  accent-color: var(--color-primary, #3498db);
  cursor: pointer;
  min-height: 44px;
  display: block;
}

.slider-value {
  font-size: clamp(11px, 0.6vw + 8px, 13px);
  color: var(--color-text-secondary);
  font-variant-numeric: tabular-nums;
}

.btn-reset {
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  font-size: clamp(10px, 0.5vw + 8px, 12px);
  padding: 2px 8px;
  cursor: pointer;
  transition: color var(--transition-fast), border-color var(--transition-fast);
  min-height: 28px;
}

.btn-reset:hover { color: var(--color-text); border-color: var(--color-text-secondary); }

/* ── Toggle Switch ── */
.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  min-height: 44px;
  padding: var(--spacing-xs) 0;
}

.toggle-row + .toggle-row {
  border-top: 1px solid var(--glass-border, var(--color-border));
}

.toggle-row-label {
  font-size: clamp(12px, 0.7vw + 9px, 14px);
  font-weight: 500;
  color: var(--color-text);
  cursor: default;
}

.toggle-switch,
.toggle-switch-inline {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
  cursor: pointer;
}

.toggle-switch input,
.toggle-switch-inline input {
  opacity: 0;
  width: 0;
  height: 0;
  position: absolute;
}

.toggle-slider {
  position: absolute;
  inset: 0;
  background: var(--color-border);
  border-radius: var(--radius-full);
  transition: background var(--transition-fast);
}

.toggle-slider::before {
  content: '';
  position: absolute;
  width: 18px;
  height: 18px;
  left: 3px;
  top: 3px;
  background: white;
  border-radius: 50%;
  transition: transform var(--transition-fast);
  box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}

.toggle-switch input:checked + .toggle-slider,
.toggle-switch-inline input:checked + .toggle-slider {
  background: var(--color-primary, #3498db);
}

.toggle-switch input:checked + .toggle-slider::before,
.toggle-switch-inline input:checked + .toggle-slider::before {
  transform: translateX(20px);
}

/* ── Status Messages ── */
.status-msg {
  font-size: clamp(11px, 0.6vw + 8px, 13px);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  margin-top: var(--spacing-xs);
}

.status-success { background: rgba(39, 174, 96, 0.15); color: #27ae60; }
.status-error   { background: rgba(231, 76, 60, 0.15);  color: #e74c3c; }

/* ── Server Info ── */
.server-info {
  margin-top: var(--spacing-md);
  border: 1px solid var(--glass-border, var(--color-border));
  border-radius: var(--radius-md);
  overflow: hidden;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: clamp(11px, 0.6vw + 8px, 13px);
}

.info-row:not(:last-child) { border-bottom: 1px solid var(--glass-border, var(--color-border)); }
.info-label { color: var(--color-text-secondary); }
.info-value { font-weight: 500; font-variant-numeric: tabular-nums; }

/* ── Instruction / Security boxes ── */
.instruction-box {
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  background: rgba(52, 152, 219, 0.08);
  border: 1px solid rgba(52, 152, 219, 0.25);
  border-radius: var(--radius-md);
  font-size: clamp(11px, 0.6vw + 8px, 13px);
}

.instruction-box h4 {
  margin: 0 0 var(--spacing-sm) 0;
  font-size: clamp(12px, 0.7vw + 9px, 14px);
}

.instruction-box ol {
  margin: 0;
  padding-left: var(--spacing-lg);
}

.instruction-box li { margin-bottom: var(--spacing-xs); }

.instruction-box code {
  background: rgba(0,0,0,0.2);
  padding: 1px 5px;
  border-radius: 3px;
  font-family: monospace;
}

.security-note {
  margin-top: var(--spacing-sm);
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

/* ── Upload ── */
.upload-section {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  align-items: center;
}

.upload-btn { min-height: 44px; }

.background-preview {
  margin-top: var(--spacing-sm);
  border-radius: var(--radius-md);
  overflow: hidden;
  max-height: 120px;
}

.background-preview img {
  width: 100%;
  height: 120px;
  object-fit: cover;
  display: block;
}

/* ── Section Header (with action button) ── */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.section-header h2 { margin: 0; border-bottom: none; padding-bottom: 0; }

/* ── Auto Switch Status ── */
.auto-switch-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: clamp(11px, 0.6vw + 8px, 13px);
  color: var(--color-success, #27ae60);
  margin-top: var(--spacing-sm);
}

.status-icon.success { color: var(--color-success, #27ae60); }

/* ── App Integration List ── */
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

.app-item:hover { background: var(--color-surface-hover, rgba(255,255,255,0.04)); }

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

.btn-icon:hover { background: var(--color-surface-hover); color: var(--color-text); }
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

/* ── Loading / Empty States ── */
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

/* ── Templates ── */
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
}

.category-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.category-icon { color: var(--color-primary, #3498db); }
.category-chevron { color: var(--color-text-secondary); }

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

.template-card:hover { box-shadow: var(--glass-glow, 0 0 20px rgba(52,152,219,0.2)); }

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

/* ── About ── */
.about-card {
  max-width: 720px;
}

.about-brand {
  margin-bottom: var(--spacing-md);
}

.about-title {
  font-size: clamp(20px, 1.6vw + 14px, 28px);
  font-weight: 700;
  margin: 0 0 var(--spacing-xs) 0;
  text-transform: none;
  letter-spacing: normal;
  border-bottom: none;
  padding-bottom: 0;
  color: var(--color-text);
}

.about-version {
  font-size: clamp(12px, 0.7vw + 9px, 14px);
  color: var(--color-primary);
  font-weight: 600;
  margin: 0 0 var(--spacing-sm) 0;
}

.about-desc {
  font-size: clamp(12px, 0.7vw + 9px, 14px);
  color: var(--color-text-secondary);
  margin: 0;
}

.about-divider {
  height: 1px;
  background: var(--glass-border, var(--color-border));
  margin: var(--spacing-md) 0;
}

.about-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.about-row h3 {
  font-size: clamp(13px, 0.8vw + 10px, 16px);
  font-weight: 600;
  margin: 0 0 4px 0;
  color: var(--color-text);
}

.feature-highlights h4 {
  font-size: clamp(12px, 0.7vw + 9px, 14px);
  font-weight: 600;
  margin: 0 0 var(--spacing-xs) 0;
}

.feature-highlights ul {
  margin: 0;
  padding-left: var(--spacing-lg);
  font-size: clamp(12px, 0.7vw + 9px, 14px);
}

.feature-highlights li { margin-bottom: 4px; }

.about-links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  align-items: center;
}

.about-link-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: clamp(12px, 0.7vw + 9px, 14px);
  text-decoration: none;
  cursor: pointer;
  transition: background var(--transition-fast);
  min-height: 36px;
}

.about-link-btn:hover { background: var(--color-surface-hover); }

.about-copyright {
  font-size: clamp(10px, 0.5vw + 8px, 12px);
  color: var(--color-text-secondary);
  width: 100%;
  margin-top: var(--spacing-xs);
}

/* ── Ko-fi ── */
.kofi-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: #ff5e5b;
  color: white;
  border-radius: var(--radius-full);
  text-decoration: none;
  font-size: clamp(13px, 0.8vw + 10px, 16px);
  font-weight: 600;
  margin-top: var(--spacing-md);
  transition: opacity var(--transition-fast), transform var(--transition-fast);
  align-self: flex-start;
  min-height: 44px;
}

.kofi-btn:hover { opacity: 0.9; transform: translateY(-1px); }

.kofi-icon { width: 24px; height: 24px; object-fit: contain; }

/* ── Recent Actions ── */
.recent-actions { display: flex; flex-direction: column; gap: var(--spacing-xs); }

.recent-action-item {
  padding: var(--spacing-xs) var(--spacing-sm);
  background: rgba(0,0,0,0.15);
  border-radius: var(--radius-sm);
  font-size: clamp(11px, 0.6vw + 8px, 13px);
  font-family: monospace;
}

/* ── Responsive ── */
@media (max-width: 900px) {
  .settings-nav-rail {
    width: 48px;
    padding: var(--spacing-sm) 4px;
    align-items: center;
  }

  .nav-rail-item {
    width: 40px;
    height: 40px;
    min-height: 40px;
    padding: 0;
    justify-content: center;
    border-left: none;
    border-radius: var(--radius-md);
    position: relative;
  }

  .nav-rail-item span { display: none; }

  .nav-rail-item.active {
    border-left: none;
    background: rgba(52, 152, 219, 0.25);
  }

  .settings-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .settings-layout-content {
    flex-direction: column;
  }

  .settings-nav-rail {
    width: 100%;
    flex-direction: row;
    height: 52px;
    overflow-x: auto;
    overflow-y: hidden;
    padding: var(--spacing-xs) var(--spacing-sm);
    border-right: none;
    border-bottom: 1px solid var(--glass-border, var(--color-border));
    gap: 4px;
  }

  .nav-rail-item {
    flex-shrink: 0;
    width: 44px;
    height: 44px;
    min-height: 44px;
  }

  .settings-content {
    padding: var(--spacing-md);
  }

  .list-header,
  .app-item {
    grid-template-columns: 1fr 60px;
  }

  .list-header span:nth-child(3),
  .list-header span:nth-child(4),
  .app-item .app-scene,
  .app-item .app-actions {
    display: none;
  }
}
/* ── Toast level segmented control ── */
.toast-level-group {
  display: flex;
  border-radius: var(--radius-full);
  overflow: hidden;
  border: 1px solid var(--glass-border, var(--color-border));
  background: var(--glass-bg, var(--color-surface));
  backdrop-filter: blur(var(--glass-blur, 14px));
  flex-shrink: 0;
}

.toast-level-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.45rem 0.9rem;
  min-height: 36px;
  font-size: clamp(11px, 0.65vw + 9px, 13px);
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background 0.18s ease, color 0.18s ease;
  white-space: nowrap;
  user-select: none;
}

.toast-level-btn input {
  display: none;
}

.toast-level-btn + .toast-level-btn {
  border-left: 1px solid var(--glass-border, var(--color-border));
}

.toast-level-btn.active {
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.45), rgba(52, 152, 219, 0.75));
  color: #fff;
  box-shadow: inset 0 0 8px rgba(255, 255, 255, 0.1);
}

@media (hover: hover) {
  .toast-level-btn:not(.active):hover {
    background: var(--color-surface-hover, rgba(255,255,255,0.08));
    color: var(--color-text);
  }
}
</style>
