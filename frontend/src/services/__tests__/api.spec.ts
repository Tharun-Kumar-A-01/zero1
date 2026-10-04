import { describe, it, expect, beforeEach, vi } from 'vitest'
import { api, apiFetch } from '@/services/api'

describe('api service (native fetch wrapper)', () => {
	beforeEach(() => {
		localStorage.clear()
		vi.restoreAllMocks()
	})

	it('attaches Authorization header when access_token exists in localStorage', async () => {
		localStorage.setItem('access_token', 'valid-test-jwt-token')

		const mockFetch = vi.fn<typeof fetch>().mockResolvedValue({
			status: 200,
			json: async () => ({ success: true, data: { value: 42 } }),
		} as Response)
		global.fetch = mockFetch

		const result = await api.get<{ value: number }>('/test-endpoint')

		expect(mockFetch).toHaveBeenCalledTimes(1)
		const firstCall = mockFetch.mock.calls[0]
		expect(firstCall).toBeDefined()
		const callOptions = firstCall?.[1] as RequestInit | undefined
		const calledHeaders = (callOptions?.headers || {}) as Record<string, string>
		expect(calledHeaders['Authorization']).toBe('Bearer valid-test-jwt-token')
		expect(result.success).toBe(true)
		expect(result.data?.value).toBe(42)
	})

	it('intercepts 401 and refreshes token via /auth/refresh before retrying', async () => {
		localStorage.setItem('access_token', 'expired-token')
		localStorage.setItem('refresh_token', 'valid-refresh-token')

		let callCount = 0
		const mockFetch = vi.fn<typeof fetch>().mockImplementation(async (input: RequestInfo | URL) => {
			const url = typeof input === 'string' ? input : input.toString()
			if (url.includes('/auth/refresh')) {
				return {
					status: 200,
					json: async () => ({
						success: true,
						data: { access_token: 'new-refreshed-token' },
					}),
				} as Response
			}

			callCount++
			if (callCount === 1) {
				return {
					status: 401,
					json: async () => ({ success: false, error: { code: 'TOKEN_EXPIRED', message: 'Expired' } }),
				} as Response
			}

			return {
				status: 200,
				json: async () => ({ success: true, data: { refreshedSuccess: true } }),
			} as Response
		})
		global.fetch = mockFetch

		const result = await apiFetch<{ refreshedSuccess: boolean }>('/test-endpoint')

		expect(mockFetch).toHaveBeenCalledTimes(3) // Initial call (401) -> Refresh call -> Retry call
		expect(localStorage.getItem('access_token')).toBe('new-refreshed-token')
		expect(result.success).toBe(true)
		expect(result.data?.refreshedSuccess).toBe(true)
	})

	it('returns structured NETWORK_ERROR envelope on fetch failure', async () => {
		global.fetch = vi.fn<typeof fetch>().mockRejectedValue(new Error('Connection refused'))

		const result = await api.get('/down-endpoint')

		expect(result.success).toBe(false)
		expect(result.error?.code).toBe('NETWORK_ERROR')
		expect(result.error?.message).toContain('Connection refused')
	})
})
