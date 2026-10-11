import { ref } from 'vue'

export interface PixelToastItem {
	id: string
	message: string
	title?: string
	color?: 'primary' | 'success' | 'danger' | 'warning' | 'info' | string
	duration?: number
}

const toasts = ref<PixelToastItem[]>([])

export function usePixelToast() {
	const init = (
		options: string | { message: string; title?: string; color?: string; duration?: number },
	) => {
		const id = 'toast_' + Math.random().toString(36).substring(2, 9)
		const toast: PixelToastItem =
			typeof options === 'string'
				? { id, message: options, color: 'primary', duration: 4000 }
				: {
						id,
						message: options.message,
						title: options.title,
						color: options.color || 'primary',
						duration: options.duration ?? 4000,
					}

		toasts.value.push(toast)

		if (toast.duration && toast.duration > 0) {
			setTimeout(() => {
				close(id)
			}, toast.duration)
		}

		return id
	}

	const close = (id: string) => {
		toasts.value = toasts.value.filter((t) => t.id !== id)
	}

	return {
		init,
		notify: init,
		close,
		toasts,
	}
}
