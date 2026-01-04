import { createApp } from 'vue'
import { VueQueryPlugin } from '@tanstack/vue-query'
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import { useAuth } from './composables/useAuth'

const app = createApp(App)

app.use(router)
app.use(vuetify)
app.use(VueQueryPlugin)

const { initAuth } = useAuth()
initAuth()

const savedTheme = localStorage.getItem('theme')
if (savedTheme) {
  vuetify.theme.global.name.value = savedTheme
}

app.mount('#app')

