import '@fontsource/jetbrains-mono/400.css'
import '@fontsource/jetbrains-mono/400-italic.css'
import '@fontsource/jetbrains-mono/500.css'
import '@fontsource/jetbrains-mono/600.css'
import '@fontsource/jetbrains-mono/700.css'
import './assets/main.css'
import 'vuestic-ui/css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createVuestic } from 'vuestic-ui'

import App from './App.vue'
import router from './router'

import { formatIndianDate } from './utils/date'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(createVuestic({
	config: {
		colors: {
			threshold: 150,
			presets: {
				light: {
					primary: '#154EC1',
					onPrimary: '#FFFFFF',
					secondary: '#666E75',
					onSecondary: '#FFFFFF',
					success: '#3D9209',
					onSuccess: '#FFFFFF',
					info: '#158DE3',
					onInfo: '#FFFFFF',
					danger: '#E42222',
					onDanger: '#FFFFFF',
					warning: '#FFD43A',
					onWarning: '#262824',
					backgroundPrimary: '#FFFFFF',
					backgroundSecondary: '#FFFFFF',
					backgroundElement: '#ECF0F1',
					backgroundBorder: '#DEE5F2',
					textPrimary: '#262824',
					textInverted: '#FFFFFF',
					shadow: 'rgba(0, 0, 0, 0.12)',
					focus: '#49A8FF',
					transparent: 'rgba(0, 0, 0, 0)',
					backgroundLanding: '#f4f9fc',
					backgroundLandingBorder: 'rgba(155, 179, 206, 0.8)',
					backgroundSidebar: '#ECF0F1',
				},
				dark: {
					primary: '#3472F0',
					onPrimary: '#FFFFFF',
					secondary: '#818992',
					onSecondary: '#FFFFFF',
					success: '#66BE33',
					onSuccess: '#FFFFFF',
					warning: '#FFD952',
					onWarning: '#0B121A',
					danger: '#F34030',
					onDanger: '#FFFFFF',
					info: '#3EAAF8',
					onInfo: '#FFFFFF',
					backgroundPrimary: '#050A10',
					backgroundSecondary: '#1F262F',
					backgroundElement: '#131A22',
					backgroundBorder: '#3D4C58',
					textPrimary: '#F1F1F1',
					textInverted: '#0B121A',
					shadow: 'rgba(0, 0, 0, 0.12)',
					focus: '#49A8FF',
				},
			},
			currentPresetName: (typeof window !== 'undefined' && localStorage.getItem('theme') === 'dark') ? 'dark' : 'light',
		},
		components: {
			VaDateInput: {
				formatDate: (d: Date) => formatIndianDate(d),
			},
		},
	},
}))

app.mount('#app')
