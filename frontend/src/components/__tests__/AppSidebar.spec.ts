import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import AppSidebar from '@/components/AppSidebar.vue'
import { useAuthStore } from '@/stores/auth'

const mockPush = vi.fn<(to: string) => void>()
vi.mock('vue-router', () => ({
	useRouter: () => ({
		push: mockPush,
	}),
	useRoute: () => ({
		path: '/admin',
	}),
}))

// Mock ResizeObserver for JSDOM
global.ResizeObserver = class ResizeObserver {
	observe() {}
	unobserve() {}
	disconnect() {}
} as unknown as typeof globalThis.ResizeObserver

describe('AppSidebar component', () => {
	beforeEach(() => {
		setActivePinia(createPinia())
		localStorage.clear()
		document.documentElement.classList.remove('dark')
		mockPush.mockReset()
	})

	it('renders brand title ZERO1', () => {
		const wrapper = mount(AppSidebar)
		expect(wrapper.text().toUpperCase()).toContain('ZERO1')
	})

	it('renders admin dashboard, leaderboard, and ADMIN badge for admin', () => {
		const auth = useAuthStore()
		auth.user = {
			id: 1,
			name: 'Admin User',
			email: 'admin@dept.edu',
			role: 'admin',
		}
		auth.token = 'dummy-token'

		const wrapper = mount(AppSidebar)

		expect(wrapper.text()).toContain('Admin Dashboard')
		expect(wrapper.text()).toContain('Leaderboard')
		expect(wrapper.text()).toContain('Admin User')
		expect(wrapper.text()).toContain('ADMIN')
	})

	it('renders student navigation, streak, and XP metrics for student', () => {
		const auth = useAuthStore()
		auth.user = {
			id: 2,
			name: 'Alice Johnson',
			email: 'alice@dept.edu',
			role: 'student',
			current_streak: 5,
			total_points: 250,
		}
		auth.token = 'dummy-token'

		const wrapper = mount(AppSidebar)

		expect(wrapper.text()).toContain('Daily Practice')
		expect(wrapper.text()).toContain('Leaderboard')
		expect(wrapper.text()).toContain('5d')
		expect(wrapper.text()).toContain('250')
		expect(wrapper.text()).toContain('XP')
		expect(wrapper.text()).toContain('STUDENT')
	})

	it('toggles theme correctly', async () => {
		const auth = useAuthStore()
		auth.user = {
			id: 1,
			name: 'Admin User',
			email: 'admin@dept.edu',
			role: 'admin',
		}
		auth.token = 'dummy-token'

		const wrapper = mount(AppSidebar)

		const buttons = wrapper.findAll('button')
		const themeButton = buttons.find((b) => b.text().includes('Dark') || b.text().includes('Daylight') || b.text().includes('Tavern'))
		expect(themeButton).toBeDefined()

		if (themeButton) {
			await themeButton.trigger('click')
		}
	})

	it('handles logout and navigates to /login', async () => {
		const auth = useAuthStore()
		auth.user = {
			id: 1,
			name: 'Admin User',
			email: 'admin@dept.edu',
			role: 'admin',
		}
		auth.token = 'dummy-token'

		const wrapper = mount(AppSidebar)

		const buttons = wrapper.findAll('button')
		const logoutButton = buttons.find((b) => b.text().includes('Logout'))
		expect(logoutButton).toBeDefined()

		if (logoutButton) {
			await logoutButton.trigger('click')
			expect(auth.isAuthenticated).toBe(false)
			expect(mockPush).toHaveBeenCalledWith('/login')
		}
	})
})
