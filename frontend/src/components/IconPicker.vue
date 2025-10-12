<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal icon-picker">
      <div class="modal-header">
        <h2>Pick an Icon</h2>
        <button class="close-btn" @click="emit('close')">
          <FontAwesomeIcon :icon="['fas', 'times']" />
        </button>
      </div>

      <div class="search-bar">
        <FontAwesomeIcon :icon="['fas', 'search']" class="search-icon" />
        <input 
          v-model="searchQuery" 
          type="text" 
          class="input" 
          placeholder="Search icons..." 
          autofocus
        />
      </div>

      <div class="icon-tabs">
        <button 
          class="tab-btn"
          :class="{ active: currentTab === 'solid' }"
          @click="currentTab = 'solid'"
        >
          Solid
        </button>
        <button 
          class="tab-btn"
          :class="{ active: currentTab === 'brands' }"
          @click="currentTab = 'brands'"
        >
          Brands
        </button>
      </div>

      <div class="icon-grid">
        <button
          v-for="icon in filteredIcons"
          :key="icon"
          class="icon-item"
          @click="selectIcon(icon)"
          :title="icon"
        >
          <FontAwesomeIcon :icon="[currentTab === 'solid' ? 'fas' : 'fab', icon]" />
        </button>
      </div>

      <div v-if="filteredIcons.length === 0" class="no-results">
        No icons found
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import Fuse from 'fuse.js'

const emit = defineEmits<{
  select: [icon: string]
  close: []
}>()

const searchQuery = ref('')
const currentTab = ref<'solid' | 'brands'>('solid')

// Common Font Awesome icons
const solidIcons = [
  'home', 'user', 'cog', 'heart', 'star', 'bell', 'envelope', 'search', 'bars', 'times',
  'check', 'arrow-right', 'arrow-left', 'arrow-up', 'arrow-down', 'play', 'pause', 'stop',
  'volume-up', 'volume-down', 'volume-mute', 'music', 'camera', 'video', 'image', 'file',
  'folder', 'folder-open', 'download', 'upload', 'cloud', 'save', 'edit', 'trash', 'plus',
  'minus', 'undo', 'redo', 'cut', 'copy', 'paste', 'print', 'share', 'link', 'lock', 'unlock',
  'eye', 'eye-slash', 'calendar', 'clock', 'map', 'map-marker', 'phone', 'mobile', 'desktop',
  'laptop', 'tablet', 'keyboard', 'mouse', 'gamepad', 'lightbulb', 'bolt', 'fire', 'sun',
  'moon', 'star', 'cloud', 'cloud-sun', 'cloud-rain', 'snowflake', 'wind', 'thermometer',
  'battery-full', 'battery-half', 'battery-empty', 'wifi', 'signal', 'bluetooth', 'usb',
  'plug', 'power-off', 'wrench', 'hammer', 'screwdriver', 'paint-brush', 'pen', 'pencil',
  'book', 'graduation-cap', 'briefcase', 'dollar-sign', 'euro-sign', 'pound-sign', 'yen-sign',
  'shopping-cart', 'credit-card', 'gift', 'trophy', 'medal', 'crown', 'gem', 'rocket', 'plane',
  'car', 'bicycle', 'motorcycle', 'bus', 'train', 'ship', 'anchor', 'tree', 'leaf', 'seedling',
  'apple-alt', 'coffee', 'pizza-slice', 'hamburger', 'utensils', 'wine-glass', 'beer', 'glass-cheers'
]

const brandIcons = [
  'twitter', 'facebook', 'instagram', 'youtube', 'linkedin', 'github', 'discord', 'spotify',
  'twitch', 'steam', 'playstation', 'xbox', 'apple', 'windows', 'android', 'chrome', 'firefox',
  'edge', 'opera', 'safari', 'amazon', 'google', 'microsoft', 'slack', 'trello', 'dropbox',
  'google-drive', 'skype', 'telegram', 'whatsapp', 'reddit', 'pinterest', 'tumblr', 'snapchat',
  'tiktok', 'patreon', 'paypal', 'stripe', 'bitcoin', 'ethereum'
]

const icons = computed(() => currentTab.value === 'solid' ? solidIcons : brandIcons)

const filteredIcons = computed(() => {
  if (!searchQuery.value) return icons.value

  const fuse = new Fuse(icons.value, {
    threshold: 0.4,
    includeScore: true
  })

  const results = fuse.search(searchQuery.value)
  return results.map(r => r.item)
})

function selectIcon(icon: string) {
  const prefix = currentTab.value === 'solid' ? 'fas' : 'fab'
  emit('select', `${prefix} fa-${icon}`)
}
</script>

<style scoped>
.icon-picker {
  width: 700px;
  max-height: 80vh;
}

.search-bar {
  position: relative;
  margin-bottom: var(--spacing-md);
}

.search-icon {
  position: absolute;
  left: var(--spacing-md);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-secondary);
  pointer-events: none;
}

.search-bar .input {
  padding-left: calc(var(--spacing-md) * 2 + 16px);
}

.icon-tabs {
  display: flex;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
  border-bottom: 2px solid var(--color-border);
}

.tab-btn {
  padding: var(--spacing-sm) var(--spacing-lg);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  font-weight: 500;
  transition: all var(--transition-fast);
  margin-bottom: -2px;
}

.tab-btn:hover {
  color: var(--color-text);
}

.tab-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.icon-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
  gap: var(--spacing-sm);
  max-height: 400px;
  overflow-y: auto;
  padding: var(--spacing-sm);
}

.icon-item {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 1.5rem;
  color: var(--color-text);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.icon-item:hover {
  background-color: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
  transform: scale(1.1);
}

.no-results {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--color-text-secondary);
}
</style>

