import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export interface UserProfile {
	id: number
	name: string
	email: string
	role: 'admin' | 'mentor' | 'student'
	roll_number?: string | null
	year_batch?: string | null
	department?: string | null
	section?: string | null
	current_streak?: number
	longest_streak?: number
	total_points?: number
}

export const useAuthStore = defineStore('auth', () => {
	const user = ref<UserProfile | null>(null)
	const token = ref<string | null>(localStorage.getItem('access_token'))

	const isAuthenticated = computed(() => !!token.value)
	const userRole = computed(() => user.value?.role || null)

	async function login(email: string, password: string): Promise<boolean> {
		const res = await api.post<{ access_token: string; refresh_token: string; user: UserProfile }>('/auth/login', {
			email,
			password,
		})
		if (res.success && res.data) {
			token.value = res.data.access_token
			localStorage.setItem('access_token', res.data.access_token)
			localStorage.setItem('refresh_token', res.data.refresh_token)
			user.value = res.data.user
			return true
		}
		return false
	}

	async function fetchProfile(): Promise<void> {
		if (!token.value) return
		try {
			const res = await api.get<UserProfile>('/auth/me')
			if (res.success && res.data) {
				user.value = res.data
			}
		} catch {
			logout()
		}
	}

	function logout(): void {
		user.value = null
		token.value = null
		localStorage.removeItem('access_token')
		localStorage.removeItem('refresh_token')
	}

	return {
		user,
		token,
		isAuthenticated,
		userRole,
		login,
		fetchProfile,
		logout,
	}
})
