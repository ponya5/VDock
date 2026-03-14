<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal user-guide-modal">
      <div class="guide-container">
        <!-- Sidebar Navigation -->
        <aside class="guide-sidebar">
          <div class="sidebar-header">
            <div class="logo">
              <span class="logo-v">V</span>
              <span class="logo-text">Dock</span>
            </div>
            <p class="subtitle">User Guide</p>
          </div>
          
          <nav class="sidebar-nav">
            <button 
              v-for="tab in tabs" 
              :key="tab.id"
              :class="['nav-item', { active: activeTab === tab.id }]"
              @click="activeTab = tab.id"
            >
              <FontAwesomeIcon :icon="tab.icon" class="nav-icon" />
              <span>{{ tab.label }}</span>
            </button>
          </nav>

          <div class="sidebar-footer">
            <button class="btn btn-secondary btn-sm close-btn" @click="$emit('close')">
              <FontAwesomeIcon :icon="['fas', 'times']" /> Close Guide
            </button>
          </div>
        </aside>

        <!-- Main Content Area -->
        <main class="guide-main">
          <button class="mobile-close-btn" @click="$emit('close')">
            <FontAwesomeIcon :icon="['fas', 'times']" />
          </button>

          <header class="main-header">
            <h1>{{ activeTabLabel }}</h1>
          </header>

          <div class="main-content">
            <!-- How to Use Tab -->
            <div v-if="activeTab === 'usage'" class="tab-content">
              <section class="guide-section">
                <h2><FontAwesomeIcon :icon="['fas', 'rocket']" /> Getting Started</h2>
                <div class="step-guide">
                  <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-text">
                      <strong>Toggle Edit Mode:</strong> Click the "Edit Mode" button in the bottom bar (or press <code>Ctrl+E</code>) to start customizing your layout.
                    </div>
                  </div>
                  <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-text">
                      <strong>Add Your First Button:</strong> Click any empty cell in the grid. The "Actions" panel will appear on the right.
                    </div>
                  </div>
                  <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-text">
                      <strong>Pick an Action:</strong> Choose from presets like "Launch App", "Hotkey", or "System Stats". Customize the labels and icons.
                    </div>
                  </div>
                  <div class="step">
                    <div class="step-number">4</div>
                    <div class="step-text">
                      <strong>Save Your Profile:</strong> Changes are saved locally. Click "Save Profile" in the footer to ensure everything is stored on the server.
                    </div>
                  </div>
                </div>
              </section>

              <section class="guide-section">
                <h2><FontAwesomeIcon :icon="['fas', 'hand-pointer']" /> Interaction Tips</h2>
                <ul>
                  <li><strong>Drag & Drop:</strong> In Edit Mode, you can drag buttons to different cells or click and drag corners to resize them.</li>
                  <li><strong>Right Click:</strong> Right-click any button in Edit Mode for quick actions like Copy, Paste, or Delete.</li>
                  <li><strong>Quick Search:</strong> Press <code>Ctrl+F</code> anywhere to search for existing buttons or potential actions across all scenes.</li>
                </ul>
              </section>

              <section class="guide-section card accent-card">
                <h3><FontAwesomeIcon :icon="['fas', 'keyboard']" /> Keyboard Shortcuts</h3>
                <div class="shortcut-list">
                  <div class="shortcut-item"><span>Show/Hide VDock</span> <kbd>Ctrl+Shift+D</kbd></div>
                  <div class="shortcut-item"><span>Toggle Edit Mode</span> <kbd>Ctrl+E</kbd></div>
                  <div class="shortcut-item"><span>Next Page</span> <kbd>Ctrl+Right</kbd></div>
                  <div class="shortcut-item"><span>Previous Page</span> <kbd>Ctrl+Left</kbd></div>
                  <div class="shortcut-item"><span>Quick Search</span> <kbd>Ctrl+F</kbd></div>
                </div>
              </section>
            </div>

            <!-- Configuration Tab -->
            <div v-if="activeTab === 'config'" class="tab-content">
              <section class="guide-section">
                <h2><FontAwesomeIcon :icon="['fas', 'palette']" /> Appearance</h2>
                <p>Personalize your dashboard in the <strong>Settings</strong> menu:</p>
                <ul>
                  <li><strong>Global Backgrounds:</strong> Choose from 20+ animated effects or upload your own custom image.</li>
                  <li><strong>Button Styling:</strong> Set global button sizes, rounded corners (using Button Shapes), and enable/disable tooltips.</li>
                  <li><strong>Brightness & UI Scale:</strong> Use the UI Brightness slider to match your room lighting, and UI Scale for high-DPI displays.</li>
                </ul>
              </section>

              <section class="guide-section">
                <h2><FontAwesomeIcon :icon="['fas', 'server']" /> Server & System</h2>
                <ul>
                  <li><strong>Auto-start:</strong> Enable "Launch on Startup" to have VDock ready the moment you log in to Windows.</li>
                  <li><strong>Server Port:</strong> Default is 5000. If you have port conflicts, you can change this in the backend <code>config.json</code>.</li>
                  <li><strong>Remote Access:</strong> Point any device on your local network to your PC's IP address (e.g. <code>192.168.1.10:3000</code>) to use your phone or tablet as a controller.</li>
                </ul>
              </section>

              <section class="guide-section">
                <h2><FontAwesomeIcon :icon="['fas', 'shield-alt']" /> Security</h2>
                <p>Protect your dashboard with a PIN or password in <strong>Settings → Security</strong>. This is highly recommended when using the Remote Access (LAN) feature.</p>
              </section>
            </div>

            <!-- Features & Actions Tab -->
            <div v-if="activeTab === 'features'" class="tab-content">
              <section class="guide-section">
                <h2><FontAwesomeIcon :icon="['fas', 'bolt']" /> Action Types</h2>
                <div class="action-grid">
                  <div class="action-card">
                    <h4>Hotkey</h4>
                    <p>Simulate any key combo (Ctrl+C, Ctrl+V, Win+D, etc.)</p>
                  </div>
                  <div class="action-card">
                    <h4>Launch App</h4>
                    <p>Open any executable or script file directly.</p>
                  </div>
                  <div class="action-card">
                    <h4>URL/Web</h4>
                    <p>Quick access to your favorite websites.</p>
                  </div>
                  <div class="action-card">
                    <h4>Macro</h4>
                    <p>Chain actions together with custom delays.</p>
                  </div>
                  <div class="action-card">
                    <h4>System Stats</h4>
                    <p>Live monitors for CPU, RAM, GPU, and Network.</p>
                  </div>
                  <div class="action-card">
                    <h4>Widgets</h4>
                    <p>World Clocks, Timers, and Weather updates.</p>
                  </div>
                </div>
              </section>

              <section class="guide-section">
                <h2><FontAwesomeIcon :icon="['fas', 'layer-group']" /> Scenes & Profiles</h2>
                <p>Organize your controls into different contexts:</p>
                <ul>
                  <li><strong>Profiles:</strong> Complete sets of scenes. You might have a "Home" profile and a "Work" profile.</li>
                  <li><strong>Scenes:</strong> Collections of pages. Switching scenes changes the entire available grid (e.g. "Gaming Scene" vs "Coding Scene").</li>
                  <li><strong>Docked Sidebar:</strong> Persistent buttons that stay visible no matter which scene or page you are on. Perfect for Volume or Mute controls.</li>
                </ul>
              </section>

              <section class="guide-section">
                <h2><FontAwesomeIcon :icon="['fas', 'cubes']" /> Templates</h2>
                <p>Don't want to start from scratch? Use the <strong>Template Gallery</strong> to import pre-configured decks for OBS, Discord, Windows Productivity, and more.</p>
              </section>
            </div>
          </div>

          <footer class="main-footer">
            <p>Still have questions? Check the full <code>docs/</code> folder in the source code or reach out at <a href="mailto:ponya81@gmail.com">ponya81@gmail.com</a>.</p>
          </footer>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

const emit = defineEmits(['close'])

const activeTab = ref('usage')

const tabs = [
  { id: 'usage', label: 'How to Use', icon: ['fas', 'rocket'] },
  { id: 'config', label: 'Configuration', icon: ['fas', 'cog'] },
  { id: 'features', label: 'Features & Actions', icon: ['fas', 'star'] }
]

const activeTabLabel = computed(() => {
  return tabs.find(t => t.id === activeTab.value)?.label || 'User Guide'
})
</script>

<style scoped>
.user-guide-modal {
  width: 950px;
  height: 85vh;
  max-width: 95vw;
  padding: 0;
  overflow: hidden;
  background: var(--color-background);
  border-radius: var(--radius-lg);
  display: flex;
}

.guide-container {
  display: flex;
  width: 100%;
  height: 100%;
}

/* Sidebar */
.guide-sidebar {
  width: 250px;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  padding: var(--spacing-lg);
}

.sidebar-header {
  margin-bottom: var(--spacing-xl);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-bottom: 4px;
}

.logo-v {
  background: var(--color-primary);
  color: white;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  font-weight: 900;
  font-size: 1.2rem;
}

.logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.5px;
}

.subtitle {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  text-align: left;
  transition: all var(--transition-fast);
  font-weight: 500;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-text);
}

.nav-item.active {
  background: var(--color-primary);
  color: white;
  box-shadow: 0 4px 12px rgba(var(--color-primary-rgb), 0.3);
}

.nav-icon {
  width: 18px;
}

/* Main Content */
.guide-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  background-image: 
    radial-gradient(circle at top right, rgba(var(--color-primary-rgb), 0.1), transparent 400px),
    radial-gradient(circle at bottom left, rgba(var(--color-primary-rgb), 0.05), transparent 300px);
}

.main-header {
  padding: var(--spacing-xl) var(--spacing-xl) 0;
}

.main-header h1 {
  font-size: 2rem;
  font-weight: 800;
  margin: 0;
  color: var(--color-text);
}

.main-content {
  flex: 1;
  padding: var(--spacing-xl);
  overflow-y: auto;
  scrollbar-width: thin;
}

.guide-section {
  margin-bottom: var(--spacing-xl);
}

.guide-section h2 {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: var(--spacing-lg);
  color: var(--color-text);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.guide-section p, .guide-section li {
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.guide-section ul {
  padding-left: var(--spacing-xl);
  list-style-type: disc;
}

.guide-section li {
  margin-bottom: var(--spacing-sm);
}

/* Components inside content */
.step-guide {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.step {
  display: flex;
  gap: var(--spacing-md);
  align-items: flex-start;
  padding: var(--spacing-md);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.step-number {
  background: var(--color-primary);
  color: white;
  min-width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: bold;
}

.step-text {
  font-size: 0.95rem;
}

.accent-card {
  background: linear-gradient(135deg, var(--color-surface) 0%, rgba(var(--color-primary-rgb), 0.05) 100%);
  border-left: 4px solid var(--color-primary);
  padding: var(--spacing-lg);
}

.shortcut-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
}

.shortcut-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

kbd {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 2px 6px;
  font-family: monospace;
  font-size: 0.8rem;
  color: var(--color-primary);
  box-shadow: 0 2px 0 var(--color-border);
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--spacing-md);
}

.action-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  transition: transform var(--transition-fast);
}

.action-card:hover {
  transform: translateY(-4px);
  border-color: var(--color-primary);
}

.action-card h4 {
  margin: 0 0 var(--spacing-xs) 0;
  color: var(--color-text);
  font-size: 1rem;
}

.action-card p {
  font-size: 0.8rem;
  margin: 0;
}

.main-footer {
  padding: var(--spacing-lg) var(--spacing-xl);
  border-top: 1px solid var(--color-border);
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  background: var(--color-surface);
}

.main-footer a {
  color: var(--color-primary);
  text-decoration: none;
}

.main-footer a:hover {
  text-decoration: underline;
}

.mobile-close-btn {
  display: none;
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  color: var(--color-text);
  font-size: 1.5rem;
}

@media (max-width: 768px) {
  .guide-sidebar {
    display: none;
  }
  .mobile-close-btn {
    display: block;
  }
}
</style>
