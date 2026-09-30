<template>
  <footer class="site-footer">
    <div class="dock-credit">
      <span class="dock-credit-text">Created by Daniel S. · v{{ appVersion }}</span>
      <div class="dock-credit-links">
        <a href="https://www.linkedin.com/in/daniel-shalom-13987a1a/" target="_blank" rel="noopener" class="dock-credit-link" title="Daniel Shalom on LinkedIn" aria-label="LinkedIn">
          <FontAwesomeIcon :icon="['fab', 'linkedin']" />
        </a>
        <a href="https://github.com/ponya5/ponya5" target="_blank" rel="noopener" class="dock-credit-link" title="Daniel Shalom on GitHub" aria-label="GitHub">
          <FontAwesomeIcon :icon="['fab', 'github']" />
        </a>
        <a href="https://www.daniel-shalom.com/" target="_blank" rel="noopener" class="dock-credit-link dock-credit-site" title="daniel-shalom.com" aria-label="Daniel Shalom's website">
          <img :src="'/assets/branding/daniel-shalom-logo.jpg'" alt="" class="dock-credit-logo" />
        </a>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
// Shared site footer — the same credit bar Settings ships, reusable by the
// standalone guide page (DL-132).
import { version as appVersion } from '../../package.json'
</script>

<style scoped>
.site-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 7px var(--gutter);
  border-top: 1px solid var(--line-soft);
  background: var(--bg-sunken);
}
.dock-credit { display: flex; align-items: center; gap: 10px; }
.dock-credit-text { font-size: var(--fs-xs); color: var(--text-3); white-space: nowrap; }
.dock-credit-links { display: flex; align-items: center; gap: 4px; }
.dock-credit-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  font-size: clamp(15px, 1.6vw, 19px);
  border-radius: var(--radius-sm);
  color: var(--text-3);
  transition: color var(--transition-fast), background-color var(--transition-fast);
}
.dock-credit-link:hover { color: var(--text); background: rgba(255, 255, 255, 0.07); }
.dock-credit-logo { width: 22px; height: 22px; border-radius: 50%; object-fit: cover; display: block; }
</style>
