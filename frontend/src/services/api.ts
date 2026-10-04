export interface ApiResponse<T = unknown> {
	success: boolean
	message?: string
	data?: T
	error?: {
		code: string
		message: string
		details?: Record<string, unknown>
	}
}

const BASE_URL = '/api'

export async function apiFetch<T = unknown>(
	endpoint: string,
	options: RequestInit = {},
	retryOnAuthFail: boolean = true,
): Promise<ApiResponse<T>> {
	const token = localStorage.getItem('access_token')
	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
		...(options.headers as Record<string, string>),
	}

	if (token) {
		headers['Authorization'] = `Bearer ${token}`
	}

	const url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${endpoint}`

	try {
		const response = await fetch(url, {
			...options,
			headers,
		})

		// Token expired -> Attempt refresh once
		if (response.status === 401 && retryOnAuthFail) {
			const refreshToken = localStorage.getItem('refresh_token')
			if (refreshToken) {
				try {
					const refreshRes = await fetch(`${BASE_URL}/auth/refresh`, {
						method: 'POST',
						headers: {
							'Content-Type': 'application/json',
							'Authorization': `Bearer ${refreshToken}`,
						},
					})
					const refreshData: ApiResponse<{ access_token: string }> = await refreshRes.json()
					if (refreshData.success && refreshData.data?.access_token) {
						localStorage.setItem('access_token', refreshData.data.access_token)
						return apiFetch<T>(endpoint, options, false)
					}
				} catch {
					// Refresh failed
				}
			}
			localStorage.removeItem('access_token')
			localStorage.removeItem('refresh_token')
		}

		const data: ApiResponse<T> = await response.json()
		return data
	} catch (error) {
		return {
			success: false,
			error: {
				code: 'NETWORK_ERROR',
				message: error instanceof Error ? error.message : 'Network request failed',
			},
		}
	}
}

export const api = {
	get<T = unknown>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
		return apiFetch<T>(endpoint, { ...options, method: 'GET' })
	},
	post<T = unknown>(endpoint: string, body?: unknown, options: RequestInit = {}): Promise<ApiResponse<T>> {
		return apiFetch<T>(endpoint, {
			...options,
			method: 'POST',
			body: body ? JSON.stringify(body) : undefined,
		})
	},
	put<T = unknown>(endpoint: string, body?: unknown, options: RequestInit = {}): Promise<ApiResponse<T>> {
		return apiFetch<T>(endpoint, {
			...options,
			method: 'PUT',
			body: body ? JSON.stringify(body) : undefined,
		})
	},
	delete<T = unknown>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
		return apiFetch<T>(endpoint, { ...options, method: 'DELETE' })
	},
	async upload<T = unknown>(endpoint: string, formData: FormData, options: RequestInit = {}): Promise<ApiResponse<T>> {
		const token = localStorage.getItem('access_token')
		const headers: Record<string, string> = {
			...(options.headers as Record<string, string>),
		}
		if (token) {
			headers['Authorization'] = `Bearer ${token}`
		}
		const url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${endpoint}`
		try {
			const res = await fetch(url, {
				...options,
				method: 'POST',
				headers,
				body: formData,
			})
			return (await res.json()) as ApiResponse<T>
		} catch (error) {
			return {
				success: false,
				error: {
					code: 'UPLOAD_ERROR',
					message: error instanceof Error ? error.message : 'Upload failed',
				},
			}
		}
	},
}

export default api
