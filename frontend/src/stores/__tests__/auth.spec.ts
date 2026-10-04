import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import type { UserProfile } from '@/types'

describe('auth store (pinia)', () => {
	beforeEach(() => {
		setActivePinia(createPinia())
		localStorage.clear()
		vi.restoreAllMocks()
	})

	it('initializes with unauthenticated state', () => {
		const auth = useAuthStore()
		expect(auth.isAuthenticated).toBe(false)
		expect(auth.userRole).toBeNull()
		expect(auth.user).toBeNull()
	})

	it('successfully logs in, persists tokens, and updates state', async () => {
		const mockProfile: UserProfile = {
			id: 10,
			name: 'Test Student',
			email: 'student@dept.edu',
			role: 'student',
			roll_number: '2024CS01',
			year_batch: '2024',
			current_streak: 5,
			total_points: 150,
		}

		vi.spyOn(api, 'post').mockResolvedValue({
			success: true,
			data: {
				access_token: 'mock-access-token',
				refresh_token: 'mock-refresh-token',
				user: mockProfile,
			},
		})

		const auth = useAuthStore()
		const ok = await auth.login('student@dept.edu', 'secret123')

		expect(ok).toBe(true)
		expect(auth.isAuthenticated).toBe(true)
		expect(auth.userRole).toBe('student')
		expect(auth.user?.name).toBe('Test Student')
		expect(localStorage.getItem('access_token')).toBe('mock-access-token')
		expect(localStorage.getItem('refresh_token')).toBe('mock-refresh-token')
	})

	it('clears state on logout', () => {
		localStorage.setItem('access_token', 'token-to-remove')
		localStorage.setItem('refresh_token', 'refresh-to-remove')

		const auth = useAuthStore()
		auth.logout()

		expect(auth.isAuthenticated).toBe(false)
		expect(auth.user).toBeNull()
		expect(localStorage.getItem('access_token')).toBeNull()
		expect(localStorage.getItem('refresh_token')).toBeNull()
	})
})
