import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { fas } from '@fortawesome/free-solid-svg-icons'
import { fab } from '@fortawesome/free-brands-svg-icons'

import App from './App.vue'
import router from './router'
import { installSessionLog } from './services/sessionLog'
import './assets/styles/main.css'

// Add all icons to the library
library.add(fas, fab)

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.component('FontAwesomeIcon', FontAwesomeIcon)

// DL-027: the PWA service worker precaches index.html, so a deployed update
// only takes effect on the SECOND reload. Reload once when a new SW claims
// the page so the fresh bundle is served in the same session.
if ('serviceWorker' in navigator) {
  let swReloading = false
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (swReloading) return
    swReloading = true
    window.location.reload()
  })

  // A deck tab stays open for days and a restored phone tab may never fire
  // `load` again — registration.update() is what actually discovers a new
  // sw.js, so poll hourly and on every return to foreground. Paired with the
  // controllerchange reload above, a deploy self-applies without a manual
  // refresh.
  const checkForSwUpdate = () => {
    navigator.serviceWorker.getRegistration().then(r => r?.update()).catch(() => {})
  }
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') checkForSwUpdate()
  })
  setInterval(checkForSwUpdate, 60 * 60 * 1000)
}

installSessionLog(app)

app.mount('#app')

