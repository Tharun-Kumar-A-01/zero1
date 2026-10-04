import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createVuestic } from 'vuestic-ui'
import AppNavbar from '@/components/AppNavbar.vue'
import { useAuthStore } from '@/stores/auth'

const mockPush = vi.fn<(to: string) => void>()
vi.mock('vue-router', () => ({
	useRouter: () => ({
		push: mockPush,
	}),
}))

describe('AppNavbar component', () => {
	beforeEach(() => {
		setActivePinia(createPinia())
		localStorage.clear()
		document.documentElement.classList.remove('dark')
		mockPush.mockReset()
	})

	it('renders brand title and login button when unauthenticated', () => {
		const wrapper = mount(AppNavbar, {
			global: {
				plugins: [createVuestic()],
			},
		})

		expect(wrapper.text()).toContain('zero1')
		expect(wrapper.text()).toContain('Login')
	})

	it('renders student streak and points metrics when student is logged in', () => {
		const auth = useAuthStore()
		auth.user = {
			id: 1,
			name: 'Alice Johnson',
			email: 'alice@dept.edu',
			role: 'student',
			current_streak: 7,
			total_points: 340,
		}
		auth.token = 'dummy-token'

		const wrapper = mount(AppNavbar, {
			global: {
				plugins: [createVuestic()],
			},
		})

		expect(wrapper.text()).toContain('7d')
		expect(wrapper.text()).toContain('340 pts')
		expect(wrapper.text()).toContain('STUDENT')
		expect(wrapper.text()).toContain('Daily Challenge')
	})

	it('toggles dark mode class on document element', async () => {
		const wrapper = mount(AppNavbar, {
			global: {
				plugins: [createVuestic()],
			},
		})

		const themeButton = wrapper.find('button[aria-label="Toggle theme"]')
		expect(themeButton.exists()).toBe(true)

		await themeButton.trigger('click')
		expect(document.documentElement.classList.contains('dark')).toBe(true)
		expect(localStorage.getItem('theme')).toBe('dark')

		await themeButton.trigger('click')
		expect(document.documentElement.classList.contains('dark')).toBe(false)
		expect(localStorage.getItem('theme')).toBe('light')
	})
})
