import '@fontsource/jetbrains-mono/400.css'
import '@fontsource/jetbrains-mono/400-italic.css'
import '@fontsource/jetbrains-mono/500.css'
import '@fontsource/jetbrains-mono/600.css'
import '@fontsource/jetbrains-mono/700.css'
import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import * as PixelComponents from '@/components/pixel'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// Globally register all Pixel components
for (const [name, component] of Object.entries(PixelComponents)) {
	if (name.startsWith('Pixel')) {
		app.component(name, component)
	}
}

app.mount('#app')
