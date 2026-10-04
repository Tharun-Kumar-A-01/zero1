import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createVuestic } from 'vuestic-ui'
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

	it('renders brand title zero1', () => {
		const wrapper = mount(AppSidebar, {
			global: {
				plugins: [createVuestic()],
			},
		})

		expect(wrapper.text()).toContain('zero1')
	})

	it('renders admin dashboard, leaderboard, and SYSTEM ADMINISTRATOR badge for admin', () => {
		const auth = useAuthStore()
		auth.user = {
			id: 1,
			name: 'Admin User',
			email: 'admin@dept.edu',
			role: 'admin',
		}
		auth.token = 'dummy-token'

		const wrapper = mount(AppSidebar, {
			global: {
				plugins: [createVuestic()],
			},
		})

		expect(wrapper.text()).toContain('Admin Dashboard')
		expect(wrapper.text()).toContain('Leaderboard')
		expect(wrapper.text()).toContain('Admin User')
		expect(wrapper.text()).toContain('SYSTEM ADMINISTRATOR')
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

		const wrapper = mount(AppSidebar, {
			global: {
				plugins: [createVuestic()],
			},
		})

		expect(wrapper.text()).toContain('Daily Practice')
		expect(wrapper.text()).toContain('Leaderboard')
		expect(wrapper.text()).toContain('5d')
		expect(wrapper.text()).toContain('250XP')
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

		const wrapper = mount(AppSidebar, {
			global: {
				plugins: [createVuestic()],
			},
		})

		const themeButton = wrapper.find('.action-btn')
		expect(themeButton.exists()).toBe(true)

		await themeButton.trigger('click')
		expect(document.documentElement.classList.contains('dark')).toBe(true)
		expect(localStorage.getItem('theme')).toBe('dark')
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

		const wrapper = mount(AppSidebar, {
			global: {
				plugins: [createVuestic()],
			},
		})

		const logoutButton = wrapper.find('.logout-btn')
		expect(logoutButton.exists()).toBe(true)

		await logoutButton.trigger('click')
		expect(auth.isAuthenticated).toBe(false)
		expect(mockPush).toHaveBeenCalledWith('/login')
	})
})
