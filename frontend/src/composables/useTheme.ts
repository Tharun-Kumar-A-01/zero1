import { ref, computed } from 'vue'

export type ThemeMode = 'dark' | 'light'

const THEME_STORAGE_KEY = 'zero1_theme'

// Default to dark theme to preserve existing experience
const currentTheme = ref<ThemeMode>('dark')

function applyTheme(theme: ThemeMode): void {
	if (typeof document === 'undefined') return

	const root = document.documentElement
	if (theme === 'light') {
		root.classList.remove('dark')
		root.classList.add('light')
		root.style.colorScheme = 'light'
	} else {
		root.classList.remove('light')
		root.classList.add('dark')
		root.style.colorScheme = 'dark'
	}
}

export function initTheme(): void {
	if (typeof window === 'undefined') return

	const saved = localStorage.getItem(THEME_STORAGE_KEY)
	if (saved === 'light' || saved === 'dark') {
		currentTheme.value = saved
	} else {
		currentTheme.value = 'dark'
	}
	applyTheme(currentTheme.value)
}

export function useTheme() {
	const isDark = computed<boolean>(() => currentTheme.value === 'dark')
	const isLight = computed<boolean>(() => currentTheme.value === 'light')

	function setTheme(theme: ThemeMode): void {
		currentTheme.value = theme
		if (typeof window !== 'undefined') {
			localStorage.setItem(THEME_STORAGE_KEY, theme)
		}
		applyTheme(theme)
	}

	function toggleTheme(): void {
		const next: ThemeMode = currentTheme.value === 'dark' ? 'light' : 'dark'
		setTheme(next)
	}

	return {
		theme: currentTheme,
		isDark,
		isLight,
		setTheme,
		toggleTheme,
		initTheme,
	}
}
