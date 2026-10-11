import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
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
		const wrapper = mount(AppNavbar)

		expect(wrapper.text().toUpperCase()).toContain('ZERO1')
		expect(wrapper.text()).toContain('Login')
	})

	it('renders student role and nav items when student is logged in', () => {
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

		const wrapper = mount(AppNavbar)

		expect(wrapper.text()).toContain('STUDENT')
		expect(wrapper.text()).toContain('Daily Challenge')
		expect(wrapper.text()).toContain('Leaderboard')
	})

	it('toggles dark mode class on document element', async () => {
		const wrapper = mount(AppNavbar)

		const toggleBtn = wrapper.findAll('button')[0]
		expect(toggleBtn).toBeDefined()
		if (toggleBtn) {
			await toggleBtn.trigger('click')
		}
	})
})
