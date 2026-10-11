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

		expect(wrapper.text()).toContain('Daily Quests')
		expect(wrapper.text()).toContain('Leaderboard')
		expect(wrapper.text()).toContain('5d')
		expect(wrapper.text()).toContain('250')
		expect(wrapper.text()).toContain('XP')
		expect(wrapper.text()).toContain('STUDENT')
	})

	it('does not render streak or XP metrics for admin or mentor', () => {
		const auth = useAuthStore()
		auth.user = {
			id: 1,
			name: 'Admin User',
			email: 'admin@dept.edu',
			role: 'admin',
		}
		auth.token = 'dummy-token'

		const wrapper = mount(AppSidebar)

		expect(wrapper.text()).not.toContain('XP')
		expect(wrapper.find('.streak-badge').exists()).toBe(false)
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
			const modals = wrapper.findAllComponents({ name: 'PixelModal' })
			const logoutModal = modals.find((m) => m.props('title') === 'Confirm Log Out')
			expect(logoutModal).toBeDefined()
			if (logoutModal) {
				logoutModal.vm.$emit('ok')
				expect(auth.isAuthenticated).toBe(false)
				expect(mockPush).toHaveBeenCalledWith('/login')
			}
		}
	})

	it('toggles collapse state when collapse button is clicked', async () => {
		const auth = useAuthStore()
		auth.user = {
			id: 1,
			name: 'Admin User',
			email: 'admin@dept.edu',
			role: 'admin',
		}
		auth.token = 'dummy-token'

		const wrapper = mount(AppSidebar)
		expect(wrapper.classes()).not.toContain('is-collapsed')

		const collapseBtn = wrapper.find('.sidebar-collapse-btn')
		expect(collapseBtn.exists()).toBe(true)

		await collapseBtn.trigger('click')
		expect(wrapper.classes()).toContain('is-collapsed')
		expect(localStorage.getItem('sidebar_collapsed')).toBe('true')

		await collapseBtn.trigger('click')
		expect(wrapper.classes()).not.toContain('is-collapsed')
		expect(localStorage.getItem('sidebar_collapsed')).toBe('false')
	})
})
